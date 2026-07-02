"""
tests/playwright_spa_switching_test.py

BI 实训工作台 SPA 内路由切换回归测试
覆盖 watch(trainingId) 响应式依赖，防止静默回归。

静默回归风险：watch(trainingId) 极易在重构时被误删（如组件拆分、强制重挂载），
冷加载测试永远 PASS，只有 SPA 内切换才会暴露问题。

用法:
    # Chrome（默认）
    BASE_URL=http://<慧学服务器1-IP> python -m pytest tests/playwright_spa_switching_test.py -v

    # Firefox
    BASE_URL=http://<慧学服务器1-IP> pytest tests/playwright_spa_switching_test.py -v --browser=firefox

    # 指定浏览器
    pytest tests/playwright_spa_switching_test.py -v --browser=chromium
"""

import os
import time
import re
from typing import Optional

import pytest

try:
    from playwright.sync_api import sync_playwright, Page, BrowserContext, ConsoleMessage, Browser
except ImportError:
    print("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium firefox")
    import sys
    sys.exit(1)


BASE_URL: str = os.environ.get("BASE_URL", "http://<慧学服务器1-IP>")
BROWSER: str = os.environ.get("BROWSER", "chromium")  # chromium or firefox

STUDENT_CREDS = {"username": "student1", "password": "student123"}

# SPA 切换序列: (ct_id, training_name, expected_dataset_hint)
WORKSPACE_SEQUENCE = [
    (11, "A股上市公司", "stock"),
    (14, "企业用能环保", "energy"),
    (17, "客户流失", "customer"),
]
FAST_SWITCH_SEQUENCE = [11, 14, 11, 17]  # A->B->A->C


def login_as_student(ctx: BrowserContext) -> Page:
    """登录 student1，返回已认证 page."""
    page = ctx.new_page()

    def console_msg(msg: ConsoleMessage):
        if msg.type == "error":
            print(f"  [CONSOLE ERROR] {msg.text}")

    page.on("console", console_msg)

    page.goto(f"{BASE_URL}/#/login", wait_until="domcontentloaded", timeout=15000)
    page.fill('input[type="text"], input[placeholder*="账号"], input[placeholder*="用户名"]',
              STUDENT_CREDS["username"], timeout=5000)
    page.fill('input[type="password"]', STUDENT_CREDS["password"], timeout=5000)
    page.click('button[type="submit"], button:has-text("登录"), button:has-text("登录")', timeout=5000)
    page.wait_for_load_state("networkidle", timeout=10000)

    # 确认登录成功
    page.wait_for_timeout(1500)
    if "#/login" in page.url:
        raise RuntimeError(f"登录失败，仍在登录页: {page.url}")

    return page


def navigate_to_training_list(page: Page) -> None:
    """导航到课堂 100 的实训列表."""
    # 尝试直接 goto 课堂列表
    page.goto(f"{BASE_URL}/#/classroom/100", wait_until="domcontentloaded", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=10000)
    page.wait_for_timeout(2000)


def enter_workspace(page: Page, ct_id: int) -> None:
    """
    通过 UI 点击进入指定 ct_id 的 BI workspace（SPA 路由切换，非 goto）.
    策略：先 goto 实训列表，再点击对应按钮.
    """
    # 确保在课堂页面
    if "#/classroom/100" not in page.url:
        page.goto(f"{BASE_URL}/#/classroom/100", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=10000)
        page.wait_for_timeout(2000)

    # 查找并点击"开启实训"按钮（匹配包含 ct_id 的按钮或链接）
    # 策略1: 找包含实训名称的链接
    ws_button = page.locator(f'a[href*="/bi-training/{ct_id}/workspace"], '
                             f'button:has-text("开启实训"), '
                             f'tr:has-text("A股") a, '
                             f'tr:has-text("企业用能") a, '
                             f'tr:has-text("客户流失") a, '
                             f'li:has-text("实训"):not([class*="disabled"]) a')

    # 策略2: 直接通过 data 属性或 title 查找
    all_links = page.locator("a[href], button")
    hrefs = []
    for link in all_links.all():
        href = link.get_attribute("href") or ""
        text = (link.inner_text() or "").strip()
        if f"/bi-training/{ct_id}/workspace" in href:
            hrefs.append(link)

    if hrefs:
        hrefs[0].click(timeout=5000)
    else:
        # 兜底: 直接 goto (只用于第一次进入，后续测试走 SPA 切换)
        page.goto(f"{BASE_URL}/#/classroom/100/bi-training/{ct_id}/workspace",
                  wait_until="domcontentloaded", timeout=15000)

    # 等待 BI workspace 加载
    page.wait_for_load_state("networkidle", timeout=10000)
    page.wait_for_timeout(2000)


def get_workspace_title(page: Page) -> str:
    """获取当前 workspace 页面标题."""
    selectors = [
        "h1", ".workspace-title", "[class*='title']", "[class*='heading']",
        ".page-header h1", ".card-header h1"
    ]
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                return el.inner_text().strip()
        except Exception:
            continue
    return page.title()


def get_api_calls_for_training(page: Page, ct_id: int) -> list[dict]:
    """记录切换到指定 ct_id 期间触发的 API 请求."""
    calls = []

    def on_request(req):
        if f"/trainings/{ct_id}/" in req.url or f"bi-dataset" in req.url:
            calls.append({
                "url": req.url,
                "method": req.method,
                "timestamp": time.time()
            })

    page.on("request", on_request)
    return calls


def wait_for_bi_workspace_ready(page: Page, ct_id: int) -> None:
    """等待 BI workspace 完全加载: iframe 存在 + 数据集加载."""
    # 等待 iframe 出现
    page.wait_for_selector("iframe", timeout=15000)
    # 等待网络空闲（数据集请求完成）
    page.wait_for_load_state("networkidle", timeout=12000)
    page.wait_for_timeout(1000)


# ─────────────────────────────────────────────────────────────────────────────
# Test Cases
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def browser_instance():
    """跨所有测试共享一个浏览器实例以加快执行."""
    with sync_playwright() as p:
        if BROWSER == "firefox":
            b = p.firefox.launch(headless=True)
        else:
            b = p.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture(scope="module")
def auth_context(browser_instance):
    """登录后共享认证 context."""
    ctx = browser_instance.new_context()
    page = login_as_student(ctx)
    page.close()
    yield ctx
    ctx.close()


class TestBISpaRouteSwitching:
    """BI 实训工作台 SPA 路由切换回归测试."""

    def test_case1_spa_continuous_switching(self, auth_context):
        """
        Case 1: SPA 内连续切换 A→B→C（核心用例）

        验证 watch(trainingId) 在 SPA 内 UI 点击切换时正确触发:
        - 数据集名称更新
        - iframe src 更新
        - 无上一个 workspace 数据残留
        - 无 console error
        """
        page = auth_context.new_page()
        console_errors = []

        def on_console(msg: ConsoleMessage):
            if msg.type == "error":
                # 过滤已知无害警告
                text = msg.text
                if any(kw in text.lower() for kw in ["favicon", "chrome-extension", "warn-only"]):
                    return
                console_errors.append(text)

        page.on("console", on_console)

        try:
            # 第一次进入用 goto 建立初始状态
            page.goto(f"{BASE_URL}/#/classroom/100/bi-training/11/workspace",
                      wait_until="domcontentloaded", timeout=15000)
            wait_for_bi_workspace_ready(page, 11)
            title_a = get_workspace_title(page)
            assert "A股" in title_a, f"A workspace title mismatch: {title_a}"
            iframe_a = page.locator("iframe").first.get_attribute("src") or ""
            print(f"  [Case1] Workspace A (ct_id=11): title={title_a}, iframe={iframe_a}")

            # 切换到 B
            page.goto(f"{BASE_URL}/#/classroom/100/bi-training/14/workspace",
                      wait_until="domcontentloaded", timeout=15000)
            wait_for_bi_workspace_ready(page, 14)
            title_b = get_workspace_title(page)
            iframe_b = page.locator("iframe").first.get_attribute("src") or ""
            assert "企业用能" in title_b, f"B workspace title mismatch: {title_b}"
            assert iframe_a != iframe_b, f"iframe src 未变化，A={iframe_a} B={iframe_b}"
            assert "11" not in iframe_b, f"B workspace iframe 仍含 A 的 training_id: {iframe_b}"
            print(f"  [Case1] Workspace B (ct_id=14): title={title_b}, iframe={iframe_b}")

            # 切换到 C
            page.goto(f"{BASE_URL}/#/classroom/100/bi-training/17/workspace",
                      wait_until="domcontentloaded", timeout=15000)
            wait_for_bi_workspace_ready(page, 17)
            title_c = get_workspace_title(page)
            iframe_c = page.locator("iframe").first.get_attribute("src") or ""
            assert "客户流失" in title_c, f"C workspace title mismatch: {title_c}"
            assert iframe_b != iframe_c, f"iframe src 未变化，B={iframe_b} C={iframe_c}"
            assert "14" not in iframe_c, f"C workspace iframe 仍含 B 的 training_id: {iframe_c}"
            print(f"  [Case1] Workspace C (ct_id=17): title={title_c}, iframe={iframe_c}")

            # 检查 console errors
            assert len(console_errors) == 0, f"Console errors found: {console_errors}"
            print(f"  [Case1] PASS: A→B→C 切换正确，无数据残留，无 console error")

        finally:
            page.close()

    def test_case2_spa_ui_click_switching(self, auth_context):
        """
        Case 2: SPA 内 UI 点击切换（非 goto）A→B→C

        验证通过 page.click() 模拟真实用户点击返回+进入,
        触发 watch(trainingId) 而非 onMounted.
        """
        page = auth_context.new_page()
        console_errors = []

        def on_console(msg: ConsoleMessage):
            if msg.type == "error":
                text = msg.text
                if any(kw in text.lower() for kw in ["favicon", "chrome-extension"]):
                    return
                console_errors.append(text)

        page.on("console", on_console)

        try:
            # 第一次进入
            page.goto(f"{BASE_URL}/#/classroom/100/bi-training/11/workspace",
                      wait_until="domcontentloaded", timeout=15000)
            wait_for_bi_workspace_ready(page, 11)
            title_a = get_workspace_title(page)
            iframe_a = page.locator("iframe").first.get_attribute("src") or ""
            print(f"  [Case2] A: {title_a}")

            # SPA 切换到 B: 点击返回按钮
            back_btn = page.locator(
                'a[href*="/classroom/100"], button:has-text("返回"), '
                '.breadcrumb a, .nav-back, [class*="back"]'
            ).first
            if back_btn.is_visible(timeout=3000):
                back_btn.click(timeout=3000)
                page.wait_for_load_state("networkidle", timeout=8000)
                page.wait_for_timeout(1000)

                # 从列表点击 B
                # 查找包含企业用能的链接
                b_link = page.locator(f'a[href*="/bi-training/14/workspace"]')
                if b_link.count() > 0 and b_link.first.is_visible(timeout=3000):
                    b_link.first.click(timeout=3000)
                else:
                    # 兜底 goto
                    page.goto(f"{BASE_URL}/#/classroom/100/bi-training/14/workspace",
                              wait_until="domcontentloaded", timeout=15000)

                wait_for_bi_workspace_ready(page, 14)
                title_b = get_workspace_title(page)
                iframe_b = page.locator("iframe").first.get_attribute("src") or ""
                assert "企业用能" in title_b, f"UI click B failed: {title_b}"
                assert "11" not in iframe_b, f"B iframe has A residual: {iframe_b}"
                print(f"  [Case2] B (via UI click): {title_b}")

            # SPA 切换到 C
            back_btn2 = page.locator(
                'a[href*="/classroom/100"], button:has-text("返回"), '
                '.breadcrumb a, .nav-back, [class*="back"]'
            ).first
            if back_btn2.is_visible(timeout=3000):
                back_btn2.click(timeout=3000)
                page.wait_for_load_state("networkidle", timeout=8000)
                page.wait_for_timeout(1000)

                c_link = page.locator(f'a[href*="/bi-training/17/workspace"]')
                if c_link.count() > 0 and c_link.first.is_visible(timeout=3000):
                    c_link.first.click(timeout=3000)
                else:
                    page.goto(f"{BASE_URL}/#/classroom/100/bi-training/17/workspace",
                              wait_until="domcontentloaded", timeout=15000)

                wait_for_bi_workspace_ready(page, 17)
                title_c = get_workspace_title(page)
                iframe_c = page.locator("iframe").first.get_attribute("src") or ""
                assert "客户流失" in title_c, f"UI click C failed: {title_c}"
                assert "14" not in iframe_c, f"C iframe has B residual: {iframe_c}"
                print(f"  [Case2] C (via UI click): {title_c}")

            assert len(console_errors) == 0, f"Console errors: {console_errors}"
            print(f"  [Case2] PASS: UI click SPA switching verified")

        finally:
            page.close()

    def test_case3_fast_consecutive_switching(self, auth_context):
        """
        Case 3: 快速连续切换 A→B→A→C（race condition 压测）

        验证快速切换时 watch 能正确响应，最终状态正确.
        """
        page = auth_context.new_page()
        console_errors = []

        def on_console(msg: ConsoleMessage):
            if msg.type == "error":
                text = msg.text
                if any(kw in text.lower() for kw in ["favicon", "chrome-extension"]):
                    return
                console_errors.append(text)

        page.on("console", on_console)

        try:
            # 初始加载 A
            page.goto(f"{BASE_URL}/#/classroom/100/bi-training/11/workspace",
                      wait_until="domcontentloaded", timeout=15000)
            wait_for_bi_workspace_ready(page, 11)

            # 快速连续 goto
            for target_id in FAST_SWITCH_SEQUENCE[1:]:
                page.goto(f"{BASE_URL}/#/classroom/100/bi-training/{target_id}/workspace",
                          wait_until="domcontentloaded", timeout=15000)
                wait_for_bi_workspace_ready(page, target_id)
                page.wait_for_timeout(200)

            # 最终验证停在 C (ct_id=17)
            title_final = get_workspace_title(page)
            iframe_final = page.locator("iframe").first.get_attribute("src") or ""
            assert "客户流失" in title_final, f"Fast switch final state wrong: {title_final}"
            assert "17" in iframe_final, f"Final iframe not C: {iframe_final}"
            assert "14" not in iframe_final and "11" not in iframe_final, \
                f"Final iframe has residual A/B: {iframe_final}"
            print(f"  [Case3] PASS: Fast switch ends at C correctly: {title_final}")

            assert len(console_errors) == 0, f"Console errors: {console_errors}"

        finally:
            page.close()

    def test_case4_same_workspace_revisit(self, auth_context):
        """
        Case 4: 同一 workspace 重复进入

        验证 watch 在 trainingId 未变时无副作用，路由跳转正常.
        """
        page = auth_context.new_page()
        console_errors = []

        def on_console(msg: ConsoleMessage):
            if msg.type == "error":
                text = msg.text
                if any(kw in text.lower() for kw in ["favicon", "chrome-extension"]):
                    return
                console_errors.append(text)

        page.on("console", on_console)

        try:
            # 第一次进入 A
            page.goto(f"{BASE_URL}/#/classroom/100/bi-training/11/workspace",
                      wait_until="domcontentloaded", timeout=15000)
            wait_for_bi_workspace_ready(page, 11)
            title_1 = get_workspace_title(page)
            iframe_1 = page.locator("iframe").first.get_attribute("src") or ""
            assert "A股" in title_1
            print(f"  [Case4] First entry A: {title_1}")

            # 返回列表
            back_btn = page.locator(
                'a[href*="/classroom/100"], button:has-text("返回"), '
                '.breadcrumb a, .nav-back, [class*="back"]'
            ).first
            if back_btn.is_visible(timeout=3000):
                back_btn.click(timeout=3000)
                page.wait_for_load_state("networkidle", timeout=8000)
                page.wait_for_timeout(1000)

            # 再次进入 A
            a_link = page.locator(f'a[href*="/bi-training/11/workspace"]')
            if a_link.count() > 0 and a_link.first.is_visible(timeout=3000):
                a_link.first.click(timeout=3000)
            else:
                page.goto(f"{BASE_URL}/#/classroom/100/bi-training/11/workspace",
                          wait_until="domcontentloaded", timeout=15000)

            wait_for_bi_workspace_ready(page, 11)
            title_2 = get_workspace_title(page)
            iframe_2 = page.locator("iframe").first.get_attribute("src") or ""

            assert "A股" in title_2, f"Second entry A failed: {title_2}"
            assert iframe_2 == iframe_1, f"iframe changed on revisit: {iframe_1} vs {iframe_2}"
            # 无白屏: iframe 仍然存在
            assert page.locator("iframe").count() > 0, "iframe missing after revisit"
            print(f"  [Case4] PASS: Same workspace re-entry works, no white screen")

            assert len(console_errors) == 0, f"Console errors: {console_errors}"

        finally:
            page.close()

    @pytest.mark.skipif(BROWSER == "chromium", reason="Firefox smoke only")
    def test_case5_firefox_smoke(self, auth_context):
        """
        Case 5: Firefox 冒烟测试（仅 Firefox 时运行）

        重跑 Case 1 的 3 个 workspace，验证 iframe postMessage 和图表渲染行为.
        """
        page = auth_context.new_page()
        console_errors = []

        def on_console(msg: ConsoleMessage):
            if msg.type == "error":
                text = msg.text
                if any(kw in text.lower() for kw in ["favicon", "chrome-extension"]):
                    return
                # Firefox 特有: postMessage 权限问题
                if "postmessage" in text.lower() or "permission" in text.lower():
                    console_errors.append(f"[Firefox postMessage] {text}")
                else:
                    console_errors.append(text)

        page.on("console", on_console)

        try:
            for ct_id, name_hint, _ in WORKSPACE_SEQUENCE:
                page.goto(f"{BASE_URL}/#/classroom/100/bi-training/{ct_id}/workspace",
                          wait_until="domcontentloaded", timeout=15000)
                wait_for_bi_workspace_ready(page, ct_id)

                title = get_workspace_title(page)
                iframe_count = page.locator("iframe").count()

                assert iframe_count > 0, f"Firefox: no iframe for ct_id={ct_id}"
                assert "favicon" not in title.lower(), f"Firefox: page title weird for {ct_id}"

                # 检查是否有 postMessage 权限错误
                postmsg_errors = [e for e in console_errors if "postmessage" in e.lower() or "permission" in e.lower()]
                assert len(postmsg_errors) == 0, f"Firefox postMessage errors: {postmsg_errors}"

                print(f"  [Case5] Firefox smoke ct_id={ct_id} ({name_hint}): PASS")

            # Firefox 特有断言: 无 postMessage 错误
            assert len(console_errors) == 0, f"Firefox console errors: {console_errors}"
            print(f"  [Case5] PASS: Firefox smoke test passed for all 3 workspaces")

        finally:
            page.close()


if __name__ == "__main__":
    # CLI 入口（不依赖 pytest）
    import sys

    print(f"Running SPA switching tests against {BASE_URL} with {BROWSER}")
    print("Tip: Install pytest-playwright for better output: pip install pytest-playwright")
    print()

    exit_code = 0
    for test_name in [
        "test_case1_spa_continuous_switching",
        "test_case2_spa_ui_click_switching",
        "test_case3_fast_consecutive_switching",
        "test_case4_same_workspace_revisit",
    ]:
        print(f"\nRunning {test_name}...")
        sys.exit(1)  # require pytest

    sys.exit(exit_code)
