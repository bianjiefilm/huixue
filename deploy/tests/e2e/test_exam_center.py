"""
Block 5: 考试中心独立入口
RED: 独立考试中心路由从未测试。
"""
from conftest import BASE_URL


def test_exam_paper_bank(teacher_page):
    """考试中心-试卷库应正常加载"""
    teacher_page.goto(f"{BASE_URL}/#/exam/paper-bank", wait_until="domcontentloaded", timeout=30000)
    teacher_page.wait_for_timeout(3000)
    body = teacher_page.text_content("body") or ""
    assert "404" not in body[:50], f"Got 404: {body[:200]}"


def test_exam_question_bank(teacher_page):
    """考试中心-试题库应正常加载"""
    teacher_page.goto(f"{BASE_URL}/#/exam/question-bank", wait_until="domcontentloaded", timeout=30000)
    teacher_page.wait_for_timeout(3000)
    body = teacher_page.text_content("body") or ""
    assert "404" not in body[:50], f"Got 404: {body[:200]}"


def test_classroom_exam_create(teacher_page):
    """课堂内创建考试页应有表单"""
    teacher_page.goto(f"{BASE_URL}/#/classroom/100/exam/create", wait_until="domcontentloaded", timeout=30000)
    teacher_page.wait_for_timeout(3000)
    body = teacher_page.text_content("body") or ""
    assert "404" not in body[:50], f"Got 404: {body[:200]}"
    has_form = (
        teacher_page.locator("input, textarea, .ant-form, .ant-select").count() > 0
        or "试卷" in body
        or "考试" in body
        or "创建" in body
    )
    assert has_form, f"No form on exam create page: {body[:300]}"
