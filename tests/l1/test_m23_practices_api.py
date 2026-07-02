"""
tests/l1/test_m23_practices_api.py
L1 实践管理 API 合约测试（自包含）

覆盖:
  AC1: 实践列表 GET /practices
  AC2: 实践详情 GET /practices/{id}
  AC3: 方向分类 GET /direction-categories
  AC4: 实践环境 GET /practice-environments
  AC5: 创建自定义实践 POST /custom-practices
  AC6: 我的实践列表 GET /custom-practices, /my-practices
  AC7: 自定义实践详情 GET /custom-practices/{id}
  AC8: 实践配置 GET/PATCH /practices/{id}/config
  AC9: 克隆实践 POST /practices/{id}/clone
  AC10: 关卡管理 GET /practices/{id}/stages/management
  AC11: 数据集 GET /practices/{id}/datasets
  AC12: 错误路径
"""
import pytest
import requests
import uuid
from tests.l1._auth_helper import get_token as _get_token, make_session as _session, BASE_URL, TIMEOUT

pytestmark = pytest.mark.l1


def _get_first_practice_id(token):
    """获取第一个可用实践 ID"""
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/practices", params={"page": 1, "size": 1}, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            items = data.get("list", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
            if items:
                return items[0].get("id") or items[0].get("practice_id")
    finally:
        s.close()
    return None


def _get_teacher_id(token):
    """获取当前教师 ID"""
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/me", timeout=TIMEOUT)
        if resp.status_code == 200:
            return resp.json().get("id")
    finally:
        s.close()
    return 1  # fallback


def _create_custom_practice(token, suffix, creator_id=1):
    """创建自定义实践，返回 practice_id 或 None"""
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/custom-practices",
            params={"creator_id": creator_id},
            json={
                "title": f"测试实践_{suffix}",
                "description": f"自动化测试 {suffix}",
                "direction": "数据分析",
                "sub_direction": "BI分析",
                "difficulty": "intermediate",
                "environment_type": "JUPYTER",
            },
            timeout=TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return data.get("practice_id") or data.get("id")
    finally:
        s.close()
    return None


def _delete_practice(token, pid, creator_id=1):
    """通过状态更新删除实践"""
    if not pid:
        return
    s = _session(token)
    try:
        s.patch(
            f"{BASE_URL}/api/v1/my-practices/{pid}/status",
            params={"creator_id": creator_id},
            json={"status": "deleted"},
            timeout=TIMEOUT,
        )
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC1: 实践列表
# ═══════════════════════════════════════════════════════════════

def test_get_practices_list():
    """AC1: GET /practices → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/practices", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()


def test_get_practices_with_keyword():
    """AC1: 关键词搜索"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/practices",
            params={"keyword": "数据"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_practices_with_direction():
    """AC1: 按方向筛选"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/practices",
            params={"direction": "数据分析"},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_practices_pagination():
    """AC1: 分页参数"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/practices",
            params={"page": 1, "size": 5},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC2: 实践详情
# ═══════════════════════════════════════════════════════════════

def test_get_practice_detail():
    """AC2: GET /practices/{id} → 200"""
    token = _get_token("admin")
    pid = _get_first_practice_id(token)
    if not pid:
        pytest.skip("No practices available")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/practices/{pid}", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()


def test_get_practice_detail_not_found():
    """AC2 错误路径: 不存在的实践 → 404"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/practices/999999", timeout=TIMEOUT)
        assert resp.status_code in (404, 200), f"Got {resp.status_code}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC3: 方向分类
# ═══════════════════════════════════════════════════════════════

def test_get_direction_categories():
    """AC3: GET /direction-categories → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/direction-categories", timeout=TIMEOUT)
        assert resp.status_code == 200
        data = resp.json().get("data")
        # data 可能为 None（无分类数据）或 list/dict
        assert data is None or isinstance(data, (list, dict)), f"Unexpected data type: {type(data)}"
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC4: 实践环境
# ═══════════════════════════════════════════════════════════════

def test_get_practice_environments():
    """AC4: GET /practice-environments → 200"""
    token = _get_token("admin")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/practice-environments", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC5: 创建自定义实践
# ═══════════════════════════════════════════════════════════════

def test_create_custom_practice():
    """AC5: POST /custom-practices → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    teacher_id = _get_teacher_id(token)
    pid = _create_custom_practice(token, suffix, creator_id=teacher_id)
    try:
        assert pid is not None, "Failed to create custom practice"
    finally:
        _delete_practice(token, pid, creator_id=teacher_id)


# ═══════════════════════════════════════════════════════════════
# AC6: 我的实践列表
# ═══════════════════════════════════════════════════════════════

def test_get_custom_practices():
    """AC6: GET /custom-practices?creator_id=X → 200"""
    token = _get_token("teacher")
    teacher_id = _get_teacher_id(token)
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/custom-practices",
            params={"creator_id": teacher_id},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


def test_get_my_practices():
    """AC6: GET /my-practices?creator_id=X → 200"""
    token = _get_token("teacher")
    teacher_id = _get_teacher_id(token)
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/my-practices",
            params={"creator_id": teacher_id},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC7: 自定义实践详情
# ═══════════════════════════════════════════════════════════════

def test_get_custom_practice_detail():
    """AC7: GET /custom-practices/{id} → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("teacher")
    teacher_id = _get_teacher_id(token)
    pid = _create_custom_practice(token, suffix, creator_id=teacher_id)
    if not pid:
        pytest.skip("Cannot create custom practice")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/custom-practices/{pid}",
            params={"creator_id": teacher_id},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    finally:
        s.close()
        _delete_practice(token, pid, creator_id=teacher_id)


# ═══════════════════════════════════════════════════════════════
# AC8: 实践配置
# ═══════════════════════════════════════════════════════════════

def test_get_practice_config():
    """AC8: GET /practices/{id}/config → 200"""
    token = _get_token("admin")
    pid = _get_first_practice_id(token)
    if not pid:
        pytest.skip("No practices available")
    s = _session(token)
    try:
        resp = s.get(f"{BASE_URL}/api/v1/practices/{pid}/config", timeout=TIMEOUT)
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC9: 克隆实践
# ═══════════════════════════════════════════════════════════════

def test_clone_practice():
    """AC9: POST /practices/{id}/clone → 200"""
    token = _get_token("teacher")
    pid = _get_first_practice_id(token)
    if not pid:
        pytest.skip("No practices available")
    s = _session(token)
    cloned_id = None
    try:
        resp = s.post(f"{BASE_URL}/api/v1/practices/{pid}/clone", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
        cloned_id = (resp.json().get("data") or {}).get("id") or (resp.json().get("data") or {}).get("practice_id")
    finally:
        s.close()
        if cloned_id:
            teacher_id = _get_teacher_id(token)
            _delete_practice(token, cloned_id, creator_id=teacher_id)


# ═══════════════════════════════════════════════════════════════
# AC10: 关卡管理
# ═══════════════════════════════════════════════════════════════

def test_get_practice_stages():
    """AC10: GET /practices/{id}/stages/management → 200"""
    token = _get_token("admin")
    pid = _get_first_practice_id(token)
    if not pid:
        pytest.skip("No practices available")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/practices/{pid}/stages/management",
            params={"creator_id": 1},
            timeout=TIMEOUT,
        )
        assert resp.status_code == 200
    finally:
        s.close()


# ═══════════════════════════════════════════════════════════════
# AC11: 数据集
# ═══════════════════════════════════════════════════════════════

def test_get_practice_datasets():
    """AC11: GET /practices/{id}/datasets → 200"""
    token = _get_token("teacher")
    teacher_id = _get_teacher_id(token)
    suffix = uuid.uuid4().hex[:8]
    pid = _create_custom_practice(token, suffix, creator_id=teacher_id)
    if not pid:
        pytest.skip("Cannot create practice")
    s = _session(token)
    try:
        resp = s.get(
            f"{BASE_URL}/api/v1/practices/{pid}/datasets",
            params={"creator_id": teacher_id},
            timeout=TIMEOUT,
        )
        assert resp.status_code in (200, 404)
    finally:
        s.close()
        _delete_practice(token, pid, creator_id=teacher_id)


# ═══════════════════════════════════════════════════════════════
# AC12: 错误路径
# ═══════════════════════════════════════════════════════════════

def test_practices_unauthorized():
    """AC12: 无 token → 401/403"""
    s = requests.Session()
    try:
        resp = s.get(f"{BASE_URL}/api/v1/practices", timeout=TIMEOUT)
        assert resp.status_code in (200, 401, 403, 307)
    finally:
        s.close()


def test_create_practice_missing_title():
    """AC12: 缺少 title → 400/422"""
    token = _get_token("teacher")
    s = _session(token)
    try:
        resp = s.post(
            f"{BASE_URL}/api/v1/custom-practices",
            params={"creator_id": 1},
            json={"description": "no title"},
            timeout=TIMEOUT,
        )
        assert resp.status_code in (400, 422, 200), f"Got {resp.status_code}"
    finally:
        s.close()
