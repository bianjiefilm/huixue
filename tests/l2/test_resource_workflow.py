"""
tests/l2/test_resource_workflow.py
L2 资源管理工作流集成测试

工作流:
  1. Login as admin
  2. Create classroom
  3. List classroom resources (initially empty)
  4. List cloud disk (initially empty)
  5. Create a resource module
  6. List resource modules — verify module appears
  7. List teaching resource modules
  8. Get student learning records (empty but endpoint works)
  9. Cleanup: delete module, delete classroom
"""
import pytest
import uuid

from tests.l1._auth_helper import get_token, make_session, BASE_URL, TIMEOUT

pytestmark = pytest.mark.l2

TEACHER_ID = 1


def test_resource_management_workflow():
    """L2: 资源管理完整工作流 — 创建课堂 → 资源模块 → 各列表查询 → 清理"""

    # ------------------------------------------------------------------
    # Step 1: Login
    # ------------------------------------------------------------------
    token = get_token("admin")
    assert token, "Admin login failed — cannot proceed"
    session = make_session(token)

    classroom_id = None
    module_id = None

    try:
        # ------------------------------------------------------------------
        # Step 2: Create classroom
        # ------------------------------------------------------------------
        suffix = uuid.uuid4().hex[:8]
        resp = session.post(
            f"{BASE_URL}/api/v1/classrooms",
            params={"teacher_id": TEACHER_ID},
            json={
                "name": f"L2资源测试_{suffix}",
                "description": f"L2 资源管理集成测试 {suffix}",
                "start_date": "2026-04-01T00:00:00",
                "end_date": "2026-12-31T23:59:59",
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Create classroom: expected 200, got {resp.status_code}"
        body = resp.json()
        assert body.get("code") == "0000", f"Create classroom failed: {body}"
        data = body.get("data") or {}
        classroom_id = data.get("classroom_id") or data.get("id")
        assert classroom_id, f"No classroom_id in response: {data}"

        # ------------------------------------------------------------------
        # Step 3: List classroom resources (expect empty / 200)
        # ------------------------------------------------------------------
        resp = session.get(
            f"{BASE_URL}/api/v1/classrooms/{classroom_id}/resources",
            params={"teacher_id": TEACHER_ID},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"List resources: expected 200, got {resp.status_code}"

        # ------------------------------------------------------------------
        # Step 4: List cloud disk (expect empty / 200)
        # ------------------------------------------------------------------
        resp = session.get(
            f"{BASE_URL}/api/v1/classrooms/{classroom_id}/cloud-disk",
            params={"teacher_id": TEACHER_ID},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Cloud disk: expected 200, got {resp.status_code}"

        # ------------------------------------------------------------------
        # Step 5: Create a resource module (query-params, not JSON body)
        # ------------------------------------------------------------------
        module_name = f"L2测试模块_{suffix}"
        resp = session.post(
            f"{BASE_URL}/api/v1/classrooms/{classroom_id}/resource-modules",
            params={
                "name": module_name,
                "description": "L2 自动化测试模块",
                "teacher_id": TEACHER_ID,
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Create module: expected 200, got {resp.status_code}"
        body = resp.json()
        assert body.get("code") == "0000", f"Create module failed: {body}"
        module_data = body.get("data") or {}
        module_id = module_data.get("id")
        assert module_id, f"No module id in response: {module_data}"

        # ------------------------------------------------------------------
        # Step 6: List resource modules — verify our module appears
        # ------------------------------------------------------------------
        resp = session.get(
            f"{BASE_URL}/api/v1/classrooms/{classroom_id}/resource-modules",
            params={"teacher_id": TEACHER_ID},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"List modules: expected 200, got {resp.status_code}"
        modules_body = resp.json()
        modules_data = modules_body.get("data")
        # data may be a list or a dict with a list inside
        if isinstance(modules_data, dict):
            modules_list = modules_data.get("list") or modules_data.get("modules") or []
        elif isinstance(modules_data, list):
            modules_list = modules_data
        else:
            modules_list = []
        found = any(
            (m.get("id") == module_id or m.get("name") == module_name)
            for m in modules_list
        )
        assert found, (
            f"Created module (id={module_id}, name={module_name}) "
            f"not found in resource-modules list: {modules_list}"
        )

        # ------------------------------------------------------------------
        # Step 7: List teaching resource modules
        # ------------------------------------------------------------------
        resp = session.get(
            f"{BASE_URL}/api/v1/teaching-resources/classrooms/{classroom_id}/modules",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, (
            f"Teaching resource modules: expected 200, got {resp.status_code}"
        )

        # ------------------------------------------------------------------
        # Step 8: Get student learning records (empty but 200)
        # ------------------------------------------------------------------
        resp = session.get(
            f"{BASE_URL}/api/v1/classrooms/{classroom_id}/student-learning-records",
            params={"student_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, (
            f"Student learning records: expected 200, got {resp.status_code}"
        )

    finally:
        # ------------------------------------------------------------------
        # Step 9: Cleanup — delete module, then delete classroom
        # ------------------------------------------------------------------
        if module_id:
            try:
                session.delete(
                    f"{BASE_URL}/api/v1/resource-modules/{module_id}",
                    params={"teacher_id": TEACHER_ID},
                    timeout=TIMEOUT,
                )
            except Exception:
                pass

        if classroom_id:
            try:
                session.delete(
                    f"{BASE_URL}/api/v1/classrooms/{classroom_id}",
                    params={"teacher_id": TEACHER_ID},
                    timeout=TIMEOUT,
                )
            except Exception:
                pass

        session.close()
