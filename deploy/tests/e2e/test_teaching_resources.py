"""
Block 4+6: 教学资源模块冒烟
Block 4: 基础页面可达性
Block 6: 教学资源交互（课堂内资源tab、课程列表）
"""
import requests
from conftest import BASE_URL, API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_classroom_detail_loads(teacher_page):
    """课堂详情页应正常加载（资源在tab内）"""
    teacher_page.goto(f"{BASE_URL}/#/classroom/100", wait_until="domcontentloaded", timeout=30000)
    teacher_page.wait_for_timeout(8000)  # SPA渲染需要较长时间
    url = teacher_page.url
    body = teacher_page.text_content("body") or ""
    # 至少应该到达课堂详��URL（未被重定向到404或登录页）
    assert "classroom" in url, f"Not on classroom page: {url}"
    assert "404" not in body[:50], f"Classroom detail 404: {body[:200]}"


def test_exam_center_accessible(teacher_page):
    """考试中心（exam模块）应正常加载"""
    teacher_page.goto(f"{BASE_URL}/#/exam", wait_until="domcontentloaded", timeout=30000)
    teacher_page.wait_for_timeout(3000)
    body = teacher_page.text_content("body") or ""
    assert "404" not in body[:50], f"Exam center 404: {body[:200]}"


def test_course_list_api(teacher_token):
    """课程列表API应返回数据"""
    r = SESSION.get(
        f"{API_URL}/api/v1/courses",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Courses API failed: {data}"


def test_trainings_api(teacher_token):
    """实训列表API应返回数据"""
    r = SESSION.get(
        f"{API_URL}/api/v1/trainings/my-trainings",
        headers={"Authorization": f"Bearer {teacher_token}"},
        timeout=TIMEOUT,
    )
    assert r.status_code == 200
    data = r.json()
    assert data.get("code") in [200, "0000", 0], f"Trainings API failed: {data}"
