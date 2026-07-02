#!/usr/bin/env python3
"""生成 WX01 handbook JSON + SQL 插入脚本"""
import json, sys, os

os.chdir('/Users/jimfu/Work/huixue')
sys.path.insert(0, '/Users/jimfu/Work/huixue')

import yaml

def yaml_to_handbook(name):
    with open(f'stage_{name}.yaml', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    # 合并所有章节内容为单一日志
    chapters = data.get('chapters', [])
    content_parts = []
    for ch in chapters:
        content_parts.append(f"## {ch['title']}\n\n{ch['content']}")

    return {
        'title': data['title'],
        'content': '\n\n'.join(content_parts),
        'description': data.get('description', ''),
        'learning_objectives': data.get('learning_objectives', []),
        'handbook_word_count': data.get('handbook_word_count', 0),
    }

def gen_handbook_json(name):
    d = yaml_to_handbook(name)
    with open(f'output/stage_{name}_handbook.json', 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    return d

def gen_sql(name, order):
    d = gen_handbook_json(name)
    title = d['title']
    content = d['content']

    questions = [
        {"id": "q" + str(order) + "-1", "type": "concept", "difficulty": "easy",
         "question": "在数据清洗全流程中,缺失值处理通常在哪一步之后进行?",
         "hint": "先识别问题再处理。",
         "options": ["A. 去重之后", "B. 格式规范化之后", "C. 去重之前", "D. 异常值检测之后"],
         "answer": "C",
         "explanation": "缺失值检测和处理是数据清洗的第一步,先了解缺失情况再决定去重策略,因为重复记录可能包含大量缺失值。"},
        {"id": "q" + str(order) + "-2", "type": "concept", "difficulty": "easy",
         "question": "某字段缺失率超过多少时,通常需要特殊处理而非简单填充?",
         "hint": "经验法则。",
         "options": ["A. 1%", "B. 5%", "C. 20%", "D. 50%"],
         "answer": "D",
         "explanation": "业界经验:缺失率超过50%的字段,通常建议删除该列而非填充,因为填充会引入过多噪声,失去该字段的统计意义。"},
        {"id": "q" + str(order) + "-3", "type": "calculation", "difficulty": "medium",
         "question": "某数据集 10000 行,某一列有 300 行缺失,另一列有 200 行缺失(无重叠),总缺失记录有多少行?",
         "hint": "注意题目说的是'总缺失记录'。",
         "options": ["A. 300 行", "B. 500 行", "C. 200 行", "D. 条件不足,无法确定"],
         "answer": "D",
         "explanation": "题目未说明两列的缺失行是否重叠,因此无法确定总缺失行数。这是数据质量探索的重要性——需要实际统计,不能简单相加。"},
        {"id": "q" + str(order) + "-4", "type": "coding", "difficulty": "medium",
         "question": "请实现 detect_missing_values(df) 函数,返回 DataFrame 各列缺失率字典。",
         "options": None,
         "answer": None,
         "explanation": None},
    ]

    q_data = json.dumps({"questions": questions}, ensure_ascii=False)

    test_cases = """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$含缺失值的 DataFrame$v$, $v$返回缺失率字典$v$, false, $v$缺失值检测$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$有重复行的 DataFrame$v$, $v$去重后行数减少$v$, false, $v$去重功能$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$手机号 138-1234-5678$v$, $v$13812345678$v$, false, $v$手机号规范化$v$, 'EXACT_MATCH', 3),
    (new_task_id, 'tc_4', $v$生成质量报告$v$, $v$含 total_rows/duplicate_rows 字段$v$, true, $v$质量报告结构$v$, 'CONTAINS', 4);"""

    sql = """-- ============================================================
-- WX%(order)d: %(title)s
-- practice_id=5, order_in_practice=%(order)d
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    5,
    $v$%(title)s$v$,
    'PRACTICE',
    %(order)d,
    $v$beginner$v$,
    $v$%(content)s$v$,
    $v$%(q_data)s$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 5 AND order_in_practice = %(order)d;

    %(test_cases)s

    RAISE NOTICE 'Inserted task tests for WX%(order)d';
END $$;

COMMIT;
""" % {
        'order': order,
        'title': title,
        'content': content,
        'q_data': q_data,
        'test_cases': test_cases,
    }

    return sql

if __name__ == '__main__':
    name = 'wx01'
    d = gen_handbook_json(name)
    print(f"handbook generated: {len(d['content'])} chars, ~{d['handbook_word_count']} words")

    sql = gen_sql(name, 1)
    path = 'deploy/scripts/stage_wx01_insert.sql'
    with open(path, 'w', encoding='utf-8') as f:
        f.write(sql)
    print(f"SQL generated: {path} ({len(sql)} chars)")
    print("Done.")
