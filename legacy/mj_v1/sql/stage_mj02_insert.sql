-- ============================================================
-- MJ2: 数据探索与特征理解
-- practice_id=7, order_in_practice=2
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$数据探索与特征理解$v$,
    'PRACTICE',
    2,
    $v$beginner$v$,
    $v$## pandas 数据探索

## 2.1 数据读取与概况

```python
import pandas as pd
import numpy as np

df = pd.read_csv('data.csv')

# 基本信息
df.info()          # 类型、非空数、内存
df.describe()     # 统计描述(count/mean/std/min/25%/50%/75%/max)
df.shape           # (行数, 列数)
df.dtypes          # 各列数据类型
df.head(5)         # 前5行

# 缺失值分析
df.isnull().sum()           # 每列缺失数
df.isnull().mean()          # 每列缺失率
df.isnull().sum().sum()     # 总缺失数
```


## 数据可视化

## 2.2 matplotlib/seaborn 基础

```python
import matplotlib.pyplot as plt
import seaborn as sns

# 直方图
plt.figure(figsize=(8, 4))
df['age'].hist(bins=30, edgecolor='black')
plt.title('Age Distribution')
plt.xlabel('Age')
plt.ylabel('Frequency')
plt.show()

# 箱线图
sns.boxplot(x='gender', y='income', data=df)
plt.title('Income by Gender')
plt.show()

# 散点图
plt.figure(figsize=(8, 5))
plt.scatter(df['sqft'], df['price'], alpha=0.5)
plt.xlabel('Square Feet')
plt.ylabel('Price')
plt.title('Price vs Square Feet')
plt.show()
```


## 相关性分析

## 2.3 皮尔逊相关系数

```python
# 计算相关系数矩阵
corr = df.corr(method='pearson')

# 热力图
import seaborn as sns
plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm',
            center=0, square=True, linewidths=0.5)
plt.title('Correlation Heatmap')
plt.tight_layout()
plt.show()

# 找高相关特征对
high_corr_pairs = []
for i in range(len(corr.columns)):
    for j in range(i+1, len(corr.columns)):
        if abs(corr.iloc[i, j]) > 0.8:
            high_corr_pairs.append((corr.columns[i], corr.columns[j], corr.iloc[i, j]))
print(high_corr_pairs)
```

## 2.4 相关性解读

| 相关系数 | 解读 |
|---------|------|
| 0.8~1.0 | 强正相关 |
| 0.5~0.8 | 中等正相关 |
| 0.2~0.5 | 弱正相关 |
| -0.2~0.2 | 几乎无关 |
| -0.5~-0.2 | 弱负相关 |
| -0.8~-0.5 | 中等负相关 |
| -1.0~-0.8 | 强负相关 |
$v$,
    $v${"questions": [{"id": "q2-1", "type": "concept", "difficulty": "easy", "question": "MJ2 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q2-2", "type": "concept", "difficulty": "easy", "question": "MJ2 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q2-3", "type": "calculation", "difficulty": "medium", "question": "MJ2 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q2-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ2 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 2;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$含缺失值的 DataFrame$v$, $v$返回概况dict$v$, false, $v$数据概况$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$计算相关系数矩阵$v$, $v$返回DataFrame$v$, false, $v$相关性分析$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$threshold=0.8$v$, $v$返回高相关特征对$v$, true, $v$高相关对检测$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$基于IQR检测异常值$v$, $v$返回异常值索引$v$, true, $v$异常值检测$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ2';
END $$;

COMMIT;
