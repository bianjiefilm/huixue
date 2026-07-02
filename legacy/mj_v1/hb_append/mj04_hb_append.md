

## 交叉熵损失(handbook 学习目标补全)

逻辑回归通过最大似然估计求解, 等价于最小化二分类交叉熵损失:

$L(w) = -\frac{1}{N} \sum_{i=1}^{N} [y_i \log(\hat{p}_i) + (1-y_i) \log(1-\hat{p}_i)]$

其中 $\hat{p}_i = \sigma(w^T x_i + b)$ 是 sigmoid 输出。直观理解: 真实 $y=1$ 时 $\hat{p}$ 越接近 1 损失越小, 越接近 0 损失越大 (惩罚错误置信)。

为什么不用 MSE? MSE + sigmoid 会让损失曲面非凸, 出现局部最优; 交叉熵 + sigmoid 是凸函数, 梯度下降一定收敛到全局最优。


## 完整可运行示例: 乳腺癌二分类全流程(LR + DT 双模型对比)

```python
import matplotlib.pyplot as plt
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    confusion_matrix, classification_report,
    roc_auc_score, roc_curve, accuracy_score, f1_score
)

# 1. 加载与划分
data = load_breast_cancer()
X, y = data.data, data.target  # 0=恶性, 1=良性
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# 2. 标准化(LR 必须, DT 不需要)
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s = scaler.transform(X_test)

# 3. 双模型训练
lr = LogisticRegression(max_iter=2000, random_state=42)
lr.fit(X_train_s, y_train)
y_prob_lr = lr.predict_proba(X_test_s)[:, 1]  # [:, 1] 取正类概率

dt = DecisionTreeClassifier(max_depth=5, min_samples_leaf=10, random_state=42)
dt.fit(X_train, y_train)  # DT 用未标准化, 阈值更可解释
y_prob_dt = dt.predict_proba(X_test)[:, 1]

# 4. 综合评估
for name, model, X_eval, y_prob in [('LR', lr, X_test_s, y_prob_lr),
                                     ('DT', dt, X_test, y_prob_dt)]:
    y_pred = model.predict(X_eval)
    print(f"\n=== {name} ===")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print(f"F1:       {f1_score(y_test, y_pred):.4f}")
    print(f"AUC:      {roc_auc_score(y_test, y_prob):.4f}")
    print(f"混淆矩阵:\n{confusion_matrix(y_test, y_pred)}")

# 5. ROC 曲线对比
plt.figure(figsize=(8, 6))
for name, y_prob in [('LR', y_prob_lr), ('DT', y_prob_dt)]:
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    plt.plot(fpr, tpr, lw=2, label=f'{name} (AUC={roc_auc_score(y_test, y_prob):.3f})')
plt.plot([0, 1], [0, 1], 'k--', lw=1)
plt.xlabel('FPR'); plt.ylabel('TPR'); plt.title('ROC Curve')
plt.legend(); plt.show()
```

跑通后 LR AUC≈0.998, DT AUC≈0.96。LR 准确率高但黑盒, DT 略差但每条路径可解释 — 医疗辅助诊断这类高解释场景 DT 反而合适。


## 常见错误与调试

**坑 1: `LogisticRegression` 报 `ConvergenceWarning`** — 修法: `max_iter=2000`, 确保 `StandardScaler` 已应用。lbfgs 优化器对未标准化的高量纲特征收敛极慢。

**坑 2: 决策树 `max_depth=None` 严重过拟合** — 不限深度时 DT 在训练集 100% 但测试集 70%。修法: 同时设 `max_depth=5~10`、`min_samples_leaf=5~20`、`min_samples_split=10~30` 三个剪枝参数。

**坑 3: `predict_proba` 列序混淆** — `[:, 0]` 是负类, `[:, 1]` 是正类。AUC/ROC 必须传正类概率。修法: 用 `model.classes_` 确认顺序, 永远用 `[:, 1]`。

**坑 4: ROC 曲线传 `y_pred` 而不是 `y_prob`** — `roc_curve(y_test, y_pred)` 用预测标签算出来只有一个点 (退化), AUC 也算错。修法: 必须传 `predict_proba(...)[:, 1]` 或 `decision_function(...)`。

**坑 5: 类别不平衡时直接看 accuracy** — 良性:恶性 = 357:212 已不算平衡, 真实业务比例可能 99:1。修法: 看 F1、ROC-AUC、PR-AUC, 或加 `class_weight='balanced'`。


## 扩展场景

| 业务场景 | 模型选择理由 | 关键评估 |
|---------|------------|---------|
| 邮件垃圾分类 | LR 训练快、易部署 | F1 + 误报率 |
| 反欺诈识别 | DT/RF 可输出规则给风控 | 召回率 + Top-K 精确 |
| 病情预后判断 | DT 决策路径医生可审 | AUC + 校准曲线 |
| 信用违约 | LR + 评分卡 | KS 值 + AUC |
