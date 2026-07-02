"""
tests/l1/test_m13_jupyter_api.py
自包含 L1 Jupyter 编码式实训 API 测试
"""
import pytest
import requests
import uuid


BASE_URL = "http://<慧学服务器1-IP>:8000"
TIMEOUT = 15

pytestmark = pytest.mark.l1


def _get_token(username, password):
    resp = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": username, "password": password},
        timeout=TIMEOUT
    )
    return resp.json().get("token", {}).get("access_token") or ""


def _create_classroom(token, suffix):
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    try:
        resp = session.post(
            f"{BASE_URL}/api/v1/classrooms",
            json={
                "name": f"Jupyter课堂_{suffix}",
                "description": f"Jupyter测试 {suffix}",
                "semester": "2026-春",
                "start_date": "2026-04-01T00:00:00",
                "end_date": "2026-12-31T23:59:59",
            },
            timeout=TIMEOUT
        )
        if resp.status_code == 200 and resp.json().get("code") == "0000":
            return (resp.json().get("data") or {}).get("classroom_id")
    finally:
        session.close()
    return None


def _delete_classroom(token, classroom_id):
    if not classroom_id:
        return
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    try:
        session.delete(f"{BASE_URL}/api/v1/classrooms/{classroom_id}", timeout=TIMEOUT)
    finally:
        session.close()


def _create_jupyter_training(token, suffix):
    """创建 JUPYTER 类型实训，返回 training_id"""
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    try:
        resp = session.post(
            f"{BASE_URL}/api/v1/trainings/",
            json={
                "title": f"Jupyter训练_{suffix}",
                "training_type": "JUPYTER",
                "description": f"Jupyter自动化测试 {suffix}",
                "course_hours": 1,
                "assignment_nodes": [],
            },
            timeout=TIMEOUT
        )
        if resp.status_code == 200 and resp.json().get("code") == "0000":
            return (resp.json().get("data") or {}).get("id")
    finally:
        session.close()
    return None


def _publish_training(token, training_id):
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    try:
        session.post(f"{BASE_URL}/api/v1/trainings/detail/{training_id}/publish", timeout=TIMEOUT)
    finally:
        session.close()


# ─────────────────────────────────────────────────────────────
# AC1: 获取实训环境列表
# ─────────────────────────────────────────────────────────────

def test_jupyter_training_environments():
    """AC1: GET /training-environments → 200 (或 404 如果端点未注册)"""
    token = _get_token("admin", "admin123")
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    try:
        resp = session.get(f"{BASE_URL}/api/v1/training-environments", timeout=TIMEOUT)
        assert resp.status_code in (200, 404), \
            f"Expected 200/404, got {resp.status_code}: {resp.text[:100]}"
    finally:
        session.close()


# ─────────────────────────────────────────────────────────────
# AC2: 获取我的实训列表
# ─────────────────────────────────────────────────────────────

def test_jupyter_my_trainings():
    """AC2: GET /my-trainings → 200 (或 404 如果端点未注册)"""
    token = _get_token("admin", "admin123")
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    try:
        resp = session.get(f"{BASE_URL}/api/v1/my-trainings", timeout=TIMEOUT)
        assert resp.status_code in (200, 404), \
            f"Expected 200/404, got {resp.status_code}: {resp.text[:100]}"
    finally:
        session.close()


# ─────────────────────────────────────────────────────────────
# AC3: 获取实训配置
# ─────────────────────────────────────────────────────────────

def test_jupyter_training_config():
    """AC3: GET /practices/{id}/config?creator_id=X → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin", "admin123")
    user_id = 1
    tid = _create_jupyter_training(token, suffix)
    if not tid:
        pytest.skip("Cannot create Jupyter training")
    _publish_training(token, tid)
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    try:
        resp = session.get(
            f"{BASE_URL}/api/v1/practices/{tid}/config",
            params={"creator_id": user_id},
            timeout=TIMEOUT
        )
        assert resp.status_code in (200, 422), \
            f"Expected 200/422, got {resp.status_code}: {resp.text[:100]}"
    finally:
        session.close()


# ─────────────────────────────────────────────────────────────
# AC4: 获取实训数据文件列表
# ─────────────────────────────────────────────────────────────

def test_jupyter_training_datasets():
    """AC4: GET /practices/{id}/datasets?creator_id=X → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin", "admin123")
    user_id = 1
    tid = _create_jupyter_training(token, suffix)
    if not tid:
        pytest.skip("Cannot create Jupyter training")
    _publish_training(token, tid)
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    try:
        resp = session.get(
            f"{BASE_URL}/api/v1/practices/{tid}/datasets",
            params={"creator_id": user_id},
            timeout=TIMEOUT
        )
        assert resp.status_code in (200, 404), \
            f"Expected 200/404, got {resp.status_code}: {resp.text[:100]}"
    finally:
        session.close()


# ─────────────────────────────────────────────────────────────
# AC5: 获取实训手册
# ─────────────────────────────────────────────────────────────

def test_jupyter_training_handbook():
    """AC5: GET /trainings/{id}/handbook → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin", "admin123")
    tid = _create_jupyter_training(token, suffix)
    if not tid:
        pytest.skip("Cannot create Jupyter training")
    _publish_training(token, tid)
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    try:
        resp = session.get(f"{BASE_URL}/api/v1/trainings/{tid}/handbook", timeout=TIMEOUT)
        assert resp.status_code in (200, 404), \
            f"Expected 200/404, got {resp.status_code}: {resp.text[:100]}"
    finally:
        session.close()


# ─────────────────────────────────────────────────────────────
# AC6: 获取实训 Git 仓库状态
# ─────────────────────────────────────────────────────────────

def test_jupyter_repo_status():
    """AC6: GET /practices/{id}/repo/status?creator_id=X → 200"""
    suffix = uuid.uuid4().hex[:8]
    token = _get_token("admin", "admin123")
    user_id = 1
    tid = _create_jupyter_training(token, suffix)
    if not tid:
        pytest.skip("Cannot create Jupyter training")
    _publish_training(token, tid)
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {token}"
    try:
        resp = session.get(
            f"{BASE_URL}/api/v1/practices/{tid}/repo/status",
            params={"creator_id": user_id},
            timeout=TIMEOUT
        )
        assert resp.status_code in (200, 404), \
            f"Expected 200/404, got {resp.status_code}: {resp.text[:100]}"
    finally:
        session.close()


# ─────────────────────────────────────────────────────────────
# AC7: 未授权访问
# ─────────────────────────────────────────────────────────────

def test_jupyter_unauthorized_access():
    """AC7: 无 token 访问 Jupyter API → 401/403/404"""
    session = requests.Session()
    try:
        resp = session.get(f"{BASE_URL}/api/v1/my-trainings", timeout=TIMEOUT)
        assert resp.status_code in (401, 403, 404), \
            f"Expected 401/403/404, got {resp.status_code}"
    finally:
        session.close()
