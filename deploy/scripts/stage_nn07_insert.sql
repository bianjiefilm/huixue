-- NN7: 优化算法
-- practice_id=8, order_in_practice=7, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$优化算法$v$,
        'PRACTICE',
        7,
        $v$advanced$v$,
        $v$## 为什么需要超越 SGD

## 1.1 SGD 的简洁公式

SGD (Stochastic Gradient Descent, 随机梯度下降) 是 NN04 介绍的基础形式:

$W_{t+1} = W_t - \eta \cdot \nabla L(W_t)$

"随机"指每次只用一个 mini-batch 计算梯度, 而不是完整数据集。这让训练大数据可行, 但也带来噪声。

## 1.2 SGD 的三个工程问题

- **方向震荡**: 损失曲面沿不同方向曲率不同时, SGD 在窄方向上震荡, 难以快速沿宽方向前进
- **学习率敏感**: 太大爆炸, 太小慢, 整个训练用同一个 $\eta$ 不灵活
- **平坦区慢**: 损失曲面趋平时梯度小, SGD 几乎停滞

解决思路两条:
1. **加动量**: 保留历史方向, 平滑震荡 → Momentum / Nesterov
2. **自适应学习率**: 不同参数用不同的有效学习率 → AdaGrad / RMSProp / Adam

Adam 是两条思路的合并, 是当前工程默认选择。

## 1.3 三种优化器的对比

| 算法 | 状态变量 | 计算成本 | 何时优于 SGD |
|------|---------|---------|--------------|
| SGD | 无 | 1× | 简单凸问题 |
| Momentum | $_v_$ | 1× | 损失曲面有狭谷震荡 |
| Adam | $m, v$ | 2× | 不知道用什么时的安全选择 |

工程口诀: **不知道选什么 → Adam**; **追求最终精度 → SGD + Momentum + 仔细调 lr**; **追求速度 → Adam**。


## Momentum: 引入历史方向

## 2.1 公式

给定上一步速度 $v_{t-1}$ 与当前梯度 $dW$, 速度与权重更新:

$v_t = \mu \cdot v_{t-1} + dW$

$W_t = W_{t-1} - \eta \cdot v_t$

其中 $\mu \in [0, 1)$ 是动量系数, 常用 0.9 或 0.95。$\mu = 0$ 退化为 SGD。

## 2.2 直观解释

把优化想象成"球滚下损失曲面":
- SGD: 球只看当前位置的坡度, 每步独立
- Momentum: 球有惯性, 累积过去几步的方向, 在窄方向上震荡互相抵消, 在宽方向上不断加速

实务效果: Momentum 通常比 SGD 收敛快 2-3 倍, 是 SGD 的"标准升级版"。

## 2.3 工程提醒

- 初始 $v_0 = 0$, 与权重形状一致
- $\mu = 0.9$ 是经验默认, 0.95+ 接近"过度记忆", 容易跳过最优
- 与学习率配合: $\mu$ 大时有效步长是 $\eta / (1 - \mu)$, 比 SGD 等效更大, 通常 $\eta$ 要相应调小


## Adam: 自适应学习率

## 3.1 一阶矩与二阶矩

Adam 维护两个状态:
- **一阶矩** $m_t$: 梯度的指数加权移动平均 (类似 Momentum 的 $_v_$, 但归一化方式不同)
- **二阶矩** $v_t$: 梯度平方的指数加权移动平均

更新公式:

$m_t = \beta_1 \cdot m_{t-1} + (1 - \beta_1) \cdot dW$
$v_t = \beta_2 \cdot v_{t-1} + (1 - \beta_2) \cdot dW^2$

其中 $\beta_1 = 0.9$, $\beta_2 = 0.999$ 是默认值。

## 3.2 偏差校正

初始 $m_0 = v_0 = 0$, 早期几步 $m_t$ 与 $v_t$ 偏向 0 (因为加权时 $(1 - \beta_1)$ 系数小)。Adam 用偏差校正:

$\hat{m}_t = \frac{m_t}{1 - \beta_1^t}$
$\hat{v}_t = \frac{v_t}{1 - \beta_2^t}$

其中 $t$ 是当前步数 (1-indexed)。$t$ 大时 $\beta^t \to 0$, 校正系数 $\to 1$, 偏差消失。

## 3.3 参数更新

$W_t = W_{t-1} - \eta \cdot \frac{\hat{m}_t}{\sqrt{\hat{v}_t} + \epsilon}$

$\epsilon$ 是数值稳定常数 (通常 $10^{-8}$), 防分母为 0。

关键洞察: 分母 $\sqrt{\hat{v}_t}$ 让"梯度大的方向" 自动收缩学习率, "梯度小的方向"自动放大学习率 — 这是 "自适应"的本质。

## 3.4 与 SGD 的对比

| 维度 | SGD | Adam |
|------|-----|------|
| 状态 | 无 | $m, v$ (内存 2× 模型大小) |
| lr 含义 | 全局统一步长 | 每参数自适应缩放 |
| 鲁棒 | 对 lr 极敏感 | 对 lr 较鲁棒 |
| 最终精度 | 调好后通常更高 | 略低 |

Adam 的"开箱即用"特性让它成为深度学习的默认选择, 但研究表明 SGD+Momentum 调好后在很多任务上反而表现更好。


## 学习率衰减与业务案例

## 4.1 学习率衰减的必要性

训练初期需要较大学习率快速逼近, 后期需要较小学习率精细调整。固定学习率两个阶段都不友好。学习率衰减让 $\eta$ 随训练进度自动减小。

## 4.2 三种常用衰减方式

给定 initial_lr $\eta_0$ 与当前 epoch $t$:

**Step decay (按步数下降)**:
$\eta = \eta_0 \cdot d^t$

其中 $d \in (0, 1)$ 是衰减率 (例如 0.95 / epoch)。最简单, 适合训练长度已知的场景。

**Exponential decay (指数衰减)**:
$\eta = \eta_0 \cdot e^{-d \cdot t}$

$d > 0$ 控制衰减速度 (例如 0.01)。比 step 更平滑。

**Inverse decay (倒数衰减)**:
$\eta = \frac{\eta_0}{1 + d \cdot t}$

下降比指数慢, 适合训练总长度不确定的场景。

## 4.3 业务案例: 图像分类训练

某 CV 任务训练一个深度图像分类网络, 数据 100K 样本, 训 50 epoch:

**方案 A**: 固定 lr=0.001 + Adam
- epoch 5 验证准确率 65%; epoch 20 → 78%; epoch 50 → 81% (收敛后慢慢爬)

**方案 B**: 初始 lr=0.01 + SGD + Momentum 0.9 + step decay 0.5/10 epoch
- epoch 5 验证 70% (快); epoch 20 (lr=0.0025) → 82%; epoch 50 (lr=0.000625) → 86% (+5 点)

方案 B 最终精度更高, 但需要仔细调 step decay 的步频与衰减率。这就是 SGD+Momentum 调好优于 Adam 的典型场景, 也是为什么 ImageNet / COCO 等大型 benchmark 的最优结果普遍用 SGD+Momentum。

## 4.4 工程口诀

- **训练不动: 调 lr 优先**, 90% 的训练失败是 lr 没调对
- **Adam vs SGD**: 业务方说 "尽快出 demo" → Adam; 业务方说 "刷 SOTA" → SGD+Momentum
- **lr decay 不是越多越好**: 训练初期就衰减太快会让网络学不到有用特征
- **lr warmup**: 训练最开始几百步用极小 lr 线性升至目标 lr, 是大模型训练的标准技巧 (后续课程展开)

$v$,
        $v${"questions": [{"id": "q07-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn07.py 中的 4 个函数; 评测以 test_nn07.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_sgd_textbook$v$, $v$W=[1,2,3] dW=[0.1,0.2,0.3] lr=10 → [0,0,0]$v$, false, $v$W=[1,2,3] dW=[0.1,0.2,0.3] lr=10 → [0,0,0]$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_sgd_negative_grad$v$, $v$W=[5] dW=[-2] lr=0.5 → [6]$v$, false, $v$W=[5] dW=[-2] lr=0.5 → [6]$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_sgd_small_lr$v$, $v$W=[10] dW=[1] lr=0.01 → [9.99]$v$, false, $v$W=[10] dW=[1] lr=0.01 → [9.99]$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_sgd_multi_param$v$, $v$W=[1,2,3,4] dW=[1,1,1,1] lr=0.5 → [0.5, 1.5, 2.5, 3.5]$v$, false, $v$W=[1,2,3,4] dW=[1,1,1,1] lr=0.5 → [0.5, 1.5, 2.5, 3.5]$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_sgd_raises_on_length_mismatch$v$, $v$sgd raises on length mismatch$v$, false, $v$sgd raises on length mismatch$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_sgd_raises_on_empty$v$, $v$sgd raises on empty$v$, false, $v$sgd raises on empty$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_sgd_raises_on_non_list$v$, $v$sgd raises on non list$v$, false, $v$sgd raises on non list$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_mom_first_step$v$, $v$v_prev=0, dW=1, mu=0.9, lr=0.1 → v=1, W_new = W - 0.1*1 W=[10] → W_new=[9.9], v=[1]$v$, false, $v$v_prev=0, dW=1, mu=0.9, lr=0.1 → v=1, W_new = W - 0.1*1 W=[10] → W_new=[9.9], v=[1]$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_mom_second_step$v$, $v$v_prev=[1], dW=[1], mu=0.9 → v_new = 0.9*1+1 = 1.9 W=[10] lr=0.1 → W_new = 10 - 0.1*1.9 = 9.81$v$, false, $v$v_prev=[1], dW=[1], mu=0.9 → v_new = 0.9*1+1 = 1.9 W=[10] lr=0.1 → W_new = 10 - 0.1*1.9 = 9.81$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_mom_zero_momentum_equals_sgd$v$, $v$mu=0 退化为 SGD: v_new = dW; W_new = W - lr*dW$v$, false, $v$mu=0 退化为 SGD: v_new = dW; W_new = W - lr*dW$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_mom_multi_param$v$, $v$W=[1,2], dW=[0.1,0.2], v_prev=[0,0], lr=1, mu=0.5 v = [0.1, 0.2]; W_new = [1-0.1, 2-0.2] = [0.9, 1.8]$v$, false, $v$W=[1,2], dW=[0.1,0.2], v_prev=[0,0], lr=1, mu=0.5 v = [0.1, 0.2]; W_new = [1-0.1, 2-0.2] = [0.9, 1.8]$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_mom_negative_grad$v$, $v$dW 负 → v 负 → W 增$v$, false, $v$dW 负 → v 负 → W 增$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_mom_raises_on_length_mismatch$v$, $v$mom raises on length mismatch$v$, false, $v$mom raises on length mismatch$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_mom_raises_on_empty$v$, $v$mom raises on empty$v$, false, $v$mom raises on empty$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_mom_raises_on_non_list$v$, $v$mom raises on non list$v$, false, $v$mom raises on non list$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_adam_first_step$v$, $v$t=1, m_prev=v_prev=0 m = 0.1*1 = 0.1; v = 0.001*1 = 0.001 m_hat = 0.1/(1-0.9) = 1; v_hat = 0.001/(1-0.999) = 1 W_new = W - lr * m_hat / (sqrt(v_hat)+eps) 取 W=[1], dW=[1], lr=0.001, b1=0.9, b2=0.999 W_$v$, true, $v$t=1, m_prev=v_prev=0 m = 0.1*1 = 0.1; v = 0.001*1 = 0.001 m_hat = 0.1/(1-0.9) = 1; v_hat = 0.001/(1-0.999) = 1 W_new = W - lr * m_hat / (sqrt(v_hat)+eps) 取 W=[1], dW=[1], lr=0.001, b1=0.9, b2=0.999 W_$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_adam_zero_grad$v$, $v$dW=0 → m=0, v=0, W 不变$v$, true, $v$dW=0 → m=0, v=0, W 不变$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_adam_known_step_t10$v$, $v$t=10, m_prev=v_prev=0, dW=1, lr=0.001 m = 0.1 (t=1 起算实际是 1 步, 但这里假设 t 直接给 10, m_prev 给 0) m_hat = 0.1 / (1 - 0.9^10) = 0.1 / 0.6513 ≈ 0.1535 v_hat = 0.001 / (1 - 0.999^10) ≈ 0.001 / 0.00996 ≈ 0.1004 W$v$, true, $v$t=10, m_prev=v_prev=0, dW=1, lr=0.001 m = 0.1 (t=1 起算实际是 1 步, 但这里假设 t 直接给 10, m_prev 给 0) m_hat = 0.1 / (1 - 0.9^10) = 0.1 / 0.6513 ≈ 0.1535 v_hat = 0.001 / (1 - 0.999^10) ≈ 0.001 / 0.00996 ≈ 0.1004 W$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_adam_dimensions_consistent$v$, $v$W=[1,2,3] → m, v, W_new 都是 3 元素$v$, true, $v$W=[1,2,3] → m, v, W_new 都是 3 元素$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_adam_raises_on_length_mismatch$v$, $v$adam raises on length mismatch$v$, true, $v$adam raises on length mismatch$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_adam_raises_on_zero_t$v$, $v$t 必须 >= 1 (防偏差校正除零)$v$, true, $v$t 必须 >= 1 (防偏差校正除零)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_adam_raises_on_non_list$v$, $v$adam raises on non list$v$, true, $v$adam raises on non list$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_lrd_step$v$, $v$step: 1.0 * 0.5^3 = 0.125$v$, true, $v$step: 1.0 * 0.5^3 = 0.125$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_lrd_step_epoch_zero$v$, $v$epoch=0 → 不衰减$v$, true, $v$epoch=0 → 不衰减$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_lrd_exp$v$, $v$exp: 1.0 * exp(-0.1*5) = exp(-0.5) ≈ 0.6065$v$, true, $v$exp: 1.0 * exp(-0.1*5) = exp(-0.5) ≈ 0.6065$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_lrd_inverse$v$, $v$inverse: 1.0 / (1 + 0.1*9) = 1/1.9 ≈ 0.5263$v$, true, $v$inverse: 1.0 / (1 + 0.1*9) = 1/1.9 ≈ 0.5263$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_lrd_decay_decreases$v$, $v$epoch 增 → lr 严格减$v$, true, $v$epoch 增 → lr 严格减$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_lrd_raises_on_negative_epoch$v$, $v$lrd raises on negative epoch$v$, true, $v$lrd raises on negative epoch$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_lrd_raises_on_invalid_type$v$, $v$lrd raises on invalid type$v$, true, $v$lrd raises on invalid type$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_lrd_raises_on_non_numeric$v$, $v$lrd raises on non numeric$v$, true, $v$lrd raises on non numeric$v$, NULL, 30)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
