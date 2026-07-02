-- DC11: 数据采集项目实战
DO $$
DECLARE new_task_id INTEGER;
BEGIN
  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 11;
  IF new_task_id IS NOT NULL THEN
    DELETE FROM task_tests WHERE task_id = new_task_id;
    DELETE FROM tasks WHERE id = new_task_id;
  END IF;

  INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
  VALUES (
    4,
    '数据采集项目实战',
    'PRACTICE',
    11,
    'intermediate',
    $dc11$# 数据采集项目实战学习手册

## 一、任务类型

本关卡为**项目实战综合练习**，重点将前续关卡所学的 HTTP 请求、HTML 解析、动态页面处理、API 采集和数据存储等知识点进行系统整合。学生将在本关卡中完成一个完整的新闻网站多页面数据采集项目，从项目需求分析出发，经过架构设计、模块划分、代码实现，最终完成测试与部署。通过本关卡的学习，你将掌握如何将零散的知识点组织成结构化的工程项目，建立起完整的项目开发能力。

## 二、学习环境

- **编程语言**: Python 3.9+
- **核心依赖库**:
  ```bash
  pip install requests beautifulsoup4 lxml python-dotenv loguru
  ```
- **项目结构**:
  ```
  news_scraper/
  ├── config.py          # 配置管理
  ├── logger.py          # 日志配置
  ├── fetcher.py         # HTTP 请求模块
  ├── parser.py          # HTML 解析模块
  ├── storage.py         # 数据存储模块
  ├── main.py            # 主入口
  ├── config.ini         # 配置文件（外置）
  └── output/            # 输出目录
  ```
- **运行环境**: 任何支持 Python 3 的解释器环境
- **输入方式**: 通过标准输入传递采集目标 URL
- **输出方式**: 将采集结果以结构化格式输出到标准输出
- **评测系统**: 评测程序对比输出数据与期望结果

## 三、知识点讲解

### 3.1 项目需求分析

在开始编写代码之前，充分的需求分析是项目成功的第一步。需求分析包括确定数据源、评估采集规模、进行技术选型三个核心环节。

**确定数据源**:
在进行数据采集前，首先需要明确要采集哪些网站、哪些数据字段。常见的数据源类型包括新闻网站（如澎湃新闻、腾讯新闻）、电商平台（京东、淘宝商品页）、社交媒体（微博、知乎）和政府公开数据平台。确定数据源时需要评估：网站是否提供官方 API（优先使用 API，更稳定合规）、目标数据是否可通过公开页面获取、网站对爬虫的态度（是否在 robots.txt 中明确禁止）。

**评估采集规模**:
采集规模直接影响技术方案的选择。少量采集（少于 100 个页面）适合使用 requests + BeautifulSoup 的轻量方案；中等规模（100 到 10000 个页面）需要引入并发控制、断点续传和去重机制；大规模采集（超过 10000 个页面）则应考虑 Scrapy 框架或分布式架构。

**技术选型**:
根据数据源特点和采集规模，综合选择最合适的技术方案：
- 静态页面 + 少量数据：requests + BeautifulSoup
- 需要登录或会话管理：requests + Session + Cookie
- 动态渲染页面：Selenium 或 Playwright
- 有公开 API：requests + 官方 SDK
- 大规模结构化采集：Scrapy + Splash/Selenium 中间件

### 3.2 项目架构设计

一个良好的项目架构是代码可维护性和可扩展性的基础。数据采集项目的架构设计通常包含三个层面：模块划分、数据流设计和异常处理策略。

**模块划分原则**:
一个好的模块应该具有高内聚、低耦合的特点。在新闻采集项目中，我们通常将代码划分为以下模块：
- **配置模块（config）**: 集中管理所有配置参数，避免硬编码
- **日志模块（logger）**: 统一管理日志输出，支持分级记录
- **请求模块（fetcher）**: 封装 HTTP 请求逻辑，处理重试和超时
- **解析模块（parser）**: 负责从 HTML 中提取目标数据
- **存储模块（storage）**: 将采集结果持久化到文件或数据库

**数据流设计**:
```
URL输入 -> [配置模块] -> [请求模块] -> [解析模块] -> [存储模块] -> 结果输出
             |              |              |              |
          配置参数        请求参数        解析规则       存储格式
          超时设置        重试策略        字段映射       路径配置
```

数据流的每个环节都应设计清晰的接口（函数签名或类方法），每个模块只关注自己的职责，通过参数传递和返回值进行模块间通信。

**异常处理策略**:
数据采集中遇到的异常可以分为三类：
- **网络异常**: 超时、DNS 解析失败、连接被拒绝（需要重试机制）
- **业务异常**: HTTP 状态码非 200、解析失败、数据校验不通过（需要错误处理）
- **系统异常**: 文件写入失败、磁盘空间不足（需要优雅降级）

### 3.3 代码组织规范

**配置外置**:
将配置参数从代码中分离出来是工程化的基本要求。配置外置的好处包括：不同环境（开发、测试、生产）使用不同配置，无需修改代码；敏感信息（如 API Key）不暴露在代码仓库中；非技术人员也可以调整采集参数。

```ini
# config.ini
[scraper]
target_url = https://news.example.com
max_pages = 50
timeout = 10
retry_times = 3
delay = 2

[storage]
output_dir = ./output
output_format = json

[logging]
level = INFO
file = ./logs/scraper.log
```

```python
# config.py
import configparser

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

TARGET_URL = config.get('scraper', 'target_url', fallback='https://news.example.com')
MAX_PAGES = config.getint('scraper', 'max_pages', fallback=50)
TIMEOUT = config.getint('scraper', 'timeout', fallback=10)
RETRY_TIMES = config.getint('scraper', 'retry_times', fallback=3)
DELAY = config.getfloat('scraper', 'delay', fallback=2.0)
```

**日志分级记录**:
使用 Python 的 logging 模块或第三方库 loguru 可以实现分级日志记录。常见的日志级别包括 DEBUG（调试信息）、INFO（一般信息）、WARNING（警告信息）、ERROR（错误信息）和 CRITICAL（严重错误）。合理的日志级别设置可以在开发阶段看到详细信息，在生产环境中只关注关键问题。

```python
# logger.py
import logging
import sys

def setup_logger(name='scraper', level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # 文件输出
    file_handler = logging.FileHandler('scraper.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()
```

日志输出示例：
```
2026-04-24 10:30:15 - scraper - INFO - 开始采集: https://news.example.com/article/123
2026-04-24 10:30:16 - scraper - INFO - 请求成功，状态码: 200
2026-04-24 10:30:16 - scraper - DEBUG - 解析文章标题: Python 3.12 新特性解析
2026-04-24 10:30:16 - scraper - INFO - 采集完成，文章标题: Python 3.12 新特性解析
```

### 3.4 完整采集流程实现

一个完整的数据采集流程通常包含以下步骤：初始化配置、发送请求、解析数据、存储结果。

```python
# fetcher.py
import requests
import time
from logger import logger

def fetch_page(url, timeout=10, retry_times=3, delay=2):
    """
    获取网页内容，支持重试和延时
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; NewsScraper/1.0; educational)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    for attempt in range(retry_times):
        try:
            logger.info(f"正在请求: {url} (第{attempt + 1}次)")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            logger.info(f"请求成功，状态码: {response.status_code}")
            return response.text
        except requests.exceptions.Timeout:
            logger.warning(f"请求超时: {url} (第{attempt + 1}次)")
            if attempt < retry_times - 1:
                time.sleep(delay)
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP错误: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"请求异常: {e}")
            if attempt < retry_times - 1:
                time.sleep(delay)
            else:
                raise

    return None
```

```python
# parser.py
from bs4 import BeautifulSoup
from logger import logger

def parse_article(html, url):
    """
    解析文章页面，提取标题、内容、发布时间
    """
    soup = BeautifulSoup(html, 'lxml')

    # 提取标题（常见选择器）
    title = None
    for selector in ['h1.article-title', 'h1#title', '.news-title', 'h1']:
        element = soup.select_one(selector)
        if element:
            title = element.get_text(strip=True)
            break

    # 提取正文内容
    content = None
    for selector in ['div.article-content', 'div.content', 'article']:
        element = soup.select_one(selector)
        if element:
            paragraphs = element.find_all('p')
            content = '\n'.join(p.get_text(strip=True) for p in paragraphs)
            break

    # 提取发布时间
    publish_time = None
    for selector in ['time', 'span.publish-time', 'div.date']:
        element = soup.select_one(selector)
        if element:
            publish_time = element.get_text(strip=True)
            break

    logger.debug(f"解析结果 - 标题: {title}, 时间: {publish_time}")

    return {
        'title': title,
        'content': content,
        'publish_time': publish_time,
        'url': url
    }
```

### 3.5 错误处理与数据校验

数据采集过程中，错误处理和数据校验是保证数据质量的关键环节。好的错误处理能够让程序在遇到问题时优雅地降级或恢复，而严格的数据校验则能确保输出数据的完整性和一致性。

**错误处理机制**:

```python
# main.py 中的错误处理示例
from fetcher import fetch_page
from parser import parse_article
from logger import logger

def scrape_article(url):
    """
    采集单篇文章，支持完整的错误处理
    """
    result = {
        'url': url,
        'success': False,
        'error': None,
        'data': None
    }

    try:
        # 步骤1: 获取页面
        html = fetch_page(url)
        if not html:
            result['error'] = '页面获取失败'
            logger.error(f"采集失败: {url} - 页面获取失败")
            return result

        # 步骤2: 解析数据
        article_data = parse_article(html, url)

        # 步骤3: 数据校验
        validation_error = validate_article(article_data)
        if validation_error:
            result['error'] = validation_error
            logger.warning(f"数据校验失败: {url} - {validation_error}")
            return result

        result['success'] = True
        result['data'] = article_data
        logger.info(f"采集成功: {article_data.get('title', 'N/A')}")

    except Exception as e:
        result['error'] = str(e)
        logger.exception(f"采集异常: {url}")

    return result


def validate_article(article_data):
    """
    校验文章数据的完整性和有效性
    """
    if not article_data.get('title'):
        return '标题不能为空'
    if len(article_data.get('title', '')) < 5:
        return '标题长度不足'
    if not article_data.get('content'):
        return '正文内容不能为空'
    if len(article_data.get('content', '')) < 50:
        return '正文内容长度不足'
    return None  # 无错误，返回 None
```

**数据校验的重要性**:
在实际项目中，即使 HTTP 请求返回了 200 状态码，采集到的数据也可能存在问题：页面结构发生变化导致选择器无法匹配到元素、网络问题导致返回了错误提示页面而非真实内容、某些字段在特定情况下缺失等等。通过在解析后进行数据校验，可以及时发现这些问题，避免将脏数据存入数据库或文件中。数据校验通常包括必填字段非空检查、字段长度合理性检查、格式合规性检查（如时间格式、URL 格式）和业务逻辑检查（如发布日期不能晚于当前日期）。

### 3.6 项目测试与调试方法

数据采集项目的测试与调试有其特殊性，主要挑战在于测试数据（HTML 页面）的可变性以及网络环境的不稳定性。

**本地调试技巧**:
- 将目标页面的 HTML 保存到本地文件，调试解析逻辑时直接读取本地文件，避免重复请求
- 使用 Python 的 `pprint` 模块美化字典输出，方便查看解析结果
- 在关键步骤添加 `logger.debug()` 日志，追踪数据流经每个模块的状态
- 使用 `ipdb` 或 `pdb` 进行交互式调试

**单元测试策略**:
```python
# test_parser.py
import unittest
from parser import parse_article, validate_article

class TestParser(unittest.TestCase):
    def test_validate_article_success(self):
        article = {
            'title': '这是一个有效的文章标题',
            'content': '这是文章正文内容，长度足够以通过校验，正文内容应该不少于50个字符。',
            'url': 'https://example.com/article/1'
        }
        error = validate_article(article)
        self.assertIsNone(error)

    def test_validate_article_empty_title(self):
        article = {
            'title': '',
            'content': '正文内容',
            'url': 'https://example.com/article/1'
        }
        error = validate_article(article)
        self.assertIsNotNone(error)
        self.assertEqual(error, '标题不能为空')

    def test_validate_article_short_content(self):
        article = {
            'title': '这是一个有效的文章标题',
            'content': '太短',
            'url': 'https://example.com/article/1'
        }
        error = validate_article(article)
        self.assertIsNotNone(error)

if __name__ == '__main__':
    unittest.main()
```

### 3.7 真实项目案例：新闻聚合采集器

新闻聚合采集器是一个典型的数据采集项目，它从多个新闻源采集文章，并按类别、时间等维度进行整理输出。

**项目需求**:
- 从新闻网站首页获取文章列表（列表页采集）
- 逐个访问文章详情页，提取文章标题、正文、发布时间等字段
- 将采集结果以 JSON 格式保存
- 支持断点续传：程序中断后可以从中断位置继续采集
- 支持增量采集：只采集新发布的内容，避免重复

**核心实现思路**:
```python
# main.py
import json
from fetcher import fetch_page
from parser import parse_article, validate_article
from logger import logger

def main():
    # 从标准输入读取要采集的文章URL
    url = input().strip()

    logger.info(f"开始采集: {url}")

    # 步骤1: 获取页面
    html = fetch_page(url)
    if not html:
        print(json.dumps({'success': False, 'error': '获取页面失败'}))
        return

    # 步骤2: 解析数据
    article_data = parse_article(html, url)

    # 步骤3: 数据校验
    validation_error = validate_article(article_data)
    if validation_error:
        print(json.dumps({'success': False, 'error': validation_error}))
        return

    # 步骤4: 输出结果
    print(json.dumps({
        'success': True,
        'data': article_data
    }, ensure_ascii=False))


if __name__ == '__main__':
    main()
```

## 四、常见模式与技巧

### 4.1 配置外置与环境隔离

使用 python-dotenv 库可以从 .env 文件加载环境变量，实现配置与代码的分离：

```dotenv
# .env
TARGET_URL=https://news.example.com
MAX_PAGES=50
TIMEOUT=10
API_KEY=your_secret_key
```

```python
# config.py
from dotenv import load_dotenv
import os

load_dotenv()  # 从 .env 文件加载环境变量

TARGET_URL = os.getenv('TARGET_URL', 'https://news.example.com')
MAX_PAGES = int(os.getenv('MAX_PAGES', '50'))
TIMEOUT = int(os.getenv('TIMEOUT', '10'))
```

### 4.2 日志分级记录的进阶用法

使用 loguru 库可以大幅简化日志配置，同时支持彩色输出和结构化日志：

```python
# logger.py
from loguru import logger
import sys

logger.remove()  # 移除默认处理器

logger.add(
    sys.stdout,
    level='INFO',
    format='<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>'
)

logger.add(
    'scraper_{time:YYYY-MM-DD}.log',
    level='DEBUG',
    rotation='00:00',  # 每天零点新建日志文件
    retention='30 days',
    compression='zip'
)
```

### 4.3 断点续传机制

断点续传通过记录已采集的进度来实现，当程序中断后重启时，可以从上次中断的位置继续采集，而不需要从头开始。实现方式是在每次采集成功后，将已处理的 URL 记录到进度文件中：

```python
import json

PROGRESS_FILE = 'progress.json'

def load_progress():
    """加载采集进度"""
    try:
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f).get('processed_urls', []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_progress(processed_urls):
    """保存采集进度"""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'processed_urls': list(processed_urls)}, f, ensure_ascii=False)
```

### 4.4 增量采集策略

增量采集只采集新增的数据，避免重复采集已有数据。实现思路是在采集前先查询数据库或本地文件中已存在的最新数据的时间戳，然后在请求列表页时只获取该时间之后发布的内容。这种方式可以显著减少不必要的网络请求和数据处理开销。

## 五、评测标准

1. **正确性**: 函数能够正确接收 URL 并返回包含标题、正文、发布时间和 URL 的字典
2. **数据校验**: 对缺失标题、空正文等无效数据进行识别和报告
3. **错误处理**: 对网络超时、请求失败等情况有合理的异常处理
4. **代码规范**: 配置外置、日志分级、结构清晰的模块划分
5. **可维护性**: 每个模块职责单一，函数命名规范，有必要的注释说明
$dc11$,
    $dc11${"questions": [{"id": "q11-1", "type": "concept", "difficulty": "easy", "question": "以下哪项不是数据采集项目需求分析阶段需要明确的内容？", "hint": "需求分析关注的是项目目标和约束条件，不涉及具体实现细节。", "options": ["A. 确定要采集哪些网站和数据字段", "B. 评估采集规模以选择合适的技术方案", "C. 编写具体的 HTTP 请求代码", "D. 判断目标网站是否提供官方 API"], "answer": "C", "explanation": "需求分析阶段的目标是明确采集目标和约束条件（数据源、规模、技术选型），具体实现代码是在需求分析之后才编写的，不属于需求分析的范畴。"}, {"id": "q11-2", "type": "concept", "difficulty": "easy", "question": "在数据采集项目中，将配置文件（如 config.ini）从代码中分离出来的主要目的是什么？", "hint": "考虑配置外置在工程实践中的主要优势。", "options": ["A. 加快程序运行速度", "B. 使不同环境可以使用不同配置，无需修改代码", "C. 减少代码行数", "D. 让程序能够自动选择最优参数"], "answer": "B", "explanation": "配置外置的主要目的是实现环境隔离：开发、测试、生产环境可以共用同一套代码，通过不同的配置文件来适应不同环境的参数需求，无需修改代码本身。"}, {"id": "q11-3", "type": "concept", "difficulty": "easy", "question": "使用 Python 的 logging 模块时，以下哪个日志级别表示最严重、需要立即关注的错误？", "hint": "Python logging 模块定义了五个标准级别。", "options": ["A. DEBUG", "B. WARNING", "C. ERROR", "D. CRITICAL"], "answer": "D", "explanation": "Python logging 的五个级别从低到高为 DEBUG < INFO < WARNING < ERROR < CRITICAL。CRITICAL（严重错误）级别最高，表示程序可能无法继续运行的严重问题。"}, {"id": "q11-4", "type": "concept", "difficulty": "easy", "question": "在数据采集项目中，数据校验的主要目的是什么？", "hint": "数据校验发生在解析之后、存储之前。", "options": ["A. 加快数据解析速度", "B. 减少网络请求次数", "C. 发现并报告无效或不完整的数据，避免存储脏数据", "D. 减少磁盘空间占用"], "answer": "C", "explanation": "数据校验在解析完成后、存储前执行，目的是验证数据的完整性和有效性（如标题非空、正文长度足够等），避免将无效数据或不完整数据存入数据库或文件，影响后续数据使用的质量。"}, {"id": "q11-5", "type": "concept", "difficulty": "easy", "question": "断点续传机制的核心实现依赖于什么？", "hint": "断点续传的目的是在程序中断后能够从上次位置继续。", "options": ["A. 自动重试的网络请求", "B. 记录已处理任务的进度文件", "C. 更长的超时等待时间", "D. 多线程并发采集"], "answer": "B", "explanation": "断点续传通过在每次采集成功后，将已处理的 URL 记录到进度文件中来实现。程序重启时读取该文件，跳过已处理的任务，从中断位置继续采集，无需从头开始。"}, {"id": "q11-6", "type": "calculation", "difficulty": "medium", "question": "某数据采集项目设计了以下模块：fetcher.py（HTTP请求）、parser.py（HTML解析）、storage.py（数据存储）、config.py（配置管理）、logger.py（日志记录）。请问这遵循了软件工程中的哪项原则？", "hint": "每个模块只负责一个明确的职责领域。", "options": ["A. 单一职责原则（SRP）", "B. 开闭原则（OCP）", "C. 里氏替换原则（LSP）", "D. 依赖倒置原则（DIP）"], "answer": "A", "explanation": "单一职责原则要求每个模块（或类、函数）只有一个引起它变化的原因。fetcher 只管请求、parser 只管解析、storage 只管存储、config 只管配置——每个模块都有明确且唯一的职责，这正是单一职责原则的体现。"}, {"id": "q11-7", "type": "calculation", "difficulty": "medium", "question": "执行以下代码片段后的输出是什么？\nimport logging\nlogging.basicConfig(level=logging.DEBUG)\nlogger = logging.getLogger('scraper')\nlogger.setLevel(logging.WARNING)\nlogger.debug('DEBUG message')\nlogger.info('INFO message')\nlogger.warning('WARNING message')", "hint": "注意 logger.setLevel 和 basicConfig 的交互关系。", "options": ["A. DEBUG message\\nINFO message\\nWARNING message", "B. WARNING message", "C. DEBUG message\\nINFO message", "D. INFO message\\nWARNING message"], "answer": "B", "answer_detail": null, "explanation": "logger.setLevel(logging.WARNING) 将该 logger 的级别设置为 WARNING，而 basicConfig 设置的全局级别是 DEBUG。由于 logger 自身的级别（WARNING）比全局级别（DEBUG）更高，最终只有 WARNING 级别及以上的日志消息会被输出。因此只输出 'WARNING message'。"}, {"id": "q11-8", "type": "calculation", "difficulty": "medium", "question": "在采集新闻文章时，以下哪种数据校验规则最可能帮助发现\"页面结构变化导致选择器匹配失败\"的问题？", "hint": "选择器匹配失败时，解析结果中会有什么表现？", "options": ["A. 标题长度不能超过 200 个字符", "B. 发布时间必须是有效的日期格式", "C. 标题和正文内容不能为空，且正文长度应超过最小阈值", "D. URL 必须以 http:// 或 https:// 开头"], "answer": "C", "explanation": "当页面结构变化导致选择器匹配失败时，标题或正文字段会被解析为空字符串或非常短的内容。通过设置\"标题非空\"和\"正文长度超过最小阈值（如50字符）\"的校验规则，可以及时发现解析失败的问题，避免将无效数据写入存储。"}, {"id": "q11-9", "type": "coding", "difficulty": "medium", "question": "请实现一个新闻文章数据校验函数 validate_article(article)。该函数接收一个包含 'title'、'content' 和 'url' 三个键的字典，进行以下校验：\n1. 如果 'title' 为空字符串或 None，返回错误信息 '标题不能为空'\n2. 如果 'content' 为空字符串或 None，或者长度小于 50，返回错误信息 '正文内容长度不足'\n3. 如果以上校验均通过，返回 None\n\n请将实现代码写入下方代码区域。", "hint": "注意 None 和空字符串的区分，使用 isinstance 检查类型。", "options": null, "answer": null, "explanation": "实现思路：首先检查 title 是否为 None 或空字符串，若违规返回对应错误信息；然后检查 content 是否为 None 或空字符串，再用 len() 检查长度是否小于 50，若违规返回对应错误信息；所有检查通过后返回 None。"}, {"id": "q11-10", "type": "coding", "difficulty": "medium", "question": "请实现一个简单的新闻文章采集函数 scrape_news(url)。该函数接收一个新闻文章页面的 URL，执行以下步骤：\n1. 使用 requests 库发送 HTTP GET 请求（User-Agent 设为 'NewsScraper/1.0'，超时 10 秒）\n2. 使用 BeautifulSoup（解析器 'lxml'）解析返回的 HTML\n3. 提取页面中第一个 h1 标签的文本作为标题（strip 去除空白）\n4. 提取页面中第一个 article 标签下所有 p 标签的文本，拼接为正文内容\n5. 返回包含 'title'（字符串）、'content'（字符串）和 'url'（原始 URL）三个键的字典\n6. 如果请求失败（抛出异常），返回包含 'error' 键的字典，值为异常消息字符串\n\n请将实现代码写入下方代码区域。", "hint": "使用 try/except 处理请求异常，使用 select_one 和 find_all 查找元素。", "options": null, "answer": null, "explanation": "实现思路：导入 requests 和 BeautifulSoup，在函数中用 try/except 包裹请求逻辑，请求头中设置 User-Agent，解析响应 HTML 后用 h1 选择器提取标题，用 article p 选择器提取正文段落并拼接，组装结果字典返回。异常处理中捕获 requests.RequestException，返回包含 error 键的字典。"}], "baseline_code": "import requests\nfrom bs4 import BeautifulSoup\n\ndef scrape_news(url):\n    \"\"\"\n    采集新闻文章页面\n    url: 新闻文章页面的 URL\n    返回包含 'success'、'title'、'content'、'url' 的字典（成功时），或包含 'success: false' 和 'error' 的字典（失败时）\n    \"\"\"\n    pass\n"}$dc11$,
    NOW(),
    NOW()
  );

  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 11;

  INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
  VALUES
    (new_task_id, 'tc_1', $dc11$"https://example.com/news/article-1"$dc11$, $dc11$"{\"success\": true, \"title\": \"Python 3.12 新特性解析\", \"content\": \"Python 3.12 引入了多项新特性和性能优化，包括更友好的错误提示、自由变量语法和更高效的解释器。\", \"url\": \"https://example.com/news/article-1\"}"$dc11$, False, '', 'CONTAINS', 1),
    (new_task_id, 'tc_2', $dc11$"https://example.com/news/article-2"$dc11$, $dc11$"{\"success\": true, \"title\": \"大数据技术发展趋势分析\", \"content\": \"随着数据量的爆发式增长，大数据技术正在从批处理向实时流处理演进。Apache Flink 和 Apache Spark Structured Streaming 成为主流选择。\", \"url\": \"https://example.com/news/article-2\"}"$dc11$, False, '', 'CONTAINS', 2),
    (new_task_id, 'tc_3', $dc11$"https://example.com/news/article-3"$dc11$, $dc11$"{\"success\": true, \"title\": \"人工智能在教育领域的应用\", \"content\": \"人工智能技术正在深刻改变教育方式，从智能批改作业到个性化学习路径推荐，AI 教育应用呈现出多元化的发展趋势。\", \"url\": \"https://example.com/news/article-3\"}"$dc11$, True, '', 'CONTAINS', 3),
    (new_task_id, 'tc_4', $dc11$"https://example.com/news/article-4"$dc11$, $dc11$"{\"success\": true, \"title\": \"云计算架构的演进与挑战\", \"content\": \"云计算从最初的虚拟化技术发展到如今的容器化和无服务器架构，企业级云原生应用成为数字化转型的核心驱动力。\", \"url\": \"https://example.com/news/article-4\"}"$dc11$, True, '', 'CONTAINS', 4),
    (new_task_id, 'tc_5', $dc11$"https://example.com/news/article-5"$dc11$, $dc11$"{\"success\": true, \"title\": \"网络安全态势分析与防护策略\", \"content\": \"面对日益复杂的网络威胁，企业需要建立全面的安全防护体系，从边界防护到零信任架构，安全策略持续演进和升级。\", \"url\": \"https://example.com/news/article-5\"}"$dc11$, True, '', 'CONTAINS', 5),
    (new_task_id, 'tc_6', $dc11$"https://invalid-domain.example"$dc11$, $dc11$"{\"success\": false, \"error\": \"RequestException\"}"$dc11$, True, '', 'CONTAINS', 6);
END $$;