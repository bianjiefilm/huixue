"""
Block 18: 数据完整性回归
防止之前修复的API路径问题和权限问题复发。
"""
import pytest
import requests
from conftest import API_URL, BASE_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_homework_upload_endpoint_still_correct(teacher_token):
    """回归：homework-submission上传路径应在/api/v1/files/前缀下"""
    r = SESSION.post(
        f"{API_URL}/api/v1/files/upload/homework-submission",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    # 422 = 缺少文件（正确路径），404 = 路径又错了
    assert r.status_code == 422, f"Endpoint broken again: {r.status_code} {r.text[:200]}"


def test_teaching_resource_upload_endpoint_still_correct(teacher_token):
    """回归：teaching-resource上传路径应在/api/v1/files/前缀下"""
    r = SESSION.post(
        f"{API_URL}/api/v1/files/upload/teaching-resource",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 422, f"Endpoint broken again: {r.status_code} {r.text[:200]}"


def test_student_still_blocked_from_edit(student_page):
    """回归：学生仍然不能访问课堂编辑页"""
    student_page.goto(
        f"{BASE_URL}/#/classroom/100/edit",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    student_page.wait_for_timeout(3000)
    url = student_page.url
    body = student_page.text_content("body") or ""
    blocked = (
        "/edit" not in url
        or "权限" in body
        or "403" in body
        or "无权" in body
    )
    assert blocked, f"Student reached edit page! url={url}"


def test_all_15_classrooms_have_courses(teacher_token):
    """所有15个预置课堂都应有课程"""
    for cid in [100, 107, 114]:  # 采样3个
        r = SESSION.get(
            f"{API_URL}/api/v1/classrooms/{cid}/courses",
            headers={"Authorization": f"Bearer {teacher_token}"},
            timeout=TIMEOUT,
        )
        assert r.status_code == 200
        data = r.json()
        courses = data.get("data", {}).get("courses", [])
        assert len(courses) > 0, f"Classroom {cid} has no courses"


def test_login_returns_consistent_format():
    """登录API返回格式应一致：{token: {access_token}, user: {...}}"""
    r = SESSION.post(
        f"{API_URL}/api/login",
        json={"username": "teacher1", "password": "teacher123"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert "token" in data, f"Missing 'token' key: {list(data.keys())}"
    assert "access_token" in data["token"], f"Missing 'access_token': {data['token']}"
    assert "user" in data, f"Missing 'user' key: {list(data.keys())}"
    assert data["user"].get("role") or data["user"].get("username"), f"User data incomplete: {data['user']}"
