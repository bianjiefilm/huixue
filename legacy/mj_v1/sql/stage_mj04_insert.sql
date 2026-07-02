-- ============================================================
-- MJ4: 监督学习: 分类基础
-- practice_id=7, order_in_practice=4
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$监督学习: 分类基础$v$,
    'PRACTICE',
    4,
    $v$intermediate$v$,
    $v$## 逻辑回归

## 4.1 原理

逻辑回归使用 sigmoid 函数将线性组合映射到 [0,1]:

$P(y=1|x) = \\frac{1}{1 + e^{-z}}$, 其中 $z = w^Tx + b$

```python
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]  # 类别1的概率
```


## 决策树

## 4.2 决策树原理

决策树通过递归分裂最大化信息增益(Information Gain)或基尼系数(Gini):

```python
from sklearn.tree import DecisionTreeClassifier, plot_tree

clf = DecisionTreeClassifier(
    max_depth=5,        # 最大深度
    min_samples_split=10, # 分裂所需最小样本数
    min_samples_leaf=5,  # 叶节点最小样本数
    criterion='gini',     # 'gini' 或 'entropy'
    random_state=42
)
clf.fit(X_train, y_train)
y_pred = clf.predict(X_test)

# 可视化
import matplotlib.pyplot as plt
plt.figure(figsize=(20, 10))
plot_tree(clf, feature_names=feature_names, class_names=['No', 'Yes'], filled=True)
plt.title('Decision Tree')
plt.show()
```


## 模型评估

## 4.3 混淆矩阵与指标

```python
from sklearn.metrics import (
    confusion_matrix, accuracy_score, precision_score,
    recall_score, f1_score, roc_auc_score, classification_report
)

cm = confusion_matrix(y_test, y_pred)
print(cm)
# [[TN, FP], [FN, TP]]

print(f"准确率: {accuracy_score(y_test, y_pred):.4f}")
print(f"精确率: {precision_score(y_test, y_pred):.4f}")
print(f"召回率: {recall_score(y_test, y_pred):.4f}")
print(f"F1: {f1_score(y_test, y_pred):.4f}")
print(f"AUC: {roc_auc_score(y_test, y_prob):.4f}")

print(classification_report(y_test, y_pred, target_names=['No', 'Yes']))
```

## 4.4 ROC 曲线

```python
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt

fpr, tpr, thresholds = roc_curve(y_test, y_prob)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
plt.legend()
plt.show()
```
$v$,
    $v${"questions": [{"id": "q4-1", "type": "concept", "difficulty": "easy", "question": "MJ4 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q4-2", "type": "concept", "difficulty": "easy", "question": "MJ4 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q4-3", "type": "calculation", "difficulty": "medium", "question": "MJ4 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q4-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ4 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 4;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$sigmoid(0)$v$, $v$0.5$v$, false, $v$sigmoid计算$v$, 'EXACT_MATCH', 1),
    (new_task_id, 'tc_2', $v$逻辑回归预测$v$, $v$返回概率数组$v$, false, $v$预测概率$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$计算混淆矩阵指标$v$, $v$返回accuracy/precision/recall/f1$v$, false, $v$评估指标$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$找最优阈值$v$, $v$返回best_threshold和best_f1$v$, true, $v$最优阈值$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ4';
END $$;

COMMIT;
