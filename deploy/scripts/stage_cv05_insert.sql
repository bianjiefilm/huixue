-- CV5: 边缘检测
-- practice_id=9, order_in_practice=5, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$边缘检测$v$,
        'PRACTICE',
        5,
        $v$intermediate$v$,
        $v$## 边缘的本质与作用

## 1.1 什么是边缘

边缘 (Edge) 是图像中**像素值剧烈变化**的位置 — 比如物体轮廓、阴影边界、纹理变化。在数学上, 边缘是图像的"梯度大"位置:

$\|\nabla I\| = \sqrt{(\partial I / \partial x)^2 + (\partial I / \partial y)^2}$

梯度大 → 边缘强; 梯度方向 → 边缘的"垂直方向"。

## 1.2 边缘检测的 CV 用途

- **轮廓提取**: 找到物体边界, 用于尺寸测量、缺陷检测
- **特征基础**: 后续课程的特征点检测 (角点) 都基于边缘
- **预处理**: 简化图像信息, 让后续算法关注重要结构

传统 CV 时代 (深度学习之前), 边缘检测是几乎所有任务的预处理步骤。深度学习时代仍然有用 — 工业检测/医学影像的特定任务用经典边缘算法比深度模型更鲁棒、可解释、不需要大量标注。

## 1.3 一阶导数与离散近似

连续图像的导数 $\partial I / \partial x$ 在数字图像中需要离散化。最简单的差分:

$G_x \approx I(x+1, y) - I(x-1, y)$

但这个近似对噪声敏感: 一个像素的随机抖动直接进入差分结果, 把"边缘"位置误判到平坦区域。Sobel 算子用 3×3 卷积, 同时对 x 方向求差分和对 y 方向"加权平均", 用平均换取鲁棒性。

## 1.4 二阶导数与零交叉 (拓展)

除了一阶导数, 二阶导数 $\nabla^2 I$ (Laplacian) 也能找边缘 — 边缘对应二阶导数的"零交叉点"。Laplacian 算子比 Sobel 更敏感但也更易受噪声影响, 工程上常用 LoG (Laplacian of Gaussian) 先平滑再求二阶导。本关只用一阶导数 (Sobel), Laplacian 作为知识储备。


## Sobel 算子

## 2.1 Sobel-x 算子

$S_x = \begin{pmatrix} -1 & 0 & 1 \\ -2 & 0 & 2 \\ -1 & 0 & 1 \end{pmatrix}$

物理含义: 中间行 (-2, 0, 2) 是中心行的差分, 上下行 (-1, 0, 1) 提供"加权平均" — 让导数估计对噪声更鲁棒。

## 2.2 Sobel-y 算子

$S_y = \begin{pmatrix} -1 & -2 & -1 \\ 0 & 0 & 0 \\ 1 & 2 & 1 \end{pmatrix}$

与 $S_x$ 转置后差一个符号 (因为 y 轴向下)。$S_y$ 是中间列差分 + 左右列加权。

## 2.3 梯度幅值

给定一个像素位置上 $G_x$ (Sobel-x 卷积结果) 与 $G_y$ (Sobel-y 卷积结果), 梯度幅值:

$\|\nabla I\| = \sqrt{G_x^2 + G_y^2}$

工程实务有时用 $|G_x| + |G_y|$ (L1 近似), 计算快但精度略差。本关用 L2 (sqrt 形式)。

梯度方向: $\theta = \arctan(G_y / G_x)$, 范围 $[-\pi, \pi]$。本关不要求方向计算, 重点在幅值。

## 2.4 边界处理

Sobel 卷积要看 3×3 邻域, 图像边缘 1 个像素没有完整邻域, 工程实现常用:
- **复制填充 (replicate)**: 边界像素复制到外面 — 默认安全选择
- **反射填充 (reflect)**: 镜像边界 — 对称纹理友好
- **零填充 (zero)**: 外面填 0 — 简单但边界会出现假边缘

本关函数只处理"中心像素邻域已就绪"的情况, 输入是已经卷积好的标量 $G_x, G_y$, 不涉及填充。


## Canny 双阈值与业务案例

## 3.1 Canny 算法的 5 步骤

Canny 边缘检测是工业级的标准流程:
1. **降噪**: 高斯滤波 (复习 CV04)
2. **梯度**: Sobel x/y 求梯度幅值与方向
3. **细化**: 沿梯度方向只保留局部最大像素 (让边缘单像素宽)
4. **双阈值**: 用高阈值 $T_h$ 与低阈值 $T_l$ 把梯度幅值分类
5. **滞后边缘连接**: weak 边缘只在与 strong 边缘连通时保留

本关聚焦第 4 步双阈值分类, 其他步骤工程框架 (cv2.Canny) 自动处理。

## 3.2 双阈值分类规则

给定一个像素位置的梯度幅值 $|G|$:

- $|G| \geq T_h$ → **strong** edge: 必是真边缘
- $T_l \leq |G| < T_h$ → **weak** edge: 候选边缘, 看是否与 strong 连通
- $|G| < T_l$ → **non-edge**: 几乎肯定不是边缘, 滤掉

经验: $T_h$ 通常是 $T_l$ 的 2-3 倍, 这是 OpenCV 默认的比例。

## 3.3 业务案例: 工业零件轮廓提取

场景: 流水线视觉检测, 从图像中提取零件轮廓, 测量尺寸是否合规。

流水线:
1. 灰度图 (复习 CV02 单通道转换)
2. 高斯滤波 (CV04, 去 CCD 噪声)
3. Sobel x/y 算子卷积 (本关)
4. 梯度幅值计算 (本关)
5. Canny 双阈值: $T_l = 50$, $T_h = 150$ (本关分类规则)
6. 细化 + 滞后连接得到最终边缘图
7. 轮廓提取 → 测量长度/面积 → 与设计规格对比

工程实务: 阈值必须根据具体场景调 (光照、零件材质、相机), 没有"一套阈值通用所有场景"的方案。

## 3.4 工程口诀

- **Sobel 是经典**: 简单 + 快 + 鲁棒, 工业首选
- **Canny 是标准流程**: 5 步全套是工业级方法
- **双阈值不是越严越好**: $T_h$ 太高漏边缘, 太低噪声当边缘
- **降噪先于求梯度**: Sobel 对噪声敏感, 必须先高斯

$v$,
        $v${"questions": [{"id": "q05-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv05.py 中的 4 个函数; 评测以 test_cv05.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_sx_shape$v$, $v$sx shape$v$, false, $v$sx shape$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_sx_full_kernel$v$, $v$Sobel-x 完整匹配$v$, false, $v$Sobel-x 完整匹配$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_sx_left_column_negative$v$, $v$左列 [-1, -2, -1]$v$, false, $v$左列 [-1, -2, -1]$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_sx_right_column_positive$v$, $v$右列 [1, 2, 1]$v$, false, $v$右列 [1, 2, 1]$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_sx_middle_row_max_abs$v$, $v$中间行权重绝对值更大: |k[1][0]|=2 > |k[0][0]|=1$v$, false, $v$中间行权重绝对值更大: |k[1][0]|=2 > |k[0][0]|=1$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_sy_shape$v$, $v$sy shape$v$, false, $v$sy shape$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_sy_full_kernel$v$, $v$Sobel-y 完整匹配$v$, false, $v$Sobel-y 完整匹配$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_sy_top_row_negative$v$, $v$顶行 [-1, -2, -1]$v$, false, $v$顶行 [-1, -2, -1]$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_sy_bottom_row_positive$v$, $v$底行 [1, 2, 1]$v$, false, $v$底行 [1, 2, 1]$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_sy_middle_column_max_abs$v$, $v$中间列权重绝对值更大$v$, false, $v$中间列权重绝对值更大$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_gm_pythagoras_3_4$v$, $v$3, 4 → 5$v$, false, $v$3, 4 → 5$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_gm_pythagoras_5_12$v$, $v$5, 12 → 13$v$, false, $v$5, 12 → 13$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_gm_pythagoras_8_15$v$, $v$8, 15 → 17$v$, false, $v$8, 15 → 17$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_gm_negative_pythagoras$v$, $v$-3, -4 → 5 (平方消符号)$v$, false, $v$-3, -4 → 5 (平方消符号)$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_gm_general_1_2$v$, $v$1, 2 → sqrt(5) ≈ 2.2361$v$, true, $v$1, 2 → sqrt(5) ≈ 2.2361$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_gm_general_2_3$v$, $v$2, 3 → sqrt(13) ≈ 3.6056$v$, true, $v$2, 3 → sqrt(13) ≈ 3.6056$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_gm_small_values$v$, $v$0.0001, 0.0002 → sqrt(5e-8) (极小值边界)$v$, true, $v$0.0001, 0.0002 → sqrt(5e-8) (极小值边界)$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_gm_raises_on_string$v$, $v$gm raises on string$v$, true, $v$gm raises on string$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_cc_strong_above_high$v$, $v$200, low=50, high=150 → strong$v$, true, $v$200, low=50, high=150 → strong$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_cc_strong_at_high$v$, $v$150, low=50, high=150 → strong (>= 高阈值)$v$, true, $v$150, low=50, high=150 → strong (>= 高阈值)$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_cc_strong_far_above$v$, $v$500, low=50, high=150 → strong$v$, true, $v$500, low=50, high=150 → strong$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_cc_weak_between$v$, $v$100, low=50, high=150 → weak$v$, true, $v$100, low=50, high=150 → weak$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_cc_weak_at_low$v$, $v$50, low=50, high=150 → weak (>= 低阈值, 边界)$v$, true, $v$50, low=50, high=150 → weak (>= 低阈值, 边界)$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_cc_non_edge_below_low$v$, $v$30, low=50, high=150 → non_edge$v$, true, $v$30, low=50, high=150 → non_edge$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_cc_non_edge_zero$v$, $v$0, low=50, high=150 → non_edge (boundary)$v$, true, $v$0, low=50, high=150 → non_edge (boundary)$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_cc_non_edge_just_below_low$v$, $v$49.999, low=50, high=150 → non_edge$v$, true, $v$49.999, low=50, high=150 → non_edge$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_cc_raises_on_low_ge_high$v$, $v$cc raises on low ge high$v$, true, $v$cc raises on low ge high$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_cc_raises_on_negative_magnitude$v$, $v$cc raises on negative magnitude$v$, true, $v$cc raises on negative magnitude$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_cc_raises_on_string$v$, $v$cc raises on string$v$, true, $v$cc raises on string$v$, NULL, 29)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
