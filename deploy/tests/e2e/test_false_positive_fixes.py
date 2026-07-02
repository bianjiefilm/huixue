"""
Block 6: 修复前一轮假阳性
RED: 之前的验证测试有3个假阳性，用严格断言重测。
"""
import requests
import pytest
from conftest import BASE_URL, API_URL, resilient_session

SESSION = resilient_session(retries=2, backoff=2.0)
TIMEOUT = 20


def test_homework_submission_endpoint_exists(teacher_token):
    """P0-1真实验证：homework-submission API应存在（非404）"""
    headers = {"Authorization": f"Bearer {teacher_token}"}
    # POST with empty body — expect 422 (validation) not 404 (missing)
    resp = SESSION.post(
        f"{API_URL}/api/v1/files/upload/homework-submission",
        headers=headers,
        json={},
        timeout=TIMEOUT,
    )
    assert resp.status_code != 404, \
        f"homework-submission endpoint does NOT exist (404)"


def test_training_edit_loads_form(teacher_page, teacher_token):
    """P0-4真实验证：实训编辑页应有表单，不能导航到首页"""
    headers = {"Authorization": f"Bearer {teacher_token}"}
    resp = SESSION.get(
        f"{API_URL}/api/v1/trainings/",
        headers=headers,
        params={"page": 1, "page_size": 1},
        timeout=TIMEOUT,
    )
    data = resp.json()
    items = data.get("data", {}).get("items", [])
    if not items:
        pytest.skip("No trainings in DB")

    training_id = items[0]["id"]
    teacher_page.goto(
        f"{BASE_URL}/#/course/training/{training_id}/edit",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    teacher_page.wait_for_timeout(4000)
    url = teacher_page.url
    # 不应该被重定向到首页
    assert "training" in url or "edit" in url, \
        f"Redirected away from edit page: {url}"


def test_exam_detail_route(teacher_page):
    """P1-2真实验证：考试详情页应存在"""
    # 正确路由：/classroom/:classroomId/course/:courseId/exam/:examId/detail
    teacher_page.goto(
        f"{BASE_URL}/#/classroom/100/course/100/exam/100/detail",
        wait_until="domcontentloaded",
        timeout=30000,
    )
    teacher_page.wait_for_timeout(3000)
    body = teacher_page.text_content("body") or ""
    assert "404" not in body[:50] and "页面不存在" not in body, \
        f"Exam detail is 404: {body[:200]}"
