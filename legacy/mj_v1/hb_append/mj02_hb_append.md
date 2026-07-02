

## 完整可运行示例: California Housing 数据 EDA 全流程

用 sklearn 内置的 California Housing 数据演示完整 EDA, 覆盖概况、分布、相关性, 可直接 Jupyter 运行:

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.datasets import fetch_california_housing

# 1. 加载与概况
data = fetch_california_housing(as_frame=True)
df = data.frame
print(f"Shape: {df.shape}")
print(df.describe().round(2))
print(f"缺失值总数: {df.isnull().sum().sum()}")

# 2. 目标变量分布
plt.figure(figsize=(10, 4))
plt.subplot(1, 2, 1)
df['MedHouseVal'].hist(bins=50, edgecolor='black')
plt.title('房价分布(直方图)')
plt.subplot(1, 2, 2)
sns.boxplot(y=df['MedHouseVal'])
plt.title('房价箱线图(看异常值)')
plt.tight_layout(); plt.show()

# 3. 相关性热力图
corr = df.corr(method='pearson')
plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm',
            center=0, square=True, linewidths=0.5)
plt.title('Correlation Heatmap')
plt.tight_layout(); plt.show()

# 4. 找与目标高相关的特征
target_corr = corr['MedHouseVal'].abs().sort_values(ascending=False)
print("特征-目标相关性排序:")
print(target_corr)

# 5. 找特征间高相关对(多重共线性诊断)
pairs = [(corr.columns[i], corr.columns[j], round(corr.iloc[i, j], 3))
         for i in range(len(corr.columns))
         for j in range(i+1, len(corr.columns))
         if abs(corr.iloc[i, j]) > 0.7]
print(f"高相关特征对(|corr|>0.7): {pairs}")
```

跑完你应该看到 MedInc 与房价呈强正相关 (≈0.69), AveRooms 与 AveBedrms 高度共线 (>0.85)。


## 常见错误与调试

**坑 1: `df.corr()` 静默忽略字符串列** — 含分类列 (object dtype) 时 `df.corr()` 直接跳过, 你以为算了实际没算。修法: `df.select_dtypes(include=[np.number]).corr()` 显式取数值列, 或先编码。

**坑 2: pearson 对非线性关系会漏判** — y=x² 这类非线性关系 pearson 算出来接近 0, 但 spearman (秩相关) 接近 1。修法: 怀疑非线性时用 `df.corr(method='spearman')` 对比。

**坑 3: 缺失值未处理就 describe** — `describe()` 默认忽略 NaN, count 列会比预期小, mean/std 是基于 dropna 算的, 容易低估变异。修法: 先 `df.isnull().sum()` 看缺失分布, 处理缺失再做统计。

**坑 4: 异常值导致 corr 被 outlier 主导** — 一个 100 倍极值可让两列 corr 从 0.1 跳到 0.9。修法: 先用 IQR 法过滤 outlier 再算; 或用 spearman (对极值不敏感)。


## 扩展场景

| 业务场景 | 重点关注 | 典型工具 |
|---------|---------|---------|
| A/B 测试探索 | 实验组 vs 对照组分布差异 | groupby + 假设检验 (t-test/chi2) |
| 风控特征筛选 | IV 值 / WOE 编码 | toad / scorecardpy |
| 时序数据 | 周期性、趋势、季节性 | pandas rolling / resample |

EDA 三层递进: **单变量** (分布/缺失/异常) → **双变量** (相关/散点/分组) → **多变量** (PCA / t-SNE 看高维结构)。每层做完再进下一层, 不要一开始就做高维分析。
