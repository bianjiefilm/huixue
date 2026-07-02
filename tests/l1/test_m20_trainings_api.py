"""
tests/l1/test_m20_trainings_api.py
L1 实训管理 API 合约测试（自包含，无 pytest fixtures 依赖）

覆盖:
  AC1: 实训列表 GET /trainings/
  AC2: 创建实训 POST /trainings/
  AC3: 实训详情 GET /trainings/detail/{id}
  AC4: 更新实训 PUT /trainings/detail/{id}
  AC5: 删除实训 DELETE /trainings/detail/{id}
  AC6: 发布/取消发布 POST /trainings/detail/{id}/publish|unpublish
  AC7: 实训资源库 GET /trainings/library
  AC8: 资源库详情 GET /trainings/library/{id}
  AC9: 添加到课堂 POST /trainings/library/{id}/add-to-classroom/{cid}
  AC10: 克隆实训 POST /trainings/{id}/clone
  AC11: 环境列表 GET /trainings/environments
  AC12: 数据集 GET /trainings/{id}/datasets
  AC13: 我的实训 GET /trainings/my-trainings
  AC14: 错误路径 - 不存在/未授权
"""
import pytest
import requests
import uuid
from tests.l1._auth_helper import get_token as _get_token, make_session as _session, BASE_URL, TIMEOUT

pytestmark = pytest.mark.l1


# ─── 资源辅助 ────────────────────────────────────────────────

def _create_training(token, suffix, training_type="BI"):
    """创建实训，返回 training_id 或 None"""
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/trainings/",
            json={
                "title": f"测试实训_{training_type}_{suffix}",
                "training_type": training_type,
                "description": f"自动化测试 {suffix}",
                "course_hours": 2,
                "assignment_nodes": [],
            },
            timeout=TIMEOUT,
        )
        if resp.status_code == 200 and resp.json().get("code") == "0000":
            return (resp.json().get("data") or {}).get("id")
    finally:
        s.close()
    return None


def _delete_training(token, tid):
    if not tid:
        return
    s = _session(token)
    try:
        s.delete(f"{BASE_URL}/api/v1/trainings/detail/{tid}", timeout=TIMEOUT)
    finally:
        s.close()


def _publish_training(token, tid):
    s = _session(token)
    try:
        s.post(f"{BASE_URL}/api/v1/trainings/detail/{tid}/publish", timeout=TIMEOUT)
    finally:
        s.close()


def _create_classroom(token, suffix):
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/classrooms",
            json={
                "name": f"实训测试课堂_{suffix}",
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
# AC1: 实训列表
# ═══════════════════════════════════════════════════════════════

def test_get_trainings_list():
    """AC1: GET /trainings/ → 200, 返回列表"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/trainings/", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.json()
        assert data.get("code") == "0000", f"Unexpected code: {data}"
    finally:
        s.close()


def test_get_trainings_with_pagination():
    """AC1: 分页参数 page=1&size=5"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/trainings/",
            params={"page": 1, "size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
        items = (resp.json().get("data") or {}).get("list", [])
        assert len(items) <= 5, f"Expected <=5 items, got {len(items)}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC2: 创建实训
# ═══════════════════════════════════════════════════════════════

def test_create_training_bi():
    """AC2: POST /trainings/ BI类型 → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix, "BI")
    try:
        assert tid is not None, "Failed to create BI training"
    finally:
        _delete_training(token, tid)


def test_create_training_jupyter():
    """AC2: POST /trainings/ JUPYTER类型 → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix, "JUPYTER")
    try:
        assert tid is not None, "Failed to create JUPYTER training"
    finally:
        _delete_training(token, tid)


def test_create_training_missing_title():
    """AC2 错误路径: 缺少 title → 422"""
    token = _get_token("teacher")
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/trainings/",
            json={
                "training_type": "BI",
                "description": "missing title",
                "course_hours": 2,
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code in (400, 422), f"Expected 400/422, got {resp.status_code}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC3: 实训详情
# ═══════════════════════════════════════════════════════════════

def test_get_training_detail():
    """AC3: GET /trainings/detail/{id} → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix)
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/trainings/detail/{tid}", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        detail = (resp.json().get("data") or {})
        assert detail.get("id") == tid or detail.get("training_id") == tid
    finally:
        s.close()
        _delete_training(token, tid)


def test_get_training_detail_not_found():
    """AC3 错误路径: 不存在的 ID → 404"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/trainings/detail/999999", timeout=TIMEOUT)
        assert resp.status_code in (404, 200), f"Got {resp.status_code}"
        if resp.status_code == 200:
            # 有些 API 返回 200 但 data 为 null
            data = resp.json()
            assert data.get("data") is None or data.get("code") != "0000"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC4: 更新实训
# ═══════════════════════════════════════════════════════════════

def test_update_training():
    """AC4: PUT /trainings/detail/{id} → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix)
    s = _session(token)
    try:
        new_title = f"已更新_{suffix}"
        resp = s.put(
            f"{BASE_URL}/api/v1/trainings/detail/{tid}",
            json={"title": new_title, "description": "updated"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_training(token, tid)


# ═══════════════════════════════════════════════════════════════
# AC5: 删除实训
# ═══════════════════════════════════════════════════════════════

def test_delete_training():
    """AC5: DELETE /trainings/detail/{id} → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix)
    s = _session(token)
    try:
        resp = s.delete(f"{BASE_URL}/api/v1/trainings/detail/{tid}", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC6: 发布 / 取消发布
# ═══════════════════════════════════════════════════════════════

def test_publish_training():
    """AC6: POST /trainings/detail/{id}/publish → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix)
    s = _session(token)
    try:
        resp = s.post(f"{BASE_URL}/api/v1/trainings/detail/{tid}/publish", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_training(token, tid)


def test_unpublish_training():
    """AC6: 发布后取消发布 → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix)
    s = _session(token)
    try:
        # 先发布
        s.post(f"{BASE_URL}/api/v1/trainings/detail/{tid}/publish", timeout=TIMEOUT)
        # 再取消
        resp = s.post(f"{BASE_URL}/api/v1/trainings/detail/{tid}/unpublish", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_training(token, tid)


# ═══════════════════════════════════════════════════════════════
# AC7: 实训资源库
# ═══════════════════════════════════════════════════════════════

def test_get_training_library():
    """AC7: GET /trainings/library → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/trainings/library", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()


def test_training_library_keyword_search():
    """AC7: 关键词搜索"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/trainings/library",
            params={"keyword": "BI"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC8: 资源库详情 / 预览
# ═══════════════════════════════════════════════════════════════

def test_get_training_library_detail():
    """AC8: GET /trainings/library/{id} → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix)
    _publish_training(token, tid)
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/trainings/library/{tid}", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()
        _delete_training(token, tid)


def test_get_training_preview():
    """AC8: GET /trainings/library/{id}/preview → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix)
    _publish_training(token, tid)
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/trainings/library/{tid}/preview", timeout=TIMEOUT * 2)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()
        _delete_training(token, tid)


# ═══════════════════════════════════════════════════════════════
# AC9: 添加到课堂
# ═══════════════════════════════════════════════════════════════

def test_add_training_to_classroom():
    """AC9: POST /trainings/library/{id}/add-to-classroom/{cid} → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin")
    tid = _create_training(token, suffix)
    _publish_training(token, tid)
    cid = _create_classroom(token, suffix)
    if not cid:
        _delete_training(token, tid)
        pytest.skip("Cannot create classroom")
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/trainings/library/{tid}/add-to-classroom/{cid}",
            json={
                "start_time": "2026-05-01T00:00:00",
                "end_time": "2026-12-31T23:59:59",
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    finally:
        s.close()
        _delete_training(token, tid)
        _delete_classroom(token, cid)


# ═══════════════════════════════════════════════════════════════
# AC10: 克隆实训
# ═══════════════════════════════════════════════════════════════

def test_clone_training():
    """AC10: POST /trainings/{id}/clone → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix)
    s = _session(token)
    cloned_id = None
    try:
        resp = s.post(f"{BASE_URL}/api/v1/trainings/{tid}/clone", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        cloned_id = (resp.json().get("data") or {}).get("id")
    finally:
        s.close()
        _delete_training(token, tid)
        _delete_training(token, cloned_id)


# ═══════════════════════════════════════════════════════════════
# AC11: 环境列表
# ═══════════════════════════════════════════════════════════════

def test_get_environments():
    """AC11: GET /trainings/environments → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/trainings/environments", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_environments_list():
    """AC11: GET /trainings/environments/list → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/trainings/environments/list", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC12: 数据集
# ═══════════════════════════════════════════════════════════════

def test_get_training_datasets():
    """AC12: GET /trainings/{id}/datasets → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    tid = _create_training(token, suffix)
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/trainings/{tid}/datasets", timeout=TIMEOUT)
        assert resp.status_code in (200, 404), f"Got {resp.status_code}"
    finally:
        s.close()
        _delete_training(token, tid)


# ═══════════════════════════════════════════════════════════════
# AC13: 我的实训
# ═══════════════════════════════════════════════════════════════

def test_get_my_trainings():
    """AC13: GET /trainings/my-trainings → 200"""
    token = _get_token("teacher")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/trainings/my-trainings",
            params={"page": 1, "size": 10},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC14: 错误路径 - 未授权
# ═══════════════════════════════════════════════════════════════

def test_unauthorized_create_training():
    """AC14: 无 token 创建实训 → 401/403"""
    s = requests.Session()
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/trainings/",
            json={"title": "hack", "training_type": "BI", "course_hours": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code in (401, 403, 307), f"Expected 401/403, got {resp.status_code}"
    finally:
        s.close()


def test_student_cannot_create_training():
    """AC14: 学生角色不能创建实训 → 403"""
    token = _get_token("student")
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/trainings/",
            json={
                "title": "student_hack",
                "training_type": "BI",
                "description": "forbidden",
                "course_hours": 1,
                "assignment_nodes": [],
            },
            timeout=TIMEOUT,
        )
        assert resp.status_code in (403, 422, 400), f"Got {resp.status_code}"
    finally:
        s.close()
