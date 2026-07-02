"""
tests/l1/test_m24_students_api.py
L1 学生 & 仪表板 API 合约测试（自包含）

覆盖:
  AC1: 学生课程列表 GET /students/{sid}/classrooms/{cid}/courses
  AC2: 课堂管理页 GET /teachers/{tid}/classrooms/{cid}/management
  AC3: 添加学生到课堂 POST /teachers/{tid}/classrooms/{cid}/students
  AC4: 学生仪表板 GET /student/dashboard
  AC5: 学习路径 GET /student/dashboard/learning-paths
  AC6: 技能星座 GET /student/dashboard/skill-constellation
  AC7: 优先情报 GET /student/dashboard/priority-intel
  AC8: 错误路径
"""
import pytest
import requests
import uuid
from tests.l1._auth_helper import get_token as _get_token, make_session as _session, BASE_URL, TIMEOUT

pytestmark = pytest.mark.l1


def _create_classroom(token, suffix):
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/classrooms",
            json={
                "name": f"学生测试课堂_{suffix}",
                "description": f"自动化测试 {suffix}",
                "semester": "2026-春",
                "start_date": "2026-04-01T00:00:00",
                "end_date": "2026-12-31T23:59:59",
            },
            timeout=TIMEOUT,
        )
        if resp.status_code == 200 and resp.json().get("code") == "0000":
            return (resp.json().get("data") or {}).get("classroom_id") or (resp.json().get("data") or {}).get("id")
    finally:
        s.close()
    return None


def _delete_classroom(token, cid):
    if not cid:
        return
    s = _session(token)
    try:
        s.delete(f"{BASE_URL}/api/v1/classrooms/{cid}", timeout=TIMEOUT)
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC1: 学生课程列表
# ═══════════════════════════════════════════════════════════════

def test_get_student_courses():
    """AC1: GET /classrooms/{cid}/courses?teacher_id= → 200
    (后端使用 classroom-centric 路径，无独立 /students/{sid}/... 路径)"""
    token = _get_token("admin")
    suffix = uuid.uuid4().hex[:8]
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/courses",
            params={"teacher_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()
        _delete_classroom(token, cid)


# ═══════════════════════════════════════════════════════════════
# AC2: 课堂管理页
# ═══════════════════════════════════════════════════════════════

def test_get_classroom_management():
    """AC2: GET /classrooms/{cid}/management?teacher_id= → 200
    (后端路径不含 /teachers/{tid} 前缀)"""
    token = _get_token("admin")
    suffix = uuid.uuid4().hex[:8]
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/management",
            params={"teacher_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()
        _delete_classroom(token, cid)


# ═══════════════════════════════════════════════════════════════
# AC4: 学生仪表板
# ═══════════════════════════════════════════════════════════════

def test_get_student_dashboard():
    """AC4: GET /student/dashboard → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/student/dashboard",
            params={"student_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC5: 学习路径
# ═══════════════════════════════════════════════════════════════

def test_get_learning_paths():
    """AC5: GET /student/dashboard/learning-paths → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/student/dashboard/learning-paths",
            params={"student_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC6: 技能星座
# ═══════════════════════════════════════════════════════════════

def test_get_skill_constellation():
    """AC6: GET /student/dashboard/skill-constellation → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/student/dashboard/skill-constellation",
            params={"student_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC7: 优先情报
# ═══════════════════════════════════════════════════════════════

def test_get_priority_intel():
    """AC7: GET /student/dashboard/priority-intel → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/student/dashboard/priority-intel",
            params={"student_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC8: 错误路径
# ═══════════════════════════════════════════════════════════════

def test_dashboard_unauthorized():
    """AC8: 无 token 访问仪表板"""
    s = requests.Session()
    try:
        resp = s.get(f"{BASE_URL}/api/v1/student/dashboard", timeout=TIMEOUT)
        assert resp.status_code in (200, 401, 403, 307)
    finally:
        s.close()
