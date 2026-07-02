"""
Block 9: Admin全模块深度测试
当前只有冒烟测试3条，扩展到覆盖admin子路由和API。
"""
import requests
import pytest
from conftest import BASE_URL, API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def _admin_navigate(page, path, wait_ms=5000):
    """Admin导航并等待SPA渲染"""
    page.goto(f"{BASE_URL}/#/{path}", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(wait_ms)
    page.wait_for_function(
        "() => (document.body?.innerText?.trim()?.length || 0) > 50",
        timeout=10000,
    )


def test_admin_student_management(admin_page):
    """admin学生管理页应可访问"""
    _admin_navigate(admin_page, "admin/user/student")
    url = admin_page.url
    body = admin_page.text_content("body") or ""
    assert "/admin/user/student" in url, f"Redirected away: {url}"
    assert "404" not in body[:50], f"Got 404: {body[:200]}"


def test_admin_role_management(admin_page):
    """admin角色管理页应可访问"""
    _admin_navigate(admin_page, "admin/user/role")
    url = admin_page.url
    body = admin_page.text_content("body") or ""
    assert "/admin/user/role" in url, f"Redirected away: {url}"
    assert "404" not in body[:50], f"Got 404: {body[:200]}"


def test_admin_course_management(admin_page):
    """admin课程管理页应可访问"""
    _admin_navigate(admin_page, "admin/course/practice")
    url = admin_page.url
    body = admin_page.text_content("body") or ""
    assert "/admin/course" in url, f"Redirected away: {url}"
    assert "404" not in body[:50], f"Got 404: {body[:200]}"


def test_admin_resource_import(admin_page):
    """admin资源导入页应可访问"""
    _admin_navigate(admin_page, "admin/resource-import")
    url = admin_page.url
    body = admin_page.text_content("body") or ""
    assert "/admin/resource-import" in url, f"Redirected away: {url}"
    assert "404" not in body[:50], f"Got 404: {body[:200]}"


def test_admin_ai_generation(admin_page):
    """admin AI课程生成页应可访问"""
    _admin_navigate(admin_page, "admin/ai-generation")
    url = admin_page.url
    body = admin_page.text_content("body") or ""
    assert "/admin/ai-generation" in url, f"Redirected away: {url}"
    assert "404" not in body[:50], f"Got 404: {body[:200]}"


def test_admin_training_courses_api(admin_token):
    """admin课程管理API应返回数据"""
    r = SESSION.get(
        f"{API_URL}/api/v1/course-management/training-courses",
        params={"page": 1, "page_size": 5},
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert "items" in data or data.get("code") in [200, "0000", 0], f"Unexpected: {str(data)[:200]}"


def test_admin_user_list_api(admin_token):
    """admin用户列表API应返回数据（通过/api/me验证admin身份）"""
    r = SESSION.get(
        f"{API_URL}/api/me",
        headers={"Authorization": f"Bearer {admin_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("is_superuser") is True or data.get("username") == "admin", f"Not admin: {data}"
