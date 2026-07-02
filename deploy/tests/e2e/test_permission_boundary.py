"""
Block 2: 权限边界测试
验证角色不能越权访问。
"""
import pytest
from conftest import BASE_URL


def test_student_blocked_from_admin(student_page):
    """学生访问admin后台应被拦截"""
    student_page.goto(f"{BASE_URL}/#/admin/dashboard", wait_until="domcontentloaded", timeout=30000)
    student_page.wait_for_timeout(3000)
    url = student_page.url
    body = student_page.text_content("body") or ""
    blocked = (
        "/admin/dashboard" not in url
        or "权限" in body
        or "403" in body
        or "无权" in body
    )
    assert blocked, f"Student reached admin! url={url}"


def test_student_blocked_from_classroom_edit(student_page):
    """学生不能编辑课堂"""
    student_page.goto(f"{BASE_URL}/#/classroom/100/edit", wait_until="domcontentloaded", timeout=30000)
    student_page.wait_for_timeout(3000)
    url = student_page.url
    body = student_page.text_content("body") or ""
    blocked = (
        "/edit" not in url
        or "权限" in body
        or "403" in body
        or "无权" in body
    )
    assert blocked, f"Student can edit classroom! url={url}"


def test_teacher_blocked_from_admin(teacher_page):
    """教师访问admin后台应被拦截"""
    teacher_page.goto(f"{BASE_URL}/#/admin/users", wait_until="domcontentloaded", timeout=30000)
    teacher_page.wait_for_timeout(3000)
    url = teacher_page.url
    body = teacher_page.text_content("body") or ""
    blocked = (
        "/admin/users" not in url
        or "权限" in body
        or "403" in body
        or "无权" in body
    )
    assert blocked, f"Teacher reached admin users! url={url}"
