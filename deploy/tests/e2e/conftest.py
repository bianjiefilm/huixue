"""
慧学平台 E2E 测试基础设施
TDD红绿纪律：每个test block < 1分钟
"""
import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pytest
from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("E2E_BASE_URL", "http://100.74.141.3:3000")
API_URL = os.environ.get("E2E_API_URL", "http://100.74.141.3:8000")


def resilient_session(retries=3, backoff=1.0, timeout=15):
    """Create a requests.Session with automatic retry on connection/timeout errors."""
    s = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=[502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


def _login(browser, user, pwd, retries=2):
    for attempt in range(retries):
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = ctx.new_page()
        try:
            page.goto(f"{BASE_URL}/#/login", wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(2000)
            page.locator("#form_item_username").fill(user)
            page.locator("#form_item_password").fill(pwd)
            page.locator("button[type='submit']").click()
            # 等待登录完成：localStorage中出现userInfo且包含role
            page.wait_for_function(
                """() => {
                    try {
                        const info = JSON.parse(localStorage.getItem('userInfo') || '{}');
                        return !!info.role && info.role !== '';
                    } catch { return false; }
                }""",
                timeout=15000,
            )
            page.wait_for_timeout(500)
            return page
        except Exception:
            page.close()
            ctx.close()
            if attempt == retries - 1:
                raise
    raise RuntimeError("Login failed after retries")


def get_api_token(username, password):
    """通过API获取token，兼容多种登录响应格式，带重试"""
    session = resilient_session(retries=3, backoff=2.0)
    for content_type in ["json", "form"]:
        kwargs = (
            {"json": {"username": username, "password": password}}
            if content_type == "json"
            else {"data": {"username": username, "password": password}}
        )
        try:
            resp = session.post(f"{API_URL}/api/login", timeout=15, **kwargs)
        except requests.exceptions.ConnectionError:
            continue
        if resp.status_code != 200:
            continue
        data = resp.json()
        # 格式1: {"token": {"access_token": "..."}, "user": {...}}
        token = (data.get("token") or {}).get("access_token")
        if token:
            return token
        # 格式2: {"data": {"access_token": "..."}}
        token = (data.get("data") or {}).get("access_token")
        if token:
            return token
        # 格式3: {"access_token": "..."}
        token = data.get("access_token")
        if token:
            return token
    return ""


@pytest.fixture
def teacher_page(browser):
    """已登录的teacher1页面"""
    page = _login(browser, "teacher1", "teacher123")
    yield page
    page.close()


@pytest.fixture
def student_page(browser):
    """已登录的student1页面"""
    page = _login(browser, "student1", "student123")
    yield page
    page.close()


@pytest.fixture
def admin_page(browser):
    """已登录的admin页面"""
    page = _login(browser, "admin", "admin123")
    yield page
    page.close()


def get_user_id(token):
    """从/api/me获取当前用户ID"""
    resp = requests.get(
        f"{API_URL}/api/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resp.status_code == 200:
        return resp.json().get("id")
    return None


@pytest.fixture
def teacher_token():
    """teacher1的API token"""
    token = get_api_token("teacher1", "teacher123")
    assert token, "teacher1 login failed"
    return token


@pytest.fixture
def teacher_id(teacher_token):
    """teacher1的用户ID"""
    uid = get_user_id(teacher_token)
    assert uid, "Failed to get teacher1 user ID"
    return uid


@pytest.fixture
def student_token():
    """student1的API token"""
    token = get_api_token("student1", "student123")
    assert token, "student1 login failed"
    return token


@pytest.fixture
def admin_token():
    """admin的API token"""
    token = get_api_token("admin", "admin123")
    assert token, "admin login failed"
    return token
