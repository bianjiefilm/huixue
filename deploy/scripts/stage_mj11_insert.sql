-- ============================================================
-- MJ11: 集成学习与模型融合
-- practice_id=7, order_in_practice=11
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$集成学习与模型融合$v$,
        'PRACTICE',
        11,
        $v$advanced$v$,
        $v$## 集成学习的全景

## 1.1 三大集成路线

MJ05 已介绍了 Bagging 与 Boosting 的两种核心思想; 本关把视角抬高, 引入第三条路线 **Stacking** (堆叠), 并系统看四种集成模式如何组合多个基础模型:

| 路线 | 思想 | 代表算法 |
|------|------|----------|
| Bagging | 并行训练 + 多数表决 | 随机森林 |
| Boosting | 串行训练 + 错误修正 | AdaBoost / GBDT / XGBoost |
| Voting | 不同算法投票 | sklearn VotingClassifier |
| Stacking | 不同算法 + 元学习器二次学习 | sklearn StackingClassifier |

## 1.2 多个模型为什么比单个好

集成学习的数学根基是**误差分解**:
$\text{Total Error} = \text{Bias}^2 + \text{Variance} + \text{Irreducible Noise}$

- Bagging 主要降 Variance (多个模型独立, 错误不相关, 平均后波动小)
- Boosting 主要降 Bias (序列学习把欠拟合部分逐步补上)
- Stacking 同时利用不同模型族的互补能力

经验上, 同一个数据集, **集成模型平均比最强单模型高 2-5 个百分点**, 这是为什么 Kaggle 比赛、广告点击预测、信用评分等性能敏感场景都用集成方案。


## Bagging 与多数表决

## 2.1 多数表决的两种规则

给定 K 个基础模型对 N 个样本的预测 (形状 K × N), 综合策略分两种:
- **硬投票**: 每个模型给一个标签, 取出现次数最多的
- **软投票**: 每个模型给一个概率, 取均值后再阈值

硬投票适合所有基础模型都给标签的场景, 软投票适合所有基础模型都给概率的场景。当 K 是偶数且票数对半时是平票, 必须明确规则 (本关约定取数值最小的类)。

## 2.2 加权投票

不是所有基础模型都同等可信。如果某个模型的 CV 分数显著高, 应该给它更高权重。**加权软投票** 公式:

$\hat{y}_s = \mathbb{1}\left[\frac{\sum_e w_e \cdot \hat{p}_{e,s}}{\sum_e w_e} \geq T\right]$

其中 $\hat{p}_{e,s}$ 是模型 $e$ 对样本 $s$ 的预测 (0/1 或概率), $w_e$ 是该模型的权重, $T$ 是阈值 (默认 0.5)。

权重选择经验:
- 等权: 一视同仁, 安全但保守
- 反比 OOB 误差: 误差小的模型权重大, 工程上常用
- 训练时学习: Stacking 的元学习器自动学习

## 2.3 OOB 评估在 Bagging 中的作用

MJ05 提过 Bootstrap 平均约 36.8% 样本未被抽到 (Out-Of-Bag, OOB)。Bagging 训练完每棵树后, 用该树的 OOB 样本计算它的"独立验证误差", 平均所有树的 OOB 误差就得到一个**不需要单独划分验证集**的内部评估。这是 RF 的实务优势, 节省了一次 K 折成本。


## Stacking: 元学习器二次学习

## 3.1 Stacking 架构

Stacking 比 Voting 复杂一层: 不只是平均/投票, 而是**让另一个模型 (元学习器, meta-learner) 学习如何组合基础模型的输出**:

```
输入 X
  │
  ├──→ 基础模型 1 (RF) ──→ 概率 p_1 ──┐
  ├──→ 基础模型 2 (LR) ──→ 概率 p_2 ──┼──→ 元学习器 (LR) ──→ 最终预测
  └──→ 基础模型 3 (KNN) ──→ 概率 p_3 ──┘
```

关键设计:
- 基础模型用 K 折产生**外样本预测**作为元学习器输入 (不能用同样数据训元学习器, 否则严重过拟合)
- 元学习器通常选简单模型 (LR / 浅 RF), 防止再过拟合一层
- 实务上 3-5 个差异化基础模型 + 1 个元学习器是性价比最高配置

## 3.2 Stacking 的核心计算

给定 N 个样本对 K 个基础模型的概率输出 (shape N × K) 与元学习器的权重 (shape K), 元学习器的线性组合输出:

$\text{stacked}_s = \sum_{e=1}^{K} w_e \cdot p_{e,s}$

最终标签由 stacked 的阈值 (默认 0.5) 决定。

## 3.3 常见陷阱

- **泄漏**: 用训练数据本身预测训元学习器, 元学习器学到"基础模型见过这条样本"的信号 → 测试集崩盘
- **基础模型同质**: 3 个 RF 即使参数不同, 错误模式相似, Stacking 提升有限。要选不同算法族 (树类 + 线性类 + 距离类)
- **元学习器太复杂**: 元学习器用深度网络反而过拟合, 简单 LR 通常最好


## Boosting 序列叠加与业务案例

## 4.1 Boosting 的递增公式

Boosting 的最终预测是各阶段预测的加权和:

$\hat{y}_s = \eta \sum_{t=1}^{T} f_t(\mathbf{x}_s)$

其中 $\eta$ 是学习率 (步长), $f_t$ 是第 $t$ 棵树。学习率小, 单步贡献小, 但需要更多树才收敛 — 这是经典的**学习率与树数反向调**关系。

## 4.2 AdaBoost 与 GBDT 的差别

| 算法 | 错误修正方式 |
|------|-------------|
| AdaBoost | 给错分样本加权, 下一轮加权采样 |
| GBDT | 拟合上一轮的残差 (梯度方向) |
| XGBoost | GBDT + 二阶梯度 + 正则 + 工程优化 |

三者本质都是"逐步降偏差", 区别是错误的形式化方式不同。AdaBoost 适合简单弱分类器 (决策桩), GBDT/XGBoost 适合中等深度树 (5-8 层) 做更复杂任务。

## 4.3 业务案例: 金融多模型融合

某券商建一个交易信号预测模型, 单模型 AUC 0.72-0.75 (RF / LR / XGBoost 各一个), 客户业务上希望进一步提升。

**方案 A: Voting 加权投票**
- 对 RF / LR / XGBoost 各 OOB-AUC 反比设权重 (0.4, 0.2, 0.4)
- 加权软投票, 整体 AUC 0.78 (+3-6 点)

**方案 B: Stacking 元学习器**
- 基础: RF / LR / XGBoost / KNN 4 个差异化模型
- 元学习: 简单 LR 用 5 折产生的外样本概率作为输入
- 整体 AUC 0.81 (+9 点)

Stacking 进一步提升的代价: 训练复杂度上升 (5 折 × 4 基础 = 20 次基础训练 + 1 次元学习训练), 推理时 4 个基础模型各跑一次, 延迟增加 4 倍。业务上若延迟敏感 (高频交易), 用 Voting; 若延迟可接受 (盘后批量信号), 用 Stacking。

## 4.4 工程提醒

- **不要嵌套太深**: Stacking 套 Stacking 在工程上几乎一定过拟合, 收益微乎其微
- **基础模型要差异化**: 3 个 RF 不是 ensemble, 是冗余
- **生产监控**: 集成模型的某个组件挂掉 (例如 XGBoost 训练崩) 不能让整体推理失败 — 设计 graceful fallback
- **可解释性下降**: 单棵 DT 可读, 50 棵树 + Stacking + Voting 几乎不可读, 高解释场景 (信贷拒绝) 慎用

$v$,
        $v${"questions": [{"id": "q11-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj11.py 中的 4 个函数; 评测以 test_mj11.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_bp_user_example$v$, $v$base_preds=[[0,1,1],[1,1,0],[1,1,1]] → 列多数 [1,1,1]$v$, false, $v$base_preds=[[0,1,1],[1,1,0],[1,1,1]] → 列多数 [1,1,1]$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_bp_first_estimator_minority$v$, $v$base_preds=[[1,1],[0,0],[0,0]] 第一估计器全错, 多数投 0 → [0,0] (b[0] 与结果不一致防 D 巧合)$v$, false, $v$base_preds=[[1,1],[0,0],[0,0]] 第一估计器全错, 多数投 0 → [0,0] (b[0] 与结果不一致防 D 巧合)$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_bp_unanimous_mixed$v$, $v$base_preds=[[0],[1],[1]] (2/3 投 1) → [1] (b[0]=[0] 与 majority 不一致)$v$, false, $v$base_preds=[[0],[1],[1]] (2/3 投 1) → [1] (b[0]=[0] 与 majority 不一致)$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_bp_tie_smaller$v$, $v$base_preds=[[0,1],[1,0]] 列 0: 0+1 平票 → 0; 列 1: 1+0 平票 → 0$v$, false, $v$base_preds=[[0,1],[1,0]] 列 0: 0+1 平票 → 0; 列 1: 1+0 平票 → 0$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_bp_three_estimators_three_samples$v$, $v$base_preds=[[1,0,0],[0,1,1],[1,1,0]] 列 0: 1+0+1=2 → 1; 列 1: 0+1+1=2 → 1; 列 2: 0+1+0=1 → 0 预期 [1,1,0]$v$, false, $v$base_preds=[[1,0,0],[0,1,1],[1,1,0]] 列 0: 1+0+1=2 → 1; 列 1: 0+1+1=2 → 1; 列 2: 0+1+0=1 → 0 预期 [1,1,0]$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_bp_raises_on_empty$v$, $v$bp raises on empty$v$, false, $v$bp raises on empty$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_bp_raises_on_inconsistent_rows$v$, $v$bp raises on inconsistent rows$v$, false, $v$bp raises on inconsistent rows$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_bp_raises_on_non_list$v$, $v$bp raises on non list$v$, false, $v$bp raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_wv_user_example$v$, $v$base_preds=[[0,1,1],[1,1,0]] weights=[0.3,0.7] (调整以避 b[0]=expected D 巧合) s0: 0*0.3+1*0.7=0.7 >= 0.5 → 1 s1: 1*0.3+1*0.7=1.0 >= 0.5 → 1 s2: 1*0.3+0*0.7=0.3 < 0.5 → 0 expected [1, 1, 0] 与 b[0]=[0,1,1] 不$v$, false, $v$base_preds=[[0,1,1],[1,1,0]] weights=[0.3,0.7] (调整以避 b[0]=expected D 巧合) s0: 0*0.3+1*0.7=0.7 >= 0.5 → 1 s1: 1*0.3+1*0.7=1.0 >= 0.5 → 1 s2: 1*0.3+0*0.7=0.3 < 0.5 → 0 expected [1, 1, 0] 与 b[0]=[0,1,1] 不$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_wv_dominant_first$v$, $v$weights=[1.0, 0.0] base_preds=[[1,0],[0,1]] → 完全由第一个估计器决定 → [1,0]$v$, false, $v$weights=[1.0, 0.0] base_preds=[[1,0],[0,1]] → 完全由第一个估计器决定 → [1,0]$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_wv_dominant_second$v$, $v$weights=[0.0, 1.0] base_preds=[[1,0],[0,1]] → [0,1]$v$, false, $v$weights=[0.0, 1.0] base_preds=[[1,0],[0,1]] → [0,1]$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_wv_balanced_50_50$v$, $v$weights=[0.5,0.5] base_preds=[[0,1],[1,0]] → 都等于 0.5, 阈值 >=0.5 → [1,1]$v$, false, $v$weights=[0.5,0.5] base_preds=[[0,1],[1,0]] → 都等于 0.5, 阈值 >=0.5 → [1,1]$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_wv_three_estimators$v$, $v$weights=[0.5, 0.3, 0.2] base_preds=[[1,0,0],[1,1,0],[0,1,1]] s0: 1*0.5+1*0.3+0*0.2=0.8 → 1 s1: 0*0.5+1*0.3+1*0.2=0.5 → 1 (>=0.5) s2: 0*0.5+0*0.3+1*0.2=0.2 → 0 expected [1,1,0]$v$, false, $v$weights=[0.5, 0.3, 0.2] base_preds=[[1,0,0],[1,1,0],[0,1,1]] s0: 1*0.5+1*0.3+0*0.2=0.8 → 1 s1: 0*0.5+1*0.3+1*0.2=0.5 → 1 (>=0.5) s2: 0*0.5+0*0.3+1*0.2=0.2 → 0 expected [1,1,0]$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_wv_raises_on_empty$v$, $v$wv raises on empty$v$, false, $v$wv raises on empty$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_wv_raises_on_dim_mismatch$v$, $v$wv raises on dim mismatch$v$, false, $v$wv raises on dim mismatch$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_wv_raises_on_non_list$v$, $v$wv raises on non list$v$, false, $v$wv raises on non list$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_sp_basic$v$, $v$base_probs=[[0.8,0.2],[0.3,0.7]] meta_weights=[0.6,0.4] s0: 0.8*0.6+0.2*0.4 = 0.48+0.08 = 0.56 s1: 0.3*0.6+0.7*0.4 = 0.18+0.28 = 0.46$v$, true, $v$base_probs=[[0.8,0.2],[0.3,0.7]] meta_weights=[0.6,0.4] s0: 0.8*0.6+0.2*0.4 = 0.48+0.08 = 0.56 s1: 0.3*0.6+0.7*0.4 = 0.18+0.28 = 0.46$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_sp_single_estimator$v$, $v$meta_weights=[1.0] → 回显 base_probs[:, 0]$v$, true, $v$meta_weights=[1.0] → 回显 base_probs[:, 0]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_sp_zero_weights$v$, $v$meta_weights=[0,0] → 全 0 输出$v$, true, $v$meta_weights=[0,0] → 全 0 输出$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_sp_three_estimators$v$, $v$3 estimators, 2 samples$v$, true, $v$3 estimators, 2 samples$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_sp_negative_weights$v$, $v$meta_weights 含负值 (元学习器学到反向贡献)$v$, true, $v$meta_weights 含负值 (元学习器学到反向贡献)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_sp_raises_on_empty$v$, $v$sp raises on empty$v$, true, $v$sp raises on empty$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_sp_raises_on_dim_mismatch$v$, $v$sp raises on dim mismatch$v$, true, $v$sp raises on dim mismatch$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_sp_raises_on_non_list$v$, $v$sp raises on non list$v$, true, $v$sp raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_bc_lr_one$v$, $v$stage_preds=[[0.5,0.7],[0.3,0.4]] lr=1.0 → [0.8, 1.1]$v$, true, $v$stage_preds=[[0.5,0.7],[0.3,0.4]] lr=1.0 → [0.8, 1.1]$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_bc_lr_half$v$, $v$stage_preds=[[0.5,0.7],[0.3,0.4]] lr=0.5 → [0.4, 0.55]$v$, true, $v$stage_preds=[[0.5,0.7],[0.3,0.4]] lr=0.5 → [0.4, 0.55]$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_bc_three_stages$v$, $v$stage_preds=[[0.1],[0.2],[0.3]] lr=0.5 → [0.5*(0.1+0.2+0.3)]=[0.3]$v$, true, $v$stage_preds=[[0.1],[0.2],[0.3]] lr=0.5 → [0.5*(0.1+0.2+0.3)]=[0.3]$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_bc_single_stage$v$, $v$stage_preds=[[1.0, 2.0]] lr=1.0 → [1.0, 2.0]$v$, true, $v$stage_preds=[[1.0, 2.0]] lr=1.0 → [1.0, 2.0]$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_bc_lr_zero$v$, $v$lr=0 → 全 0$v$, true, $v$lr=0 → 全 0$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_bc_raises_on_empty$v$, $v$bc raises on empty$v$, true, $v$bc raises on empty$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_bc_raises_on_inconsistent_rows$v$, $v$bc raises on inconsistent rows$v$, true, $v$bc raises on inconsistent rows$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_bc_raises_on_non_list$v$, $v$bc raises on non list$v$, true, $v$bc raises on non list$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
