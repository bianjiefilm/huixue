-- DC1: 数据采集概述与工具选型
DO $$
DECLARE new_task_id INTEGER;
BEGIN
  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 1;
  IF new_task_id IS NOT NULL THEN
    DELETE FROM task_tests WHERE task_id = new_task_id;
    DELETE FROM tasks WHERE id = new_task_id;
  END IF;

  INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
  VALUES (
    4,
    '数据采集概述与工具选型',
    'PRACTICE',
    1,
    'intermediate',
    $dc1$# 数据采集与预处理 - 第1阶段：数据采集概述与工具选型

## 任务类型

本阶段为**概念理解 + 工具选型**任务。学生需要理解数据采集的基本流程、掌握主流Python数据采集工具的特点，并能够根据实际场景选择最合适的工具。任务不涉及大规模编码实现，重点在于建立对数据采集领域的全局认知。

## 学习环境

### 基础环境
- Python 3.9+
- pip 包管理器
- 虚拟环境（推荐使用 venv 或 conda）

### 推荐安装的库
```bash
pip install requests httpx beautifulsoup4 lxml scrapy selenium playwright
```

### 网络环境说明
- 部分网站可能需要代理访问
- 请确保遵守网站的 robots.txt 协议和使用条款
- 测试时优先使用公开的示例接口（如 JSONPlaceholder、OpenWeatherMap 等）

## 知识点讲解

### 1. 什么是数据采集

数据采集（Data Collection / Web Scraping）是指从各种来源获取结构化或非结构化数据的过程。在互联网场景下，数据采集通常指通过网络请求获取网页内容、API 数据或其他数字资源。

**为什么数据采集很重要？**
- 补充内部数据源的不足
- 实时获取公开可用的网络数据
- 为机器学习模型提供训练数据
- 竞品分析、价格监控、舆情分析的基础

### 2. 数据采集工具分类

#### 2.1 HTTP 客户端库

**requests**
- 最流行的 Python HTTP 库
- 适合简单的 GET/POST 请求
- 不支持异步，性能有限

**httpx**
- 支持同步和异步两种模式
- API 与 requests 高度兼容
- 适合需要并发请求的场景

#### 2.2 HTML 解析库

**BeautifulSoup**
- 配合 requests/httpx 使用
- 解析 HTML/XML 文档
- 提供灵活的 DOM 查询接口

**lxml**
- 基于 C 语言实现的高速解析器
- 支持 XPath 和 XSLT
- 通常作为 BeautifulSoup 的底层解析器

#### 2.3 爬虫框架

**Scrapy**
- 全功能的爬虫框架
- 内置请求调度、去重、并发控制
- 支持管道（Pipeline）处理数据
- 适合大规模、结构化的爬取任务

**Selenium**
- 通过浏览器自动化控制真实浏览器
- 能执行 JavaScript，渲染动态页面
- 适合登录验证、复杂交互场景
- 速度较慢，资源消耗大

**Playwright**
- 微软开发的浏览器自动化工具
- 支持 Chromium、Firefox、WebKit
- 比 Selenium 更快，API 更现代
- 内置等待机制，减少 flaky test

### 3. 工具对比表

| 工具 | 类型 | JavaScript 支持 | 学习曲线 | 性能 | 并发能力 | 适用场景 |
|------|------|----------------|----------|------|----------|----------|
| requests | HTTP客户端 | 否 | 极低 | 中 | 低 | 简单API调用、静态页面 |
| httpx | HTTP客户端 | 否 | 低 | 高 | 高（异步） | 高并发API请求 |
| BeautifulSoup | HTML解析 | 否 | 低 | 中 | 低 | 配合requests解析HTML |
| Scrapy | 爬虫框架 | 需中间件 | 中 | 高 | 极高 | 大规模、结构化爬取 |
| Selenium | 浏览器自动化 | 完全支持 | 中 | 低 | 低 | 动态页面、登录验证 |
| Playwright | 浏览器自动化 | 完全支持 | 低 | 中 | 中高 | 复杂SPA、API拦截 |

### 4. 决策流程（工具选型矩阵）

**Step 1: 判断数据来源类型**
- 有公开 API？ → 直接调用 API → 选 `requests` 或 `httpx`
- 无 API，需要解析 HTML？
  - 静态页面（服务器端渲染）→ Step 2
  - 动态页面（JavaScript 渲染）→ Step 3

**Step 2: 评估爬取规模**
- 单次/少量请求 → `requests` + `BeautifulSoup`
- 大规模、多页面、需要去重和调度 → `Scrapy`

**Step 3: 评估动态页面复杂度**
- 简单 JS 渲染，页面较少 → `Selenium`
- 复杂 SPA（单页应用），需要拦截 API 调用 → `Playwright`

**快速选型口诀**：
- **API 用 requests，异步用 httpx**
- **静态页面 BeautifulSoup，规模爬取上 Scrapy**
- **JS 页面 Selenium 要快用 Playwright**

### 5. 真实数据源示例

**天气数据**
- OpenWeatherMap API（需注册获取 API Key）
- 心知天气 API（国内服务）

**股票数据**
- Tushare 金融数据库
- 聚合数据股票接口

**新闻数据**
- 澎湃新闻 RSS
- 腾讯新闻 API

**通用测试接口**
- JSONPlaceholder (https://jsonplaceholder.typicode.com)
- httpbin.org（调试 HTTP 请求）

### 6. 伦理与法律规范

#### robots.txt 协议
```bash
# 查看网站的爬虫规则
curl https://example.com/robots.txt
```
robots.txt 是网站声明的爬虫访问规则，虽然没有法律强制力，但遵守它是网络爬虫的基本礼仪。

#### Rate Limiting（速率限制）
- 两次请求之间添加适当延迟（推荐 1-3 秒）
- 使用 `time.sleep()` 控制请求频率
- 避免对目标服务器造成过大压力

#### 其他注意事项
- 遵守网站的 Terms of Service（服务条款）
- 不要采集个人隐私数据（违反 GDPR 等法律）
- 大量爬取前考虑使用官方 API（更稳定、更合规）
- 在请求头中设置合理的 User-Agent
- 对于需要登录的内容，使用 Cookie 或 Token 时注意安全

## 常见模式与技巧

### 模式 1：礼貌请求头设置
```python
import requests

# 使用礼貌的 User-Agent 标识，方便网站管理员联系
headers = {
    'User-Agent': 'HuixueBot/1.0 (educational-purpose)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

response = requests.get(url, headers=headers, timeout=10)
```

### 模式 2：BeautifulSoup 解析
```python
from bs4 import BeautifulSoup

html = response.text
soup = BeautifulSoup(html, 'lxml')

# 按 CSS 选择器查找
titles = soup.select('.article-title')
# 按标签查找
links = soup.find_all('a', href=True)
# 按文本内容查找
heading = soup.find('h1', string=lambda t: '数据' in t)
```

### 模式 3：分页爬取
```python
all_data = []
for page in range(1, 11):
    url = f'https://example.com/list?page={page}'
    resp = requests.get(url, headers=headers)
    data = parse_page(resp.text)
    all_data.extend(data)
    time.sleep(2)  # 控制请求频率
```

### 模式 4：Selenium 基本使用
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

driver = webdriver.Chrome()
driver.get('https://example.com')
wait = WebDriverWait(driver, 10)
element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content')))
print(element.text)
driver.quit()
```

## 评测标准

### 功能评测
- 函数能正确接收场景描述和参数
- 返回值类型为字符串（工具名称）
- 针对不同场景返回合理的工具推荐

### 代码质量要求
- 函数命名规范，参数类型注解清晰
- 包含必要的 docstring 说明
- 代码逻辑可扩展（方便后续实现具体推荐逻辑）

### 边界情况处理
- 空字符串场景
- 同时要求多个特性的场景（如既需要 JS 支持又需要高并发）

### 性能要求
- 函数执行时间不超过 1 秒
- 无网络请求，纯逻辑计算
$dc1$,
    $dc1${"questions": [{"id": "q1", "type": "concept", "difficulty": "easy", "question": "以下哪种工具最适合从公开的 RESTful API 获取 JSON 数据？", "hint": "API 调用通常只需要发送 HTTP 请求并处理响应，不需要解析 HTML 或执行 JavaScript。", "options": ["A. Selenium", "B. BeautifulSoup", "C. requests", "D. Scrapy"], "answer": "C", "explanation": "requests 是 Python 中最流行的 HTTP 客户端库，专门用于发送 HTTP 请求和接收响应，非常适合调用 RESTful API 获取 JSON 数据。Selenium 和 BeautifulSoup 主要用于浏览器自动化和 HTML 解析，Scrapy 是爬虫框架，不适合简单的 API 调用。"}, {"id": "q2", "type": "concept", "difficulty": "easy", "question": "以下哪个 Python 库无法直接执行 JavaScript 代码？", "hint": "注意区分哪些工具通过真实浏览器执行 JS，哪些只是发送 HTTP 请求。", "options": ["A. Selenium", "B. Playwright", "C. requests", "D. 以上都可以"], "answer": "C", "explanation": "requests 是一个纯 HTTP 客户端库，只能发送和接收 HTTP 请求，无法执行 JavaScript 代码。Selenium 和 Playwright 都是通过控制真实浏览器来执行 JavaScript 的工具。"}, {"id": "q3", "type": "concept", "difficulty": "easy", "question": "Scrapy 框架最不适合以下哪种场景？", "hint": "考虑工具的复杂度与任务规模的匹配程度。", "options": ["A. 爬取10万个商品页面的价格信息", "B. 爬取100个新闻标题", "C. 需要自动去重的批量 URL 爬取", "D. 需要自定义下载中间件的爬取任务"], "answer": "B", "explanation": "Scrapy 是一个功能强大的爬虫框架，内置了请求调度、去重、并发控制等丰富功能，适合大规模爬取任务。对于只需要爬取100个页面的简单场景，使用 requests + BeautifulSoup 会更加轻量和高效。Scrapy 的启动开销较大，不适合小规模一次性任务。"}, {"id": "q4", "type": "concept", "difficulty": "medium", "question": "使用 Python 进行网络爬虫时，以下哪种做法最不符合爬虫伦理规范？", "hint": "注意区分合法的数据采集行为和可能引发法律问题的行为。", "options": ["A. 遵守网站的 robots.txt 协议", "B. 在请求之间添加 2 秒延迟", "C. 设置与真实浏览器一致的 User-Agent", "D. 绕过网站的登录验证直接爬取付费内容"], "answer": "D", "explanation": "绕过登录验证直接爬取付费内容不仅违反了网站的服务条款，还可能侵犯版权法和计算机安全法。遵守 robots.txt、设置合理延迟、设置真实 User-Agent 都是符合伦理规范的爬虫实践。"}, {"id": "q5", "type": "concept", "difficulty": "easy", "question": "BeautifulSoup 库在数据采集中通常扮演什么角色？", "hint": "BeautifulSoup 通常与其他工具配合使用，它的本职功能是什么？", "options": ["A. 发送 HTTP 请求", "B. 解析和遍历 HTML 文档树", "C. 控制浏览器自动化", "D. 管理请求队列和去重"], "answer": "B", "explanation": "BeautifulSoup 是一个 HTML/XML 解析库，它将原始 HTML 文本解析为可遍历的文档树（DOM），然后提供 find()、select() 等方法方便用户查找和提取其中的元素。它需要配合 requests 等工具获取 HTML 文本，本身不具备发送网络请求的能力。"}, {"id": "q6", "type": "calculation", "difficulty": "medium", "question": "某爬虫每分钟向目标网站发送 1200 次请求，每次请求间隔均匀。如果网站允许的最大请求频率为每秒 10 次，那么该爬虫的请求频率超过了安全阈值的多少倍？", "hint": "首先计算当前每秒请求数：1200次/60秒 = 20次/秒。然后与阈值10次/秒比较。", "options": ["A. 1.5 倍", "B. 2 倍", "C. 10 倍", "D. 12 倍"], "answer": "B", "explanation": "每分钟 1200 次请求相当于每秒 1200/60 = 20 次请求。网站允许的阈值为每秒 10 次，因此当前请求频率是安全阈值的 20/10 = 2 倍，即超过了安全阈值 2 倍。这可能会导致 IP 被封禁。"}, {"id": "q7", "type": "calculation", "difficulty": "medium", "question": "使用 requests 库并发发送 100 个 GET 请求，每个请求耗时平均 0.5 秒。如果按顺序执行，总耗时约是多少？如果使用 httpx 异步并发执行，理论上最少可以降到多少秒？", "hint": "顺序执行：100 * 0.5秒。异步并发：所有请求同时发出，总耗时约为单个请求的时间。", "options": ["A. 顺序 50 秒，异步 0.5 秒", "B. 顺序 50 秒，异步 50 秒", "C. 顺序 0.5 秒，异步 50 秒", "D. 顺序 50 秒，异步 5 秒"], "answer": "A", "explanation": "顺序执行时，总耗时 = 100 * 0.5秒 = 50秒。使用 httpx 的异步并发时，所有 100 个请求可以同时发出，理论上总耗时约为最慢那个请求的时间，即约 0.5 秒（不考虑网络波动）。这体现了异步编程在 I/O 密集型任务中的巨大性能优势。"}, {"id": "q8", "type": "calculation", "difficulty": "hard", "question": "某网站页面总数为 5000 页，需要爬取所有页面。每个请求平均耗时 0.8 秒，网站限制最高并发为 5 个请求，且要求每秒请求数不超过 2 次。使用 Scrapy 时，理论上最短需要多少秒完成全部爬取？（不考虑其他延迟因素）", "hint": "每秒最多2个请求，5000页需要的最短时间为 5000/2 = 2500 秒。每个请求0.8秒，并发5个时，每个并发批次耗时0.8秒，但受限于每秒2个请求的速率。", "options": ["A. 2500 秒", "B. 2000 秒", "C. 800 秒", "D. 400 秒"], "answer": "A", "explanation": "网站限制每秒最多2个请求（每0.5秒可发一个），因此5000页最快也需 5000/2 = 2500秒。虽然并发为5，但速率限制使有效并发降为2。此题说明：在严格的速率限制下，并发能力无法发挥作用，只能遵守网站的速率限制。"}, {"id": "q9", "type": "coding", "difficulty": "easy", "question": "补全下面的函数，使其返回对给定的数据采集场景最合适的工具名称字符串。如果场景包含 \"JavaScript\" 或 \"JS\" 且包含 \"动态\"，应返回 \"Selenium\"。", "hint": "使用 in 操作符检查字符串是否包含特定关键词。注意检查顺序——先检查 JS 相关的条件。", "options": null, "answer": "def simple_tool_selector(scenario: str) -> str:\n    if 'JavaScript' in scenario or 'JS' in scenario:\n        if '动态' in scenario:\n            return 'Selenium'\n        return 'Playwright'\n    if 'API' in scenario or 'JSON' in scenario:\n        return 'requests'\n    if '大量' in scenario or '批量' in scenario:\n        return 'Scrapy'\n    return 'requests + BeautifulSoup' ", "explanation": "该函数根据场景描述中的关键词判断最合适的工具：包含 JavaScript/JS 且包含动态内容时返回 Selenium；包含 JavaScript/JS 但不包含动态时返回 Playwright；包含 API/JSON 时返回 requests；包含大量/批量时返回 Scrapy；其他情况默认返回 requests + BeautifulSoup 的组合方案。"}, {"id": "q10", "type": "coding", "difficulty": "medium", "question": "编写一个函数 analyze_requirements(scenario: str, requires_js: bool, requires_speed: bool) -> dict，返回包含推荐工具和相关理由的字典。当 requires_js=True 且 requires_speed=False 时应返回 {\"tool\": \"Selenium\", \"reason\": \"需要执行 JavaScript，速度要求不高\"}；当 requires_js=False 且 requires_speed=True 时应返回 {\"tool\": \"httpx\", \"reason\": \"高并发需求，无需 JavaScript\"}。", "hint": "这是一个多条件判断函数，需要同时考虑 requires_js 和 requires_speed 两个布尔参数。可以使用 if-elif-else 链处理不同组合。", "options": null, "answer": "def analyze_requirements(scenario: str, requires_js: bool, requires_speed: bool) -> dict:\n    if requires_js and not requires_speed:\n        return {\"tool\": \"Selenium\", \"reason\": \"需要执行 JavaScript，速度要求不高\"}\n    elif not requires_js and requires_speed:\n        return {\"tool\": \"httpx\", \"reason\": \"高并发需求，无需 JavaScript\"}\n    elif requires_js and requires_speed:\n        return {\"tool\": \"Playwright\", \"reason\": \"需要 JavaScript 支持且追求较高性能\"}\n    else:\n        return {\"tool\": \"requests\", \"reason\": \"简单请求，无需特殊功能\"} ", "explanation": "该函数根据两个布尔参数的不同组合返回对应的推荐结果。Selenium 虽然支持 JS 但速度较慢，所以当需要 JS 但不追求速度时选择它；httpx 在不需要 JS 的情况下提供最好的异步并发性能；Playwright 在同时需要 JS 和一定性能时是最佳选择；其他情况使用 requests 即可。"}], "baseline_code": "def recommend_tool(scenario: str, requires_js: bool = False, requires_speed: bool = False) -> str:\n    \"\"\"\n    根据数据采集场景推荐最合适的工具。\n    \n    参数:\n        scenario: 场景描述字符串，描述数据来源和采集需求\n        requires_js: 是否需要执行 JavaScript（用于渲染动态页面）\n        requires_speed: 是否需要高并发/高性能\n    \n    返回:\n        推荐的工具名称字符串，如 \"requests\", \"Scrapy\", \"Selenium\", \"Playwright\" 等\n    \"\"\"\n    # TODO: 根据 scenario 内容和 requires_js、requires_speed 参数\n    #       实现工具推荐逻辑，返回最合适的工具名称\n    pass\n"}$dc1$,
    NOW(),
    NOW()
  );

  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 1;

  INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
  VALUES
    (new_task_id, 'tc_1', $dc1$"爬取一个静态 HTML 页面，获取所有新闻标题和链接，页面数量少于 10 个"$dc1$, $dc1$"requests + BeautifulSoup"$dc1$, False, '', 'CONTAINS', 1),
    (new_task_id, 'tc_2', $dc1$"抓取一个需要登录后才能查看的页面，该页面内容通过 JavaScript 动态渲染"$dc1$, $dc1$"Selenium"$dc1$, False, '', 'CONTAINS', 2),
    (new_task_id, 'tc_3', $dc1$"需要并发发送 1000 个 HTTP GET 请求到不同的 API 端点获取 JSON 数据"$dc1$, $dc1$"httpx"$dc1$, True, '', 'CONTAINS', 3),
    (new_task_id, 'tc_4', $dc1$"爬取一个有 1000+ 页面的电商网站，每个页面结构相同，需要自动去重和请求调度"$dc1$, $dc1$"Scrapy"$dc1$, True, '', 'CONTAINS', 4),
    (new_task_id, 'tc_5', $dc1$"分析一个 React 单页应用（SPA），需要拦截其内部 API 调用来获取数据"$dc1$, $dc1$"Playwright"$dc1$, True, '', 'CONTAINS', 5),
    (new_task_id, 'tc_6', $dc1$"调用一个天气数据公开 API，获取未来 7 天的天气预报数据"$dc1$, $dc1$"requests"$dc1$, True, '', 'CONTAINS', 6);
END $$;