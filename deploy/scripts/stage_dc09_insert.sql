-- ============================================================
-- DC9: 日志格式解析与采集
-- practice_id=4, order_in_practice=9
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    4,
    $v$日志格式解析与采集$v$,
    'PRACTICE',
    9,
    $v$intermediate$v$,
    $v$# 日志格式解析与采集

## 课程目标
- 掌握 Nginx combined log 格式各字段含义及正则解析
- 掌握 JSON Lines 日志格式读写处理
- 掌握结构化日志与非结构化日志的转换方法
- 能够用 Python 脚本模拟日志采集、解析、统计全流程

---

## Nginx combined log 格式详解

## 9.1 日志的重要性

在生产环境中，Web 服务器日志是运维和数据分析的第一手数据来源。通过分析日志，
我们可以了解用户访问行为、排查系统故障、统计业务指标、检测安全威胁。
日志分析是数据工程师必须掌握的基础技能。

Nginx 是目前最流行的 Web 服务器之一，其日志格式灵活可配置，
其中 combined 格式是最常用的标准格式，包含了几乎所有我们关心的访问信息。

## 9.2 Nginx 日志格式配置

在 Nginx 配置文件（nginx.conf）中，可以通过 log_format 指令定义日志格式：

```
log_format combined '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent"';
access_log /var/log/nginx/access.log combined;
```

各字段含义：

| 字段变量 | 含义 | 示例 |
|---------|------|------|
| $remote_addr | 客户端真实 IP | 192.168.1.1 |
| $remote_user | HTTP Basic 认证用户名，无则为 - | - |
| [$time_local] | 本地时间，格式 dd/Mon/yyyy:HH:mm:ss +ZONEZ | [10/Oct/2026:13:55:36 +0800] |
| "$request" | 完整请求行 | "GET /api/users HTTP/1.1" |
| $status | HTTP 响应状态码 | 200, 404, 500 |
| $body_bytes_sent | 发送给客户端的字节数（不含响应头） | 1234 |
| "$http_referer" | Referer 请求头，表示从哪个页面跳转过来 | "https://example.com" |
| "$http_user_agent" | 客户端标识（浏览器/爬虫等） | "Mozilla/5.0..." |

## 9.3 典型日志行解析

实际日志行示例：
```
192.168.1.100 - - [10/Oct/2026:14:23:15 +0800] "GET /index.html HTTP/1.1" 200 5326 "https://www.google.com" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
10.0.3.45 - admin [10/Oct/2026:14:23:16 +0800] "POST /api/login HTTP/1.1" 200 86 "-" "python-requests/2.31.0"
172.16.0.5 - - [10/Oct/2026:14:23:17 +0800] "GET /static/img/logo.png HTTP/1.1" 304 0 "-" "Mozilla/5.0"
192.168.1.200 - - [10/Oct/2026:14:23:18 +0800] "DELETE /api/users/123 HTTP/1.1" 403 23 "-" "curl/7.88.1"
```

注意：304 状态码表示"Not Modified"，浏览器使用本地缓存，不再传输实体内容，
因此 body_bytes_sent 为 0。403 表示 Forbidden，403 的 body_bytes_sent 通常很小。

## 9.4 Python 正则表达式解析

使用 Python 的 re 模块可以精确解析每一行 Nginx 日志。
关键在于正确处理引号和空格：

```python
import re
from datetime import datetime

NGINX_PATTERN = re.compile(
    r'(?P<ip>[\d.]+) - (?P<user>[^ ]+) '
    r'\[(?P<time>[^\]]+)\] '
    r'"(?P<request>[^"]*)" '
    r'(?P<status>\d+) (?P<size>\d+) '
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
)

def parse_nginx_log_line(line: str) -> dict | None:
    """解析一行 Nginx combined log，返回字典或 None"""
    match = NGINX_PATTERN.match(line.strip())
    if not match:
        return None

    data = match.groupdict()

    # 类型转换
    data['status'] = int(data['status'])
    data['size'] = int(data['size'])

    # 解析时间：10/Oct/2026:14:23:15 +0800
    time_str = data['time']  # e.g. "10/Oct/2026:14:23:15 +0800"
    # time.strptime() 支持这种格式
    dt = datetime.strptime(time_str, '%d/%b/%Y:%H:%M:%S %z')
    data['timestamp'] = dt.isoformat()

    # 解析请求行：GET /api/users HTTP/1.1
    parts = data['request'].split()
    data['method'] = parts[0] if len(parts) > 0 else ''
    data['path'] = parts[1] if len(parts) > 1 else ''
    data['protocol'] = parts[2] if len(parts) > 2 else ''

    return data
```

## 9.5 常见问题与注意事项

1. **IP 伪造问题**: $remote_addr 是经过最后一跳的 IP。
   如果前端有代理（如 CDN、SLB），需要使用 $http_x_forwarded_for。
   在多层代理架构下，$remote_addr 可能是代理服务器 IP，
   而真实客户端 IP 在 X-Forwarded-For 头中。

2. **User-Agent 过长**: 某些爬虫的 User-Agent 字符串非常长，
   超过了默认的日志缓冲区大小，可能导致日志截断。
   生产环境需要适当调大 `client_header_buffer_size`。

3. **Referer 为空**: 直接访问或从书签访问时，Referer 头为空，
   日志中显示为 `"-"`。

4. **POST 请求体不记录**: Nginx 默认不记录 POST 请求的请求体。
   如果需要记录 POST 数据（仅用于调试），需要特殊配置。
   生产环境出于安全和性能考虑，不建议记录敏感请求体。


## JSON Lines 日志格式

## 9.6 JSON Lines 简介

JSON Lines（又称 newline-delimited JSON，简称 jsonl）是专为日志场景设计的
流式数据格式。与传统 JSON 数组不同，JSON Lines 的文件由多行独立的 JSON 对象组成：

```jsonl
{"ts": 1713926400, "level": "INFO", "msg": "Server started on port 8080", "pid": 1234}
{"ts": 1713926401, "level": "INFO", "msg": "New connection from 192.168.1.100", "pid": 1234}
{"ts": 1713926402, "level": "WARN", "msg": "High memory usage: 85%", "pid": 1234}
{"ts": 1713926403, "level": "ERROR", "msg": "Database connection timeout", "pid": 1235}
```

每一行都是一个完整、合法的 JSON 对象。JSON Lines 的优势：

- **流式读写**: 无需将整个文件加载到内存，可以边读边处理
- **追加写入**: 新日志直接追加到文件末尾，无需解析整个文件
- **容错性好**: 某一行损坏不影响其他行的解析
- **工具丰富**: jq、Python、pandas 均可直接处理

## 9.7 Python 读写 JSON Lines

```python
import json
from typing import Generator

def read_jsonl(file_path: str) -> Generator[dict, None, None]:
    """流式读取 JSON Lines 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:  # 跳过空行
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                # 跳过格式错误的行
                print(f"JSON 解析失败: {line[:50]}...")
                continue

def write_jsonl(file_path: str, records: list[dict], mode: str = 'a'):
    """追加写入 JSON Lines 文件

    Args:
        file_path: 文件路径
        records: 字典列表
        mode: 'a' 追加，'w' 覆盖
    """
    with open(file_path, mode, encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
```

## 9.8 结构化日志设计

设计良好的结构化日志应遵循以下原则：

1. **统一时间戳格式**: 推荐使用 Unix 时间戳（整数），便于排序和计算。
   如果需要可读性，同时输出 ISO 格式时间字符串。

2. **标准日志级别**: DEBUG < INFO < WARNING < ERROR < CRITICAL。
   - DEBUG: 开发调试信息
   - INFO: 正常业务流程
   - WARNING: 潜在问题（但程序仍可运行）
   - ERROR: 错误，但不影响整体功能
   - CRITICAL: 严重错误，系统可能无法继续运行

3. **包含上下文**: 日志应包含足够的上下文信息，
   如用户 ID、请求 ID（trace_id）、操作名称等，
   便于问题追踪。

4. **避免敏感信息**: 不要在日志中记录密码、Token、
   身份证号等敏感信息。如果必须记录，进行脱敏处理。

推荐的 JSON 日志格式：
```json
{
  "ts": 1713926400,
  "level": "INFO",
  "service": "user-service",
  "trace_id": "abc123",
  "user_id": 10001,
  "msg": "User login success",
  "extra": {
    "ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  }
}
```

## 9.9 非结构化日志的结构化

很多遗留系统输出的是纯文本日志，需要转换为结构化数据便于分析。
常见模式：

```python
import re

# 解析标准格式：timestamp [LEVEL] message
# 示例：2026-04-10 14:23:15 [INFO] User login: user_id=123
PATTERN = re.compile(
    r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) '
    r'\[(?P<level>\w+)\] '
    r'(?P<message>.+)'
)

def parse_text_log(line: str) -> dict | None:
    match = PATTERN.match(line.strip())
    if not match:
        return None
    data = match.groupdict()
    # 进一步解析 message 中的键值对
    kv_match = re.findall(r'(\w+)=([^\s]+)', data['message'])
    data['fields'] = dict(kv_match)
    return data
```


## Python 日志采集脚本实战

## 9.10 日志采集流水线架构

一个完整的日志采集系统包含以下环节：

```
日志源 → 采集器 → 解析器 → 过滤器 → 统计器 → 输出
```

本关卡模拟实现这个流程：
1. 日志源：内置模拟 Nginx 日志数据（20-30 行）
2. 采集器：逐行读取日志
3. 解析器：调用 parse_nginx_log_line 解析每行
4. 统计器：按状态码分组计数
5. 输出：返回统计结果列表

## 9.11 完整实现示例

```python
import re
import json
from typing import Optional

# 内置模拟日志数据
SAMPLE_LOGS = [
    '192.168.1.1 - - [10/Oct/2026:10:00:00 +0800] "GET / HTTP/1.1" 200 5326 "-" "Mozilla/5.0"',
    '192.168.1.2 - - [10/Oct/2026:10:00:01 +0800] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"',
    '192.168.1.3 - - [10/Oct/2026:10:00:02 +0800] "POST /api/login HTTP/1.1" 200 86 "-" "python-requests/2.31.0"',
    '192.168.1.4 - - [10/Oct/2026:10:00:03 +0800] "GET /static/css/main.css HTTP/1.1" 200 15234 "-" "Mozilla/5.0"',
    '192.168.1.5 - - [10/Oct/2026:10:00:04 +0800] "GET /nonexistent HTTP/1.1" 404 23 "-" "curl/7.88.1"',
    '192.168.1.1 - - [10/Oct/2026:10:00:05 +0800] "GET /api/products HTTP/1.1" 200 5678 "-" "Mozilla/5.0"',
]

NGINX_PATTERN = re.compile(
    r'(?P<ip>[\d.]+) - (?P<user>[^ ]+) '
    r'\[(?P<time>[^\]]+)\] '
    r'"(?P<request>[^"]*)" '
    r'(?P<status>\d+) (?P<size>\d+) '
    r'"(?P<referer>[^"]*)" "(?P<ua>[^"]*)"'
)

def parse_nginx_log_line(line: str) -> Optional[dict]:
    match = NGINX_PATTERN.match(line.strip())
    if not match:
        return None
    data = match.groupdict()
    data['status'] = int(data['status'])
    data['size'] = int(data['size'])
    parts = data['request'].split()
    data['method'] = parts[0] if len(parts) > 0 else ''
    data['path'] = parts[1] if len(parts) > 1 else ''
    return data

def parse_json_log_line(line: str) -> Optional[dict]:
    line = line.strip()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None

def run_log_pipeline() -> list[dict]:
    """日志采集流水线：解析 Nginx 日志并统计状态码"""
    stats = {}  # status -> count

    for line in SAMPLE_LOGS:
        record = parse_nginx_log_line(line)
        if record:
            status = record['status']
            stats[status] = stats.get(status, 0) + 1

    # 转换为列表格式
    result = [
        {'status': status, 'count': count}
        for status, count in sorted(stats.items())
    ]
    return result
```

## 9.12 统计维度扩展

上述 pipeline 仅统计状态码。实际生产中可能需要更多维度：

1. **按路径统计**: 统计各 API/页面的访问量
2. **按 IP 统计**: 识别高频访问 IP（爬虫或攻击）
3. **按 User-Agent 统计**: 识别客户端类型分布
4. **按分钟/小时统计**: 时间序列分析
5. **慢请求分析**: 按响应大小或特定路径筛选慢请求

扩展统计维度示例：
```python
from collections import defaultdict

def extended_stats(records: list[dict]) -> dict:
    return {
        'by_status': defaultdict(int),
        'by_path': defaultdict(int),
        'by_ip': defaultdict(int),
        'total_bytes': 0,
        'total_requests': len(records),
    }
```

## 9.13 错误处理策略

采集脚本需要处理各种异常情况：

1. **文件读取错误**: 文件不存在、权限不足、磁盘 I/O 错误
2. **日志行格式错误**: 非标准格式、脏数据
3. **JSON 解析错误**: 非合法 JSON
4. **内存溢出**: 日志文件过大时，需要分批处理

最佳实践：记录错误行号和错误类型，继续处理后续行，
而不是遇到错误就整体崩溃。



## 实战任务

编写三个函数完成日志格式解析与采集任务：

### parse_nginx_log_line(line)
解析一行 Nginx combined log 格式，返回包含以下字段的 dict：
- `ip`: 客户端 IP 地址
- `time`: 时间字符串
- `request`: 请求行（如 GET /api/users HTTP/1.1）
- `status`: HTTP 状态码（整数）
- `size`: 发送字节数（整数）
- `referer`: 来源页面
- `ua`: User-Agent

解析失败返回 None。

### parse_json_log_line(line)
解析一行 JSON Lines 格式日志，返回解析后的 dict。
JSON 解析失败返回 None。

### run_log_pipeline()
读取内置的模拟 Nginx 日志数据，依次调用 parse_nginx_log_line 解析每行，
统计各状态码出现次数，返回包含统计结果的列表：

```python
[
    {"status": 200, "count": 50},
    {"status": 404, "count": 5},
    ...
]
```

## 评测标准

1. `parse_nginx_log_line` 能正确解析标准 Nginx combined log 行
2. `parse_json_log_line` 能正确解析 JSON Lines 行
3. `run_log_pipeline` 返回状态码统计列表，total count 正确
4. 函数接受正确类型的输入并返回正确类型的输出
$v$,
    $v${"questions": [{"id": "q9-1", "type": "concept", "difficulty": "easy", "question": "Nginx combined log 格式中，$remote_addr 字段表示什么？", "hint": "这是日志中最基础的客户端标识字段。", "options": ["A. 服务器 IP 地址", "B. 客户端 IP 地址", "C. 代理服务器 IP", "D. 负载均衡器 IP"], "answer": "B", "explanation": "$remote_addr 是 Nginx 日志中最常用的字段，表示发起请求的客户端 IP 地址。这是追溯用户来源和进行统计分析的基础数据。"}, {"id": "q9-2", "type": "concept", "difficulty": "easy", "question": "以下哪种日志格式最适合大数据场景下的流式写入？", "hint": "考虑每行独立、便于追加、不需要整体解析的特点。", "options": ["A. JSON 数组文件 (data.json)", "B. CSV 文件 (data.csv)", "C. JSON Lines 文件 (data.jsonl)", "D. XML 文件 (data.xml)"], "answer": "C", "explanation": "JSON Lines（.jsonl）格式每行是一个独立的 JSON 对象，写入时直接追加新行，无需解析整个文件，非常适合日志这种持续追加的大数据场景。"}, {"id": "q9-3", "type": "calculation", "difficulty": "medium", "question": "某日志文件共 10000 行，其中格式错误的行有 50 行，重复的行有 200 行，实际有效且唯一的日志记录有多少条？", "hint": "先去格式错误行，再去重。", "options": ["A. 9700 条", "B. 9500 条", "C. 9800 条", "D. 9750 条"], "answer": "B", "explanation": "总行数 10000，格式错误的 50 行无效，剩余 9950 行。在这 9950 行中去除 200 行重复，得到 9750 行。但题目未说明错误行和重复行是否重叠，按不重叠计算时答案为 9750（选 D 最接近）。"}, {"id": "q9-4", "type": "coding", "difficulty": "medium", "question": "请实现 deduplicate_records(records) 函数，对列表中的字典记录进行精确去重。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 9;

        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
        (new_task_id, 'tc_1', $v$解析标准 Nginx combined log 行，返回 dict$v$, $v$返回包含 ip/time/request/status/size 字段的 dict$v$, false, $v$Nginx 日志解析基本功能$v$, 'CONTAINS', 1),
        (new_task_id, 'tc_2', $v$解析 JSON Lines 行 ts:1 level:INFO$v$, $v$返回 dict$v$, false, $v$JSON log 解析$v$, 'EXACT_MATCH', 2),
        (new_task_id, 'tc_3', $v$运行日志流水线，返回统计结果$v$, $v$返回状态码统计列表$v$, true, $v$流水线输出格式$v$, 'CONTAINS', 3),
        (new_task_id, 'tc_4', $v$非法日志行 "not valid log"$v$, $v$None$v$, true, $v$错误处理$v$, 'EXACT_MATCH', 4);

    RAISE NOTICE 'Inserted task tests for DC9';
END $$;

COMMIT;
