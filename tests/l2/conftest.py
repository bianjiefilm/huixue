"""
tests/l2/conftest.py
L2 Playwright UI 测试 - 专用 fixtures

修复记录 (2026-04-07):
- 根因: Playwright 1.58+ 中 about:blank 无法访问 localStorage (无 origin)
- 修复: 每个已认证 fixture 创建独立 BrowserContext，
  使用 context.add_init_script() 在页面加载前注入 localStorage
"""

import os
import pytest
from typing import Generator, Optional

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)
from tests.conftest import TEST_BASE_URL, TEST_API_URL


# ─────────────────────────────────────────────────────────────
# 环境配置
# ─────────────────────────────────────────────────────────────

PLAYWRIGHT_HEADLESS = os.environ.get("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
PLAYWRIGHT_SLOWMO = int(os.environ.get("PLAYWRIGHT_SLOWMO", "0"))
PLAYWRIGHT_TIMEOUT = int(os.environ.get("PLAYWRIGHT_TIMEOUT", "30000"))
PLAYWRIGHT_VIEWPORT = {
    "width": int(os.environ.get("PLAYWRIGHT_VIEWPORT_WIDTH", "1920")),
    "height": int(os.environ.get("PLAYWRIGHT_VIEWPORT_HEIGHT", "1080")),
}


# ─────────────────────────────────────────────────────────────
# Playwright 全局启动/关闭
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def playwright_instance() -> Generator[Playwright, None, None]:
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance: Playwright) -> Generator[Browser, None, None]:
    browser = playwright_instance.chromium.launch(
        headless=PLAYWRIGHT_HEADLESS,
        slow_mo=PLAYWRIGHT_SLOWMO,
    )
    yield browser
    browser.close()


# ─────────────────────────────────────────────────────────────
# 认证辅助
# ─────────────────────────────────────────────────────────────

def _get_auth_token(api_url: str, username: str, password: str) -> Optional[str]:
    """直接通过 requests 获取 auth token"""
    import requests
    try:
        resp = requests.post(
            f"{api_url}/api/login",
            json={"username": username, "password": password},
            timeout=15,
        )
        if resp.ok:
            data = resp.json()
            return (
                data.get("token", {}).get("access_token")
                or data.get("data", {}).get("token", {}).get("access_token")
                or data.get("data", {}).get("access_token")
                or data.get("access_token")
            )
    except Exception:
        return None
    return None


def _create_authenticated_context(
    browser: Browser,
    username: str,
    password: str,
    role: str = "student",
) -> Optional[BrowserContext]:
    """
    创建已认证的 BrowserContext。
    使用 add_init_script() 在页面加载前注入 localStorage，
    解决 Playwright 1.58+ 中 about:blank 无法访问 localStorage 的问题。

    同时注入 userInfo（含 role），避免前端 v-if="isTeacherOrAdmin" 这类按角色判断的分支全部误判为 student。
    """
    import json as _json
    token = _get_auth_token(TEST_API_URL, username, password)
    if not token:
        return None

    user_info = {
        "id": "1",
        "user_id": 1,
        "username": username,
        "realname": username,
        "role": role,
    }

    context = browser.new_context(
        viewport=PLAYWRIGHT_VIEWPORT,
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
        ignore_https_errors=True,
    )
    context.set_default_timeout(PLAYWRIGHT_TIMEOUT)

    # add_init_script 在页面加载前执行，确保 storage 在任何 JS 之前就位
    # 前端 SecureStorage 使用 'huixue_token'（sessionStorage，非 HTTPS 环境）
    # 用户信息使用 'huixue_user'（localStorage），兼容老 key 'userInfo'
    user_info_json = _json.dumps(user_info)
    context.add_init_script(f"""
        window.__TEST_TOKEN__ = {repr(token)};
        try {{
            window.sessionStorage.setItem('huixue_token', {repr(token)});
        }} catch (e) {{}}
        try {{
            window.localStorage.setItem('huixue_user', {repr(user_info_json)});
            window.localStorage.setItem('userInfo', {repr(user_info_json)});
            window.localStorage.setItem('token', {repr(token)});
            window.localStorage.setItem('access_token', {repr(token)});
            window.localStorage.setItem('auth_token', {repr(token)});
        }} catch (e) {{}}
    """)
    return context


# ─────────────────────────────────────────────────────────────
# 未认证的通用页面 fixture
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def browser_context(browser: Browser) -> Generator[BrowserContext, None, None]:
    """Function 级别的浏览器上下文，每个测试独立（未认证）"""
    context = browser.new_context(
        viewport=PLAYWRIGHT_VIEWPORT,
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
        ignore_https_errors=True,
    )
    context.set_default_timeout(PLAYWRIGHT_TIMEOUT)
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(browser_context: BrowserContext) -> Generator[Page, None, None]:
    """Function 级别的未认证页面 fixture"""
    page = browser_context.new_page()
    page.goto(TEST_BASE_URL, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT)
    yield page
    page.close()


# ─────────────────────────────────────────────────────────────
# 已认证的页面 fixtures
# 每个 fixture 创建独立的 BrowserContext（避免 localStorage 泄漏）
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def admin_page(browser: Browser) -> Generator[Page, None, None]:
    """管理员页面 fixture（已认证，独立 context）"""
    context = _create_authenticated_context(browser, "admin", "admin123", role="admin")
    if not context:
        pytest.skip("Cannot get auth token for admin")
    page = context.new_page()
    page.goto(TEST_BASE_URL, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT)
    yield page
    page.close()
    context.close()


@pytest.fixture(scope="function")
def teacher_page(browser: Browser) -> Generator[Page, None, None]:
    """教师页面 fixture（已认证，独立 context）"""
    context = _create_authenticated_context(browser, "teacher1", "teacher123", role="teacher")
    if not context:
        pytest.skip("Cannot get auth token for teacher1")
    page = context.new_page()
    page.goto(TEST_BASE_URL, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT)
    yield page
    page.close()
    context.close()


@pytest.fixture(scope="function")
def student_page(browser: Browser) -> Generator[Page, None, None]:
    """学生页面 fixture（已认证，独立 context）"""
    context = _create_authenticated_context(browser, "student1", "student123", role="student")
    if not context:
        pytest.skip("Cannot get auth token for student1")
    page = context.new_page()
    page.goto(TEST_BASE_URL, wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT)
    yield page
    page.close()
    context.close()


# ─────────────────────────────────────────────────────────────
# 特定功能页面的已认证 fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def bi_page(browser: Browser) -> Generator[Page, None, None]:
    """BI 可视化页面 fixture（已认证，教师身份）"""
    context = _create_authenticated_context(browser, "teacher1", "teacher123", role="teacher")
    if not context:
        pytest.skip("Cannot get auth token for teacher1")
    page = context.new_page()
    # 前端使用 Hash Router（createWebHashHistory），路径要用 /#/ 前缀
    page.goto(f"{TEST_BASE_URL}/#/visual", wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT)
    yield page
    page.close()
    context.close()


@pytest.fixture(scope="function")
def jupyter_page(browser: Browser) -> Generator[Page, None, None]:
    """Jupyter 编码训练页面 fixture（已认证，教师身份）"""
    context = _create_authenticated_context(browser, "teacher1", "teacher123", role="teacher")
    if not context:
        pytest.skip("Cannot get auth token for teacher1")
    page = context.new_page()
    page.goto(f"{TEST_BASE_URL}/#/project/jupyter", wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT)
    yield page
    page.close()
    context.close()


@pytest.fixture(scope="function")
def classroom_page(browser: Browser) -> Generator[Page, None, None]:
    """课堂管理页面 fixture（已认证，教师身份）"""
    context = _create_authenticated_context(browser, "teacher1", "teacher123", role="teacher")
    if not context:
        pytest.skip("Cannot get auth token for teacher1")
    page = context.new_page()
    page.goto(f"{TEST_BASE_URL}/#/classroom", wait_until="domcontentloaded", timeout=PLAYWRIGHT_TIMEOUT)
    yield page
    page.close()
    context.close()


# ─────────────────────────────────────────────────────────────
# 辅助函数
# ─────────────────────────────────────────────────────────────

def wait_for_element(page: Page, selector: str, timeout: int = None) -> bool:
    """等待元素出现"""
    timeout = timeout or PLAYWRIGHT_TIMEOUT
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except Exception:
        return False


def click_if_visible(page: Page, selector: str) -> bool:
    """如果元素可见则点击"""
    try:
        el = page.locator(selector)
        if el.is_visible():
            el.click()
            return True
    except Exception:
        pass
    return False


def get_text_safe(page: Page, selector: str, default: str = "") -> str:
    """安全获取元素文本"""
    try:
        return page.locator(selector).first.inner_text()
    except Exception:
        return default


# ─────────────────────────────────────────────────────────────
# L2 API Workflow Fixtures
# 用于 test_*_workflow.py 测试，避免每个测试函数重复登录
# ─────────────────────────────────────────────────────────────

import requests
from tests.l1._auth_helper import get_token, make_session, BASE_URL, TIMEOUT


@pytest.fixture(scope="module")
def l2_admin_token():
    """
    Module-scoped admin token for L2 workflow tests.
    Logs in once per test module, reuses the token across all tests in that module.
    Falls back to pytest.skip if login fails.
    """
    token = get_token("admin")
    if not token:
        pytest.skip("Cannot obtain admin token for L2 workflow tests")
    return token


@pytest.fixture(scope="module")
def l2_admin_session(l2_admin_token):
    """
    Module-scoped requests.Session with admin auth headers.
    Shares one HTTP connection pool across all tests in a module,
    eliminating per-test TCP handshake + login overhead.
    """
    session = make_session(l2_admin_token)
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()
