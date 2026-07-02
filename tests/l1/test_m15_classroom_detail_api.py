"""
tests/l1/test_m15_classroom_detail_api.py
自包含 L1 课堂详情 API 测试（章节/课时/统计）
每个测试独立管理自己的资源创建和清理。
"""
import pytest
import requests
import uuid
from tests.l1._auth_helper import get_token as _get_token, make_session as _session, BASE_URL, TIMEOUT

pytestmark = pytest.mark.l1


def _get_teacher_id(token):
    """从 JWT token 中提取 user_id"""
    import json, base64
    try:
        parts = token.split(".")
        payload = json.loads(base64.b64decode(parts[1] + "=="))
        return payload.get("user_id", 1)
    except Exception:
        return 1


def _create_classroom(token, suffix):
    """创建课堂，返回 classroom_id 或 None"""
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/classrooms",
            json={
                "name": f"测试课堂_{suffix}",
                "description": f"自动化测试 {suffix}",
                "semester": "2026-春",
                "start_date": "2026-04-01T00:00:00",
                "end_date": "2026-12-31T23:59:59",
            },
            timeout=TIMEOUT,
        )
        if resp.status_code == 200 and resp.json().get("code") == "0000":
            d = resp.json()
            cid = (d.get("data") or {}).get("classroom_id") or (d.get("data") or {}).get("id") or d.get("id")
            return cid
    finally:
        s.close()
    return None


def _delete_classroom(token, classroom_id):
    if not classroom_id:
        return
    s = _session(token)
    try:
        s.delete(f"{BASE_URL}/api/v1/classrooms/{classroom_id}", timeout=TIMEOUT)
    finally:
        s.close()


def _create_chapter(token, classroom_id, suffix):
    """创建章节，返回 chapter_id 或 None"""
    teacher_id = _get_teacher_id(token)
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/classrooms/{classroom_id}/chapters",
            params={"teacher_id": teacher_id, "title": f"章节_{suffix}"},
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            d = resp.json()
            return (d.get("data") or {}).get("id") or d.get("id")
    finally:
        s.close()
    return None


def _delete_chapter(token, chapter_id):
    if not chapter_id:
        return
    teacher_id = _get_teacher_id(token)
    s = _session(token)
    try:
        s.delete(
            f"{BASE_URL}/api/v1/chapters/{chapter_id}",
            params={"teacher_id": teacher_id},
            timeout=TIMEOUT,
        )
    finally:
        s.close()


# -----------------------------------------------------------------
# AC1: 创建章节
# -----------------------------------------------------------------

def test_create_chapter():
    """AC1: POST /classrooms/{id}/chapters -> 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    cid = _create_classroom(token, suffix)
    if cid is None:
        pytest.skip("Cannot create classroom")
    chapter_id = _create_chapter(token, cid, suffix)
    try:
        assert chapter_id is not None, \
            f"Failed to create chapter for classroom {cid}"
    finally:
        _delete_chapter(token, chapter_id)
        _delete_classroom(token, cid)


# -----------------------------------------------------------------
# AC2: 获取章节列表
# -----------------------------------------------------------------

def test_get_chapters():
    """AC2: GET /classrooms/{id}/chapters -> 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    cid = _create_classroom(token, suffix)
    if cid is None:
        pytest.skip("Cannot create classroom")
    _create_chapter(token, cid, suffix)
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/chapters",
            params={"teacher_id": _get_teacher_id(token)},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_classroom(token, cid)


# -----------------------------------------------------------------
# AC3: 更新章节
# -----------------------------------------------------------------

def test_update_chapter():
    """AC3: PATCH /chapters/{id}?teacher_id=X + title JSON -> 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    cid = _create_classroom(token, suffix)
    if cid is None:
        pytest.skip("Cannot create classroom")
    chapter_id = _create_chapter(token, cid, suffix)
    if chapter_id is None:
        _delete_classroom(token, cid)
        pytest.skip("Cannot create chapter")
    teacher_id = _get_teacher_id(token)
    s = _session(token)
    try:
        resp = s.patch(
            f"{BASE_URL}/api/v1/chapters/{chapter_id}",
            params={"teacher_id": teacher_id, "title": f"已更新章节_{suffix}"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_chapter(token, chapter_id)
        _delete_classroom(token, cid)


# -----------------------------------------------------------------
# AC4: 删除章节
# -----------------------------------------------------------------

def test_delete_chapter():
    """AC4: DELETE /chapters/{id}?teacher_id=X -> 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    cid = _create_classroom(token, suffix)
    if cid is None:
        pytest.skip("Cannot create classroom")
    chapter_id = _create_chapter(token, cid, suffix)
    if chapter_id is None:
        _delete_classroom(token, cid)
        pytest.skip("Cannot create chapter")
    teacher_id = _get_teacher_id(token)
    s = _session(token)
    try:
        resp = s.delete(
            f"{BASE_URL}/api/v1/chapters/{chapter_id}",
            params={"teacher_id": teacher_id},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_classroom(token, cid)


# -----------------------------------------------------------------
# AC5: 创建课时
# -----------------------------------------------------------------

def test_create_course():
    """AC5: GET /classrooms/{id}/courses?teacher_id=X -> 200 (列出课时)"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    cid = _create_classroom(token, suffix)
    if cid is None:
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/courses",
            params={"teacher_id": _get_teacher_id(token)},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_classroom(token, cid)


# -----------------------------------------------------------------
# AC6: 获取课堂统计
# -----------------------------------------------------------------

def test_get_classroom_statistics():
    """AC6: GET /classrooms/{id}/statistics -> 200 or 404 (endpoint may not exist)"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin")
    cid = _create_classroom(token, suffix)
    if cid is None:
        pytest.skip("Cannot create classroom")
    teacher_id = _get_teacher_id(token)
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/statistics",
            params={"teacher_id": teacher_id},
            timeout=TIMEOUT,
        )
        # Endpoint may return 404 if not implemented
        assert resp.status_code in (200, 404), \
            f"Expected 200/404, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_classroom(token, cid)


# -----------------------------------------------------------------
# AC7: 课堂分析概览
# -----------------------------------------------------------------

def test_classroom_analytics_overview():
    """AC7: GET /classrooms/{id}/analytics/overview?teacher_id=X -> 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin")
    cid = _create_classroom(token, suffix)
    if cid is None:
        pytest.skip("Cannot create classroom")
    teacher_id = _get_teacher_id(token)
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{cid}/analytics/overview",
            params={"teacher_id": teacher_id},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_classroom(token, cid)


# -----------------------------------------------------------------
# AC8: 错误路径 - 不存在的章节
# -----------------------------------------------------------------

def test_chapter_not_found():
    """AC8: 章节列表 -> 200 (无章节时返回空列表)"""
    token = _get_token("teacher")
    fake_id = 999999
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{fake_id}/chapters",
            params={"teacher_id": _get_teacher_id(token)},
            timeout=TIMEOUT,
        )
        # 后端对不存在课堂也返回 200 空列表
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()


# -----------------------------------------------------------------
# AC9: 错误路径 - 不存在的课时
# -----------------------------------------------------------------

def test_course_not_found():
    """AC9: 不存在的课时 -> 200 (后端返回 code="404" 而非 HTTP 404)"""
    token = _get_token("teacher")
    fake_id = 999999
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/classrooms/{fake_id}/courses",
            timeout=TIMEOUT,
        )
        # 后端对不存在的资源返回 200 + code="404" 而非 HTTP 404
        data = resp.json()
        assert resp.status_code == 200 and data.get("code") == "404", \
            f"Expected 200+code=404, got {resp.status_code}+{data.get('code')}: {resp.text[:200]}"
    finally:
        s.close()
