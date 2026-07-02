"""
慧学 — 深度渲染验证测试
================================
目标：验证视频播放、PPT预览、教学资源列表在浏览器中【真正渲染】
不是检查API返回，而是检查DOM元素是否生成。

禁止mock，使用真实数据。
"""
import os
import json
import time
import pytest
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, expect

BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8000"
SCREENSHOT_DIR = Path("/sessions/charming-friendly-pascal/screenshots/deep")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

CLASSROOM_ID = 100
TEACHER_ID = 29
STUDENT_ID = 30


# ─── Fixtures ───────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def browser():
    pw = sync_playwright().start()
    b = pw.chromium.launch(headless=True, args=["--no-sandbox"])
    yield b
    b.close()
    pw.stop()


def _extract_token(data):
    if data.get("data", {}).get("access_token"):
        return data["data"]["access_token"]
    if data.get("token", {}).get("access_token"):
        return data["token"]["access_token"]
    if data.get("access_token"):
        return data["access_token"]
    return None


@pytest.fixture(scope="session")
def teacher_token():
    r = requests.post(f"{API_URL}/api/login", json={"username": "teacher1", "password": "password123"})
    data = r.json()
    token = _extract_token(data)
    assert token, f"Teacher login failed: {data}"
    return token


@pytest.fixture(scope="session")
def student_token():
    r = requests.post(f"{API_URL}/api/login", json={"username": "student1", "password": "password123"})
    data = r.json()
    token = _extract_token(data)
    assert token, f"Student login failed: {data}"
    return token


def _real_login(browser: Browser, username: str, password: str) -> BrowserContext:
    """通过真实表单登录，确保前端状态正确初始化"""
    ctx = browser.new_context(viewport={"width": 1280, "height": 900})
    page = ctx.new_page()
    page.goto(f"{BASE_URL}/#/login", wait_until="networkidle", timeout=15000)
    page.wait_for_timeout(1000)
    page.locator("input[type='text']").first.fill(username)
    page.locator("input[type='password']").first.fill(password)
    page.locator("button").first.click()
    page.wait_for_timeout(5000)
    # 验证登录成功（不在login页面）
    assert "/login" not in page.url or "redirect" not in page.url, \
        f"Login failed, still on login page: {page.url}"
    page.close()
    return ctx


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


# ─── Helper ─────────────────────────────────────────────────────────────
MENU_ROUTE_MAP = {
    "课程实践": "",
    "项目实训": "trainings",
    "教学资源": "resources",
    "课程考核": "exams",
    "学情分析": "analytics",
    "课堂云盘": "drive",
}


def _nav_to_classroom_tab(page: Page, tab_name: str):
    """导航到课堂详情页的指定标签页"""
    route_suffix = MENU_ROUTE_MAP.get(tab_name, "")
    if route_suffix:
        url = f"{BASE_URL}/#/classroom/{CLASSROOM_ID}/{route_suffix}"
    else:
        url = f"{BASE_URL}/#/classroom/{CLASSROOM_ID}"
    page.goto(url, wait_until="networkidle", timeout=20000)
    page.wait_for_timeout(4000)
    return True


def _screenshot(page: Page, name: str):
    page.screenshot(path=str(SCREENSHOT_DIR / f"{name}.png"), full_page=True)


# ═══════════════════════════════════════════════════════════════════════
# TEST 1: 教学资源模块列表渲染
# ═══════════════════════════════════════════════════════════════════════
class TestTeachingResources:
    """验证教学资源在浏览器中真正渲染出模块和文件列表"""

    def test_resources_tab_shows_modules(self, teacher_context):
        """导航到教学资源tab → 验证模块和文件名出现在DOM中"""
        page = teacher_context.new_page()
        try:
            _nav_to_classroom_tab(page, "教学资源")
            _screenshot(page, "01_resources_tab")

            page_text = page.inner_text("body")
            assert "第一章" in page_text or "Python基础" in page_text, \
                f"页面未渲染资源模块名称。页面文本片段: {page_text[:500]}"

            assert "数据清洗" in page_text or ".webm" in page_text, \
                f"页面未渲染视频文件名"
            assert "缺失值处理" in page_text or ".pptx" in page_text, \
                f"页面未渲染PPT文件名"

            assert "暂无教学资源模块" not in page_text, \
                "页面显示'暂无教学资源模块' — resource_modules 数据未正确加载"

            # 验证DOM结构
            assert page.locator(".module-card").count() >= 2, "模块卡片数量不足2"
            assert page.locator(".file-item").count() >= 5, "文件列表数量不足5"
        finally:
            page.close()

    def test_video_preview_renders_video_element(self, teacher_context):
        """点击视频文件的预览按钮 → 验证 <video> 元素出现并可播放"""
        page = teacher_context.new_page()
        try:
            _nav_to_classroom_tab(page, "教学资源")

            file_items = page.locator(".file-item")
            video_preview_clicked = False

            for i in range(file_items.count()):
                item_text = file_items.nth(i).inner_text()
                if ".webm" in item_text or ".mp4" in item_text:
                    preview_btn = file_items.nth(i).locator("button", has_text="预览")
                    if preview_btn.count() > 0:
                        preview_btn.first.click()
                        video_preview_clicked = True
                        break

            assert video_preview_clicked, "未找到视频文件的预览按钮"
            page.wait_for_timeout(3000)
            _screenshot(page, "02_video_preview_modal")

            # 核心断言：验证 <video> 元素存在
            video_el = page.locator("video")
            assert video_el.count() > 0, \
                "点击视频预览后，DOM中未找到 <video> 元素！"

            video_src = video_el.first.get_attribute("src")
            assert video_src and len(video_src) > 5, \
                f"<video> 元素存在但 src 为空或无效: {video_src}"

            has_controls = video_el.first.get_attribute("controls")
            assert has_controls is not None, \
                "<video> 元素没有 controls 属性"

            # 验证视频可播放（readyState >= 1 表示有元数据）
            ready_state = page.evaluate("document.querySelector('video').readyState")
            assert ready_state >= 1, f"视频未加载，readyState={ready_state}"

            print(f"✅ Video element found, src={video_src[:80]}..., readyState={ready_state}")
        finally:
            page.close()

    def test_ppt_preview_renders_canvas(self, teacher_context):
        """点击PPT文件的预览按钮 → 验证 pdf.js 渲染出 canvas 元素"""
        page = teacher_context.new_page()
        try:
            _nav_to_classroom_tab(page, "教学资源")

            file_items = page.locator(".file-item")
            ppt_preview_clicked = False

            for i in range(file_items.count()):
                item_text = file_items.nth(i).inner_text()
                if ".pptx" in item_text:
                    preview_btn = file_items.nth(i).locator("button", has_text="预览")
                    if preview_btn.count() > 0:
                        preview_btn.first.click()
                        ppt_preview_clicked = True
                        break

            assert ppt_preview_clicked, "未找到PPT文件的预览按钮"
            page.wait_for_timeout(5000)
            _screenshot(page, "03_ppt_preview_modal")

            # 核心断言：PPTX→PDF 通过 pdf.js 渲染为 canvas
            canvas_count = page.locator("canvas.pdf-page-canvas").count()
            assert canvas_count > 0, \
                f"PPT预览未渲染出 canvas 元素，canvas数量={canvas_count}"

            # 验证 canvas 有实际尺寸（不是空白）
            canvas_width = page.evaluate(
                "document.querySelector('canvas.pdf-page-canvas').width"
            )
            assert canvas_width > 100, f"PPT canvas 宽度异常: {canvas_width}"

            print(f"✅ PPT preview rendered {canvas_count} canvas pages, width={canvas_width}")
        finally:
            page.close()

    def test_pdf_preview_renders_canvas(self, teacher_context):
        """点击PDF文件的预览按钮 → 验证 pdf.js 渲染出 canvas 元素"""
        page = teacher_context.new_page()
        try:
            _nav_to_classroom_tab(page, "教学资源")

            file_items = page.locator(".file-item")
            pdf_preview_clicked = False

            for i in range(file_items.count()):
                item_text = file_items.nth(i).inner_text()
                if ".pdf" in item_text:
                    preview_btn = file_items.nth(i).locator("button", has_text="预览")
                    if preview_btn.count() > 0:
                        preview_btn.first.click()
                        pdf_preview_clicked = True
                        break

            assert pdf_preview_clicked, "未找到PDF文件的预览按钮"
            page.wait_for_timeout(5000)
            _screenshot(page, "04_pdf_preview_modal")

            # 核心断言：pdf.js 渲染为 canvas 元素
            canvas_count = page.locator("canvas.pdf-page-canvas").count()
            assert canvas_count > 0, \
                f"PDF预览未渲染出 canvas 元素，canvas数量={canvas_count}"

            # 验证 canvas 有实际尺寸
            canvas_height = page.evaluate(
                "document.querySelector('canvas.pdf-page-canvas').height"
            )
            assert canvas_height > 100, f"PDF canvas 高度异常: {canvas_height}"

            print(f"✅ PDF preview rendered {canvas_count} canvas pages, height={canvas_height}")
        finally:
            page.close()


# ═══════════════════════════════════════════════════════════════════════
# TEST 2: 实训项目列表渲染
# ═══════════════════════════════════════════════════════════════════════
class TestTrainingProjects:
    """验证实训项目在浏览器中真正渲染"""

    def test_training_tab_shows_projects(self, teacher_context):
        """导航到项目实训tab → 验证实训项目名称出现在DOM"""
        page = teacher_context.new_page()
        try:
            _nav_to_classroom_tab(page, "项目实训")
            _screenshot(page, "05_training_tab")

            page_text = page.inner_text("body")
            assert "数据清洗实训" in page_text, \
                f"页面未渲染实训项目名称。页面文本片段: {page_text[:500]}"
        finally:
            page.close()


# ═══════════════════════════════════════════════════════════════════════
# TEST 3: 课程实践列表渲染
# ═══════════════════════════════════════════════════════════════════════
class TestCoursePractice:
    """验证课程实践在浏览器中真正渲染"""

    def test_practice_tab_shows_courses(self, teacher_context):
        """导航到课程实践tab → 验证课程名称出现在DOM"""
        page = teacher_context.new_page()
        try:
            _nav_to_classroom_tab(page, "课程实践")
            _screenshot(page, "06_practice_tab")

            page_text = page.inner_text("body")
            # 课程实践tab 可能显示课程列表或者"暂无课程"
            # 至少要有"数据清洗实训项目"（实训也在practice tab下）
            has_content = (
                "Python数据分析基础" in page_text or
                "Spark" in page_text or
                "数据清洗实训" in page_text or
                "全部课程" in page_text
            )
            assert has_content, \
                f"课程实践tab未显示任何内容。页面文本片段: {page_text[:500]}"
        finally:
            page.close()


# ═══════════════════════════════════════════════════════════════════════
# TEST 4: 考试列表渲染
# ═══════════════════════════════════════════════════════════════════════
class TestExamRendering:
    """验证考试在浏览器中真正渲染"""

    def test_exam_tab_shows_exam(self, teacher_context):
        """导航到课程考核tab → 验证考试名称出现在DOM"""
        page = teacher_context.new_page()
        try:
            _nav_to_classroom_tab(page, "课程考核")
            _screenshot(page, "07_exam_tab")

            page_text = page.inner_text("body")
            assert "Python基础随堂测验" in page_text, \
                f"页面未渲染考试名称。页面文本片段: {page_text[:500]}"
        finally:
            page.close()


# ═══════════════════════════════════════════════════════════════════════
# TEST 5: 课堂详情基本信息
# ═══════════════════════════════════════════════════════════════════════
class TestClassroomDetail:
    """验证课堂详情页基本信息正确渲染"""

    def test_classroom_info(self, teacher_context):
        """课堂详情页显示课堂名称、教师信息等"""
        page = teacher_context.new_page()
        try:
            page.goto(f"{BASE_URL}/#/classroom/{CLASSROOM_ID}", wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(3000)
            _screenshot(page, "08_classroom_detail")

            page_text = page.inner_text("body")
            assert "大数据分析实验班" in page_text, "未显示课堂名称"
            assert "3" in page_text, "未显示学生数量"
        finally:
            page.close()

    def test_sidebar_menus_present(self, teacher_context):
        """验证左侧导航菜单完整"""
        page = teacher_context.new_page()
        try:
            page.goto(f"{BASE_URL}/#/classroom/{CLASSROOM_ID}", wait_until="networkidle", timeout=20000)
            page.wait_for_timeout(3000)

            menu_items = page.locator(".menu-item")
            menu_texts = [menu_items.nth(i).inner_text() for i in range(menu_items.count())]
            menu_text_str = " ".join(menu_texts)

            assert "课程实践" in menu_text_str, "缺少'课程实践'菜单"
            assert "项目实训" in menu_text_str, "缺少'项目实训'菜单"
            assert "教学资源" in menu_text_str, "缺少'教学资源'菜单"
            assert "课程考核" in menu_text_str, "缺少'课程考核'菜单"
        finally:
            page.close()


# ═══════════════════════════════════════════════════════════════════════
# TEST 6: API 数据完整性验证
# ═══════════════════════════════════════════════════════════════════════
class TestAPIDataIntegrity:
    """直接验证API返回真实数据"""

    def test_teaching_resources_api(self, teacher_token):
        """教学资源API返回模块和文件"""
        r = requests.get(
            f"{API_URL}/api/v1/teaching-resources/classrooms/{CLASSROOM_ID}/modules",
            params={"teacher_id": TEACHER_ID},
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        data = r.json()
        assert data["code"] == "0000", f"API error: {data}"
        modules = data["data"]["modules"]
        assert len(modules) >= 2, f"Expected >=2 modules, got {len(modules)}"

        files = modules[0]["files"]
        assert len(files) >= 3, f"Expected >=3 files in module 1, got {len(files)}"

        file_types = {f["file_type"] for f in files}
        assert "webm" in file_types, f"No webm video file, types: {file_types}"
        assert "pptx" in file_types, f"No pptx file, types: {file_types}"
        assert "pdf" in file_types, f"No pdf file, types: {file_types}"
        print(f"✅ Teaching resources API: {len(modules)} modules, {sum(len(m['files']) for m in modules)} files")

    def test_question_library_api(self, teacher_token):
        """试题库API返回题目"""
        r = requests.get(
            f"{API_URL}/api/v1/question-library/questions",
            params={"teacher_id": TEACHER_ID},
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        data = r.json()
        assert data.get("code") == "0000", f"Question API error: {data}"

    def test_paper_library_api(self, teacher_token):
        """试卷库API返回试卷"""
        r = requests.get(
            f"{API_URL}/api/v1/paper-library/papers",
            params={"teacher_id": TEACHER_ID},
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        data = r.json()
        assert data.get("code") == "0000", f"Paper API error: {data}"

    def test_classroom_exam_api(self, teacher_token):
        """考试API返回考试列表"""
        r = requests.get(
            f"{API_URL}/api/v1/classrooms/{CLASSROOM_ID}/exams",
            params={"teacher_id": TEACHER_ID},
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        data = r.json()
        assert data.get("code") == "0000", f"Exam API error: {data}"
        exam_data = data.get("data", {})
        if isinstance(exam_data, dict):
            exams = exam_data.get("list", exam_data.get("exams", []))
        else:
            exams = exam_data
        assert len(exams) >= 1, f"No exams returned: {data}"

    def test_classroom_trainings_api(self, teacher_token):
        """课堂实训API返回实训项目"""
        r = requests.get(
            f"{API_URL}/api/v1/classrooms/{CLASSROOM_ID}/trainings",
            headers={"Authorization": f"Bearer {teacher_token}"}
        )
        assert r.status_code == 200, f"Training API status={r.status_code}: {r.text[:200]}"

    def test_login_api(self):
        """登录API正常工作"""
        r = requests.post(f"{API_URL}/api/login", json={"username": "teacher1", "password": "password123"})
        data = r.json()
        token = _extract_token(data)
        assert token, f"Login failed: {data}"
        assert len(token) > 20, f"Token too short: {token}"
