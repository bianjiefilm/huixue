-- NN6: 深层神经网络与初始化
-- practice_id=8, order_in_practice=6, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$深层神经网络与初始化$v$,
        'PRACTICE',
        6,
        $v$advanced$v$,
        $v$## 为什么深层网络需要专门的初始化

## 1.1 深层 vs 浅层

浅层 (NN05 介绍的 1 隐层 MLP) 用纯随机小值初始化 (例如 N(0, 0.01)) 也能训得动。深层 (10 层以上) 网络对初始化极度敏感 — 错误的初始化会让训练在第一步就失败。

根本原因: 信号 (前向激活) 和梯度 (反向) 都要穿过几十层。如果每层都把信号"放大 1.1 倍", 10 层后放大 2.6 倍, 100 层后放大 13780 倍 — 数值爆炸。如果每层放大 0.9 倍, 10 层后只剩 0.35 倍, 100 层后剩 0.000027 倍 — 数值消失。

初始化的核心目标: **让每层的输入输出方差大致相等**, 信号在前向中保持稳定, 梯度在反向中也不爆/不消。

## 1.2 朴素初始化为什么失败

历史上常见的失败模式:
- **零初始化**: 所有权重 = 0, 所有神经元输出相同, 反向梯度也相同, 网络失去对称性破坏能力, 永远学不出有意义的特征
- **大常数初始化** (例如 N(0, 1)): 第一层激活方差与输入相当, 但后续每层方差成倍增长 (因为权重和很多), 几层后激活全部饱和到极端值, 训练崩溃
- **小常数初始化** (例如 N(0, 0.001)): 反过来, 信号每层缩水, 几层后激活几乎全是 0, 梯度也消失

## 1.3 关键洞察: 方差守恒

设输入 $\mathbf{x}$ 的每个分量方差为 $\sigma_x^2$, 一层的 $z = \sum_{i=1}^{n_{in}} w_i x_i + b$。在 $w_i$ 与 $x_i$ 独立、$w_i$ 均值 0 的假设下:

$\text{Var}(z) = n_{in} \cdot \text{Var}(w) \cdot \text{Var}(x)$

要让 $\text{Var}(z) = \text{Var}(x)$, 必须让 $\text{Var}(w) = 1 / n_{in}$ — 这就是 Xavier 与 He 初始化公式的来源。


## Xavier 与 He 初始化

## 2.1 Xavier 初始化 (Glorot, 2010)

考虑前向方差守恒 ($n_{in}$ 项相加) 与反向方差守恒 ($n_{out}$ 项相加), Xavier 初始化取两者折中:

$\text{Var}(w) = \frac{2}{n_{in} + n_{out}}$

具体实现常用**均匀分布**:
$w \sim U\left(-\sqrt{\frac{6}{n_{in} + n_{out}}}, \sqrt{\frac{6}{n_{in} + n_{out}}}\right)$

均匀分布 $U(-a, a)$ 的方差是 $a^2/3$, 取 $a = \sqrt{6/(n_{in}+n_{out})}$ 让方差 = $2/(n_{in}+n_{out})$。

Xavier 适合 **Sigmoid / tanh** 激活的网络。

## 2.2 He 初始化 (He, 2015)

ReLU 把负数截 0, 让"有效"输入只有一半。He 初始化补偿这一点:

$\text{Var}(w) = \frac{2}{n_{in}}$

具体实现常用**正态分布**:
$w \sim \mathcal{N}\left(0, \sqrt{\frac{2}{n_{in}}}\right)$

He 适合 **ReLU / Leaky ReLU** 激活的网络。Xavier 用在 ReLU 网络会让方差逐层减半, 几层后激活几乎归零。

## 2.3 偏置初始化

偏置一般初始化为 0 (或接近 0 的小值)。理论上偏置打破对称性的作用比权重弱, 用 0 不会引入零梯度问题 (因为权重已经是随机的)。

工程实务: 用 ReLU 时偶尔把偏置初始化为小正数 (0.01) 避免初始 ReLU 死亡, 但默认 0 已经够用。


## 梯度消失与爆炸

## 3.1 现象

- **梯度消失**: 反向传播时, 浅层 (靠近输入) 的梯度趋近 0, 这些层"学不动", 网络等价于只用深层
- **梯度爆炸**: 反过来, 浅层梯度数值极大 (10^6 量级), 一次更新让权重跳到极端值, 损失变 NaN

## 3.2 数值诊断

训练时打印每层梯度的 mean 与 std:
- 健康范围: $|\text{mean}| < 0.1$, std 在 $0.001 \sim 1.0$
- 消失迹象: max 绝对值 $< 10^{-7}$
- 爆炸迹象: max 绝对值 $> 10^3$ 或出现 inf/nan

自动诊断的简易判断:

```
vanishing := mean(|grad|) < threshold_v   (例: 1e-7)
exploding := max(|grad|) > threshold_e   (例: 1e3)
```

## 3.3 缓解手段

- **正确初始化**: ReLU 用 He, Sigmoid/tanh 用 Xavier (本关重点)
- **梯度裁剪**: max-norm 截断, 让 ||grad|| 不超过阈值 (一般 1.0)
- **batch normalization**: 在每层把激活归一化到 (0 均值, 1 方差) — 后续课程展开
- **残差连接** (ResNet): 让梯度有"短路"路径, 避免逐层衰减 — 后续课程展开

初始化只是缓解的第一道防线, 训练超深网络 (50+) 还需要其他技术配合。


## 深层前向与业务案例

## 4.1 深层网络的前向公式

给定 L 层网络, 第 $l$ 层的输出:

$a^{(l)} = f^{(l)}\left(a^{(l-1)} \cdot W^{(l)} + b^{(l)}\right)$

其中 $a^{(0)} = X$, $f^{(l)}$ 是该层的激活函数。

工程实务: 中间层用 ReLU, 输出层根据任务用 Sigmoid (二分类) / Softmax (多分类) / 无激活 (回归)。每层 $W^{(l)}$, $b^{(l)}$ 都用合适的初始化方法 (中间层用 He 因为 ReLU)。

## 4.2 业务案例: ResNet-18 用于图像分类

ResNet-18 (常见图像分类深网络) 共 18 层, 主要由卷积层和全连接层组成。本关只讨论全连接部分的初始化原则:
- 中间层: ReLU + He 初始化
- 输出层 (1000 类分类): Linear + 小 std (例如 0.01) 让初始 logits 接近 0, 配合 softmax 输出接近均匀分布
- 偏置全初始化为 0

用 He 初始化 + ReLU 训练, 第一个 epoch 损失就开始稳定下降; 用 N(0, 1) 错误初始化, 第一步就 NaN — 这是 NN02 提到 "AlexNet 触发深度学习起飞" 中容易被忽略的细节: AlexNet 之前没有合理初始化, 12+ 层网络几乎训不动。

## 4.3 工程口诀

- **中间层激活定初始化**: ReLU/Leaky ReLU → He; Sigmoid/tanh → Xavier
- **fan_in 与 fan_out**: $W$ 形状 $(d, h)$, fan_in=d, fan_out=h
- **seed 固定**: 复现实验必须固定 numpy/torch random seed, 是工程纪律
- **训练第一步看梯度健康**: mean/std 异常 (NaN / 1e10 / 1e-15) 立刻停, 检查初始化与学习率

$v$,
        $v${"questions": [{"id": "q06-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn06.py 中的 4 个函数; 评测以 test_nn06.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_xavier_shape$v$, $v$形状正确$v$, false, $v$形状正确$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_xavier_uniform_bounds$v$, $v$所有元素绝对值 ≤ sqrt(6/(fan_in+fan_out)) (seed=42 防 identity all-0)$v$, false, $v$所有元素绝对值 ≤ sqrt(6/(fan_in+fan_out)) (seed=42 防 identity all-0)$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_xavier_std_correct$v$, $v$大矩阵 std ≈ sqrt(2/(fan_in+fan_out))$v$, false, $v$大矩阵 std ≈ sqrt(2/(fan_in+fan_out))$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_xavier_deterministic_and_valid$v$, $v$同 seed 同结果 (可复现性) + std > 0.01 (非常量) + max(|W|) < 5 (合理范围)  设计加强 (非删测试): hardcode return zeros 在 std=0 fail; hardcode 常量 0.5 在 std=0 fail; identity all-seed 在 std=0 fail。$v$, false, $v$同 seed 同结果 (可复现性) + std > 0.01 (非常量) + max(|W|) < 5 (合理范围)  设计加强 (非删测试): hardcode return zeros 在 std=0 fail; hardcode 常量 0.5 在 std=0 fail; identity all-seed 在 std=0 fail。$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_xavier_different_seeds_with_validity$v$, $v$不同 seed 不同结果 + 双方 std 都非零 (防 identity 返回常量)$v$, false, $v$不同 seed 不同结果 + 双方 std 都非零 (防 identity 返回常量)$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_xavier_not_all_zero$v$, $v$xavier 必产生有变化的权重 (防 hardcode 全 0)$v$, false, $v$xavier 必产生有变化的权重 (防 hardcode 全 0)$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_xavier_raises_on_zero_fan$v$, $v$xavier raises on zero fan$v$, false, $v$xavier raises on zero fan$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_xavier_raises_on_non_int$v$, $v$xavier raises on non int$v$, false, $v$xavier raises on non int$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_he_shape$v$, $v$he shape$v$, false, $v$he shape$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_he_std_correct$v$, $v$大矩阵 std ≈ sqrt(2/fan_in) — He 公式$v$, false, $v$大矩阵 std ≈ sqrt(2/fan_in) — He 公式$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_he_deterministic_and_valid$v$, $v$同 seed 同结果 + std > 0.01 + max(|W|) < 5 (设计加强)$v$, false, $v$同 seed 同结果 + std > 0.01 + max(|W|) < 5 (设计加强)$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_he_different_seeds_with_validity$v$, $v$不同 seed 不同结果 + 双方 std 非零$v$, false, $v$不同 seed 不同结果 + 双方 std 非零$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_he_max_value_reasonable$v$, $v$he 大矩阵 max(|W|) 应在 5σ 内 (5*sqrt(2/fan_in)), 防 identity 返回 seed 值$v$, false, $v$he 大矩阵 max(|W|) 应在 5σ 内 (5*sqrt(2/fan_in)), 防 identity 返回 seed 值$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_he_not_all_zero$v$, $v$he 必产生有变化的权重 (防 hardcode 全 0)$v$, false, $v$he 必产生有变化的权重 (防 hardcode 全 0)$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_he_raises_on_zero_fan$v$, $v$he raises on zero fan$v$, false, $v$he raises on zero fan$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_he_raises_on_non_int$v$, $v$he raises on non int$v$, false, $v$he raises on non int$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_cgh_healthy$v$, $v$健康梯度: [0.1, -0.2, 0.05] → mean/std 合理, 无 vanishing/exploding$v$, true, $v$健康梯度: [0.1, -0.2, 0.05] → mean/std 合理, 无 vanishing/exploding$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_cgh_vanishing$v$, $v$全极小值 mean(|grad|) < 1e-7 → has_vanishing=True$v$, true, $v$全极小值 mean(|grad|) < 1e-7 → has_vanishing=True$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_cgh_exploding$v$, $v$含极大值 max(|grad|) > 1e3 → has_exploding=True$v$, true, $v$含极大值 max(|grad|) > 1e3 → has_exploding=True$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_cgh_specific_values$v$, $v$[1, 2, 3] mean=2, std=sqrt(2/3) (population), max_abs=3$v$, true, $v$[1, 2, 3] mean=2, std=sqrt(2/3) (population), max_abs=3$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_cgh_negative_max_abs$v$, $v$[-5, -3, -1] max_abs=5 (绝对值)$v$, true, $v$[-5, -3, -1] max_abs=5 (绝对值)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_cgh_zero_grad$v$, $v$全 0 → has_vanishing=True (mean=0 < 1e-7)$v$, true, $v$全 0 → has_vanishing=True (mean=0 < 1e-7)$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_cgh_raises_on_empty$v$, $v$cgh raises on empty$v$, true, $v$cgh raises on empty$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_cgh_raises_on_non_list$v$, $v$cgh raises on non list$v$, true, $v$cgh raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_fd_two_layers_relu_sigmoid$v$, $v$X=[[1]], W1=[[1]], b1=[0], relu → 1; W2=[[1]], b2=[0], sigmoid → σ(1)$v$, true, $v$X=[[1]], W1=[[1]], b1=[0], relu → 1; W2=[[1]], b2=[0], sigmoid → σ(1)$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_fd_three_layers_all_relu$v$, $v$X=[[1]], 三层都 W=[[2]], b=[0], relu → 1*2*2*2 = 8$v$, true, $v$X=[[1]], 三层都 W=[[2]], b=[0], relu → 1*2*2*2 = 8$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_fd_with_negative_relu_kills_then_bias$v$, $v$X=[[-1]], relu 杀负 → 0; 第二层 b=3 linear → 3 (避 0 巧合)$v$, true, $v$X=[[-1]], relu 杀负 → 0; 第二层 b=3 linear → 3 (避 0 巧合)$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_fd_linear_activation$v$, $v$linear (no activation): X=[[2]], W=[[3]], b=[1], linear → 7$v$, true, $v$linear (no activation): X=[[2]], W=[[3]], b=[1], linear → 7$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_fd_tanh_layer$v$, $v$X=[[1]], W=[[1]], b=[0], tanh → tanh(1)$v$, true, $v$X=[[1]], W=[[1]], b=[0], tanh → tanh(1)$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_fd_raises_on_length_mismatch$v$, $v$weights/biases/activations 长度不一致$v$, true, $v$weights/biases/activations 长度不一致$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_fd_raises_on_invalid_activation$v$, $v$fd raises on invalid activation$v$, true, $v$fd raises on invalid activation$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_fd_raises_on_non_list$v$, $v$fd raises on non list$v$, true, $v$fd raises on non list$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
