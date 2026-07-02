-- NN4: 反向传播与梯度下降
-- practice_id=8, order_in_practice=4, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$反向传播与梯度下降$v$,
        'PRACTICE',
        4,
        $v$intermediate$v$,
        $v$## 为什么需要反向传播

## 1.1 训练神经网络的核心问题

网络有几百到几亿参数, 每个参数都需要"知道自己应该朝哪个方向调整、调多少"才能让损失下降。直接逐参数试探是不可能的 (一亿参数, 每个试 10 个值就是 $10^9$ 次评估)。

解决思路: **求出损失对每个参数的偏导数 (梯度)**, 然后让参数沿"负梯度方向"前进一小步, 损失就会下降。这个"求所有参数梯度"的算法就是反向传播 (Backpropagation)。

## 1.2 链式法则: 反向传播的数学根基

微积分的链式法则: 复合函数 $f(g(x))$ 关于 $x$ 的导数 = $f'(g(x)) \cdot g'(x)$。

神经网络是一个长长的复合函数: $L = \text{Loss}(\sigma_3(W_3 \sigma_2(W_2 \sigma_1(W_1 x))))$。要算 $\partial L / \partial W_1$, 必须从外到内逐层应用链式法则。

关键洞察: **算梯度的过程从输出向输入"反向"传播, 每一层把"上游梯度"和"本层局部偏导"相乘, 得到"下游梯度"**。这是 Backprop 名字的由来。

## 1.3 算梯度的两条路

数学上有两种求梯度的方式:
- **数值梯度**: $\nabla L \approx \frac{L(w + \epsilon) - L(w - \epsilon)}{2\epsilon}$。简单但每个参数要算 2 次前向, 一亿参数需要 2 亿次, 慢得不能用
- **解析梯度** (反向传播): 一次反向传播算完所有参数的梯度, 计算量约等于一次前向传播

工程实务: 训练永远用反向传播, 数值梯度仅用于"梯度检查" (用 1-2 个参数对比解析与数值, 验证实现正确)。


## Sigmoid 的导数与 MSE 梯度

## 2.1 Sigmoid 的导数

$\sigma(z) = \frac{1}{1 + e^{-z}}$

$\sigma'(z) = \sigma(z) \cdot (1 - \sigma(z))$

推导: 用商规则或者直接对 $1 + e^{-z}$ 求导。结果用 $\sigma$ 自身表达, 计算时把前向时存下的 $\sigma(z)$ 重用即可, 避免重复计算指数。

关键值:
- $\sigma'(0) = 0.5 \cdot (1 - 0.5) = 0.25$ (最大值)
- $\sigma'(\pm \infty) \to 0$ (饱和区)

工程提醒: $\sigma'$ 在 $|z| > 5$ 时几乎为 0, 这是 Sigmoid "饱和饿梯度"问题的数学本质 — 深度网络中间层用 Sigmoid, 反向传播经过几层就因为多个小数相乘"梯度消失"。这是 NN02 提到 ReLU 替代 Sigmoid 的根本原因之一。

## 2.2 MSE 损失的梯度

$L = \frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2$

对 $\hat{y}_i$ 求偏导:

$\frac{\partial L}{\partial \hat{y}_i} = \frac{2}{N}(\hat{y}_i - y_i)$

工程提醒: 不同框架有的省略 $1/N$ (报告 sum 而非 mean), 有的省略 2 (合并到学习率), 实现上要清楚自己的版本。本关约定: **MSE 梯度 = 2(ŷ-y)/N**, 与 mean 损失一致。


## 单神经元的反向公式

## 3.1 前向回顾

单神经元 (单样本): $z = \sum_{i=1}^{d} w_i x_i + b$, $\hat{y} = f(z)$

## 3.2 反向公式

给定 $\partial L / \partial z = dz$ (上游传来的梯度), 求三个本层局部梯度:

$\frac{\partial L}{\partial w_i} = dz \cdot x_i$ (向量化: $dw = dz \cdot \mathbf{x}$)

$\frac{\partial L}{\partial b} = dz$

$\frac{\partial L}{\partial x_i} = dz \cdot w_i$ (向量化: $dx = dz \cdot \mathbf{w}$)

推导很直观: $z = \mathbf{w} \cdot \mathbf{x} + b$, 关于 $w_i$ 的偏导是 $x_i$, 关于 $b$ 的偏导是 1, 关于 $x_i$ 的偏导是 $w_i$。乘上上游梯度 $dz$ 即得本层梯度。

## 3.3 多样本批量的扩展

$N$ 个样本同时反向: $dz$ 形状 $(N,)$, $X$ 形状 $(N, d)$, $w$ 形状 $(d,)$。

$dw = X^T \cdot dz$ (sum 各样本贡献), 形状 $(d,)$
$db = \sum_n dz_n$ (sum 各样本贡献), 标量
$dx = dz \otimes \mathbf{w}$, 形状 $(N, d)$

本关只要求单样本版本, 多样本扩展是后续章节内容。


## 梯度下降单步与业务案例

## 4.1 梯度下降公式

参数更新规则:

$w_{\text{new}} = w_{\text{old}} - \eta \cdot \frac{\partial L}{\partial w}$

其中 $\eta$ 是学习率 (步长)。同样的公式对所有参数 (W, b) 都适用 — 每个参数减去 (学习率 × 自己的梯度)。

关键直觉:
- 梯度方向是损失上升最快的方向, 所以**减号**让参数朝下降方向走
- $\eta$ 太小: 收敛极慢; $\eta$ 太大: 跳过最优解或发散
- 工程经验值: $\eta = 0.01 \sim 0.001$ (具体后续课程展开)

## 4.2 业务案例: 房价预测的一个 epoch 手算

复习 MJ06 房价线性回归: $\hat{y} = w \cdot \text{tenure} + b$ (单特征单输出)。

初始 $w = 0.5, b = 1.0, \eta = 0.01$, 一个样本 $(\text{tenure}=10, y=8)$。

**前向**: $\hat{y} = 0.5 \cdot 10 + 1 = 6$

**损失**: MSE = $(8-6)^2 / 1 = 4$

**反向**: $dz = 2(\hat{y} - y) / N = 2(6 - 8) / 1 = -4$
- $dw = dz \cdot x = -4 \cdot 10 = -40$
- $db = dz = -4$

**更新**: $w_{\text{new}} = 0.5 - 0.01 \cdot (-40) = 0.9$, $b_{\text{new}} = 1.0 - 0.01 \cdot (-4) = 1.04$

下次前向: $\hat{y} = 0.9 \cdot 10 + 1.04 = 10.04$, 离真值 8 的偏差从 -2 变成 +2.04 — 跳过了最优, 因为学习率偏大。这是单步直观体验, 实际训练用 mini-batch 多步迭代。

## 4.3 工程提醒

- **梯度爆炸**: 反向传播经过深网络时梯度可能指数级放大, 解决: 梯度裁剪 (clip) — 后续课程展开
- **梯度消失**: 反过来, 深网络底层梯度趋零学不动 — 跟激活函数选择 (NN02) 与初始化 (后续课程) 都有关
- **数值梯度检查**: 实现复杂反向时, 与 $\frac{L(w+\epsilon) - L(w-\epsilon)}{2\epsilon}$ 对比, 误差 $< 10^{-7}$ 才算正确
- **学习率最重要**: 调一个超参先调 $\eta$, 90% 的训练失败是 $\eta$ 没调对 — 后续优化算法课程会展开

$v$,
        $v${"questions": [{"id": "q04-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn04.py 中的 4 个函数; 评测以 test_nn04.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_sd_zero_max$v$, $v$σ'(0) = 0.5*0.5 = 0.25 (最大值)$v$, false, $v$σ'(0) = 0.5*0.5 = 0.25 (最大值)$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_sd_diverse$v$, $v$[0, 1, -1, 2, -2] 多组独特$v$, false, $v$[0, 1, -1, 2, -2] 多组独特$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_sd_extreme_saturation$v$, $v$[10, -10] 饱和区 σ' 接近 0$v$, false, $v$[10, -10] 饱和区 σ' 接近 0$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_sd_half_values$v$, $v$[0.5, -0.5]$v$, false, $v$[0.5, -0.5]$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_sd_empty$v$, $v$sd empty$v$, false, $v$sd empty$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_sd_raises_on_non_list$v$, $v$sd raises on non list$v$, false, $v$sd raises on non list$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_sd_raises_on_non_numeric$v$, $v$sd raises on non numeric$v$, false, $v$sd raises on non numeric$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_mg_perfect$v$, $v$y_pred = y_true → 梯度 = 0$v$, false, $v$y_pred = y_true → 梯度 = 0$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_mg_known$v$, $v$y_true=[3,5], y_pred=[5,3] → 2(y_pred-y_true)/2 = (2, -2)$v$, false, $v$y_true=[3,5], y_pred=[5,3] → 2(y_pred-y_true)/2 = (2, -2)$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_mg_four_samples$v$, $v$y_true=[0,0,0,0], y_pred=[1,2,3,4] → 2(y_pred-0)/4 = (0.5,1,1.5,2)$v$, false, $v$y_true=[0,0,0,0], y_pred=[1,2,3,4] → 2(y_pred-0)/4 = (0.5,1,1.5,2)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_mg_negative_pred$v$, $v$y_true=[5], y_pred=[3] → 2(3-5)/1 = -4$v$, false, $v$y_true=[5], y_pred=[3] → 2(3-5)/1 = -4$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_mg_floats$v$, $v$y_true=[1.5, 2.5], y_pred=[2.0, 2.0] → 2(0.5, -0.5)/2 = (0.5, -0.5)$v$, false, $v$y_true=[1.5, 2.5], y_pred=[2.0, 2.0] → 2(0.5, -0.5)/2 = (0.5, -0.5)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_mg_raises_on_length_mismatch$v$, $v$mg raises on length mismatch$v$, false, $v$mg raises on length mismatch$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_mg_raises_on_empty$v$, $v$mg raises on empty$v$, false, $v$mg raises on empty$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_mg_raises_on_non_list$v$, $v$mg raises on non list$v$, false, $v$mg raises on non list$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_lbs_textbook$v$, $v$dz=2, x=[3,4], w=[1,1] → dw=[6,8], dx=[2,2], db=2$v$, true, $v$dz=2, x=[3,4], w=[1,1] → dw=[6,8], dx=[2,2], db=2$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_lbs_unit_dz$v$, $v$dz=1, x=[1,2,3], w=[0.5,0.5,0.5] → dw=[1,2,3], dx=[0.5,0.5,0.5], db=1$v$, true, $v$dz=1, x=[1,2,3], w=[0.5,0.5,0.5] → dw=[1,2,3], dx=[0.5,0.5,0.5], db=1$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_lbs_negative_dz$v$, $v$dz=-3, x=[2], w=[5] → dw=[-6], dx=[-15], db=-3$v$, true, $v$dz=-3, x=[2], w=[5] → dw=[-6], dx=[-15], db=-3$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_lbs_zero_dz$v$, $v$dz=0 → 所有梯度都是 0$v$, true, $v$dz=0 → 所有梯度都是 0$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_lbs_zero_x$v$, $v$x=[0,0], w=[1,2] → dw=[0,0], dx=[dz,2dz], db=dz$v$, true, $v$x=[0,0], w=[1,2] → dw=[0,0], dx=[dz,2dz], db=dz$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_lbs_raises_on_dim_mismatch$v$, $v$lbs raises on dim mismatch$v$, true, $v$lbs raises on dim mismatch$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_lbs_raises_on_empty$v$, $v$lbs raises on empty$v$, true, $v$lbs raises on empty$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_lbs_raises_on_non_list$v$, $v$lbs raises on non list$v$, true, $v$lbs raises on non list$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_gds_textbook$v$, $v$params=[0.5, 1.0], grads=[-40, -4], lr=0.01 → [0.9, 1.04]$v$, true, $v$params=[0.5, 1.0], grads=[-40, -4], lr=0.01 → [0.9, 1.04]$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_gds_multiple_params$v$, $v$params=[1,2,3], grads=[0.1,0.2,0.3], lr=10 → [0, 0, 0]$v$, true, $v$params=[1,2,3], grads=[0.1,0.2,0.3], lr=10 → [0, 0, 0]$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_gds_unit_step$v$, $v$params=[10], grads=[5], lr=1 → [5]$v$, true, $v$params=[10], grads=[5], lr=1 → [5]$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_gds_negative_grad_increases$v$, $v$grad 负 → param 增$v$, true, $v$grad 负 → param 增$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_gds_positive_grad_decreases$v$, $v$grad 正 → param 减$v$, true, $v$grad 正 → param 减$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_gds_raises_on_length_mismatch$v$, $v$gds raises on length mismatch$v$, true, $v$gds raises on length mismatch$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_gds_raises_on_empty$v$, $v$gds raises on empty$v$, true, $v$gds raises on empty$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_gds_raises_on_non_list$v$, $v$gds raises on non list$v$, true, $v$gds raises on non list$v$, NULL, 31)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
