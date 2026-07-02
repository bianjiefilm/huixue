-- DC9: 日志格式解析与采集
DO $$
DECLARE new_task_id INTEGER;
BEGIN
  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 9;
  IF new_task_id IS NOT NULL THEN
    DELETE FROM task_tests WHERE task_id = new_task_id;
    DELETE FROM tasks WHERE id = new_task_id;
  END IF;

  INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
  VALUES (
    4,
    '日志格式解析与采集',
    'PRACTICE',
    9,
    'intermediate',
    $dc9$# 日志格式解析与采集学习手册

## 一、任务类型

本阶段任务为**解析 Nginx 日志和 JSON Lines 日志，提取统计信息**。

### 任务描述

日志是服务器运行状态的重要记录，Nginx 访问日志记录了每一次 HTTP 请求的详细信息。通过正则表达式和结构化解析技术，我们可以从海量日志中提取有价值的数据，如访问量统计、热门资源、错误分析等。

### 任务目标

- 掌握 Nginx combined 日志格式的结构
- 使用 Python 正则表达式解析日志行
- 解析 JSON Lines 格式的结构化日志
- 统计 IP 访问量、状态码分布、热门 URL
- 配置 Python logging 模块输出日志
- 使用日志切割工具管理日志文件大小

---

## 二、学习环境

- **Python 版本**: Python 3.8+
- **内置库**: `re`, `json`, `logging`, `collections`, `datetime`, `io`
- **无需外部依赖**: 所有功能均使用 Python 标准库实现

---

## 三、知识点讲解

### 知识点 1: Nginx 访问日志格式

Nginx 默认使用 **combined** 日志格式，记录每一次 HTTP 请求的完整信息：

```
log_format combined '$remote_addr - $remote_user [$time_local] '
                    '"$request"' '$status $body_bytes_sent '
                    '"$http_referer"' '"$http_user_agent"';
```

**实际日志行示例**：

```
192.168.1.100 - - [10/Jan/2026:13:55:36 +0800] "GET /index.html HTTP/1.1" 200 612 "https://example.com/" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
```

**各字段含义**：

| 字段序号 | 字段名 | 示例值 | 说明 |
|---------|--------|--------|------|
| 1 | remote_addr | 192.168.1.100 | 客户端 IP 地址 |
| 2 | remote_user | - | 远程用户名（未认证时为 -） |
| 3 | time_local | [10/Jan/2026:13:55:36 +0800] | 本地时间，格式：DD/Mon/YYYY:HH:MM:SS TZ |
| 4 | request | "GET /index.html HTTP/1.1" | 请求行：方法 路径 协议版本 |
| 5 | status | 200 | HTTP 状态码 |
| 6 | body_bytes_sent | 612 | 发送给客户端的字节数 |
| 7 | http_referer | "https://example.com/" | 来源页面 URL |
| 8 | http_user_agent | "Mozilla/5.0..." | 客户端 User-Agent |

**常见 HTTP 状态码**：

- `200`: OK，请求成功
- `301/302`: 永久/临时重定向
- `400`: Bad Request，请求语法错误
- `401`: Unauthorized，需要认证
- `403`: Forbidden，禁止访问
- `404`: Not Found，资源不存在
- `500`: Internal Server Error，服务器内部错误
- `502/503`: Bad Gateway/Service Unavailable，网关或服务不可用

---

### 知识点 2: Python 正则解析日志

使用 `re` 模块的 `re.compile()` 编译正则表达式，然后匹配日志行：

```python
import re

# Nginx combined 日志正则
# 各字段: IP - - [时间] "请求" 状态码 字节 "来源" "UA"
NGINX_PATTERN = re.compile(
    r'^(\S+) '                # remote_addr
    r'(\S+) '                 # remote_user
    r'(\S+) '                 # remote_ident (always -)
    r'\[([^\]]+)\] '         # time_local
    r'"([^"]+)" '            # request
    r'(\d{3}) '               # status
    r'(\S+)'                  # body_bytes_sent
    r'(?:\s+"([^"]*)"\s+"([^"]*)")?'  # referer and user_agent (optional)
)

# 简化版正则（推荐）
NGINX_SIMPLE = re.compile(
    r'^(\S+) - - \[([^\]]+)\] '
    r'"(\S+) (\S+) \S+" '
    r'(\d{3}) (\d+|-)'
)
```

**正则分组提取字段**：

```python
def parse_nginx_log(line):
    """解析单行 Nginx 日志"""
    match = NGINX_SIMPLE.match(line)
    if not match:
        return None
    groups = match.groups()
    ip = groups[0]
    time_str = groups[3]
    request_str = groups[4]
    status = groups[5]
    bytes_sent = groups[6]
    # Parse method and path from request string
    parts = request_str.split(' ')
    method = parts[0] if len(parts) > 0 else ''
    path = parts[1] if len(parts) > 1 else ''
    return {
        'ip': ip,
        'time': time_str,
        'method': method,
        'path': path,
        'status': int(status),
        'bytes': bytes_sent if bytes_sent != '-' else 0
    }
```

**常用正则技巧**：

- `\S+`: 匹配非空白字符（适用于 IP、路径等）
- `\d{3}`: 精确匹配 3 位数字（状态码）
- `\[([^\]]+)\]`: 捕获方括号内的内容
- `"([^"]+)"`: 捕获双引号内的内容
- `(?:...)`: 非捕获组，不创建分组

---

### 知识点 3: 结构化日志 (JSON Lines)

**JSON Lines** 是一种流式日志格式，每行是一个有效的 JSON 对象：

```json
{"level": "INFO", "time": "2026-01-10T13:55:36", "msg": "Server started", "port": 8080}
{"level": "WARNING", "time": "2026-01-10T13:56:01", "msg": "High memory usage", "usage": 85}
{"level": "ERROR", "time": "2026-01-10T13:57:15", "msg": "Connection timeout", "host": "db-01"}
```

**解析 JSON Lines**：

```python
import json

def parse_jsonl_line(line):
    """解析单行 JSON Lines，返回字典"""
    line = line.strip()
    if not line:
        return None
    return json.loads(line)

def read_jsonl(filepath):
    """读取整个 JSON Lines 文件，返回字典列表"""
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            record = parse_jsonl_line(line)
            if record:
                records.append(record)
    return records
```

**逐行处理大文件**（内存友好）：

```python
def process_jsonl_stream(filepath):
    """流式处理 JSON Lines，适合超大文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            record = parse_jsonl_line(line)
            if record:
                # 在此处理每条记录
                yield record
```

---

### 知识点 4: 日志文件读取

**基础文件操作**：

```python
# 基本读取模式
f = open('access.log', 'r', encoding='utf-8')
content = f.read()
f.close()

# 推荐写法：使用 with 语句自动关闭
with open('access.log', 'r', encoding='utf-8') as f:
    content = f.read()

# 按行读取
with open('access.log', 'r', encoding='utf-8') as f:
    for line in f:
        print(line.strip())

# readlines() 读取所有行到列表
with open('access.log', 'r', encoding='utf-8') as f:
    lines = f.readlines()
```

**编码处理**：

```python
# 常见中文日志编码：GBK、GB2312
with open('error.log', 'r', encoding='gbk') as f:
    for line in f:
        print(line.strip())

# 自动检测编码（需要 chardet 库）
import chardet

def detect_encoding(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read(10000)
    return chardet.detect(raw)['encoding']

# 二进制读取后解码
with open('access.log', 'rb') as f:
    content = f.read().decode('utf-8', errors='replace')
```

**大文件处理策略**：

```python
# 分块读取
CHUNK_SIZE = 8192
with open('large.log', 'r', encoding='utf-8') as f:
    while True:
        chunk = f.read(CHUNK_SIZE)
        if not chunk:
            break
        # 处理 chunk
```

---

### 知识点 5: 日志数据分析

**IP 访问统计**：

```python
from collections import Counter

def count_ips(log_lines):
    """统计各 IP 的访问次数"""
    ip_counter = Counter()
    for line in log_lines:
        parsed = parse_nginx_log(line)
        if parsed:
            ip_counter[parsed['ip']] += 1
    return ip_counter.most_common(10)  # Top 10

# 输出 Top 10 IP
for ip, count in count_ips(lines):
    print(f"{ip}: {count} 次")
```

**状态码分布**：

```python
def status_distribution(log_lines):
    """统计各状态码的出现次数"""
    status_counter = Counter()
    for line in log_lines:
        parsed = parse_nginx_log(line)
        if parsed:
            status_counter[parsed['status']] += 1
    return dict(sorted(status_counter.items()))

# 输出状态码分布
for status, count in status_distribution(lines).items():
    pct = count / total * 100
    print(f"{status}: {count} ({pct:.1f}%)")
```

**热门 URL 统计**：

```python
def top_urls(log_lines, limit=10):
    """统计最常访问的 URL"""
    url_counter = Counter()
    for line in log_lines:
        parsed = parse_nginx_log(line)
        if parsed:
            url_counter[parsed['path']] += 1
    return url_counter.most_common(limit)
```

**综合分析函数**：

```python
def analyze_nginx_log(filepath):
    """综合分析 Nginx 日志"""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total = len(lines)
    ip_stats = Counter()
    status_stats = Counter()
    url_stats = Counter()

    for line in lines:
        parsed = parse_nginx_log(line)
        if parsed:
            ip_stats[parsed['ip']] += 1
            status_stats[parsed['status']] += 1
            url_stats[parsed['path']] += 1

    return {
        'total_requests': total,
        'unique_ips': len(ip_stats),
        'top_ips': ip_stats.most_common(5),
        'status_distribution': dict(status_stats),
        'top_urls': url_stats.most_common(5)
    }
```

---

### 知识点 6: Python logging 模块

Python 标准库的 `logging` 模块提供灵活的日志记录功能：

**基础配置**：

```python
import logging

# 最简配置：输出到控制台
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("程序开始运行")
logger.warning("内存使用率较高")
logger.error("数据库连接失败")
```

**配置日志格式器 (Formatter)**：

```python
import logging

# 创建 Logger
logger = logging.getLogger('myapp')
logger.setLevel(logging.DEBUG)

# 创建 Formatter
formatter = logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建 Handler（输出到文件）
file_handler = logging.FileHandler('app.log', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# 创建 Handler（输出到控制台）
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# 添加 Handler 到 Logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
```

**输出到文件 + 控制台组合**：

```python
import logging

def setup_logging(log_file='app.log'):
    """配置日志：同时输出到文件和控制台"""
    logger = logging.getLogger('myapp')
    logger.setLevel(logging.DEBUG)

    # 格式
    fmt = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    formatter = logging.Formatter(fmt, datefmt='%H:%M:%S')

    # 文件 Handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    # 控制台 Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

logger = setup_logging()
```

---

### 知识点 7: 日志切割

当日志文件增长过大时，需要使用日志切割来管理。Python `logging` 模块提供两种切割方式：

**按文件大小切割 (RotatingFileHandler)**：

```python
import logging
from logging.handlers import RotatingFileHandler

def setup_rotating_log(log_file='app.log'):
    """配置按大小切割的日志"""
    logger = logging.getLogger('myapp')
    logger.setLevel(logging.DEBUG)

    # 最多保留 5 个备份文件，每个最大 10MB
    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    handler.setLevel(logging.DEBUG)

    fmt = '%(asctime)s [%(levelname)s] %(message)s'
    handler.setFormatter(logging.Formatter(fmt, datefmt='%H:%M:%S'))

    logger.addHandler(handler)
    return logger

# 当文件达到 10MB 时，自动切割：
# app.log -> app.log.1 -> app.log.2 -> ... -> app.log.5
# 超过 5 个备份时，最旧的会被删除
```

**按时间切割 (TimedRotatingFileHandler)**：

```python
import logging
from logging.handlers import TimedRotatingFileHandler

def setup_timed_log(log_file='app.log'):
    """配置按时间切割的日志"""
    logger = logging.getLogger('myapp')
    logger.setLevel(logging.DEBUG)

    # 每天凌晨 0 点切割一次，保留 7 天
    handler = TimedRotatingFileHandler(
        filename=log_file,
        when='midnight',      # 切割时间：midnight, H, D, W0-W6
        interval=1,            # 间隔
        backupCount=7,        # 保留 7 个备份
        encoding='utf-8'
    )
    handler.setLevel(logging.DEBUG)

    # 添加 .log 扩展名（可选）
    handler.suffix = '%Y-%m-%d.log'

    fmt = '%(asctime)s [%(levelname)s] %(message)s'
    handler.setFormatter(logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S'))

    logger.addHandler(handler)
    return logger
```

**按时间 + 大小切割的常用配置**：

```python
# 按大小切割（适合高流量服务）
handler = RotatingFileHandler(
    filename='access.log',
    maxBytes=100 * 1024 * 1024,  # 100MB
    backupCount=10
)

# 按天切割（适合日常分析）
handler = TimedRotatingFileHandler(
    filename='access.log',
    when='D',           # D=按天, H=按小时
    interval=1,
    backupCount=30      # 保留 30 天
)

# 按小时切割（适合高频日志）
handler = TimedRotatingFileHandler(
    filename='access.log',
    when='H',           # H=按小时
    interval=6,         # 每 6 小时
    backupCount=24
)
```

---

## 四、实战代码

### 实战 1: Nginx 日志解析

```python
import re
from collections import Counter

# Nginx combined 日志正则
NGINX_PATTERN = re.compile(
    r'^(\S+) - - \[([^\]]+)\] '
    r'"(\S+) (\S+) \S+" '
    r'(\d{3}) (\d+|-)'
)

def parse_nginx_log(line):
    """解析 Nginx 日志行，返回字段字典或 None"""
    match = NGINX_PATTERN.match(line.strip())
    if not match:
        return None
    ip, time_local, method, path, status, bytes_sent = match.groups()
    return {
        'ip': ip,
        'time': time_local,
        'method': method,
        'path': path,
        'status': int(status),
        'bytes': 0 if bytes_sent == '-' or not bytes_sent else int(bytes_sent)
    }

def analyze_nginx_lines(lines):
    """分析多行 Nginx 日志，返回统计信息"""
    ip_counter = Counter()
    status_counter = Counter()
    url_counter = Counter()
    total = 0

    for line in lines:
        parsed = parse_nginx_log(line)
        if parsed:
            total += 1
            ip_counter[parsed['ip']] += 1
            status_counter[parsed['status']] += 1
            url_counter[parsed['path']] += 1

    return {
        'total': total,
        'unique_ips': len(ip_counter),
        'top_ip': ip_counter.most_common(1)[0] if ip_counter else None,
        'status_distribution': dict(status_counter),
        'top_urls': url_counter.most_common(5)
    }

# 示例使用
if __name__ == '__main__':
    sample_logs = [
        '192.168.1.100 - - [10/Jan/2026:13:55:36 +0800] "GET /index.html HTTP/1.1" 200 612',
        '192.168.1.101 - - [10/Jan/2026:13:56:01 +0800] "POST /api/login HTTP/1.1" 200 128',
        '192.168.1.100 - - [10/Jan/2026:13:57:15 +0800] "GET /api/data HTTP/1.1" 404 0',
    ]
    result = analyze_nginx_lines(sample_logs)
    print(result)
```

### 实战 2: JSON Lines 解析

```python
import json
from collections import Counter

def parse_jsonl_line(line):
    """解析单行 JSON Lines，返回字典"""
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None

def count_levels(jsonl_lines):
    """统计日志级别分布"""
    level_counter = Counter()
    for line in jsonl_lines:
        record = parse_jsonl_line(line)
        if record and 'level' in record:
            level_counter[record['level']] += 1
    return dict(level_counter)

def extract_messages(jsonl_lines):
    """提取所有消息"""
    messages = []
    for line in jsonl_lines:
        record = parse_jsonl_line(line)
        if record and 'msg' in record:
            messages.append(record['msg'])
    return messages

def filter_by_level(jsonl_lines, level):
    """按级别过滤日志"""
    results = []
    for line in jsonl_lines:
        record = parse_jsonl_line(line)
        if record and record.get('level') == level:
            results.append(record)
    return results

# 示例使用
if __name__ == '__main__':
    sample_jsonl = [
        '{"level": "INFO", "msg": "Server started", "port": 8080}',
        '{"level": "DEBUG", "msg": "Config loaded", "path": "/etc/app"}',
        '{"level": "ERROR", "msg": "Connection failed", "host": "db-01"}',
        '{"level": "INFO", "msg": "Request handled", "duration": 45}',
    ]
    print(count_levels(sample_jsonl))
    print(extract_messages(sample_jsonl))
    print(filter_by_level(sample_jsonl, 'ERROR'))
```
$dc9$,
    $dc9${"multiple_choice": [{"id": "mc01", "question": "Nginx combined 日志格式中，状态码 404 的含义是？", "options": ["服务器内部错误", "资源不存在（Not Found）", "禁止访问（Forbidden）", "请求超时"], "answer": "B", "explanation": "HTTP 状态码 404 表示 Not Found，即请求的资源在服务器上不存在。"}, {"id": "mc02", "question": "以下哪个正则表达式能正确匹配 Nginx 日志中的客户端 IP 地址（第一个字段）？", "options": ["\\[(\\S+)\\]", "^(\\S+) - -", "(\\d+\\.\\d+\\.\\d+\\.\\d+)", "remote_addr: (\\S+)"], "answer": "B", "explanation": "Nginx combined 日志格式中，IP 地址是第一个字段，后面跟着 ' - - '，正则 ^(\\S+) - - 可以匹配。"}, {"id": "mc03", "question": "JSON Lines 格式的特点是什么？", "options": ["整个文件是一个大的 JSON 数组", "每行是一个独立的有效 JSON 对象", "使用分号分隔多个 JSON 对象", "必须包含特定的换行符标记"], "answer": "B", "explanation": "JSON Lines 格式的核心特点是每行都是一个完整、独立、可解析的 JSON 对象，便于流式处理。"}, {"id": "mc04", "question": "使用 Python 读取日志文件时，以下哪种方式是正确的？", "options": ["f = open('log.txt'); content = f.read(); f.close()", "with open('log.txt', 'r') as f: content = f.read()", "read('log.txt')", "File.open('log.txt').read()"], "answer": "B", "explanation": "with open() 语句是 Python 读取文件的标准方式，能确保文件正确关闭，是最佳实践。"}, {"id": "mc05", "question": "Python logging 模块中，用于设置日志输出格式的类是？", "options": ["Handler", "Logger", "Formatter", "Filter"], "answer": "C", "explanation": "Formatter 负责定义日志输出的格式，包括时间戳、日志级别、消息内容等格式字符串。"}, {"id": "mc06", "question": "RotatingFileHandler 在什么情况下会创建备份文件？", "options": ["每当写入日志时", "当日志文件大小超过 maxBytes 设定值时", "每天凌晨自动创建", "程序启动时"], "answer": "B", "explanation": "RotatingFileHandler 会监控日志文件大小，当达到 maxBytes 限制时，自动将当前日志重命名为 .1 等备份文件，并创建新的日志文件。"}, {"id": "mc07", "question": "Nginx combined 日志中，时间字段 time_local 的格式是什么？", "options": ["YYYY-MM-DD HH:MM:SS", "DD/Mon/YYYY:HH:MM:SS +TZ", "Mon DD YYYY HH:MM:SS", "Unix 时间戳"], "answer": "B", "explanation": "Nginx combined 日志的时间格式为 [DD/Mon/YYYY:HH:MM:SS +TZ]，例如 [10/Jan/2026:13:55:36 +0800]。"}, {"id": "mc08", "question": "解析 JSON Lines 文件时，应该如何处理大文件以节省内存？", "options": ["一次性读取所有行到内存", "使用 readlines() 读取", "逐行读取并流式处理", "先将文件压缩再读取"], "answer": "C", "explanation": "对于大文件，应使用逐行读取的流式处理方式（如 for line in f），避免一次性加载全部内容到内存。"}], "programming": [{"id": "prog01", "title": "使用正则解析 Nginx 日志行", "description": "编写函数 parse_nginx_log(line)，使用正则表达式解析单行 Nginx combined 日志，返回包含各字段的字典。", "difficulty": "intermediate", "baseline_code": "import re\n\n# Nginx combined 日志正则\nNGINX_PATTERN = re.compile(\n    r'^(\\S+) - - \\[([^\\]]+)\\] '\n    r'\"(\\S+) (\\S+) \\S+\" '\n    r'(\\d{3}) (\\d+|-)'\n)\n\ndef parse_nginx_log(line):\n    # TODO: 使用 NGINX_PATTERN 匹配日志行\n    # 返回字典: {ip, time, method, path, status, bytes}\n    pass", "test_cases": [{"id": "tc01", "input": "192.168.1.100 - - [10/Jan/2026:13:55:36 +0800] \"GET /index.html HTTP/1.1\" 200 612", "expected": {"ip": "192.168.1.100", "time": "10/Jan/2026:13:55:36 +0800", "method": "GET", "path": "/index.html", "status": 200, "bytes": 612}, "hidden": false}, {"id": "tc02", "input": "10.0.0.55 - - [15/Mar/2026:08:30:15 +0000] \"POST /api/submit HTTP/1.1\" 201 45", "expected": {"ip": "10.0.0.55", "time": "15/Mar/2026:08:30:15 +0000", "method": "POST", "path": "/api/submit", "status": 201, "bytes": 45}, "hidden": false}, {"id": "tc03", "input": "172.16.0.1 - - [20/Apr/2026:22:10:00 +0800] \"DELETE /users/123 HTTP/1.1\" 204 0", "expected": {"ip": "172.16.0.1", "time": "20/Apr/2026:22:10:00 +0800", "method": "DELETE", "path": "/users/123", "status": 204, "bytes": 0}, "hidden": false}, {"id": "tc04", "input": "invalid log line without proper format", "expected": null, "hidden": false}, {"id": "tc05", "input": "203.0.113.42 - - [01/Feb/2026:14:20:33 +0800] \"GET /static/app.js HTTP/1.1\" 304 -", "expected": {"ip": "203.0.113.42", "time": "01/Feb/2026:14:20:33 +0800", "method": "GET", "path": "/static/app.js", "status": 304, "bytes": 0}, "hidden": true}]}, {"id": "prog02", "title": "解析 JSON Lines 日志并统计", "description": "编写函数 parse_jsonl_line(line) 解析单行 JSON Lines，以及统计日志级别分布的函数 count_levels(lines)。", "difficulty": "intermediate", "baseline_code": "import json\nfrom collections import Counter\n\ndef parse_jsonl_line(line):\n    # TODO: 解析单行 JSON Lines\n    # 忽略空行，解析失败返回 None\n    pass\n\ndef count_levels(lines):\n    # TODO: 统计各日志级别的出现次数\n    # 返回 Counter 对象或字典\n    pass", "test_cases": [{"id": "tc01", "input": "{\"level\": \"INFO\", \"msg\": \"Server started\"}", "expected": {"level": "INFO", "msg": "Server started"}, "hidden": false}, {"id": "tc02", "input": "{\"level\": \"ERROR\", \"msg\": \"Connection failed\", \"host\": \"db-01\"}", "expected": {"level": "ERROR", "msg": "Connection failed", "host": "db-01"}, "hidden": false}, {"id": "tc03", "input": "  {\"level\": \"DEBUG\", \"count\": 42}  ", "expected": {"level": "DEBUG", "count": 42}, "hidden": false}, {"id": "tc04", "input": "", "expected": null, "hidden": false}, {"id": "tc05", "input": "not valid json at all", "expected": null, "hidden": false}, {"id": "tc06", "input": "[\"INFO\", \"ERROR\", \"INFO\", \"WARNING\", \"INFO\", \"ERROR\", \"ERROR\"]", "expected": {"INFO": 3, "ERROR": 3, "WARNING": 1}, "hidden": false}, {"id": "tc07", "input": "{\"level\": \"INFO\"}\n{\"level\": \"WARNING\"}\n{\"level\": \"ERROR\"}", "expected": {"INFO": 1, "WARNING": 1, "ERROR": 1}, "hidden": true}]}]}$dc9$,
    NOW(),
    NOW()
  );

  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 9;

  INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
  VALUES
    (new_task_id, 'tc01', $dc9$"192.168.1.100 - - [10/Jan/2026:13:55:36 +0800] \"GET /index.html HTTP/1.1\" 200 612"$dc9$, $dc9${"ip": "192.168.1.100", "time": "10/Jan/2026:13:55:36 +0800", "method": "GET", "path": "/index.html", "status": 200, "bytes": 612}$dc9$, False, '', 'CONTAINS', 1),
    (new_task_id, 'tc02', $dc9$"10.0.0.55 - - [15/Mar/2026:08:30:15 +0000] \"POST /api/submit HTTP/1.1\" 201 45"$dc9$, $dc9${"ip": "10.0.0.55", "time": "15/Mar/2026:08:30:15 +0000", "method": "POST", "path": "/api/submit", "status": 201, "bytes": 45}$dc9$, False, '', 'CONTAINS', 2),
    (new_task_id, 'tc03', $dc9$"172.16.0.1 - - [20/Apr/2026:22:10:00 +0800] \"DELETE /users/123 HTTP/1.1\" 204 0"$dc9$, $dc9${"ip": "172.16.0.1", "time": "20/Apr/2026:22:10:00 +0800", "method": "DELETE", "path": "/users/123", "status": 204, "bytes": 0}$dc9$, False, '', 'CONTAINS', 3),
    (new_task_id, 'tc04', $dc9$"invalid log line without proper format"$dc9$, $dc9$null$dc9$, False, '', 'CONTAINS', 4),
    (new_task_id, 'tc05', $dc9$"203.0.113.42 - - [01/Feb/2026:14:20:33 +0800] \"GET /static/app.js HTTP/1.1\" 304 -"$dc9$, $dc9${"ip": "203.0.113.42", "time": "01/Feb/2026:14:20:33 +0800", "method": "GET", "path": "/static/app.js", "status": 304, "bytes": 0}$dc9$, True, '', 'CONTAINS', 5),
    (new_task_id, 'tc01', $dc9$"{\"level\": \"INFO\", \"msg\": \"Server started\"}"$dc9$, $dc9${"level": "INFO", "msg": "Server started"}$dc9$, False, '', 'CONTAINS', 6),
    (new_task_id, 'tc02', $dc9$"{\"level\": \"ERROR\", \"msg\": \"Connection failed\", \"host\": \"db-01\"}"$dc9$, $dc9${"level": "ERROR", "msg": "Connection failed", "host": "db-01"}$dc9$, False, '', 'CONTAINS', 7),
    (new_task_id, 'tc03', $dc9$"  {\"level\": \"DEBUG\", \"count\": 42}  "$dc9$, $dc9${"level": "DEBUG", "count": 42}$dc9$, False, '', 'CONTAINS', 8),
    (new_task_id, 'tc04', $dc9$""$dc9$, $dc9$null$dc9$, False, '', 'CONTAINS', 9),
    (new_task_id, 'tc05', $dc9$"not valid json at all"$dc9$, $dc9$null$dc9$, False, '', 'CONTAINS', 10),
    (new_task_id, 'tc06', $dc9$"[\"INFO\", \"ERROR\", \"INFO\", \"WARNING\", \"INFO\", \"ERROR\", \"ERROR\"]"$dc9$, $dc9${"INFO": 3, "ERROR": 3, "WARNING": 1}$dc9$, False, '', 'CONTAINS', 11),
    (new_task_id, 'tc07', $dc9$"{\"level\": \"INFO\"}\n{\"level\": \"WARNING\"}\n{\"level\": \"ERROR\"}"$dc9$, $dc9${"INFO": 1, "WARNING": 1, "ERROR": 1}$dc9$, True, '', 'CONTAINS', 12);
END $$;