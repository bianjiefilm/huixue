-- NN9: 卷积神经网络基础
-- practice_id=8, order_in_practice=9, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$卷积神经网络基础$v$,
        'PRACTICE',
        9,
        $v$advanced$v$,
        $v$## 为什么图像需要卷积

## 1.1 全连接的弊端

复习 NN05 的全连接网络: 每个隐藏神经元连接所有输入。对一张 224×224×3 图像 (150528 输入), 单层 1024 神经元就需要 1.5 亿权重 — 内存爆炸 + 训练样本不足 + 没考虑空间结构。

图像有两个特点:
- **空间局部性**: 一个像素与邻近像素强相关, 与远处像素弱相关
- **平移不变性**: 同样的物体在图像不同位置应有相同特征

全连接网络两个特点都没利用 — 第 (0, 0) 与第 (10, 10) 像素被同等独立对待, 模型必须从数据学到"邻近"概念。

## 1.2 卷积的两大设计原则

- **局部连接**: 每个卷积神经元只看输入的一个小窗口 (kernel, 通常 3x3 或 5x5), 不看远处像素
- **权重共享**: 同一个 kernel 在整个图像上滑动, 提取相同模式 (无论物体在哪里)

这两个设计让参数从 1.5 亿降到 27 (单 3x3 kernel, 1 通道) ~ 几千 (多通道), 极大提升训练效率, 同时学到与空间结构匹配的特征。

## 1.3 卷积运算的最简形式 (1D)

给定输入切片 $\mathbf{x} = (x_1, \ldots, x_K)$, 卷积核 $\mathbf{w} = (w_1, \ldots, w_K)$, 偏置 $b$:

$z = \sum_{i=1}^{K} x_i w_i + b$

这与 NN03 单神经元线性求和**完全一样** — 卷积不是新运算, 而是"线性求和 + 滑动窗口"。


## 卷积输出形状公式

## 2.1 1D 卷积输出长度

给定输入长度 $N$, 卷积核长度 $K$, padding $P$, stride $S$:

$L_{\text{out}} = \left\lfloor \frac{N + 2P - K}{S} \right\rfloor + 1$

示例:
- $N=10, K=3, P=0, S=1$: $L_{\text{out}} = (10-3)/1 + 1 = 8$
- $N=10, K=3, P=1, S=1$: $L_{\text{out}} = (10+2-3)/1 + 1 = 10$ (same padding 保大小)
- $N=10, K=3, P=0, S=2$: $L_{\text{out}} = (10-3)/2 + 1 = 4.5 → 4$

## 2.2 2D 卷积同公式

宽高分别套同公式即可。给定输入 $H \times W$, 输出 $H' \times W'$:

$H' = \lfloor (H + 2P - K) / S \rfloor + 1$
$W' = \lfloor (W + 2P - K) / S \rfloor + 1$

## 2.3 padding 与 stride 的工程意义

- **padding=0 (valid)**: 边缘像素被卷积 K-1 次的少量, 信息利用不均
- **padding=K/2 (same)**: 输出与输入同大小, 易堆叠多层
- **stride=1**: 输出尺寸近似输入, 计算量大
- **stride=2**: 输出尺寸减半, 计算量降到 1/4 (类似池化)

工程实务: 主流网络 (卷积层) 用 padding=same, stride=1; 降采样用专门的池化或 stride=2 卷积。


## 池化与参数计算

## 3.1 池化的目的

池化 (Pooling) 是降采样, 把 feature map 尺寸减小, 主要好处:
- 减少参数与计算量
- 引入一定的平移不变性
- 控制过拟合 (信息瓶颈)

## 3.2 最大池化与平均池化

**最大池化 (Max Pooling)**: 取 $K \times K$ 窗口内最大值, 突出最强响应

$z_{i,j} = \max_{(p, q) \in \text{window}} x_{p,q}$

**平均池化 (Average Pooling)**: 取窗口平均值, 平滑响应

工程实务: 最大池化最常用, 因为"显著特征"更重要; 平均池化用在最后输出层 (Global Average Pooling) 替代全连接。

池化操作没有学习参数 (只是聚合), 这是它与卷积的主要区别。

## 3.3 卷积层参数数量

一个卷积层有 $C_{\text{in}}$ 输入通道、$C_{\text{out}}$ 输出通道、$K \times K$ 卷积核:

$\text{params} = C_{\text{in}} \cdot C_{\text{out}} \cdot K^2 + C_{\text{out}}$

$C_{\text{in}} \cdot C_{\text{out}} \cdot K^2$ 是权重 (每个输出通道一个 $C_{\text{in}} \times K \times K$ 的 kernel), $C_{\text{out}}$ 是每输出通道一个偏置。

示例: 输入 64 通道, 输出 128 通道, kernel 3x3 → 64 × 128 × 9 + 128 = 73,856 参数 (相比全连接 64 × 128 × H × W 大幅降低)。


## 业务案例: 图像分类网络结构设计

## 4.1 经典 CNN 流水线

图像分类网络的典型层级 (高层视角):

```
输入: H × W × 3
  │
  Conv 3x3 → 32 通道, padding=same, stride=1 → H × W × 32
  ReLU
  Max Pool 2x2 → H/2 × W/2 × 32
  │
  Conv 3x3 → 64 通道, padding=same → H/2 × W/2 × 64
  ReLU
  Max Pool 2x2 → H/4 × W/4 × 64
  │
  ... (重复加深)
  │
  Flatten → 全连接 → 类别概率
```

规律: 通道数从浅到深加倍 (32 → 64 → 128 → ...), 空间尺寸通过池化减半 (224 → 112 → 56 → ...)。

## 4.2 业务案例: 224×224 三分类网络的参数估算

架构:
- Conv1: 3 → 32, 3x3 → 3·32·9 + 32 = 896 参数, 输出 224×224×32
- Pool: 输出 112×112×32, 0 参数
- Conv2: 32 → 64, 3x3 → 32·64·9 + 64 = 18,496
- Pool: 56×56×64, 0 参数
- Conv3: 64 → 128, 3x3 → 64·128·9 + 128 = 73,856
- Pool: 28×28×128 = 100,352 features
- FC: 100,352 → 3 → 100,352·3 + 3 = 301,059

总参数 ≈ 394K, fp32 下 ≈ 1.5 MB。相比全连接基线 (224×224×3 → 3) 直接需要 451K 参数 — 但全连接没空间结构利用, 准确率会差很多。

## 4.3 工程口诀

- **3x3 卷积是黄金尺寸**: 大部分场景默认, 计算/表达力平衡
- **更深 + 通道加倍**: 比"单层加宽"更高效
- **池化或 stride=2**: 二选一做降采样, 不要同层都用
- **第一层 stride 通常更大**: 7x7 stride=2 是 ResNet 风格, 快速降空间
- **参数计算要心里有数**: 估完才知道模型能否放进显存

$v$,
        $v${"questions": [{"id": "q09-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn09.py 中的 4 个函数; 评测以 test_nn09.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_c1d_textbook$v$, $v$c1d textbook$v$, false, $v$c1d textbook$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_c1d_only_bias$v$, $v$c1d only bias$v$, false, $v$c1d only bias$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_c1d_unit_kernel$v$, $v$kernel=[1,1,1] 求和$v$, false, $v$kernel=[1,1,1] 求和$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_c1d_negative$v$, $v$全负 kernel$v$, false, $v$全负 kernel$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_c1d_single_element$v$, $v$单元素 kernel$v$, false, $v$单元素 kernel$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_c1d_raises_on_length_mismatch$v$, $v$c1d raises on length mismatch$v$, false, $v$c1d raises on length mismatch$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_c1d_raises_on_empty$v$, $v$c1d raises on empty$v$, false, $v$c1d raises on empty$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_c1d_raises_on_non_list$v$, $v$c1d raises on non list$v$, false, $v$c1d raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_cos_basic$v$, $v$N=10 K=3 P=0 S=1 → 8$v$, false, $v$N=10 K=3 P=0 S=1 → 8$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_cos_same_padding$v$, $v$N=10 K=3 P=1 S=1 → 10$v$, false, $v$N=10 K=3 P=1 S=1 → 10$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_cos_stride_2$v$, $v$N=10 K=3 P=0 S=2 → 4$v$, false, $v$N=10 K=3 P=0 S=2 → 4$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_cos_large_input$v$, $v$N=224 K=7 P=3 S=2 → (224+6-7)/2 + 1 = 112$v$, false, $v$N=224 K=7 P=3 S=2 → (224+6-7)/2 + 1 = 112$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_cos_K_equals_N$v$, $v$N=5 K=5 P=0 S=1 → 1$v$, false, $v$N=5 K=5 P=0 S=1 → 1$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_cos_raises_on_invalid$v$, $v$K > N+2P → 输出 ≤ 0$v$, false, $v$K > N+2P → 输出 ≤ 0$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_cos_raises_on_zero_stride$v$, $v$cos raises on zero stride$v$, false, $v$cos raises on zero stride$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_cos_raises_on_non_int$v$, $v$cos raises on non int$v$, false, $v$cos raises on non int$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_mp_simple_2x2$v$, $v$[[1,2],[3,4]] → [[4]]$v$, true, $v$[[1,2],[3,4]] → [[4]]$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_mp_4x4$v$, $v$[[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]] → [[6,8],[14,16]]$v$, true, $v$[[1,2,3,4],[5,6,7,8],[9,10,11,12],[13,14,15,16]] → [[6,8],[14,16]]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_mp_negative_values$v$, $v$[[−1,−2],[−3,−4]] → [[-1]]$v$, true, $v$[[−1,−2],[−3,−4]] → [[-1]]$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_mp_2x4$v$, $v$[[1,2,3,4],[5,6,7,8]] → [[6,8]]$v$, true, $v$[[1,2,3,4],[5,6,7,8]] → [[6,8]]$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_mp_4x2$v$, $v$[[1,2],[3,4],[5,6],[7,8]] → [[4],[8]]$v$, true, $v$[[1,2],[3,4],[5,6],[7,8]] → [[4],[8]]$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_mp_raises_on_odd_size$v$, $v$mp raises on odd size$v$, true, $v$mp raises on odd size$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_mp_raises_on_empty$v$, $v$mp raises on empty$v$, true, $v$mp raises on empty$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_mp_raises_on_non_list$v$, $v$mp raises on non list$v$, true, $v$mp raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_ccp_basic$v$, $v$64 → 128, K=3 → 64*128*9 + 128 = 73856$v$, true, $v$64 → 128, K=3 → 64*128*9 + 128 = 73856$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_ccp_first_conv$v$, $v$3 → 32, K=3 → 3*32*9 + 32 = 896$v$, true, $v$3 → 32, K=3 → 3*32*9 + 32 = 896$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_ccp_5x5_kernel$v$, $v$3 → 16, K=5 → 3*16*25 + 16 = 1216$v$, true, $v$3 → 16, K=5 → 3*16*25 + 16 = 1216$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_ccp_1x1_kernel$v$, $v$64 → 32, K=1 → 64*32 + 32 = 2080$v$, true, $v$64 → 32, K=1 → 64*32 + 32 = 2080$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_ccp_large_layer$v$, $v$256 → 512, K=3 → 256*512*9 + 512 = 1180160$v$, true, $v$256 → 512, K=3 → 256*512*9 + 512 = 1180160$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_ccp_raises_on_zero$v$, $v$ccp raises on zero$v$, true, $v$ccp raises on zero$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_ccp_raises_on_negative$v$, $v$ccp raises on negative$v$, true, $v$ccp raises on negative$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_ccp_raises_on_non_int$v$, $v$ccp raises on non int$v$, true, $v$ccp raises on non int$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
