-- ============================================================
-- Stage 6: API数据采集
-- practice_id=4, order_in_practice=6
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    4,
    $v$API数据采集$v$,
    'PRACTICE',
    6,
    $v$hard$v$,
    $v$# API 数据采集学习手册

## 一、任务类型

本关卡为网络编程进阶练习，重点掌握通过 Python 程序向外部 RESTful API 发起 HTTP 请求、解析 JSON 响应数据、处理认证与分页、完成大规模数据采集任务。通过本关卡的学习，你将能够使用 requests 或 httpx 库调用各类 Web API，理解不同认证方式的适用场景，掌握分页数据的完整采集策略，并能够实现带重试机制和错误处理的健壮数据采集流程。

## 二、学习环境

- **编程语言**: Python 3.8+
- **运行环境**: 支持网络访问的标准 Python 环境
- **核心依赖**: requests 库（推荐）或 httpx 库（支持异步）
- **输入方式**: 函数接收 API 基础 URL 和必要参数，返回采集到的完整数据列表
- **输出方式**: 返回 Python 列表（每个元素为字典）或直接打印结果
- **评分系统**: 评测程序验证返回数据的完整性、正确性和格式

**安装依赖**:
```bash
pip install requests
# 或使用 httpx（支持异步）
pip install httpx
```

## 三、知识点讲解

### 3.1 RESTful API 基础

REST（Representational State Transfer）是目前最流行的 Web API 设计风格。一个 RESTful API 通过 HTTP 动词表达对资源的操作。

**四种基本 HTTP 方法**:

| 方法 | 含义 | 幂等性 | 典型用途 |
|------|------|--------|----------|
| GET | 获取资源 | 幂等 | 查询数据 |
| POST | 创建资源 | 非幂等 | 提交表单、创建新记录 |
| PUT | 完整更新资源 | 幂等 | 替换整个资源 |
| DELETE | 删除资源 | 幂等 | 删除指定资源 |

**requests 库基本用法**:
```python
import requests

# GET 请求 - 最常用
response = requests.get("https://api.example.com/users", params={"page": 1, "size": 20})
print(response.status_code)   # HTTP 状态码
print(response.json())         # 解析 JSON 响应
print(response.text)           # 原始文本
print(response.headers)        # 响应头

# POST 请求 - 创建资源
payload = {"name": "张三", "age": 25}
response = requests.post("https://api.example.com/users", json=payload)
print(response.status_code)    # 201 表示创建成功
print(response.json())

# PUT 请求 - 完整更新
update_data = {"name": "李四", "age": 30}
response = requests.put("https://api.example.com/users/123", json=update_data)

# DELETE 请求 - 删除资源
response = requests.delete("https://api.example.com/users/123")
print(response.status_code)    # 204 表示删除成功，无返回体
```

**URL 参数传递方式**:
```python
# 方式1: 通过 params 参数自动构建查询字符串
response = requests.get(
    "https://api.example.com/search",
    params={"q": "Python", "page": 1, "per_page": 50}
)
# 请求 URL 自动变为: https://api.example.com/search?q=Python&page=1&per_page=50

# 方式2: 直接拼接 URL
url = "https://api.example.com/users/" + user_id
response = requests.get(url)
```

### 3.2 JSON 响应解析与数据结构

API 响应体通常为 JSON 格式，需要正确解析为 Python 数据结构。

**JSON 数据类型映射**:

| JSON 类型 | Python 类型 |
|-----------|-------------|
| object | dict |
| array | list |
| string | str |
| number (integer) | int |
| number (float) | float |
| boolean | bool |
| null | None |

**解析 JSON 响应**:
```python
import requests

response = requests.get("https://api.example.com/posts/1")

# 安全解析（推荐）：先检查状态码
if response.status_code == 200:
    data = response.json()  # 将 JSON 字符串解析为 Python 对象
    print(data)
    # 假设 data = {"id": 1, "title": "Hello", "author": {"name": "Alice"}}

    # 访问嵌套数据
    print(data["title"])           # "Hello"
    print(data["author"]["name"])  # "Alice"
else:
    print(f"请求失败: {response.status_code}")

# 处理非 JSON 响应
if response.headers.get("Content-Type", "").startswith("application/json"):
    data = response.json()
else:
    print("响应不是 JSON 格式")

# 处理列表型响应（批量数据）
response = requests.get("https://api.example.com/posts")
posts = response.json()  # posts 是一个列表
for post in posts:
    print(post["id"], post["title"])

# 处理分页响应的常见结构
# 假设响应为: {"data": [...], "total": 100, "page": 1}
result = response.json()
items = result["data"]
total = result["total"]
current_page = result["page"]
```

### 3.3 请求认证方式

API 认证是保护数据安全的重要机制。常见的三种认证方式各有适用场景。

**方式一：API Key（最简单）**

API Key 通常作为 URL 查询参数或请求头传递。适用于服务器到服务器的固定身份验证。

```python
import requests

# 方式 A: 作为查询参数
api_key = "your_api_key_here"
response = requests.get(
    "https://api.example.com/data",
    params={"api_key": api_key}
)

# 方式 B: 作为请求头（更安全，URL 中不暴露 key）
headers = {"X-API-Key": api_key}
response = requests.get("https://api.example.com/data", headers=headers)
```

**方式二：Bearer Token（JWT 令牌，最常用）**

OAuth2 访问令牌通过 Authorization 头传递，格式为 `Bearer <token>`。适用于绝大多数现代 Web API。

```python
import requests

access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get("https://api.example.com/protected", headers=headers)

# 简化写法（requests 自动添加 Bearer 前缀）
response = requests.get(
    "https://api.example.com/protected",
    auth=requests.auth.HTTPBearerAuth(access_token)
)
```

**方式三：OAuth2（最完整，适合用户授权场景）**

OAuth2 用于第三方应用代表用户访问资源，需要先获取授权码，再交换为访问令牌。

```python
import requests

# 完整的 OAuth2 流程（简化版）
# Step 1: 引导用户授权，获取 authorization_code
# Step 2: 用 code 换取 access_token
token_url = "https://auth.example.com/oauth/token"
token_data = {
    "grant_type": "authorization_code",
    "code": authorization_code,
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "https://yourapp.com/callback"
}
token_response = requests.post(token_url, data=token_data)
access_token = token_response.json()["access_token"]

# Step 3: 使用 access_token 访问受保护资源
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get("https://api.example.com/user/profile", headers=headers)
```

**认证方式对比**:

| 认证方式 | 安全性 | 复杂度 | 适用场景 |
|----------|--------|--------|----------|
| API Key | 中 | 低 | 固定身份、内部服务 |
| Bearer Token | 高 | 中 | 绝大多数 Web API |
| OAuth2 | 高 | 高 | 第三方用户授权 |

### 3.4 分页处理

API 通常对返回数据量有限制，需要通过分页获取全部数据。

**分页方式一：偏移量分页（offset/limit）**

通过 `offset` 指定跳过的记录数，`limit` 指定每页数量。

```python
import requests

base_url = "https://api.example.com/users"
all_users = []
offset = 0
limit = 100

while True:
    response = requests.get(base_url, params={"offset": offset, "limit": limit})
    data = response.json()
    users = data["data"]  # 当前页数据

    if not users:  # 无更多数据，退出循环
        break

    all_users.extend(users)
    offset += limit
    print(f"已采集 {len(all_users)} 条记录")

print(f"总计采集 {len(all_users)} 条数据")
```

**分页方式二：页码分页（page/page_size）**

通过 `page` 指定当前页码，`page_size` 或 `per_page` 指定每页数量。

```python
import requests

base_url = "https://api.example.com/posts"
all_posts = []
page = 1
per_page = 50
total_pages = float('inf')

while page <= total_pages:
    response = requests.get(base_url, params={"page": page, "per_page": per_page})
    data = response.json()
    posts = data["posts"]
    total_pages = data["total_pages"]  # 从响应中获取总页数

    all_posts.extend(posts)
    print(f"第 {page}/{total_pages} 页，已采集 {len(all_posts)} 条")
    page += 1
```

**分页方式三：游标分页（cursor/page_token，最推荐）**

游标分页通过上一页返回的 cursor 或 next_cursor 定位下一页，适合数据频繁变动的场景，性能更好。

```python
import requests

base_url = "https://api.example.com/feed"
all_items = []
cursor = None

while True:
    params = {"limit": 100}
    if cursor:
        params["cursor"] = cursor

    response = requests.get(base_url, params=params)
    data = response.json()
    items = data["data"]
    cursor = data.get("next_cursor")  # 获取下一页游标

    all_items.extend(items)

    if not cursor:  # 无 next_cursor 表示最后一页
        break

print(f"总计采集 {len(all_items)} 条数据")
```

### 3.5 限流与错误码处理

API 会对请求频率进行限制，超出限制会收到 429 Too Many Requests 错误。

**常见 HTTP 状态码**:

| 状态码 | 含义 | 处理建议 |
|--------|------|----------|
| 200 | 成功 | 正常处理 |
| 201 | 创建成功 | 正常处理 |
| 400 | 请求参数错误 | 检查参数 |
| 401 | 未认证 | 检查 API Key 或 Token |
| 403 | 无权限 | 检查认证和权限 |
| 404 | 资源不存在 | 停止请求 |
| 429 | 请求过于频繁 | 降速后重试 |
| 500 | 服务器内部错误 | 稍后重试 |

**限流信息解析**（通常在响应头中）:
```python
import requests

response = requests.get("https://api.example.com/data")
print(response.headers)

# 常见限流相关响应头
print(response.headers.get("X-RateLimit-Limit"))       # 请求上限次数
print(response.headers.get("X-RateLimit-Remaining"))  # 剩余可用次数
print(response.headers.get("X-RateLimit-Reset"))       # 限流重置时间戳
print(response.headers.get("Retry-After"))              # 需要等待的秒数（429 时出现）
```

**优雅的错误处理**:
```python
import requests

def safe_request(url, params=None, headers=None, max_retries=3):
    """带错误处理的请求函数"""
    import time
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # 限流：等待后重试
                retry_after = int(response.headers.get("Retry-After", 60))
                print(f"触发限流，等待 {retry_after} 秒...")
                time.sleep(retry_after)
            elif response.status_code == 401:
                raise Exception("API 认证失败，请检查 API Key 或 Token")
            elif response.status_code == 404:
                print("资源不存在")
                return None
            elif 400 <= response.status_code < 500:
                print(f"客户端错误: {response.status_code}")
                return None
            elif response.status_code >= 500:
                print(f"服务器错误: {response.status_code}，重试中...")
            else:
                return None

        except requests.exceptions.Timeout:
            print(f"请求超时（尝试 {attempt + 1}/{max_retries}）")
        except requests.exceptions.ConnectionError:
            print(f"连接错误（尝试 {attempt + 1}/{max_retries}）")
        except Exception as e:
            print(f"未知错误: {e}")
            return None

    print("达到最大重试次数")
    return None
```

## 四、常见模式与技巧

### 4.1 自动重试与指数退避

网络请求可能因临时故障失败，指数退避（Exponential Backoff）是最佳实践：每次失败后等待时间翻倍增长。

**使用 requests 库实现重试**:
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time

def create_session_with_retry(total_retries=5, backoff_factor=1.0):
    """创建一个自动重试的 requests Session"""
    session = requests.Session()
    retry_strategy = Retry(
        total=total_retries,
        backoff_factor=backoff_factor,     # 退避因子：1s, 2s, 4s, 8s, 16s...
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# 使用示例
session = create_session_with_retry(total_retries=5, backoff_factor=1.0)
response = session.get("https://api.example.com/data", timeout=10)
print(response.json())
```

**手动实现指数退避**:
```python
import requests
import time
import random

def fetch_with_backoff(url, max_retries=5):
    """手动实现指数退避重试"""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # 指数退避：base * 2^attempt + jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                print(f"限流，等待 {wait_time:.2f} 秒后重试...")
                time.sleep(wait_time)
            elif 500 <= response.status_code < 600:
                wait_time = (2 ** attempt)
                print(f"服务器错误 {response.status_code}，{wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"请求失败: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            wait_time = (2 ** attempt)
            print(f"请求异常: {e}，{wait_time} 秒后重试...")
            time.sleep(wait_time)

    print("重试次数耗尽")
    return None
```

### 4.2 大规模数据分页采集

处理大量数据时，需要分页采集并注意内存管理和采集效率。

**完整的分页采集模式**:
```python
import requests
import time

def collect_all_pages(base_url, api_key, page_param="page", per_page=100):
    """完整分页采集函数模板"""
    headers = {"Authorization": f"Bearer {api_key}"}
    all_data = []
    page = 1

    while True:
        response = requests.get(
            base_url,
            headers=headers,
            params={page_param: page, "per_page": per_page},
            timeout=30
        )

        if response.status_code != 200:
            print(f"请求失败: {response.status_code}")
            break

        data = response.json()
        items = data.get("data", data.get("results", []))

        if not items:
            break

        all_data.extend(items)
        print(f"第 {page} 页: {len(items)} 条，当前累计 {len(all_data)} 条")

        # 检查是否还有下一页
        if page >= data.get("total_pages", page):
            break

        page += 1
        time.sleep(0.5)  # 礼貌性延迟，避免触发限流

    return all_data
```

### 4.3 API 数据质量检查

采集到的数据需要验证质量，确保数据完整可靠。

```python
import requests

def validate_api_data(data, required_fields):
    """验证数据字段完整性"""
    if not isinstance(data, list):
        print("警告: 数据不是列表格式")
        return False

    missing_count = 0
    for item in data:
        for field in required_fields:
            if field not in item or item[field] is None:
                missing_count += 1
                print(f"缺失字段: {field}, 数据ID: {item.get('id', 'unknown')}")

    if missing_count > 0:
        print(f"总计缺失 {missing_count} 个字段")
        return False

    print(f"数据验证通过: {len(data)} 条记录，{len(required_fields)} 个必填字段")
    return True

# 使用示例
data = [
    {"id": 1, "name": "张三", "email": "zhang@example.com"},
    {"id": 2, "name": "李四", "email": None},
]
validate_api_data(data, ["id", "name", "email"])
# 输出: 缺失字段: email, 数据ID: 2
#       总计缺失 1 个字段
```

## 五、评测标准

1. **API 调用正确性**: 正确使用 HTTP 方法（GET/POST/PUT/DELETE），URL 参数传递正确
2. **JSON 解析准确性**: 正确解析响应数据，正确访问嵌套字典和列表
3. **认证方式正确性**: 根据题目要求正确选择和应用 API Key / Bearer Token / OAuth2
4. **分页数据完整性**: 能够完整采集所有分页数据，不遗漏任何记录
5. **错误处理健壮性**: 能够处理限流（429）、超时、网络错误等异常情况
6. **重试机制有效性**: 实现了指数退避重试，避免雪崩式重试

**常见错误**:
- 直接打印 `response` 对象而不是 `response.json()` 的结果
- 忽略了分页，导致只采集到第一页数据
- 在限流响应后立即重试，没有等待足够时间
- 认证 Token 拼写错误（如 `Bearer` 写成 `bearer`）
- 超时设置过长或过短，影响采集效率
$v$,
    $v${"questions": [{"id": "q6-1", "type": "concept", "difficulty": "easy", "question": "在 RESTful API 中，哪个 HTTP 方法用于获取资源数据？", "hint": "对应“读”操作", "options": ["A. POST", "B. PUT", "C. GET", "D. DELETE"], "answer": "C", "explanation": "GET 方法用于从服务器获取资源数据，是 RESTful API 中最常用的读操作。POST 用于创建资源，PUT 用于完整更新资源，DELETE 用于删除资源。"}, {"id": "q6-2", "type": "concept", "difficulty": "easy", "question": "在 requests 库中，将 JSON 响应体解析为 Python 对象的正确方法是？", "hint": "requests 库提供了专门的 JSON 解析方法", "options": ["A. response.text", "B. json.loads(response)", "C. response.json()", "D. json.parse(response)"], "answer": "C", "explanation": "response.json() 是 requests 库内置的 JSON 解析方法，直接将 JSON 字符串转换为 Python 对象（字典或列表）。json.loads(response) 需要先取 response.text，json.parse 不是标准方法。"}, {"id": "q6-3", "type": "concept", "difficulty": "easy", "question": "HTTP 状态码 429 的含义是？", "hint": "请求频率过高", "options": ["A. 服务器内部错误", "B. 未认证", "C. 请求过于频繁", "D. 资源不存在"], "answer": "C", "explanation": "429 Too Many Requests 表示客户端在规定时间内发送了过多请求，触发了服务器的限流机制。通常需要等待 Retry-After 头指定的时间后再重试。"}, {"id": "q6-4", "type": "concept", "difficulty": "easy", "question": "Bearer Token 认证方式中，令牌应该放在哪个 HTTP 头中？", "hint": "Authorization 头", "options": ["A. X-API-Key", "B. Content-Type", "C. Authorization: Bearer <token>", "D. Token: <token>"], "answer": "C", "explanation": "Bearer Token 通过 Authorization 头传递，格式为 'Authorization: Bearer <token>'。X-API-Key 是 API Key 认证的常用头，Content-Type 用于指定请求体格式。"}, {"id": "q6-5", "type": "concept", "difficulty": "easy", "question": "以下哪种分页方式最适合数据频繁变动的 API？", "hint": "通过游标定位下一页", "options": ["A. offset/limit 分页", "B. page/page_size 分页", "C. cursor（游标）分页", "D. 无限制返回所有数据"], "answer": "C", "explanation": "游标（cursor）分页通过上一页返回的 cursor 定位下一页，不依赖固定的偏移量或页码，在数据频繁变动的场景下能避免重复或遗漏记录，是最推荐的分页方式。"}, {"id": "q6-6", "type": "calculation", "difficulty": "medium", "question": "使用指数退避重试策略，重试第 3 次（从0开始计数）时，backoff_factor=1 时应等待多少秒（不考虑随机 jitter）？", "hint": "等待时间 = backoff_factor × 2^attempt", "options": null, "answer": "8", "explanation": "指数退避公式为 wait = backoff_factor × 2^attempt。第3次重试时 attempt=3，wait = 1 × 2^3 = 8 秒。依次为：第0次1s、第1次2s、第2次4s、第3次8s。"}, {"id": "q6-7", "type": "calculation", "difficulty": "medium", "question": "假设 API 每次返回最多 100 条记录，共有 350 条数据。使用 offset/limit 分页方式，需要请求几次才能获取全部数据？", "hint": "需要 ceil(350/100) 次请求", "options": null, "answer": "4", "explanation": "offset/limit 分页每页 100 条。offset=0 取第1-100条，offset=100 取第101-200条，offset=200 取第201-300条，offset=300 取第301-350条。需要 4 次请求。ceil(350/100)=4。"}, {"id": "q6-8", "type": "calculation", "difficulty": "medium", "question": "执行以下代码后，data 变量的值是什么？\n\nimport requests\nresponse = requests.get('https://api.example.com/user', params={'name': 'Alice'})\ndata = response.json()\n# 假设服务器返回: {\"id\": 1, \"name\": \"Alice\"}", "hint": "params 参数会自动构建查询字符串", "options": null, "answer": "{\"id\": 1, \"name\": \"Alice\"}", "explanation": "response.json() 将 JSON 响应体解析为 Python 字典。params={'name': 'Alice'} 会自动构建查询字符串，因此 data 的值就是服务器返回的字典 {'id': 1, 'name': 'Alice'}。"}, {"id": "q6-9", "type": "coding", "difficulty": "medium", "question": "编写一个函数 fetch_with_retry，接收 url 参数，发起 GET 请求。如果响应状态码为 200 则返回 response.json()；如果状态码为 429 或 500-599 则等待 (2 ** attempt) 秒后重试，最多重试 3 次（attempt 从 0 开始）。重试次数耗尽返回 None。", "hint": "使用循环和状态码判断", "options": null, "answer": "def fetch_with_retry(url, max_retries=3):\n    import time, requests\n    for attempt in range(max_retries):\n        response = requests.get(url)\n        if response.status_code == 200:\n            return response.json()\n        elif response.status_code == 429 or 500 <= response.status_code < 600:\n            wait_time = 2 ** attempt\n            time.sleep(wait_time)\n        else:\n            return None\n    return None", "explanation": "函数使用 for 循环实现重试逻辑。status_code==200 时返回解析后的 JSON；429 或 5xx 时计算退避时间并等待后继续循环；其他错误码直接返回 None。循环结束后返回 None 表示重试耗尽。"}, {"id": "q6-10", "type": "coding", "difficulty": "hard", "question": "编写一个函数 collect_all_pages，接收 base_url 和 api_key 参数（使用 Bearer Token 认证），使用分页参数 page（初始为1）和 per_page=50，循环请求直到数据为空。所有数据聚合在一个列表中返回。", "hint": "Bearer Token 放在 Authorization 头，循环直到数据为空", "options": null, "answer": "def collect_all_pages(base_url, api_key):\n    import requests\n    headers = {'Authorization': f'Bearer {api_key}'}\n    all_data = []\n    page = 1\n    per_page = 50\n    while True:\n        response = requests.get(base_url, headers=headers,\n            params={'page': page, 'per_page': per_page})\n        data = response.json()\n        items = data.get('data', [])\n        if not items:\n            break\n        all_data.extend(items)\n        page += 1\n    return all_data", "explanation": "函数首先构造带 Bearer Token 的请求头，然后进入 while True 循环。循环中请求当前页，提取 items，累加到 all_data。当 items 为空时退出循环，返回完整数据列表。"}], "baseline_code": "def fetch_api_data(base_url, api_key):\n    \"\"\"\n    采集 API 数据，支持分页。\n    base_url: API 基础地址\n    api_key: Bearer Token 认证密钥\n    返回: 所有数据的列表\n    \"\"\"\n    import requests\n    pass\n"}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 6;
    RAISE NOTICE 'Inserted task_id: %', new_task_id;

    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
        (new_task_id, 'case_1', $v$https://api.example.com/data | Bearer sk_test_123456$v$, $v$data_length >= 50$v$, false, $v$https://api.example.com/data | Bearer sk_test_123456$v$, 'EXACT_MATCH', 1),
        (new_task_id, 'case_2', $v$https://api.example.com/users | Bearer sk_test_789012$v$, $v$data_length >= 30$v$, false, $v$https://api.example.com/users | Bearer sk_test_789012$v$, 'EXACT_MATCH', 2),
        (new_task_id, 'case_3', $v$https://api.example.com/posts | Bearer sk_live_abc123$v$, $v$data_length >= 100$v$, true, $v$https://api.example.com/posts | Bearer sk_live_abc123$v$, 'EXACT_MATCH', 3),
        (new_task_id, 'case_4', $v$https://api.example.com/orders | Bearer sk_live_xyz789$v$, $v$data_length >= 20$v$, true, $v$https://api.example.com/orders | Bearer sk_live_xyz789$v$, 'EXACT_MATCH', 4),
        (new_task_id, 'case_5', $v$https://api.example.com/products | Bearer sk_prod_def456$v$, $v$data_length >= 60$v$, true, $v$https://api.example.com/products | Bearer sk_prod_def456$v$, 'EXACT_MATCH', 5),
        (new_task_id, 'case_6', $v$https://api.example.com/comments | Bearer sk_prod_ghi789$v$, $v$data_length >= 40$v$, true, $v$https://api.example.com/comments | Bearer sk_prod_ghi789$v$, 'EXACT_MATCH', 6);

    RAISE NOTICE 'Inserted 6 test cases for task_id: %', new_task_id;
END $$;

COMMIT;
