

## 缺失值处理(handbook 学习目标补全)

```python
import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer, KNNImputer

# 策略 1: 删除(缺失率 <5% 且 MCAR 时可用)
df.dropna(axis=1, thresh=len(df)*0.7)  # 删缺失率 >30% 的列

# 策略 2: 单值填充
df['age'].fillna(df['age'].median(), inplace=True)         # 数值: 中位数(对异常值鲁棒)
df['city'].fillna(df['city'].mode()[0], inplace=True)      # 分类: 众数

# 策略 3: KNN 多重插补(基于相似样本)
KNNImputer(n_neighbors=5).fit_transform(df[['age', 'income', 'tenure']])
```

口诀: 缺失 <5% 删行; 数值用中位数 (不易受异常值拉动); 分类用众数或 `'UNKNOWN'`; 高价值数据用 KNN/MICE 多重插补。


## 完整可运行示例: 信用风险数据预处理全流程

下面演示 split → 缺失填充 → 编码 → 标准化 → 特征选择 全流程, 可直接 Jupyter 运行:

```python
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import VarianceThreshold
from sklearn.model_selection import train_test_split

df = pd.DataFrame({
    'age':       [25, 45, np.nan, 33, 52, 28, 41, np.nan, 35, 30],
    'income':    [3000, 8000, 5500, 4200, 9500, 3500, 7200, 4800, 5200, 3800],
    'gender':    ['M', 'F', 'M', 'F', 'M', 'F', 'F', 'M', 'M', 'F'],
    'edu':       ['hs', 'phd', 'ba', 'ba', 'ms', 'hs', 'ms', 'ba', 'phd', 'hs'],
    'default':   [0, 0, 1, 0, 0, 1, 0, 1, 0, 1],
})
y = df['default']; X = df.drop('default', axis=1)

# 1. 必须最先 split, 防泄漏
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)

# 2. 缺失填充: 用 train 的中位数
imputer = SimpleImputer(strategy='median')
X_train[['age']] = imputer.fit_transform(X_train[['age']])
X_test[['age']] = imputer.transform(X_test[['age']])

# 3. 编码: 有序用 map, 无序用 get_dummies + 列对齐
X_train['edu'] = X_train['edu'].map({'hs':0,'ba':1,'ms':2,'phd':3})
X_test['edu'] = X_test['edu'].map({'hs':0,'ba':1,'ms':2,'phd':3})
X_train = pd.get_dummies(X_train, columns=['gender'], drop_first=True)
X_test = pd.get_dummies(X_test, columns=['gender'], drop_first=True)
X_test = X_test.reindex(columns=X_train.columns, fill_value=0)  # 关键! 列对齐

# 4. 方差过滤(删常量列)+ 标准化
selector = VarianceThreshold(threshold=0.0)
X_train_v = selector.fit_transform(X_train)
X_test_v = selector.transform(X_test)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train_v)
X_test_s = scaler.transform(X_test_v)

print(f"训练集: {X_train_s.shape}, 均值≈0: {X_train_s.mean(axis=0).round(2)}")
```

黄金顺序: **split → fit imputer/scaler 用 train → transform 用 train 的统计量**。任何步骤做反都会引入数据泄漏。


## 常见错误与调试

**坑 1: split 之前 `fit_transform`** — 测试集 mean/std 泄漏到训练。修法: 先 split, 再用 X_train fit, X_test 只 transform。

**坑 2: `LabelEncoder` 用于无序多类别** — `LE` 给 red/blue/green 编 0/1/2 让模型误以为类别有大小关系。修法: 无序类别用 `get_dummies` 或 `OneHotEncoder`; 有序 (S/M/L) 用 `OrdinalEncoder` 或 dict map。

**坑 3: `get_dummies` 训练测试列不一致** — 测试集某类别没出现 → 列丢失, predict 报形状错。修法: `X_test = X_test.reindex(columns=X_train.columns, fill_value=0)`。

**坑 4: `train_test_split` 没 `stratify=y`** — 类别不平衡时小类可能完全消失在测试集。修法: 分类问题永远加 `stratify=y`。


## 扩展场景

| 业务场景 | 关键预处理 | 工具 |
|---------|----------|------|
| 信贷评分卡 | WOE 编码 / 分箱 | toad / scorecardpy |
| 推荐系统 | user-item 编码 / hashing trick | sklearn FeatureHasher |
| 文本特征 | TF-IDF / Word Embedding | TfidfVectorizer / gensim |
| 不平衡分类 | SMOTE 上采样 / class_weight | imbalanced-learn |
