"""
Block 1: Admin冒烟测试
验证admin能访问管理后台核心页面。
"""
from conftest import BASE_URL


def _navigate_and_wait(page, path, wait_ms=5000):
    """导航并等待SPA渲染完成"""
    page.goto(f"{BASE_URL}/#/{path}", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(wait_ms)
    # 等待SPA内容渲染（不只是shell）
    page.wait_for_function(
        "() => (document.body?.innerText?.trim()?.length || 0) > 50",
        timeout=10000,
    )


def test_admin_reaches_dashboard(admin_page):
    """admin登录后能到达admin仪表盘"""
    _navigate_and_wait(admin_page, "admin/dashboard")
    url = admin_page.url
    body = admin_page.text_content("body") or ""
    assert "/admin/dashboard" in url, f"Admin redirected away: {url}"
    assert "权限" not in body and "没有权限" not in body, f"Permission denied: {body[:200]}"


def test_admin_dashboard_has_content(admin_page):
    """admin仪表盘应有实质内容"""
    _navigate_and_wait(admin_page, "admin/dashboard")
    body = admin_page.text_content("body") or ""
    assert len(body.strip()) > 50, f"Dashboard is nearly empty: {body[:200]}"


def test_admin_teacher_management(admin_page):
    """admin教师管理页应可访问"""
    _navigate_and_wait(admin_page, "admin/user/teacher")
    url = admin_page.url
    body = admin_page.text_content("body") or ""
    assert "/admin/user/teacher" in url, f"Redirected away: {url}"
    assert "404" not in body[:50], f"Got 404: {body[:200]}"
