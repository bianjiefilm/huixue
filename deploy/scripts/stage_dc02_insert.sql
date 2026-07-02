-- ============================================================
-- Stage 2: HTTP协议与请求基础
-- practice_id=4, order_in_practice=2
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    4,
    $v$HTTP协议与请求基础$v$,
    'PRACTICE',
    2,
    $v$easy$v$,
    $v$# HTTP协议与请求基础

## 一、HTTP协议概述

HTTP（HyperText Transfer Protocol，超文本传输协议）是互联网上应用最为广泛的应用层协议之一。它基于客户端-服务器模型，由Tim Berners-Lee于1989年在CERN提出。HTTP协议经历了多个版本的演进，从HTTP/0.9（仅支持GET方法和HTML传输）到HTTP/1.0（引入了请求方法、响应头、媒体类型），再到HTTP/1.1（引入了持久连接、管道化、chunked传输编码），直到现代的HTTP/2（多路复用、头部压缩、服务器推送）和HTTP/3（基于QUIC/UDP）。

HTTP是一种无状态协议（stateless protocol），这意味着服务器不保存客户端的请求历史信息。每次请求都是独立的，服务器不记忆上一个请求的状态。这种设计简化了服务器的实现，使得HTTP可以轻松扩展，但也催生了Cookie和Session机制来解决状态管理问题。

HTTP协议默认使用TCP的80端口（HTTPS使用443端口）。在建立连接时，客户端首先与服务器完成TCP三次握手，然后发送HTTP请求。HTTP/1.1默认启用Keep-Alive机制，可以在同一个TCP连接上发送多个请求，减少了连接建立的开销。

## 二、HTTP请求结构

一个完整的HTTP请求由三部分组成：请求行（Request Line）、请求头（Headers）、请求体（Body）。

请求行的格式为：`METHOD /path HTTP/1.1`，例如 `GET /index.html HTTP/1.1`。请求方法（Method）定义了客户端希望对资源执行的操作，常见的方法包括GET（获取资源）、POST（提交数据）、PUT（更新资源）、DELETE（删除资源）、PATCH（部分更新）、HEAD（获取响应头）、OPTIONS（查询支持的请求方法）。

请求头以键值对的形式提供了关于请求的元信息。常见的请求头包括：Host（目标主机名）、User-Agent（客户端信息）、Accept（可接受的媒体类型）、Accept-Encoding（可接受的编码方式）、Accept-Language（可接受的语言）、Content-Type（请求体的媒体类型）、Content-Length（请求体的长度）、Authorization（认证信息）、Cookie（会话Cookie）、Referer（请求来源页面）、Connection（连接管理选项）。

请求体用于承载需要发送给服务器的数据。GET和HEAD请求通常不包含请求体，而POST、PUT、PATCH请求通常在请求体中包含表单数据、JSON数据或文件内容。请求体的格式由Content-Type头指定，常见的有application/x-www-form-urlencoded（表单编码）、multipart/form-data（多部分表单，含文件上传）、application/json（JSON数据）、text/plain（纯文本）等。

## 三、HTTP响应结构

HTTP响应同样由三部分组成：状态行（Status Line）、响应头（Headers）、响应体（Body）。

状态行的格式为：`HTTP/1.1 StatusCode ReasonPhrase`，例如 `HTTP/1.1 200 OK`。状态码是一个三位数字，表示请求的处理结果。状态码的第一个数字定义了响应的类别：1xx（信息性响应，如100 Continue）、2xx（成功响应，如200 OK、201 Created、204 No Content）、3xx（重定向响应，如301 Moved Permanently、302 Found、304 Not Modified）、4xx（客户端错误，如400 Bad Request、401 Unauthorized、403 Forbidden、404 Not Found、405 Method Not Allowed、429 Too Many Requests）、5xx（服务器错误，如500 Internal Server Error、502 Bad Gateway、503 Service Unavailable、504 Gateway Timeout）。

响应头提供了关于响应的元信息。常见的响应头包括：Content-Type（响应体的媒体类型）、Content-Length（响应体的长度）、Content-Encoding（响应体的编码方式）、Cache-Control（缓存控制指令）、Set-Cookie（设置Cookie）、Server（服务器信息）、Date（响应时间）、Last-Modified（资源最后修改时间）、ETag（资源标识符）、Location（重定向目标）、Access-Control-Allow-Origin（跨域资源共享）等。

响应体包含服务器返回的实际数据，可以是HTML文档、JSON数据、图片、视频、PDF等任何类型的内容。Content-Type头决定了如何解析响应体。

## 四、Python requests库详解

Python的requests库是进行HTTP通信最流行的第三方库，由Kenneth Reitz开发，提供了优雅且人性化的API。相比于标准库的urllib，requests大幅简化了HTTP请求的编写。

安装方式：`pip install requests`。基本用法非常直观：使用requests.get()发送GET请求，requests.post()发送POST请求，以此类推。所有方法都返回一个Response对象。

Response对象包含服务器响应的所有信息：status_code（HTTP状态码）、headers（响应头字典）、text（响应体的文本形式，自动根据编码进行解码）、content（响应体的字节形式）、json()（将JSON响应解析为Python字典）、encoding（文本编码）、cookies（响应的Cookie字典）、url（请求的最终URL，可能经过重定向）、history（重定向历史列表）。

发送带参数的请求有两种方式：URL查询字符串（如 `requests.get('http://httpbin.org/get', params={'key': 'value'})`）和请求体数据（POST请求使用data或json参数）。使用params参数时，requests会自动对参数进行URL编码；使用json参数时，requests会自动设置Content-Type为application/json。

处理请求头和Cookie：使用headers参数设置自定义请求头，使用cookies参数发送特定的Cookie。Session对象可以在多个请求之间保持Cookie和配置，适用于需要维护会话状态的应用场景，如登录后的操作。

处理超时：使用timeout参数设置超时时间（单位为秒）。可以设置单个值（连接超时和读取超时相同）或元组（connect, read）。例如 `requests.get(url, timeout=(3.05, 27))` 表示连接超时3.05秒、读取超时27秒。

处理异常：requests可能抛出多种异常，包括ConnectionError（网络连接问题）、HTTPError（HTTP错误状态码，4xx或5xx）、Timeout（请求超时）、TooManyRedirects（重定向次数过多）。建议使用try-except块包装请求，并使用response.raise_for_status()在非2xx状态码时抛出异常。

## 五、实战技巧与最佳实践

处理HTTPS请求时，requests默认验证SSL证书。在生产环境中，应保持证书验证开启。对于使用自签名证书的测试服务器，可以设置verify=False绕过验证，但这应在明确了解安全风险的情况下使用。更安全的做法是指定CA证书文件：verify='/path/to/ca-bundle.crt'。

重试机制可以通过urllib3的Retry配置实现。创建Session后，设置其mount适配器以自动重试失败的请求。这在网络不稳定或服务器繁忙时特别有用。

文件上传使用files参数，可以上传单个文件（`files={'file': open('data.csv', 'rb')}`）或带文件名和内容类型的多部分上传。对于大文件，应使用流式上传（将文件对象作为值传递）以避免一次性将整个文件读入内存。

流式响应通过设置stream=True实现，可以分块读取大型响应体，避免内存溢出。使用response.iter_content()或response.iter_lines()进行流式处理。

代理设置使用proxies参数，支持HTTP和HTTPS代理：`proxies={'http': 'http://proxy:8080', 'https': 'http://proxy:8080'}`。认证代理使用URL格式 `http://user:password@proxy:8080`。

使用Session对象可以获得更好的性能，因为底层TCP连接会被复用，减少了连接建立的开销。Session还能自动管理Cookie，使得连续请求之间保持状态变得更加简单。在需要发送多个请求到同一主机时，始终使用Session是最佳实践。

监控请求进度可以使用第三方库如tqdm，或者使用requests_toolbelt的MultipartMonitor来跟踪文件上传进度。
$v$,
    $v${"questions": [{"id": "dc2_q01", "type": "multiple_choice", "difficulty": "easy", "topic": "HTTP基础", "question": "以下哪个HTTP方法通常用于从服务器获取资源？", "options": ["A. POST", "B. GET", "C. DELETE", "D. PATCH"], "answer": "B", "explanation": "GET方法用于请求服务器发送指定的资源，是HTTP中最常用的读取操作方法。", "tags": ["HTTP方法", "基础"]}, {"id": "dc2_q02", "type": "multiple_choice", "difficulty": "easy", "topic": "HTTP响应码", "question": "HTTP状态码404表示什么含义？", "options": ["A. 服务器内部错误", "B. 找不到请求的资源", "C. 请求超时", "D. 服务器暂时不可用"], "answer": "B", "explanation": "404 Not Found表示服务器无法找到客户端请求的资源，该资源可能已被删除或URL地址错误。", "tags": ["状态码", "HTTP基础"]}, {"id": "dc2_q03", "type": "multiple_choice", "difficulty": "easy", "topic": "请求头", "question": "在HTTP请求中，哪个头字段用于告诉服务器客户端可以接受哪些类型的响应内容？", "options": ["A. Content-Type", "B. Accept", "C. User-Agent", "D. Host"], "answer": "B", "explanation": "Accept请求头用于告诉服务器客户端能够接受哪些媒体类型（ MIME types），服务器应尽量返回Accept中列出的类型。", "tags": ["HTTP头", "请求头"]}, {"id": "dc2_q04", "type": "multiple_choice", "difficulty": "easy", "topic": "HTTP特性", "question": "HTTP协议默认使用的端口号是？", "options": ["A. 21", "B. 443", "C. 80", "D. 22"], "answer": "C", "explanation": "HTTP协议默认使用TCP的80端口，而HTTPS（HTTP over TLS/SSL）默认使用443端口。", "tags": ["HTTP基础", "端口"]}, {"id": "dc2_q05", "type": "multiple_choice", "difficulty": "easy", "topic": "Content-Type", "question": "当使用Python requests库发送JSON格式数据时，应该使用哪个Content-Type值？", "options": ["A. application/x-www-form-urlencoded", "B. multipart/form-data", "C. application/json", "D. text/plain"], "answer": "C", "explanation": "application/json表示请求体中的数据是JSON格式。当使用requests.post(url, json=data)时，库会自动设置此Content-Type。", "tags": ["Content-Type", "JSON"]}, {"id": "dc2_q06", "type": "multiple_choice", "difficulty": "medium", "topic": "HTTP状态码", "question": "以下哪组状态码全部表示“成功”响应（2xx范围）？", "options": ["A. 200, 201, 301", "B. 200, 201, 204", "C. 201, 302, 200", "D. 204, 404, 200"], "answer": "B", "explanation": "200 OK（成功获取资源）、201 Created（成功创建资源）、204 No Content（成功但无返回内容）都属于2xx成功响应。301是重定向，不属于2xx。", "tags": ["状态码", "分类"]}, {"id": "dc2_q07", "type": "multiple_choice", "difficulty": "medium", "topic": "HTTP请求结构", "question": "一个完整的HTTP请求必须包含哪三个部分？", "options": ["A. 请求行、状态行、响应体", "B. 请求行、请求头、请求体", "C. 请求行、响应头、响应体", "D. 请求头、状态行、请求体"], "answer": "B", "explanation": "HTTP请求由请求行（包含方法、路径、协议版本）、请求头（键值对元信息）、请求体（可选，数据内容）三部分组成。", "tags": ["HTTP结构", "请求"]}, {"id": "dc2_q08", "type": "multiple_choice", "difficulty": "medium", "topic": "requests库", "question": "使用requests.Session与直接调用requests.get()相比，主要优势是什么？", "options": ["A. Session无法设置请求头", "B. Session可以复用TCP连接，提升性能", "C. Session不支持Cookie", "D. Session只能发送GET请求"], "answer": "B", "explanation": "Session对象会复用底层TCP连接（HTTP Keep-Alive），减少连接建立的开销。同时Session还能自动管理Cookie，适合需要维护会话状态的场景（如登录后的连续请求）。", "tags": ["requests", "Session"]}, {"id": "dc2_q09", "type": "coding", "difficulty": "hard", "topic": "requests库编程", "question": "编写一个Python函数，使用requests库获取指定URL的HTTP状态码和响应头中的Content-Type。如果请求失败（超时或网络错误），返回None。", "analysis": "需要使用try-except捕获ConnectionError和Timeout，返回状态码和Content-Type。", "tags": ["requests", "异常处理"]}, {"id": "dc2_q10", "type": "coding", "difficulty": "hard", "topic": "数据采集", "question": "编写一个函数，接收一个URL列表，遍历所有URL，使用requests发送GET请求，将每个URL的HTTP状态码和响应Content-Length头保存到字典中返回。请求需要设置5秒超时，并设置User-Agent为'MyBot/1.0'。", "analysis": "需要遍历URL列表，使用requests.Session保持连接，设置timeout和headers，返回{url: {'status_code': ..., 'content_length': ...}}格式的字典。", "tags": ["requests", "批量请求", "Session"]}], "baseline_code": "\"\"\"\nDC Stage 2: HTTP协议与请求基础 - 基准代码\n学生需要补全以下函数实现。\n\"\"\"\nimport requests\n\n\ndef fetch_url_status(url: str) -> tuple[int, str] | None:\n    \"\"\"\n    获取URL的HTTP状态码和Content-Type。\n    如果请求失败（超时或网络错误），返回None。\n\n    Args:\n        url: 目标URL\n\n    Returns:\n        (status_code, content_type) 或 None\n    \"\"\"\n    # TODO: 实现此函数\n    pass\n\n\ndef batch_fetch_status(urls: list[str]) -> dict:\n    \"\"\"\n    批量获取URL的状态码和Content-Length。\n    使用Session复用连接，设置5秒超时，User-Agent为'MyBot/1.0'。\n\n    Args:\n        urls: URL列表\n\n    Returns:\n        {url: {'status_code': int, 'content_length': int}} 的字典\n    \"\"\"\n    # TODO: 实现此函数\n    pass\n"}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 2;
    RAISE NOTICE 'Inserted task_id: %', new_task_id;

    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
        (new_task_id, 'case_1', $v$http://httpbin.org/status/200$v$, $v$200$v$, false, $v$http://httpbin.org/status/200$v$, 'EXACT_MATCH', 1),
        (new_task_id, 'case_2', $v$http://httpbin.org/get$v$, $v$200$v$, false, $v$http://httpbin.org/get$v$, 'EXACT_MATCH', 2),
        (new_task_id, 'case_3', $v$http://httpbin.org/status/404$v$, $v$404$v$, true, $v$http://httpbin.org/status/404$v$, 'EXACT_MATCH', 3),
        (new_task_id, 'case_4', $v$http://httpbin.org/html$v$, $v$200$v$, true, $v$http://httpbin.org/html$v$, 'EXACT_MATCH', 4),
        (new_task_id, 'case_5', $v$http://httpbin.org/json$v$, $v$200$v$, true, $v$http://httpbin.org/json$v$, 'EXACT_MATCH', 5),
        (new_task_id, 'case_6', $v$http://httpbin.org/status/500$v$, $v$500$v$, true, $v$http://httpbin.org/status/500$v$, 'EXACT_MATCH', 6);

    RAISE NOTICE 'Inserted 6 test cases for task_id: %', new_task_id;
END $$;

COMMIT;
