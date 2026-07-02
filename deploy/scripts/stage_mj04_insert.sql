-- ============================================================
-- MJ4: 监督学习: 分类基础
-- practice_id=7, order_in_practice=4
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$监督学习: 分类基础$v$,
        'PRACTICE',
        4,
        $v$intermediate$v$,
        $v$## 分类问题与逻辑回归

## 1.1 二分类问题的核心结构

给定输入特征 $\mathbf{x}$ 与二元标签 $y \in \{0, 1\}$, 模型要学习一个决策函数 $f(\mathbf{x}) \in [0, 1]$, 表示 $\mathbf{x}$ 属于类别 1 的概率。然后通过阈值 (默认 0.5) 把概率转为标签。

逻辑回归是最基础的二分类模型 — 它不是回归问题, 名字"回归"来自历史命名遗留, 实际做的是分类。

## 1.2 sigmoid 函数

把任意实数 $z$ 压缩到 $(0, 1)$ 区间:

$\sigma(z) = \frac{1}{1 + e^{-z}}$

关键性质:
- $\sigma(0) = 0.5$ (中点)
- $\sigma(z) \to 1$ 当 $z \to +\infty$
- $\sigma(z) \to 0$ 当 $z \to -\infty$
- 单调递增, 输出严格落在 $(0, 1)$
- 中心对称: $\sigma(-z) = 1 - \sigma(z)$

数值要点: $z$ 极大时 $e^{-z}$ 下溢, 极小时 $e^{-z}$ 上溢, 工业实现需做数值稳定 (本关数据规模小不要求, 但概念要懂)。

## 1.3 交叉熵损失

逻辑回归用最大似然估计求解, 等价于最小化二分类交叉熵:

$L = -\frac{1}{N} \sum_{i=1}^{N} [y_i \log(\hat{p}_i) + (1-y_i) \log(1-\hat{p}_i)]$

为什么交叉熵优于平方误差? sigmoid 配上平方误差形成的损失曲面非凸, 优化时容易陷入局部最优; sigmoid 配上交叉熵则是凸函数, 梯度优化一定收敛到全局最优。这是逻辑回归选交叉熵的本质原因。


## 决策树概念

## 2.1 决策树的工作方式

决策树通过一系列"是/否"分裂构造决策路径。比如风控场景: 第一次问"年龄是否 < 30?"; 若是, 再问"收入是否 > 5000?", 若否则归为"高风险"; 这样形成一棵从根到叶的判定树, 每个叶节点对应一个最终类别。

与逻辑回归相比, 决策树的最大优势是**可解释性**: 每个预测都有一条人类可读的决策路径。这在金融/医疗/法律场景非常重要 — 模型说"拒贷", 银行必须告诉客户原因。

## 2.2 分裂的核心: 不纯度下降

每次分裂选哪个特征、哪个阈值, 取决于"分裂后两个子集的纯度"。常用纯度指标 gini:

$\text{Gini}(S) = 1 - \sum_{c} p_c^2$

其中 $p_c$ 是类别 $c$ 在节点 $S$ 中的占比。完全纯净 (单类) 时 Gini=0, 类别均匀时 Gini 最大 (二分类下 0.5)。

分裂目标: 选使加权子节点 Gini 最小 (即不纯度下降最多) 的分裂。本关只要求理解概念, 实现细节留给后续章节。

## 2.3 决策树的过拟合风险

不限深度的决策树会一直分裂到每个叶子只剩一个样本, 训练 100% 但测试糟糕。**剪枝**是控制过拟合的标准手段:

| 参数 | 作用 |
|------|------|
| max_depth | 限制最大深度 |
| min_samples_leaf | 叶节点最小样本数 |
| min_samples_split | 分裂所需最小样本数 |


## 混淆矩阵与四大指标

## 3.1 混淆矩阵

二分类预测对 4 种结果 (取真实正类为"阳性"):

|              | 预测正 | 预测负 |
|--------------|--------|--------|
| **真实正**   | TP     | FN     |
| **真实负**   | FP     | TN     |

- **TP** (True Positive): 真阳性, 真的是 1 也预测为 1
- **FN** (False Negative): 假阴性, 真的是 1 但预测为 0 (漏报)
- **FP** (False Positive): 假阳性, 真的是 0 但预测为 1 (误报)
- **TN** (True Negative): 真阴性, 真的是 0 也预测为 0

## 3.2 四个核心指标

$\text{Accuracy} = \frac{TP + TN}{TP + FP + TN + FN}$ — 整体正确率, 类别不平衡时不可信 (见 MJ01)

$\text{Precision} = \frac{TP}{TP + FP}$ — 预测为正的样本里, 真的是正的比例; 衡量"误报代价"

$\text{Recall} = \frac{TP}{TP + FN}$ — 真实为正的样本里, 被识别出来的比例; 衡量"漏报代价"

$F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$ — 精确率与召回率的调和平均

## 3.3 业务上的取舍

Precision 与 Recall 通常此消彼长, 调阈值就在两者之间平衡。业务上选哪个看错的代价:

- **医疗筛查**: 漏掉一个病人代价远高于误诊一个健康人 → 优先 Recall
- **垃圾邮件**: 把正常邮件标垃圾代价高于漏过个垃圾邮件 → 优先 Precision
- **信贷风控**: 漏放贷给坏客户损失巨大 → 优先 Recall

F1 是综合分, 没有特别业务偏向时用 F1 选模型。


## 阈值、ROC-AUC 与业务案例

## 4.1 阈值如何把分数变标签

sigmoid (或任何分类器) 输出的是概率 $\hat{p} \in [0, 1]$。要变标签必须设阈值:

$\hat{y} = \begin{cases} 1 & \text{if } \hat{p} \geq T \\ 0 & \text{otherwise} \end{cases}$

默认 $T = 0.5$ 是均衡选择。但业务可能调高 (要求更高置信才判 1, 提高 Precision) 或调低 (希望尽量召回, 提高 Recall)。

## 4.2 ROC 与 AUC

ROC 曲线: 横轴 FPR (假阳性率), 纵轴 TPR (真阳性率, 即 Recall), 通过遍历所有阈值得到一条曲线。

AUC = ROC 曲线下的面积, 是阈值无关的综合评估。AUC=1.0 完美分类, AUC=0.5 随机猜测。AUC 优势: 不受类别不平衡影响 (与 accuracy 形成对照, 见 MJ01 类别不平衡时 accuracy 失效)。

## 4.3 业务案例: 医疗辅助诊断

某医院想用 AI 辅助识别早期肺结节。CT 影像样本 10000 例, 真阳率 (有结节) 5%。

**业务定调**: 漏掉一个结节患者代价 (延误治疗) 远高于误判健康人多做一次复查。Recall > Precision, 阈值要调低。

**若 T=0.5 (默认)**: TP=400, FP=50, TN=9450, FN=100。
- Accuracy = 9850/10000 = 98.5% (看似漂亮)
- Recall = 400/(400+100) = 80% (漏了 20% 的患者)
- Precision = 400/(400+50) = 89%

**调到 T=0.3**: TP=480, FP=300, TN=9200, FN=20。
- Accuracy = 9680/10000 = 96.8% (反而下降)
- Recall = 480/(480+20) = 96% (大幅提升)
- Precision = 480/(480+300) = 61.5% (下降但可接受)

业务接受: 多让 250 个健康人复查 (FP 增 250) 换来多救 80 个患者 (Recall 从 80% → 96%)。这就是 Recall 优先场景的阈值选择逻辑。

## 4.4 决策树 vs 逻辑回归 何时选哪个

- **特征间有强非线性交互, 业务要规则可解释**: 决策树
- **特征大致线性、需要校准的概率输出**: 逻辑回归
- **可解释性次要、追求性能**: 后续课程介绍的进阶模型

$v$,
        $v${"questions": [{"id": "q04-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj04.py 中的 4 个函数; 评测以 test_mj04.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_sig_positive_two$v$, $v$sigmoid(2) ≈ 0.8808 (避免 0 这种被 hardcode 0.5 命中的输入)$v$, false, $v$sigmoid(2) ≈ 0.8808 (避免 0 这种被 hardcode 0.5 命中的输入)$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_sig_three_values$v$, $v$[0, 1, -1] → [0.5, 0.7311, 0.2689]$v$, false, $v$[0, 1, -1] → [0.5, 0.7311, 0.2689]$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_sig_extreme_values$v$, $v$[10, -10] → 接近 (1, 0)$v$, false, $v$[10, -10] → 接近 (1, 0)$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_sig_half_values$v$, $v$[0.5, -0.5] → [~0.622, ~0.378]$v$, false, $v$[0.5, -0.5] → [~0.622, ~0.378]$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_sig_empty$v$, $v$边界: 空列表 → 空列表$v$, false, $v$边界: 空列表 → 空列表$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_sig_negative_extreme$v$, $v$边界: 单个极小值 → 接近 0$v$, false, $v$边界: 单个极小值 → 接近 0$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_sig_raises_on_non_list$v$, $v$负例: 非 list → TypeError$v$, false, $v$负例: 非 list → TypeError$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_sig_raises_on_non_numeric$v$, $v$负例: 含非数值元素 → TypeError$v$, false, $v$负例: 含非数值元素 → TypeError$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_cm_all_correct$v$, $v$cm all correct$v$, false, $v$cm all correct$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_cm_all_wrong$v$, $v$cm all wrong$v$, false, $v$cm all wrong$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_cm_mixed$v$, $v$cm mixed$v$, false, $v$cm mixed$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_cm_unbalanced$v$, $v$y_true=[1]*5+[0]*5, y_pred=[1]*8+[0]*2$v$, false, $v$y_true=[1]*5+[0]*5, y_pred=[1]*8+[0]*2$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_cm_all_negative$v$, $v$cm all negative$v$, false, $v$cm all negative$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_cm_raises_on_empty$v$, $v$边界: 空 → ValueError$v$, false, $v$边界: 空 → ValueError$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_cm_raises_on_length_mismatch$v$, $v$边界: 长度不一致 → ValueError$v$, false, $v$边界: 长度不一致 → ValueError$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_cm_raises_on_non_list$v$, $v$负例: 非 list → TypeError$v$, true, $v$负例: 非 list → TypeError$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_m_typical$v$, $v$tp=50, fp=10, tn=30, fn=10: acc=0.8, p≈0.833, r≈0.833, f1≈0.833$v$, true, $v$tp=50, fp=10, tn=30, fn=10: acc=0.8, p≈0.833, r≈0.833, f1≈0.833$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_m_perfect$v$, $v$tp=10, fp=0, tn=90, fn=0: 全 1.0$v$, true, $v$tp=10, fp=0, tn=90, fn=0: 全 1.0$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_m_zero_tp_with_fp$v$, $v$tp=0, fp=100, tn=0, fn=0: acc=0, p=0, r 除零应为 0$v$, true, $v$tp=0, fp=100, tn=0, fn=0: acc=0, p=0, r 除零应为 0$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_m_balanced_half$v$, $v$tp=fp=tn=fn=5: 全 0.5$v$, true, $v$tp=fp=tn=fn=5: 全 0.5$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_m_raises_on_all_zero$v$, $v$边界: 全 0 → ValueError$v$, true, $v$边界: 全 0 → ValueError$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_m_raises_on_negative$v$, $v$边界: 负数 → ValueError$v$, true, $v$边界: 负数 → ValueError$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_m_raises_on_non_int$v$, $v$负例: 非整数 → TypeError$v$, true, $v$负例: 非整数 → TypeError$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_cbt_basic$v$, $v$[0.1, 0.5, 0.9], threshold=0.5 → [0, 1, 1] (>= 边界判 1)$v$, true, $v$[0.1, 0.5, 0.9], threshold=0.5 → [0, 1, 1] (>= 边界判 1)$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_cbt_near_extremes$v$, $v$[0.05, 0.95], threshold=0.5 → [0, 1] (避免 0.0/1.0 与整数 0/1 等值的 D 巧合)$v$, true, $v$[0.05, 0.95], threshold=0.5 → [0, 1] (避免 0.0/1.0 与整数 0/1 等值的 D 巧合)$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_cbt_at_boundary$v$, $v$[0.5, 0.5], threshold=0.5 → [1, 1] (>= 严格大于等于)$v$, true, $v$[0.5, 0.5], threshold=0.5 → [1, 1] (>= 严格大于等于)$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_cbt_around_threshold$v$, $v$[0.4, 0.6], threshold=0.5 → [0, 1]$v$, true, $v$[0.4, 0.6], threshold=0.5 → [0, 1]$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_cbt_high_threshold$v$, $v$[0.1, 0.5, 0.9], threshold=0.95 → [0, 0, 0]$v$, true, $v$[0.1, 0.5, 0.9], threshold=0.95 → [0, 0, 0]$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_cbt_negative_with_zero_threshold$v$, $v$[-0.5, 0.5], threshold=0.0 → [0, 1]$v$, true, $v$[-0.5, 0.5], threshold=0.0 → [0, 1]$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_cbt_empty$v$, $v$边界: 空列表 → 空列表$v$, true, $v$边界: 空列表 → 空列表$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_cbt_raises_on_non_list$v$, $v$负例: scores 非 list → TypeError$v$, true, $v$负例: scores 非 list → TypeError$v$, NULL, 31)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
