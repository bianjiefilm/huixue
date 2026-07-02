#!/usr/bin/env python3
"""Generate MJ01 SQL insert for school DB."""
import json, os, sys
os.chdir('/Users/jimfu/Work/huixue')
sys.path.insert(0, '/Users/jimfu/Work/huixue')
import yaml

with open('stage_mj01.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f)

chapters = data.get('chapters', [])
content = '\n\n'.join(f"## {ch['title']}\n\n{ch['content']}" for ch in chapters)

questions = [
    {"id": "q1-1", "type": "concept", "difficulty": "easy",
     "question": "CRISP-DM 流程中，哪个阶段负责明确业务目标和评估资源？",
     "hint": "流程的第一步。",
     "options": ["A. 数据理解", "B. 业务理解", "C. 数据准备", "D. 建模"],
     "answer": "B",
     "explanation": "业务理解(Business Understanding)是CRISP-DM的第一步，负责明确业务目标、确定挖掘目标和评估资源。"},
    {"id": "q1-2", "type": "concept", "difficulty": "easy",
     "question": "scikit-learn 建模流程中，哪个方法负责对数据进行预测？",
     "hint": "预测方法。",
     "options": ["A. fit()", "B. predict()", "C. transform()", "D. score()"],
     "answer": "B",
     "explanation": "predict()方法用训练好的模型对数据进行预测，fit()负责训练，transform()负责转换特征，score()返回模型评估得分。"},
    {"id": "q1-3", "type": "calculation", "difficulty": "medium",
     "question": "某模型训练集准确率 0.99，测试集准确率 0.60，gap 是多少？是否过拟合？",
     "hint": "gap = 训练 - 测试。",
     "options": ["A. gap=0.39，过拟合", "B. gap=0.39，欠拟合", "C. gap=1.59，过拟合", "D. gap=0.39，正常"],
     "answer": "A",
     "explanation": "gap = 0.99 - 0.60 = 0.39，训练远高于测试，是典型的过拟合现象。"},
    {"id": "q1-4", "type": "coding", "difficulty": "medium",
     "question": "请实现 evaluate_classifier(y_true, y_pred) 函数，返回准确率/精确率/召回率/F1。",
     "options": None, "answer": None, "explanation": None},
]

q_data = json.dumps({"questions": questions}, ensure_ascii=False)

test_cases = """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$CRISP-DM 6阶段$v$, $v$返回6个阶段名称$v$, false, $v$阶段列表$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$有标签的特征矩阵和标签向量$v$, $v$supervised$v$, false, $v$问题类型判断$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$准确率/精确率/召回率/F1$v$, $v$返回dict含4指标$v$, false, $v$评估指标$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$train=0.99, test=0.60$v$, $v$is_overfitting=true, gap=0.39$v$, true, $v$过拟合检测$v$, 'CONTAINS', 4);"""

sql = f"""-- ============================================================
-- MJ1: 数据挖掘概述与流程
-- practice_id=7, order_in_practice=1
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v${data['title']}$v$,
    'PRACTICE',
    1,
    $v$beginner$v$,
    $v${content}$v$,
    $v${q_data}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 1;
    {test_cases}
    RAISE NOTICE 'Inserted task tests for MJ1';
END $$;

COMMIT;
"""

with open('deploy/scripts/stage_mj01_insert.sql', 'w', encoding='utf-8') as f:
    f.write(sql)
print(f"Generated: {len(sql)} chars")
