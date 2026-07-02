-- ============================================================
-- MJ5: 监督学习: 分类进阶
-- practice_id=7, order_in_practice=5
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$监督学习: 分类进阶$v$,
    'PRACTICE',
    5,
    $v$intermediate$v$,
    $v$## 支持向量机 SVM

## 5.1 SVM 原理

SVM 寻找最大间隔超平面分隔不同类别:

```python
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler

# SVM 对特征尺度敏感,需先标准化
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

svc = SVC(kernel='rbf', C=1.0, gamma='scale', probability=True, random_state=42)
svc.fit(X_train_s, y_train)
y_pred = svc.predict(X_test_s)
y_prob = svc.predict_proba(X_test_s)[:, 1]
```

核函数选择:
- `linear`: 线性可分,高维映射快
- `rbf` (默认): 非线性,效果好但慢
- `poly`: 多项式核


## 随机森林

## 5.2 随机森林原理

Bagging + 决策树: 多棵决策树并行训练,结果投票:

```python
from sklearn.ensemble import RandomForestClassifier

rf = RandomForestClassifier(
    n_estimators=100,     # 树的数量
    max_depth=10,         # 最大深度
    min_samples_split=5,
    min_samples_leaf=2,
    max_features='sqrt', # 分裂时考虑的最大特征数
    bootstrap=True,        # 有放回抽样
    random_state=42,
    n_jobs=-1             # 并行
)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)

# 特征重要性
importances = rf.feature_importances_
indices = np.argsort(importances)[::-1]
print("特征重要性排名:")
for i in range(X.shape[1]):
    print(f"  {i+1}. {feature_names[indices[i]]}: {importances[indices[i]]:.4f}")
```


## XGBoost 梯度提升

## 5.3 XGBoost 原理

序列化训练决策树,每棵树学习前面树的残差:

```python
import xgboost as xgb

xgb_clf = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    objective='binary:logistic',
    eval_metric='auc',
    use_label_encoder=False,
    random_state=42
)
xgb_clf.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
y_pred = xgb_clf.predict(X_test)
y_prob = xgb_clf.predict_proba(X_test)[:, 1]

# 特征重要性
xgb.plot_importance(xgb_clf, max_num_features=10)
plt.show()
```

## 5.4 主要超参数调优建议

| 参数 | 小数据 | 大数据 | 作用 |
|------|-------|-------|------|
| n_estimators | 100 | 300-500 | 树的数量,多可提高但增过拟合风险 |
| max_depth | 3-6 | 6-10 | 树深,控制复杂度 |
| learning_rate | 0.01-0.1 | 0.01-0.05 | 学习率,XGB需配合n_estimators |
| subsample | 0.8 | 0.7 | 行抽样比,防过拟合 |
| colsample_bytree | 0.8 | 0.6 | 列抽样比,增加多样性 |
$v$,
    $v${"questions": [{"id": "q5-1", "type": "concept", "difficulty": "easy", "question": "MJ5 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q5-2", "type": "concept", "difficulty": "easy", "question": "MJ5 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q5-3", "type": "calculation", "difficulty": "medium", "question": "MJ5 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q5-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ5 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 5;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$compute_gini纯集合$v$, $v$0.0$v$, false, $v$基尼系数$v$, 'EXACT_MATCH', 1),
    (new_task_id, 'tc_2', $v$找最优分裂点$v$, $v$返回特征索引/阈值/增益$v$, false, $v$最优分裂$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$随机森林投票预测$v$, $v$返回预测标签$v$, false, $v$RF预测$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$汇总特征重要性$v$, $v$返回归一化重要性$v$, true, $v$特征重要性$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ5';
END $$;

COMMIT;
