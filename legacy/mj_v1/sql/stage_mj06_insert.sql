-- ============================================================
-- MJ6: 监督学习: 回归
-- practice_id=7, order_in_practice=6
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$监督学习: 回归$v$,
    'PRACTICE',
    6,
    $v$intermediate$v$,
    $v$## 线性回归

## 6.1 原理

线性回归拟合超平面 $y = Xw + b$, 通过最小化均方误差(MSE):

```python
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

lr = LinearRegression()
lr.fit(X_train, y_train)
y_pred = lr.predict(X_test)

mse = mean_squared_error(y_test, y_pred)
rmse = np.sqrt(mse)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"MSE: {mse:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}, R²: {r2:.4f}")
```


## 正则化回归

## 6.2 Ridge 回归 (L2 正则化)

在损失函数中加入权重平方和,惩罚大权重:

$Loss = MSE + \\alpha \\sum_{i} w_i^2$

```python
from sklearn.linear_model import Ridge

ridge = Ridge(alpha=1.0)  # alpha 越大,权重越接近0
ridge.fit(X_train, y_train)
y_pred = ridge.predict(X_test)
```

## 6.3 Lasso 回归 (L1 正则化)

$Loss = MSE + \\alpha \\sum_{i} |w_i|$

Lasso 的特点: 可以将不重要特征的权重压缩为0,实现特征选择:

```python
from sklearn.linear_model import Lasso

lasso = Lasso(alpha=1.0)
lasso.fit(X_train, y_train)
y_pred = lasso.predict(X_test)
# lasso.coef_ 中接近0的系数对应不重要特征
```

## 6.4 正则化对比

| 方法 | 正则项 | 特点 |
|------|--------|------|
| LinearRegression | 无 | 易过拟合 |
| Ridge (L2) | αΣw² | 收缩权重到小值,不完全清零 |
| Lasso (L1) | αΣ|w| | 稀疏解,可做特征选择 |
| ElasticNet | L1+L2 | 兼具两者优点 |
$v$,
    $v${"questions": [{"id": "q6-1", "type": "concept", "difficulty": "easy", "question": "MJ6 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q6-2", "type": "concept", "difficulty": "easy", "question": "MJ6 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q6-3", "type": "calculation", "difficulty": "medium", "question": "MJ6 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q6-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ6 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 6;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$MSE计算$v$, $v$MSE=0.375$v$, false, $v$MSE$v$, 'EXACT_MATCH', 1),
    (new_task_id, 'tc_2', $v$MAE计算$v$, $v$MAE=0.5$v$, false, $v$MAE$v$, 'EXACT_MATCH', 2),
    (new_task_id, 'tc_3', $v$R2计算$v$, $v$返回0~1之间的值$v$, false, $v$R2$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$Ridge损失计算$v$, $v$返回正损失值$v$, true, $v$Ridge损失$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ6';
END $$;

COMMIT;
