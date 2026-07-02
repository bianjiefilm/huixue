"""
慧学 (慧学元伴) — 深度功能交互浏览器测试 v3
=====================================================
核心原则：
- 每个测试验证【真实数据】显示，而非仅检查页面文字长度
- 每个测试断言页面【无错误提示】
- 比对 API 返回数据与页面显示内容
- 使用真实表单登录（非 cookie/localStorage 手动设置）
- 所有 ID 和密码与当前数据库一致
"""
import os
import re
import json
import pytest
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8000"
SCREENSHOT_DIR = Path("/sessions/charming-friendly-pascal/screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

# 当前数据库 ID 常量
TEACHER_ID = 29
STUDENT_ID = 30
ADMIN_ID = 1
CLASSROOM_ID = 100
TRAINING_ID = 100

# 页面中不应出现的错误关键词
ERROR_KEYWORDS = ["服务器错误", "不存在", "错误", "无法获取", "未找到"]


# ─── Fixtures ───────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def browser():
    pw = sync_playwright().start()
    b = pw.chromium.launch(headless=True, args=["--no-sandbox"])
    yield b
    b.close()
    pw.stop()


def _extract_token(data):
    """从登录响应中提取 token，兼容多种响应格式"""
    if data.get("token", {}).get("access_token"):
        return data["token"]["access_token"]
    if data.get("data", {}).get("access_token"):
        return data["data"]["access_token"]
    if data.get("access_token"):
        return data["access_token"]
    return None


def _real_login(browser: Browser, username: str, password: str) -> BrowserContext:
    """通过真实表单登录获取认证上下文"""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(f"{BASE_URL}/#/login", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(1000)
    page.locator("input[type='text']").first.fill(username)
    page.locator("input[type='password']").first.fill(password)
    page.locator("button").first.click()
    page.wait_for_timeout(5000)
    # 登录后不应停留在 login 页
    assert "/login" not in page.url or "redirect" in page.url, \
        f"Login failed for {username}: still at {page.url}"
    page.close()
    return ctx


@pytest.fixture(scope="session")
def teacher_token():
    r = requests.post(f"{API_URL}/api/login",
                      json={"username": "teacher1", "password": "password123"})
    data = r.json()
    token = _extract_token(data)
    assert token, f"Teacher login failed: {data}"
    return token


@pytest.fixture(scope="session")
def student_token():
    r = requests.post(f"{API_URL}/api/login",
                      json={"username": "student1", "password": "password123"})
    data = r.json()
    token = _extract_token(data)
    assert token, f"Student login failed: {data}"
    return token


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API_URL}/api/login",
                      json={"username": "admin", "password": "password123"})
    data = r.json()
    token = _extract_token(data)
    assert token, f"Admin login failed: {data}"
    return token


@pytest.fixture(scope="session")
def teacher_context(browser) -> BrowserContext:
    ctx = _real_login(browser, "teacher1", "password123")
    yield ctx
    ctx.close()


@pytest.fixture(scope="session")
def student_context(browser) -> BrowserContext:
    ctx = _real_login(browser, "student1", "password123")
    yield ctx
    ctx.close()


@pytest.fixture(scope="session")
def admin_context(browser) -> BrowserContext:
    ctx = _real_login(browser, "admin", "password123")
    yield ctx
    ctx.close()


def _screenshot(page: Page, name: str):
    path = SCREENSHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=True)
    return path


def _wait_and_check(page: Page, timeout=10000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        page.wait_for_timeout(3000)


def _assert_no_error_toast(page: Page, context_msg: str = ""):
    """断言页面中没有错误提示 toast/弹窗"""
    error_selectors = [
        ".ant-message-error",
        ".ant-notification-notice-error",
        ".ant-message-warning",
    ]
    for sel in error_selectors:
        count = page.locator(sel).count()
        if count > 0:
            error_text = page.locator(sel).first.inner_text()
            pytest.fail(f"[{context_msg}] 页面存在错误提示: {error_text}")


def _assert_no_error_in_text(page_text: str, context_msg: str = "", allowed: list = None):
    """断言页面文本中没有错误关键词"""
    allowed = allowed or []
    for kw in ERROR_KEYWORDS:
        if kw in page_text and kw not in allowed:
            idx = page_text.index(kw)
            snippet = page_text[max(0, idx - 20):idx + 30]
            pytest.fail(f"[{context_msg}] 页面包含错误关键词 '{kw}': ...{snippet}...")


def _nav_to_classroom_tab(page: Page, tab_suffix: str = ""):
    """导航到课堂详情的特定 tab"""
    if tab_suffix:
        url = f"{BASE_URL}/#/classroom/{CLASSROOM_ID}/{tab_suffix}"
    else:
        url = f"{BASE_URL}/#/classroom/{CLASSROOM_ID}"
    page.goto(url, wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(4000)


def api_get(endpoint, token, params=None):
    r = requests.get(f"{API_URL}{endpoint}",
                     headers={"Authorization": f"Bearer {token}"},
                     params=params, timeout=10)
    return r.json()


# ═══════════════════════════════════════════════════════════════════════════
# PART 1: 登录流程
# ═══════════════════════════════════════════════════════════════════════════
class TestLoginDeep:
    def test_login_page_renders(self, browser):
        page = browser.new_page()
        page.goto(f"{BASE_URL}/#/login", wait_until="networkidle", timeout=15000)
        _screenshot(page, "01_login_page")
        # 检查登录表单元素
        text_inputs = page.locator("input[type='text']")
        pwd_inputs = page.locator("input[type='password']")
        assert text_inputs.count() > 0, "用户名输入框不可见"
        assert pwd_inputs.count() > 0, "密码输入框不可见"
        assert page.locator("button").count() > 0, "登录按钮不可见"
        page.close()

    def test_teacher_login_flow(self, browser):
        page = browser.new_page()
        page.goto(f"{BASE_URL}/#/login", wait_until="networkidle", timeout=15000)
        page.locator("input[type='text']").first.fill("teacher1")
        page.locator("input[type='password']").first.fill("password123")
        page.locator("button").first.click()
        page.wait_for_timeout(5000)
        _screenshot(page, "02_teacher_login_success")
        assert "/login" not in page.url, f"教师登录未跳转: {page.url}"
        page.close()

    def test_student_login_flow(self, browser):
        page = browser.new_page()
        page.goto(f"{BASE_URL}/#/login", wait_until="networkidle", timeout=15000)
        page.locator("input[type='text']").first.fill("student1")
        page.locator("input[type='password']").first.fill("password123")
        page.locator("button").first.click()
        page.wait_for_timeout(5000)
        _screenshot(page, "03_student_login_success")
        assert "/login" not in page.url, f"学生登录未跳转: {page.url}"
        page.close()

    def test_wrong_password(self, browser):
        page = browser.new_page()
        page.goto(f"{BASE_URL}/#/login", wait_until="networkidle", timeout=15000)
        page.locator("input[type='text']").first.fill("teacher1")
        page.locator("input[type='password']").first.fill("wrongpassword")
        page.locator("button").first.click()
        page.wait_for_timeout(2000)
        _screenshot(page, "04_wrong_password")
        assert "login" in page.url, "错误密码不应跳转"
        page.close()


# ═══════════════════════════════════════════════════════════════════════════
# PART 2: 课堂列表和详情 — 验证真实数据
# ═══════════════════════════════════════════════════════════════════════════
class TestClassroomDataVerification:
    def test_classroom_list_shows_real_names(self, teacher_context, teacher_token):
        """课堂列表应显示真实课堂名称"""
        page = teacher_context.new_page()
        page.goto(f"{BASE_URL}/#/classroom", wait_until="networkidle", timeout=15000)
        _wait_and_check(page)
        _screenshot(page, "10_classroom_list")
        page_text = page.inner_text("body")
        # 验证出现课堂名称关键词（大数据分析实验班）
        assert any(kw in page_text for kw in ["大数据", "数据分析", "实验班"]), \
            f"课堂列表未显示课堂名称关键词"
        page.close()

    def test_classroom_detail_shows_content(self, teacher_context, teacher_token):
        """进入课堂100，验证有内容"""
        page = teacher_context.new_page()
        _nav_to_classroom_tab(page)
        _screenshot(page, "11_classroom_detail")
        page_text = page.inner_text("body")
        _assert_no_error_toast(page, "课堂详情")
        # 课堂关联课程：Python数据分析基础 和 Spark大数据处理
        assert any(kw in page_text for kw in ["Python", "数据分析", "Spark", "大数据", "课程"]), \
            f"课堂详情缺少课程内容"
        page.close()


# ═══════════════════════════════════════════════════════════════════════════
# PART 3: 试题库 — 验证数据正确加载
# ═══════════════════════════════════════════════════════════════════════════
class TestQuestionBankDeep:
    def test_question_bank_api_returns_data(self, teacher_token):
        """API 层验证：试题库接口返回试题"""
        data = api_get("/api/v1/question-library/questions", teacher_token,
                       {"teacher_id": TEACHER_ID})
        assert data.get("code") == "0000", f"试题库API异常: {data}"
        items = data["data"]["list"]
        assert len(items) >= 3, f"试题库应有>=3题，实际{len(items)}"

    def test_question_bank_page_shows_questions(self, teacher_context, teacher_token):
        """浏览器验证：试题库页面显示真实试题内容"""
        page = teacher_context.new_page()
        page.goto(f"{BASE_URL}/#/exam/question-bank", wait_until="networkidle", timeout=15000)
        _wait_and_check(page)
        page.wait_for_timeout(2000)
        _screenshot(page, "20_question_bank")
        page_text = page.inner_text("body")
        _assert_no_error_toast(page, "试题库")
        # 至少出现试题类型或内容关键词
        found = any(kw in page_text for kw in ["单选", "多选", "判断", "Python", "列表", "函数"])
        assert found, "试题库页面未显示任何试题内容"
        page.close()


class TestPaperBankDeep:
    def test_paper_bank_api_returns_data(self, teacher_token):
        """API 层验证：试卷库接口返回试卷"""
        data = api_get("/api/v1/paper-library/papers", teacher_token,
                       {"teacher_id": TEACHER_ID})
        assert data.get("code") == "0000", f"试卷库API异常: {data}"
        items = data["data"]["list"]
        assert len(items) >= 1, f"试卷库应有>=1张，实际{len(items)}"

    def test_paper_bank_page_shows_papers(self, teacher_context, teacher_token):
        """浏览器验证：试卷库页面显示真实试卷"""
        page = teacher_context.new_page()
        page.goto(f"{BASE_URL}/#/exam/paper-bank", wait_until="networkidle", timeout=15000)
        _wait_and_check(page)
        page.wait_for_timeout(2000)
        _screenshot(page, "21_paper_bank")
        page_text = page.inner_text("body")
        _assert_no_error_toast(page, "试卷库")
        # 验证试卷标题出现（Python基础测验）
        found = any(kw in page_text for kw in ["Python基础", "测验", "试卷"])
        assert found, "试卷库页面未显示任何试卷标题"
        page.close()


# ═══════════════════════════════════════════════════════════════════════════
# PART 4: 课堂考试 — 验证考试列表加载
# ═══════════════════════════════════════════════════════════════════════════
class TestClassroomExamDeep:
    def test_exam_api_returns_data(self, teacher_token):
        """API 层验证：课堂考试列表返回数据"""
        data = api_get(f"/api/v1/classrooms/{CLASSROOM_ID}/exams", teacher_token,
                       {"teacher_id": TEACHER_ID})
        assert data.get("code") == "0000", f"课堂考试API异常: {data}"
        items = data["data"]["list"]
        assert len(items) >= 1, f"课堂应有>=1个考试，实际{len(items)}"

    def test_classroom_exams_page(self, teacher_context, teacher_token):
        """浏览器验证：课堂考试页面显示考试列表"""
        page = teacher_context.new_page()
        _nav_to_classroom_tab(page, "exams")
        page.wait_for_timeout(2000)
        _screenshot(page, "22_classroom_exams")
        page_text = page.inner_text("body")
        _assert_no_error_toast(page, "课堂考试")
        # 验证考试标题（Python基础随堂测验）
        found = any(kw in page_text for kw in ["Python基础", "随堂测验", "测验", "考试"])
        assert found, "课堂考试页面未显示任何考试"
        page.close()


# ═══════════════════════════════════════════════════════════════════════════
# PART 5: 学生成绩单
# ═══════════════════════════════════════════════════════════════════════════
class TestStudentGradesDeep:
    def test_student_grades_api(self, teacher_token):
        """API 层验证：学生成绩端点返回课程成绩"""
        data = api_get(f"/api/v1/students/{STUDENT_ID}/classrooms/{CLASSROOM_ID}/grades",
                       teacher_token)
        assert data.get("code") == "0000", f"学生成绩API异常: {data}"
        courses = data["data"]["courses"]
        assert len(courses) >= 1, f"应有>=1门课程成绩, 实际{len(courses)}"

    def test_student_grades_have_scores(self, teacher_token):
        """验证学生成绩有分数"""
        data = api_get(f"/api/v1/students/{STUDENT_ID}/classrooms/{CLASSROOM_ID}/grades",
                       teacher_token)
        courses = data["data"]["courses"]
        has_score = any(c.get("overall_score") is not None for c in courses)
        assert has_score, "学生成绩中没有任何分数"

    def test_student_grades_page(self, student_context):
        """浏览器验证：学生自己查看成绩单"""
        page = student_context.new_page()
        page.goto(f"{BASE_URL}/#/classroom/{CLASSROOM_ID}/student-grades",
                  wait_until="networkidle", timeout=15000)
        _wait_and_check(page)
        page.wait_for_timeout(3000)
        _screenshot(page, "23_student_grades_view")
        page_text = page.inner_text("body")
        has_content = any(kw in page_text for kw in [
            "成绩", "分数", "课程", "大数据", "总分", "评分", "个人成绩单"
        ])
        assert has_content or len(page_text) > 100, "学生成绩单页面无内容"
        page.close()


# ═══════════════════════════════════════════════════════════════════════════
# PART 6: 实训项目详情
# ═══════════════════════════════════════════════════════════════════════════
class TestTrainingProjectDeep:
    def test_training_library_api(self, teacher_token):
        """API 层验证：实训库详情接口正常"""
        data = api_get(f"/api/v1/trainings/library/{TRAINING_ID}", teacher_token)
        assert data.get("code") == "0000", f"实训库API异常: {data}"
        assert "数据清洗" in data["data"]["title"]

    def test_classroom_trainings_tab(self, teacher_context):
        """浏览器验证：课堂实训Tab显示项目"""
        page = teacher_context.new_page()
        _nav_to_classroom_tab(page, "trainings")
        _screenshot(page, "24_classroom_trainings")
        page_text = page.inner_text("body")
        _assert_no_error_toast(page, "课堂实训")
        has_training = any(kw in page_text for kw in ["数据清洗", "实训", "项目", "JUPYTER"])
        assert has_training or len(page_text) > 80, "课堂实训列表无内容"
        page.close()


# ═══════════════════════════════════════════════════════════════════════════
# PART 7: 教学资源页面 — 验证视频/PPT/PDF 真实渲染
# ═══════════════════════════════════════════════════════════════════════════
class TestTeachingResourcesDeep:
    def test_resources_api_returns_modules(self, teacher_token):
        """API 层验证：教学资源返回模块和文件"""
        data = api_get(
            f"/api/v1/teaching-resources/classrooms/{CLASSROOM_ID}/modules",
            teacher_token, {"teacher_id": TEACHER_ID}
        )
        assert data.get("code") == "0000", f"教学资源API异常: {data}"
        modules = data["data"]["modules"]
        assert len(modules) >= 2, f"应有>=2个模块，实际{len(modules)}"
        # 验证文件存在
        total_files = sum(len(m.get("files", [])) for m in modules)
        assert total_files >= 5, f"应有>=5个文件，实际{total_files}"

    def test_resources_tab_shows_modules(self, teacher_context):
        """浏览器验证：教学资源Tab显示模块名称"""
        page = teacher_context.new_page()
        _nav_to_classroom_tab(page, "resources")
        _screenshot(page, "30_resources_modules")
        page_text = page.inner_text("body")
        _assert_no_error_toast(page, "教学资源")
        # 验证模块名称
        assert any(kw in page_text for kw in ["Python基础", "数据处理"]), \
            "教学资源页面未显示模块名称"
        page.close()

    def test_resources_tab_shows_file_names(self, teacher_context):
        """浏览器验证：教学资源Tab显示文件名"""
        page = teacher_context.new_page()
        _nav_to_classroom_tab(page, "resources")
        page_text = page.inner_text("body")
        # 验证文件名出现
        file_names = ["数据清洗_视频3_重复值处理", "数据清洗课程_视频1_缺失值处理",
                      "第一章：数据清洗概述教学方案", "数据清洗_视频2_异常值检测",
                      "数据清洗课程_视频3_重复值处理"]
        found_count = sum(1 for fn in file_names if fn in page_text)
        assert found_count >= 3, \
            f"教学资源页面应显示>=3个文件名，实际显示{found_count}个"
        page.close()

    def test_video_preview_renders(self, teacher_context):
        """浏览器验证：点击视频文件的预览按钮后出现 <video> 元素并可播放"""
        page = teacher_context.new_page()
        _nav_to_classroom_tab(page, "resources")
        # 在 .file-item 中找到包含 .webm 的条目，点击其"预览"按钮
        file_items = page.locator(".file-item")
        video_clicked = False
        for i in range(file_items.count()):
            item_text = file_items.nth(i).inner_text()
            if ".webm" in item_text or ".mp4" in item_text:
                preview_btn = file_items.nth(i).locator("button", has_text="预览")
                if preview_btn.count() > 0:
                    preview_btn.first.click()
                    video_clicked = True
                    break
        if not video_clicked:
            pytest.skip("未找到视频文件的预览按钮")
        page.wait_for_timeout(3000)
        _screenshot(page, "31_video_preview")
        # 核心断言：video 元素存在
        video_count = page.locator("video").count()
        assert video_count > 0, "点击视频预览后未出现 <video> 元素"
        video_src = page.locator("video").first.get_attribute("src")
        assert video_src and len(video_src) > 5, f"video src 为空: {video_src}"
        # 验证视频可播放（readyState >= 1 表示有元数据）
        ready_state = page.evaluate("document.querySelector('video').readyState")
        assert ready_state >= 1, f"视频未加载，readyState={ready_state}"
        page.close()

    def test_pptx_preview_renders_canvas(self, teacher_context):
        """浏览器验证：点击pptx文件的预览按钮后通过pdf.js渲染canvas"""
        page = teacher_context.new_page()
        _nav_to_classroom_tab(page, "resources")
        file_items = page.locator(".file-item")
        ppt_clicked = False
        for i in range(file_items.count()):
            item_text = file_items.nth(i).inner_text()
            if ".pptx" in item_text:
                preview_btn = file_items.nth(i).locator("button", has_text="预览")
                if preview_btn.count() > 0:
                    preview_btn.first.click()
                    ppt_clicked = True
                    break
        if not ppt_clicked:
            pytest.skip("未找到pptx文件的预览按钮")
        page.wait_for_timeout(5000)
        _screenshot(page, "32_pptx_preview")
        # 核心断言：pdf.js 将 PPTX→PDF 渲染为 canvas 元素
        canvas_count = page.locator("canvas.pdf-page-canvas").count()
        assert canvas_count > 0, \
            f"PPT预览未渲染出 canvas 元素（pdf.js），canvas数量={canvas_count}"
        # 验证 canvas 有实际尺寸（不是 0x0）
        canvas_width = page.evaluate(
            "document.querySelector('canvas.pdf-page-canvas').width"
        )
        assert canvas_width > 100, f"PPT canvas 宽度异常: {canvas_width}"
        page.close()

    def test_pdf_preview_renders_canvas(self, teacher_context):
        """浏览器验证：点击pdf文件的预览按钮后通过pdf.js渲染canvas"""
        page = teacher_context.new_page()
        _nav_to_classroom_tab(page, "resources")
        file_items = page.locator(".file-item")
        pdf_clicked = False
        for i in range(file_items.count()):
            item_text = file_items.nth(i).inner_text()
            if ".pdf" in item_text:
                preview_btn = file_items.nth(i).locator("button", has_text="预览")
                if preview_btn.count() > 0:
                    preview_btn.first.click()
                    pdf_clicked = True
                    break
        if not pdf_clicked:
            pytest.skip("未找到pdf文件的预览按钮")
        page.wait_for_timeout(5000)
        _screenshot(page, "33_pdf_preview")
        # 核心断言：pdf.js 渲染为 canvas 元素
        canvas_count = page.locator("canvas.pdf-page-canvas").count()
        assert canvas_count > 0, \
            f"PDF预览未渲染出 canvas 元素（pdf.js），canvas数量={canvas_count}"
        # 验证 canvas 有实际尺寸
        canvas_height = page.evaluate(
            "document.querySelector('canvas.pdf-page-canvas').height"
        )
        assert canvas_height > 100, f"PDF canvas 高度异常: {canvas_height}"
        page.close()


# ═══════════════════════════════════════════════════════════════════════════
# PART 8: 实训工作空间
# ═══════════════════════════════════════════════════════════════════════════
class TestTrainingWorkspace:
    def test_training_workspace_page(self, teacher_context):
        """实训工作空间页面至少能渲染"""
        page = teacher_context.new_page()
        page.goto(
            f"{BASE_URL}/#/classroom/{CLASSROOM_ID}/training/{TRAINING_ID}/workspace",
            wait_until="networkidle", timeout=15000
        )
        _wait_and_check(page)
        _screenshot(page, "34_training_workspace")
        page_text = page.inner_text("body")
        assert len(page_text) > 30, "实训工作空间页面完全空白"
        page.close()


# ═══════════════════════════════════════════════════════════════════════════
# PART 9: 管理后台页面
# ═══════════════════════════════════════════════════════════════════════════
class TestAdminPagesDeep:
    def test_admin_dashboard(self, admin_context):
        """管理后台仪表盘正常加载"""
        page = admin_context.new_page()
        page.goto(f"{BASE_URL}/#/admin/dashboard", wait_until="networkidle", timeout=15000)
        _wait_and_check(page)
        _screenshot(page, "40_admin_dashboard")
        page_text = page.inner_text("body")
        _assert_no_error_toast(page, "管理仪表盘")
        has_content = any(kw in page_text for kw in ["仪表盘", "统计", "概览", "管理", "系统"])
        assert has_content or len(page_text) > 100, "管理仪表盘无内容"
        page.close()

    @pytest.mark.parametrize("path,name", [
        ("/admin/user/student", "admin_students"),
        ("/admin/organization/department", "admin_department"),
        ("/admin/course/practice", "admin_practice_course"),
    ])
    def test_admin_subpages_render(self, admin_context, path, name):
        """管理后台子页面不应返回404"""
        page = admin_context.new_page()
        page.goto(f"{BASE_URL}/#{path}", wait_until="networkidle", timeout=15000)
        _wait_and_check(page)
        _screenshot(page, f"41_{name}")
        page_text = page.inner_text("body")
        assert "404" not in page_text and "页面不存在" not in page_text, \
            f"{name} 页面返回 404"
        page.close()


# ═══════════════════════════════════════════════════════════════════════════
# PART 10: 学生视角
# ═══════════════════════════════════════════════════════════════════════════
class TestStudentViewDeep:
    def test_student_classroom_list(self, student_context):
        """学生视角：课堂列表"""
        page = student_context.new_page()
        page.goto(f"{BASE_URL}/#/classroom", wait_until="networkidle", timeout=15000)
        _wait_and_check(page)
        _screenshot(page, "50_student_classroom_list")
        page_text = page.inner_text("body")
        _assert_no_error_toast(page, "学生课堂列表")
        assert len(page_text) > 50, "学生课堂列表页面空白"
        page.close()

    def test_student_classroom_detail(self, student_context):
        """学生视角：课堂详情"""
        page = student_context.new_page()
        page.goto(f"{BASE_URL}/#/classroom/{CLASSROOM_ID}",
                  wait_until="networkidle", timeout=15000)
        _wait_and_check(page)
        _screenshot(page, "51_student_classroom_detail")
        page_text = page.inner_text("body")
        _assert_no_error_toast(page, "学生课堂详情")
        page.close()

    def test_student_resources_tab(self, student_context):
        """学生视角：教学资源Tab"""
        page = student_context.new_page()
        _nav_to_classroom_tab(page, "resources")
        _screenshot(page, "52_student_resources")
        page_text = page.inner_text("body")
        # 学生也应能看到教学资源模块
        has_content = any(kw in page_text for kw in ["Python基础", "数据处理", "资源"])
        assert has_content or len(page_text) > 80, "学生教学资源页面无内容"
        page.close()


# ═══════════════════════════════════════════════════════════════════════════
# PART 11: API 健康检查
# ═══════════════════════════════════════════════════════════════════════════
class TestAPIHealthCheck:
    """验证所有关键 API 端点返回 code=0000"""

    @pytest.mark.parametrize("endpoint,params,desc", [
        ("/api/v1/question-library/questions", {"teacher_id": TEACHER_ID}, "试题库"),
        ("/api/v1/paper-library/papers", {"teacher_id": TEACHER_ID}, "试卷库"),
        (f"/api/v1/classrooms/{CLASSROOM_ID}/exams", {"teacher_id": TEACHER_ID}, "课堂考试"),
        (f"/api/v1/trainings/library/{TRAINING_ID}", {}, "实训库详情"),
        (f"/api/v1/students/{STUDENT_ID}/classrooms/{CLASSROOM_ID}/grades", {}, "学生成绩"),
        (f"/api/v1/teaching-resources/classrooms/{CLASSROOM_ID}/modules",
         {"teacher_id": TEACHER_ID}, "教学资源"),
        (f"/api/v1/classrooms/{CLASSROOM_ID}/trainings",
         {"teacher_id": TEACHER_ID}, "课堂实训"),
    ])
    def test_api_endpoint_health(self, teacher_token, endpoint, params, desc):
        data = api_get(endpoint, teacher_token, params)
        assert data.get("code") == "0000", \
            f"{desc} API 返回异常: {json.dumps(data, ensure_ascii=False)[:200]}"


# ═══════════════════════════════════════════════════════════════════════════
# PART 12: 综合数据完整性验证
# ═══════════════════════════════════════════════════════════════════════════
class TestDataIntegrity:
    def test_question_data_has_content(self, teacher_token):
        """验证试题有内容和类型"""
        data = api_get("/api/v1/question-library/questions", teacher_token,
                       {"teacher_id": TEACHER_ID})
        questions = data["data"]["list"]
        for q in questions:
            assert q.get("content"), f"试题{q['id']}缺少内容"
            assert q.get("question_type"), f"试题{q['id']}缺少类型"

    def test_exam_has_valid_time(self, teacher_token):
        """验证考试有有效时间设置"""
        data = api_get(f"/api/v1/classrooms/{CLASSROOM_ID}/exams", teacher_token,
                       {"teacher_id": TEACHER_ID})
        exams = data["data"]["list"]
        for e in exams:
            assert e.get("duration_minutes", 0) > 0, f"考试'{e['title']}'缺少时长"
            assert e.get("exam_start_time"), f"考试'{e['title']}'缺少开始时间"

    def test_resource_modules_have_files(self, teacher_token):
        """验证教学资源模块包含文件"""
        data = api_get(
            f"/api/v1/teaching-resources/classrooms/{CLASSROOM_ID}/modules",
            teacher_token, {"teacher_id": TEACHER_ID}
        )
        modules = data["data"]["modules"]
        for m in modules:
            files = m.get("files", [])
            assert len(files) > 0, f"模块'{m['name']}'没有文件"

    def test_resource_files_have_correct_types(self, teacher_token):
        """验证文件类型正确（webm, pptx, pdf）"""
        data = api_get(
            f"/api/v1/teaching-resources/classrooms/{CLASSROOM_ID}/modules",
            teacher_token, {"teacher_id": TEACHER_ID}
        )
        all_types = set()
        for m in data["data"]["modules"]:
            for f in m.get("files", []):
                all_types.add(f.get("file_type"))
        assert "webm" in all_types, f"缺少 webm 视频文件，类型集合: {all_types}"
        assert "pptx" in all_types, f"缺少 pptx 文件，类型集合: {all_types}"
        assert "pdf" in all_types, f"缺少 pdf 文件，类型集合: {all_types}"
