-- DC5: 动态页面处理
DO $$
DECLARE new_task_id INTEGER;
BEGIN
  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 5;
  IF new_task_id IS NOT NULL THEN
    DELETE FROM task_tests WHERE task_id = new_task_id;
    DELETE FROM tasks WHERE id = new_task_id;
  END IF;

  INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
  VALUES (
    4,
    '动态页面处理',
    'PRACTICE',
    5,
    'intermediate',
    $dc5$# Stage 5: 动态页面处理

## 一、任务类型

本阶段的核心任务是掌握**动态页面（JavaScript 渲染页面）**的数据抓取技术。互联网上的许多主流网站（如社交媒体、电商平台、SaaS 管理后台）使用 JavaScript 在客户端动态生成页面内容，传统的 HTTP 请求配合 BeautifulSoup 解析方式无法获取这些渲染后的数据。

本关卡需要完成以下任务：

1. 使用 Selenium WebDriver 启动真实浏览器，加载 JavaScript 引擎
2. 编写元素定位表达式准确定位动态生成的 DOM 节点
3. 实现显式等待逻辑，确保元素在可控时间内出现
4. 模拟用户交互行为（点击、输入、滚动）触发数据加载
5. 对比 Playwright 框架的 API 与使用场景，完成框架选型判断
6. 配置无头浏览器模式与反检测参数，提升爬虫的隐蔽性

---

## 二、学习环境

### 2.1 依赖安装

```bash
# Selenium
pip install selenium webdriver-manager

# Playwright（需要额外安装浏览器二进制）
pip install playwright
playwright install chromium
```

### 2.2 基本目录结构

```
data_collection/
├── config/
│   ├── selenium_config.py   # WebDriver 初始化配置
│   └── playwright_config.py  # Playwright 浏览器上下文配置
├── locators/
│   └── element_locators.py  # 元素定位表达式统一管理
├── waiters/
│   └── explicit_waits.py     # 显式等待辅助函数
├── interactions/
│   └── page_actions.py       # 页面交互操作封装
└── main.py                   # 爬虫入口
```

### 2.3 ChromeDriver 配置（Selenium）

使用 `webdriver-manager` 自动管理驱动版本，避免手动下载的版本不匹配问题：

```python
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def create_driver(headless=False, stealth=False):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # 更多反检测参数可按需添加
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)
```

### 2.4 Playwright 上下文配置

```python
from playwright.sync_api import sync_playwright

def create_context(stealth=True):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        viewport={"width": 1920, "height": 1080},
    )
    if stealth:
        # 隐藏 webdriver 标识
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
    return p, browser, context
```

---

## 三、知识点讲解

### 3.1 JavaScript 渲染原理与静态 HTML 的差异

**静态 HTML 页面**：服务器返回完整的 HTML 文档，浏览器直接解析渲染。所有内容在 HTML 源码中可见。

**JavaScript 渲染页面**：服务器返回一个含少量 HTML 骨架和 JavaScript 代码的文档，浏览器执行 JS 后通过 DOM API 动态插入内容。常见的渲染模式：

- **CSR（Client-Side Rendering）**：数据完全由前端 JS 异步加载（Fetch/Axios）后渲染
- **SSR（Server-Side Rendering）**：页面框架在服务端预渲染，部分内容仍由前端 JS 填充（如 Next.js、Nuxt.js）
- **混合模式**：首屏静态渲染，数据列表通过 JS 懒加载

**判断页面是否为动态渲染**：
- 查看页面源码（Ctrl+U），若关键内容不在源码中则很可能是 JS 渲染
- 使用 Selenium/Playwright 等浏览器自动化工具能完整获取渲染后的 DOM

### 3.2 Selenium WebDriver 架构

Selenium WebDriver 是 W3C WebDriver 协议的工业级实现，通过 Chrome DevTools Protocol（Chrome）或 WebDriver 协议与其他浏览器通信。核心架构：

```
Python API (selenium.webdriver)
    │
    ▼
WebDriver 协议层（HTTP REST API）
    │
    ▼
浏览器驱动（chromedriver.exe / geckodriver）
    │
    ▼
真实浏览器实例（Chrome/Firefox/Edge）
```

**驱动选择**：
- Chrome → chromedriver
- Firefox → geckodriver
- Edge → msedgedriver

**隐式等待（Implicit Wait）**：全局设置，查找元素时自动等待最大时长。适合页面加载整体较慢的场景。

```python
driver.implicitly_wait(10)  # 全局最大等待 10 秒
```

**显式等待（Explicit Wait）**：针对单个元素设置等待条件，更精确、更可控。推荐优先使用显式等待。

```python
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.ID, "dynamic-content"))
)
```

### 3.3 元素定位方法

Selenium 提供 8 种元素定位策略：

| 定位方法 | Selenium By | 示例 | 适用场景 |
|---------|------------|------|---------|
| ID | `By.ID` | `driver.find_element(By.ID, "login-btn")` | 唯一标识的表单元素 |
| Class Name | `By.CLASS_NAME` | `driver.find_element(By.CLASS_NAME, "article-title")` | 同类元素的第一个 |
| XPath | `By.XPATH` | `//div[@class='container']//a[contains(@href,'/item')]` | 复杂层级关系 |
| CSS Selector | `By.CSS_SELECTOR` | `driver.find_element(By.CSS_SELECTOR, "div.container > a.item")` | 快速路径匹配 |
| Name | `By.NAME` | `driver.find_element(By.NAME, "username")` | 表单输入字段 |
| Link Text | `By.LINK_TEXT` | `driver.find_element(By.LINK_TEXT, "下一页")` | 已知链接文本 |
| Tag Name | `By.TAG_NAME` | `driver.find_element(By.TAG_NAME, "h1")` | 同标签首个元素 |
| Partial Link Text | `By.PARTIAL_LINK_TEXT` | `driver.find_element(By.PARTIAL_LINK_TEXT, "详情")` | 部分匹配链接 |

**XPath 轴与函数**：
- `//div[contains(@class, 'item')]` — 包含特定 class
- `//tr[position() mod 2 = 1]` — 奇偶行筛选
- `//div[@id='container']//following-sibling::table` — 兄弟节点

**CSS Selector 进阶**：
- `div:not(.hidden)` — 排除特定 class
- `input[type='text']:focus` — 伪类选择器
- `ul > li:first-child` — 结构伪类

### 3.4 页面交互操作

```python
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# 点击
driver.find_element(By.ID, "submit-btn").click()

# 输入文本（先清空再输入）
input_elem = driver.find_element(By.NAME, "search")
input_elem.clear()
input_elem.send_keys("Python 数据采集")
input_elem.send_keys(Keys.RETURN)  # 模拟回车

# 滚动到元素可见
driver.execute_script("arguments[0].scrollIntoView(true);", element)

# 悬停操作
ActionChains(driver).move_to_element(menu).perform()

# 切换 Frame
driver.switch_to.frame("iframe-name")  # 或 frame_element
driver.switch_to.default_content()       # 切回主文档

# 处理多窗口
main_window = driver.window_handles[0]
driver.switch_to.window(driver.window_handles[1])
# ... 在新窗口操作 ...
driver.switch_to.window(main_window)
```

### 3.5 Playwright vs Selenium 核心对比

| 对比维度 | Selenium | Playwright |
|---------|---------|-----------|
| **诞生时间** | 2004 年 | 2020 年（微软出品） |
| **语言支持** | Java/Python/C#/JS/Ruby/Go | JS/TS/Python/.NET/Java/C# |
| **浏览器支持** | 所有主流浏览器 | Chromium/Firefox/WebKit |
| **速度** | 较慢（协议开销） | 较快（CDP 直连） |
| **等待机制** | 手动等待为主 | 自动等待（Auto-waiting） |
| **API 简洁性** | API 较分散 | 链式 API，风格统一 |
| **内置等待** | 无，需手动写等待 | presence/visible/clickable 自动等待 |
| **调试工具** | Selenium IDE | Playwright Codegen/Trace Viewer |
| **反检测** | 需手动配置 | 提供 `stealth` 插件 |
| **并发能力** | 受浏览器实例数限制 | 支持 Browser Context 隔离 |

**代码对比（等效操作）**：

```python
# 导航与元素操作对比
# Selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get("https://example.com")
element = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.CSS_SELECTOR, "button.submit"))
)
element.click()
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

# Playwright
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://example.com")
    page.wait_for_selector("button.submit").click()
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    browser.close()
```

### 3.6 无头模式与反检测配置

**无头模式（Headless）**：浏览器运行时不显示窗口，节省资源，适合服务器环境。

```python
# Selenium 无头
options = Options()
options.add_argument("--headless=new")

# Playwright 无头
browser = p.chromium.launch(headless=True)
```

**反检测（Stealth）配置**：绕过基于 WebDriver 标识的检测机制。

Selenium 反检测要点：
- 修改 `navigator.webdriver` 属性
- 移除 `window.navigator.plugins` 中的自动化特征
- 修改 `user-agent` 模拟真实浏览器

```python
# Selenium 反检测脚本注入
driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    "source": """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
    """
})
```

Playwright 可使用第三方包 `playwright-stealth`：
```python
from playwright_stealth import stealth

page = browser.new_page()
stealth(page,
    languages=["en-US", "en"],
    vendor="Google Inc.",
    webgl_vendor="Intel Inc.",
)
```

---

## 四、常见模式与技巧

### 4.1 JavaScript 片段注入

当 Selenium 的标准 API 无法满足需求时，可直接执行 JS：

```python
# 移除元素的 disabled 属性
driver.execute_script(
    "arguments[0].removeAttribute('disabled');", 
    button_element
)

# 获取懒加载图片的真实 src
imgs = driver.execute_script("""
    return Array.from(document.querySelectorAll('img[data-src]'))
        .map(img => img.getAttribute('data-src'));
""")

# 模拟键盘快捷键
driver.execute_script(
    "document.querySelector('#editor').dispatchEvent(new KeyboardEvent('keydown', {key:'a', ctrlKey:true}))"
)
```

### 4.2 文件下载处理

Selenium 下载配置：

```python
options = Options()
prefs = {
    "download.default_directory": "/tmp/downloads",
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
}
options.add_experimental_option("prefs", prefs)
```

Playwright 下载拦截：

```python
with page.expect_download() as download_info:
    page.click("a.download-btn")
download = download_info.value
path = download.path()
download.save_as("/tmp/output.csv")
```

### 4.3 截图与 PDF 保存

```python
# Selenium 截图
driver.save_screenshot("/tmp/page.png")
element.screenshot("/tmp/element.png")  # 单元素截图

# Playwright 截图与 PDF
page.screenshot(path="/tmp/page.png", full_page=True)
page.pdf(format="A4", print_background=True)
```

### 4.4 网络请求拦截（Playwright）

```python
def intercept_response(response):
    if "api/data" in response.url:
        print(f"Intercepted: {response.url}")
        return response

page.on("response", intercept_response)
page.goto("https://example.com")
```

### 4.5 翻页遍历模式

```python
# Selenium 翻页
while True:
    items = driver.find_elements(By.CSS_SELECTOR, ".item-card")
    for item in items:
        parse_item(item)

    next_btn = driver.find_elements(By.CSS_SELECTOR, ".next-page")
    if not next_btn or "disabled" in next_btn[0].get_attribute("class"):
        break
    next_btn[0].click()
    time.sleep(2)  # 等待页面加载
```

---

## 五、评测标准

本关卡的评分维度如下：

| 评分维度 | 分值 | 说明 |
|---------|------|------|
| 元素定位准确性 | 25 分 | 定位表达式是否唯一且健壮（不依赖脆弱位置） |
| 等待机制合理性 | 25 分 | 是否使用显式等待而非硬编码 sleep |
| 页面交互完整性 | 20 分 | 是否正确完成点击、输入、滚动等操作 |
| 框架使用规范性 | 15 分 | API 调用是否符合框架规范 |
| 反检测配置 | 15 分 | 是否合理配置无头模式与反检测参数 |

**评测环境说明**：评测在无头浏览器模式下运行，自动注入动态渲染的内容。代码需要能够在没有图形界面的服务器环境中正常执行。$dc5$,
    $dc5${"questions": [{"id": "q5_01", "type": "concept", "difficulty": "easy", "question": "以下哪种元素定位方法在页面结构频繁变化时最为健壮（鲁棒性最强）？", "options": ["A) By.ID", "B) By.CLASS_NAME", "C) By.XPATH（绝对路径）", "D) By.XPATH（包含逻辑条件的相对路径）"], "answer": "D", "explanation": "包含逻辑条件（如 contains、starts-with）的相对 XPath 可以适应页面局部变化，而绝对 XPath（/html/body/div[1]/...）在页面任何位置变化时都会失效。ID 虽然固定但并非所有元素都有。Class 在多个元素共用时需要配合索引。", "score": 10}, {"id": "q5_02", "type": "concept", "difficulty": "easy", "question": "关于 Selenium 中的显式等待（Explicit Wait）和隐式等待（Implicit Wait），以下说法正确的是？", "options": ["A) 显式等待和隐式等待可以同时设置，互不影响", "B) 隐式等待只需设置一次，对所有 find_element 操作生效", "C) 显式等待会阻塞整个浏览器进程", "D) 隐式等待的默认等待时间为 0 秒"], "answer": "B", "explanation": "隐式等待在 WebDriver 实例级别设置一次后，对该会话中所有 find_element 调用生效。显式等待只针对特定元素，不阻塞其他操作。两者同时使用可能导致意外行为，因此不推荐混用。隐式等待默认确实为 0，但不设置时即为 0。", "score": 10}, {"id": "q5_03", "type": "concept", "difficulty": "easy", "question": "在 Playwright 中，以下哪个方法可以实现点击一个等待目标元素出现后点击，且无需手动编写等待逻辑？", "options": ["A) page.click(\"#btn\", delay=1000)", "B) page.click(\"#btn\", timeout=5000)", "C) page.wait_for_selector(\"#btn\").click()", "D) page.locator(\"#btn\").click(timeout=5000)"], "answer": "D", "explanation": "Playwright 的 Locator API 内置自动等待机制（Auto-waiting），会在执行 click 前自动等待元素达到可点击状态（visible、enabled、stable）。page.click 直接调用也支持 timeout 参数但机制不同。wait_for_selector + click 是手动等待模式，但 Locator.click 更简洁。", "score": 10}, {"id": "q5_04", "type": "concept", "difficulty": "easy", "question": "以下哪个 CSS Selector 能够选中所有 class 中包含 'active' 的 div 元素？", "options": ["A) div.active", "B) div.class=\"active\"", "C) div[class~=\"active\"]", "D) div\\[class*=\"active\"\\]"], "answer": "C", "explanation": "CSS 属性选择器 ~= 表示属性值以空格分隔的词列表中包含指定词。D 的 *= 是子串匹配也会匹配 'active-link' 等误匹配。A 的 .active 要求 class 属性值恰好等于 'active'（无其他 class）。", "score": 10}, {"id": "q5_05", "type": "concept", "difficulty": "easy", "question": "以下关于浏览器无头模式（Headless Mode）的描述，错误的是哪一项？", "options": ["A) 无头模式下浏览器不渲染可见窗口，适合服务器环境", "B) 无头模式可以显著减少内存占用", "C) 无头模式下 JavaScript 的执行行为与有头模式完全一致", "D) 所有主流浏览器（Chrome/Firefox/Edge）都支持无头模式"], "answer": "C", "explanation": "无头模式下某些依赖 GPU 加速的特性（如 WebGL、CSS 动画性能）可能表现不同。部分网站的反爬检测会通过检测硬件参数（navigator.hardwareConcurrency、deviceMemory）来识别无头模式。需要配合反检测配置才能更接近真实浏览器环境。", "score": 10}, {"id": "q5_06", "type": "calculation", "difficulty": "medium", "question": "假设一个页面需要先登录（登录后设置 session cookie），然后访问数据页面。Selenium WebDriver 中，从初始化浏览器到完成数据抓取，依次需要执行哪三个核心步骤的操作顺序？", "options": ["A) 1) 切换 Frame  2) 执行 JavaScript  3) 获取 Cookie", "B) 1) 访问登录页  2) 填写表单并提交  3) 访问目标数据页", "C) 1) 设置隐式等待  2) 访问 URL  3) 执行 send_keys", "D) 1) 最大化窗口  2) 截图  3) 关闭浏览器"], "answer": "B", "explanation": "Selenium 模拟登录流程的标准步骤是：1) driver.get(login_url) 访问登录页；2) find_element + send_keys 填表 + submit/click 提交；3) driver.get(data_url) 或通过页面导航进入目标页面。前端两种选项描述的是无关步骤，C 中的隐式等待是配置而非操作步骤。", "score": 10}, {"id": "q5_07", "type": "calculation", "difficulty": "medium", "question": "某电商列表页每次滚动到底部后，JS 会异步加载 20 条商品数据。如果要抓取全部 200 条商品，至少需要滚动几次才能确保所有数据加载完成？（不考虑性能优化，假设每次滚动必定触发一次异步加载）", "options": ["A) 9 次", "B) 10 次", "C) 11 次", "D) 19 次"], "answer": "A", "explanation": "初始加载 20 条，滚动一次再加载 20 条（累计 40），依此类推。需要加载 200 条，减去首次加载的 20 条，还需 180 条。180 / 20 = 9 次滚动。", "score": 10}, {"id": "q5_08", "type": "calculation", "difficulty": "medium", "question": "在 Selenium 中，显式等待条件 EC.presence_of_element_located 和 EC.visibility_of_element_located 的主要区别是什么？", "options": ["A) presence 只检查 DOM 中存在，visibility 检查元素可见且有尺寸", "B) presence 的等待时间比 visibility 更长", "C) visibility 只能用于 input 元素", "D) 两者完全等价，只是名称不同"], "answer": "A", "explanation": "presence_of_element_located 只要求元素存在于 DOM 中（可能被隐藏）；visibility_of_element_located 要求元素在可视区域内且有非零尺寸（display != none, visibility != hidden, height > 0, width > 0）。对于懒加载图片，应使用 presence；对于需要用户看到的按钮点击，应使用 visibility 或 element_to_be_clickable。", "score": 10}, {"id": "q5_09", "type": "coding", "difficulty": "hard", "question": "补全以下 Selenium 代码，使用显式等待定位 ID 为 'search-box' 的输入框，清空后输入关键词 'Python'，然后点击 class 为 'search-btn' 的按钮，并返回按钮点击后页面 title。请在下方写出完整的函数体。\n\n```python\nfrom selenium import webdriver\nfrom selenium.webdriver.common.by import By\nfrom selenium.webdriver.support.ui import WebDriverWait\nfrom selenium.webdriver.support import expected_conditions as EC\n\ndef search_and_get_title(driver, url):\n    # 请补全以下代码\n    pass\n```", "answer": "```python\ndef search_and_get_title(driver, url):\n    driver.get(url)\n    wait = WebDriverWait(driver, 10)\n    search_box = wait.until(\n        EC.presence_of_element_located((By.ID, \"search-box\"))\n    )\n    search_box.clear()\n    search_box.send_keys(\"Python\")\n    search_btn = wait.until(\n        EC.element_to_be_clickable((By.CLASS_NAME, \"search-btn\"))\n    )\n    search_btn.click()\n    return driver.title\n```", "explanation": "本题考察显式等待的完整使用流程：通过 WebDriverWait 设置等待对象，用 EC.presence_of_element_located 等待输入框出现，清空后输入文本，再用 EC.element_to_be_clickable 等待按钮可点击（考虑可能的动画禁用状态），最后返回页面标题。", "score": 15}, {"id": "q5_10", "type": "coding", "difficulty": "hard", "question": "补全以下 Playwright 代码，实现以下功能：1) 启动无头 Chromium；2) 创建页面上下文；3) 访问指定 URL；4) 等待 class 为 'data-list' 的元素加载；5) 通过 JavaScript 获取页面滚动高度；6) 关闭浏览器。请在下方写出完整的函数体。\n\n```python\nfrom playwright.sync_api import sync_playwright\n\ndef get_page_scroll_height(url):\n    # 请补全以下代码\n    pass\n```", "answer": "```python\ndef get_page_scroll_height(url):\n    with sync_playwright() as p:\n        browser = p.chromium.launch(headless=True)\n        page = browser.new_page()\n        page.goto(url)\n        page.wait_for_selector(\".data-list\", timeout=10000)\n        scroll_height = page.evaluate(\"document.body.scrollHeight\")\n        browser.close()\n        return scroll_height\n```", "explanation": "本题考察 Playwright 的核心 API 使用：launch 创建浏览器实例，new_page 创建标签页，goto 导航，wait_for_selector 等待特定元素，evaluate 执行 JS 获取 DOM 属性，最后关闭浏览器。with 语句确保资源正确释放。", "score": 15}], "baseline_code": "from selenium import webdriver\nfrom selenium.webdriver.common.by import By\nfrom selenium.webdriver.chrome.options import Options\nfrom selenium.webdriver.support.ui import WebDriverWait\nfrom selenium.webdriver.support import expected_conditions as EC\n\n\ndef login_and_get_content(username: str, password: str, login_url: str) -> str:\n    \"\"\"\n    使用 Selenium WebDriver 模拟登录并获取登录后页面的内容。\n\n    Args:\n        username: 登录用户名\n        password: 登录密码\n        login_url: 登录页面的 URL\n\n    Returns:\n        登录成功后页面 body 元素的 innerHTML 文本\n    \"\"\"\n    # 1. 配置 Chrome 无头选项\n    options = Options()\n    options.add_argument(\"--headless=new\")\n    options.add_argument(\"--no-sandbox\")\n    options.add_argument(\"--disable-dev-shm-usage\")\n\n    # 2. 初始化 WebDriver\n    driver = webdriver.Chrome(options=options)\n\n    try:\n        # 3. 访问登录页面\n        pass\n\n        # 4. 定位用户名和密码输入框，输入凭据\n        pass\n\n        # 5. 点击登录按钮并等待页面跳转完成\n        pass\n\n        # 6. 等待某个可见元素出现，确认登录成功\n        pass\n\n        # 7. 返回页面 body 的 innerHTML\n        pass\n    finally:\n        driver.quit()\n", "test_cases": [{"id": "tc5_01", "description": "调用 login_and_get_content 函数，传入有效的登录 URL 和凭据，验证函数返回的是非空字符串", "expected_behavior": "函数正常执行，无异常抛出，返回值为字符串类型且长度大于 0", "inputs": {"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}, "visible": true, "score": 10}, {"id": "tc5_02", "description": "验证返回内容中包含 HTML 标签（如 '<body' 或 '<h1'），确认获取的是渲染后的 DOM 内容", "expected_behavior": "返回的字符串中包含至少一个 HTML 标签标记", "inputs": {"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}, "visible": true, "score": 10}, {"id": "tc5_03", "description": "测试函数使用显式等待而非硬编码 sleep，验证页面跳转后等待机制生效", "expected_behavior": "函数执行过程中未调用 time.sleep（通过代码审查或执行时间推断）", "inputs": {"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}, "visible": false, "score": 20}, {"id": "tc5_04", "description": "验证元素定位使用了多种定位策略（By.ID、By.CLASS_NAME 或 By.CSS_SELECTOR）", "expected_behavior": "代码中至少使用了两种不同的元素定位方法", "inputs": {"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}, "visible": false, "score": 15}, {"id": "tc5_05", "description": "验证函数在抛出异常时仍能通过 finally 块正确关闭浏览器（driver.quit()）", "expected_behavior": "连续调用多次函数，每次调用后 WebDriver 进程被正确终止，不出现僵尸进程", "inputs": {"username": "invalid_user", "password": "wrong_pass", "login_url": "https://httpbin.org/status/404"}, "visible": false, "score": 25}, {"id": "tc5_06", "description": "验证无头模式配置生效，浏览器启动参数中包含 '--headless'", "expected_behavior": "Chrome 启动时带上 --headless=new 参数，可在日志或进程参数中确认", "inputs": {"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}, "visible": false, "score": 20}]}$dc5$,
    NOW(),
    NOW()
  );

  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 5;

  INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
  VALUES
    (new_task_id, 'tc_1', $dc5${"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}$dc5$, $dc5$"函数正常执行，无异常抛出，返回值为字符串类型且长度大于 0"$dc5$, False, '', 'CONTAINS', 1),
    (new_task_id, 'tc_2', $dc5${"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}$dc5$, $dc5$"返回的字符串中包含至少一个 HTML 标签标记"$dc5$, False, '', 'CONTAINS', 2),
    (new_task_id, 'tc_3', $dc5${"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}$dc5$, $dc5$"函数执行过程中未调用 time.sleep（通过代码审查或执行时间推断）"$dc5$, True, '', 'CONTAINS', 3),
    (new_task_id, 'tc_4', $dc5${"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}$dc5$, $dc5$"代码中至少使用了两种不同的元素定位方法"$dc5$, True, '', 'CONTAINS', 4),
    (new_task_id, 'tc_5', $dc5${"username": "invalid_user", "password": "wrong_pass", "login_url": "https://httpbin.org/status/404"}$dc5$, $dc5$"连续调用多次函数，每次调用后 WebDriver 进程被正确终止，不出现僵尸进程"$dc5$, True, '', 'CONTAINS', 5),
    (new_task_id, 'tc_6', $dc5${"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}$dc5$, $dc5$"Chrome 启动时带上 --headless=new 参数，可在日志或进程参数中确认"$dc5$, True, '', 'CONTAINS', 6),
    (new_task_id, 'tc5_01', $dc5${"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}$dc5$, $dc5$"函数正常执行，无异常抛出，返回值为字符串类型且长度大于 0"$dc5$, False, '调用 login_and_get_content 函数，传入有效的登录 URL 和凭据，验证函数返回的是非空字符串', 'CONTAINS', 7),
    (new_task_id, 'tc5_02', $dc5${"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}$dc5$, $dc5$"返回的字符串中包含至少一个 HTML 标签标记"$dc5$, False, '验证返回内容中包含 HTML 标签（如 ''<body'' 或 ''<h1''），确认获取的是渲染后的 DOM 内容', 'CONTAINS', 8),
    (new_task_id, 'tc5_03', $dc5${"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}$dc5$, $dc5$"函数执行过程中未调用 time.sleep（通过代码审查或执行时间推断）"$dc5$, True, '测试函数使用显式等待而非硬编码 sleep，验证页面跳转后等待机制生效', 'CONTAINS', 9),
    (new_task_id, 'tc5_04', $dc5${"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}$dc5$, $dc5$"代码中至少使用了两种不同的元素定位方法"$dc5$, True, '验证元素定位使用了多种定位策略（By.ID、By.CLASS_NAME 或 By.CSS_SELECTOR）', 'CONTAINS', 10),
    (new_task_id, 'tc5_05', $dc5${"username": "invalid_user", "password": "wrong_pass", "login_url": "https://httpbin.org/status/404"}$dc5$, $dc5$"连续调用多次函数，每次调用后 WebDriver 进程被正确终止，不出现僵尸进程"$dc5$, True, '验证函数在抛出异常时仍能通过 finally 块正确关闭浏览器（driver.quit()）', 'CONTAINS', 11),
    (new_task_id, 'tc5_06', $dc5${"username": "test_user", "password": "test_pass", "login_url": "https://httpbin.org/html"}$dc5$, $dc5$"Chrome 启动时带上 --headless=new 参数，可在日志或进程参数中确认"$dc5$, True, '验证无头模式配置生效，浏览器启动参数中包含 ''--headless''', 'CONTAINS', 12);
END $$;