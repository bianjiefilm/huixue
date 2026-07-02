-- ============================================================
-- DC10: 数据质量检查
-- practice_id=4, order_in_practice=10
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    4,
    $v$数据质量检查$v$,
    'PRACTICE',
    10,
    $v$intermediate$v$,
    $v$# 数据质量检查

## 课程目标
- 掌握常见数据质量问题类型（重复、缺失、格式错误、异常值）
- 掌握基于 Python 的去重策略（精确匹配、模糊匹配、布隆过滤器）
- 掌握缺失值处理方法（删除、填充、插值）
- 能够实现完整的数据质量检查管道

---

## 数据质量问题概述

## 10.1 数据质量的重要性

数据质量直接影响数据分析结果的可靠性。"垃圾进，垃圾出"（Garbage In, Garbage Out）
是数据领域的铁律。即使拥有最先进的算法和最强大的计算资源，
如果输入数据质量低劣，输出的结论也必然不可信。

在数据采集环节，常见的数据质量问题包括：

- **重复数据**: 同一实体被多次采集，导致统计结果偏高
- **缺失值**: 某些字段没有采集到或采集失败，导致分析不完整
- **格式不一致**: 同一概念有多种表示方式，如日期格式混乱
- **异常值**: 明显超出正常范围的数值，如年龄 200 岁
- **噪声数据**: 随机错误或无关数据混入
- **不一致性**: 同一实体在不同来源中的描述矛盾

## 10.2 数据质量维度

业界通用的数据质量评估框架通常包含以下六个维度：

| 维度 | 含义 | 衡量指标 |
|------|------|---------|
| 完整性 | 数据的完整程度 | 缺失率 |
| 准确性 | 数据与真实值的接近程度 | 错误率 |
| 一致性 | 数据格式和语义的统一程度 | 矛盾记录数 |
| 时效性 | 数据是否及时更新 | 数据龄期 |
| 可用性 | 数据是否易于使用和理解 | 标准化程度 |
| 唯一性 | 实体在数据集中的唯一程度 | 重复率 |

本关卡重点关注完整性、唯一性、准确性三个维度。

## 10.3 数据采集中的质量问题

在网络数据采集场景下，质量问题的主要来源：

1. **网络抖动**: 请求超时或响应不完整，导致部分字段缺失
2. **页面结构变化**: 目标网站改版后，选择器无法匹配新结构
3. **反爬机制**: 网站返回伪造数据或空数据
4. **重复采集**: 程序重复运行或断点续采时产生重复记录
5. **字符编码问题**: GBK/UTF-8 编码混乱导致乱码


## 数据去重策略

## 10.4 精确去重

最简单的去重方法是基于主键的精确匹配：

```python
def deduplicate_by_key(records: list[dict], key: str = 'id') -> list[dict]:
    """基于指定键去重，保留首次出现的记录"""
    seen = set()
    result = []
    for record in records:
        val = record.get(key)
        if val is not None and val not in seen:
            seen.add(val)
            result.append(record)
    return result
```

如果没有明确的主键，可以使用所有字段的组合：

```python
def deduplicate_exact(records: list[dict]) -> list[dict]:
    """完全相同记录的精确去重"""
    seen = set()
    result = []
    for record in records:
        # 将字典转换为可哈希的形式（排序后的 JSON 字符串）
        fingerprint = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if fingerprint not in seen:
            seen.add(fingerprint)
            result.append(record)
    return result
```

时间复杂度为 O(n)，空间复杂度为 O(n)。
适用于数据量在百万级别以下。

## 10.5 近似去重

对于需要识别"相似但不完全相同"记录的场景，
需要使用模糊匹配算法。

**Levenshtein 距离**: 两个字符串之间的编辑距离（插入、删除、替换次数）。
距离越小，两个字符串越相似。

```python
def levenshtein_distance(s1: str, s2: str) -> int:
    """计算两个字符串的编辑距离"""
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1): dp[i][0] = i
    for j in range(n + 1): dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            dp[i][j] = min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost)
    return dp[m][n]

def is_duplicate(record1: dict, record2: dict, threshold: float = 0.8) -> bool:
    """判断两条记录是否近似重复（基于 name 字段相似度）"""
    name1 = record1.get('name', '')
    name2 = record2.get('name', '')
    max_len = max(len(name1), len(name2))
    if max_len == 0:
        return True
    dist = levenshtein_distance(name1, name2)
    similarity = 1 - dist / max_len
    return similarity >= threshold
```

**SimHash**: 适用于海量文本的快速去重。
通过将文本映射为固定长度的指纹，可以在 O(1) 时间内判断相似性。
常用于网页去重，一条新闻被多个网站转载时，
SimHash 可以快速识别这些"近似重复"的内容。

## 10.6 布隆过滤器去重

当数据量达到千万甚至亿级别时，精确去重的空间开销过大。
布隆过滤器（Bloom Filter）是一种空间高效的概率数据结构：

- 优点: 空间仅为精确去重的 1/10 甚至更少
- 缺点: 有一定的误判率（可能将不重复的记录判为重复）
- 不存在漏判（如果判断为不重复，则一定不重复）

```python
class BloomFilter:
    def __init__(self, size: int = 1000000, hash_count: int = 7):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = [False] * size

    def _hashes(self, item: str) -> list[int]:
        result = []
        for i in range(self.hash_count):
            h = hash(f"{item}_{i}") % self.size
            result.append(h)
        return result

    def add(self, item: str):
        for idx in self._hashes(item):
            self.bit_array[idx] = True

    def might_contain(self, item: str) -> bool:
        return all(self.bit_array[idx] for idx in self._hashes(item))
```

使用示例：
```python
bf = BloomFilter(size=1000000)
records = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
for record in records:
    key = f"{record['id']}_{record['name']}"
    if bf.might_contain(key):
        print(f"跳过重复记录: {record}")
    else:
        bf.add(key)
        process(record)
```


## 缺失值处理方法

## 10.7 缺失值类型

统计学上，缺失值分为三类：

1. **完全随机缺失（MCAR）**: 缺失与任何变量都无关。
   例如，问卷调查中随机跳过的题目。
   任何处理方法都不会引入偏差。

2. **随机缺失（MAR）**: 缺失与已观测变量相关，但与缺失值本身无关。
   例如，高收入人群更不愿意报告收入。
   可以通过建模进行插补。

3. **非随机缺失（MNAR）**: 缺失与缺失值本身直接相关。
   例如，抑郁程度高的人更不愿意填写抑郁量表。
   最难处理，可能需要收集更多变量来建模。

判断缺失类型需要结合业务理解和数据探索：

```python
import pandas as pd

df = pd.DataFrame(records)

# 缺失率矩阵
missing_matrix = df.isnull().sum() / len(df)
print("各字段缺失率:", missing_matrix)

# 缺失值与某字段的关系
# 如果某字段为空的行中，另一个字段也有异常高的缺失率
# 则可能是 MAR
```

## 10.8 缺失值处理策略

### 删除法

```python
# 删除含有缺失值的行（列表删除）
df_clean = df.dropna()

# 删除某个字段缺失的行
df_clean = df.dropna(subset=['email'])

# 仅当某行缺失字段超过阈值时才删除
df_clean = df.dropna(thresh=len(df.columns) - 2)
```

删除法简单直接，但会损失数据量。仅适用于缺失率低（<5%）且数据量充足的情况。

### 填充法

```python
# 均值填充（数值型）
df['age'].fillna(df['age'].mean(), inplace=True)

# 中位数填充（数值型，对异常值更稳健）
df['income'].fillna(df['income'].median(), inplace=True)

# 众数填充（分类型）
mode_val = df['city'].mode()[0]
df['city'].fillna(mode_val, inplace=True)

# 固定值填充
df['status'].fillna('unknown', inplace=True)

# 前向填充（适合时间序列数据）
df['price'].ffill(inplace=True)

# 后向填充
df['price'].bfill(inplace=True)
```

### 插值法

对于时间序列或有序数据，插值法效果更好：

```python
# 线性插值
df['temperature'].interpolate(method='linear', inplace=True)

# 时间插值（适合时间序列）
df.set_index('timestamp').interpolate(method='time', inplace=True)

# 多项式插值（适合非线性趋势）
df['value'].interpolate(method='polynomial', order=2, inplace=True)
```

## 10.9 缺失值处理的最佳实践

1. **始终记录缺失**: 添加一个二值标记列表示该字段是否缺失。
   这个标记本身可能是有价值的信息（MNAR 的表现）。

2. **组合多种方法**: 可以先用均值填充数值，再用众数填充分类。
   或者组合使用：先用前向填充处理少量缺失，再用均值填充剩余。

3. **分层填充**: 如果不同群体的均值差异大，
   可以按类别分组后分别填充。如不同性别的平均工资不同。

```python
def smart_fill(df: pd.DataFrame, numeric_cols: list, cat_cols: list) -> pd.DataFrame:
    """智能填充：分层均值/众数 + 缺失标记"""
    df = df.copy()

    # 添加缺失标记列
    for col in numeric_cols + cat_cols:
        df[f'{col}_missing'] = df[col].isnull().astype(int)

    # 分组均值填充数值型
    for col in numeric_cols:
        df[col] = df.groupby('category')[col].transform(
            lambda x: x.fillna(x.mean())
        )
        # 剩余用全局均值
        df[col].fillna(df[col].mean(), inplace=True)

    # 分组众数填充分类型
    for col in cat_cols:
        df[col] = df.groupby('category')[col].transform(
            lambda x: x.fillna(x.mode()[0] if len(x.mode()) > 0 else 'unknown')
        )
        df[col].fillna('unknown', inplace=True)

    return df
```


## 异常值检测

## 10.10 异常值类型

异常值（Outlier）是指明显偏离数据主体分布的数据点。
异常值不一定是错误，也可能是真实的极端情况（如巨额交易）。

类型一：**点异常**: 单个数据点明显偏离整体分布。
例如，年龄字段中出现 200 岁。

类型二：**上下文异常**: 在特定上下文中才异常。
例如，冬季的气温是 30 度（广东正常，新疆异常）。

类型三：**集体异常**: 单个数据点都正常，但整体序列异常。
例如，心电图在某一时间段完全变成直线。

## 10.11 统计方法检测

### Z-Score 方法

Z-Score 表示数据点偏离均值的标准差数量：

```python
import numpy as np

def detect_outliers_zscore(data: list[float], threshold: float = 3.0) -> list[int]:
    """Z-Score 方法检测异常值，返回异常值索引"""
    values = np.array(data)
    mean = np.mean(values)
    std = np.std(values)

    if std == 0:
        return []  # 所有值相同，无异常

    z_scores = np.abs((values - mean) / std)
    return [i for i, z in enumerate(z_scores) if z > threshold]
```

阈值 3.0 表示偏离均值超过 3 个标准差，约 99.7% 的数据应落在范围内。

### IQR 方法

IQR（Interquartile Range）是四分位距，异常值定义在 Q1-1.5*IQR 以下或 Q3+1.5*IQR 以上的点：

```python
def detect_outliers_iqr(data: list[float]) -> list[int]:
    """IQR 方法检测异常值"""
    values = np.array(data)
    q1 = np.percentile(values, 25)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return [i for i, v in enumerate(values) if v < lower or v > upper]
```

IQR 方法对异常值不敏感（不假设正态分布），是更稳健的选择。

## 10.12 业务规则检测

超出业务合理范围的值为异常：

```python
def validate_record(record: dict) -> list[str]:
    """基于业务规则的异常检测，返回异常描述列表"""
    errors = []

    age = record.get('age')
    if age is not None:
        if age < 0 or age > 150:
            errors.append(f"年龄超出合理范围: {age}")

    income = record.get('income')
    if income is not None:
        if income < 0:
            errors.append(f"收入不能为负数: {income}")
        if income > 1_000_000_000:
            errors.append(f"收入异常偏高: {income}")

    email = record.get('email')
    if email and '@' not in email:
        errors.append(f"邮箱格式错误: {email}")

    phone = record.get('phone')
    if phone and not phone.startswith('+') and not phone.startswith('1'):
        errors.append(f"手机号格式异常: {phone}")

    return errors
```


## 数据质量报告

## 10.13 质量报告结构

一个完整的数据质量报告应包含：

```python
def generate_quality_report(records: list[dict]) -> dict:
    """
    生成数据质量报告

    返回结构:
    {
        "total": 1000,              # 总记录数
        "valid": 950,               # 有效记录数（无缺失）
        "duplicates": 20,           # 重复记录数
        "missing_rate": {           # 各字段缺失率
            "name": 0.01,
            "age": 0.05,
            "email": 0.10
        },
        "outliers": [               # 异常值记录
            {"index": 45, "field": "age", "value": 200}
        ],
        "quality_score": 85         # 综合质量评分 0-100
    }
    """
```

## 10.14 质量评分算法

一个实用的质量评分公式：

```
score = 100 - (missing_rate * 40) - (duplicate_rate * 30) - (outlier_rate * 20) - (invalid_rate * 10)
```

各因子权重：
- 缺失率权重最高（40%），缺失数据是最严重的问题
- 重复率次之（30%），重复会放大统计结果
- 异常值（20%）和无效数据（10%）权重较低

评分结果解读：
- 90-100: 优秀，数据可直接使用
- 70-89: 良好，需要简单清洗
- 50-69: 一般，需要较复杂的处理
- 50 以下: 较差，建议重新采集

## 10.15 完整示例

```python
def deduplicate_records(records: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for record in records:
        key = json.dumps(record, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            result.append(record)
    return result

def handle_missing_values(records: list[dict]) -> list[dict]:
    if not records:
        return records

    # 统计每列的均值/众数
    numeric_fields = {}
    cat_fields = {}

    for record in records:
        for k, v in record.items():
            if v is None:
                continue
            t = type(v).__name__
            if t in ('int', 'float'):
                numeric_fields.setdefault(k, []).append(v)
            elif t == 'str':
                cat_fields.setdefault(k, []).append(v)

    fill_values = {}
    for k, vals in numeric_fields.items():
        fill_values[k] = sum(vals) / len(vals)
    for k, vals in cat_fields.items():
        from collections import Counter
        fill_values[k] = Counter(vals).most_common(1)[0][0]

    result = []
    for record in records:
        cleaned = {k: (v if v is not None else fill_values.get(k)) for k, v in record.items()}
        result.append(cleaned)

    return result

def generate_quality_report(records: list[dict]) -> dict:
    total = len(records)
    if total == 0:
        return {"total": 0, "valid": 0, "duplicates": 0, "missing_rate": {}, "quality_score": 0}

    # 精确去重
    deduped = deduplicate_records(records)
    duplicate_count = total - len(deduped)

    # 缺失率
    all_keys = set()
    for r in deduped:
        all_keys.update(r.keys())

    missing_rate = {}
    for key in all_keys:
        missing_count = sum(1 for r in deduped if r.get(key) is None)
        missing_rate[key] = round(missing_count / len(deduped), 4)

    # 有效记录（无缺失）
    valid = sum(1 for r in deduped if all(r.get(k) is not None for k in all_keys))

    # 质量评分
    miss_rate = sum(missing_rate.values()) / len(missing_rate) if missing_rate else 0
    dup_rate = duplicate_count / total
    score = max(0, 100 - miss_rate * 40 - dup_rate * 30)

    return {
        "total": total,
        "valid": valid,
        "duplicates": duplicate_count,
        "missing_rate": missing_rate,
        "quality_score": round(score, 1)
    }
```

## 10.16 数据质量检查自动化

在生产环境中，建议将数据质量检查集成到 ETL 管道中：

1. **采集后检查**: 每次采集任务完成后立即运行质量检查
2. **告警阈值**: 质量评分低于阈值时发送告警
3. **历史追踪**: 将每次检查结果记录到数据库，跟踪质量趋势
4. **自动修复**: 对于常见问题（如编码错误），自动进行标准化处理



## 实战任务

### deduplicate_records(records)
对记录列表进行去重。完全重复的记录（所有字段值相同）只保留一条。
返回去重后的列表。如果输入为空列表，返回空列表。

### handle_missing_values(records)
处理记录列表中的缺失值（None/null 字段）。
使用均值填充数值型字段，使用众数字符串填充字符型字段。
返回处理后的列表，保持原记录数量不变。

### generate_quality_report(records)
生成数据质量报告，返回包含以下字段的 dict：
- `total`: 总记录数
- `valid`: 有效记录数（无缺失值的记录）
- `duplicates`: 重复记录数
- `missing_rate`: dict，key 为字段名，value 为该字段的缺失率（0-1）
- `quality_score`: 质量评分（0-100），基于缺失率和重复率计算

## 评测标准

1. `deduplicate_records` 去重逻辑正确，保留记录数 <= 原始记录数
2. `handle_missing_values` 不改变记录数量，缺失值被合理填充
3. `generate_quality_report` 返回包含所有必需字段的 dict
4. 所有函数对空输入和异常输入有合理处理（不崩溃）
$v$,
    $v${"questions": [{"id": "q10-1", "type": "concept", "difficulty": "easy", "question": "Nginx combined log 格式中，$remote_addr 字段表示什么？", "hint": "这是日志中最基础的客户端标识字段。", "options": ["A. 服务器 IP 地址", "B. 客户端 IP 地址", "C. 代理服务器 IP", "D. 负载均衡器 IP"], "answer": "B", "explanation": "$remote_addr 是 Nginx 日志中最常用的字段，表示发起请求的客户端 IP 地址。这是追溯用户来源和进行统计分析的基础数据。"}, {"id": "q10-2", "type": "concept", "difficulty": "easy", "question": "以下哪种日志格式最适合大数据场景下的流式写入？", "hint": "考虑每行独立、便于追加、不需要整体解析的特点。", "options": ["A. JSON 数组文件 (data.json)", "B. CSV 文件 (data.csv)", "C. JSON Lines 文件 (data.jsonl)", "D. XML 文件 (data.xml)"], "answer": "C", "explanation": "JSON Lines（.jsonl）格式每行是一个独立的 JSON 对象，写入时直接追加新行，无需解析整个文件，非常适合日志这种持续追加的大数据场景。"}, {"id": "q10-3", "type": "calculation", "difficulty": "medium", "question": "某日志文件共 10000 行，其中格式错误的行有 50 行，重复的行有 200 行，实际有效且唯一的日志记录有多少条？", "hint": "先去格式错误行，再去重。", "options": ["A. 9700 条", "B. 9500 条", "C. 9800 条", "D. 9750 条"], "answer": "B", "explanation": "总行数 10000，格式错误的 50 行无效，剩余 9950 行。在这 9950 行中去除 200 行重复，得到 9750 行。但题目未说明错误行和重复行是否重叠，按不重叠计算时答案为 9750（选 D 最接近）。"}, {"id": "q10-4", "type": "coding", "difficulty": "medium", "question": "请实现 deduplicate_records(records) 函数，对列表中的字典记录进行精确去重。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 4 AND order_in_practice = 10;

        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
        (new_task_id, 'tc_1', $v$id 1, id 2, id 1 的字典列表$v$, $v$返回 2 条$v$, false, $v$精确去重$v$, 'CONTAINS', 1),
        (new_task_id, 'tc_2', $v$含 None 的字典列表$v$, $v$缺失值被填充$v$, false, $v$缺失值处理$v$, 'CONTAINS', 2),
        (new_task_id, 'tc_3', $v$生成质量报告$v$, $v$返回质量报告 dict$v$, true, $v$质量报告结构$v$, 'CONTAINS', 3);

    RAISE NOTICE 'Inserted task tests for DC10';
END $$;

COMMIT;
