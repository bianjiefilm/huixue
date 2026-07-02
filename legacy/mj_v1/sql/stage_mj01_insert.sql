-- ============================================================
-- MJ1: 数据挖掘概述与流程
-- practice_id=7, order_in_practice=1
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$数据挖掘概述与流程$v$,
    'PRACTICE',
    1,
    $v$beginner$v$,
    $v$## 数据挖掘导论

## 1.1 什么是数据挖掘

数据挖掘是从大规模数据中提取隐含在其中的、先前未知的、但又是有效的
可利用信息的过程。与数据分析不同，数据挖掘更强调自动发现规律。

典型应用场景:
- 用户行为分析（推荐系统）
- 风险控制（信用评分）
- 客户流失预警
- 欺诈检测
- 市场细分

## 1.2 CRISP-DM 标准流程

Cross-Industry Standard Process for Data Mining 是业界最权威的数据挖掘方法论:

```
业务理解 → 数据理解 → 数据准备 → 建模 → 评估 → 部署
      ↑______________↓                    ↓
      (迭代优化)                      (反馈改进)
```

各阶段核心任务:

| 阶段 | 核心任务 |
|------|---------|
| 业务理解 | 明确业务目标、确定挖掘目标、评估资源 |
| 数据理解 | 收集数据、描述数据、探索数据质量 |
| 数据准备 | 清洗数据、特征工程、构建新特征 |
| 建模 | 选择算法、训练模型、调参 |
| 评估 | 模型评估、结果解释、业务验证 |
| 部署 | 上线、监控、维护 |

## 1.3 机器学习分类

| 类型 | 特点 | 代表算法 |
|------|------|---------|
| 监督学习 | 有标签，预测标签 | 逻辑回归、决策树、SVM |
| 无监督学习 | 无标签，发现结构 | K-Means、PCA、关联规则 |
| 半监督学习 | 部分标签 | 自编码器、标签传播 |
| 强化学习 | 试错，延迟奖励 | Q-Learning、Policy Gradient |


## scikit-learn 建模流程

## 1.4 sklearn 建模六步法

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

# 1. 划分训练集/测试集
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 2. 特征标准化
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)

# 3. 选择模型
model = LogisticRegression(max_iter=1000)

# 4. 训练模型
model.fit(X_train, y_train)

# 5. 预测
y_pred = model.predict(X_test)

# 6. 评估
print(f"准确率: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred))
```

## 1.5 sklearn 数据集 API

```python
from sklearn.datasets import load_iris, make_classification

# 内置数据集
iris = load_iris()
X, y = iris.data, iris.target

# 生成模拟数据
X, y = make_classification(
    n_samples=1000, n_features=20,
    n_informative=15, n_redundant=5,
    random_state=42
)
```


## 模型评估基础

## 1.6 评估指标

分类问题:

| 指标 | 公式 | 适用场景 |
|------|------|---------|
| 准确率 | TP+TN / Total | 类别均衡 |
| 精确率 | TP / (TP+FP) | 假阳性代价高 |
| 召回率 | TP / (TP+FN) | 漏检代价高 |
| F1 分数 | 2×P×R / (P+R) | 综合衡量 |
| AUC-ROC | ROC 曲线下面积 | 不受阈值影响 |

```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)

accuracy  = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred, average='macro')
recall    = recall_score(y_test, y_pred, average='macro')
f1       = f1_score(y_test, y_pred, average='macro')
auc      = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])

cm = confusion_matrix(y_test, y_pred)
print(cm)
```

## 1.7 过拟合与欠拟合

- **过拟合**: 模型在训练集上表现很好，在测试集上表现差
  → 解决: 增加数据、正则化、降低模型复杂度、交叉验证
- **欠拟合**: 模型在训练集和测试集上都表现差
  → 解决: 增加特征、使用更复杂模型、增加训练轮次
$v$,
    $v${"questions": [{"id": "q1-1", "type": "concept", "difficulty": "easy", "question": "CRISP-DM 流程中，哪个阶段负责明确业务目标和评估资源？", "hint": "流程的第一步。", "options": ["A. 数据理解", "B. 业务理解", "C. 数据准备", "D. 建模"], "answer": "B", "explanation": "业务理解(Business Understanding)是CRISP-DM的第一步，负责明确业务目标、确定挖掘目标和评估资源。"}, {"id": "q1-2", "type": "concept", "difficulty": "easy", "question": "scikit-learn 建模流程中，哪个方法负责对数据进行预测？", "hint": "预测方法。", "options": ["A. fit()", "B. predict()", "C. transform()", "D. score()"], "answer": "B", "explanation": "predict()方法用训练好的模型对数据进行预测，fit()负责训练，transform()负责转换特征，score()返回模型评估得分。"}, {"id": "q1-3", "type": "calculation", "difficulty": "medium", "question": "某模型训练集准确率 0.99，测试集准确率 0.60，gap 是多少？是否过拟合？", "hint": "gap = 训练 - 测试。", "options": ["A. gap=0.39，过拟合", "B. gap=0.39，欠拟合", "C. gap=1.59，过拟合", "D. gap=0.39，正常"], "answer": "A", "explanation": "gap = 0.99 - 0.60 = 0.39，训练远高于测试，是典型的过拟合现象。"}, {"id": "q1-4", "type": "coding", "difficulty": "medium", "question": "请实现 evaluate_classifier(y_true, y_pred) 函数，返回准确率/精确率/召回率/F1。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 1;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$CRISP-DM 6阶段$v$, $v$返回6个阶段名称$v$, false, $v$阶段列表$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$有标签的特征矩阵和标签向量$v$, $v$supervised$v$, false, $v$问题类型判断$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$准确率/精确率/召回率/F1$v$, $v$返回dict含4指标$v$, false, $v$评估指标$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$train=0.99, test=0.60$v$, $v$is_overfitting=true, gap=0.39$v$, true, $v$过拟合检测$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ1';
END $$;

COMMIT;
