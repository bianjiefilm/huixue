-- ============================================================
-- MJ11: 集成学习与模型融合
-- practice_id=7, order_in_practice=11
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$集成学习与模型融合$v$,
    'PRACTICE',
    11,
    $v$advanced$v$,
    $v$## Bagging 与随机森林

## 11.1 Bagging 原理

Bootstrap Aggregating: 对训练集有放回抽样,每个子集训练一个模型,结果投票/平均

核心效果: 降低方差,提高稳定性

随机森林 = Bagging + 特征子采样:
- 行抽样: 有放回抽样 (bootstrap=True)
- 列抽样: 每次分裂考虑 sqrt(d) 个特征

```python
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier
from sklearn.tree import DecisionTreeClassifier

# Bagging
bag = BaggingClassifier(
    estimator=DecisionTreeClassifier(max_depth=5),
    n_estimators=100,
    bootstrap=True, max_samples=0.8,
    random_state=42, n_jobs=-1
)
bag.fit(X_train, y_train)

# 随机森林(RandomForest, Bagging的特例)
rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
rf.fit(X_train, y_train)
```


## Boosting 与 GBDT

## 11.2 Boosting 原理

序列化训练: 每棵树学习前面所有树的残差/梯度,逐步减少偏差

```python
from sklearn.ensemble import GradientBoostingClassifier, AdaBoostClassifier

# AdaBoost: 对错误样本加权
ada = AdaBoostClassifier(
    n_estimators=100, learning_rate=1.0,
    random_state=42
)
ada.fit(X_train, y_train)

# GBDT: 梯度下降优化
gbdt = GradientBoostingClassifier(
    n_estimators=100,
    learning_rate=0.1,
    max_depth=5,
    subsample=0.8,
    random_state=42
)
gbdt.fit(X_train, y_train)
```


## Stacking 与 Voting

## 11.3 Stacking 多层融合

元学习器(meta-learner)对基础模型输出做二次学习:

```python
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier

base_models = [
    ('rf', RandomForestClassifier(n_estimators=100, random_state=42)),
    ('svc', SVC(probability=True, random_state=42)),
    ('knn', KNeighborsClassifier(n_neighbors=5)),
]

stacking = StackingClassifier(
    estimators=base_models,
    final_estimator=LogisticRegression(),
    cv=5,
    n_jobs=-1
)
stacking.fit(X_train, y_train)
y_pred = stacking.predict(X_test)
```

## 11.4 Voting 投票

```python
from sklearn.ensemble import VotingClassifier

voting = VotingClassifier(
    estimators=base_models,
    voting='soft',  # 'hard' 多数投票, 'soft' 概率加权
    n_jobs=-1
)
voting.fit(X_train, y_train)
```
$v$,
    $v${"questions": [{"id": "q11-1", "type": "concept", "difficulty": "easy", "question": "MJ11 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q11-2", "type": "concept", "difficulty": "easy", "question": "MJ11 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q11-3", "type": "calculation", "difficulty": "medium", "question": "MJ11 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q11-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ11 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 11;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$Bagging投票$v$, $v$返回投票结果$v$, false, $v$Bagging投票$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$加权Bagging投票$v$, $v$返回加权结果$v$, false, $v$加权投票$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$Stacking预测$v$, $v$返回元模型预测$v$, false, $v$Stacking$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$AdaBoost权重更新$v$, $v$返回更新后权重$v$, true, $v$权重更新$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ11';
END $$;

COMMIT;
