-- NN8: 正则化与 Dropout
-- practice_id=8, order_in_practice=8, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$正则化与 Dropout$v$,
        'PRACTICE',
        8,
        $v$advanced$v$,
        $v$## 过拟合的本质与正则化

## 1.1 过拟合的两种症状

过拟合 = 模型在训练集上完美, 在验证/测试集上表现差。两个观察症状:
- **gap 大**: train_loss 0.05, val_loss 0.30 → gap 0.25 (远大于自然波动 0.02-0.05)
- **val_loss 不再下降**: 训练继续 train_loss 持续降, val_loss 反而上升 → 模型在记忆训练噪声

MJ01 已用单一标量 gap 诊断过拟合。NN08 引入更精细工具: 通过损失"长期序列"判断 + 通过权重正则化"防止过拟合于源头"。

## 1.2 正则化思路

给损失函数加一个"惩罚权重幅度"的项:

$L_{\text{total}}(W) = L_{\text{data}}(W) + \alpha \cdot R(W)$

$R(W)$ 是正则项, $\alpha$ 控制强度。直觉: 模型可以选择"完美拟合训练 (大权重)"或"折中拟合 + 小权重", 加正则项后后者损失更低, 模型偏向后者。

$R(W)$ 两个常见形式:
- **L1**: $R(W) = \sum_i |w_i|$, 鼓励稀疏 (很多权重压到 0)
- **L2**: $R(W) = \sum_i w_i^2$, 鼓励小权重但非零

$\alpha$ 调参: 太小 (1e-6) 几乎无效; 太大 (1) 训练崩 (权重被压死); 经验起点 1e-4 ~ 1e-3。


## L1 vs L2 的几何与工程含义

## 2.1 L1 鼓励稀疏

L1 的等高线在 2D 中是菱形, 顶点在坐标轴上。最优解倾向 "落在菱形顶点", 即某些维度精确为 0。这等价于自动特征选择 — 模型学到"哪些权重不重要"并把它们设 0。

工程实务: 高维场景 (输入特征数 > 1000), L1 让模型只关注少数关键特征, 提升可解释性。

## 2.2 L2 鼓励小权重

L2 的等高线是圆, 与损失等高线相切的点权重幅度更小 (但通常都非零)。这等价于"温和均匀地缩小所有权重"。

工程实务: 通用首选, 默认在大多数 NN 训练中加 L2 (PyTorch 的 weight_decay 参数就是 L2 系数)。

## 2.3 ElasticNet 与权重衰减

- **ElasticNet**: $\alpha_1 |w| + \alpha_2 w^2$, 兼具稀疏性与小权重
- **权重衰减 (weight decay)**: 与 L2 数学等价, 但实现是直接在每步更新时 $W \leftarrow (1 - \eta \alpha) W - \eta \nabla L$

工程上 weight_decay 与 L2 通常等价, 但与 NN07 提到的某些自适应优化器配合时数学不完全等价 (有 Decoupled Weight Decay 之类的变种)。


## Dropout: 训练时随机置零

## 3.1 Dropout 的核心思想

Dropout 在训练时, 对每个神经元的输出按概率 $p$ 置零 (drop), 输出乘 $\frac{1}{1-p}$ 缩放 (Inverted Dropout, 让期望不变):

```
mask ~ Bernoulli(1-p)        # 1 = keep, 0 = drop
a_dropped = a * mask / (1-p)
```

推理 (inference) 时不 dropout, 直接用全部神经元。

直觉: 训练时随机"残疾"一部分神经元, 让网络不能依赖任何单一神经元, 学出冗余/鲁棒的表示。

## 3.2 Dropout 的两个工程作用

- **防过拟合**: 等价于训练 $2^N$ 个不同子网络的隐式集成 (NN05 集成思想)
- **稀疏激活**: 强迫每个神经元独立学到有用特征, 减少 co-adaptation

## 3.3 经验设置

- **drop_rate**: 0.2 (大网络) ~ 0.5 (浅网络)。中间层用; **输出层不要 dropout**, 否则推理时分布偏移
- **训练 / 推理切换**: 框架有 model.train() / model.eval() 模式, 自动处理 dropout 开关
- **与 BN 的位置**: Dropout 后接 BN (后续课程介绍) 反而会破坏统计稳定, 实务一般 BN 后再 Dropout

## 3.4 数值稳定提醒

drop_rate = 1.0 全部置零, 整层失能; drop_rate = 0 退化为 identity。两个边界值都会让训练崩, 工程实现应在合理区间 (0, 0.7) 内。


## 过拟合诊断与业务案例

## 4.1 训练/验证损失序列的 4 种典型形态

| 形态 | 描述 | 诊断 | 行动 |
|------|------|------|------|
| A | train ↘ val ↘ 接近 | 健康 | 继续训练 |
| B | train ↘ val ↘↑ 拐头 | 早期过拟合 | 早停 / 加正则 |
| C | train ↘ val 平 / 噪声 | 验证集太小 / 不稳定 | 增 val 比例 |
| D | train 持续 ≈ val | 数据少 / 任务简单 | 模型已收敛, 上线 |

自动诊断的简易判断:
- **过拟合信号**: val_loss 连续 patience 步未改善 (差异 < min_delta)
- **欠拟合信号**: train_loss 几个 epoch 后仍接近随机水平
- **gap 信号**: |train_loss - val_loss| > threshold

## 4.2 业务案例: 图像分类训练曲线诊断

某 CV 任务 50 epoch 训练, val 损失曲线:
- epoch 1-10: train 0.8 → 0.4, val 0.85 → 0.5 (健康下降)
- epoch 10-20: train 0.4 → 0.15, val 0.5 → 0.45 (val 下降变缓)
- epoch 20-30: train 0.15 → 0.05, val 0.45 → 0.48 (val 反弹, 过拟合)

诊断: epoch 22 是最佳模型 (val_loss 最低)。后续应:
- 早停: 保留 epoch 22 的权重
- 加正则: 加 L2 (alpha=1e-4) 或 Dropout (rate=0.3)
- 增数据: 数据扩充 (augmentation, 后续课程展开) 通常比正则化更有效

## 4.3 工程口诀

- **正则化是兜底, 不是首选**: 数据足够时优先增数据; 数据不足时再加正则
- **L2 通用, L1 用于特征选择**: 不知道选什么 → L2; 想要稀疏权重 → L1
- **Dropout 与 BN 之间**: BN 之后再 Dropout, 不要反过来
- **Train ≠ Inference**: 训练和推理时 dropout 行为不同, 是 NN 工程的常见 bug 来源

$v$,
        $v${"questions": [{"id": "q08-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn08.py 中的 4 个函数; 评测以 test_nn08.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_l1_basic$v$, $v$[1, -2, 3] alpha=0.1 → 0.1 * (1+2+3) = 0.6$v$, false, $v$[1, -2, 3] alpha=0.1 → 0.1 * (1+2+3) = 0.6$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_l1_zero_weights$v$, $v$全 0 → 0$v$, false, $v$全 0 → 0$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_l1_zero_alpha$v$, $v$alpha=0 → 0$v$, false, $v$alpha=0 → 0$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_l1_negative_weights$v$, $v$[-1, -2, -3] alpha=1.0 → 1.0 * (1+2+3) = 6$v$, false, $v$[-1, -2, -3] alpha=1.0 → 1.0 * (1+2+3) = 6$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_l1_decimals$v$, $v$[0.5, -0.5, 0.25] alpha=2.0 → 2.0 * 1.25 = 2.5$v$, false, $v$[0.5, -0.5, 0.25] alpha=2.0 → 2.0 * 1.25 = 2.5$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_l1_raises_on_empty$v$, $v$l1 raises on empty$v$, false, $v$l1 raises on empty$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_l1_raises_on_negative_alpha$v$, $v$l1 raises on negative alpha$v$, false, $v$l1 raises on negative alpha$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_l1_raises_on_non_list$v$, $v$l1 raises on non list$v$, false, $v$l1 raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_l2_basic$v$, $v$[1, -2, 3] alpha=0.1 → 0.1 * (1+4+9) = 1.4$v$, false, $v$[1, -2, 3] alpha=0.1 → 0.1 * (1+4+9) = 1.4$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_l2_zero_weights$v$, $v$l2 zero weights$v$, false, $v$l2 zero weights$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_l2_zero_alpha$v$, $v$l2 zero alpha$v$, false, $v$l2 zero alpha$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_l2_known_simple$v$, $v$[2, 2] alpha=0.5 → 0.5 * (4+4) = 4$v$, false, $v$[2, 2] alpha=0.5 → 0.5 * (4+4) = 4$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_l2_decimals$v$, $v$[0.1, 0.2] alpha=10 → 10 * (0.01 + 0.04) = 0.5$v$, false, $v$[0.1, 0.2] alpha=10 → 10 * (0.01 + 0.04) = 0.5$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_l2_raises_on_empty$v$, $v$l2 raises on empty$v$, false, $v$l2 raises on empty$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_l2_raises_on_negative_alpha$v$, $v$l2 raises on negative alpha$v$, false, $v$l2 raises on negative alpha$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_l2_raises_on_non_list$v$, $v$l2 raises on non list$v$, false, $v$l2 raises on non list$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_dropout_zero_rate_identity$v$, $v$drop_rate=0 → 输入不变 (除以 1)$v$, true, $v$drop_rate=0 → 输入不变 (除以 1)$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_dropout_deterministic_same_seed$v$, $v$同 seed 同输出$v$, true, $v$同 seed 同输出$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_dropout_different_seeds_differ$v$, $v$不同 seed 不同输出$v$, true, $v$不同 seed 不同输出$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_dropout_some_zeroed$v$, $v$drop_rate=0.5 大输入下应有一部分置零$v$, true, $v$drop_rate=0.5 大输入下应有一部分置零$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_dropout_kept_scaled$v$, $v$被保留的元素乘 1/(1-drop_rate)$v$, true, $v$被保留的元素乘 1/(1-drop_rate)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_dropout_raises_on_invalid_rate$v$, $v$dropout raises on invalid rate$v$, true, $v$dropout raises on invalid rate$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_dropout_raises_on_empty$v$, $v$dropout raises on empty$v$, true, $v$dropout raises on empty$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_dropout_raises_on_non_list$v$, $v$dropout raises on non list$v$, true, $v$dropout raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_cos_healthy$v$, $v$train ↘ val ↘ → has_overfit=False, gap 小$v$, true, $v$train ↘ val ↘ → has_overfit=False, gap 小$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_cos_overfit$v$, $v$val 在 epoch 4 最低后开始上升, patience=3 → has_overfit=True$v$, true, $v$val 在 epoch 4 最低后开始上升, patience=3 → has_overfit=True$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_cos_gap_signed$v$, $v$gap = train[-1] - val[-1]$v$, true, $v$gap = train[-1] - val[-1]$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_cos_best_val_first$v$, $v$val 第一个 epoch 就是最低 → best_val_epoch=0$v$, true, $v$val 第一个 epoch 就是最低 → best_val_epoch=0$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_cos_diverging_false_small_uptick$v$, $v$val 末尾仅小幅上升 (< 10%) → is_diverging=False$v$, true, $v$val 末尾仅小幅上升 (< 10%) → is_diverging=False$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_cos_raises_on_length_mismatch$v$, $v$cos raises on length mismatch$v$, true, $v$cos raises on length mismatch$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_cos_raises_on_empty$v$, $v$cos raises on empty$v$, true, $v$cos raises on empty$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_cos_raises_on_non_list$v$, $v$cos raises on non list$v$, true, $v$cos raises on non list$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
