"""
Block 15: 学生端前端路由批量扫描
SPA应用——所有hash路由都返回同一个HTML壳，需通过Playwright验证SPA渲染。
这里用轻量HTTP检查确认SPA壳可达，加采样Playwright验证。
"""
import pytest
import requests
from conftest import BASE_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


STUDENT_ROUTES = [
    "/#/classroom",
    "/#/classroom/100",
    "/#/course",
    "/#/exam",
    "/#/login",
]


@pytest.mark.parametrize("route", STUDENT_ROUTES)
def test_spa_shell_returns_html(route):
    """SPA壳应返回有效HTML"""
    r = SESSION.get(f"{BASE_URL}{route}", timeout=TIMEOUT)
    assert r.status_code == 200
    assert len(r.text) > 200, f"Route {route}: body too small ({len(r.text)})"
    assert "<div id=" in r.text or "<script" in r.text, f"Not SPA HTML: {r.text[:200]}"


def test_student_classroom_list_page(student_page):
    """学生课堂列表页应正常渲染"""
    student_page.goto(f"{BASE_URL}/#/classroom", wait_until="domcontentloaded", timeout=30000)
    student_page.wait_for_timeout(5000)
    url = student_page.url
    body = student_page.text_content("body") or ""
    assert "classroom" in url, f"Redirected away: {url}"
    assert len(body.strip()) > 30, f"Page nearly empty: {body[:200]}"


def test_student_profile_page(student_page):
    """学生个人中心页应可访问"""
    student_page.goto(f"{BASE_URL}/#/profile", wait_until="domcontentloaded", timeout=30000)
    student_page.wait_for_timeout(3000)
    # 不应被重定向到登录页
    url = student_page.url
    assert "login" not in url, f"Redirected to login: {url}"
