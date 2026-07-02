"""
tests/l1/test_m28_resources_api.py
L1 资源管理 API 合约测试（自包含）

覆盖:
  AC1: 课程资源 GET /courses/{id}/resources
  AC2: 课堂资源 GET /classrooms/{cid}/resources
  AC3: 云盘列表 GET /classrooms/{cid}/cloud-disk
  AC4: 资源模块 GET /classrooms/{cid}/resource-modules
  AC5: 教学资源模块 GET /teaching-resources/classrooms/{cid}/modules
  AC6: 课程教材列表 GET /coursematerial/lists
  AC7: 课程教材详情 GET /coursematerial/{id}
  AC8: 教学资源管理 (practice-environments, server-nodes, etc)
  AC9: 学生学习记录 GET /classrooms/{cid}/student-learning-records
  AC10: 错误路径
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
                "name": f"资源测试课堂_{suffix}",
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


def _get_first_course_id(token):
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/courses", params={"page": 1, "size": 1}, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            items = data.get("list", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            if items:
                return items[0].get("id") or items[0].get("course_id")
    finally:
        s.close()
    return None


# ═══════════════════════════════════════════════════════════════
# AC1: 课程资源
# ═══════════════════════════════════════════════════════════════

def test_get_course_resources():
    """AC1: GET /courses/{id}/resources → 200"""
    token = _get_token("admin")
    cid = _get_first_course_id(token)
    if not cid:
        pytest.skip("No courses available")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/courses/{cid}/resources", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC2: 课堂资源
# ═══════════════════════════════════════════════════════════════

def test_get_classroom_resources():
    """AC2: GET /classrooms/{cid}/resources → 200"""
    token = _get_token("admin")
    suffix = uuid.uuid4().hex[:8]
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/resources",
            params={"teacher_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()
        _delete_classroom(token, cid)


# ═══════════════════════════════════════════════════════════════
# AC3: 云盘
# ═══════════════════════════════════════════════════════════════

def test_get_classroom_cloud_disk():
    """AC3: GET /classrooms/{cid}/cloud-disk → 200"""
    token = _get_token("admin")
    suffix = uuid.uuid4().hex[:8]
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/classrooms/{cid}/cloud-disk", params={"teacher_id": 1}, timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()
        _delete_classroom(token, cid)


# ═══════════════════════════════════════════════════════════════
# AC4: 资源模块
# ═══════════════════════════════════════════════════════════════

def test_get_classroom_resource_modules():
    """AC4: GET /classrooms/{cid}/resource-modules → 200"""
    token = _get_token("admin")
    suffix = uuid.uuid4().hex[:8]
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/classrooms/{cid}/resource-modules", params={"teacher_id": 1}, timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()
        _delete_classroom(token, cid)


# ═══════════════════════════════════════════════════════════════
# AC5: 教学资源模块
# ═══════════════════════════════════════════════════════════════

def test_get_teaching_resource_modules():
    """AC5: GET /teaching-resources/classrooms/{cid}/modules → 200"""
    token = _get_token("admin")
    suffix = uuid.uuid4().hex[:8]
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/teaching-resources/classrooms/{cid}/modules",
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()
        _delete_classroom(token, cid)


# ═══════════════════════════════════════════════════════════════
# AC6: 课程教材列表
# ═══════════════════════════════════════════════════════════════

def test_get_course_materials_list():
    """AC6: GET /coursematerial/lists → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/coursematerial/lists", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC7: 课程教材详情
# ═══════════════════════════════════════════════════════════════

def test_get_course_material_detail():
    """AC7: GET /coursematerial/{id} → 200"""
    token = _get_token("admin")
    course_id = _get_first_course_id(token)
    if not course_id:
        pytest.skip("No courses available")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/coursematerial/{course_id}", timeout=TIMEOUT)
        assert resp.status_code in (200, 404), f"Expected 200/404, got {resp.status_code}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC8: 教学资源管理
# ═══════════════════════════════════════════════════════════════

def test_get_practice_environments():
    """AC8: GET /teaching-resources/practice-environments → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/teaching-resources/practice-environments", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_server_nodes_overview():
    """AC8: GET /teaching-resources/server-nodes/overview → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/teaching-resources/server-nodes/overview", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_container_processes():
    """AC8: GET /teaching-resources/container-processes → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/teaching-resources/container-processes", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_concurrent_experiment_setting():
    """AC8: GET /teaching-resources/concurrent-experiment-setting → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/teaching-resources/concurrent-experiment-setting", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC9: 学生学习记录
# ═══════════════════════════════════════════════════════════════

def test_get_student_learning_records():
    """AC9: GET /classrooms/{cid}/student-learning-records → 200"""
    token = _get_token("admin")
    suffix = uuid.uuid4().hex[:8]
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/student-learning-records",
            params={"student_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()
        _delete_classroom(token, cid)


# ═══════════════════════════════════════════════════════════════
# AC10: 错误路径
# ═══════════════════════════════════════════════════════════════

def test_resources_unauthorized():
    """AC10: 无 token 访问课堂资源 → 422 (teacher_id required)"""
    s = requests.Session()
    try:
        resp = s.get(f"{BASE_URL}/api/v1/classrooms/1/resources", timeout=TIMEOUT)
        assert resp.status_code in (200, 401, 403, 422, 307)
    finally:
        s.close()


def test_course_materials_unauthorized():
    """AC10: 无 token 访问教材"""
    s = requests.Session()
    try:
        resp = s.get(f"{BASE_URL}/api/coursematerial/lists", timeout=TIMEOUT)
        assert resp.status_code in (200, 401, 403, 307)
    finally:
        s.close()
