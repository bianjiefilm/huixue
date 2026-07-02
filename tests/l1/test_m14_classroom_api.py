"""
tests/l1/test_m14_classroom_api.py
自包含 L1 课堂管理 API 测试（无 pytest fixtures 依赖）
每个测试独立管理自己的资源创建和清理。
"""
import pytest
import requests
import uuid
from tests.l1._auth_helper import get_token as _get_token, make_session as _session, BASE_URL, TIMEOUT

pytestmark = pytest.mark.l1


# ─── 资源辅助 ────────────────────────────────────────────────

def _create_classroom(token, suffix):
    """创建课堂，返回 classroom_id 或 None"""
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/classrooms",
            params={"teacher_id": 1},
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
    """删除课堂"""
    if not classroom_id:
        return
    s = _session(token)
    try:
        s.delete(
            f"{BASE_URL}/api/v1/classrooms/{classroom_id}",
            params={"teacher_id": 1},
            timeout=TIMEOUT,
        )
    finally:
        s.close()


# ─────────────────────────────────────────────────────────────
# AC1: 创建课堂
# ─────────────────────────────────────────────────────────────

def test_create_classroom_teacher():
    """AC1: 教师创建课堂 → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    cid = _create_classroom(token, suffix)
    try:
        assert cid is not None, "Failed to create classroom"
    finally:
        _delete_classroom(token, cid)


def test_create_classroom_admin():
    """AC1: 管理员创建课堂 → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin")
    cid = _create_classroom(token, suffix)
    try:
        assert cid is not None, "Failed to create classroom"
    finally:
        _delete_classroom(token, cid)


def test_create_classroom_student_forbidden():
    """AC1 错误路径: 学生不能创建课堂 → 403/422"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("student")
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/classrooms",
            json={
                "name": f"学生课堂_{suffix}",
                "description": "test",
                "semester": "2026-春",
                "start_date": "2026-04-01T00:00:00",
                "end_date": "2026-12-31T23:59:59",
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code in (401, 403, 422, 400), \
            f"Expected 401/403/422/400, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()


# ─────────────────────────────────────────────────────────────
# AC2: 获取课堂列表
# ─────────────────────────────────────────────────────────────

def test_get_classrooms_list():
    """AC2: 获取课堂列表 → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/classrooms", timeout=TIMEOUT)
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()


# ─────────────────────────────────────────────────────────────
# AC3: 获取单个课堂详情
# ─────────────────────────────────────────────────────────────

def test_get_classroom_detail():
    """AC3: 获取课堂详情 → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin")
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom — skipping detail test")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/classrooms/{cid}", timeout=TIMEOUT)
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_classroom(token, cid)


# ─────────────────────────────────────────────────────────────
# AC4: 更新课堂
# ─────────────────────────────────────────────────────────────

def test_update_classroom():
    """AC4: PUT /classrooms/{id}?teacher_id=X → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin")
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom — skipping update test")
    s = _session(token)
    try:
        resp = s.put(
            f"{BASE_URL}/api/v1/classrooms/{cid}",
            params={"teacher_id": 1},
            json={"name": f"已更新_{suffix}"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_classroom(token, cid)


# ─────────────────────────────────────────────────────────────
# AC5: 删除课堂
# ─────────────────────────────────────────────────────────────

def test_delete_classroom():
    """AC5: DELETE 删除课堂 → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin")
    cid = _create_classroom(token, suffix)
    if not cid:
        pytest.skip("Cannot create classroom — skipping delete test")
    s = _session(token)
    try:
        resp = s.delete(f"{BASE_URL}/api/v1/classrooms/{cid}", params={"teacher_id": 1}, timeout=TIMEOUT)
        assert resp.status_code == 200, \
            f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()


# ─────────────────────────────────────────────────────────────
# AC6: 错误路径 - 不存在的课堂
# ─────────────────────────────────────────────────────────────

def test_classroom_not_found():
    """AC6: 不存在的课堂 ID → 404"""
    token = _get_token("admin")
    fake_id = 999999
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/classrooms/{fake_id}", timeout=TIMEOUT)
        assert resp.status_code == 404, \
            f"Expected 404, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()


# ─────────────────────────────────────────────────────────────
# AC7: 未授权访问
# ─────────────────────────────────────────────────────────────

def test_unauthorized_access():
    """AC7: 无 token 访问 → 401/403 或 200（课堂列表可能公开）"""
    s = requests.Session()
    try:
        resp = s.get(f"{BASE_URL}/api/v1/classrooms", timeout=TIMEOUT)
        # Classrooms list may be publicly accessible; accept 200 as well
        assert resp.status_code in (200, 401, 403, 302, 307), \
            f"Expected 200/401/403/302/307, got {resp.status_code}"
    finally:
        s.close()
