-- ============================================================
-- MJ3: 数据预处理与特征工程
-- practice_id=7, order_in_practice=3
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$数据预处理与特征工程$v$,
    'PRACTICE',
    3,
    $v$intermediate$v$,
    $v$## 编码方法

## 3.1 标签编码与独热编码

```python
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, OrdinalEncoder

# 标签编码(仅用于有序类别)
le = LabelEncoder()
df['size_encoded'] = le.fit_transform(df['size'])  # S/M/L → 0/1/2

# 独热编码(用于无序类别)
pd.get_dummies(df, columns=['color'], prefix='color')
# 或
ohe = OneHotEncoder(sparse=False, drop='first')
encoded = ohe.fit_transform(df[['color']])

# 有序编码(Ordinal)
size_order = {'small': 0, 'medium': 1, 'large': 2}
df['size_ord'] = df['size'].map(size_order)
```


## 标准化与归一化

## 3.2 z-score 标准化

将数据转换为均值0、标准差1的分布:

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
# scaler.mean_  → 均值
# scaler.scale_  → 标准差
```

## 3.3 MinMax 归一化

将数据缩放到 [0, 1] 区间:

```python
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
X_norm = scaler.fit_transform(X)
# 公式: X_norm = (X - X.min()) / (X.max() - X.min())
```


## 特征选择

## 3.4 方差过滤

```python
from sklearn.feature_selection import VarianceThreshold

# 删除方差为0的特征(所有样本值相同)
selector = VarianceThreshold(threshold=0.0)
X_selected = selector.fit_transform(X)
# selector.get_support() → 各特征是否被保留
```

## 3.5 相关性特征选择

删除与目标变量高度相关的特征,避免多重共线性:

```python
# 计算与目标的相关性
corr_with_target = df.corr()['target'].abs().sort_values(ascending=False)
# 删除与target相关性<0.1的特征
low_corr_features = corr_with_target[corr_with_target < 0.1].index.tolist()
df = df.drop(columns=low_corr_features)
```

## 3.6 训练/测试集划分

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
# stratify=y 保证训练/测试集类别比例一致
```
$v$,
    $v${"questions": [{"id": "q3-1", "type": "concept", "difficulty": "easy", "question": "MJ3 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q3-2", "type": "concept", "difficulty": "easy", "question": "MJ3 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q3-3", "type": "calculation", "difficulty": "medium", "question": "MJ3 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q3-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ3 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 3;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$标签编码$v$, $v$返回编码Series和映射$v$, false, $v$标签编码$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$独热编码$v$, $v$返回含新列DataFrame$v$, false, $v$独热编码$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$标准化train和test$v$, $v$返回标准化后数据$v$, false, $v$标准化$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$方差过滤$v$, $v$返回筛选后矩阵和索引$v$, true, $v$方差过滤$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ3';
END $$;

COMMIT;
