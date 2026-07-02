#!/usr/bin/env python3
"""Generate DC09 and DC10 handbook JSON from YAML configs."""
import json, yaml, os

os.chdir('/Users/jimfu/Work/huixue')

# ─── DC09: 日志格式解析与采集 ───────────────────────────────
with open('stage_dc09.yaml') as f:
    cfg9 = yaml.safe_load(f)

handbook9 = f"""# {cfg9['title']}

## 课程目标
"""
for obj in cfg9['learning_objectives']:
    handbook9 += f"- {obj}\n"
handbook9 += "\n---\n\n"

for ch in cfg9['chapters']:
    handbook9 += f"## {ch['title']}\n\n{ch['content']}\n\n"

handbook9 += """
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
"""

data9 = {
    'name': cfg9['name'],
    'title': cfg9['title'],
    'order_in_practice': cfg9['order_in_practice'],
    'difficulty': cfg9['difficulty'],
    'content': handbook9,
    'word_count': len(handbook9.split()),
    'char_count': len(handbook9)
}
with open('output/stage_dc09_handbook.json', 'w', encoding='utf-8') as f:
    json.dump(data9, f, ensure_ascii=False, indent=2)
print(f"DC09: {data9['char_count']} chars, {data9['word_count']} words")

# ─── DC10: 数据质量检查 ─────────────────────────────────────
with open('stage_dc10.yaml') as f:
    cfg10 = yaml.safe_load(f)

handbook10 = f"""# {cfg10['title']}

## 课程目标
"""
for obj in cfg10['learning_objectives']:
    handbook10 += f"- {obj}\n"
handbook10 += "\n---\n\n"

for ch in cfg10['chapters']:
    handbook10 += f"## {ch['title']}\n\n{ch['content']}\n\n"

handbook10 += """
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
"""

data10 = {
    'name': cfg10['name'],
    'title': cfg10['title'],
    'order_in_practice': cfg10['order_in_practice'],
    'difficulty': cfg10['difficulty'],
    'content': handbook10,
    'word_count': len(handbook10.split()),
    'char_count': len(handbook10)
}
with open('output/stage_dc10_handbook.json', 'w', encoding='utf-8') as f:
    json.dump(data10, f, ensure_ascii=False, indent=2)
print(f"DC10: {data10['char_count']} chars, {data10['word_count']} words")
print("Done.")
