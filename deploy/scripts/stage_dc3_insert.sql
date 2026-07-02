-- DC3: HTML 解析与 BeautifulSoup
DO $$
DECLARE new_task_id INTEGER;
BEGIN
  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 3;
  IF new_task_id IS NOT NULL THEN
    DELETE FROM task_tests WHERE task_id = new_task_id;
    DELETE FROM tasks WHERE id = new_task_id;
  END IF;

  INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
  VALUES (
    4,
    'HTML 解析与 BeautifulSoup',
    'PRACTICE',
    3,
    'intermediate',
    $dc3$# Stage 3: HTML 解析与 BeautifulSoup

---

## 一、任务类型

本阶段的核心任务是**从网页或 HTML 字符串中精确提取所需信息**。具体包括：

- 解析 HTML 文档结构，理解标签、属性、嵌套关系
- 使用 BeautifulSoup 的 `find()` / `find_all()` / `select()` 方法定位目标元素
- 提取文本内容（`.text` / `.get_text()`）和属性值（如 `href`、`src`）
- 处理不同编码的 HTML 页面，避免乱码
- 处理脏 HTML（未闭合标签、错误嵌套等）并保证鲁棒解析

常见的提取目标包括：文章正文、表格数据、图片链接、视频链接、价格信息、评分等结构化或半结构化数据。

---

## 二、学习环境

### 2.1 安装 BeautifulSoup

```bash
pip install beautifulsoup4 lxml html5lib
```

### 2.2 基础用法

```python
from bs4 import BeautifulSoup

html = """
<!DOCTYPE html>
<html>
<head><title>示例页面</title></head>
<body>
    <div class="container">
        <h1 class="title">学习 BeautifulSoup</h1>
        <a href="https://example.com">访问示例</a>
        <img src="/img/logo.png" alt="logo" />
    </div>
</body>
</html>
"""

# 使用 html.parser（内置，无需额外安装）
soup = BeautifulSoup(html, 'html.parser')
print(soup.title.text)          # 输出: 示例页面
print(soup.a['href'])            # 输出: https://example.com
print(soup.img['src'])           # 输出: /img/logo.png
```

### 2.3 解析器对比

BeautifulSoup 支持多种底层解析器，不同解析器在速度、容错性、功能上有显著差异。以下是同一段 HTML 在三种解析器下的行为对比：

```html
<html>
<body>
    <table>
        <tr><td>1</td><td>2</td></tr>
        <tr><td>3</td><td>4</td></tr>
    </table>
    <div>多余内容</div>
</body>
</html>
```

| 特性 | `html.parser` | `lxml` | `html5lib` |
|------|---------------|--------|------------|
| **安装需求** | 内置，无需安装 | `pip install lxml` | `pip install html5lib` |
| **解析速度** | 快 | 最快 | 慢 |
| **容错性** | 中等（部分错误 HTML 可处理） | 低（严格模式） | 高（浏览器级容错） |
| **HTML5 支持** | 一般 | 一般 | 完全支持 |
| **返回类型** | BeautifulSoup | BeautifulSoup | BeautifulSoup |
| **缺失闭合标签** | 自动补全，但位置可能不准确 | 可能报错 | 自动补全，接近浏览器行为 |
| **嵌套 CDATA** | 视为文本 | 视为文本 | 视为文本 |
| **适用场景** | 简单 HTML、快速原型 | 大规模数据清洗（已知 HTML 质量好） | 真实网页、脏 HTML |

**实践建议**：生产环境中优先使用 `lxml`，处理来源不明的网页时使用 `html5lib`，快速脚本和测试用 `html.parser`。

---

## 三、知识点讲解

### 3.1 HTML 文档结构

HTML 是树形结构，每个标签是一个节点：

```
html (根节点)
├── head
│   ├── title
│   └── meta
└── body
    ├── div (class="container")
    │   ├── h1 (class="title")
    │   ├── p
    │   └── a (href="...")
    └── table
        ├── thead
        │   └── tr → th × n
        └── tbody
            └── tr → td × n
```

- **标签（Tag）**：`<div>`, `<a>`, `<p>` 等
- **属性（Attribute）**：`class`, `id`, `href`, `src` 等，格式为 `key="value"`
- **嵌套关系**：父节点、子节点、兄弟节点
- **文本节点**：标签之间的文字内容，如 `<p>这是文本</p>`

### 3.2 BeautifulSoup 核心方法

#### find() 与 find_all()

```python
soup = BeautifulSoup(html, 'html.parser')

# find() 返回第一个匹配项（单个 Tag 对象或 None）
div = soup.find('div', class_='container')  # class_ 避免与 Python 关键字冲突
p = soup.find('p', id='intro')

# find_all() 返回所有匹配项（列表）
all_links = soup.find_all('a')
all_tds = soup.find_all('td', class_='data')

# 支持多个标签（OR 匹配）
headers = soup.find_all(['h1', 'h2', 'h3'])

# 支持正则表达式
import re
links_with_example = soup.find_all('a', href=re.compile(r'example'))
```

#### select() — CSS 选择器

```python
soup = BeautifulSoup(html, 'html.parser')

# 按标签
links = soup.select('a')

# 按 class（点号）
title = soup.select('.title')        # class="title"

# 按 id（井号）
intro = soup.select('#intro')        # id="intro"

# 按属性
images = soup.select('img[src]')
buttons = soup.select('button[type="submit"]')

# 组合选择器
container_links = soup.select('div.container a')   # 空格表示后代
card_title = soup.select('div.card > h2')            # > 表示直接子元素
active_link = soup.select('a.active')              # 复合选择器
```

#### 方法对比总结

| 方法 | 返回类型 | 选择方式 | 适用场景 |
|------|---------|---------|---------|
| `find(tag, attrs)` | 单个 Tag / None | 标签名 + 属性 | 定位唯一元素 |
| `find_all(tag, attrs, limit)` | 列表 | 标签名 + 属性 | 提取多个元素 |
| `select(css_selector)` | 列表 | CSS 选择器字符串 | 复杂条件、组合选择 |
| `select_one(css_selector)` | 单个 Tag / None | CSS 选择器字符串 | 复杂条件定位单一元素 |

### 3.3 DOM 导航

```python
soup = BeautifulSoup(html, 'html.parser')

# 父节点
parent = soup.find('a').parent

# 子节点（直接子节点）
children = soup.find('div').children      # 返回迭代器

# 所有后代
descendants = soup.find('body').descendants  # 返回迭代器，包含文本节点

# 下一个兄弟节点
next_sibling = soup.find('h2').next_sibling

# 上一个兄弟节点
prev_sibling = soup.find('h2').previous_sibling

# 获取所有兄弟节点
all_siblings = soup.find('tr').find_next_siblings()

# 下一个/上一个元素节点（跳过空白文本节点）
next_element = soup.find('td').next_element
```

### 3.4 提取文本与属性

```python
soup = BeautifulSoup(html, 'html.parser')

# 提取标签内的纯文本
text = soup.find('p').text          # str，去除所有 HTML 标签
text2 = soup.find('p').get_text()   # 等价于 .text
text3 = soup.find('p').get_text(strip=True)  # 去除首尾空白

# 提取所有文本（包括嵌套标签）
all_text = soup.body.get_text(separator='\n', strip=True)

# 提取属性值
href = soup.find('a').get('href')       # 不存在返回 None
href2 = soup.find('a')['href']          # 不存在会抛出异常
src = soup.find('img', src=True).get('src')

# 提取多个属性
attrs = soup.find('a').attrs           # 返回所有属性的字典
```

### 3.5 处理中文编码

```python
import requests
from bs4 import BeautifulSoup

# 情况1：HTTP 响应编码错误
response = requests.get(url)
# 手动指定编码
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')

# 情况2：HTML 中指定了编码
soup = BeautifulSoup(html_bytes, 'html.parser',
                     from_encoding='gb2312')

# 情况3：编码检测
import chardet
detected = chardet.detect(html_bytes)
soup = BeautifulSoup(html_bytes, 'html.parser',
                     from_encoding=detected['encoding'])

# 情况4：BeautifulSoup 自动检测
soup = BeautifulSoup(html_bytes, 'lxml')  # lxml 自动处理编码
```

---

## 四、常见模式与技巧

### 4.1 从复杂页面中提取文章正文

```python
def extract_article_body(html):
    """
    从新闻/博客页面提取正文内容
    """
    soup = BeautifulSoup(html, 'html.parser')

    # 方法1：通过 class/id 定位
    article = soup.find('div', class_='article-content')
    if not article:
        article = soup.find('article')
    if not article:
        # 方法2：找最大的文本块
        candidates = soup.find_all('div')
        if not candidates:
            return ""
        article = max(candidates, key=lambda x: len(x.get_text()))

    # 移除无关标签
    for tag in article.find_all(['script', 'style', 'nav', 'footer', 'aside']):
        tag.decompose()

    return article.get_text(separator='\n', strip=True)
```

### 4.2 表格数据转 CSV

```python
import csv
from bs4 import BeautifulSoup

def table_to_csv(html, output_file):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # 提取表头
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        writer.writerow(headers)

        # 提取数据行
        for row in table.find_all('tr')[1:]:  # 跳过表头行
            cells = row.find_all(['td', 'th'])
            writer.writerow([cell.get_text(strip=True) for cell in cells])

    print(f"已导出 {len(table.find_all('tr')) - 1} 行数据到 {output_file}")
```

### 4.3 图片链接批量提取

```python
def extract_images(html):
    soup = BeautifulSoup(html, 'html.parser')
    images = []

    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-lazy')
        alt = img.get('alt', '')
        if src:
            images.append({'src': src, 'alt': alt})

    return images
```

### 4.4 处理脏 HTML

```python
# 问题1：未闭合标签
# html.parser 和 html5lib 会自动补全
soup = BeautifulSoup('<p>未闭合', 'html.parser')

# 问题2：嵌套错误
soup = BeautifulSoup('<div><p>嵌套<div>错误</p></div></div>', 'html5lib')

# 问题3：移除特定标签（广告、追踪脚本）
def clean_html(html):
    soup = BeautifulSoup(html, 'lxml')
    unwanted = soup.find_all(['script', 'style', 'iframe', 'noscript'])
    for tag in unwanted:
        tag.decompose()
    return str(soup)
```

---

## 五、评测标准

### 5.1 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 正确性 | 60% | 提取结果与预期完全匹配 |
| 鲁棒性 | 20% | 对边界情况（空值、缺失属性）的处理 |
| 代码质量 | 10% | 命名规范、注释、结构清晰 |
| 性能 | 10% | 避免不必要的全量遍历 |

### 5.2 常见错误提示

- `AttributeError: 'NoneType' object has no attribute 'text'` — 未检查 find 返回 None
- `KeyError: 'href'` — 使用 `tag['href']` 访问不存在的属性，应用 `tag.get('href')`
- 编码错误 — 确保响应 encoding 与实际编码一致
- 空列表 — find_all 返回空列表时应返回空列表或默认值，而非报错

### 5.3 测试原则

- 每个函数至少测试：正常输入、空输入、部分缺失属性
- 验证 `.text` 与 `.get_text()` 的行为差异
- 确认不同解析器对同一 HTML 的解析结果一致性
$dc3$,
    $dc3${"baseline_code": "from bs4 import BeautifulSoup\n\ndef extract_all_links(html: str) -> list[dict]:\n    \"\"\"\n    解析 HTML 字符串，提取所有 <a> 标签的链接信息。\n\n    参数:\n        html: HTML 字符串\n\n    返回:\n        包含字典的列表，每个字典包含 'text' 和 'href' 两个键。\n        如果某个 <a> 标签没有 href 属性，'href' 值为 None。\n        如果 <a> 标签没有文本内容，'text' 值为空字符串。\n    \"\"\"\n    pass", "questions": [{"id": 1, "type": "concept", "difficulty": "easy", "question": "BeautifulSoup 的 `find()` 方法和 `find_all()` 方法的主要区别是什么？请说明它们的返回值类型和使用场景。", "answer": "`find()` 返回第一个匹配的元素（Tag 对象），如果没有任何匹配则返回 None；`find_all()` 返回所有匹配元素的列表（可能为空列表）。`find()` 适用于已知目标唯一、需要快速定位的场景；`find_all()` 适用于需要提取多个元素或不确定元素是否存在时的批量提取。"}, {"id": 2, "type": "concept", "difficulty": "easy", "question": "请列出 BeautifulSoup 支持的三种解析器，并说明哪种解析器最适合处理\"来源不明的真实网页\"（即可能包含脏 HTML、错误嵌套的页面）。", "answer": "BeautifulSoup 支持的三种解析器是 `html.parser`（内置）、`lxml`（需要 pip install lxml）和 `html5lib`（需要 pip install html5lib）。对于来源不明的真实网页，`html5lib` 是最合适的选择，因为它采用浏览器级容错策略，能最大程度地处理脏 HTML 和错误嵌套，在缺失闭合标签时自动补全的结果最接近浏览器行为。"}, {"id": 3, "type": "concept", "difficulty": "easy", "question": "假设有一个 BeautifulSoup 的 Tag 对象 `tag`，请说明获取其纯文本内容应该使用哪个属性或方法？两者有何区别？", "answer": "可以使用 `.text` 属性或 `.get_text()` 方法。两者功能等价，都会返回标签内所有文本内容的字符串。`.get_text()` 的优势在于提供额外参数：`separator`（文本片段之间的分隔符，默认空字符串）、`strip`（是否去除首尾空白，默认 False）。而 `.text` 不接受参数，是一个简写属性。"}, {"id": 4, "type": "concept", "difficulty": "easy", "question": "CSS 选择器 `.container .card-title` 和 `.container > .card-title` 的区别是什么？在 BeautifulSoup 的 `select()` 方法中使用时，分别会匹配哪些元素？", "answer": "`.container .card-title`（空格分隔）是后代选择器，匹配 `.container` 内部任意深度（包括子、孙、曾孙等）的 `.card-title` 元素。`.container > .card-title`（> 分隔）是直接子选择器，只匹配 `.container` 直接子节点的 `.card-title` 元素。例如在 `<div class='container'><div class='card'><h2 class='card-title'>` 的结构中，后者不匹配（因为 `.card-title` 不是 `.container` 的直接子节点），前者可以匹配。"}, {"id": 5, "type": "concept", "difficulty": "easy", "question": "在提取 HTML 元素的属性值时，`tag['href']` 和 `tag.get('href')` 有什么区别？哪种写法更安全，为什么？", "answer": "`tag['href']` 在属性不存在时会抛出 `KeyError` 异常；`tag.get('href')` 在属性不存在时返回 `None`，不会抛出异常。此外，`tag.get('href', 'default')` 还支持指定默认值。因此 `tag.get('href')` 更安全，建议在不确定属性是否存在的场景中使用，特别是在遍历多个元素并批量提取属性时。"}, {"id": 6, "type": "calculation", "difficulty": "medium", "question": "给定以下 HTML 字符串，使用 `html.parser` 解析后，`select('div.container a')` 会返回几个元素？分别是哪些元素的文本内容？\n```html\n<div class='container'>\n  <a href='/a'>链接A</a>\n  <div class='inner'>\n    <a href='/b'>链接B</a>\n  </div>\n</div>\n<a href='/c'>链接C</a>\n```", "answer": "会返回 2 个元素。`select('div.container a')` 是后代选择器（空格分隔），查找 `.container` 内部任意深度的所有 `<a>` 标签。第一个是 `<a href='/a'>链接A</a>`（直接子节点），第二个是 `<a href='/b'>链接B</a>`（`.inner` 的后代）。第三个 `<a href='/c'>链接C</a>` 不在 `.container` 内，不会被匹配。"}, {"id": 7, "type": "calculation", "difficulty": "medium", "question": "分析以下代码的输出结果：\n```python\nfrom bs4 import BeautifulSoup\nhtml = '<div><p>第一段</p><p>第二段</p><p>第三段</p></div>'\nsoup = BeautifulSoup(html, 'html.parser')\nprint(len(soup.find_all('p')))\nprint(soup.find_all('p', limit=2)[-1].text)\n```", "answer": "第一行输出为 `3`（因为 HTML 中有 3 个 `<p>` 标签，`find_all` 返回包含 3 个元素的列表）。第二行输出为 `第二段`（`limit=2` 限制最多返回 2 个结果，所以取索引 -1 即倒数第 2 个元素，内容为\"第二段\"）。注意：如果 limit=1，则 `[-1]` 会取到最后一个，即\"第三段\"。"}, {"id": 8, "type": "calculation", "difficulty": "medium", "question": "使用 BeautifulSoup 解析以下 HTML 后，如何用链式方法调用获取\"最后一项\"的文本？请给出完整的代码表达式，并说明每一步的作用。\n```html\n<ul id='list'>\n  <li class='item'>第一项</li>\n  <li class='item'>第二项</li>\n  <li class='item selected'>最后一项</li>\n</ul>\n```", "answer": "可以使用 `soup.select_one('#list .item:last-child').text`，其中 `#list` 通过 id 定位到 `<ul>`，`.item:last-child` 选择作为父元素最后一个子元素的 `.item` 类元素（等价于 `soup.find_all('li', class_='item')[-1]`）。或者用：`soup.select_one('li.selected').text` 直接定位带有 `selected` 类的 `<li>` 元素。更保守的写法是先 find 检查 None：`soup.find('li', class_='selected').get_text(strip=True)`。"}, {"id": 9, "type": "coding", "difficulty": "medium", "question": "请实现 `extract_all_links(html: str) -> list[dict]` 函数，使其能够解析 HTML 字符串并提取所有 `<a>` 标签的链接信息。具体要求：返回一个字典列表，每个字典包含 'text'（链接文本，去除首尾空白）和 'href'（href 属性值，不存在则为 None）两个键。注意处理空字符串输入和不包含任何 `<a>` 标签的 HTML。", "answer": "def extract_all_links(html: str) -> list[dict]:\\n    soup = BeautifulSoup(html, 'html.parser')\\n    results = []\\n    for a_tag in soup.find_all('a'):\\n        text = a_tag.get_text(strip=True)\\n        href = a_tag.get('href')\\n        results.append({'text': text, 'href': href})\\n    return results"}, {"id": 10, "type": "coding", "difficulty": "medium", "question": "请实现 `extract_table_texts(html: str, selector: str = 'table') -> list[list[str]]` 函数，将指定 CSS 选择器匹配的第一个表格的所有单元格文本提取为二维列表（按行，每行为单元格文本列表）。每行文本需要去除首尾空白。如果选择器未匹配到任何表格，返回空列表。请注意处理嵌套表格的边界情况。", "answer": "def extract_table_texts(html: str, selector: str = 'table') -> list[list[str]]:\\n    soup = BeautifulSoup(html, 'html.parser')\\n    table = soup.select_one(selector)\\n    if not table:\\n        return []\\n    rows = []\\n    for tr in table.find_all('tr'):\\n        cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th']) if td\\n                 .parent == tr]\\n        if cells:\\n            rows.append(cells)\\n    return rows"}], "test_cases": [{"id": 1, "visible": true, "input": {"html": "<html><body><a href=\"https://example.com\">Example</a><a href=\"https://test.org\">Test</a></body></html>"}, "expected": "Example -> https://example.com\nTest -> https://test.org", "hidden": false, "description": "标准 HTML，包含两个带 href 的链接"}, {"id": 2, "visible": true, "input": {"html": "<html><body><a>无 href 链接</a><a href=\"https://cn.bing.com\">必应</a><div>不是链接</div></body></html>"}, "expected": "无 href 链接 -> None\n必应 -> https://cn.bing.com", "hidden": false, "description": "包含缺失 href 属性的链接，以及普通 div（非链接）不应被提取"}, {"id": 3, "visible": false, "input": {"html": "<html><body><a href=\"/path?param=中文&key=value\">编码测试</a><a href=\"https://unicode.com\">Unicode</a></body></html>"}, "expected": "编码测试 -> /path?param=中文&key=value\nUnicode -> https://unicode.com", "hidden": true, "description": "URL 包含中文和特殊字符的情况"}, {"id": 4, "visible": false, "input": {"html": "<html><body><a href=\"https://a.com\"><span class=\"icon\">🔗</span>带图标的链接</a></body></html>"}, "expected": "🔗带图标的链接 -> https://a.com", "hidden": true, "description": "链接包含子标签（如 <span>）的情况，文本应包含子标签内的文字"}, {"id": 5, "visible": false, "input": {"html": "<html><body><!-- 注释里的 <a> 链接 --><a href=\"https://visible.com\">可见链接</a><script>document.write('<a href=\"https://invisible.com\">脚本链接</a>')</script></body></html>"}, "expected": "可见链接 -> https://visible.com", "hidden": true, "description": "注释和 script 标签内的 <a> 不应被提取，只有 DOM 树中实际存在的链接才被提取"}, {"id": 6, "visible": false, "input": {"html": "<html><body>\n    <div class=\"nav\">\n        <a href=\"/home\"> 首页 </a>\n        <a href=\"/about\"> 关于 </a>\n        <a href=\"\"> 空 href </a>\n        <a href=\"https://demo.com\">  示例站  </a>\n    </div>\n</body></html>"}, "expected": "首页 -> /home\n关于 -> /about\n空 href -> \n示例站 -> https://demo.com", "hidden": true, "description": "空字符串 href（不是缺失，是显式空值）以及文本首尾含空白字符的情况"}]}$dc3$,
    NOW(),
    NOW()
  );

  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 3;

  INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
  VALUES
    (new_task_id, '1', $dc3${"html": "<html><body><a href=\"https://example.com\">Example</a><a href=\"https://test.org\">Test</a></body></html>"}$dc3$, $dc3$"Example -> https://example.com\nTest -> https://test.org"$dc3$, False, '标准 HTML，包含两个带 href 的链接', 'CONTAINS', 1),
    (new_task_id, '2', $dc3${"html": "<html><body><a>无 href 链接</a><a href=\"https://cn.bing.com\">必应</a><div>不是链接</div></body></html>"}$dc3$, $dc3$"无 href 链接 -> None\n必应 -> https://cn.bing.com"$dc3$, False, '包含缺失 href 属性的链接，以及普通 div（非链接）不应被提取', 'CONTAINS', 2),
    (new_task_id, '3', $dc3${"html": "<html><body><a href=\"/path?param=中文&key=value\">编码测试</a><a href=\"https://unicode.com\">Unicode</a></body></html>"}$dc3$, $dc3$"编码测试 -> /path?param=中文&key=value\nUnicode -> https://unicode.com"$dc3$, True, 'URL 包含中文和特殊字符的情况', 'CONTAINS', 3),
    (new_task_id, '4', $dc3${"html": "<html><body><a href=\"https://a.com\"><span class=\"icon\">🔗</span>带图标的链接</a></body></html>"}$dc3$, $dc3$"🔗带图标的链接 -> https://a.com"$dc3$, True, '链接包含子标签（如 <span>）的情况，文本应包含子标签内的文字', 'CONTAINS', 4),
    (new_task_id, '5', $dc3${"html": "<html><body><!-- 注释里的 <a> 链接 --><a href=\"https://visible.com\">可见链接</a><script>document.write('<a href=\"https://invisible.com\">脚本链接</a>')</script></body></html>"}$dc3$, $dc3$"可见链接 -> https://visible.com"$dc3$, True, '注释和 script 标签内的 <a> 不应被提取，只有 DOM 树中实际存在的链接才被提取', 'CONTAINS', 5),
    (new_task_id, '6', $dc3${"html": "<html><body>\n    <div class=\"nav\">\n        <a href=\"/home\"> 首页 </a>\n        <a href=\"/about\"> 关于 </a>\n        <a href=\"\"> 空 href </a>\n        <a href=\"https://demo.com\">  示例站  </a>\n    </div>\n</body></html>"}$dc3$, $dc3$"首页 -> /home\n关于 -> /about\n空 href -> \n示例站 -> https://demo.com"$dc3$, True, '空字符串 href（不是缺失，是显式空值）以及文本首尾含空白字符的情况', 'CONTAINS', 6),
    (new_task_id, '1', $dc3${"html": "<html><body><a href=\"https://example.com\">Example</a><a href=\"https://test.org\">Test</a></body></html>"}$dc3$, $dc3$"Example -> https://example.com\nTest -> https://test.org"$dc3$, False, '标准 HTML，包含两个带 href 的链接', 'CONTAINS', 7),
    (new_task_id, '2', $dc3${"html": "<html><body><a>无 href 链接</a><a href=\"https://cn.bing.com\">必应</a><div>不是链接</div></body></html>"}$dc3$, $dc3$"无 href 链接 -> None\n必应 -> https://cn.bing.com"$dc3$, False, '包含缺失 href 属性的链接，以及普通 div（非链接）不应被提取', 'CONTAINS', 8),
    (new_task_id, '3', $dc3${"html": "<html><body><a href=\"/path?param=中文&key=value\">编码测试</a><a href=\"https://unicode.com\">Unicode</a></body></html>"}$dc3$, $dc3$"编码测试 -> /path?param=中文&key=value\nUnicode -> https://unicode.com"$dc3$, True, 'URL 包含中文和特殊字符的情况', 'CONTAINS', 9),
    (new_task_id, '4', $dc3${"html": "<html><body><a href=\"https://a.com\"><span class=\"icon\">🔗</span>带图标的链接</a></body></html>"}$dc3$, $dc3$"🔗带图标的链接 -> https://a.com"$dc3$, True, '链接包含子标签（如 <span>）的情况，文本应包含子标签内的文字', 'CONTAINS', 10),
    (new_task_id, '5', $dc3${"html": "<html><body><!-- 注释里的 <a> 链接 --><a href=\"https://visible.com\">可见链接</a><script>document.write('<a href=\"https://invisible.com\">脚本链接</a>')</script></body></html>"}$dc3$, $dc3$"可见链接 -> https://visible.com"$dc3$, True, '注释和 script 标签内的 <a> 不应被提取，只有 DOM 树中实际存在的链接才被提取', 'CONTAINS', 11),
    (new_task_id, '6', $dc3${"html": "<html><body>\n    <div class=\"nav\">\n        <a href=\"/home\"> 首页 </a>\n        <a href=\"/about\"> 关于 </a>\n        <a href=\"\"> 空 href </a>\n        <a href=\"https://demo.com\">  示例站  </a>\n    </div>\n</body></html>"}$dc3$, $dc3$"首页 -> /home\n关于 -> /about\n空 href -> \n示例站 -> https://demo.com"$dc3$, True, '空字符串 href（不是缺失，是显式空值）以及文本首尾含空白字符的情况', 'CONTAINS', 12);
END $$;