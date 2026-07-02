

## 完整可运行示例: Iris 三分类全流程

CRISP-DM 在 sklearn 上的最小闭环, 可直接复制到 Jupyter 运行:

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

iris = load_iris()
X, y = iris.data, iris.target

# 必须先 split 再 fit_transform, 否则测试集泄漏
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)  # 测试集只 transform 不 fit

model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train_s, y_train)
y_pred = model.predict(X_test_s)

print(f"准确率: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred, target_names=iris.target_names))
```

跑通后准确率约 0.97。这就是 CRISP-DM 在代码层的最小闭环。


## 常见错误与调试

**坑 1: 在 `train_test_split` 之前做 `fit_transform`** — 测试集统计量 (mean/std) 泄漏进训练。修法: 永远先 split, 再用 X_train fit, X_test 只 transform。

**坑 2: `LogisticRegression` 报 `ConvergenceWarning: lbfgs failed to converge`** — 修法: `max_iter=1000` 或 `2000`; 同时检查特征是否标准化, 未标准化的高量纲特征让优化器收敛极慢。

**坑 3: 类别不平衡用 accuracy 误导** — 正/负 99:1 时全预测为正能拿 99% accuracy, 模型实则没学到。修法: 用 `f1_score(average='macro')` 或 `classification_report` 看每类指标; 不平衡分类首选 ROC-AUC 或召回率。

**坑 4: `random_state` 没固定, 结果不可复现** — 调参时无法判断改动是否真的有效。修法: 在 `train_test_split` 与所有模型构造器统一 `random_state=42`。


## 扩展场景与算法选型

| 业务场景 | 数据特点 | 推荐算法 | 关键评估指标 |
|---------|---------|---------|-------------|
| 信贷违约预测 | 类别不平衡 | XGBoost + 类别权重 | KS / AUC / 召回@阈值 |
| 客户流失预警 | 时序 + 静态特征 | GBDT / RNN | 召回率 (漏报代价高) |
| 商品推荐 | 用户-物品稀疏矩阵 | 协同过滤 / 矩阵分解 | NDCG / Hit Rate |
| 客户分群 | 无标签, 多维行为 | K-Means / DBSCAN | 轮廓系数 |
| 关联购买分析 | 事务数据 | Apriori / FP-Growth | 提升度 (lift) |

选型口诀: 有标签做监督, 数值用回归, 类别用分类; 高解释性 (金融/医疗) 优先逻辑回归与决策树; 大样本表格数据首选 XGBoost / LightGBM。
