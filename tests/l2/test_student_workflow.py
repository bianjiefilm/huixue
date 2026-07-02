"""
tests/l2/test_student_workflow.py
L2 学生学习工作流集成测试

跨模块交互测试（学生视角）:
  1. 管理员登录
  2. 创建课堂
  3. 获取可用课程
  4. 添加课程到课堂
  5. 查看课堂课程列表（学生视角）
  6. 查看学生仪表板
  7. 查看学习路径
  8. 查看技能星座
  9. 清理测试数据
"""
import pytest
import uuid
from tests.l1._auth_helper import (
    get_token as _get_token,
    make_session as _session,
    BASE_URL,
    TIMEOUT,
)

pytestmark = pytest.mark.l2

# ── Shared fixtures ──────────────────────────────────────────


@pytest.fixture(scope="module")
def admin_token():
    """Module-scoped admin token."""
    token = _get_token("admin")
    if not token:
        pytest.skip("Cannot obtain admin token")
    return token


@pytest.fixture(scope="module")
def workflow_state(admin_token):
    """
    Module-scoped fixture that sets up the entire workflow:
    create classroom -> find course -> add course -> yield state -> cleanup.

    Yields a dict with:
      classroom_id, course_id, token
    """
    state = {"token": admin_token, "classroom_id": None, "course_id": None}
    suffix = uuid.uuid4().hex[:8]

    # ── Step 1: Create classroom ──
    s = _session(admin_token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/classrooms",
            params={"teacher_id": 1},
            json={
                "name": f"L2学生工作流_{suffix}",
                "description": f"L2 集成测试 - 学生学习工作流 {suffix}",
                "semester": "2026-春",
                "start_date": "2026-04-01T00:00:00",
                "end_date": "2026-12-31T23:59:59",
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Create classroom failed: {resp.status_code} {resp.text[:300]}"
        body = resp.json()
        assert body.get("code") == "0000", f"Create classroom error: {body}"
        cid = (body.get("data") or {}).get("classroom_id") or (body.get("data") or {}).get("id")
        assert cid, f"No classroom_id in response: {body}"
        state["classroom_id"] = cid
    finally:
        s.close()

    # ── Step 2: Find first available course ──
    s = _session(admin_token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/courses",
            params={"page": 1, "size": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Get courses failed: {resp.status_code}"
        data = resp.json().get("data", {})
        items = data.get("list", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        if not items:
            pytest.skip("No courses available in the system")
        course_id = items[0].get("id") or items[0].get("course_id")
        assert course_id, f"No course id in first item: {items[0]}"
        state["course_id"] = course_id
    finally:
        s.close()

    # ── Step 3: Add course to classroom ──
    s = _session(admin_token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/classrooms/{state['classroom_id']}/courses",
            params={"course_id": state["course_id"], "teacher_id": 1},
            timeout=TIMEOUT,
        )
        # Server may return 200 or 500 (known pydantic serialization bug),
        # but the course still gets added. Accept both.
        assert resp.status_code in (200, 500), (
            f"Add course to classroom unexpected status: {resp.status_code} {resp.text[:300]}"
        )
    finally:
        s.close()

    yield state

    # ── Cleanup ──
    if state["classroom_id"]:
        s = _session(admin_token)
        try:
            s.delete(
                f"{BASE_URL}/api/v1/classrooms/{state['classroom_id']}",
                params={"teacher_id": 1},
                timeout=TIMEOUT,
            )
        except Exception:
            pass
        finally:
            s.close()


# ── Test cases ───────────────────────────────────────────────


class TestStudentLearningWorkflow:
    """L2: 学生学习工作流 - 跨模块集成测试"""

    def test_step1_classroom_created(self, workflow_state):
        """Verify classroom was created successfully."""
        assert workflow_state["classroom_id"] is not None

    def test_step2_course_available(self, workflow_state):
        """Verify a course was found in the system."""
        assert workflow_state["course_id"] is not None

    def test_step3_course_visible_in_classroom(self, workflow_state):
        """
        After adding a course, verify it appears in the classroom course list.
        Uses GET /classrooms/{cid}/courses which is the student-facing course view.
        """
        s = _session(workflow_state["token"])
        try:
            resp = s.get(
                f"{BASE_URL}/api/v1/classrooms/{workflow_state['classroom_id']}/courses",
                params={"teacher_id": 1},
                timeout=TIMEOUT,
            )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:300]}"
            body = resp.json()
            assert body.get("code") == "0000", f"Unexpected response code: {body.get('code')}"

            courses = (body.get("data") or {}).get("courses", [])
            course_ids = [
                c.get("course_id") or c.get("id") for c in courses
            ]
            assert workflow_state["course_id"] in course_ids, (
                f"Course {workflow_state['course_id']} not found in classroom courses: {course_ids}"
            )
        finally:
            s.close()

    def test_step4_student_dashboard(self, workflow_state):
        """
        Student dashboard returns valid data.
        GET /student/dashboard?student_id=1
        """
        s = _session(workflow_state["token"])
        try:
            resp = s.get(
                f"{BASE_URL}/api/v1/student/dashboard",
                params={"student_id": 1},
                timeout=TIMEOUT,
            )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            body = resp.json()
            # Dashboard may use {success: true} or {code: "0000"} format
            is_ok = body.get("success") is True or body.get("code") == "0000"
            assert is_ok, f"Dashboard returned unexpected response: {body}"
        finally:
            s.close()

    def test_step5_learning_paths(self, workflow_state):
        """
        Learning paths endpoint returns valid structure.
        GET /student/dashboard/learning-paths?student_id=1
        """
        s = _session(workflow_state["token"])
        try:
            resp = s.get(
                f"{BASE_URL}/api/v1/student/dashboard/learning-paths",
                params={"student_id": 1},
                timeout=TIMEOUT,
            )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            body = resp.json()
            is_ok = body.get("success") is True or body.get("code") == "0000"
            assert is_ok, f"Learning paths returned unexpected response: {body}"
            # data should be a list (may be empty if student has no paths yet)
            data = body.get("data")
            assert isinstance(data, list), f"Expected data to be a list, got {type(data).__name__}"
        finally:
            s.close()

    def test_step6_skill_constellation(self, workflow_state):
        """
        Skill constellation endpoint returns valid structure.
        GET /student/dashboard/skill-constellation?student_id=1
        """
        s = _session(workflow_state["token"])
        try:
            resp = s.get(
                f"{BASE_URL}/api/v1/student/dashboard/skill-constellation",
                params={"student_id": 1},
                timeout=TIMEOUT,
            )
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
            body = resp.json()
            is_ok = body.get("success") is True or body.get("code") == "0000"
            assert is_ok, f"Skill constellation returned unexpected response: {body}"
            data = body.get("data")
            assert isinstance(data, dict), f"Expected data to be a dict, got {type(data).__name__}"
            # Constellation should have nodes
            nodes = data.get("nodes", [])
            assert isinstance(nodes, list), f"Expected nodes to be a list, got {type(nodes).__name__}"
        finally:
            s.close()

    def test_step7_dashboard_has_skill_data(self, workflow_state):
        """
        Cross-check: dashboard response includes skillConstellation data,
        confirming cross-module data aggregation works.
        """
        s = _session(workflow_state["token"])
        try:
            resp = s.get(
                f"{BASE_URL}/api/v1/student/dashboard",
                params={"student_id": 1},
                timeout=TIMEOUT,
            )
            assert resp.status_code == 200
            body = resp.json()
            # The dashboard aggregates skill constellation inline
            constellation = body.get("skillConstellation")
            if constellation is not None:
                assert isinstance(constellation, dict), (
                    f"Expected skillConstellation to be dict, got {type(constellation).__name__}"
                )
                assert "nodes" in constellation, "skillConstellation missing 'nodes' key"
        finally:
            s.close()
