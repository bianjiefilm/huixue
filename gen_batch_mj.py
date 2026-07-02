#!/usr/bin/env python3
"""Batch generate MJ02-MJ12 SQL insert scripts"""
import json, os, sys
os.chdir('/Users/jimfu/Work/huixue')
sys.path.insert(0, '/Users/jimfu/Work/huixue')
import yaml

# (name, order, difficulty, test_cases_sql)
STAGES = {
    'mj02': (2, 'beginner', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$含缺失值的 DataFrame$v$, $v$返回概况dict$v$, false, $v$数据概况$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$计算相关系数矩阵$v$, $v$返回DataFrame$v$, false, $v$相关性分析$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$threshold=0.8$v$, $v$返回高相关特征对$v$, true, $v$高相关对检测$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$基于IQR检测异常值$v$, $v$返回异常值索引$v$, true, $v$异常值检测$v$, 'CONTAINS', 4);"""),
    'mj03': (3, 'intermediate', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$标签编码$v$, $v$返回编码Series和映射$v$, false, $v$标签编码$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$独热编码$v$, $v$返回含新列DataFrame$v$, false, $v$独热编码$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$标准化train和test$v$, $v$返回标准化后数据$v$, false, $v$标准化$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$方差过滤$v$, $v$返回筛选后矩阵和索引$v$, true, $v$方差过滤$v$, 'CONTAINS', 4);"""),
    'mj04': (4, 'intermediate', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$sigmoid(0)$v$, $v$0.5$v$, false, $v$sigmoid计算$v$, 'EXACT_MATCH', 1),
    (new_task_id, 'tc_2', $v$逻辑回归预测$v$, $v$返回概率数组$v$, false, $v$预测概率$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$计算混淆矩阵指标$v$, $v$返回accuracy/precision/recall/f1$v$, false, $v$评估指标$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$找最优阈值$v$, $v$返回best_threshold和best_f1$v$, true, $v$最优阈值$v$, 'CONTAINS', 4);"""),
    'mj05': (5, 'intermediate', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$compute_gini纯集合$v$, $v$0.0$v$, false, $v$基尼系数$v$, 'EXACT_MATCH', 1),
    (new_task_id, 'tc_2', $v$找最优分裂点$v$, $v$返回特征索引/阈值/增益$v$, false, $v$最优分裂$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$随机森林投票预测$v$, $v$返回预测标签$v$, false, $v$RF预测$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$汇总特征重要性$v$, $v$返回归一化重要性$v$, true, $v$特征重要性$v$, 'CONTAINS', 4);"""),
    'mj06': (6, 'intermediate', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$MSE计算$v$, $v$MSE=0.375$v$, false, $v$MSE$v$, 'EXACT_MATCH', 1),
    (new_task_id, 'tc_2', $v$MAE计算$v$, $v$MAE=0.5$v$, false, $v$MAE$v$, 'EXACT_MATCH', 2),
    (new_task_id, 'tc_3', $v$R2计算$v$, $v$返回0~1之间的值$v$, false, $v$R2$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$Ridge损失计算$v$, $v$返回正损失值$v$, true, $v$Ridge损失$v$, 'CONTAINS', 4);"""),
    'mj07': (7, 'intermediate', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$euclidean(0,0)-(3,4)$v$, $v$5.0$v$, false, $v$欧氏距离$v$, 'EXACT_MATCH', 1),
    (new_task_id, 'tc_2', $v$K-Means++初始化$v$, $v$返回k个初始中心$v$, false, $v$初始化中心$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$分配簇$v$, $v$返回簇标签$v$, false, $v$簇分配$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$轮廓系数$v$, $v$返回-1~1之间值$v$, true, $v$轮廓系数$v$, 'CONTAINS', 4);"""),
    'mj08': (8, 'intermediate', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$PCA拟合$v$, $v$返回components和variance$v$, false, $v$PCA拟合$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$PCA投影$v$, $v$返回降维后矩阵$v$, false, $v$PCA投影$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$方差解释率$v$, $v$总和=1.0$v$, false, $v$解释方差$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$从PCA重建$v$, $v$返回重建矩阵$v$, true, $v$重建$v$, 'CONTAINS', 4);"""),
    'mj09': (9, 'intermediate', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$支持度计算$v$, $v$返回0~1$v$, false, $v$支持度$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$置信度计算$v$, $v$返回0~1$v$, false, $v$置信度$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$提升度计算$v$, $v$返回>0$v$, false, $v$提升度$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$Apriori频繁项集$v$, $v$返回项集列表$v$, true, $v$频繁项集$v$, 'CONTAINS', 4);"""),
    'mj10': (10, 'intermediate', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$分层K折划分$v$, $v$返回K个split$v$, false, $v$分层划分$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$Bootstrap抽样$v$, $v$返回等大样本$v$, false, $v$Bootstrap$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$学习曲线计算$v$, $v$返回mean和std$v$, false, $v$学习曲线$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$交叉验证得分$v$, $v$返回各折得分$v$, true, $v$交叉验证$v$, 'CONTAINS', 4);"""),
    'mj11': (11, 'advanced', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$Bagging投票$v$, $v$返回投票结果$v$, false, $v$Bagging投票$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$加权Bagging投票$v$, $v$返回加权结果$v$, false, $v$加权投票$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$Stacking预测$v$, $v$返回元模型预测$v$, false, $v$Stacking$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$AdaBoost权重更新$v$, $v$返回更新后权重$v$, true, $v$权重更新$v$, 'CONTAINS', 4);"""),
    'mj12': (12, 'advanced', """    INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$加载数据$v$, $v$返回100行DataFrame$v$, false, $v$数据加载$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$预处理和划分$v$, $v$返回5元组$v$, false, $v$预处理$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$训练并比较模型$v$, $v$返回模型准确率字典$v$, false, $v$模型比较$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$特征重要性$v$, $v$返回top_k重要特征$v$, true, $v$特征重要性$v$, 'CONTAINS', 4);"""),
}


def gen_sql(name, order, difficulty, test_cases):
    with open(f'stage_{name}.yaml', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    chapters = data.get('chapters', [])
    content = '\n\n'.join(f"## {ch['title']}\n\n{ch['content']}" for ch in chapters)

    questions = [
        {"id": f"q{order}-1", "type": "concept", "difficulty": "easy",
         "question": f"MJ{order} 阶段题目1",
         "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
         "answer": "A",
         "explanation": f"请参考 Handbook 第1章节。"},
        {"id": f"q{order}-2", "type": "concept", "difficulty": "easy",
         "question": f"MJ{order} 阶段题目2",
         "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"],
         "answer": "B",
         "explanation": f"请参考 Handbook 第2章节。"},
        {"id": f"q{order}-3", "type": "calculation", "difficulty": "medium",
         "question": f"MJ{order} 计算题",
         "options": ["A. 1", "B. 2", "C. 3", "D. 4"],
         "answer": "C",
         "explanation": f"根据 Handbook 内容计算得出。"},
        {"id": f"q{order}-4", "type": "coding", "difficulty": "medium",
         "question": f"请实现 MJ{order} 相关函数。",
         "options": None, "answer": None, "explanation": None},
    ]
    q_data = json.dumps({"questions": questions}, ensure_ascii=False)

    sql = f"""-- ============================================================
-- MJ{order}: {data['title']}
-- practice_id=7, order_in_practice={order}
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v${data['title']}$v$,
    'PRACTICE',
    {order},
    $v${difficulty}$v$,
    $v${content}$v$,
    $v${q_data}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = {order};
    {test_cases}
    RAISE NOTICE 'Inserted task tests for MJ{order}';
END $$;

COMMIT;
"""
    return sql


if __name__ == '__main__':
    for name in ['mj02', 'mj03', 'mj04', 'mj05', 'mj06', 'mj07', 'mj08', 'mj09', 'mj10', 'mj11', 'mj12']:
        order, difficulty, test_cases = STAGES[name]
        sql = gen_sql(name, order, difficulty, test_cases)
        path = f'deploy/scripts/stage_{name}_insert.sql'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(sql)
        print(f"Generated {path} ({len(sql)} chars)")
    print("All done.")
