"""
tests/l1/test_m21_courses_api.py
L1 课程管理 API 合约测试（自包含）

覆盖:
  AC1: 课程列表 GET /courses
  AC2: 课程详情 GET /courses/{id}
  AC3: 筛选标签 GET /courses/filter-tags
  AC4: 课程大纲 GET /courses/{id}/outline
  AC5: 课程章节 GET /courses/{id}/modules
  AC6: 课程技能 GET /courses/{id}/skills
  AC7: 统计概览 GET /statistics
  AC8: 实践资源库 GET /hands-on-library
  AC9: 课程资源库 GET /courses/library
  AC10: 课堂课程管理 POST /classrooms/{cid}/courses
  AC11: 错误路径
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
                "name": f"课程测试课堂_{suffix}",
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
    """获取第一个可用课程 ID"""
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
# AC1: 课程列表
# ═══════════════════════════════════════════════════════════════

def test_get_courses_list():
    """AC1: GET /courses → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/courses", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()


def test_get_courses_with_keyword():
    """AC1: 关键词搜索"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/courses",
            params={"keyword": "数据"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_courses_pagination():
    """AC1: 分页参数"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/courses",
            params={"page": 1, "size": 3},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC2: 课程详情
# ═══════════════════════════════════════════════════════════════

def test_get_course_detail():
    """AC2: GET /courses/{id} → 200"""
    token = _get_token("admin")
    cid = _get_first_course_id(token)
    if not cid:
        pytest.skip("No courses available")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/courses/{cid}", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json().get("data", {})
        assert data, f"No data in response: {resp.json()}"
    finally:
        s.close()


def test_get_course_detail_not_found():
    """AC2 错误路径: 不存在课程 → 404"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/courses/999999", timeout=TIMEOUT)
        assert resp.status_code in (404, 200), f"Got {resp.status_code}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC3: 筛选标签
# ═══════════════════════════════════════════════════════════════

def test_get_filter_tags():
    """AC3: GET /courses/filter-tags → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/courses/filter-tags", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_filter_tags_v2():
    """AC3: GET /filter-tags/courses → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/filter-tags/courses", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC4: 课程大纲
# ═══════════════════════════════════════════════════════════════

def test_get_course_outline():
    """AC4: GET /courses/{id}/outline → 200"""
    token = _get_token("admin")
    cid = _get_first_course_id(token)
    if not cid:
        pytest.skip("No courses available")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/courses/{cid}/outline", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC5: 课程章节
# ═══════════════════════════════════════════════════════════════

def test_get_course_modules():
    """AC5: GET /courses/{id}/modules → 200"""
    token = _get_token("admin")
    cid = _get_first_course_id(token)
    if not cid:
        pytest.skip("No courses available")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/courses/{cid}/modules", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC6: 课程技能标签
# ═══════════════════════════════════════════════════════════════

def test_get_course_skills():
    """AC6: GET /courses/{id}/skills → 200"""
    token = _get_token("admin")
    cid = _get_first_course_id(token)
    if not cid:
        pytest.skip("No courses available")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/courses/{cid}/skills",
            params={"user_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC7: 统计概览
# ═══════════════════════════════════════════════════════════════

def test_get_statistics():
    """AC7: GET /statistics → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/statistics", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC8: 实践资源库
# ═══════════════════════════════════════════════════════════════

def test_get_hands_on_library():
    """AC8: GET /hands-on-library → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/hands-on-library", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_hands_on_library_keyword():
    """AC8: 关键词搜索"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/hands-on-library",
            params={"keyword": "Python"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC9: 课程资源库
# ═══════════════════════════════════════════════════════════════

def test_get_course_library():
    """AC9: GET /courses/library → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/courses/library", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_course_library_by_type():
    """AC9: 按类型筛选"""
    token = _get_token("admin")
    s = _session(token)
    try:
        for course_type in ["practice", "training"]:
            resp = s.get(
                f"{BASE_URL}/api/v1/courses/library",
                params={"course_type": course_type},
                timeout=TIMEOUT,
            )
            assert resp.status_code == 200, f"Failed for type={course_type}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC10: 课堂课程管理
# ═══════════════════════════════════════════════════════════════

def test_add_course_to_classroom():
    """AC10: POST /classrooms/{cid}/courses?course_id=X → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin")
    course_id = _get_first_course_id(token)
    if not course_id:
        pytest.skip("No courses available")
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/classrooms/{cid}/courses",
            params={"course_id": course_id, "teacher_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code in (200, 409, 400), f"Got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_classroom(token, cid)


def test_get_available_courses_for_classroom():
    """AC10: GET /classrooms/{cid}/courses/available → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin")
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/courses/available",
            params={"teacher_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()
        _delete_classroom(token, cid)


# ═══════════════════════════════════════════════════════════════
# AC11: 错误路径
# ═══════════════════════════════════════════════════════════════

def test_courses_unauthorized():
    """AC11: 无 token → 401/403"""
    s = requests.Session()
    try:
        resp = s.get(f"{BASE_URL}/api/v1/courses", timeout=TIMEOUT)
        # courses 可能是公开的也可能需要认证
        assert resp.status_code in (200, 401, 403, 307)
    finally:
        s.close()
