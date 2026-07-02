"""
Block 7: 负面测试（安全边界）
RED: 负面测试覆盖率=0%。验证错误输入和越权访问的处理。
"""
import requests
from conftest import API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_wrong_password_rejected():
    """错误密码应被拒绝"""
    r = SESSION.post(
        f"{API_URL}/api/login",
        json={"username": "teacher1", "password": "wrongpassword"},
        timeout=TIMEOUT,
    )
    # 不应返回有效token
    if r.status_code == 200:
        data = r.json()
        token = (data.get("token") or {}).get("access_token")
        assert not token, "Wrong password returned a valid token!"
    else:
        assert r.status_code in [401, 422, 400, 403]


def test_empty_credentials_rejected():
    """空凭据应被拒绝"""
    r = SESSION.post(
        f"{API_URL}/api/login",
        json={"username": "", "password": ""},
        timeout=TIMEOUT,
    )
    if r.status_code == 200:
        data = r.json()
        token = (data.get("token") or {}).get("access_token")
        assert not token, "Empty credentials returned a valid token!"
    else:
        assert r.status_code in [401, 422, 400, 403]


def test_invalid_token_rejected():
    """无效token应被拒绝"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms",
        headers={"Authorization": "Bearer invalid_token_12345"},
        timeout=TIMEOUT,
    )
    assert r.status_code in [401, 403], f"Invalid token accepted: {r.status_code}"


def test_nonexistent_classroom_handled(teacher_token):
    """不存在的课堂应返回404或错误码"""
    r = SESSION.get(
        f"{API_URL}/api/v1/classrooms/99999",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code in [200, 404], f"Server error: {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        # code应该表示未找到，不应该是成功
        assert data.get("code") not in [200, "0000"], f"Nonexistent classroom returned success: {data}"


def test_sql_injection_blocked():
    """SQL注入应被阻止"""
    r = SESSION.post(
        f"{API_URL}/api/login",
        json={"username": "' OR 1=1 --", "password": "test"},
        timeout=TIMEOUT,
    )
    if r.status_code == 200:
        data = r.json()
        token = (data.get("token") or {}).get("access_token")
        assert not token, "SQL injection returned a valid token!"
    # 不应该是500（表明注入到达了数据库）
    assert r.status_code != 500, f"SQL injection caused server error: {r.text[:200]}"
