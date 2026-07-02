-- CV4: 滤波与降噪
-- practice_id=9, order_in_practice=4, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$滤波与降噪$v$,
        'PRACTICE',
        4,
        $v$intermediate$v$,
        $v$## 图像噪声与滤波必要性

## 1.1 噪声从哪里来

数字图像几乎不可避免有噪声, 来源:
- **传感器**: CCD/CMOS 在低光照下读出电子噪声
- **传输**: 信号经过有损通道引入失真
- **量化**: 模拟到数字转换的精度损失
- **环境**: 空气抖动、光线变化等

噪声特征常见两类:
- **高斯噪声**: 像素值受加性高斯扰动 (零均值小方差), 均匀分布在整图
- **椒盐噪声**: 少量像素跳到 0 或 255 (黑白噪点), 局部极端

不同噪声适合不同滤波方法, 这是滤波器选择的核心。

## 1.2 滤波的本质

滤波 = 用邻域信息平滑当前像素。给定窗口大小 $K \times K$ (常用 3×3 或 5×5), 对每个像素位置, 取它附近 $K \times K$ 范围内的像素, 用某个聚合规则得到新像素值。

聚合规则的选择决定滤波器类型:
- **均值**: 平均, 对所有邻居等权
- **中值**: 取中间值, 鲁棒于极端值
- **高斯**: 加权平均, 中心权重高, 远处权重低
- **双边**: 同时考虑空间距离与像素值差异 (保边缘)


## 均值与中值滤波

## 2.1 均值滤波

公式: $\bar{x} = \frac{1}{|W|} \sum_{p \in W} x_p$

简单, 计算快, 适合**高斯噪声**。但对**椒盐噪声**效果差 — 一个 255 的噪点把均值拉高很多。

## 2.2 中值滤波

公式: $\text{med}(W) = $ W 中所有元素排序后取中位数

对椒盐噪声极有效 — 极端值不参与中心计算, 噪点直接被剔除。但计算量比均值大 (需要排序), 且对高斯噪声效果不如均值。

## 2.3 选型口诀

- **椒盐噪声 → 中值滤波**: 唯一最优选择
- **高斯噪声 → 均值或高斯滤波**: 高斯滤波边缘保留更好
- **不知道噪声类型 → 高斯滤波**: 通用安全选择

工程实务: 滤波是 CV 流水线的标配, 但**过度滤波会模糊细节**, kernel 大小 3×3 或 5×5 通常足够。


## 高斯核生成

## 3.1 高斯函数

1D 高斯函数:

$G(x) = \frac{1}{\sqrt{2\pi} \sigma} \exp\left(-\frac{x^2}{2 \sigma^2}\right)$

$\sigma$ 控制"扩散范围": $\sigma$ 小 → 集中中心 (锐化效果差), $\sigma$ 大 → 扩散远 (强力平滑)。

## 3.2 离散高斯核

实际工程中需要离散化为 size 长度的核。给定 size = $2k + 1$ (奇数), $\sigma$:

$k_i = G(i - k)$, $i = 0, 1, \ldots, 2k$

然后归一化让总和 = 1:
$K_i = k_i / \sum_j k_j$

例: size = 3, $\sigma = 1$:
$k_0 = G(-1) \approx 0.2420$
$k_1 = G(0) \approx 0.3989$
$k_2 = G(1) \approx 0.2420$

归一化: $\sum = 0.8829$, 各除以 0.8829 → [0.2741, 0.4519, 0.2741]。

## 3.3 size 与 sigma 的关系

经验规则: $\text{size} = 2 \cdot \lceil 3\sigma \rceil + 1$, 让核覆盖 $\pm 3\sigma$ 范围 (高斯 99.7% 质量)。

$\sigma = 1 \to$ size 7; $\sigma = 2 \to$ size 13。但工程上常固定 size 3 或 5, 反算 $\sigma$ 让效果合适。


## 1D 卷积与业务案例

## 4.1 valid 卷积

给定信号 $\mathbf{x}$ 长 $N$, 核 $\mathbf{k}$ 长 $K$, valid 卷积 (无 padding):

$y_i = \sum_{j=0}^{K-1} x_{i+j} \cdot k_j$, $i = 0, 1, \ldots, N-K$

输出长度 = $N - K + 1$ (复习 NN09 的输出形状公式, padding=0, stride=1)。

## 4.2 卷积与互相关的区别

数学上"卷积"要先把 kernel 翻转, "互相关"不翻转。CV/DL 工程中常用 "互相关" 但叫"卷积"。本关也用互相关, 学生不需要翻转 kernel。

## 4.3 业务案例: CCD 噪声去除

场景: 工业检测低光照下的零件成像, 图像有明显椒盐噪点 + 高斯噪声混合。

流水线:
1. **中值滤波** (3×3) 先去椒盐噪声 — 椒盐去掉后高斯噪声仍在
2. **高斯滤波** ($\sigma = 1$, 5×5) 进一步去高斯噪声
3. 后续步骤 (边缘检测、缺陷识别)

为什么先中值再高斯: 椒盐噪声是极端值, 高斯滤波会把噪点扩散到周围反而污染更大区域。先用中值剔除噪点, 再用高斯平滑, 是混合噪声场景的标准流程。

## 4.4 双边滤波: 边缘保护

均值/高斯滤波平滑的副作用: 边缘也被模糊。双边滤波 (Bilateral Filter) 同时考虑空间距离与像素值差异, 在像素值差异大的位置 (边缘) 减少平滑权重, 既去噪又保边。

公式不写出 (本关不实现), 但工程上是处理"既要降噪又要保细节" (人脸美颜、医学影像) 的标准方法。代价: 比高斯滤波慢 5-10 倍。

## 4.5 工程口诀

- **滤波是预处理标配**: 几乎所有 CV 任务都先滤波
- **kernel 大小 3 或 5**: 太大模糊细节, 太小去噪不够
- **sigma 不要乱调**: 默认 1.0 在大多数场景够用
- **混合噪声先椒盐再高斯**: 顺序重要
- **保边缘选双边**: 既要降噪又要保细节场景的最优选择

$v$,
        $v${"questions": [{"id": "q04-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv04.py 中的 4 个函数; 评测以 test_cv04.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_mean_basic$v$, $v$mean basic$v$, false, $v$mean basic$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_mean_with_outlier$v$, $v$含异常值: [10, 20, 200] mean=76.67$v$, false, $v$含异常值: [10, 20, 200] mean=76.67$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_mean_zeros$v$, $v$mean zeros$v$, false, $v$mean zeros$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_mean_two_distinct$v$, $v$两元素 [42, 100] mean=71 (避 identity 单元素巧合)$v$, false, $v$两元素 [42, 100] mean=71 (避 identity 单元素巧合)$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_mean_negative$v$, $v$mean negative$v$, false, $v$mean negative$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_mean_raises_on_empty$v$, $v$mean raises on empty$v$, false, $v$mean raises on empty$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_mean_raises_on_non_list$v$, $v$mean raises on non list$v$, false, $v$mean raises on non list$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_med_odd$v$, $v$[1, 2, 3, 4, 5] → 3$v$, false, $v$[1, 2, 3, 4, 5] → 3$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_med_even$v$, $v$[1, 2, 3, 4] → (2+3)/2 = 2.5$v$, false, $v$[1, 2, 3, 4] → (2+3)/2 = 2.5$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_med_outlier_ignored$v$, $v$[10, 20, 200] → 20 (与 mean 76.67 不同, 中值滤波鲁棒)$v$, false, $v$[10, 20, 200] → 20 (与 mean 76.67 不同, 中值滤波鲁棒)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_med_unsorted$v$, $v$[5, 1, 3, 2, 4] → 3 (中值)$v$, false, $v$[5, 1, 3, 2, 4] → 3 (中值)$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_med_two_distinct$v$, $v$两元素 [42, 100] median=71 (避 identity 单元素巧合)$v$, false, $v$两元素 [42, 100] median=71 (避 identity 单元素巧合)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_med_raises_on_empty$v$, $v$med raises on empty$v$, false, $v$med raises on empty$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_med_raises_on_non_list$v$, $v$med raises on non list$v$, false, $v$med raises on non list$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_gauss_size3_sigma1$v$, $v$size=3 sigma=1: G(-1)≈0.2420, G(0)≈0.3989, G(1)≈0.2420 归一化: sum=0.8829, [0.2741, 0.4519, 0.2741]$v$, false, $v$size=3 sigma=1: G(-1)≈0.2420, G(0)≈0.3989, G(1)≈0.2420 归一化: sum=0.8829, [0.2741, 0.4519, 0.2741]$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_gauss_size1$v$, $v$size=1 → [1.0]$v$, true, $v$size=1 → [1.0]$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_gauss_size5_sigma1$v$, $v$size=5 sigma=1: 对称 + 总和 1$v$, true, $v$size=5 sigma=1: 对称 + 总和 1$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_gauss_large_sigma$v$, $v$大 sigma → 接近均匀$v$, true, $v$大 sigma → 接近均匀$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_gauss_small_sigma$v$, $v$小 sigma → 集中中心$v$, true, $v$小 sigma → 集中中心$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_gauss_raises_on_even_size$v$, $v$gauss raises on even size$v$, true, $v$gauss raises on even size$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_gauss_raises_on_zero_sigma$v$, $v$gauss raises on zero sigma$v$, true, $v$gauss raises on zero sigma$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_gauss_raises_on_non_int_size$v$, $v$gauss raises on non int size$v$, true, $v$gauss raises on non int size$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_f1d_simple$v$, $v$values=[1,2,3], kernel=[1,1] → [1+2, 2+3] = [3, 5]$v$, true, $v$values=[1,2,3], kernel=[1,1] → [1+2, 2+3] = [3, 5]$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_f1d_identity_kernel$v$, $v$kernel=[1] → 输出 = 输入$v$, true, $v$kernel=[1] → 输出 = 输入$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_f1d_average_kernel$v$, $v$values=[1,2,3,4,5], kernel=[1/3,1/3,1/3] → [2, 3, 4]$v$, true, $v$values=[1,2,3,4,5], kernel=[1/3,1/3,1/3] → [2, 3, 4]$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_f1d_kernel_equals_input$v$, $v$kernel 长度 = values, 输出长度 1$v$, true, $v$kernel 长度 = values, 输出长度 1$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_f1d_negative_kernel$v$, $v$kernel 含负值$v$, true, $v$kernel 含负值$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_f1d_raises_on_kernel_too_long$v$, $v$f1d raises on kernel too long$v$, true, $v$f1d raises on kernel too long$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_f1d_raises_on_empty$v$, $v$f1d raises on empty$v$, true, $v$f1d raises on empty$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_f1d_raises_on_non_list$v$, $v$f1d raises on non list$v$, true, $v$f1d raises on non list$v$, NULL, 30)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
