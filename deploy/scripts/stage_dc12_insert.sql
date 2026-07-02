-- DC12: 大数据综合项目
DO $$
DECLARE new_task_id INTEGER;
BEGIN
  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 12;
  IF new_task_id IS NOT NULL THEN
    DELETE FROM task_tests WHERE task_id = new_task_id;
    DELETE FROM tasks WHERE id = new_task_id;
  END IF;

  INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
  VALUES (
    4,
    '大数据综合项目',
    'PRACTICE',
    12,
    'intermediate',
    $dc12$# 数据采集与预处理 - 第12阶段：综合项目与评估

## 一、任务类型

本阶段为**综合项目实战 + 知识体系回顾**任务。学生需要将前11个阶段所学的知识融会贯通，设计并实现一个完整的数据采集管道。本阶段重点培养学生的全局视角：不仅关注"能否采到数据"，更关注"采集的数据质量如何"、"效率是否达标"、"是否符合合规要求"等关键问题。任务涵盖项目设计、代码实现、质量评估、文档撰写全流程。

## 二、学习环境

### 基础环境
- Python 3.9+
- pip 包管理器
- 虚拟环境（推荐使用 venv 或 conda）

### 推荐安装的库
```bash
pip install requests httpx beautifulsoup4 lxml scrapy selenium playwright aiohttp pandas openpyxl pymongo redis
```

### 外部服务（可选）
- Redis：分布式采集的请求队列和去重存储
- MongoDB：灵活schema的采集结果存储
- MySQL/PostgreSQL：结构化数据的持久化存储

### 网络环境说明
- 部分网站可能需要代理访问
- 请确保遵守网站的 robots.txt 协议和使用条款
- 测试时优先使用公开的示例接口

## 三、知识点讲解

### 1. 数据采集完整管道设计

一个完整的数据采集管道通常包含以下模块：

```
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌────────────────┐
│  URL 队列   │ -> │  请求调度器  │ -> │   下载器模块    │ -> │   解析器模块    │
│ (待采集URL) │    │ (优先级/去重)│    │ (requests/httpx)│    │ (BS4/XPath/re) │
└─────────────┘    └──────────────┘    └─────────────────┘    └────────────────┘
                                                                   │
                                                                   v
┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌────────────────┐
│  数据存储   │ <- │  数据清洗    │ <- │  数据质量评估   │ <- │  原始数据解析  │
│ (DB/文件)   │    │ (去重/格式化)│    │ (完整性/准确性) │    │   (提取字段)   │
└─────────────┘    └──────────────┘    └─────────────────┘    └────────────────┘
```

#### 1.1 模块职责划分

**URL管理模块**：负责维护待采集URL队列，支持增量采集（断点续传），自动去除已采集URL。

**请求调度模块**：根据网站限速策略控制请求频率，支持优先级调度，支持代理轮换。

**下载器模块**：封装HTTP请求逻辑，统一处理Cookie、UA、代理、重试逻辑。

**解析器模块**：根据目标网站的HTML结构，提取所需字段，支持多种解析方式（CSS/XPath/re）。

**数据清洗模块**：对原始提取数据进行格式化、去重、异常值处理。

**质量评估模块**：从多个维度评估数据质量（见下一节）。

**存储模块**：将清洗后的数据持久化存储，支持多种存储后端。

#### 1.2 配置外置原则

```yaml
# config.yaml
scraper:
  name: "news_aggregator"
  seed_urls:
    - "https://news.example.com/tech"
    - "https://news.example.com/finance"
  request:
    timeout: 30
    max_retries: 3
    retry_delay: 5
    rate_limit:
      requests_per_second: 2
      burst_size: 5
  storage:
    type: "mongodb"
    host: "localhost"
    port: 27017
    database: "news_db"
```

```python
# loader.py
import yaml

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
```

### 2. 数据质量评估体系

数据质量是数据采集项目的生命线。即使采集到了大量数据，如果质量不达标，这些数据也毫无价值。数据质量通常从以下四个维度进行评估：

#### 2.1 完整性（Completeness）

完整性衡量采集到的数据占理论应采集数据的比例。

| 指标 | 定义 | 计算方式 | 达标阈值 |
|------|------|----------|----------|
| 字段完整率 | 必填字段非空的记录比例 | 非空字段数 / (记录数 x 字段数) | > 95% |
| 页面覆盖度 | 实际采集页数 / 目标总页数 | 采集页数 / 目标页数 | > 90% |
| 时间跨度 | 采集数据覆盖的时间范围 | 数据最大时间 - 数据最小时间 | 视业务需求 |
| 关联完整性 | 关联表/字段的匹配率 | 匹配数 / 引用总数 | > 98% |

```python
def evaluate_completeness(df: 'pd.DataFrame', required_fields: list) -> dict:
    results = {}
    for field in required_fields:
        non_null_ratio = df[field].notna().sum() / len(df)
        results[field] = {
            'non_null_count': int(df[field].notna().sum()),
            'null_count': int(df[field].isna().sum()),
            'complete_ratio': round(non_null_ratio * 100, 2)
        }
    overall = sum(r['complete_ratio'] for r in results.values()) / len(results)
    results['overall_completeness'] = round(overall, 2)
    return results
```

#### 2.2 准确性（Accuracy）

准确性衡量采集到的数据与真实数据之间的吻合程度。

| 指标 | 定义 | 检测方法 |
|------|------|----------|
| 格式准确率 | 符合预设格式的字段比例 | 正则校验 / 类型检查 |
| 语义准确率 | 语义上正确的字段比例 | 抽样人工复核 |
| 数值准确率 | 数值在合理范围内的比例 | 范围校验 |
| 重复率 | 完全重复记录的比例 | 哈希去重 |

```python
import re

def validate_field_format(value: str, pattern: str) -> bool:
    """使用正则表达式验证字段格式"""
    if value is None:
        return False
    return bool(re.match(pattern, str(value)))

def validate_numeric_range(value: float, min_val: float, max_val: float) -> bool:
    """验证数值是否在合理范围内"""
    try:
        return min_val <= float(value) <= max_val
    except (ValueError, TypeError):
        return False

def check_duplicates(df: 'pd.DataFrame', key_fields: list) -> dict:
    """检测重复记录"""
    total_records = len(df)
    unique_records = df.drop_duplicates(subset=key_fields).shape[0]
    duplicate_count = total_records - unique_records
    return {
        'total_records': total_records,
        'unique_records': unique_records,
        'duplicate_count': duplicate_count,
        'duplicate_ratio': round(duplicate_count / total_records * 100, 2) if total_records > 0 else 0
    }
```

#### 2.3 时效性（Timeliness）

时效性衡量数据从产生到被采集的时间间隔，以及数据本身的时效性。

| 指标 | 定义 | 说明 |
|------|------|------|
| 采集延迟 | 数据产生到被采集的时间 | 新闻类：< 5分钟；商品类：< 1小时 |
| 数据新鲜度 | 最新数据的时间戳与当前时间差 | 根据业务需求设定阈值 |
| 更新周期 | 相邻两次采集的时间间隔 | 与网站更新频率匹配 |
| 过期率 | 超过时效阈值的记录比例 | 实时监控指标 |

```python
from datetime import datetime, timedelta

def assess_timeliness(df: 'pd.DataFrame', timestamp_field: str, max_age_hours: int = 24) -> dict:
    """评估数据时效性"""
    now = datetime.now()
    df['age_hours'] = (now - pd.to_datetime(df[timestamp_field])).dt.total_seconds() / 3600
    fresh_records = df[df['age_hours'] <= max_age_hours]
    return {
        'total_records': len(df),
        'fresh_records': len(fresh_records),
        'stale_records': len(df) - len(fresh_records),
        'fresh_ratio': round(len(fresh_records) / len(df) * 100, 2) if len(df) > 0 else 0,
        'max_age_hours': max_age_hours,
        'oldest_record_age_hours': round(df['age_hours'].max(), 2) if len(df) > 0 else 0
    }
```

#### 2.4 可用性（Availability）

可用性衡量数据在实际使用场景中的可用程度。

| 指标 | 定义 | 说明 |
|------|------|------|
| 接口成功率 | HTTP请求成功（2xx）的比例 | > 95% 为良好 |
| 数据解析成功率 | 成功提取到目标字段的比例 | > 90% 为良好 |
| 存储成功率 | 成功写入存储的比例 | > 99% 为良好 |
| 可追溯性 | 每条数据可追溯到采集时间、来源URL | 全链路日志 |

```python
class DataQualityReport:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.parsed_records = 0
        self.stored_records = 0

    def add_request(self, success: bool):
        self.total_requests += 1
        if success:
            self.successful_requests += 1

    def add_parse(self):
        self.parsed_records += 1

    def add_storage(self):
        self.stored_records += 1

    def generate_report(self) -> dict:
        return {
            'request_success_rate': round(self.successful_requests / self.total_requests * 100, 2) if self.total_requests > 0 else 0,
            'parse_success_rate': round(self.parsed_records / self.successful_requests * 100, 2) if self.successful_requests > 0 else 0,
            'storage_success_rate': round(self.stored_records / self.parsed_records * 100, 2) if self.parsed_records > 0 else 0,
            'end_to_end_success_rate': round(self.stored_records / self.total_requests * 100, 2) if self.total_requests > 0 else 0
        }
```

### 3. 采集效率评估与优化策略

#### 3.1 效率评估指标

| 指标 | 定义 | 理想值 |
|------|------|--------|
| 吞吐量 | 单位时间内采集的记录数 | 越高越好 |
| 带宽利用率 | 实际带宽占用 / 可用带宽 | 60-80% |
| CPU利用率 | 采集进程CPU占用 | < 70% |
| 内存占用 | 采集进程内存占用 | 稳定，不持续增长 |
| 平均响应时间 | 单次请求平均耗时 | < 1秒 |
| 并发度 | 同时进行的请求数 | 根据目标网站限制调整 |

#### 3.2 优化策略

**策略一：并发采集**

```python
import asyncio
import httpx
from asyncio import Semaphore

async def concurrent_fetch(urls: list, max_concurrent: int = 10) -> list:
    semaphore = Semaphore(max_concurrent)

    async def fetch_one(client, url):
        async with semaphore:
            try:
                resp = await client.get(url, timeout=30)
                return {'url': url, 'status': resp.status_code, 'body': resp.text}
            except Exception as e:
                return {'url': url, 'status': 0, 'error': str(e)}

    async with httpx.AsyncClient() as client:
        tasks = [fetch_one(client, url) for url in urls]
        return await asyncio.gather(*tasks)
```

**策略二：增量采集与断点续传**

```python
import json
from pathlib import Path

class IncrementalCrawler:
    def __init__(self, checkpoint_file: str = "crawl_checkpoint.json"):
        self.checkpoint_file = Path(checkpoint_file)
        self.completed_urls = self._load_checkpoint()

    def _load_checkpoint(self) -> set:
        if self.checkpoint_file.exists():
            return set(json.loads(self.checkpoint_file.read_text()))
        return set()

    def _save_checkpoint(self):
        self.checkpoint_file.write_text(json.dumps(list(self.completed_urls)))

    def should_fetch(self, url: str) -> bool:
        return url not in self.completed_urls

    def mark_completed(self, url: str):
        self.completed_urls.add(url)
        self._save_checkpoint()
```

**策略三：智能重试与退避**

```python
import time
import random

def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
    """指数退避策略，避免对服务器造成压力"""
    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
    return delay

def smart_retry(func, max_attempts: int = 3):
    """智能重试装饰器，根据错误类型决定是否重试"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                if attempt == max_attempts - 1:
                    raise
                time.sleep(exponential_backoff(attempt))
    return wrapper
```

### 4. 数据安全与合规要求

#### 4.1 法律合规框架

| 法规 | 适用范围 | 关键要求 |
|------|----------|----------|
| 《网络安全法》| 中国境内 | 不得窃取个人信息，不得危害网络安全 |
| 《数据安全法》| 中国境内 | 重要数据的采集、处理需合规 |
| 《个人信息保护法》| 中国境内 | 处理个人信息需取得同意 |
| GDPR | 欧盟用户 | 需明确告知数据用途，用户有权删除 |
| CCPA | 加州居民 | 消费者有权了解被收集的数据 |

#### 4.2 合规采集 checklist

1. **检查 robots.txt**：遵守网站声明的爬虫规则
2. **阅读服务条款**：确认网站允许的数据使用方式
3. **频率控制**：请求间隔不低于 1 秒，避免影响网站运营
4. **User-Agent 标识**：使用可识别的 UA，方便网站管理员联系
5. **数据脱敏**：采集的个人信息需脱敏处理后方可使用
6. **存储安全**：采集数据加密存储，访问权限最小化
7. **用途限制**：采集数据仅用于声明目的

#### 4.3 敏感数据识别与处理

```python
import re

SENSITIVE_PATTERNS = {
    'phone': r'1[3-9]\d{9}',  # 中国手机号
    'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
    'id_card': r'\d{15}|\d{18}',  # 身份证号
    'bank_card': r'\d{16,19}',  # 银行卡号
}

def mask_sensitive_data(text: str, pattern_name: str) -> str:
    """脱敏处理敏感数据"""
    pattern = SENSITIVE_PATTERNS.get(pattern_name)
    if not pattern:
        return text

    def replacer(match):
        matched = match.group()
        if pattern_name == 'phone':
            return matched[:3] + '****' + matched[-4:]
        elif pattern_name == 'email':
            parts = matched.split('@')
            return parts[0][:2] + '***@' + parts[1]
        else:
            return matched[:4] + '****' + matched[-4:]

    return re.sub(pattern, replacer, text)
```

### 5. 行业应用案例

#### 5.1 舆情监控系统

**场景**：实时监控社交媒体和新闻网站上的品牌舆情。

**技术方案**：
- 数据源：微博热搜、微信公众号、知乎、抖音评论
- 采集工具：Scrapy + Selenium（处理登录态）
- 数据处理：中文分词（jieba） -> 情感分析（snownlp）
- 存储：MongoDB（JSON 文档存储）+ MySQL（结构化统计）
- 可视化：ECharts 仪表盘

**数据质量关注点**：
- 时效性要求极高（舆情 5 分钟内需感知）
- 情感分析的准确率（需要人工标注数据持续优化）
- 去重（同一事件可能被多平台报道）

#### 5.2 竞品价格采集系统

**场景**：电商平台竞品价格实时监控。

**技术方案**：
- 数据源：京东、天猫、拼多多商品页
- 采集工具：Playwright（应对动态渲染 + 反爬）
- 代理池：轮换 IP 避免封禁
- 存储：TimescaleDB（时序数据优化）
- 告警：价格变动超过阈值时发送通知

**数据质量关注点**：
- 完整性：确保每个 SKU 都被采集到
- 准确性：识别"到手价"而非"标价"
- 防作弊：识别虚假促销（先涨价再降价）

#### 5.3 竞品分析数据平台

**场景**：收集竞品的公开信息进行商业分析。

**技术方案**：
- 数据源：企业官网、天眼查、启信宝、招聘网站
- 采集工具：requests + BeautifulSoup
- 数据整合：从多个来源整合同一公司的信息
- 存储：图数据库（Neo4j）展示企业关系图谱

**数据质量关注点**：
- 数据一致性：同一公司不同来源的命名可能不同
- 准确性：公开信息可能存在误差
- 可追溯性：记录每条数据的来源 URL

### 6. 课程知识体系回顾

经过12个阶段的学习，我们已经掌握了数据采集的完整知识体系：

| 阶段 | 核心内容 | 关键技能 |
|------|----------|----------|
| Stage 1 | 数据采集概述与工具选型 | 根据场景选择合适的工具 |
| Stage 2 | HTTP 协议与请求基础 | 理解请求/响应头、会话管理 |
| Stage 3 | HTML 解析与 BeautifulSoup | CSS 选择器、DOM 遍历 |
| Stage 4 | 正则表达式与数据提取 | re 模块、复杂模式匹配 |
| Stage 5 | 动态页面处理 | Selenium、Playwright 浏览器自动化 |
| Stage 6 | API 数据采集 | RESTful API 调用、认证机制 |
| Stage 7 | 数据存储与清洗 | CSV/JSON/数据库、异常值处理 |
| Stage 8 | 反爬机制与应对策略 | IP 代理、验证码识别、Cookie 管理 |
| Stage 9 | 异步采集与并发控制 | asyncio、httpx、Semaphore |
| Stage 10 | 分布式采集初步 | Scrapy、分布式队列 |
| Stage 11 | 数据采集项目实战 | 项目架构、配置管理、断点续传 |
| Stage 12 | 综合项目与评估 | 质量评估、合规要求、优化策略 |

## 四、常见模式与技巧

### 模式 1：管道式数据处理

```python
from typing import Callable, Any
from dataclasses import dataclass

@dataclass
class PipelineContext:
    raw_data: Any = None
    parsed_data: Any = None
    cleaned_data: Any = None
    errors: list = None

def pipeline(*stages: Callable) -> Callable:
    """数据处理管道装饰器"""
    def execute(ctx: PipelineContext) -> PipelineContext:
        for stage in stages:
            try:
                ctx = stage(ctx)
            except Exception as e:
                ctx.errors.append(f"{stage.__name__}: {e}")
        return ctx
    return execute

def parse_stage(ctx: PipelineContext) -> PipelineContext:
    ctx.parsed_data = parse_html(ctx.raw_data)
    return ctx

def clean_stage(ctx: PipelineContext) -> PipelineContext:
    ctx.cleaned_data = remove_duplicates(ctx.parsed_data)
    return ctx

# 使用示例
pipe = pipeline(fetch_stage, parse_stage, clean_stage)
result = pipe(PipelineContext(raw_data=html, errors=[]))
```

### 模式 2：全链路日志记录

```python
import logging
from functools import wraps
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('crawler')

def log_request(func):
    """记录每个请求的详细信息"""
    @wraps(func)
    def wrapper(url, *args, **kwargs):
        start = datetime.now()
        logger.info(f"[START] GET {url}")
        try:
            result = func(url, *args, **kwargs)
            duration = (datetime.now() - start).total_seconds()
            logger.info(f"[SUCCESS] {url} ({duration:.2f}s)")
            return result
        except Exception as e:
            duration = (datetime.now() - start).total_seconds()
            logger.error(f"[FAILED] {url} ({duration:.2f}s): {e}")
            raise
    return wrapper
```

### 模式 3：多数据源聚合

```python
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor

class MultiSourceAggregator:
    def __init__(self, sources: List[dict]):
        self.sources = sources

    def fetch_all(self, max_workers: int = 5) -> List[Dict]:
        """并发从多个数据源采集"""
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.fetch_source, source): source
                for source in self.sources
            }
            for future in futures:
                source = futures[future]
                try:
                    data = future.result()
                    results.extend(data)
                except Exception as e:
                    logger.error(f"Source {source['name']} failed: {e}")
        return results

    def merge_and_dedupe(self, data_list: List[Dict], key_field: str) -> List[Dict]:
        """合并多源数据并去重"""
        seen = set()
        unique_data = []
        for item in data_list:
            key = item.get(key_field)
            if key and key not in seen:
                seen.add(key)
                unique_data.append(item)
        return unique_data
```

## 五、评测标准

### 功能评测

1. **管道完整性**：函数能正确实现完整的数据采集管道（请求 -> 解析 -> 清洗 -> 存储）
2. **数据质量评估**：函数能返回包含完整性、准确性、时效性、可用性四个维度的评估结果
3. **质量评分**：每个维度有具体的评分（0-100），综合评分反映整体数据质量
4. **错误处理**：函数能优雅处理网络异常、解析错误、存储失败等情况

### 代码质量要求

- 函数命名规范，参数类型注解清晰
- 包含必要的 docstring 说明
- 代码模块化，易于扩展和维护
- 配置外置，不硬编码敏感参数

### 边界情况处理

- 空数据集场景（返回零分但程序不崩溃）
- 部分字段缺失场景（能计算有数据字段的质量评分）
- 网络超时场景（重试后仍失败则记录日志）
- 存储连接失败场景（返回错误信息而非崩溃）

### 性能要求

- 评估函数执行时间不超过 2 秒
- 支持对大数据集（> 10000 条）进行评估
- 评估过程内存占用稳定，不随数据量线性增长
$dc12$,
    $dc12${"questions": [{"id": "q1", "type": "concept", "difficulty": "easy", "question": "在数据质量评估体系中，以下哪个指标最能反映\"采集到的数据是否涵盖所有应采集的字段\"？", "hint": "思考数据质量四大维度：完整性、准确性、时效性、可用性。", "options": ["A. 解析成功率", "B. 字段完整率", "C. 数据新鲜度", "D. 重复率"], "answer": "B", "explanation": "字段完整率衡量的是必填字段非空的记录比例，直接反映了采集到的数据是否涵盖所有应采集的字段。解析成功率反映的是数据提取层面的能力；数据新鲜度反映时效性；重复率反映准确性中的去重维度。"}, {"id": "q2", "type": "concept", "difficulty": "easy", "question": "以下哪种做法最不符合数据采集的合规要求？", "hint": "注意区分合法数据采集行为和可能引发法律问题的行为。", "options": ["A. 采集前检查 robots.txt 并遵守其声明的规则", "B. 在请求之间添加 2 秒延迟以避免对服务器造成压力", "C. 使用虚假 User-Agent 伪装成正常浏览器以绕过反爬机制", "D. 采集的数据中包含个人信息时进行脱敏处理"], "answer": "C", "explanation": "使用虚假 User-Agent 伪装成正常浏览器可能构成对目标网站的欺骗行为，违反了诚实信用原则和部分网站的服务条款。正确做法是使用真实可识别的 UA 标识（如 'MyBot/1.0'），遵守 robots.txt、添加适当延迟、对个人信息脱敏都是符合合规要求的行为。"}, {"id": "q3", "type": "concept", "difficulty": "easy", "question": "在数据采集管道设计中，以下哪个模块负责维护待采集URL队列并实现断点续传？", "hint": "思考管道各模块的职责：请求调度、下载、解析、清洗、存储。", "options": ["A. 下载器模块", "B. 解析器模块", "C. URL管理模块", "D. 数据清洗模块"], "answer": "C", "explanation": "URL管理模块负责维护待采集URL队列、记录已采集URL、支持增量采集（断点续传）。下载器模块负责发送HTTP请求；解析器模块负责提取HTML中的目标字段；数据清洗模块负责去重和格式化处理。"}, {"id": "q4", "type": "concept", "difficulty": "easy", "question": "对于新闻舆情监控系统，以下哪个数据质量维度的要求最高？", "hint": "舆情监控的核心需求是什么？是历史数据的完整性还是最新动态的及时感知？", "options": ["A. 完整性", "B. 准确性", "C. 时效性", "D. 可用性"], "answer": "C", "explanation": "舆情监控的核心价值在于实时感知舆情动态，时效性要求极高（通常需在 5 分钟内感知新舆情）。准确性虽然也重要，但相比实时性，舆情监控更关注'快'。完整性和可用性是基础要求，但不如时效性突出。"}, {"id": "q5", "type": "concept", "difficulty": "easy", "question": "指数退避（Exponential Backoff）策略的主要目的是什么？", "hint": "指数退避是在什么情况下使用的策略？它对谁友好？", "options": ["A. 提高并发度，加快采集速度", "B. 减少服务器压力，避免被封禁", "C. 降低内存占用", "D. 提高解析准确率"], "answer": "B", "explanation": "指数退避策略在请求失败时逐渐增加重试间隔时间（delay = base * 2^n），避免在短时间内向服务器发送大量重复请求，从而减少对服务器的压力，降低被限速或封禁的风险。"}, {"id": "q6", "type": "calculation", "difficulty": "medium", "question": "某数据采集项目共发送了 10000 次 HTTP 请求，其中 9500 次返回 2xx 状态码，300 次返回 4xx 状态码，200 次超时。接口成功率为多少？数据解析阶段有 9200 条成功提取到目标字段，解析成功率为多少？整体端到端成功率为多少？", "hint": "接口成功率 = 2xx次数 / 总次数；解析成功率 = 解析成功数 / 2xx次数；端到端成功率 = 最终存储数 / 总次数。", "options": ["A. 95%、97%、92%", "B. 95%、96.8%、92%", "C. 95%、96.8%、91.8%", "D. 95%、97%、91.8%"], "answer": "B", "explanation": "接口成功率 = 9500/10000 = 95%；解析成功率 = 9200/9500 = 96.84%（约96.8%）；假设存储全部成功则端到端 = 9200/10000 = 92%。若存储也有损耗则更低。"}, {"id": "q7", "type": "calculation", "difficulty": "medium", "question": "使用 asyncio 异步并发发送 500 个 HTTP 请求，每个请求平均耗时 0.5 秒，Semaphore 限制最大并发数为 20。在不考虑网络波动的情况下，理论上最短需要多少秒完成？", "hint": "总请求数500，并发20，每批20个请求需要500/20=25批，每批耗时约0.5秒。", "options": ["A. 0.5 秒", "B. 12.5 秒", "C. 25 秒", "D. 250 秒"], "answer": "B", "explanation": "500 个请求，最大并发 20，则需要 500/20 = 25 批。理想情况下每批请求同时发出，耗时约等于单个请求时间 0.5 秒，因此总耗时约为 25 * 0.5 = 12.5 秒。相比顺序执行的 250 秒，效率提升 20 倍。"}, {"id": "q8", "type": "calculation", "difficulty": "medium", "question": "某电商竞品价格采集系统采集了 10000 条商品数据，其中有 500 条价格字段为空，200 条价格超出合理范围（0-100000元），300 条是之前已采集过的重复记录。该数据的完整性、准确性、重复率分别是多少？", "hint": "完整性 = (10000-500)/10000；准确性 = (10000-500-200)/10000；重复率 = 300/10000。", "options": ["A. 95%, 93%, 3%", "B. 95%, 93%, 0.6%", "C. 95%, 97%, 3%", "D. 97%, 93%, 3%"], "answer": "A", "explanation": "完整性 = (10000 - 500) / 10000 = 95%（扣除了空值记录）；准确性 = (10000 - 500 - 200) / 10000 = 93%（扣除了空值和超范围记录）；重复率 = 300 / 10000 = 3%。"}, {"id": "q9", "type": "coding", "difficulty": "easy", "question": "补全下面的函数 assess_data_quality(records: list, required_fields: list) -> dict，使其接收记录列表和必填字段列表，返回包含各字段完整性评分的字典，还需要在返回字典中包含 overall_score（综合完整性评分，范围 0-100）。", "hint": "遍历每条记录的每个必填字段，统计非空字段数量，计算比例后转换为百分制。", "options": null, "answer": "def assess_data_quality(records: list, required_fields: list) -> dict:\n    \"\"\"\n    评估数据集的完整性质量。\n\n    参数:\n        records: 记录列表，每条记录为字典\n        required_fields: 必填字段列表\n\n    返回:\n        包含各字段完整性评分和综合评分的字典\n    \"\"\"\n    if not records or not required_fields:\n        return {'overall_score': 0.0, 'details': {}}\n\n    total_records = len(records)\n    field_scores = {}\n    total_non_null = 0\n    total_expected = total_records * len(required_fields)\n\n    for field in required_fields:\n        non_null_count = sum(1 for r in records if r.get(field) is not None and r.get(field) != '')\n        score = (non_null_count / total_records) * 100 if total_records > 0 else 0\n        field_scores[field] = round(score, 2)\n        total_non_null += non_null_count\n\n    overall_score = (total_non_null / total_expected) * 100 if total_expected > 0 else 0\n\n    return {\n        'overall_score': round(overall_score, 2),\n        'details': field_scores\n    }", "explanation": "该函数遍历所有记录和必填字段，统计每个字段的非空记录数量，计算各字段的完整性评分（百分比），然后计算所有字段的综合评分。总非空字段数除以期望总数（记录数 x 字段数）得到综合评分。"}, {"id": "q10", "type": "coding", "difficulty": "medium", "question": "补全下面的函数 calculate_efficiency_metrics(total_requests: int, successful_requests: int, failed_requests: int, total_time: float, avg_response_time: float) -> dict，使其计算并返回采集效率的关键指标字典，包含：success_rate（成功率%）、throughput（吞吐量，每秒请求数）、avg_time_per_request（平均每请求耗时秒）、efficiency_score（效率评分，综合考虑成功率和吞吐量，范围 0-100）。", "hint": "成功率 = successful / total * 100；吞吐量 = total / total_time；效率评分可以加权 success_rate * 0.6 + min(throughput*10, 100) * 0.4。", "options": null, "answer": "def calculate_efficiency_metrics(total_requests: int, successful_requests: int, failed_requests: int, total_time: float, avg_response_time: float) -> dict:\n    \"\"\"\n    计算数据采集的效率指标。\n\n    参数:\n        total_requests: 总请求数\n        successful_requests: 成功请求数\n        failed_requests: 失败请求数\n        total_time: 总耗时（秒）\n        avg_response_time: 平均单次响应时间（秒）\n\n    返回:\n        包含各项效率指标的字典\n    \"\"\"\n    if total_requests == 0 or total_time == 0:\n        return {\n            'success_rate': 0.0,\n            'throughput': 0.0,\n            'avg_time_per_request': 0.0,\n            'efficiency_score': 0.0\n        }\n\n    success_rate = (successful_requests / total_requests) * 100\n    throughput = total_requests / total_time\n    avg_time_per_request = total_time / total_requests\n\n    # 效率评分：成功率占60%权重，吞吐量占40%权重\n    throughput_score = min(throughput * 10, 100)\n    efficiency_score = success_rate * 0.6 + throughput_score * 0.4\n\n    return {\n        'success_rate': round(success_rate, 2),\n        'throughput': round(throughput, 2),\n        'avg_time_per_request': round(avg_time_per_request, 4),\n        'efficiency_score': round(efficiency_score, 2)\n    }", "explanation": "该函数计算四个效率指标：成功率反映采集可靠性；吞吐量反映采集速度；平均每请求耗时是吞吐量到单次尺度的转换；效率评分综合考虑成功率和吞吐量两个维度，成功率权重60%（更可靠），吞吐量权重40%（权重上限100）。"}], "baseline_code": "from typing import List, Dict, Any, Optional\nfrom datetime import datetime\nimport pandas as pd\n\ndef evaluate_pipeline_performance(records: List[Dict[str, Any]], total_requests: int, successful_requests: int, failed_requests: int, collection_time_seconds: float) -> Dict[str, Any]:\n    \"\"\"\n    综合评估数据采集管道的性能和质量。\n\n    本函数整合数据质量评估和效率评估，返回完整的评估报告。\n\n    参数:\n        records: 采集到的数据记录列表，每条记录为字典\n        total_requests: 总发送的HTTP请求数\n        successful_requests: 成功返回（2xx）的请求数\n        failed_requests: 失败的请求数\n        collection_time_seconds: 整个采集过程的耗时（秒）\n\n    返回:\n        包含以下键的字典：\n        - quality_report: 数据质量报告（完整性、准确性、时效性、可用性）\n        - efficiency_report: 效率指标报告（成功率、吞吐量、效率评分）\n        - overall_score: 综合评分（0-100）\n        - generated_at: 评估时间戳\n    \"\"\"\n    # TODO Step 1: 计算数据质量报告\n    # - 遍历 records，计算各字段非空率\n    # - 检测重复记录，计算重复率\n    # - 计算接口成功率、解析成功率\n    # - 汇总为 quality_report\n\n    # TODO Step 2: 计算效率指标\n    # - 计算请求成功率\n    # - 计算吞吐量（requests/second）\n    # - 计算效率评分\n    # - 汇总为 efficiency_report\n\n    # TODO Step 3: 综合评分\n    # - 将 quality_score 和 efficiency_score 按权重合并\n    # - 返回包含所有信息的完整报告\n\n    pass\n"}$dc12$,
    NOW(),
    NOW()
  );

  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 12;

  INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
  VALUES
    (new_task_id, 'tc_1', $dc12$"records=[{'title': '新闻A', 'content': '内容A', 'author': '作者A'}, {'title': '新闻B', 'content': None, 'author': '作者B'}], total_requests=100, successful_requests=95, failed_requests=5, collection_time_seconds=50.0"$dc12$, $dc12${"quality_report": {"completeness": 0.75, "accuracy": 0.5}, "efficiency_report": {"success_rate": 0.85, "throughput": 1.8}, "overall_score": 85.0}$dc12$, False, '', 'CONTAINS', 1),
    (new_task_id, 'tc_2', $dc12$"records=[{'id': 1, 'name': '商品1', 'price': 99.9}, {'id': 2, 'name': '商品2', 'price': None}, {'id': 3, 'name': '商品3', 'price': -10.0}, {'id': 4, 'name': '商品1', 'price': 99.9}], total_requests=200, successful_requests=180, failed_requests=20, collection_time_seconds=120.0"$dc12$, $dc12${"quality_report": {"completeness": 0.75, "accuracy": 0.5}, "efficiency_report": {"success_rate": 0.85}, "overall_score": 80.0}$dc12$, False, '', 'CONTAINS', 2),
    (new_task_id, 'tc_3', $dc12$"records=[{'title': f'Item_{i}', 'url': f'http://example.com/{i}', 'timestamp': '2026-04-24T10:00:00'} for i in range(100)], total_requests=100, successful_requests=100, failed_requests=0, collection_time_seconds=30.0"$dc12$, $dc12${"quality_report": {"completeness": 0.99, "accuracy": 0.99}, "efficiency_report": {"success_rate": 1.0}, "overall_score": 95.0}$dc12$, True, '', 'CONTAINS', 3),
    (new_task_id, 'tc_4', $dc12$"records=[{'field_a': 'data', 'field_b': None} for _ in range(50)], total_requests=50, successful_requests=50, failed_requests=0, collection_time_seconds=10.0"$dc12$, $dc12${"quality_report": {"completeness": 0.5}, "overall_score": 70.0}$dc12$, True, '', 'CONTAINS', 4),
    (new_task_id, 'tc_5', $dc12$"records=[], total_requests=0, successful_requests=0, failed_requests=0, collection_time_seconds=0.0"$dc12$, $dc12${"quality_report": {"completeness": 0.0, "accuracy": 0.0}, "efficiency_report": {"success_rate": 0.0}, "overall_score": 0.0}$dc12$, True, '', 'CONTAINS', 5),
    (new_task_id, 'tc_6', $dc12$"records=[{'product': f'P{i}', 'price': 100+i, 'category': 'test'} for i in range(1000)], total_requests=1000, successful_requests=950, failed_requests=50, collection_time_seconds=100.0"$dc12$, $dc12${"quality_report": {"completeness": 0.99}, "efficiency_report": {"throughput": 9.0}, "overall_score": 90.0}$dc12$, True, '', 'CONTAINS', 6);
END $$;