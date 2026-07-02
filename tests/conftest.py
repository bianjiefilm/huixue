"""
tests/conftest.py
慧学云平台 - 全局测试配置与 fixtures
适用于 L1 / L2 / L3 所有测试层级
"""

import os
import sys
import uuid
import time
import pytest
import requests
from datetime import datetime, timedelta
from typing import Generator, Optional, Dict, Any


# ─────────────────────────────────────────────────────────────
# 环境配置（支持环境变量覆盖默认值）
# ─────────────────────────────────────────────────────────────

TEST_BASE_URL: str = os.environ.get("TEST_BASE_URL", "http://100.74.141.3:3000")
TEST_API_URL: str = os.environ.get("TEST_API_URL", "http://100.74.141.3:8000")
TEST_JUPYTER_URL: str = os.environ.get("TEST_JUPYTER_URL", "http://100.74.141.3:8888")

# 超时配置（适配 Tailscale VPN 网络）
TIMEOUT_SHORT = 15    # 简单 GET 请求
TIMEOUT_MEDIUM = 30   # POST /save 等中等复杂度
TIMEOUT_LONG = 60     # 文件下载、容器启动

# Scope 常量
SCOPE_SESSION = "session"
SCOPE_MODULE = "module"
SCOPE_FUNC = "function"


# ─────────────────────────────────────────────────────────────
# pytest 配置钩子
# ─────────────────────────────────────────────────────────────

def pytest_configure(config):
    """注册自定义 markers"""
    config.addinivalue_line("markers", "l1: L1 API contract tests")
    config.addinivalue_line("markers", "l2: L2 UI interaction tests")
    config.addinivalue_line("markers", "l3: L3 E2E tests")
    config.addinivalue_line("markers", "slow: slow tests (>30s)")
    config.addinivalue_line("markers", "ui: Playwright UI tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "bi: BI visualization tests")
    config.addinivalue_line("markers", "jupyter: Jupyter integration tests")
    config.addinivalue_line("markers", "classroom: Classroom management tests")


def pytest_collection_modifyitems(config, items):
    """根据文件路径自动添加 marker"""
    for item in items:
        path = str(item.fspath)
        if "/l1/" in path:
            item.add_marker(pytest.mark.l1)
        elif "/l2/" in path:
            item.add_marker(pytest.mark.l2)
        elif "/l3/" in path:
            item.add_marker(pytest.mark.l3)


# ─────────────────────────────────────────────────────────────
# 全局 Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope=SCOPE_SESSION)
def test_run_id() -> str:
    """本次测试运行的唯一 ID（用于数据隔离）"""
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope=SCOPE_SESSION)
def api_base_url() -> str:
    """后端 API 基础 URL"""
    return TEST_API_URL


@pytest.fixture(scope=SCOPE_SESSION)
def frontend_base_url() -> str:
    """前端基础 URL"""
    return TEST_BASE_URL


@pytest.fixture(scope=SCOPE_SESSION)
def jupyter_base_url() -> str:
    """Jupyter 服务 URL"""
    return TEST_JUPYTER_URL


# ─────────────────────────────────────────────────────────────
# HTTP 客户端封装（带重试）
# ─────────────────────────────────────────────────────────────

class APIClient:
    """带重试和超时的 HTTP 客户端"""

    def __init__(self, base_url: str, timeout: int = TIMEOUT_SHORT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self._token: Optional[str] = None

    def set_token(self, token: str):
        self._token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})

    def clear_token(self):
        if self._token:
            self.session.headers.pop("Authorization", None)
            self._token = None

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """带重试的请求"""
        kwargs.setdefault("timeout", self.timeout)
        url = f"{self.base_url}{path}"
        max_retries = kwargs.pop("max_retries", 3)
        retry_delay = kwargs.pop("retry_delay", 2)

        last_error = None
        for attempt in range(max_retries):
            try:
                resp = self.session.request(method, url, **kwargs)
                # 4xx/5xx 不重试（业务错误，非网络错误）
                return resp
            except (requests.ConnectionError, requests.Timeout) as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))

        raise last_error or Exception("Request failed after retries")

    def get(self, path: str, **kwargs) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self._request("POST", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        return self._request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self._request("DELETE", path, **kwargs)


@pytest.fixture(scope=SCOPE_SESSION)
def api_client(api_base_url) -> Generator[APIClient, None, None]:
    """Session 级别的 API 客户端（所有测试共享同一 HTTP session）"""
    client = APIClient(api_base_url, timeout=TIMEOUT_MEDIUM)
    yield client
    client.session.close()


# ─────────────────────────────────────────────────────────────
# 认证 Fixtures
# ─────────────────────────────────────────────────────────────

_PASSWORD_MAP = {
    "admin": "admin123",
    "teacher1": "teacher123",
    "student1": "student123",
    "student2": "student123",
    "student3": "student123",
}


class AuthManager:
    """认证管理器：负责登录、Token 获取、Token 刷新"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self._cache: Dict[str, str] = {}

    def login(self, username: str, password: str = None) -> str:
        """登录并返回 access_token"""
        if password is None:
            password = _PASSWORD_MAP.get(username, "test123")

        resp = requests.post(
            f"{self.api_url}/api/login",
            json={"username": username, "password": password},
            timeout=TIMEOUT_SHORT
        )
        if resp.status_code == 401:
            raise Exception(f"Login failed (401): {resp.text}")
        if resp.status_code >= 400:
            raise Exception(f"Login failed ({resp.status_code}): {resp.text}")

        data = resp.json()
        # 实际后端返回: {"token": {"access_token": "..."}}
        token = (
            data.get("token", {}).get("access_token")
            or data.get("data", {}).get("token", {}).get("access_token")
            or data.get("data", {}).get("access_token")
            or data.get("access_token")
            or ""
        )
        if not token:
            raise Exception(f"No token in response: {data}")
        return token

    def get_token(self, username: str, password: str = None) -> str:
        """获取 token（带缓存）"""
        key = username
        if key in self._cache:
            return self._cache[key]

        token = self.login(username, password)
        self._cache[key] = token
        return token


_auth_manager: Optional[AuthManager] = None


def get_auth_manager(api_url: str) -> AuthManager:
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager(api_url)
    return _auth_manager


@pytest.fixture(scope=SCOPE_SESSION)
def auth_manager(api_base_url) -> AuthManager:
    """Session 级别的认证管理器"""
    return get_auth_manager(api_base_url)


@pytest.fixture(scope=SCOPE_SESSION)
def admin_token(auth_manager) -> str:
    """Session 级别的管理员 Token（跨函数共享，同一 token 不重复获取）"""
    return auth_manager.get_token("admin")


@pytest.fixture(scope=SCOPE_SESSION)
def teacher_token(auth_manager) -> str:
    """Session 级别的教师 Token"""
    return auth_manager.get_token("teacher1")


@pytest.fixture(scope=SCOPE_SESSION)
def student_token(auth_manager) -> str:
    """Session 级别的学生 Token"""
    return auth_manager.get_token("student1")


@pytest.fixture(scope=SCOPE_FUNC)
def admin_client(api_client, admin_token) -> APIClient:
    """Function 级别的管理员 API 客户端"""
    api_client.set_token(admin_token)
    yield api_client
    api_client.clear_token()


@pytest.fixture(scope=SCOPE_FUNC)
def teacher_client(api_client, teacher_token) -> APIClient:
    """Function 级别的教师 API 客户端"""
    api_client.set_token(teacher_token)
    yield api_client
    api_client.clear_token()


@pytest.fixture(scope=SCOPE_FUNC)
def student_client(api_client, student_token) -> APIClient:
    """Function 级别的学生 API 客户端"""
    api_client.set_token(student_token)
    yield api_client
    api_client.clear_token()


# ─────────────────────────────────────────────────────────────
# 数据隔离 Fixture
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope=SCOPE_MODULE)
def unique_suffix(test_run_id, request) -> str:
    """
    每个测试模块生成唯一后缀（用于并发安全隔离）。
    格式：{run_id}_{module_name_hash}
    """
    func_name = request.node.nodeid.replace("/", "_").replace("\\", "_")[:40]
    suffix_hash = str(abs(hash(func_name)) % 10**8).zfill(8)
    return f"{test_run_id}_{suffix_hash}"


# ─────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────

def auth_header(token: str) -> Dict[str, str]:
    """构造 Authorization header"""
    return {"Authorization": f"Bearer {token}"}


def wait_for_condition(condition_fn, timeout: int = 10, interval: float = 0.5) -> bool:
    """轮询等待条件满足"""
    elapsed = 0.0
    while elapsed < timeout:
        if condition_fn():
            return True
        time.sleep(interval)
        elapsed += interval
    return False


def safe_json_extract(data: dict, *keys) -> Any:
    """
    安全提取嵌套 JSON 字段。
    处理 API 返回 {"data": null} 或 {"data": {"field": null}} 的情况。
    用法: safe_json_extract(data, "data", "config", "canvas_data")
    """
    result = data
    for key in keys:
        if result is None:
            return None
        if isinstance(result, dict):
            result = result.get(key)
        else:
            return None
    return result


def assert_api_success(resp: requests.Response, msg: str = ""):
    """断言 API 响应成功（status 200/201 或 code=0000）"""
    data = resp.json()
    code = data.get("code", "")
    assert resp.status_code in (200, 201) or code == "0000", \
        f"{msg}: status={resp.status_code}, body={data}"


def assert_api_error(resp: requests.Response, expected_status: int, msg: str = ""):
    """断言 API 返回错误"""
    assert resp.status_code == expected_status, \
        f"{msg}: expected {expected_status}, got {resp.status_code}"


def get_api_code(resp: requests.Response) -> str:
    """从响应 JSON 中提取 code 字段"""
    try:
        return resp.json().get("code", "")
    except Exception:
        return ""


# ─────────────────────────────────────────────────────────────
# Training Fixture（所有 BI/Jupyter 测试的前置资源）
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope=SCOPE_MODULE)
def test_training_bi(teacher_client, unique_suffix) -> dict:
    """
    创建 BI 类型实训，返回 {"id": int, "name": str, "classroom_id": int}
    前置条件链：
    1. 创建 Training(type=BI) via POST /api/v1/trainings/
    2. 发布 via /api/v1/trainings/detail/{id}/publish
    3. 创建 Classroom via POST /api/v1/classrooms
    4. 关联 via /api/v1/trainings/library/{id}/add-to-classroom/{classroom_id}
    """
    # Step 1: 创建 Training
    name = f"BI测试_{unique_suffix}"
    resp = teacher_client.post(
        "/api/v1/trainings/",
        json={
            "title": name,
            "training_type": "BI",
            "description": f"自动化BI实训 {unique_suffix}",
            "course_hours": 4,
            "assignment_nodes": [],
        },
        timeout=TIMEOUT_MEDIUM
    )
    if resp.status_code == 307:
        resp = teacher_client.post(
            resp.headers.get("Location", "/api/v1/trainings/"),
            json={
                "title": name,
                "training_type": "BI",
                "description": f"自动化BI实训 {unique_suffix}",
                "course_hours": 4,
                "assignment_nodes": [],
            },
            timeout=TIMEOUT_MEDIUM
        )

    if resp.status_code >= 400:
        raise Exception(f"Failed to create BI training: {resp.status_code} {resp.text}")

    data = resp.json()
    training_id = (
        data.get("data") or {}
    ).get("id") or data.get("id")
    assert training_id is not None, f"No training_id in response: {data}"

    # Step 2: 发布
    teacher_client.post(
        f"/api/v1/trainings/detail/{training_id}/publish",
        timeout=TIMEOUT_SHORT
    )

    # Step 3: 创建 Classroom
    class_resp = teacher_client.post(
        "/api/v1/classrooms",
        json={
            "name": f"BI测试课堂_{unique_suffix}",
            "description": f"BI测试用课堂 {unique_suffix}",
            "teacher_id": 1,
        },
        timeout=TIMEOUT_MEDIUM
    )
    class_data = class_resp.json()
    classroom_id = (
        class_data.get("data") or {}
    ).get("classroom_id") or class_data.get("classroom_id") or class_data.get("id")
    if not classroom_id:
        # fallback: 从现有的 classrooms 中找第一个
        list_resp = teacher_client.get("/api/v1/classrooms")
        list_data = (list_resp.json().get("data") or [{}])[0] if list_resp.status_code == 200 else {}
        classroom_id = list_data.get("id") or 1

    # Step 4: 关联 Training 和 Classroom
    teacher_client.post(
        f"/api/v1/trainings/library/{training_id}/add-to-classroom/{classroom_id}",
        timeout=TIMEOUT_SHORT
    )

    yield {"id": training_id, "name": name, "type": "BI", "classroom_id": classroom_id}

    # 清理
    try:
        teacher_client.delete(f"/api/v1/trainings/detail/{training_id}", timeout=TIMEOUT_SHORT)
    except Exception:
        pass
    try:
        if classroom_id:
            teacher_client.delete(f"/api/v1/classrooms/{classroom_id}", timeout=TIMEOUT_SHORT)
    except Exception:
        pass


@pytest.fixture(scope=SCOPE_MODULE)
def test_training_jupyter(teacher_client, unique_suffix) -> dict:
    """
    创建 JUPYTER 类型实训，返回 {"id": int, "name": str, "classroom_id": int}
    前置条件链：Training(type=JUPYTER) → publish → Classroom → associate
    """
    # Step 1: 创建 Training
    name = f"Jupyter测试_{unique_suffix}"
    resp = teacher_client.post(
        "/api/v1/trainings/",
        json={
            "title": name,
            "training_type": "JUPYTER",
            "description": f"自动化Jupyter实训 {unique_suffix}",
            "course_hours": 4,
            "assignment_nodes": [],
        },
        timeout=TIMEOUT_MEDIUM
    )
    if resp.status_code == 307:
        resp = teacher_client.post(
            resp.headers.get("Location", "/api/v1/trainings/"),
            json={
                "title": name,
                "training_type": "JUPYTER",
                "description": f"自动化Jupyter实训 {unique_suffix}",
                "course_hours": 4,
                "assignment_nodes": [],
            },
            timeout=TIMEOUT_MEDIUM
        )

    if resp.status_code >= 400:
        raise Exception(f"Failed to create Jupyter training: {resp.status_code} {resp.text}")

    data = resp.json()
    training_id = (
        data.get("data") or {}
    ).get("id") or data.get("id")
    assert training_id is not None, f"No training_id in response: {data}"

    # Step 2: 发布
    teacher_client.post(
        f"/api/v1/trainings/detail/{training_id}/publish",
        timeout=TIMEOUT_SHORT
    )

    # Step 3: 创建 Classroom
    class_resp = teacher_client.post(
        "/api/v1/classrooms",
        json={
            "name": f"Jupyter测试课堂_{unique_suffix}",
            "description": f"Jupyter测试用课堂 {unique_suffix}",
            "teacher_id": 1,
        },
        timeout=TIMEOUT_MEDIUM
    )
    class_data = class_resp.json()
    classroom_id = (
        class_data.get("data") or {}
    ).get("classroom_id") or class_data.get("classroom_id") or class_data.get("id")
    if not classroom_id:
        list_resp = teacher_client.get("/api/v1/classrooms")
        list_data = (list_resp.json().get("data") or [{}])[0] if list_resp.status_code == 200 else {}
        classroom_id = list_data.get("id") or 1

    # Step 4: 关联
    teacher_client.post(
        f"/api/v1/trainings/library/{training_id}/add-to-classroom/{classroom_id}",
        timeout=TIMEOUT_SHORT
    )

    yield {"id": training_id, "name": name, "type": "JUPYTER", "classroom_id": classroom_id}

    # 清理
    try:
        teacher_client.delete(f"/api/v1/trainings/detail/{training_id}", timeout=TIMEOUT_SHORT)
    except Exception:
        pass
    try:
        if classroom_id:
            teacher_client.delete(f"/api/v1/classrooms/{classroom_id}", timeout=TIMEOUT_SHORT)
    except Exception:
        pass
