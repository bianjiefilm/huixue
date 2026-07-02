-- NN2: 单个神经元与激活函数
-- practice_id=8, order_in_practice=2, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$单个神经元与激活函数$v$,
        'PRACTICE',
        2,
        $v$beginner$v$,
        $v$## 单个神经元的数学结构

## 1.1 加权求和 + 激活

一个神经元接收若干输入 $x_1, x_2, \ldots, x_n$, 经两步变换产生输出:

**第 1 步 加权求和**: $z = \sum_{i=1}^{n} w_i x_i + b$

其中 $w_i$ 是输入对应的权重, $b$ 是偏置 (bias)。这一步是线性的, 等价于一个"打分":  权重表示输入的重要性, 偏置表示打分的基准。

**第 2 步 激活**: $a = f(z)$

$f$ 是激活函数, 把线性打分 $z$ 转换为非线性的输出 $a$。激活函数的引入是神经元具备"非线性表达能力"的关键 — 没有激活函数, 多层神经元堆叠仍然只是线性变换, 无法学习曲线/分段/复杂决策边界。

## 1.2 为什么必须非线性

考虑两层只有线性变换的神经元: $y = W_2 (W_1 x + b_1) + b_2 = (W_2 W_1) x + (W_2 b_1 + b_2)$。展开后整体仍是 $\tilde{W} x + \tilde{b}$, 等价于一个单层。

一旦在层间加入非线性激活 $a_1 = f(W_1 x + b_1)$, 后续 $W_2 a_1 + b_2$ 就不再是 $x$ 的线性函数, 网络才能学习复杂模式。**非线性是深度网络获得表达力的根本**。

## 1.3 主流激活函数概览

| 名字 | 公式 | 输出范围 | 主要用途 |
|------|------|----------|----------|
| sigmoid | $\frac{1}{1 + e^{-z}}$ | (0, 1) | 二分类输出层 |
| tanh | $\frac{e^z - e^{-z}}{e^z + e^{-z}}$ | (-1, 1) | 中间层 (零均值) |
| ReLU | $\max(0, z)$ | $[0, +\infty)$ | 中间层默认首选 |
| Leaky ReLU | $\max(\alpha z, z)$ | $(-\infty, +\infty)$ | 解决 ReLU 死亡问题 |


## Sigmoid 与 Tanh

## 2.1 Sigmoid 的特点

公式: $\sigma(z) = \frac{1}{1 + e^{-z}}$

关键值:
- $\sigma(0) = 0.5$ (中点)
- $\sigma(z) \to 1$ 当 $z \to +\infty$
- $\sigma(z) \to 0$ 当 $z \to -\infty$
- 严格单调递增, 输出落在 $(0, 1)$ 开区间

Sigmoid 的优势是输出可以解释为"概率", 因此适合二分类的输出层。劣势:
- **饱和区梯度趋零**: $|z| > 5$ 时输出几乎恒为 0 或 1, 后续课程的训练算法在饱和区"学不动"
- **输出非零均值**: 总是 > 0, 让下一层输入永远偏正, 不利于训练
- 这两点让 Sigmoid 在中间层基本被 ReLU 取代

## 2.2 Tanh 的特点

公式: $\tanh(z) = \frac{e^z - e^{-z}}{e^z + e^{-z}}$

关键值:
- $\tanh(0) = 0$
- $\tanh(z) \to 1$ 当 $z \to +\infty$
- $\tanh(z) \to -1$ 当 $z \to -\infty$
- 关于原点对称: $\tanh(-z) = -\tanh(z)$

Tanh 实质是 Sigmoid 的"零均值版本": $\tanh(z) = 2 \sigma(2z) - 1$. 输出范围 $(-1, 1)$ 让下一层输入大致零均值, 训练比 Sigmoid 更稳定。劣势同 Sigmoid: 仍有饱和区。

工程实务: 中间层若坚持要"光滑非线性", 优先选 tanh 而非 sigmoid; 但默认还是用 ReLU。


## ReLU 与 Leaky ReLU

## 3.1 ReLU 的革命性

公式: $\text{ReLU}(z) = \max(0, z)$

关键性质:
- $z > 0$ 时输出 $z$, 梯度恒为 1 (后续课程的训练算法不会"学不动")
- $z \leq 0$ 时输出 0, 梯度为 0
- 单边线性, 计算极快 (一次比较 + 选择)

ReLU 的简单与速度让它成为现代深度网络的默认激活。AlexNet 2012 用 ReLU 替代 Sigmoid 是深度学习起飞的关键技术之一。

## 3.2 ReLU 的"死亡神经元"问题

$z \leq 0$ 时输出 0、梯度也 0, 这部分神经元在训练中"学不动" — 永远输出 0, 网络容量浪费。这种现象叫**死亡 ReLU** (Dying ReLU)。

触发条件:
- 学习率过大, 一次更新让权重跳到极端值, 后续输入永远落在负区
- 数据预处理不到位, 输入分布偏负
- 初始化不当 (后续课程会展开)

## 3.3 Leaky ReLU: 给负区一个小斜率

公式: $\text{LReLU}(z) = \max(\alpha z, z) = \begin{cases} z & z > 0 \\ \alpha z & z \leq 0 \end{cases}$

其中 $\alpha$ 是小正数 (常用 0.01 或 0.1)。负区不再是 0, 而是有一个小斜率, 神经元不会"死掉"。

$\alpha$ 取 0 退化为标准 ReLU。$\alpha = 1$ 退化为线性函数 (失去非线性, 不能用)。工程实务 $\alpha = 0.01$ 是经验值, 也有 PReLU (把 $\alpha$ 当可学习参数) 等变种。

## 3.4 选型口诀

- 中间层默认: **ReLU** (快、好用、行业标准)
- 死亡神经元问题严重: 换 **Leaky ReLU** ($\alpha = 0.01$)
- 二分类输出层: **Sigmoid** (概率解释)
- 中间层需要零均值光滑: **tanh**
- 多分类输出层: 后续课程介绍 (这里不展开)


## 业务案例: 图像识别中的激活选择

## 4.1 场景

某医疗影像公司训练一个肺部 CT 异常检测模型, 输入 CT 图像 (512×512×1), 输出"异常概率"。架构 (高层视角):
- 中间层: 多层网络 (具体结构后续课程展开)
- 输出层: 单个神经元给概率

初版用 Sigmoid 做所有中间层激活, 训练 50 个 epoch 后准确率卡在 70%, 训练曲线观察到 loss 下降极慢。诊断后改用 ReLU 中间层 + Sigmoid 输出层, 同样 50 个 epoch 准确率到 88%。

## 4.2 失败的根因

Sigmoid 在中间层导致两个问题:
1. **饱和饿梯度**: 中间层若有几十个神经元一起进入饱和区, 整层"学不动"
2. **负偏态**: Sigmoid 输出永远 > 0, 多层堆叠后激活分布越走越偏

改 ReLU 后中间层梯度健康, 训练效率提升一个数量级。Sigmoid 只保留在最终输出 (因为概率解释)。

## 4.3 工程口诀

- **不要在中间层无脑堆 Sigmoid**: 这是新手最常见的训练慢的原因
- **观察激活分布**: 训练时打印每层的激活值分布直方图, 若某层 90% 神经元输出接近 0 或 1, 就是激活函数选错了
- **激活函数选择优先级**: 业务对输出区间没有明确约束 → ReLU; 有约束 (概率/区间) → Sigmoid 或 tanh; 死亡神经元严重 → Leaky ReLU

激活函数看似细节, 实际是深度网络能否训得动的关键。后续课程会从训练动力学的角度进一步展开。

$v$,
        $v${"questions": [{"id": "q02-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn02.py 中的 4 个函数; 评测以 test_nn02.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_sig_five_diverse$v$, $v$[0, 1, -1, 2, -2] → [0.5, 0.7311, 0.2689, 0.8808, 0.1192]$v$, false, $v$[0, 1, -1, 2, -2] → [0.5, 0.7311, 0.2689, 0.8808, 0.1192]$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_sig_extreme_positive$v$, $v$[10, 100] 极正值 → 接近 1.0$v$, false, $v$[10, 100] 极正值 → 接近 1.0$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_sig_extreme_negative$v$, $v$[-10, -100] 极负值 → 接近 0.0$v$, false, $v$[-10, -100] 极负值 → 接近 0.0$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_sig_half_values$v$, $v$[0.5, -0.5, 1.5, -1.5] 非整数$v$, false, $v$[0.5, -0.5, 1.5, -1.5] 非整数$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_sig_empty$v$, $v$边界: 空列表 → 空列表$v$, false, $v$边界: 空列表 → 空列表$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_sig_raises_on_non_list$v$, $v$sig raises on non list$v$, false, $v$sig raises on non list$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_sig_raises_on_non_numeric$v$, $v$sig raises on non numeric$v$, false, $v$sig raises on non numeric$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_tanh_diverse$v$, $v$[0, 1, -1, 2, -2] → [0, 0.7616, -0.7616, 0.9640, -0.9640]$v$, false, $v$[0, 1, -1, 2, -2] → [0, 0.7616, -0.7616, 0.9640, -0.9640]$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_tanh_one_nontrivial$v$, $v$tanh(1) ≈ 0.7616 (避 tanh(0)=0 与 identity 巧合)$v$, false, $v$tanh(1) ≈ 0.7616 (避 tanh(0)=0 与 identity 巧合)$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_tanh_extreme$v$, $v$[10, -10] → 接近 ±1$v$, false, $v$[10, -10] → 接近 ±1$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_tanh_symmetric$v$, $v$tanh(z) = -tanh(-z): [0.5, -0.5] → [a, -a]$v$, false, $v$tanh(z) = -tanh(-z): [0.5, -0.5] → [a, -a]$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_tanh_empty$v$, $v$tanh empty$v$, false, $v$tanh empty$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_tanh_raises_on_non_list$v$, $v$tanh raises on non list$v$, false, $v$tanh raises on non list$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_tanh_raises_on_non_numeric$v$, $v$tanh raises on non numeric$v$, false, $v$tanh raises on non numeric$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_relu_mixed$v$, $v$[-2, 0, 1, 5, -10, 0.5] → [0, 0, 1, 5, 0, 0.5]$v$, false, $v$[-2, 0, 1, 5, -10, 0.5] → [0, 0, 1, 5, 0, 0.5]$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_relu_negatives_zeroed$v$, $v$[-1, -2, -3] 全负 → [0, 0, 0] (identity 必失败)$v$, true, $v$[-1, -2, -3] 全负 → [0, 0, 0] (identity 必失败)$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_relu_zero_boundary$v$, $v$边界: [0, -0.0001, 0.0001] → [0, 0, 0.0001]$v$, true, $v$边界: [0, -0.0001, 0.0001] → [0, 0, 0.0001]$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_relu_large_negative$v$, $v$[-100, 100] → [0, 100] (含负, 防 identity)$v$, true, $v$[-100, 100] → [0, 100] (含负, 防 identity)$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_relu_with_decimals$v$, $v$[-0.5, 0.5] → [0, 0.5]$v$, true, $v$[-0.5, 0.5] → [0, 0.5]$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_relu_empty$v$, $v$relu empty$v$, true, $v$relu empty$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_relu_raises_on_non_list$v$, $v$relu raises on non list$v$, true, $v$relu raises on non list$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_relu_raises_on_non_numeric$v$, $v$relu raises on non numeric$v$, true, $v$relu raises on non numeric$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_lrelu_default_alpha$v$, $v$默认 alpha=0.01: [-10, 0, 10] → [-0.1, 0, 10]$v$, true, $v$默认 alpha=0.01: [-10, 0, 10] → [-0.1, 0, 10]$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_lrelu_alpha_01$v$, $v$alpha=0.1: [-5, 5] → [-0.5, 5]$v$, true, $v$alpha=0.1: [-5, 5] → [-0.5, 5]$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_lrelu_alpha_05$v$, $v$alpha=0.5: [-2, 0, 2] → [-1, 0, 2]$v$, true, $v$alpha=0.5: [-2, 0, 2] → [-1, 0, 2]$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_lrelu_alpha_zero_equals_relu$v$, $v$alpha=0: 退化为 ReLU$v$, true, $v$alpha=0: 退化为 ReLU$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_lrelu_mixed_decimals$v$, $v$alpha=0.01: [-100, -1, 0, 1, 100] → [-1.0, -0.01, 0, 1, 100]$v$, true, $v$alpha=0.01: [-100, -1, 0, 1, 100] → [-1.0, -0.01, 0, 1, 100]$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_lrelu_empty$v$, $v$lrelu empty$v$, true, $v$lrelu empty$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_lrelu_raises_on_non_list$v$, $v$lrelu raises on non list$v$, true, $v$lrelu raises on non list$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_lrelu_raises_on_non_numeric_alpha$v$, $v$lrelu raises on non numeric alpha$v$, true, $v$lrelu raises on non numeric alpha$v$, NULL, 30)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
