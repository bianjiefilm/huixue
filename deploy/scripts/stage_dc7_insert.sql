-- DC7: JSON/XML 数据解析
DO $$
DECLARE new_task_id INTEGER;
BEGIN
  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 7;
  IF new_task_id IS NOT NULL THEN
    DELETE FROM task_tests WHERE task_id = new_task_id;
    DELETE FROM tasks WHERE id = new_task_id;
  END IF;

  INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
  VALUES (
    4,
    'JSON/XML 数据解析',
    'PRACTICE',
    7,
    'intermediate',
    $dc7$# JSON/XML 数据解析学习手册

## 一、任务类型

本关卡为 Python 数据解析进阶练习，重点掌握使用 Python 内置库解析 JSON 和 XML 格式的结构化数据。具体任务包括：从 API 返回的嵌套 JSON 响应中精确提取目标字段，将多层嵌套的 JSON 结构展平为扁平字典，使用 ElementTree 解析 XML 文档并通过 XPath 表达式定位元素，以及处理各种异常情况和边界条件。通过本关卡的学习，你将能够熟练处理实际工作中常见的 JSON/XML 数据解析需求，编写出健壮且高效的解析代码。

## 二、学习环境

- **编程语言**: Python 3.8+
- **运行环境**: 标准 Python 环境，无需安装额外依赖
- **核心依赖**: Python 内置库 `json` 和 `xml.etree.ElementTree`
- **输入方式**: 函数接收 JSON 字符串、XML 字符串或文件路径作为输入
- **输出方式**: 返回 Python 字典、列表或字符串等结构化数据
- **评分系统**: 评测程序验证解析结果的完整性和正确性

**说明**: Python 的 `json` 模块和 `xml.etree.ElementTree` 模块均为标准库，无需额外安装，可直接导入使用：

```python
import json
import xml.etree.ElementTree as ET
```

## 三、知识点讲解

### 3.1 Python json 模块详解

JSON（JavaScript Object Notation）是一种轻量级的数据交换格式，在 Web API、移动端接口、微服务通信等领域广泛应用。Python 内置的 `json` 模块提供了完整的 JSON 解析和生成功能。

#### json.loads() 与 json.dumps()

`json.loads()` 用于将 JSON 字符串解析为 Python 对象，`json.dumps()` 用于将 Python 对象序列化为 JSON 字符串。

```python
import json

# json.loads(): 字符串转 Python 对象
json_str = '{"name": "张三", "age": 25, "score": 95.5}'
data = json.loads(json_str)
print(data)          # {'name': '张三', 'age': 25, 'score': 95.5}
print(type(data))    # <class 'dict'>

# json.loads() 处理列表
json_list = '[1, 2, 3, "hello", true, null]'
data_list = json.loads(json_list)
print(data_list)     # [1, 2, 3, 'hello', True, None]

# json.dumps(): Python 对象转字符串
python_obj = {"城市": ["北京", "上海", "广州"], "人口": 140000000}
result = json.dumps(python_obj, ensure_ascii=False)
print(result)        # {"城市": ["北京", "上海", "广州"], "人口": 140000000}

# json.dumps() 格式化输出
pretty = json.dumps(python_obj, indent=2, ensure_ascii=False)
print(pretty)
# {
#   "城市": [
#     "北京",
#     "上海",
#     "广州"
#   ],
#   "人口": 140000000
# }
```

#### json.load() 与 json.dump()

`json.load()` 用于从文件对象读取并解析 JSON 数据，`json.dump()` 用于将 Python 对象序列化并写入文件。

```python
import json

# json.load(): 从文件读取 JSON
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# json.dump(): 写入 JSON 到文件
with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# 处理二进制文件
with open('data.json', 'rb') as f:
    data = json.load(f)
```

#### JSON 与 Python 数据类型映射

| JSON 类型 | Python 类型 |
|-----------|-------------|
| object | dict |
| array | list |
| string | str |
| number (integer) | int |
| number (float) | float |
| boolean | bool |
| null | None |

#### JSONDecodeError 异常处理

在解析格式不正确的 JSON 时，会抛出 `json.JSONDecodeError` 异常。健壮的代码应当捕获并处理此异常。

```python
import json

# 正常解析
def safe_loads(json_string):
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
        return None

# 测试
print(safe_loads('{"name": "测试"}'))        # {'name': '测试'}
print(safe_loads('这不是有效的JSON'))          # JSON 解析错误: Expecting value...
print(safe_loads('[1, 2, 3]'))                # [1, 2, 3]

# 更精细的异常处理
def parse_json_robust(json_string):
    if not json_string or not json_string.strip():
        return None
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"解析失败: 行 {e.lineno}, 列 {e.colno}: {e.msg}")
        return None
```

### 3.2 嵌套 JSON 解析

在实际应用中，API 返回的 JSON 数据通常是深层嵌套的结构，正确访问嵌套字段是数据解析的核心技能。

#### 基本嵌套访问

```python
import json

data = {
    "code": 200,
    "message": "success",
    "data": {
        "user": {
            "id": 1001,
            "profile": {
                "name": "李四",
                "email": "lisi@example.com"
            }
        },
        "orders": [1, 2, 3]
    }
}

# 逐层访问
user_id = data["data"]["user"]["id"]
user_name = data["data"]["user"]["profile"]["name"]
print(f"用户ID: {user_id}, 姓名: {user_name}")  # 用户ID: 1001, 姓名: 李四
```

#### KeyError 与 TypeError 处理

当访问不存在的键或对非字典类型使用键访问时，会抛出异常。

```python
# 场景1: 键不存在
try:
    value = data["data"]["user"]["phone"]  # phone 键不存在
except KeyError as e:
    print(f"键不存在: {e}")

# 场景2: 类型错误 - 期望字典但得到列表
try:
    value = data["data"]["orders"]["id"]  # orders 是列表
except TypeError as e:
    print(f"类型错误: {e}")

# 安全访问函数
def safe_get(data, *keys, default=None):
    """安全获取嵌套字典中的值"""
    current = data
    for key in keys:
        try:
            if isinstance(current, dict):
                current = current[key]
            else:
                return default
        except (KeyError, TypeError, IndexError):
            return default
    return current

# 使用示例
print(safe_get(data, "data", "user", "profile", "name"))       # 李四
print(safe_get(data, "data", "user", "phone"))                # None
print(safe_get(data, "data", "user", "profile", "age", 0))    # 0
```

#### 递归访问多层嵌套结构

对于深度嵌套或结构不确定的数据，递归访问是更灵活的解决方案。

```python
def get_nested_value(obj, path):
    """
    通过路径获取嵌套值，路径格式: 'key1.key2.0.field'
    """
    if not path:
        return obj

    keys = path.split('.')
    current = obj

    for key in keys:
        if current is None:
            return None

        # 处理列表索引
        if isinstance(key, str) and key.isdigit():
            try:
                current = current[int(key)]
            except (IndexError, TypeError):
                return None
        else:
            try:
                current = current[key]
            except (KeyError, TypeError):
                return None

    return current

# 测试
data = {
    "a": {
        "b": [
            {"c": 1},
            {"c": 2}
        ]
    }
}
print(get_nested_value(data, "a.b.1.c"))    # 2
print(get_nested_value(data, "a.x"))          # None
print(get_nested_value(data, "a.b.5.c"))      # None
```

### 3.3 JSON 数据展平

将嵌套的 JSON 结构展平为单层字典，便于数据存储、传输或进一步处理。

#### 基础展平方法

```python
def flatten_json(data, parent_key='', sep='_'):
    """
    将嵌套 JSON 展平为单层字典
    :param data: 嵌套字典或列表
    :param parent_key: 父级键名前缀
    :param sep: 键名连接符
    :return: 展平后的字典
    """
    items = []

    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, (dict, list)):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))

    elif isinstance(data, list):
        for i, v in enumerate(data):
            new_key = f"{parent_key}{sep}{i}"
            if isinstance(v, (dict, list)):
                items.extend(flatten_json(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))

    else:
        items.append((parent_key, data))

    return dict(items)

# 测试
nested = {
    "name": "产品A",
    "price": 99.9,
    "specs": {
        "weight": "500g",
        "dimensions": {
            "width": 10,
            "height": 20
        }
    },
    "tags": ["热销", "新品"]
}

flattened = flatten_json(nested)
print(flattened)
# {'name': '产品A', 'price': 99.9, 'specs_weight': '500g',
#  'specs_dimensions_width': 10, 'specs_dimensions_height': 20,
#  'tags_0': '热销', 'tags_1': '新品'}
```

#### 自定义展平策略

有时需要更精细地控制展平行为，例如保留某些嵌套结构或自定义键名格式。

```python
def flatten_json_custom(data, prefix='', max_depth=None, current_depth=0):
    """
    支持最大深度限制和自定义前缀的展平函数
    """
    if max_depth is not None and current_depth >= max_depth:
        return {prefix.rstrip('_'): data} if prefix else {'': data}

    items = {}

    if isinstance(data, dict):
        for k, v in data.items():
            new_key = f"{prefix}{k}" if not prefix else f"{prefix}_{k}"
            if isinstance(v, (dict, list)):
                items.update(flatten_json_custom(
                    v, new_key, max_depth, current_depth + 1
                ))
            else:
                items[new_key] = v

    elif isinstance(data, list):
        for i, v in enumerate(data):
            new_key = f"{prefix}_{i}"
            if isinstance(v, (dict, list)):
                items.update(flatten_json_custom(
                    v, new_key, max_depth, current_depth + 1
                ))
            else:
                items[new_key] = v
    else:
        items[prefix] = data

    return items

# 只展平到指定深度
print(flatten_json_custom(nested, max_depth=1))
# {'name': '产品A', 'price': 99.9, 'specs': {'weight': '500g', ...},
#  'tags': ['热销', '新品']}
```

### 3.4 xml.etree.ElementTree 模块详解

ElementTree 是 Python 内置的 XML 解析库，提供简洁高效的 XML 处理能力。相比第三方库（如 lxml），ElementTree 无需额外安装，是处理 XML 数据的首选工具。

#### ET.parse() 与 ET.fromstring()

有两种方式解析 XML：

```python
import xml.etree.ElementTree as ET

# 方式1: 从文件解析
tree = ET.parse('data.xml')
root = tree.getroot()  # 获取根元素

# 方式2: 从字符串解析
xml_string = '''
<bookstore>
    <book category="fiction">
        <title>Python编程</title>
        <author>张三</author>
        <price>59.9</price>
    </book>
</bookstore>
'''
root = ET.fromstring(xml_string)

# 获取根元素信息
print(root.tag)      # bookstore
print(root.attrib)    # {} - 根元素无属性
```

#### 元素的基本属性：tag、attrib、text

```python
# 遍历所有 book 元素
for book in root.findall('book'):
    print(f"Tag: {book.tag}")           # book
    print(f"Attrib: {book.attrib}")     # {'category': 'fiction'}
    print(f"Category: {book.get('category')}")  # fiction

    # 获取子元素的文本
    title = book.find('title')
    print(f"Title: {title.text}")        # Python编程

    # 获取第一个子元素的文本（简洁写法）
    author = book.find('author')
    if author is not None:
        print(f"Author: {author.text}")
```

#### find()、findall()、iter() 方法

```python
# find(): 查找第一个匹配的元素
first_book = root.find('book')
print(first_book.tag)  # book

# findall(): 查找所有匹配的元素
all_books = root.findall('book')
print(f"共 {len(all_books)} 本书")

# iter(): 遍历所有后代元素（深度优先）
for elem in root.iter():
    print(f"Tag: {elem.tag}, Text: {elem.text.strip() if elem.text else ''}")

# iter() 带过滤器
prices = list(root.iter('price'))
print(f"所有价格: {[p.text for p in prices]}")
```

#### 完整的 XML 解析示例

```python
import xml.etree.ElementTree as ET

xml_data = '''
<catalog>
    <product id="P001" status="active">
        <name>笔记本电脑</name>
        <category>
            <main>电子产品</main>
            <sub>电脑配件</sub>
        </category>
        <price currency="CNY">5999</price>
        <specs>
            <spec name="内存">16GB</spec>
            <spec name="硬盘">512GB SSD</spec>
        </specs>
        <tags>
            <tag>轻薄</tag>
            <tag>高性能</tag>
        </tags>
    </product>
    <product id="P002">
        <name>无线鼠标</name>
        <category>
            <main>电子产品</main>
            <sub>外设</sub>
        </category>
        <price currency="CNY">99</price>
    </product>
</catalog>
'''

root = ET.fromstring(xml_data)

# 解析第一个产品的信息
product = root.find('product')
print(f"产品ID: {product.get('id')}")
print(f"产品名: {product.find('name').text}")
elem = product.find('category/main')
    if elem is not None:
        print(f"主类别: {elem.text}")
print(f"价格: {product.find('price').text} {product.find('price').get('currency')}")

# 获取所有产品规格
for spec in product.findall('specs/spec'):
    print(f"  {spec.get('name')}: {spec.text}")

# 获取所有产品名
for p in root.findall('product'):
    print(f"- {p.find('name').text}")
```

### 3.5 XPath 表达式详解

ElementTree 支持部分 XPath 表达式，可用于精确定位 XML 元素。

#### 常用 XPath 表达式

| 表达式 | 含义 | 示例 |
|--------|------|------|
| tag | 直接子元素 | `book/title` 匹配 book 下的直接 title |
| //tag | 任意位置后代 | `//title` 匹配任意位置的 title |
| * | 任意元素 | `book/*` 匹配 book 下所有直接子元素 |
| [@attr] | 带属性的元素 | `book[@id='P001']` 匹配 id 属性为 P001 的 book |
| text() | 元素文本 | `title/text()` 获取 title 元素的文本内容 |

```python
import xml.etree.ElementTree as ET

xml_data = '''
<company>
    <department id="D001" name="技术部">
        <employee id="E001">
            <name>王五</name>
            <role>工程师</role>
        </employee>
        <employee id="E002">
            <name>赵六</name>
            <role>经理</role>
        </employee>
    </department>
    <department id="D002" name="市场部">
        <employee id="E003">
            <name>孙七</name>
            <role>专员</role>
        </employee>
    </department>
</company>
'''

root = ET.fromstring(xml_data)

# //tag: 查找任意位置的元素
all_employees = root.findall('.//employee')  # 等价于 //employee
for emp in all_employees:
    print(f"员工: {emp.find('name').text}, ID: {emp.get('id')}")

# /tag[@attr]: 带属性筛选
tech_dept = root.find("department[@id='D001']")
print(f"部门: {tech_dept.get('name')}")

# 查找特定部门下的所有员工
for emp in tech_dept.findall('employee'):
    print(f"  - {emp.find('name').text}")

# text(): 获取文本内容
names = [el.text for el in root.iter('name')]
print(f"所有姓名: {[n.text for n in root.iter('name')]}")

# 组合条件
emp_e001 = root.find(".//employee[@id='E001']")
print(f"E001: {emp_e001.find('name').text}, 职位: {emp_e001.find('role').text}")
```

#### contains() 函数

`contains()` 函数用于匹配属性值包含特定字符串的元素。

```python
import xml.etree.ElementTree as ET

xml_data = '''
<products>
    <item type="electronics" brand="apple">iPhone 15</item>
    <item type="electronics" brand="samsung">Galaxy S24</item>
    <item type="furniture">办公桌</item>
    <item type="electronics" brand="huawei">Mate 60</item>
</products>
'''

root = ET.fromstring(xml_data)

# 注意: ElementTree 标准版本对 contains() 支持有限
# 可以通过遍历+条件判断实现类似功能
for item in root.findall('item'):
    item_type = item.get('type', '')
    brand = item.get('brand', '')
    if 'electronics' in item_type:
        print(f"电子产品: {item.text}", end="")
        if brand:
            print(f" ({brand})")
        else:
            print()

# 使用 attrib 筛选
electronics = [item for item in root.findall('item')
               if item.get('type') == 'electronics']
print(f"\n电子产品总数: {len(electronics)}")
```

#### 复杂的 XPath 查询

```python
# 查找所有有 brand 属性的 item
items_with_brand = root.findall('.//item[@brand]')
print(f"有品牌的产品: {[item.text for item in items_with_brand]}")

# 查找没有 brand 属性的 item
items_without_brand = [item for item in root.findall('.//item')
                       if not item.get('brand')]
print(f"无品牌的产品: {[item.text for item in items_without_brand]}")

# 嵌套条件
for dept in root.findall('department'):
    print(f"\n部门: {dept.get('name')}")
    for emp in dept.findall('employee'):
        role = emp.find('role').text
        if role in ['工程师', '经理']:  # 筛选特定职位
            print(f"  - {emp.find('name').text}: {role}")
```

### 3.6 JSON 与 XML 对比

JSON 和 XML 都是常用的数据交换格式，但各有特点和适用场景。

#### 结构差异对比

```python
# XML 示例
xml_example = '''
<order id="1001">
    <customer>张三</customer>
    <items>
        <item>
            <product_id>P001</product_id>
            <quantity>2</quantity>
        </item>
        <item>
            <product_id>P002</product_id>
            <quantity>1</quantity>
        </item>
    </items>
</order>
'''

# JSON 示例
json_example = {
    "order_id": "1001",
    "customer": "张三",
    "items": [
        {"product_id": "P001", "quantity": 2},
        {"product_id": "P002", "quantity": 1}
    ]
}
```

#### 优缺点对比

| 特性 | JSON | XML |
|------|------|-----|
| **语法简洁性** | 更简洁，冗余少 | 标签冗长，冗余较多 |
| **数据类型** | 原生支持数字、布尔、null | 全部为文本，需要模式定义 |
| **可读性** | 结构紧凑 | 有缩进时更易读 |
| **数据模型** | 键值对、数组 | 树形结构、属性、命名空间 |
| **注释支持** | 不支持 | 支持注释 |
| **元数据** | 需要约定 | 属性可存储元数据 |
| **Schema** | JSON Schema（可选） | DTD、XSD（强大） |
| **处理复杂度** | 解析简单 | 解析相对复杂 |
| **应用场景** | API响应、配置文件 | 文档、配置文件、Web服务 |

#### 适用场景选择

```python
# 选择 JSON 的场景
json_scenarios = [
    "RESTful API 响应",           # 简洁高效
    "前后端数据交互",              # 原生 JavaScript 支持
    "NoSQL 数据库",               # MongoDB 等文档数据库
    "配置文件",                   # 简洁的配置格式
    "轻量级数据传输"              # 移动端优先
]

# 选择 XML 的场景
xml_scenarios = [
    "企业级 Web 服务 (SOAP)",     # 成熟的 SOAP 协议
    "复杂文档结构",                # Word、PDF 等格式
    "需要数据验证",               # XSD Schema 强大验证
    "需要处理命名空间",            # SVG、RSS/Atom
    "需要注释的配置文件"          # 配置可文档化
]
```

#### 数据格式转换

```python
import json
import xml.etree.ElementTree as ET

# JSON 转 XML
def json_to_xml(data, root_tag="root"):
    """将 Python 对象转换为简单的 XML 字符串"""
    def build_element(tag, value):
        elem = ET.Element(tag)
        if isinstance(value, dict):
            for k, v in value.items():
                elem.append(build_element(k, v))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                child = build_element(f"{tag}_item", item)
                elem.append(child)
        else:
            elem.text = str(value)
        return elem

    root = ET.Element(root_tag)
    if isinstance(data, dict):
        for k, v in data.items():
            root.append(build_element(k, v))
    else:
        root.text = str(data)

    return ET.tostring(root, encoding='unicode')

# XML 转 JSON
def xml_to_json(root):
    """将 XML 元素转换为 Python 字典"""
    result = {}

    # 处理属性
    if root.attrib:
        result['@attributes'] = root.attrib

    # 处理子元素
    children = list(root)
    if children:
        child_dict = {}
        for child in children:
            child_data = xml_to_json(child)
            tag = child.tag

            if tag in child_dict:
                # 多个同名子元素，转为列表
                if not isinstance(child_dict[tag], list):
                    child_dict[tag] = [child_dict[tag]]
                child_dict[tag].append(child_data)
            else:
                child_dict[tag] = child_data

        result.update(child_dict)
    else:
        # 叶节点，返回文本
        result = root.text if root.text else ""

    # 如果根元素只有一个子元素且无属性，直接返回子元素
    if len(result) == 1 and '@attributes' not in result:
        return result

    return result

# 测试
data = {"name": "测试", "values": [1, 2, 3]}
xml_str = json_to_xml(data)
print(f"JSON -> XML: {xml_str}")
```

### 3.7 深度嵌套数据处理

处理深层嵌套或结构复杂的数据时，需要设计健壮的递归函数和异常处理机制。

#### 递归函数设计原则

```python
# 递归遍历嵌套结构的通用模式
def traverse(data, path=""):
    """
    递归遍历任意嵌套结构
    """
    results = []

    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path}.{key}" if path else key
            if isinstance(value, (dict, list)):
                results.extend(traverse(value, new_path))
            else:
                results.append((new_path, value))

    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{path}[{i}]"
            if isinstance(item, (dict, list)):
                results.extend(traverse(item, new_path))
            else:
                results.append((new_path, item))

    else:
        results.append((path, data))

    return results

# 测试
nested_data = {
    "a": {
        "b": [1, 2, 3],
        "c": {
            "d": "value"
        }
    }
}

for path, value in traverse(nested_data):
    print(f"{path} = {value}")
# a.b[0] = 1
# a.b[1] = 2
# a.b[2] = 3
# a.c.d = value
```

#### 默认值保护模式

```python
from typing import Any, Optional

class SafeAccessor:
    """安全的嵌套数据访问器"""

    def __init__(self, data):
        self._data = data

    def get(self, *keys, default: Any = None) -> Any:
        """安全的链式获取"""
        current = self._data

        for key in keys:
            if current is None:
                return default

            try:
                if isinstance(current, dict):
                    current = current[key]
                elif isinstance(current, list):
                    idx = int(key) if isinstance(key, str) else key
                    current = current[idx]
                else:
                    return default
            except (KeyError, IndexError, TypeError, ValueError):
                return default

        return current

    def get_or_raise(self, *keys, exc_type=KeyError):
        """获取值，不存在则抛出异常"""
        result = self.get(*keys)
        if result is None:
            raise exc_type(f"Path {'.'.join(map(str, keys))} not found")
        return result

# 使用示例
data = {
    "user": {
        "profile": {
            "settings": {
                "theme": "dark"
            }
        },
        "orders": []
    }
}

accessor = SafeAccessor(data)
print(accessor.get("user", "profile", "settings", "theme"))      # dark
print(accessor.get("user", "profile", "avatar"))                  # None
print(accessor.get("user", "profile", "avatar", default="default.png"))  # default.png
print(accessor.get("user", "orders", 0))                          # None (空列表)
```

#### 复杂数据的条件提取

```python
def extract_by_condition(data, condition_func, path_prefix=""):
    """
    根据条件函数提取满足条件的路径和值
    """
    results = []

    if isinstance(data, dict):
        for key, value in data.items():
            new_path = f"{path_prefix}.{key}" if path_prefix else key
            if isinstance(value, (dict, list)):
                results.extend(extract_by_condition(value, condition_func, new_path))
            else:
                if condition_func(value, key, new_path):
                    results.append((new_path, value))

    elif isinstance(data, list):
        for i, item in enumerate(data):
            new_path = f"{path_prefix}[{i}]"
            if isinstance(item, (dict, list)):
                results.extend(extract_by_condition(item, condition_func, new_path))
            else:
                if condition_func(item, None, new_path):
                    results.append((new_path, item))

    return results

# 示例: 提取所有数值大于 100 的字段
data = {
    "prices": {
        "apple": 50,
        "banana": 20,
        "orange": 150
    },
    "stock": [30, 200, 80]
}

results = extract_by_condition(
    data,
    lambda v, k, p: isinstance(v, (int, float)) and v > 100
)
print(results)
# [('prices.orange', 150), ('stock[1]', 200)]
```

## 四、实战代码

### 4.1 解析嵌套 JSON 数据

以下函数演示如何从电商 API 响应中提取商品信息：

```python
import json
from typing import Any, Optional, List, Dict

def parse_ecommerce_response(response_json: str) -> Dict[str, Any]:
    """
    解析电商 API 返回的嵌套 JSON 数据

    示例响应结构:
    {
        "code": 200,
        "message": "success",
        "data": {
            "products": [
                {
                    "id": "P001",
                    "name": "笔记本电脑",
                    "category": {
                        "main": "电子产品",
                        "sub": "电脑"
                    },
                    "price": {
                        "current": 5999,
                        "original": 6999
                    },
                    "specs": {
                        "brand": "品牌A",
                        "model": "2024款"
                    }
                }
            ],
            "pagination": {
                "page": 1,
                "page_size": 20,
                "total": 100
            }
        }
    }
    """
    try:
        data = json.loads(response_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    # 检查响应状态
    if data.get("code") != 200:
        raise ValueError(f"API error: {data.get('message')}")

    result = {
        "products": [],
        "total_count": 0,
        "page": 1
    }

    # 安全获取嵌套数据
    products_data = data.get("data", {}).get("products", [])
    pagination = data.get("data", {}).get("pagination", {})

    # 提取分页信息
    result["total_count"] = pagination.get("total", 0)
    result["page"] = pagination.get("page", 1)

    # 提取商品信息
    for product in products_data:
        parsed_product = {
            "id": product.get("id"),
            "name": product.get("name"),
            "category_main": product.get("category", {}).get("main"),
            "category_sub": product.get("category", {}).get("sub"),
            "price_current": product.get("price", {}).get("current"),
            "price_original": product.get("price", {}).get("original"),
            "brand": product.get("specs", {}).get("brand"),
            "model": product.get("specs", {}).get("model"),
        }
        result["products"].append(parsed_product)

    return result


def get_nested_value(data: Dict, *keys, default=None):
    """
    安全获取嵌套字典中的值
    支持列表索引（用数字或字符串数字）
    """
    current = data
    for key in keys:
        try:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, list):
                idx = int(key)
                current = current[idx]
            else:
                return default
        except (KeyError, IndexError, TypeError, ValueError):
            return default
    return current


# 测试
response = '''
{
    "code": 200,
    "message": "success",
    "data": {
        "products": [
            {
                "id": "P001",
                "name": "笔记本电脑",
                "category": {"main": "电子产品", "sub": "电脑"},
                "price": {"current": 5999, "original": 6999},
                "specs": {"brand": "品牌A", "model": "2024款"}
            }
        ],
        "pagination": {"page": 1, "page_size": 20, "total": 100}
    }
}
'''

result = parse_ecommerce_response(response)
print(f"总数: {result['total_count']}, 第 {result['page']} 页")
print(f"商品: {result['products'][0]['name']}, 价格: {result['products'][0]['price_current']}")
```

### 4.2 解析 XML 数据

以下函数演示如何从 XML 文档中提取结构化数据：

```python
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

def parse_product_catalog(xml_string: str) -> Dict[str, List[Dict]]:
    """
    解析产品目录 XML，返回结构化数据

    XML 结构:
    <catalog>
        <product id="P001" category="electronics">
            <name>产品名</name>
            <price currency="CNY">99.99</price>
            <specs>
                <spec name="属性名">属性值</spec>
            </specs>
            <tags>
                <tag>标签1</tag>
            </tags>
        </product>
    </catalog>
    """
    root = ET.fromstring(xml_string)

    result = {
        "products": [],
        "categories": set()
    }

    # 遍历所有产品
    for product in root.findall('.//product'):
        prod_data = {
            "id": product.get('id'),
            "category": product.get('category'),
            "name": None,
            "price": None,
            "currency": None,
            "specs": {},
            "tags": []
        }

        # 添加到类别集合
        if prod_data["category"]:
            result["categories"].add(prod_data["category"])

        # 提取产品名称
        name_elem = product.find('name')
        if name_elem is not None:
            prod_data["name"] = name_elem.text

        # 提取价格（含货币单位）
        price_elem = product.find('price')
        if price_elem is not None:
            prod_data["price"] = float(price_elem.text) if price_elem.text else None
            prod_data["currency"] = price_elem.get('currency')

        # 提取规格（通过属性定位）
        specs_elem = product.find('specs')
        if specs_elem is not None:
            for spec in specs_elem.findall('spec'):
                spec_name = spec.get('name')
                spec_value = spec.text
                if spec_name:
                    prod_data["specs"][spec_name] = spec_value

        # 提取标签
        tags_elem = product.find('tags')
        if tags_elem is not None:
            for tag in tags_elem.findall('tag'):
                if tag.text:
                    prod_data["tags"].append(tag.text.strip())

        result["products"].append(prod_data)

    # 转换集合为列表
    result["categories"] = list(result["categories"])

    return result


def find_products_by_category(xml_string: str, category: str) -> List[Dict]:
    """
    使用 XPath 查找特定类别的产品
    """
    root = ET.fromstring(xml_string)

    # 使用 XPath 表达式筛选
    xpath_expr = f".//product[@category='{category}']"
    products = root.findall(xpath_expr)

    results = []
    for product in products:
        prod_info = {
            "id": product.get('id'),
            "name": product.find('name').text if product.find('name') is not None else None,
            "price": product.find('price').text if product.find('price') is not None else None
        }
        results.append(prod_info)

    return results


# 测试
catalog_xml = '''
<catalog>
    <product id="P001" category="electronics">
        <name>笔记本电脑</name>
        <price currency="CNY">5999</price>
        <specs>
            <spec name="品牌">品牌A</spec>
            <spec name="内存">16GB</spec>
        </specs>
        <tags>
            <tag>热销</tag>
            <tag>新品</tag>
        </tags>
    </product>
    <product id="P002" category="furniture">
        <name>办公桌</name>
        <price currency="CNY">999</price>
        <specs>
            <spec name="材质">实木</spec>
        </specs>
        <tags>
            <tag>环保</tag>
        </tags>
    </product>
</catalog>
'''

result = parse_product_catalog(catalog_xml)
print(f"类别: {result['categories']}")
print(f"电子产品: {find_products_by_category(catalog_xml, 'electronics')}")

for p in result["products"]:
    print(f"{p['name']}: {p['price']} {p['currency']}")
    print(f"  规格: {p['specs']}")
    print(f"  标签: {p['tags']}")
```

## 五、实战练习

### 5.1 练习背景

假设你需要从电商平台采集商品数据。平台 API 返回的 JSON 数据包含多层嵌套的商品信息，你需要编写解析函数提取所需字段。

### 5.2 示例数据

**API 返回的 JSON 数据结构**:

```json
{
    "status": "success",
    "timestamp": 1712000000,
    "data": {
        "total_count": 150,
        "page_info": {
            "current_page": 1,
            "page_size": 10,
            "has_next": true
        },
        "items": [
            {
                "product_id": "SKU001",
                "basic_info": {
                    "name": "无线蓝牙耳机",
                    "brand": "品牌X",
                    "model": "TWS-2000"
                },
                "price_info": {
                    "current_price": 299.00,
                    "original_price": 399.00,
                    "discount": 0.75
                },
                "inventory": {
                    "available": 500,
                    "reserved": 50
                },
                "category_path": [
                    {"level": 1, "name": "数码产品"},
                    {"level": 2, "name": "耳机音响"},
                    {"level": 3, "name": "蓝牙耳机"}
                ],
                "specs": {
                    "颜色": "黑色",
                    "续航时间": "24小时",
                    "防水等级": "IPX5"
                },
                "rating": {
                    "average": 4.5,
                    "count": 1250
                }
            }
        ]
    }
}
```

**XML 格式的同类数据**:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<api_response status="success">
    <timestamp>1712000000</timestamp>
    <data>
        <total_count>150</total_count>
        <page_info>
            <current_page>1</current_page>
            <page_size>10</page_size>
            <has_next>true</has_next>
        </page_info>
        <items>
            <product id="SKU001">
                <basic_info>
                    <name>无线蓝牙耳机</name>
                    <brand>品牌X</brand>
                    <model>TWS-2000</model>
                </basic_info>
                <price_info>
                    <current_price>299.00</current_price>
                    <original_price>399.00</original_price>
                    <discount>0.75</discount>
                </price_info>
                <inventory>
                    <available>500</available>
                    <reserved>50</reserved>
                </inventory>
                <category_path>
                    <category level="1">数码产品</category>
                    <category level="2">耳机音响</category>
                    <category level="3">蓝牙耳机</category>
                </category_path>
                <specs>
                    <spec name="颜色">黑色</spec>
                    <spec name="续航时间">24小时</spec>
                    <spec name="防水等级">IPX5</spec>
                </specs>
                <rating>
                    <average>4.5</average>
                    <count>1250</count>
                </rating>
            </product>
        </items>
    </data>
</api_response>
```

### 5.3 解析要点

1. **处理嵌套结构**: 商品信息有多层嵌套（basic_info, price_info, specs 等）
2. **处理列表数据**: category_path 是一个列表，需要遍历获取完整路径
3. **计算派生字段**: 如可用库存 = available - reserved
4. **处理属性**: XML 中规格信息存储在 name 属性中
5. **异常处理**: 某些字段可能缺失，需要有默认值

### 5.4 完整解析示例

```python
import json
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any

# ============= JSON 解析示例 =============
def parse_product_from_json(product_data: Dict) -> Dict[str, Any]:
    """从嵌套 JSON 中提取商品信息"""

    # 安全获取嵌套值
    def safe_get(d, *keys, default=None):
        curr = d
        for k in keys:
            if isinstance(curr, dict):
                curr = curr.get(k)
            elif isinstance(curr, list):
                try:
                    curr = curr[int(k)]
                except (ValueError, IndexError):
                    return default
            else:
                return default
            if curr is None:
                return default
        return curr

    # 提取基本信息
    result = {
        "product_id": safe_get(product_data, "product_id"),
        "name": safe_get(product_data, "basic_info", "name"),
        "brand": safe_get(product_data, "basic_info", "brand"),
        "model": safe_get(product_data, "basic_info", "model"),
        "current_price": safe_get(product_data, "price_info", "current_price"),
        "original_price": safe_get(product_data, "price_info", "original_price"),
        "available_stock": safe_get(product_data, "inventory", "available", default=0),
        "reserved_stock": safe_get(product_data, "inventory", "reserved", default=0),
        "rating": safe_get(product_data, "rating", "average"),
        "review_count": safe_get(product_data, "rating", "count"),
    }

    # 计算可用库存
    result["actual_stock"] = result["available_stock"] - result["reserved_stock"]

    # 提取类别路径
    category_path = safe_get(product_data, "category_path", default=[])
    if isinstance(category_path, list):
        result["category_path"] = "/".join([
            cat.get("name", "") for cat in category_path
            if isinstance(cat, dict)
        ])
    else:
        result["category_path"] = ""

    # 提取规格（保留为字典）
    specs = safe_get(product_data, "specs", default={})
    result["specs"] = specs if isinstance(specs, dict) else {}

    return result


# ============= XML 解析示例 =============
def parse_product_from_xml(product_elem) -> Dict[str, Any]:
    """从 XML 元素中提取商品信息"""

    def find_text(elem, xpath):
        """在元素中查找文本"""
        target = elem.find(xpath)
        return target.text if target is not None else None

    def find_int(elem, xpath, default=0):
        """查找并转换为整数"""
        text = find_text(elem, xpath)
        try:
            return int(text) if text else default
        except ValueError:
            return default

    def find_float(elem, xpath, default=0.0):
        """查找并转换为浮点数"""
        text = find_text(elem, xpath)
        try:
            return float(text) if text else default
        except ValueError:
            return default

    result = {
        "product_id": product_elem.get('id'),
        "name": find_text(product_elem, 'basic_info/name'),
        "brand": find_text(product_elem, 'basic_info/brand'),
        "model": find_text(product_elem, 'basic_info/model'),
        "current_price": find_float(product_elem, 'price_info/current_price'),
        "original_price": find_float(product_elem, 'price_info/original_price'),
        "available_stock": find_int(product_elem, 'inventory/available'),
        "reserved_stock": find_int(product_elem, 'inventory/reserved'),
        "rating": find_float(product_elem, 'rating/average'),
        "review_count": find_int(product_elem, 'rating/count'),
    }

    # 计算可用库存
    result["actual_stock"] = result["available_stock"] - result["reserved_stock"]

    # 提取类别路径
    category_elems = product_elem.findall('category_path/category')
    result["category_path"] = "/".join([c.text for c in category_elems if c.text])

    # 提取规格
    specs = {}
    for spec in product_elem.findall('specs/spec'):
        name = spec.get('name')
        if name and spec.text:
            specs[name] = spec.text
    result["specs"] = specs

    return result


# ============= 测试 =============
product_json = {
    "product_id": "SKU001",
    "basic_info": {"name": "无线蓝牙耳机", "brand": "品牌X", "model": "TWS-2000"},
    "price_info": {"current_price": 299.00, "original_price": 399.00, "discount": 0.75},
    "inventory": {"available": 500, "reserved": 50},
    "category_path": [{"level": 1, "name": "数码产品"}, {"level": 2, "name": "耳机音响"}],
    "specs": {"颜色": "黑色", "续航时间": "24小时"},
    "rating": {"average": 4.5, "count": 1250}
}

parsed = parse_product_from_json(product_json)
print(f"商品: {parsed['name']}")
print(f"品牌: {parsed['brand']}")
print(f"现价: {parsed['current_price']}, 原价: {parsed['original_price']}")
print(f"实际库存: {parsed['actual_stock']}")
print(f"类别: {parsed['category_path']}")
print(f"规格: {parsed['specs']}")
```

## 六、评测标准

1. **JSON 解析正确性**: 正确使用 `json.loads()` 解析 JSON 字符串，正确处理 `JSONDecodeError`
2. **XML 解析正确性**: 正确使用 `ET.fromstring()` 或 `ET.parse()` 解析 XML
3. **嵌套访问准确性**: 正确访问多层嵌套的字段，处理 KeyError 和 TypeError
4. **XPath 使用准确性**: 正确使用 XPath 表达式定位元素
5. **默认值处理**: 对缺失字段提供合理的默认值，不抛出未处理异常
6. **数据展平能力**: 能够将嵌套 JSON 展平为扁平结构

**常见错误**:
- 直接使用 `[key]` 访问嵌套字段而不检查键是否存在
- 忽略 JSON 解析失败的情况，导致后续代码报错
- 对列表类型数据使用字典访问方式
- XPath 表达式写错（如 `//tag` 与 `/tag` 的区别）
- 忘记处理 XML 元素的 `text` 属性可能为 None

**最佳实践**:
- 始终使用 try-except 包裹可能失败的解析操作
- 提供默认值或默认值保护函数
- 对复杂嵌套结构编写单元测试
- 使用类型注解提高代码可读性
- 解析前先打印数据结构，了解实际格式
$dc7$,
    $dc7${"questions": [{"id": "q7-1", "type": "concept", "difficulty": "easy", "question": "Python 的 `json` 模块中，以下哪个函数用于将 JSON 字符串转换为 Python 对象？", "options": ["A. json.dumps()", "B. json.loads()", "C. json.dump()", "D. json.load()"], "answer": "B", "explanation": "`json.loads()` (load string) 用于将 JSON 字符串解析为 Python 对象（如 dict、list）。`json.dumps()` 是反向操作，将 Python 对象序列化为 JSON 字符串。`json.load()` 和 `json.dump()` 用于文件操作。"}, {"id": "q7-2", "type": "concept", "difficulty": "easy", "question": "当尝试解析格式错误的 JSON 字符串时，Python 会抛出什么异常？", "options": ["A. ValueError", "B. TypeError", "C. json.JSONDecodeError", "D. KeyError"], "answer": "C", "explanation": "解析无效 JSON 时，`json` 模块会抛出 `json.JSONDecodeError` 异常，这是 `ValueError` 的子类。健壮的代码应当捕获此异常并做适当处理，如返回 None 或记录错误日志。"}, {"id": "q7-3", "type": "concept", "difficulty": "medium", "question": "使用 `xml.etree.ElementTree` 解析 XML 时，以下哪个方法用于从字符串直接解析 XML？", "options": ["A. ET.parse()", "B. ET.fromstring()", "C. ET.read()", "D. ET.load()"], "answer": "B", "explanation": "`ET.fromstring()` 用于将 XML 字符串直接解析为 Element 对象。`ET.parse()` 用于从文件或文件对象解析 XML，返回一个 ElementTree 对象，需要通过 `.getroot()` 获取根元素。"}, {"id": "q7-4", "type": "calculation", "difficulty": "medium", "question": "对于 XML 结构 `<book category=\"fiction\"><title>Python编程</title></book>`，以下代码的输出是什么？\n\n```python\nimport xml.etree.ElementTree as ET\nxml_str = '<book category=\"fiction\"><title>Python编程</title></book>'\nroot = ET.fromstring(xml_str)\nprint(root.tag, root.attrib['category'], root.find('title').text)\n```", "options": ["A. book fiction Python编程", "B. book category fiction", "C. root fiction Python编程", "D. book {'category': 'fiction'} Python编程"], "answer": "A", "explanation": "`root.tag` 返回元素标签名 'book'，`root.attrib['category']` 返回属性值 'fiction'，`root.find('title').text` 返回 title 子元素的文本内容 'Python编程'。"}, {"id": "q7-5", "type": "concept", "difficulty": "medium", "question": "在 ElementTree 中，XPath 表达式 `//title` 和 `/title` 的区别是什么？", "options": ["A. 两者完全相同，都表示查找所有 title 元素", "B. //title 查找任意位置的后代 title，/title 只查找根元素的直接子元素", "C. /title 查找所有 title，//title 只查找直接子元素", "D. //title 用于属性查找，/title 用于文本查找"], "answer": "B", "explanation": "//title 使用后代轴（descendant-or-self），匹配文档任意位置的 title 元素。/title 使用子轴（child），只匹配根元素的直接子元素 title。在根元素下没有直接子元素 title 时，/title 会返回 None。"}, {"id": "q7-6", "type": "concept", "difficulty": "medium", "question": "JSON 和 XML 相比，以下哪项不是 JSON 的优势？", "options": ["A. 语法更简洁，数据冗余少", "B. 原生支持数字、布尔值等数据类型", "C. 支持注释，便于文档化", "D. 解析速度通常更快"], "answer": "C", "explanation": "JSON 不支持注释，这是它相对于 XML 的劣势之一。XML 支持注释（<!-- 注释内容 -->），可以用于文档化配置文件。JSON 的优势包括：语法简洁、原生数据类型支持、解析速度快等。"}, {"id": "q7-7", "type": "calculation", "difficulty": "medium", "question": "给定以下嵌套 JSON，要获取 \"Python\"，正确的访问方式是什么？\n\n```json\n{\"data\": {\"languages\": [\"Python\", \"Java\", \"Go\"]}}\n```", "options": ["A. data['languages']['Python']", "B. data['languages'][0]", "C. data['languages'][1]", "D. data[0]['languages']"], "answer": "B", "explanation": "'languages' 是一个列表，第一元素（索引0）是字符串 'Python'。所以正确访问方式是 `data['languages'][0]`。选项 A 试图用字符串作为列表索引，选项 C 返回 'Java'，选项 D 的访问顺序错误。"}, {"id": "q7-8", "type": "concept", "difficulty": "medium", "question": "以下哪个函数调用可以将 Python 对象 `{'name': '张三', 'age': 25}` 转换为 JSON 字符串？", "options": ["A. json.loads({'name': '张三', 'age': 25})", "B. json.dumps({'name': '张三', 'age': 25})", "C. json.load({'name': '张三', 'age': 25})", "D. json.parse({'name': '张三', 'age': 25})"], "answer": "B", "explanation": "`json.dumps()` (dump string) 将 Python 对象序列化为 JSON 字符串。`json.loads()` 接收字符串，`json.load()` 接收文件对象。Python 没有 `json.parse()` 函数。"}, {"id": "q7-9", "type": "coding", "difficulty": "medium", "question": "请编写函数 `parse_nested_json(json_str, path)`，解析嵌套 JSON 字符串并按路径提取值。\n\n参数说明：\n- `json_str`: JSON 格式的字符串\n- `path`: 点分隔的路径字符串，如 'data.user.name'\n\n返回：路径对应的值，如果路径不存在或 JSON 无效则返回 None。\n\n示例：\n- 输入: `parse_nested_json('{\"data\":{\"user\":{\"name\":\"张三\"}}}', 'data.user.name')`\n- 输出: `'张三'`", "correct_answer": "import json\n\ndef parse_nested_json(json_str, path):\n    \"\"\"\n    解析嵌套 JSON 字符串并按路径提取值\n\n    参数:\n        json_str: JSON 格式的字符串\n        path: 点分隔的路径字符串，如 'data.user.name'\n\n    返回:\n        路径对应的值，如果路径不存在或 JSON 无效则返回 None\n    \"\"\"\n    try:\n        data = json.loads(json_str)\n    except json.JSONDecodeError:\n        return None\n\n    keys = path.split('.')\n    current = data\n\n    for key in keys:\n        if isinstance(current, dict):\n            current = current.get(key)\n        elif isinstance(current, list):\n            try:\n                current = current[int(key)]\n            except (ValueError, IndexError):\n                return None\n        else:\n            return None\n\n        if current is None:\n            return None\n\n    return current", "test_cases": [{"input": "'{\\\"data\\\":{\\\"user\\\":{\\\"name\\\":\\\"张三\\\"}}}', 'data.user.name'", "expected": "'张三'"}, {"input": "'{\\\"data\\\":{\\\"items\\\":[\\\"a\\\",\\\"b\\\",\\\"c\\\"]}}', 'data.items.1'", "expected": "'b'"}, {"input": "'{\\\"name\\\":\\\"test\\\"}', 'name'", "expected": "'test'"}, {"input": "'{\\\"a\\\":{\\\"b\\\":{\\\"c\\\":1}}}', 'a.x.c'", "expected": "null"}, {"input": "'invalid json', 'data'", "expected": "null"}, {"input": "'{\\\"data\\\":{\\\"list\\\":[{\\\"id\\\":1},{\\\"id\\\":2}]}}', 'data.list.1.id'", "expected": "2"}]}, {"id": "q7-10", "type": "coding", "difficulty": "medium", "question": "请编写函数 `parse_product_xml(xml_str)`，解析产品目录 XML 并提取所有产品的关键信息。\n\nXML 结构：\n```xml\n<catalog>\n    <product id=\"产品ID\">\n        <name>产品名称</name>\n        <price currency=\"CNY\">价格</price>\n        <specs>\n            <spec name=\"规格名\">规格值</spec>\n        </specs>\n        <tags>\n            <tag>标签名</tag>\n        </tags>\n    </product>\n</catalog>\n```\n\n返回格式：包含字典的列表，每个字典包含 'id', 'name', 'price', 'currency', 'specs', 'tags' 字段。", "correct_answer": "import xml.etree.ElementTree as ET\n\ndef parse_product_xml(xml_str):\n    \"\"\"\n    解析产品目录 XML，提取所有产品的关键信息\n\n    参数:\n        xml_str: XML 格式的字符串\n\n    返回:\n        包含字典的列表，每个字典包含:\n        - id: 产品ID\n        - name: 产品名称\n        - price: 价格（浮点数）\n        - currency: 货币单位\n        - specs: 规格字典\n        - tags: 标签列表\n    \"\"\"\n    try:\n        root = ET.fromstring(xml_str)\n    except ET.ParseError:\n        return []\n\n    results = []\n\n    for product in root.findall('.//product'):\n        product_info = {\n            'id': product.get('id'),\n            'name': None,\n            'price': None,\n            'currency': None,\n            'specs': {},\n            'tags': []\n        }\n\n        # 提取名称\n        name_elem = product.find('name')\n        if name_elem is not None and name_elem.text:\n            product_info['name'] = name_elem.text.strip()\n\n        # 提取价格\n        price_elem = product.find('price')\n        if price_elem is not None:\n            product_info['currency'] = price_elem.get('currency')\n            if price_elem.text:\n                try:\n                    product_info['price'] = float(price_elem.text.strip())\n                except ValueError:\n                    product_info['price'] = None\n\n        # 提取规格\n        specs_elem = product.find('specs')\n        if specs_elem is not None:\n            for spec in specs_elem.findall('spec'):\n                spec_name = spec.get('name')\n                spec_value = spec.text.strip() if spec.text else ''\n                if spec_name:\n                    product_info['specs'][spec_name] = spec_value\n\n        # 提取标签\n        tags_elem = product.find('tags')\n        if tags_elem is not None:\n            for tag in tags_elem.findall('tag'):\n                if tag.text:\n                    product_info['tags'].append(tag.text.strip())\n\n        results.append(product_info)\n\n    return results", "test_cases": [{"input": "'<catalog><product id=\\\"P001\\\"><name>产品A</name><price currency=\\\"CNY\\\">99.9</price><specs><spec name=\\\"颜色\\\">红色</spec></specs><tags><tag>热销</tag></tags></product></catalog>'", "expected": "[{'id': 'P001', 'name': '产品A', 'price': 99.9, 'currency': 'CNY', 'specs': {'颜色': '红色'}, 'tags': ['热销']}]"}, {"input": "'<catalog><product id=\\\"P002\\\"><name>产品B</name><price currency=\\\"USD\\\">49.99</price></product></catalog>'", "expected": "[{'id': 'P002', 'name': '产品B', 'price': 49.99, 'currency': 'USD', 'specs': {}, 'tags': []}]"}, {"input": "'<catalog><product id=\\\"P003\\\"><name>产品C</name></product><product id=\\\"P004\\\"><name>产品D</name></product></catalog>'", "expected": "[{'id': 'P003', 'name': '产品C', 'price': None, 'currency': None, 'specs': {}, 'tags': []}, {'id': 'P004', 'name': '产品D', 'price': None, 'currency': None, 'specs': {}, 'tags': []}]"}, {"input": "'<catalog></catalog>'", "expected": "[]"}, {"input": "'invalid xml'", "expected": "[]"}, {"input": "'<catalog><product id=\\\"P005\\\"><name>产品E</name><price currency=\\\"EUR\\\">199</price><specs><spec name=\\\"尺寸\\\">大</spec><spec name=\\\"重量\\\">500g</spec></specs><tags><tag>新品</tag><tag>推荐</tag></tags></product></catalog>'", "expected": "[{'id': 'P005', 'name': '产品E', 'price': 199.0, 'currency': 'EUR', 'specs': {'尺寸': '大', '重量': '500g'}, 'tags': ['新品', '推荐']}]"}]}], "baseline_code": "import json\nimport xml.etree.ElementTree as ET\n\n\ndef parse_nested_json(json_str, path):\n    \"\"\"\n    解析嵌套 JSON 字符串并按路径提取值\n\n    参数:\n        json_str: JSON 格式的字符串\n        path: 点分隔的路径字符串，如 'data.user.name'\n\n    返回:\n        路径对应的值，如果路径不存在或 JSON 无效则返回 None\n    \"\"\"\n    pass\n\n\ndef parse_product_xml(xml_str):\n    \"\"\"\n    解析产品目录 XML，提取所有产品的关键信息\n\n    参数:\n        xml_str: XML 格式的字符串\n\n    返回:\n        包含字典的列表，每个字典包含:\n        - id: 产品ID\n        - name: 产品名称\n        - price: 价格（浮点数）\n        - currency: 货币单位\n        - specs: 规格字典\n        - tags: 标签列表\n    \"\"\"\n    pass\n", "test_cases": [{"id": 1, "hidden": false, "input": "'{\\\"data\\\":{\\\"user\\\":{\\\"name\\\":\\\"张三\\\"}}}', 'data.user.name'", "expected": "'张三'"}, {"id": 2, "hidden": false, "input": "'{\\\"data\\\":{\\\"items\\\":[\\\"a\\\",\\\"b\\\",\\\"c\\\"]}}', 'data.items.1'", "expected": "'b'"}, {"id": 3, "hidden": true, "input": "'{\\\"name\\\":\\\"test\\\"}', 'name'", "expected": "'test'"}, {"id": 4, "hidden": true, "input": "'{\\\"a\\\":{\\\"b\\\":{\\\"c\\\":1}}}', 'a.x.c'", "expected": "null"}, {"id": 5, "hidden": true, "input": "'invalid json', 'data'", "expected": "null"}, {"id": 6, "hidden": true, "input": "'{\\\"data\\\":{\\\"list\\\":[{\\\"id\\\":1},{\\\"id\\\":2}]}}', 'data.list.1.id'", "expected": "2"}, {"id": 7, "hidden": true, "input": "'<catalog><product id=\\\"P001\\\"><name>产品A</name><price currency=\\\"CNY\\\">99.9</price></product></catalog>'", "expected": "[{'id': 'P001', 'name': '产品A', 'price': 99.9, 'currency': 'CNY', 'specs': {}, 'tags': []}]"}, {"id": 8, "hidden": true, "input": "'<catalog></catalog>'", "expected": "[]"}]}$dc7$,
    NOW(),
    NOW()
  );

  SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 7;

  INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
  VALUES
    (new_task_id, '1', $dc7$"'{\\\"data\\\":{\\\"user\\\":{\\\"name\\\":\\\"张三\\\"}}}', 'data.user.name'"$dc7$, $dc7$"'张三'"$dc7$, False, '', 'CONTAINS', 1),
    (new_task_id, '2', $dc7$"'{\\\"data\\\":{\\\"items\\\":[\\\"a\\\",\\\"b\\\",\\\"c\\\"]}}', 'data.items.1'"$dc7$, $dc7$"'b'"$dc7$, False, '', 'CONTAINS', 2),
    (new_task_id, '3', $dc7$"'{\\\"name\\\":\\\"test\\\"}', 'name'"$dc7$, $dc7$"'test'"$dc7$, True, '', 'CONTAINS', 3),
    (new_task_id, '4', $dc7$"'{\\\"a\\\":{\\\"b\\\":{\\\"c\\\":1}}}', 'a.x.c'"$dc7$, $dc7$"null"$dc7$, True, '', 'CONTAINS', 4),
    (new_task_id, '5', $dc7$"'invalid json', 'data'"$dc7$, $dc7$"null"$dc7$, True, '', 'CONTAINS', 5),
    (new_task_id, '6', $dc7$"'{\\\"data\\\":{\\\"list\\\":[{\\\"id\\\":1},{\\\"id\\\":2}]}}', 'data.list.1.id'"$dc7$, $dc7$"2"$dc7$, True, '', 'CONTAINS', 6),
    (new_task_id, '7', $dc7$"'<catalog><product id=\\\"P001\\\"><name>产品A</name><price currency=\\\"CNY\\\">99.9</price></product></catalog>'"$dc7$, $dc7$"[{'id': 'P001', 'name': '产品A', 'price': 99.9, 'currency': 'CNY', 'specs': {}, 'tags': []}]"$dc7$, True, '', 'CONTAINS', 7),
    (new_task_id, '8', $dc7$"'<catalog></catalog>'"$dc7$, $dc7$"[]"$dc7$, True, '', 'CONTAINS', 8),
    (new_task_id, 'tc_9', $dc7$"'{\\\"data\\\":{\\\"user\\\":{\\\"name\\\":\\\"张三\\\"}}}', 'data.user.name'"$dc7$, $dc7$"'张三'"$dc7$, False, '', 'CONTAINS', 9),
    (new_task_id, 'tc_10', $dc7$"'{\\\"data\\\":{\\\"items\\\":[\\\"a\\\",\\\"b\\\",\\\"c\\\"]}}', 'data.items.1'"$dc7$, $dc7$"'b'"$dc7$, False, '', 'CONTAINS', 10),
    (new_task_id, 'tc_11', $dc7$"'{\\\"name\\\":\\\"test\\\"}', 'name'"$dc7$, $dc7$"'test'"$dc7$, False, '', 'CONTAINS', 11),
    (new_task_id, 'tc_12', $dc7$"'{\\\"a\\\":{\\\"b\\\":{\\\"c\\\":1}}}', 'a.x.c'"$dc7$, $dc7$"null"$dc7$, False, '', 'CONTAINS', 12),
    (new_task_id, 'tc_13', $dc7$"'invalid json', 'data'"$dc7$, $dc7$"null"$dc7$, False, '', 'CONTAINS', 13),
    (new_task_id, 'tc_14', $dc7$"'{\\\"data\\\":{\\\"list\\\":[{\\\"id\\\":1},{\\\"id\\\":2}]}}', 'data.list.1.id'"$dc7$, $dc7$"2"$dc7$, False, '', 'CONTAINS', 14),
    (new_task_id, 'tc_15', $dc7$"'<catalog><product id=\\\"P001\\\"><name>产品A</name><price currency=\\\"CNY\\\">99.9</price><specs><spec name=\\\"颜色\\\">红色</spec></specs><tags><tag>热销</tag></tags></product></catalog>'"$dc7$, $dc7$"[{'id': 'P001', 'name': '产品A', 'price': 99.9, 'currency': 'CNY', 'specs': {'颜色': '红色'}, 'tags': ['热销']}]"$dc7$, False, '', 'CONTAINS', 15),
    (new_task_id, 'tc_16', $dc7$"'<catalog><product id=\\\"P002\\\"><name>产品B</name><price currency=\\\"USD\\\">49.99</price></product></catalog>'"$dc7$, $dc7$"[{'id': 'P002', 'name': '产品B', 'price': 49.99, 'currency': 'USD', 'specs': {}, 'tags': []}]"$dc7$, False, '', 'CONTAINS', 16),
    (new_task_id, 'tc_17', $dc7$"'<catalog><product id=\\\"P003\\\"><name>产品C</name></product><product id=\\\"P004\\\"><name>产品D</name></product></catalog>'"$dc7$, $dc7$"[{'id': 'P003', 'name': '产品C', 'price': None, 'currency': None, 'specs': {}, 'tags': []}, {'id': 'P004', 'name': '产品D', 'price': None, 'currency': None, 'specs': {}, 'tags': []}]"$dc7$, False, '', 'CONTAINS', 17),
    (new_task_id, 'tc_18', $dc7$"'<catalog></catalog>'"$dc7$, $dc7$"[]"$dc7$, False, '', 'CONTAINS', 18),
    (new_task_id, 'tc_19', $dc7$"'invalid xml'"$dc7$, $dc7$"[]"$dc7$, False, '', 'CONTAINS', 19),
    (new_task_id, 'tc_20', $dc7$"'<catalog><product id=\\\"P005\\\"><name>产品E</name><price currency=\\\"EUR\\\">199</price><specs><spec name=\\\"尺寸\\\">大</spec><spec name=\\\"重量\\\">500g</spec></specs><tags><tag>新品</tag><tag>推荐</tag></tags></product></catalog>'"$dc7$, $dc7$"[{'id': 'P005', 'name': '产品E', 'price': 199.0, 'currency': 'EUR', 'specs': {'尺寸': '大', '重量': '500g'}, 'tags': ['新品', '推荐']}]"$dc7$, False, '', 'CONTAINS', 20);
END $$;