-- CV9: 图像分类与 CNN 基础 (LeNet)
-- practice_id=9, order_in_practice=9, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$图像分类与 CNN 基础 (LeNet)$v$,
        'PRACTICE',
        9,
        $v$hard$v$,
        $v$## CNN 与 LeNet 经典结构

## 1.1 为什么需要 CNN

传统 CV (CV01-08) 主要靠**手工设计特征** (Sobel 梯度、Harris 角点、SIFT 描述子、模板匹配)。手工特征的局限:
- **场景特定**: 工厂检测的特征不一定能用于自然图像
- **不可学习**: 特征参数靠经验调, 数据再多也帮不了
- **组合困难**: 多层级抽象 (毛 → 耳朵 → 头 → 猫) 难以手工堆叠

CNN (Convolutional Neural Network) 的核心思想: 让网络**从数据中自动学习特征**。每一层是一组可学习的卷积核, 通过反向传播 (复习 NN04) 调整核参数, 自动找到对当前任务最有用的特征。

## 1.2 LeNet 经典结构

LeNet (Yann LeCun, 1998) 是第一个成功的 CNN, 用于手写数字识别 (MNIST 28×28 → 10 类):

```
Input (1×28×28)
 → Conv1 (1→6 channels, 5×5 kernel)
 → Pool1 (2×2 average)
 → Conv2 (6→16 channels, 5×5 kernel)
 → Pool2 (2×2 average)
 → FC1 (120 units)
 → FC2 (84 units)
 → Output (10 logits, softmax → 类别概率)
```

LeNet 验证了 CNN 在结构化图像 (手写数字、字符) 上的有效性, 是现代 CNN 的鼻祖。

## 1.3 三大组件

- **卷积层 (Conv)**: 可学习的 kernel + 输入做卷积 (复习 CV04 valid 卷积公式), 提取局部特征
- **池化层 (Pool)**: 下采样 (max 或 average), 减少特征图尺寸, 提供平移不变性
- **全连接层 (FC)**: 把特征图展平 (flatten) 后接全连接 (复习 NN05 浅层 MLP)

工程实务: 现代 CNN (VGG/ResNet) 是 LeNet 的"加宽加深"版本, 结构主体一致。


## 卷积参数量与输出形状

## 2.1 卷积层参数量

一个 2D 卷积层的参数量公式:

$\text{params} = C_{in} \cdot C_{out} \cdot k_h \cdot k_w + (C_{out} \text{ if bias else } 0)$

其中:
- $C_{in}$: 输入通道数
- $C_{out}$: 输出通道数
- $k_h, k_w$: kernel 高度与宽度
- bias: 是否有偏置项 (每个输出通道一个 scalar)

**例**: LeNet 的 Conv1 (1→6, 5×5, with bias) = $1 \cdot 6 \cdot 5 \cdot 5 + 6 = 150 + 6 = 156$。

**例**: VGG 的 Conv (64→128, 3×3, with bias) = $64 \cdot 128 \cdot 3 \cdot 3 + 128 = 73728 + 128 = 73856$。

参数量计算是模型选型的关键 — 移动端部署对参数量敏感。

## 2.2 2D 卷积输出形状

给定输入 $H_{in} \times W_{in}$, kernel $k_h \times k_w$, padding $p$, stride $s$:

$H_{out} = \lfloor (H_{in} + 2p - k_h) / s \rfloor + 1$
$W_{out} = \lfloor (W_{in} + 2p - k_w) / s \rfloor + 1$

复习 CV04 的 1D valid 卷积公式 — 这是 2D 推广, 加了 padding 项。

**例**: 输入 28×28, kernel 5×5, p=0, s=1 → $H_{out} = (28+0-5)/1 + 1 = 24$, 输出 24×24。

**例**: 输入 32×32, kernel 3×3, p=1, s=1 → $H_{out} = (32+2-3)/1 + 1 = 32$, 输出 32×32 (same padding)。

## 2.3 padding 与 stride 选择

- **padding=0** (valid): 输出比输入小, 标准 LeNet 用
- **padding=(k-1)/2** (same): 输出与输入同尺寸, 现代 CNN (VGG/ResNet) 标配
- **stride=1**: 全密集卷积, 主流
- **stride=2**: 下采样替代池化, ResNet 风格


## softmax 分类 / 交叉熵 / 业务案例

## 3.1 softmax 函数

把 logits (任意实数向量) 转成概率分布:

$p_i = \frac{e^{z_i}}{\sum_j e^{z_j}}$

性质:
- $p_i \in (0, 1)$
- $\sum_i p_i = 1$
- argmax(softmax(z)) = argmax(z) — 单调性保证 softmax 不影响预测类别

工程实务: 实际预测时不需要算 softmax, 直接 argmax(logits) 即可, 省一次 exp。

## 3.2 交叉熵损失

给定真实类别 $y$ (one-hot 或 index), 模型预测概率分布 $p$:

$\text{CE} = -\sum_i y_i \log p_i = -\log p_y$ (one-hot 简化)

性质:
- $p_y = 1$ → CE = 0 (完美预测)
- $p_y \to 0$ → CE → ∞ (大错)
- 损失对错误类别完全不关心 (one-hot)

复习 NN03: 我们已经从 Logistic 回归学过 CE, CNN 分类只是把 logits 来源换成卷积特征。

## 3.3 业务案例: 手写数字识别 (MNIST)

场景: 邮政自动分拣需要识别手写邮编, 业界标准基准是 MNIST (28×28 灰度 0-9 数字)。

LeNet 训练流水线:
1. **数据**: MNIST 60000 训练 + 10000 测试, 28×28 灰度
2. **预处理**: 归一化到 [0, 1] (复习 CV01)
3. **前向**: Conv1 → Pool1 → Conv2 → Pool2 → FC1 → FC2 → logits
4. **softmax + 交叉熵**: 训练用 CE, 预测用 argmax (本关函数)
5. **反向传播**: 从 CE 反向计算梯度, 更新所有参数 (NN04 / NN07 复习)
6. **评估**: 测试集 accuracy (本关 cross_entropy_for_classification 用于训练循环)

工程实务:
- **MNIST 是 baseline**: 现代 CNN 在 MNIST 准确率 99%+
- **真实邮编**: 手写体差异大, 需要数据增强 (旋转/缩放/扭曲)
- **部署**: 移动端用 MobileNet / EfficientNet 等紧凑结构

## 3.4 工程口诀

- **CNN 自动学特征**: 比手工设计省力且效果常更好
- **LeNet 是经典**: 学新架构先理解 LeNet 的卷积+池化+全连接组合
- **参数量看 kernel 与通道**: 通道翻倍参数量 4 倍
- **输出形状别死记**: 用 floor 公式现算
- **softmax 训练用, 预测可省**: argmax(logits) 直接预测

$v$,
        $v${"questions": [{"id": "q09-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv09.py 中的 4 个函数; 评测以 test_cv09.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_conv_param_lenet_conv1$v$, $v$LeNet Conv1 (1→6, 5×5, bias) = 1*6*25 + 6 = 156$v$, false, $v$LeNet Conv1 (1→6, 5×5, bias) = 1*6*25 + 6 = 156$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_conv_param_vgg_block$v$, $v$VGG (64→128, 3×3, bias) = 64*128*9 + 128 = 73856$v$, false, $v$VGG (64→128, 3×3, bias) = 64*128*9 + 128 = 73856$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_conv_param_no_bias$v$, $v$LeNet Conv1 无 bias: 1*6*25 = 150$v$, false, $v$LeNet Conv1 无 bias: 1*6*25 = 150$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_conv_param_1x1$v$, $v$1×1 卷积 (32→64, bias) = 32*64 + 64 = 2112$v$, false, $v$1×1 卷积 (32→64, bias) = 32*64 + 64 = 2112$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_conv_param_boundary_small$v$, $v$边界: 1→2 3×1 无 bias = 1*2*3*1 = 6 (Shape: 1*2=2 不同)$v$, false, $v$边界: 1→2 3×1 无 bias = 1*2*3*1 = 6 (Shape: 1*2=2 不同)$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_conv_param_default_bias_true$v$, $v$bias 默认 True: 1*6*25 + 6 = 156$v$, false, $v$bias 默认 True: 1*6*25 + 6 = 156$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_conv_param_raises_on_zero$v$, $v$conv param raises on zero$v$, false, $v$conv param raises on zero$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_conv_param_raises_on_non_int$v$, $v$conv param raises on non int$v$, false, $v$conv param raises on non int$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_conv_output_lenet$v$, $v$28×28, k=5, p=0, s=1 → 24×24$v$, false, $v$28×28, k=5, p=0, s=1 → 24×24$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_conv_output_same_padding$v$, $v$32×32, k=3, p=1, s=1 → 32×32 (same)$v$, false, $v$32×32, k=3, p=1, s=1 → 32×32 (same)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_conv_output_stride_2$v$, $v$32×32, k=3, p=1, s=2 → 16×16 (downsample)$v$, false, $v$32×32, k=3, p=1, s=2 → 16×16 (downsample)$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_conv_output_imagenet$v$, $v$224×224, k=7, p=3, s=2 → (224+6-7)/2+1 = 112$v$, false, $v$224×224, k=7, p=3, s=2 → (224+6-7)/2+1 = 112$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_conv_output_raises_on_too_small$v$, $v$conv output raises on too small$v$, false, $v$conv output raises on too small$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_conv_output_raises_on_non_int$v$, $v$conv output raises on non int$v$, false, $v$conv output raises on non int$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_softmax_simple$v$, $v$[1, 5, 3] → 1$v$, true, $v$[1, 5, 3] → 1$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_softmax_last$v$, $v$[1, 2, 9] → 2$v$, true, $v$[1, 2, 9] → 2$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_softmax_negative_argmax_middle$v$, $v$[-5, -1, -3] → 1 (-1 最大)$v$, true, $v$[-5, -1, -3] → 1 (-1 最大)$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_softmax_ties_first$v$, $v$并列取最小: [3, 5, 5] → 1$v$, true, $v$并列取最小: [3, 5, 5] → 1$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_softmax_two_class$v$, $v$[0.5, 2.0] → 1 (boundary 二分类)$v$, true, $v$[0.5, 2.0] → 1 (boundary 二分类)$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_softmax_raises_on_empty$v$, $v$softmax raises on empty$v$, true, $v$softmax raises on empty$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_softmax_raises_on_non_list$v$, $v$softmax raises on non list$v$, true, $v$softmax raises on non list$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_ce_high_conf_label_1$v$, $v$probs=[0.05, 0.9, 0.05], label=1 → -ln(0.9) (probs[0]≠probs[label])$v$, true, $v$probs=[0.05, 0.9, 0.05], label=1 → -ln(0.9) (probs[0]≠probs[label])$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_ce_high_conf_label_2$v$, $v$probs=[0.05, 0.05, 0.9], label=2 → -ln(0.9)$v$, true, $v$probs=[0.05, 0.05, 0.9], label=2 → -ln(0.9)$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_ce_wrong_class$v$, $v$probs=[0.9, 0.05, 0.05], label=1 → -ln(0.05) ≈ 2.9957$v$, true, $v$probs=[0.9, 0.05, 0.05], label=1 → -ln(0.05) ≈ 2.9957$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_ce_two_class_label_1$v$, $v$probs=[0.7, 0.3], label=1 → -ln(0.3) (boundary 二分类)$v$, true, $v$probs=[0.7, 0.3], label=1 → -ln(0.3) (boundary 二分类)$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_ce_skewed_label_3$v$, $v$probs=[0.1, 0.2, 0.3, 0.4], label=3 → -ln(0.4)$v$, true, $v$probs=[0.1, 0.2, 0.3, 0.4], label=3 → -ln(0.4)$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_ce_skewed_label_2$v$, $v$同上 label=2 → -ln(0.3)$v$, true, $v$同上 label=2 → -ln(0.3)$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_ce_raises_on_label_out_of_range$v$, $v$ce raises on label out of range$v$, true, $v$ce raises on label out of range$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_ce_raises_on_non_list$v$, $v$ce raises on non list$v$, true, $v$ce raises on non list$v$, NULL, 29)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
