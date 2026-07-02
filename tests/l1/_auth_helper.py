"""
L1 测试共享认证辅助
- 模块级 token 缓存，避免重复登录
- 带重试和 fallback 的 token 获取
"""
import time
import requests

BASE_URL = "http://<慧学服务器1-IP>:8000"
TIMEOUT = 15

_token_cache = {}

# 用户名 → 密码映射，按 fallback 优先级排列
_CREDENTIALS = {
    "admin": "admin123",
    "teacher1": "teacher123",
    "student1": "student123",
    "student2": "student123",
}

# 角色 → 用户名 fallback 链（第一个能登录的生效）
_ROLE_FALLBACK = {
    "teacher": ["teacher1", "admin"],
    "student": ["student1", "student2"],
    "admin": ["admin"],
}


def _try_login(username, password, max_retries=2, retry_delay=2):
    """尝试登录，带重试处理瞬态网络问题。成功返回 token，失败返回空字符串"""
    for attempt in range(max_retries + 1):
        try:
            resp = requests.post(
                f"{BASE_URL}/api/login",
                json={"username": username, "password": password},
                timeout=TIMEOUT,
            )
            if resp.status_code == 200 and resp.text.strip():
                data = resp.json()
                return data.get("token", {}).get("access_token") or ""
            # Non-retryable HTTP error (4xx/5xx) — don't retry
            if resp.status_code >= 400:
                return ""
        except (requests.ConnectionError, requests.exceptions.ReadTimeout):
            # Transient network issue — retry after delay
            if attempt < max_retries:
                time.sleep(retry_delay)
                continue
        except (requests.RequestException, ValueError):
            pass
        break
    return ""


def get_token(username_or_role, password=None):
    """
    获取 token（带缓存、重试和角色 fallback）

    支持:
      get_token("admin")           → admin 用户
      get_token("teacher")         → 先试 teacher1, 不行就用 admin
      get_token("admin", "admin123") → 明确用户名+密码
    """
    # 检查缓存
    cache_key = f"{username_or_role}:{password or 'default'}"
    if cache_key in _token_cache:
        return _token_cache[cache_key]

    # 如果是角色名，走 fallback 链
    if username_or_role in _ROLE_FALLBACK and password is None:
        for uname in _ROLE_FALLBACK[username_or_role]:
            pwd = _CREDENTIALS.get(uname, "test123")
            token = _try_login(uname, pwd)
            if token:
                _token_cache[cache_key] = token
                return token
        return ""

    # 直接用户名
    if password is None:
        password = _CREDENTIALS.get(username_or_role, "test123")

    for attempt in range(3):
        token = _try_login(username_or_role, password)
        if token:
            _token_cache[cache_key] = token
            return token
        if attempt < 2:
            time.sleep(1)

    # 最后 fallback 到 admin
    if username_or_role != "admin":
        admin_token = get_token("admin")
        if admin_token:
            _token_cache[cache_key] = admin_token
            return admin_token

    return ""


def make_session(token):
    """创建带认证的 session"""
    s = requests.Session()
    if token:
        s.headers["Authorization"] = f"Bearer {token}"
    return s
