-- ============================================================
-- MJ12: 综合项目: 客户流失预测全流程
-- practice_id=7, order_in_practice=12
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$综合项目: 客户流失预测全流程$v$,
    'PRACTICE',
    12,
    $v$advanced$v$,
    $v$## 客户流失问题概述

## 12.1 业务背景

客户流失(Churn)是电信、银行、电商等行业的核心指标:
- 电信: 用户携号转网
- 银行: 客户关闭账户
- 电商: 用户超过N天未登录

数据集字段(模拟电信流失数据):
- customer_id: 客户ID
- tenure: 在网时长(月)
- contract_type: 合同类型(Month-to-month/1-year/2-year)
- monthly_charges: 月费用
- total_charges: 累计费用
- internet_service: 网络服务类型
- tech_support: 是否订阅技术支持
- churn: 是否流失(目标变量)


## 完整建模流程

## 12.2 全流程实现

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix

# 1. 数据加载
df = pd.read_csv('customer_churn.csv')

# 2. EDA
print(df.isnull().sum())
print(df['churn'].value_counts(normalize=True))

# 3. 预处理
le = LabelEncoder()
df['gender'] = le.fit_transform(df['gender'])
# ... 其他编码

X = df.drop('churn', axis=1)
y = df['churn']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# 4. 特征标准化
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

# 5. 多模型比较
models = {
    'LogisticRegression': LogisticRegression(max_iter=1000),
    'RandomForest': RandomForestClassifier(n_estimators=100),
    'GradientBoosting': GradientBoostingClassifier(n_estimators=100),
}
results = {}
for name, model in models.items():
    model.fit(X_train_s, y_train)
    y_prob = model.predict_proba(X_test_s)[:, 1]
    results[name] = roc_auc_score(y_test, y_prob)
best_model_name = max(results, key=results.get)
print(f"Best: {best_model_name} AUC={results[best_model_name]:.4f}")
```


## 模型优化与业务建议

## 12.3 GridSearch 调参

```python
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.05, 0.1, 0.2],
}
grid = GridSearchCV(
    GradientBoostingClassifier(random_state=42),
    param_grid, cv=5, scoring='roc_auc', n_jobs=-1
)
grid.fit(X_train_s, y_train)
print(f"Best params: {grid.best_params_}")
print(f"Best AUC: {grid.best_score_:.4f}")
best_model = grid.best_estimator_
```

## 12.4 业务建议

基于特征重要性给出可操作建议:

```python
# 特征重要性
importances = best_model.feature_importances_
feature_imp = pd.DataFrame({'feature': X.columns, 'importance': importances})
feature_imp = feature_imp.sort_values('importance', ascending=False)
print(feature_imp.head())

# 业务建议
# - tenure 重要性高 → 关注新客户,建立早期关怀机制
# - contract_type 重要 → 推广长期合约,减少月付用户流失风险
# - tech_support 重要 → 加强技术支持服务推广
```
$v$,
    $v${"questions": [{"id": "q12-1", "type": "concept", "difficulty": "easy", "question": "MJ12 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q12-2", "type": "concept", "difficulty": "easy", "question": "MJ12 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q12-3", "type": "calculation", "difficulty": "medium", "question": "MJ12 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q12-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ12 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 12;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$加载数据$v$, $v$返回100行DataFrame$v$, false, $v$数据加载$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$预处理和划分$v$, $v$返回5元组$v$, false, $v$预处理$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$训练并比较模型$v$, $v$返回模型准确率字典$v$, false, $v$模型比较$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$特征重要性$v$, $v$返回top_k重要特征$v$, true, $v$特征重要性$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ12';
END $$;

COMMIT;
