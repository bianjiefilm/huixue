-- ============================================================
-- MJ10: 模型评估与优化
-- practice_id=7, order_in_practice=10
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$模型评估与优化$v$,
    'PRACTICE',
    10,
    $v$intermediate$v$,
    $v$## 交叉验证

## 10.1 K折交叉验证

```python
from sklearn.model_selection import cross_val_score, StratifiedKFold

skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# 单指标
scores = cross_val_score(model, X, y, cv=skf, scoring='accuracy')
print(f"5折CV准确率: {scores.mean():.4f} ± {scores.std():.4f}")

# 多指标
from sklearn.model_selection import cross_validate
results = cross_validate(model, X, y, cv=skf,
                         scoring=['accuracy', 'f1', 'roc_auc'],
                         return_train_score=True)
print(f"训练准确率: {results['train_accuracy'].mean():.4f}")
print(f"测试准确率: {results['test_accuracy'].mean():.4f}")
```


## 网格搜索

## 10.2 GridSearchCV

```python
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import RandomForestClassifier

param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 5, 7, None],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
}

rf = RandomForestClassifier(random_state=42)
grid_search = GridSearchCV(
    rf, param_grid,
    cv=5, scoring='accuracy',
    n_jobs=-1, verbose=1,
    refit=True  # 用最佳参数在全部数据上重新训练
)
grid_search.fit(X_train, y_train)

print(f"最佳参数: {grid_search.best_params_}")
print(f"最佳CV得分: {grid_search.best_score_:.4f}")
best_model = grid_search.best_estimator_
```


## 学习曲线与诊断

## 10.3 学习曲线

```python
from sklearn.model_selection import learning_curve

train_sizes, train_scores, test_scores = learning_curve(
    model, X, y, cv=5,
    train_sizes=np.linspace(0.1, 1.0, 10),
    scoring='accuracy'
)

train_mean = train_scores.mean(axis=1)
train_std = train_scores.std(axis=1)
test_mean = test_scores.mean(axis=1)
test_std = test_scores.std(axis=1)

plt.plot(train_sizes, train_mean, 'b-', label='Training Score')
plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, alpha=0.2, color='blue')
plt.plot(train_sizes, test_mean, 'r-', label='Validation Score')
plt.fill_between(train_sizes, test_mean - test_std, test_mean + test_std, alpha=0.2, color='red')
plt.xlabel('Training Size')
plt.ylabel('Accuracy')
plt.title('Learning Curve')
plt.legend()
plt.show()
```

## 10.4 诊断结论

| 曲线形态 | 诊断 | 解决方向 |
|---------|------|---------|
| 训练高/验证低,gap大 | 过拟合 | 增加数据/正则化/简化模型 |
| 训练低/验证低,gap小 | 欠拟合 | 增加特征/增加模型复杂度 |
| 训练/验证都低且收敛 | 数据本身难 | 重新特征工程 |
$v$,
    $v${"questions": [{"id": "q10-1", "type": "concept", "difficulty": "easy", "question": "MJ10 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q10-2", "type": "concept", "difficulty": "easy", "question": "MJ10 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q10-3", "type": "calculation", "difficulty": "medium", "question": "MJ10 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q10-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ10 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 10;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$分层K折划分$v$, $v$返回K个split$v$, false, $v$分层划分$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$Bootstrap抽样$v$, $v$返回等大样本$v$, false, $v$Bootstrap$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$学习曲线计算$v$, $v$返回mean和std$v$, false, $v$学习曲线$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$交叉验证得分$v$, $v$返回各折得分$v$, true, $v$交叉验证$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ10';
END $$;

COMMIT;
