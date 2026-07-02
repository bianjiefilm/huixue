-- ============================================================
-- Stage 4: Scrapy 框架基础
-- practice_id=4, order_in_practice=4
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    4,
    $sc$Scrapy 框架基础$sc$,
    'PRACTICE',
    4,
    $sc$intermediate$sc$,
    $sc$# Scrapy 框架基础学习手册

## 一、任务类型

本阶段的核心任务是**使用 Scrapy 框架完成电商商品信息采集项目**。具体包括：

- 构建完整的 Scrapy 项目结构
- 编写 Spider 类实现网页内容抓取
- 定义 Item 和使用 ItemLoader 提取结构化数据
- 编写 Item Pipeline 实现数据清洗、验证和持久化
- 配置 Scrapy 爬虫参数实现高效稳定采集

本阶段以电商网站的商品列表页和详情页为采集目标，涵盖从项目初始化到数据导出的完整流程。

---

## 二、学习环境

### 2.1 安装 Scrapy

```bash
pip install scrapy
```

Scrapy 是基于 Twisted 异步网络框架实现的，对 Python 版本有要求：
- Python 3.8+
- Twisted 22.10+
- cryptography (用于 HTTPS 请求)

### 2.2 创建 Scrapy 项目

```bash
scrapy startproject ecommerce_spider
cd ecommerce_spider
scrapy genspider products example.com
```

项目结构如下：

```
ecommerce_spider/
├── scrapy.cfg              # 部署配置文件
└── ecommerce_spider/       # 项目 Python 包
    ├── __init__.py
    ├── items.py             # Item 定义
    ├── middlewares.py      # 中间件
    ├── pipelines.py        # 数据管道
    ├── settings.py         # 配置
    └── spiders/            # 爬虫目录
        ├── __init__.py
        └── products.py     # 商品爬虫
```

### 2.3 运行爬虫

```bash
# 运行指定爬虫
scrapy crawl products

# 保存为 JSON
scrapy crawl products -o items.json

# 保存为 CSV
scrapy crawl products -o items.csv

# 只显示日志
scrapy crawl products --logfile scrapy.log

# 禁用机器人协议检查
scrapy crawl products --no-robots
```

---

## 三、知识点讲解

### 3.1 Scrapy 框架架构

Scrapy 是一个基于 Twisted 异步框架的高级爬虫框架，其核心设计理念是将数据流、控制流和组件解耦。下面是 Scrapy 的核心架构图：

```
+---------------------------------------------------+
|                    Scrapy Engine                  |
|          (核心引擎，协调各组件工作)                 |
+---------------------------------------------------+
        |              |              |
        v              v              v
  +-----------+  +-----------+  +-----------+
  | Scheduler |  | Downloader|  |  Spider   |
  |  (调度器)  |  |  (下载器)  |  |  (爬虫)   |
  +-----------+  +-----------+  +-----------+
        ^              ^              ^
        |              |              |
        |              v              |
        |        +-----------+        |
        |        | Response  |        |
        |        +-----------+        |
        |              |              |
        |              v              |
        |        +-----------+        |
        |        |  Item     |        |
        |        | Pipeline  |        |
        |        +-----------+        |
        |              ^              |
        +----------------------------+
              (Item 数据流)
```

**各组件职责**：

1. **Engine（引擎）**：Scrapy 的核心，负责控制数据流在各个组件之间的流动。当触发某个动作时，引擎负责调度其他组件。

2. **Scheduler（调度器）**：负责管理待爬取的请求队列（Request Queue）。引擎从调度器获取下一个请求，调度器决定请求的优先级和去重策略。

3. **Downloader（下载器）**：负责获取网页内容，使用 Twisted的高效异步 HTTP 客户端。下载完成后，将 Response 对象返回给引擎。

4. **Spider（爬虫）**：用户编写的自定义类，负责解析 Response、提取数据（Item）和跟进链接（Request）。每个 Spider 负责处理特定的网站。

5. **Item Pipeline（数据管道）**：处理从 Spider 提取的 Item，通常包括数据清洗、验证、持久化到数据库或文件等操作。

**异步数据流**：Scrapy 使用 Twisted 实现完全异步的请求-响应循环。当 Downloader 获取一个页面的同时，引擎可以同时处理其他请求的下载和响应解析，这使得 Scrapy 能够实现极高的并发吞吐量。

### 3.2 Spider 类详解

Spider 是 Scrapy 中最核心的组件，用于定义如何抓取特定网站。以下是一个标准的 Spider 类结构：

```python
import scrapy
from ecommerce_spider.items import ProductItem

class ProductSpider(scrapy.Spider):
    # 爬虫唯一标识名
    name = 'products'

    # 允许爬取的域名列表
    allowed_domains = ['example.com']

    # 起始 URL 列表
    start_urls = [
        'https://example.com/products',
        'https://example.com/products?page=2',
    ]

    def parse(self, response):
        """
        默认回调方法，处理 start_urls 返回的响应
        """
        # 解析页面，提取商品链接
        for product_url in response.css('a.product-link::attr(href)'):
            yield response.follow(product_url, self.parse_product)

        # 处理分页
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_product(self, response):
        """
        处理商品详情页
        """
        item = ProductItem()
        item['title'] = response.css('h1.product-title::text').get()
        item['price'] = response.css('span.price::text').re_first(r'\d+\.?\d*')
        item['description'] = response.css('div.description::text').get()
        item['rating'] = response.css('span.rating::attr(data-score)').get()
        item['url'] = response.url
        yield item
```

**start_urls 和 start_requests**：

- `start_urls`：简单的 URL 列表，Scrapy 会自动为每个 URL 创建一个 GET 请求并调用 `parse` 方法。

- `start_requests()`：更灵活的方法，可以重写以发送带有自定义 headers、cookies 或使用 FormRequest 的初始请求：

```python
def start_requests(self):
    # 发送带自定义 headers 的请求
    yield scrapy.Request(
        url='https://example.com/login',
        headers={'User-Agent': 'Mozilla/5.0'},
        callback=self.login
    )

def login(self, response):
    # 使用 FormRequest 模拟登录
    yield scrapy.FormRequest(
        url='https://example.com/do_login',
        formdata={'username': 'user', 'password': 'pass'},
        callback=self.after_login
    )
```

**yield Item 和 yield Request**：

Spider 可以 yield 两种类型的对象：

- **Item 对象**：包含提取的结构化数据，会被发送到 Item Pipeline 处理。
- **Request 对象**：表示新的 HTTP 请求，会被添加到调度器等待下载。

### 3.3 Item 和 ItemLoader

**Item 定义**：

Item 是 Scrapy 用来保存抓取数据的容器，类似于字典但提供了更好的类型检查和调试支持。

```python
# items.py
import scrapy

class ProductItem(scrapy.Item):
    title = scrapy.Field()           # 商品标题
    price = scrapy.Field()          # 价格
    currency = scrapy.Field()       # 货币单位
    description = scrapy.Field()    # 描述
    rating = scrapy.Field()         # 评分
    reviews_count = scrapy.Field()  # 评论数
    category = scrapy.Field()       # 分类
    brand = scrapy.Field()          # 品牌
    availability = scrapy.Field()   # 库存状态
    image_urls = scrapy.Field()     # 图片链接列表
    product_url = scrapy.Field()    # 原始链接
    scraped_time = scrapy.Field()    # 抓取时间
```

**ItemLoader 使用**：

ItemLoader 提供了从响应中提取数据的便捷方式，支持多种数据源和处理函数。

```python
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join

class ProductLoader(ItemLoader):
    # 默认输出处理器：只取第一个值
    default_output_processor = TakeFirst()

    # 定义各字段的输入/输出处理器
    title_in = MapCompose(str.strip, str.title)
    title_out = TakeFirst()

    price_in = MapCompose(str.strip)
    price_out = TakeFirst()

    # 描述字段：合并多个段落并清理空白
    description_in = MapCompose(str.strip)
    description_out = Join(' ')

    # 图片 URL：提取所有链接
    image_urls_out = TakeFirst()
```

在 Spider 中使用 ItemLoader：

```python
from ecommerce_spider.items import ProductItem
from ecommerce_spider.loaders import ProductLoader

def parse_product(self, response):
    loader = ProductLoader(item=ProductItem(), response=response)

    # 使用 CSS 选择器提取
    loader.add_css('title', 'h1.product-title::text')
    loader.add_css('price', 'span.price::text')
    loader.add_css('description', 'div.description p::text')
    loader.add_css('rating', 'span.rating::attr(data-score)')

    # 使用 XPath 提取
    loader.add_xpath('category', '//nav[@class="breadcrumb"]/span[last()]/text()')
    loader.add_xpath('brand', '//span[@class="brand-name"]/text()')

    # 直接添加值
    loader.add_value('product_url', response.url)
    loader.add_value('scraped_time', datetime.now().isoformat())

    return loader.load_item()
```

**输入/输出处理器**（Input/Output Processor）：

Scrapy 提供了多种内置处理器：

| 处理器 | 说明 |
|--------|------|
| `TakeFirst()` | 返回第一个非空值 |
| `Identity()` | 返回原始列表 |
| `MapCompose(*functions)` | 对每个值应用函数 |
| `Join(separator='')` | 用分隔符合并值 |
| `Compose(*functions)` | 将函数组合成管道 |
| `SelectJmes(json_path)` | 从 JSON 字段提取 |

```python
from scrapy.loader.processors import (
    TakeFirst, MapCompose, Compose, Join
)

# 清理和转换数据
price_processor = Compose(
    MapCompose(str.strip),      # 清理空白
    lambda x: x.replace(',', ''),  # 移除千分位逗号
    float                           # 转换为浮点数
)

# 文本清理
text_processor = Compose(
    MapCompose(str.strip, lambda x: x.replace(',', '')),
    Join(' ')
)
```

### 3.4 Item Pipeline

Item Pipeline 处理从 Spider yield 的每个 Item，典型用途包括：

1. **清洗数据**：移除无效或冗余数据
2. **验证数据**：检查必填字段、数据格式
3. **去重**：基于唯一标识字段去重
4. **持久化**：保存到文件、数据库

**Pipeline 结构**：

```python
# pipelines.py
import json
import pymongo
from itemadapter import ItemAdapter

class EcommercePipeline:
    """数据清洗和验证管道"""

    def open_spider(self, spider):
        """爬虫启动时调用"""
        spider.logger.info('Pipeline opened')
        self.items_processed = 0
        self.invalid_items = []

    def process_item(self, item, spider):
        """处理每个 Item"""
        adapter = ItemAdapter(item)

        # 验证必填字段
        required_fields = ['title', 'price', 'product_url']
        for field in required_fields:
            if not adapter.get(field):
                spider.logger.warning(f'Missing {field} in item')
                return item  # 或 drop_item()

        # 清洗价格字段
        price = adapter.get('price')
        if price:
            try:
                # 移除货币符号和千分位
                price_clean = price.replace('$', '').replace(',', '')
                adapter['price'] = float(price_clean)
            except ValueError:
                adapter['price'] = None

        # 清洗评分
        rating = adapter.get('rating')
        if rating:
            try:
                adapter['rating'] = float(rating)
            except (ValueError, TypeError):
                adapter['rating'] = None

        self.items_processed += 1
        return item

    def close_spider(self, spider):
        """爬虫关闭时调用"""
        spider.logger.info(
            f'Pipeline closed. Processed {self.items_processed} items.'
        )


class DuplicatesPipeline:
    """去重管道"""

    def __init__(self):
        self.urls_seen = set()

    def open_spider(self, spider):
        self.urls_seen.clear()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter.get('product_url')

        if url in self.urls_seen:
            spider.logger.debug(f'Duplicate item dropped: {url}')
            raise DropItem(f'Duplicate item: {url}')

        self.urls_seen.add(url)
        return item


class MongoPipeline:
    """MongoDB 持久化管道"""

    def __init__(self, mongo_uri, mongo_db):
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db
        self.client = None
        self.db = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            mongo_uri=crawler.settings.get('MONGO_URI'),
            mongo_db=crawler.settings.get('MONGO_DB')
        )

    def open_spider(self, spider):
        self.client = pymongo.MongoClient(self.mongo_uri)
        self.db = self.client[self.mongo_db]

    def process_item(self, item, spider):
        self.db.products.insert_one(ItemAdapter(item).asdict())
        return item

    def close_spider(self, spider):
        self.client.close()


class JsonExportPipeline:
    """JSON 文件导出管道"""

    def __init__(self):
        self.file = None

    def open_spider(self, spider):
        self.file = open('products.json', 'w', encoding='utf-8')
        self.file.write('[')

    def process_item(self, item, spider):
        line = json.dumps(
            ItemAdapter(item).asdict(),
            ensure_ascii=False
        ) + ',\n'
        self.file.write(line)
        return item

    def close_spider(self, spider):
        self.file.write(']')
        self.file.close()
```

**激活 Pipeline**：在 `settings.py` 中配置：

```python
ITEM_PIPELINES = {
    'ecommerce_spider.pipelines.EcommercePipeline': 300,
    'ecommerce_spider.pipelines.DuplicatesPipeline': 350,
    'ecommerce_spider.pipelines.MongoPipeline': 400,
    'ecommerce_spider.pipelines.JsonExportPipeline': 500,
}
```

数字表示执行顺序，数字越小越先执行。

### 3.5 CSS 选择器和 XPath 在 Spider 中的使用

Scrapy 的 Response 对象提供了 `css()` 和 `xpath()` 方法来提取数据。

**CSS 选择器**：

```python
def parse_product(self, response):
    # 选择单个元素，获取文本
    title = response.css('h1.product-title::text').get()

    # 选择多个元素，获取所有文本
    paragraphs = response.css('div.description p::text').getall()

    # 获取属性值
    link = response.css('a.buy-button::attr(href)').get()

    # 获取多个链接
    image_urls = response.css('img.product-image::attr(src)').getall()

    # 使用伪元素
    first_li_text = response.css('ul li:first-child::text').get()

    # 组合选择器
    prices = response.css('div.price-list span.price::text').getall()

    # 选择器链
    breadcrumb = response.css('.breadcrumb').css('a::text').getall()
```

**XPath 选择器**：

```python
def parse_product(self, response):
    # 基本选择
    title = response.xpath('//h1[@class="product-title"]/text()').get()

    # 属性选择
    link = response.xpath('//a[@id="buy-now"]/@href').get()

    # 文本包含
    nav_item = response.xpath(
        '//nav//a[contains(text(), "首页")]/@href'
    ).get()

    # 位置函数
    first_product = response.xpath('//div[@class="product"][1]').get()
    last_breadcrumb = response.xpath('//nav/span[last()]/text()').get()

    # 轴（Ancestors/Descendants）
    parent_text = response.xpath('//span[@class="price"]/parent::div/text()').get()

    # 多条件
    items = response.xpath(
        '//div[contains(@class, "product") and @data-active="true"]'
    )

    # 使用 position 限制数量
    first_three = response.xpath('//ul/li[position() <= 3]/text()').getall()
```

**CSS vs XPath 对比**：

| 特性 | CSS | XPath |
|------|-----|-------|
| 学习曲线 | 更简单直观 | 较陡但更强大 |
| 文本提取 | `::text` | `/text()` |
| 属性提取 | `::attr(href)` | `/@href` |
| 父元素 | 不支持 | 支持 `/..` |
| 函数支持 | CSS 伪元素 | 内置函数丰富 |
| 位置选择 | `:nth-child()` | `[position()]` |
| 适用场景 | 简单选择 | 复杂结构、跨节点 |

**实际项目建议**：
- 简单选择（class、id、标签）：使用 CSS
- 复杂选择（父节点、文本包含、多条件）：使用 XPath
- 可以混合使用：`response.css('div.products').xpath('.//a/@href')`

### 3.6 Scrapy 命令详解

Scrapy 提供了一组命令行工具，简化项目管理和爬虫操作。

**项目命令**：

```bash
# 创建新项目
scrapy startproject myproject

# 进入项目目录
cd myproject

# 列出项目中所有爬虫
scrapy list

# 查看爬虫帮助
scrapy genspider --help

# 创建爬虫
scrapy genspider myspider example.com

# 使用模板创建爬虫
scrapy genspider -t crawl myspider example.com
```

**爬虫命令**：

```bash
# 运行爬虫
scrapy crawl myspider

# 运行并设置并发数
scrapy crawl myspider -s CONCURRENT_REQUESTS=16

# 运行并设置下载延迟
scrapy crawl myspider -s DOWNLOAD_DELAY=1

# 运行并禁用 ROBOTSTXT_OBEY
scrapy crawl myspider -s ROBOTSTXT_OBEY=False

# 运行并设置日志级别
scrapy crawl myspider -L INFO
scrapy crawl myspider -L DEBUG

# 运行并保存输出
scrapy crawl myspider -o output.json
scrapy crawl myspider -o output.jl      # JSON Lines
scrapy crawl myspider -o output.csv
scrapy crawl myspider -o output.xml

# 只运行少量请求用于测试
scrapy crawl myspider -s CLOSESPIDER_ITEMCOUNT=100

# 在指定 URL 上运行 Shell 进行调试
scrapy shell "https://example.com/products"

# 检查爬虫是否正确配置
scrapy check

# 视图响应（浏览器中打开）
scrapy view "https://example.com/products"

# 获取爬虫代码模板
scrapy genspider --list-template
```

**settings 命令**：

```bash
# 列出所有可用设置
scrapy settings --get DOWNLOAD_DELAY
scrapy settings --get DEFAULT_REQUEST_HEADERS

# 获取设置（带默认值）
scrapy settings --get BOT_NAME
```

### 3.7 Request 和 Response

**Request 对象**：

```python
import scrapy

class MySpider(scrapy.Spider):
    def parse(self, response):
        # 基本 GET 请求
        yield scrapy.Request(
            url='https://example.com/page1',
            callback=self.parse_page1
        )

        # 带参数的请求
        yield scrapy.Request(
            url='https://example.com/api/data',
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({'key': 'value'}),
            callback=self.parse_api
        )

        # 使用 follow 快捷方法
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

        # follow 还可以处理相对 URL
        for link in response.css('a.product::attr(href)'):
            yield response.follow(link, self.parse_product)
```

**meta 参数**：

meta 用于在请求之间传递数据：

```python
def parse(self, response):
    # 传递数据到下一个回调
    yield scrapy.Request(
        url='https://example.com/detail',
        meta={'category': 'electronics', 'page': 1},
        callback=self.parse_detail
    )

def parse_detail(self, response):
    # 获取 meta 传递的数据
    category = response.meta['category']
    page = response.meta['page']

    # 修改 meta 并传递给下一个请求
    yield scrapy.Request(
        url='https://example.com/review',
        meta={'category': category, 'page': page, 'detail_parsed': True},
        callback=self.parse_review
    )
```

**FormRequest**：

用于模拟表单提交和登录：

```python
def parse(self, response):
    # 登录表单
    yield scrapy.FormRequest.from_response(
        response,
        formdata={'username': 'user', 'password': 'pass'},
        callback=self.after_login
    )

def after_login(self, response):
    # 检查登录是否成功
    if 'Welcome' in response.text:
        self.log('Login successful')
    else:
        self.log('Login failed', level=logging.ERROR)

# 或者直接创建 FormRequest
def login(self, response):
    yield scrapy.FormRequest(
        url='https://example.com/login',
        formdata={
            'username': 'myuser',
            'password': 'mypassword',
            'csrf_token': response.css('input[name="csrf"]::attr(value)').get()
        },
        callback=self.logged_in
    )
```

**Request 优先级和重试**：

```python
yield scrapy.Request(
    url='https://example.com/high-priority',
    priority=10,          # 更高优先级
    dont_filter=False,    # 是否允许去重
    errback=self.handle_error
)

def handle_error(self, failure):
    self.logger.error(repr(failure))
    # 处理错误，如重试
    if failure.check(HttpError):
        response = failure.value.response
        self.logger.error(f'HttpError on {response.url}')
```

**Response 子类**：

Scrapy 根据响应类型自动选择合适的 Response 子类：

| 类型 | 说明 |
|------|------|
| `TextResponse` | 包含 text 属性，支持字符编码处理 |
| `HtmlResponse` | HTML 专用，提供 css/xpath 方法 |
| `XmlResponse` | XML 专用，提供 xpath 方法 |

### 3.8 settings.py 配置详解

Scrapy 的配置文件控制爬虫行为的各个方面。

**并发和性能配置**：

```python
# settings.py

# 最大并发请求数（默认 16）
CONCURRENT_REQUESTS = 16

# 每个域名的最大并发请求数
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# 每个 IP 的最大并发请求数（当 CONCURRENT_REQUESTS_PER_DOMAIN 生效时可用）
# CONCURRENT_REQUESTS_PER_IP = 8

# 请求之间的下载延迟（秒），支持浮点数
DOWNLOAD_DELAY = 0.5

# 是否启用随机下载延迟（DOWNLOAD_DELAY 的随机倍数）
# RANDOMIZE_DOWNLOAD_DELAY = True

# 每个域名的请求队列大小
# QUEUE_LENGTH = 100
```

**机器人协议配置**：

```python
# 是否遵守 robots.txt 协议（默认 True）
ROBOTSTXT_OBEY = True

# robots.txt 文件的 URL
# ROBOTSTXT_USER_AGENT = 'mybot/1.0'
```

**自动限速（AutoThrottle）**：

AutoThrottle 根据服务器的响应时间自动调整爬虫速度：

```python
# 启用自动限速
AUTOTHROTTLE_ENABLED = True

# 初始请求间隔（秒）
AUTOTHROTTLE_START_DELAY = 0.5

# 最大请求间隔（秒）
AUTOTHROTTLE_MAX_DELAY = 10.0

# 并发请求的目标数
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# 启用 DEBUG 级别显示限速调节信息
# AUTOTHROTTLE_DEBUG = False
```

**下载器中间件和 User-Agent**：

```python
# User-Agent 列表（默认使用 Scrapy 的 UA）
USER_AGENT = 'MySpider (+http://www.example.com)'

# 或使用轮换 UA
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
]

# 下载器中间件（按顺序执行）
DOWNLOADER_MIDDLEWARES = {
    'myproject.middlewares.RandomUserAgentMiddleware': 400,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
}

# 重试配置
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]
```

**请求头和 Cookie**：

```python
# 默认请求头
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
}

# Cookie 启用
COOKIES_ENABLED = True

# Cookie 中间件调试
# COOKIES_DEBUG = False
```

**缓存配置**：

```python
# 启用 HTTP 缓存
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
```

**日志配置**：

```python
# 日志级别
LOG_LEVEL = 'INFO'

# 日志文件
LOG_FILE = 'scrapy.log'

# 日志格式
# LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
# LOG_DATEFORMAT = '%Y-%m-%d %H:%M:%S'
```

**内存配置**：

```python
# 启用内存监控
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 512
MEMUSAGE_WARNING_MB = 256

# 当达到内存限制时关闭爬虫
# MEMUSAGE_CHECK_INTERVAL_SECONDS = 60
```

---

## 四、实战代码：完整电商商品采集 Spider

以下是一个完整的电商商品采集 Spider 示例，展示了 Scrapy 各组件的协同使用：

```python
# ecommerce_spider/spiders/product_spider.py
import scrapy
from scrapy.loader import ItemLoader
from itemadapter import ItemAdapter
from ecommerce_spider.items import ProductItem
from scrapy.loader.processors import MapCompose, TakeFirst
import re


class ProductSpider(scrapy.Spider):
    name = 'product_spider'
    allowed_domains = ['example.com']

    # 使用动态起始 URL
    def start_requests(self):
        base_url = 'https://example.com/products'
        categories = ['electronics', 'clothing', 'home']

        for category in categories:
            yield scrapy.Request(
                url=f'{base_url}?category={category}',
                meta={'category': category},
                callback=self.parse_category
            )

    def parse_category(self, response):
        """解析商品列表页"""
        category = response.meta['category']

        # 提取商品链接
        product_selectors = response.css('div.product-card')

        for product in product_selectors:
            # 使用 CSS 选择器提取
            loader = ItemLoader(item=ProductItem(), selector=product)

            loader.add_css('title', 'h3.product-name::text',
                          MapCompose(str.strip))
            loader.add_css('price', 'span.price::text',
                          MapCompose(lambda x: x.replace('$', '').strip()))
            loader.add_css('rating', 'span.rating::attr(data-score)')
            loader.add_css('reviews_count', 'span.reviews::text',
                          MapCompose(lambda x: re.search(r'\d+', x).group()))
            loader.add_css('image_urls', 'img.product-img::attr(src)')

            # 获取详情页链接
            detail_link = product.css('a.detail-link::attr(href)').get()
            if detail_link:
                yield response.follow(
                    detail_link,
                    callback=self.parse_product,
                    meta={'item': loader.load_item(), 'category': category}
                )

        # 处理分页
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse_category)

    def parse_product(self, response):
        """解析商品详情页"""
        item = response.meta['item']
        category = response.meta['category']

        # 使用 XPath 补充提取
        item['brand'] = response.xpath(
            '//span[@class="brand"]/text()'
        ).get()

        item['description'] = response.xpath(
            '//div[@class="description"]//text()'
        ).getall()

        item['availability'] = response.xpath(
            '//span[contains(@class, "stock")]/text()'
        ).get()

        item['specifications'] = self._parse_specifications(response)
        item['product_url'] = response.url
        item['category'] = category

        yield item

    def _parse_specifications(self, response):
        """解析规格信息"""
        specs = {}
        rows = response.xpath('//table[@class="specs"]/tr')

        for row in rows:
            key = row.xpath('th/text()').get()
            value = row.xpath('td/text()').get()
            if key and value:
                specs[key.strip()] = value.strip()

        return specs


# ecommerce_spider/items.py
import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst


def strip_text(text):
    if text:
        return text.strip()
    return ''


class ProductItem(scrapy.Item):
    title = scrapy.Field()
    price = scrapy.Field(
        input_processor=MapCompose(strip_text, lambda x: x.replace(',', '')),
        output_processor=TakeFirst()
    )
    brand = scrapy.Field()
    description = scrapy.Field()
    rating = scrapy.Field()
    reviews_count = scrapy.Field()
    availability = scrapy.Field()
    specifications = scrapy.Field()
    image_urls = scrapy.Field()
    product_url = scrapy.Field()
    category = scrapy.Field()
    scraped_time = scrapy.Field()


# ecommerce_spider/pipelines.py
import json
from datetime import datetime
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class DataCleaningPipeline:
    """数据清洗管道"""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # 价格清洗
        price = adapter.get('price')
        if price:
            try:
                adapter['price'] = float(price)
            except (ValueError, TypeError):
                adapter['price'] = None

        # 评分归一化
        rating = adapter.get('rating')
        if rating:
            try:
                rating_val = float(rating)
                # 假设原始评分为 0-5，转换为 0-1
                if rating_val > 1:
                    rating_val = rating_val / 5.0
                adapter['rating'] = round(rating_val, 2)
            except (ValueError, TypeError):
                adapter['rating'] = None

        # 评论数清洗
        reviews = adapter.get('reviews_count')
        if reviews:
            try:
                adapter['reviews_count'] = int(reviews)
            except (ValueError, TypeError):
                adapter['reviews_count'] = 0

        # 添加抓取时间
        adapter['scraped_time'] = datetime.now().isoformat()

        return item


class DuplicatesPipeline:
    """URL 去重管道"""

    def __init__(self):
        self.seen_urls = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter.get('product_url')

        if url in self.seen_urls:
            raise DropItem(f'Duplicate item: {url}')

        self.seen_urls.add(url)
        return item


class ValidationPipeline:
    """数据验证管道"""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        errors = []

        # 必填字段检查
        if not adapter.get('title'):
            errors.append('Missing title')

        if not adapter.get('product_url'):
            errors.append('Missing product_url')

        # 价格范围检查
        price = adapter.get('price')
        if price is not None and (price < 0 or price > 1000000):
            errors.append(f'Invalid price: {price}')

        # 评分范围检查
        rating = adapter.get('rating')
        if rating is not None and (rating < 0 or rating > 1):
            errors.append(f'Invalid rating: {rating}')

        if errors:
            spider.logger.warning(f"Validation failed: {', '.join(errors)}")

        return item


class JsonExportPipeline:
    """JSON 导出管道"""

    def __init__(self):
        self.file = None
        self.first_item = True

    def open_spider(self, spider):
        self.file = open('products.json', 'w', encoding='utf-8')
        self.file.write('[')

    def process_item(self, item, spider):
        if not self.first_item:
            self.file.write(',')
        self.first_item = False

        line = json.dumps(
            ItemAdapter(item).asdict(),
            ensure_ascii=False,
            indent=2
        )
        self.file.write('\n' + line)
        return item

    def close_spider(self, spider):
        self.file.write('\n]')
        self.file.close()


# ecommerce_spider/settings.py (相关配置)
BOT_NAME = 'ecommerce_spider'

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 16
DOWNLOAD_DELAY = 1
AUTOTHROTTLE_ENABLED = True

USER_AGENT = 'EcommerceSpider/1.0 (+http://example.com/bot)'

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

ITEM_PIPELINES = {
    'ecommerce_spider.pipelines.DataCleaningPipeline': 100,
    'ecommerce_spider.pipelines.DuplicatesPipeline': 200,
    'ecommerce_spider.pipelines.ValidationPipeline': 300,
    'ecommerce_spider.pipelines.JsonExportPipeline': 900,
}

TELNETCONSOLE_ENABLED = False
```

---

## 五、性能与配置

### 5.1 并发控制

Scrapy 的并发控制是性能调优的核心：

```python
# settings.py

# 全局并发（同时进行的最大请求数）
CONCURRENT_REQUESTS = 32

# 域名级并发（每个域名同时最多多少请求）
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# IP 级并发（当需要时）
# CONCURRENT_REQUESTS_PER_IP = 8
```

**调优建议**：
- 小型网站：设置较低的 CONCURRENT_REQUESTS_PER_DOMAIN（2-4）
- 大型网站：可以提高到 16-32
- API 端点：通常可以承受更高并发
- 观察服务器响应时间和错误率进行调整

### 5.2 下载延迟

```python
# 固定延迟（秒）
DOWNLOAD_DELAY = 0.5

# 随机延迟（默认开启）
RANDOMIZE_DOWNLOAD_DELAY = True

# 随机延迟范围：DOWNLOAD_DELAY * 0.5 ~ DOWNLOAD_DELAY * 1.5
```

**设置策略**：
- 遵守 robots.txt：设置 DOWNLOAD_DELAY >= 1
- 无限制：设置 DOWNLOAD_DELAY = 0 并使用 AUTOTHROTTLE
- 敏感网站：设置 DOWNLOAD_DELAY = 2 或更高

### 5.3 AutoThrottle 扩展

AutoThrottle 根据服务器响应自动调整爬取速度：

```python
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 60.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0  # 单并发
# AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0  # 双并发
```

**工作原理**：
1. 初始延迟 = AUTOTHROTTLE_START_DELAY
2. 如果响应快，逐渐减小延迟
3. 如果响应慢（>1秒）或出现错误，逐渐增加延迟
4. 最大不超过 AUTOTHROTTLE_MAX_DELAY

### 5.4 DNS 缓存

Scrapy 使用 dnscache 扩展缓存 DNS 查询：

```python
# 默认启用，缓存 60 秒
# DNSCACHE_ENABLED = True
# DNSCACHE_SIZE = 10000
# DNS_TIMEOUT = 10
```

### 5.5 连接池配置

```python
# 每个域名的最大连接池大小
# DOWNLOADER_CLIENTCONNECTION_POOL_SIZE = 6

# 保持连接超时
# DOWNLOADER_CLIENT_TCP_KEEPALIVE = True

# 请求超时
# DOWNLOAD_TIMEOUT = 180

# 连接超时（与服务器建立连接的时间）
# CONNECT_TIMEOUT = 10

# 读取超时（读取响应的时间）
# READ_TIMEOUT = 30
```

### 5.6 推荐配置组合

**保守配置（低资源占用）**：
```python
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 2
AUTOTHROTTLE_ENABLED = True
```

**平衡配置（一般网站）**：
```python
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DOWNLOAD_DELAY = 1
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
```

**高速配置（允许更高资源占用）**：
```python
CONCURRENT_REQUESTS = 64
CONCURRENT_REQUESTS_PER_DOMAIN = 16
DOWNLOAD_DELAY = 0.1
AUTOTHROTTLE_ENABLED = False  # 手动控制
RETRY_TIMES = 2
```

---

## 六、常见问题与调试

### 6.1 常见错误处理

```python
# 处理 404、500 等 HTTP 错误
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError, TimeoutError

class MySpider(scrapy.Spider):
    def start_requests(self):
        yield scrapy.Request(
            url='https://example.com',
            errback=self.handle_error,
            callback=self.parse
        )

    def handle_error(self, failure):
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error(f'HttpError {response.status}: {response.url}')
        elif failure.check(DNSLookupError):
            self.logger.error(f'DNS lookup failed: {failure.request.url}')
        elif failure.check(TimeoutError):
            self.logger.error(f'Timeout: {failure.request.url}')
```

### 6.2 调试技巧

```bash
# 使用 Scrapy Shell 调试
scrapy shell "https://example.com/products"

# 在 Shell 中测试选择器
>>> response.css('h1::text').get()
>>> response.xpath('//div[@class="price"]/text()').getall()

# 测试 ItemLoader
>>> from scrapy.loader import ItemLoader
>>> from myproject.items import ProductItem
>>> loader = ItemLoader(item=ProductItem(), response=response)
>>> loader.add_css('title', 'h1::text')
>>> loader.load_item()

# 查看响应
>>> view(response)  # 在浏览器中打开

# 测试 Pipeline
>>> from myproject.pipelines import DataCleaningPipeline
>>> pipeline = DataCleaningPipeline()
>>> item = {'price': '$19.99', 'title': 'Test Product'}
>>> pipeline.process_item(item, spider)
```

### 6.3 日志管理

```python
# 在 Spider 中使用日志
import logging

class MySpider(scrapy.Spider):
    logger = logging.getLogger(__name__)

    def parse(self, response):
        self.logger.info(f'Parsing {response.url}')
        self.logger.debug(f'Response status: {response.status}')

        if response.status != 200:
            self.logger.warning(f'Non-200 status for {response.url}')
```
$sc$,
    $sc${"questions": [{"id": "q4-1", "type": "multiple_choice", "difficulty": "easy", "topic": "Scrapy架构", "question": "Scrapy 框架的核心引擎（Engine）主要负责什么工作？", "options": ["A. 下载网页内容并返回响应", "B. 协调各组件之间的数据和控制流", "C. 存储抓取的数据到数据库", "D. 管理待爬取的 URL 列表"], "answer": "B", "explanation": "Scrapy Engine（引擎）是框架的核心，负责控制数据流在各个组件（Scheduler、Downloader、Spider、Pipeline）之间的流动，协调整个爬取过程。", "tags": ["Scrapy架构", "核心组件"]}, {"id": "q4-2", "type": "multiple_choice", "difficulty": "easy", "topic": "Scrapy架构", "question": "在 Scrapy 架构中，哪个组件负责将下载完成的 Response 对象分发给对应的 Spider 回调方法？", "options": ["A. Scheduler（调度器）", "B. Downloader（下载器）", "C. Engine（引擎）", "D. Spider（爬虫）"], "answer": "C", "explanation": "Engine 负责接收 Downloader 返回的 Response，然后将其分发给 Spider 的回调方法进行处理。这是 Engine 控制流的一部分。", "tags": ["Scrapy架构", "数据流"]}, {"id": "q4-3", "type": "multiple_choice", "difficulty": "medium", "topic": "Spider类", "question": "Spider 类中的 `start_urls` 属性和 `start_requests()` 方法的主要区别是什么？", "options": ["A. 没有区别，两者是同义词", "B. start_urls 只能设置 GET 请求，start_requests 可以发送任何类型的请求", "C. start_requests 必须返回 Request 对象，start_urls 自动创建 GET 请求", "D. start_urls 的优先级高于 start_requests"], "answer": "C", "explanation": "start_urls 是一个 URL 列表，Scrapy 会自动为每个 URL 创建 GET 请求并调用 parse 方法。start_requests() 是一个可重写的方法，可以返回任何类型的 Request 对象（包括 FormRequest、带有自定义 headers 的请求等），更加灵活。", "tags": ["Spider", "start_requests"]}, {"id": "q4-4", "type": "multiple_choice", "difficulty": "easy", "topic": "Item和ItemLoader", "question": "在 Scrapy 中，以下哪个方法是 ItemLoader 用于从 CSS 选择器结果中提取数据并添加到 Item 的？", "options": ["A. append_css()", "B. extract_css()", "C. add_css()", "D. load_css()"], "answer": "C", "explanation": "ItemLoader 的 add_css() 方法接收 CSS 选择器和字段名，从响应中提取数据并添加到对应字段。类似的方法还有 add_xpath()（使用 XPath）和 add_value()（直接添加值）。", "tags": ["ItemLoader", "CSS选择器"]}, {"id": "q4-5", "type": "multiple_choice", "difficulty": "medium", "topic": "ItemLoader", "question": "在 ItemLoader 中，MapCompose 和 TakeFirst 分别属于什么类型的处理器？", "options": ["A. MapCompose 是输出处理器，TakeFirst 是输入处理器", "B. 两者都是输入处理器", "C. MapCompose 是输入处理器，TakeFirst 是输出处理器", "D. 两者都是输出处理器"], "answer": "C", "explanation": "MapCompose 是输入处理器（Input Processor），用于对每个提取的值应用转换函数。TakeFirst 是输出处理器（Output Processor），用于从结果列表中取出最终值（通常是第一个非空值）。", "tags": ["ItemLoader", "处理器"]}, {"id": "q4-6", "type": "multiple_choice", "difficulty": "easy", "topic": "ItemPipeline", "question": "Scrapy 中 Item Pipeline 的 open_spider、process_item、close_spider 三个方法的执行顺序是什么？", "options": ["A. open_spider -> process_item -> close_spider", "B. process_item -> open_spider -> close_spider", "C. open_spider -> close_spider -> process_item", "D. 没有固定顺序"], "answer": "A", "explanation": "open_spider 在爬虫启动时调用（初始化资源），process_item 在每个 Item 被 Spider yield 时调用（处理数据），close_spider 在爬虫关闭时调用（清理资源）。", "tags": ["ItemPipeline", "生命周期"]}, {"id": "q4-7", "type": "multiple_choice", "difficulty": "medium", "topic": "CSS选择器和XPath", "question": "在 Scrapy 的 Spider 中，如何使用 XPath 提取元素的文本内容？", "options": ["A. response.xpath('//h1::text')", "B. response.xpath('//h1/text()')", "C. response.xpath('//h1').text()", "D. response.xpath('//h1').get_text()"], "answer": "B", "explanation": "XPath 中使用 /text() 函数提取文本内容。注意：CSS 选择器使用 ::text 获取文本，而 XPath 使用 /text()。其他选项分别是 CSS 选择器语法（::text）和 BeautifulSoup 方法（get_text()）。", "tags": ["XPath", "文本提取"]}, {"id": "q4-8", "type": "multiple_choice", "difficulty": "easy", "topic": "Scrapy命令", "question": "以下哪个 Scrapy 命令用于列出当前项目中所有可用的爬虫？", "options": ["A. scrapy show", "B. scrapy list", "C. scrapy spider", "D. scrapy available"], "answer": "B", "explanation": "scrapy list 命令会列出项目中所有可用的 Spider（位于 spiders/ 目录下且继承自 scrapy.Spider 的类）。", "tags": ["Scrapy命令", "项目命令"]}, {"id": "q4-9", "type": "multiple_choice", "difficulty": "medium", "topic": "Request和Response", "question": "在 Scrapy 中，Request 对象的 meta 参数有什么作用？", "options": ["A. 设置请求的元数据（请求头）", "B. 在不同的请求/响应之间传递数据", "C. 指定请求的优先级", "D. 配置请求的重试策略"], "answer": "B", "explanation": "meta 参数用于在请求链中传递数据。例如，从列表页进入详情页时，可以在 yield Request 时通过 meta 传递 category、page 等信息，在详情页的回调方法中通过 response.meta 获取。", "tags": ["Request", "meta"]}, {"id": "q4-10", "type": "multiple_choice", "difficulty": "medium", "topic": "settings配置", "question": "在 Scrapy 中，CONCURRENT_REQUESTS 和 CONCURRENT_REQUESTS_PER_DOMAIN 两个配置项的区别是什么？", "options": ["A. 两者没有区别，是同一个配置的不同写法", "B. CONCURRENT_REQUESTS 是全局并发限制，CONCURRENT_REQUESTS_PER_DOMAIN 是每个域名的并发限制", "C. CONCURRENT_REQUESTS_PER_DOMAIN 限制全局并发，CONCURRENT_REQUESTS 限制每个域名", "D. CONCURRENT_REQUESTS 限制请求数量，CONCURRENT_REQUESTS_PER_DOMAIN 限制下载速度"], "answer": "B", "explanation": "CONCURRENT_REQUESTS 设置全局同时进行的最大请求数。CONCURRENT_REQUESTS_PER_DOMAIN 设置每个域名同时进行的最大请求数。两者可以同时生效，实际并发数取两者中的较小值。", "tags": ["settings", "并发配置"]}, {"id": "q4-11", "type": "coding", "difficulty": "medium", "question": "请补全以下 Spider 类，实现从 start_urls 开始抓取，解析商品列表页，yield Item。请注意使用 CSS 选择器提取数据。\n```python\nimport scrapy\n\nclass ProductSpider(scrapy.Spider):\n    name = 'product_spider'\n    allowed_domains = ['example.com']\n    start_urls = ['https://example.com/products']\n\n    def parse(self, response):\n        # TODO: 使用 CSS 选择器提取商品信息\n        # 商品标题: h3.product-title::text\n        # 商品价格: span.price::text\n        # 商品链接: a.product-link::attr(href)\n        pass\n```", "hint": "使用 ItemLoader 或直接创建 Item", "options": null, "answer": "import scrapy\nfrom ecommerce_spider.items import ProductItem\n\nclass ProductSpider(scrapy.Spider):\n    name = 'product_spider'\n    allowed_domains = ['example.com']\n    start_urls = ['https://example.com/products']\n\n    def parse(self, response):\n        # 提取所有商品卡片\n        for product in response.css('div.product-card'):\n            item = ProductItem()\n            item['title'] = product.css('h3.product-title::text').get()\n            item['price'] = product.css('span.price::text').get()\n            detail_link = product.css('a.product-link::attr(href)').get()\n\n            # 跟进详情页\n            if detail_link:\n                yield response.follow(detail_link, self.parse_detail)\n\n            yield item\n\n        # 处理分页\n        next_page = response.css('a.next-page::attr(href)').get()\n        if next_page:\n            yield response.follow(next_page, self.parse)\n\n    def parse_detail(self, response):\n        # 处理详情页的逻辑（可选）\n        item = ProductItem()\n        item['title'] = response.css('h1::text').get()\n        item['url'] = response.url\n        yield item"}, {"id": "q4-12", "type": "coding", "difficulty": "medium", "question": "请补全以下 Item Pipeline 类，实现数据清洗、去重和 JSON 导出功能。\n```python\nimport json\nfrom scrapy.exceptions import DropItem\n\nclass DataProcessingPipeline:\n    def __init__(self):\n        self.seen_urls = set()\n        self.file = None\n        self.items_count = 0\n\n    def open_spider(self, spider):\n        # TODO: 打开文件准备写入 JSON\n        pass\n\n    def process_item(self, item, spider):\n        # TODO: 清洗价格字段（移除$符号，转换为float）\n        # TODO: 去重检查（基于 product_url）\n        # TODO: 写入文件\n        pass\n\n    def close_spider(self, spider):\n        # TODO: 关闭文件，打印统计信息\n        pass\n```", "hint": "使用 itemadapter 库访问 Item 字段", "options": null, "answer": "import json\nfrom scrapy.exceptions import DropItem\nfrom itemadapter import ItemAdapter\n\nclass DataProcessingPipeline:\n    def __init__(self):\n        self.seen_urls = set()\n        self.file = None\n        self.items_count = 0\n\n    def open_spider(self, spider):\n        self.file = open('products.json', 'w', encoding='utf-8')\n        self.file.write('[')\n\n    def process_item(self, item, spider):\n        adapter = ItemAdapter(item)\n\n        # 清洗价格字段\n        price = adapter.get('price')\n        if price:\n            try:\n                price_clean = price.replace('$', '').replace(',', '').strip()\n                adapter['price'] = float(price_clean)\n            except (ValueError, TypeError):\n                adapter['price'] = None\n\n        # 去重检查\n        url = adapter.get('product_url')\n        if url in self.seen_urls:\n            raise DropItem(f'Duplicate item: {url}')\n        self.seen_urls.add(url)\n\n        # 写入文件\n        if self.items_count > 0:\n            self.file.write(',')\n        self.file.write(json.dumps(dict(item), ensure_ascii=False))\n        self.items_count += 1\n\n        return item\n\n    def close_spider(self, spider):\n        self.file.write(']')\n        self.file.close()\n        spider.logger.info(f'Pipeline finished. Total items: {self.items_count}')"}], "baseline_code": "import scrapy\n\nclass ProductSpider(scrapy.Spider):\n    \"\"\"\n    电商商品爬虫示例\n    \"\"\"\n    name = 'product_spider'\n    allowed_domains = ['example.com']\n    start_urls = ['https://example.com/products']\n\n    def parse(self, response):\n        \"\"\"\n        解析商品列表页\n\n        参数:\n            response: Response 对象\n\n        返回:\n            ProductItem 或 Request 对象\n        \"\"\"\n        # TODO: 使用 CSS 选择器遍历商品卡片\n        # TODO: 提取 title (h3.product-title::text)\n        # TODO: 提取 price (span.price::text)\n        # TODO: 跟进详情页链接\n        pass\n\n    def parse_detail(self, response):\n        \"\"\"\n        解析商品详情页\n\n        参数:\n            response: Response 对象\n\n        返回:\n            ProductItem\n        \"\"\"\n        # TODO: 创建 Item 对象\n        # TODO: 使用 XPath 提取品牌、描述等信息\n        # TODO: 返回完整的 Item\n        pass\n\n\n# ============ Item 定义 ============\nclass ProductItem(scrapy.Item):\n    title = scrapy.Field()\n    price = scrapy.Field()\n    brand = scrapy.Field()\n    description = scrapy.Field()\n    product_url = scrapy.Field()\n    category = scrapy.Field()\n\n\n# ============ Item Pipeline 定义 ============\nclass ProductPipeline:\n    \"\"\"\n    商品数据处理管道\n    \"\"\"\n\n    def __init__(self):\n        self.processed_count = 0\n        self.seen_urls = set()\n\n    def open_spider(self, spider):\n        \"\"\"\n        爬虫启动时调用\n        \"\"\"\n        # TODO: 初始化文件或数据库连接\n        pass\n\n    def process_item(self, item, spider):\n        \"\"\"\n        处理每个 Item\n\n        参数:\n            item: ProductItem 对象\n            spider: Spider 对象\n\n        返回:\n            处理后的 Item\n        \"\"\"\n        # TODO: 清洗价格字段\n        # TODO: 去重检查\n        # TODO: 保存数据\n        pass\n\n    def close_spider(self, spider):\n        \"\"\"\n        爬虫关闭时调用\n        \"\"\"\n        # TODO: 关闭文件或数据库连接\n        # TODO: 打印统计信息\n        pass\n", "test_cases": [{"id": "tc1", "input": "商品列表页 HTML 包含 3 个商品卡片，每个卡片有 title 和 price", "expected": "yield 3 个 ProductItem", "hidden": false, "description": "测试基本商品列表解析"}, {"id": "tc2", "input": "商品列表页 HTML 包含商品卡片和分页链接", "expected": "yield 商品 Item 和下一页 Request", "hidden": false, "description": "测试分页处理"}, {"id": "tc3", "input": "商品价格为 '$19.99' 字符串", "expected": "Pipeline 清洗后为 19.99 (float)", "hidden": true, "description": "测试价格清洗功能"}, {"id": "tc4", "input": "两个 Item 拥有相同的 product_url", "expected": "第二个 Item 被 DropItem 抛出", "hidden": true, "description": "测试 URL 去重功能"}, {"id": "tc5", "input": "使用 response.follow() 处理相对路径 URL", "expected": "Request 对象使用 response.urljoin() 转换后的绝对 URL", "hidden": true, "description": "测试相对路径 URL 处理"}, {"id": "tc6", "input": "Item 的 meta 参数传递 category='electronics'", "expected": "详情页回调方法通过 response.meta['category'] 获取值", "hidden": true, "description": "测试 meta 参数传递"}]}$sc$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 4;
    RAISE NOTICE 'Inserted task_id: %', new_task_id;

    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
        (new_task_id, 'case_1', $sc$商品列表页 HTML 包含 3 个商品卡片，每个卡片有 title 和 price$sc$, $sc$yield 3 个 ProductItem$sc$, false, $sc$测试基本商品列表解析$sc$, 'CONTAINS', 1),
        (new_task_id, 'case_2', $sc$商品列表页 HTML 包含商品卡片和分页链接$sc$, $sc$yield 商品 Item 和下一页 Request$sc$, false, $sc$测试分页处理$sc$, 'CONTAINS', 2),
        (new_task_id, 'case_3', $sc$商品价格为 ''$19.99'' 字符串$sc$, $sc$Pipeline 清洗后为 19.99 (float)$sc$, true, $sc$测试价格清洗功能$sc$, 'CONTAINS', 3),
        (new_task_id, 'case_4', $sc$两个 Item 拥有相同的 product_url$sc$, $sc$第二个 Item 被 DropItem 抛出$sc$, true, $sc$测试 URL 去重功能$sc$, 'CONTAINS', 4),
        (new_task_id, 'case_5', $sc$使用 response.follow() 处理相对路径 URL$sc$, $sc$Request 对象使用 response.urljoin() 转换后的绝对 URL$sc$, true, $sc$测试相对路径 URL 处理$sc$, 'CONTAINS', 5),
        (new_task_id, 'case_6', $sc$Item 的 meta 参数传递 category=''electronics''$sc$, $sc$详情页回调方法通过 response.meta[''category''] 获取值$sc$, true, $sc$测试 meta 参数传递$sc$, 'CONTAINS', 6)
;

    RAISE NOTICE 'Inserted test cases for task_id: %', new_task_id;
END $$;

COMMIT;