-- CV7: 特征检测 (Harris / SIFT 原理)
-- practice_id=9, order_in_practice=7, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$特征检测 (Harris / SIFT 原理)$v$,
        'PRACTICE',
        7,
        $v$hard$v$,
        $v$## 特征点的本质与作用

## 1.1 什么是特征点

特征点 (feature point / keypoint) 是图像中**局部独特、可重复检出**的位置, 比如:
- **角点 (corner)**: 两条边交汇处, x 和 y 方向梯度都强
- **斑点 (blob)**: 一个圆形小区域, 中心与周围值差异大
- **边缘点**: 沿一个方向梯度强, 垂直方向弱

角点是最常用的特征点 — 它在多个方向都有强梯度, 即使图像有光照变化、小幅旋转、放缩, 角点位置仍然相对稳定。

## 1.2 特征点的两个属性

工程中一个有用的特征点必须有两个属性:
- **位置 (location)**: (x, y) 坐标
- **描述子 (descriptor)**: 一个固定维度的向量, 编码了该点周围区域的"长相"

位置告诉"在哪里", 描述子告诉"长什么样"。两张图相同物体的特征点, 描述子向量应该相似 (距离小)。

## 1.3 应用场景

- **图像拼接 (panorama)**: 找两张图重叠区的对应特征点 → 估计变换 → 拼接
- **3D 重建**: 多视角图像的特征对应 → 三角测量恢复深度
- **物体识别**: 已知物体的特征 vs 待检图的特征, 找匹配
- **SLAM**: 视觉定位 + 建图依赖跨帧的特征对应

传统手工设计特征 (Harris, SIFT, ORB) 在 2010 年前是主流, 现在仍在工业级低算力场景使用。


## Harris 角点响应

## 2.1 结构张量 (Structure Tensor)

给定图像在某点的 x/y 梯度 $I_x, I_y$ (复习 CV05 Sobel), 在该点周围窗口求和得到 2x2 矩阵:

$M = \sum_{w} \begin{pmatrix} I_x^2 & I_x I_y \\ I_x I_y & I_y^2 \end{pmatrix} = \begin{pmatrix} I_{xx} & I_{xy} \\ I_{xy} & I_{yy} \end{pmatrix}$

记号: $I_{xx} = \sum I_x^2$, $I_{yy} = \sum I_y^2$, $I_{xy} = \sum I_x I_y$。$M$ 是对称矩阵。

## 2.2 特征值与角点判别

$M$ 的两个特征值 $\lambda_1, \lambda_2$ 反映该点局部的梯度强度结构:
- $\lambda_1 \approx \lambda_2 \approx 0$: 平坦区, 不是特征点
- $\lambda_1 \gg \lambda_2$ 或反之: 边缘点, 单方向梯度强
- $\lambda_1, \lambda_2$ 都大: 角点, 多方向梯度都强

## 2.3 Harris 响应公式

直接算特征值需要解二次方程, 工程上 Harris 用一个**响应函数 R**, 等价于特征值判别但只用矩阵元素:

$R = \det(M) - k \cdot \text{trace}(M)^2$

其中:
- $\det(M) = I_{xx} \cdot I_{yy} - I_{xy}^2 = \lambda_1 \lambda_2$
- $\text{trace}(M) = I_{xx} + I_{yy} = \lambda_1 + \lambda_2$
- $k$: 经验常数, 通常取 $k = 0.04 \sim 0.06$ (本关默认 0.04)

响应解读:
- $R > 0$, 数值大: 角点 (两个特征值都大)
- $R < 0$: 边缘 (两特征值差距大)
- $R \approx 0$: 平坦区

## 2.4 局部极值判断

Harris 响应图上, 不是每个 $R > 0$ 的点都是角点, 还要在 3x3 邻域内是局部最大值, 才算真角点。这就是"局部极值筛选" — 给定 3x3 窗口, 判断中心是否大于所有 8 个邻居 (max), 或小于所有邻居 (min), 或都不是 (neither)。

工程实务: 角点检测先算响应图, 再做局部极值筛选, 最后阈值化得到稀疏角点。


## SIFT 描述子与 Hessian

## 3.1 SIFT 概览

SIFT (Scale-Invariant Feature Transform) 是经典的特征点 + 描述子算法, 主要解决"图像放缩后特征仍可对应"的问题。SIFT 流程:

1. **尺度空间极值**: 在多尺度 (不同 sigma 的高斯金字塔) 找极值点
2. **精确定位**: 二阶泰勒展开亚像素精度
3. **方向赋值**: 每个特征点赋一个主方向 (旋转不变性)
4. **描述子计算**: 4x4 子区域 × 8 方向直方图 = **128 维向量**

关键事实: SIFT 描述子的总维度 = **方向数 × 子块数**。标准 SIFT 用 8 个方向 × 16 个子块 (4×4 网格) = **128**。本关函数接收 (num_orientations, num_blocks) 参数, 返回乘积; 标准参数 (8, 16) 对应工程默认 128。

## 3.2 Hessian 矩阵的作用

Hessian 矩阵是图像二阶导数构成的 2x2 矩阵:

$H = \begin{pmatrix} I_{xx}' & I_{xy}' \\ I_{xy}' & I_{yy}' \end{pmatrix}$ (对称)

其中 $I_{xx}'$ 是图像对 x 二阶导, $I_{xy}'$ 是混合二阶导。Hessian 的特征值反映该点的"曲率结构", SIFT 用它过滤掉边缘响应 (边缘对应 Hessian 一大一小, 不是真特征点)。

## 3.3 2x2 对称矩阵特征值公式

对称 $H = \begin{pmatrix} a & b \\ b & d \end{pmatrix}$, 特征值通过特征方程 $\det(H - \lambda I) = 0$ 求得:

$(a - \lambda)(d - \lambda) - b^2 = 0$
$\lambda^2 - (a+d) \lambda + (ad - b^2) = 0$

用二次公式:

$\lambda_{1,2} = \frac{(a+d) \pm \sqrt{(a-d)^2 + 4b^2}}{2}$

约定: $\lambda_1$ 是大的, $\lambda_2$ 是小的 (取 + 与 - 分支)。

$(a-d)^2 + 4b^2 \geq 0$ 永远成立 (对称矩阵特征值都实数), 所以根号永远合法。

## 3.4 业务案例: 老照片拼接

场景: 给定两张老照片, 内容有部分重叠, 要拼成一张全景图。

流水线:
1. 灰度 + 滤波 (CV02, CV04 复习)
2. Sobel 求梯度 (CV05 复习)
3. **Harris 角点响应** (本关) 找候选特征点
4. 局部极值筛选 + 阈值化 → 稀疏角点
5. **SIFT 描述子** (本关原理) 编码每个角点的局部外观
6. 跨图特征匹配 → 估计单应变换 → 拼接

工程实务: 角点+描述子是经典 CV 的"基础设施", 即使深度学习时代, 工业级低算力 SLAM 仍在使用。

## 3.5 工程口诀

- **角点 = 多方向梯度强**: Harris 响应是判别的基础
- **响应不够还要局部最大**: 极值筛选过滤伪角点
- **SIFT 描述子 128 维**: 工程默认 (8 方向 × 16 子块), 不要随意改
- **Hessian 特征值看曲率**: 过滤边缘伪特征
- **对称 2x2 用闭式公式**: 不要数值迭代, 浪费算力

$v$,
        $v${"questions": [{"id": "q07-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv07.py 中的 4 个函数; 评测以 test_cv07.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_harris_corner_strong$v$, $v$Ixx=10, Iyy=10, Ixy=0, k=0.04 → det=100, trace=20, R = 100 - 0.04*400 = 84$v$, false, $v$Ixx=10, Iyy=10, Ixy=0, k=0.04 → det=100, trace=20, R = 100 - 0.04*400 = 84$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_harris_flat_region$v$, $v$全 0 → R = 0$v$, false, $v$全 0 → R = 0$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_harris_edge_one_direction$v$, $v$Ixx=100, Iyy=0.01, Ixy=0, k=0.04 → det=1, trace=100.01, R = 1 - 0.04*10002 ≈ -399.08$v$, false, $v$Ixx=100, Iyy=0.01, Ixy=0, k=0.04 → det=1, trace=100.01, R = 1 - 0.04*10002 ≈ -399.08$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_harris_with_cross_term$v$, $v$Ixx=5, Iyy=5, Ixy=2, k=0.04 → det = 25 - 4 = 21, trace = 10, R = 21 - 0.04*100 = 17$v$, false, $v$Ixx=5, Iyy=5, Ixy=2, k=0.04 → det = 25 - 4 = 21, trace = 10, R = 21 - 0.04*100 = 17$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_harris_default_k$v$, $v$k 默认应该是 0.04: Ixx=Iyy=2, Ixy=0 → det=4, trace=4, R = 4 - 0.04*16 = 3.36$v$, false, $v$k 默认应该是 0.04: Ixx=Iyy=2, Ixy=0 → det=4, trace=4, R = 4 - 0.04*16 = 3.36$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_harris_custom_k$v$, $v$k=0.06: Ixx=Iyy=2, Ixy=0 → R = 4 - 0.06*16 = 3.04$v$, false, $v$k=0.06: Ixx=Iyy=2, Ixy=0 → R = 4 - 0.06*16 = 3.04$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_harris_raises_on_string$v$, $v$harris raises on string$v$, false, $v$harris raises on string$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_sift_standard_8x16$v$, $v$标准 SIFT (8, 16) → 128$v$, false, $v$标准 SIFT (8, 16) → 128$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_sift_smaller_4x16$v$, $v$(4, 16) → 64$v$, false, $v$(4, 16) → 64$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_sift_8x8$v$, $v$(8, 8) → 64$v$, false, $v$(8, 8) → 64$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_sift_larger_16x16$v$, $v$(16, 16) → 256$v$, false, $v$(16, 16) → 256$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_sift_minimum$v$, $v$(1, 1) → 1 (boundary)$v$, false, $v$(1, 1) → 1 (boundary)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_sift_raises_on_zero$v$, $v$sift raises on zero$v$, false, $v$sift raises on zero$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_sift_raises_on_negative$v$, $v$sift raises on negative$v$, false, $v$sift raises on negative$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_sift_raises_on_non_int$v$, $v$sift raises on non int$v$, true, $v$sift raises on non int$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_extrema_max$v$, $v$中心最大: 中心=10, 邻居都 < 10$v$, true, $v$中心最大: 中心=10, 邻居都 < 10$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_extrema_min$v$, $v$中心最小: 中心=-1, 邻居都 > -1$v$, true, $v$中心最小: 中心=-1, 邻居都 > -1$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_extrema_neither_tied_max$v$, $v$中心 = 一个邻居 (不严格 > ): neither$v$, true, $v$中心 = 一个邻居 (不严格 > ): neither$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_extrema_neither_tied_min$v$, $v$中心 = 邻居 (相等不算 strict min)$v$, true, $v$中心 = 邻居 (相等不算 strict min)$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_extrema_neither_middle$v$, $v$中心既不最大也不最小$v$, true, $v$中心既不最大也不最小$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_extrema_max_negative$v$, $v$中心 -1 是最大 (其他更小)$v$, true, $v$中心 -1 是最大 (其他更小)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_extrema_raises_on_wrong_shape$v$, $v$extrema raises on wrong shape$v$, true, $v$extrema raises on wrong shape$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_extrema_raises_on_non_list$v$, $v$extrema raises on non list$v$, true, $v$extrema raises on non list$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_hessian_with_offdiag_symmetric$v$, $v$a=2, b=1, d=2 → ((4) ± sqrt(0+4))/2 = (4±2)/2 = 3, 1$v$, true, $v$a=2, b=1, d=2 → ((4) ± sqrt(0+4))/2 = (4±2)/2 = 3, 1$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_hessian_with_offdiag_general$v$, $v$a=4, b=2, d=1 → trace=5, sqrt((4-1)²+4·4)=sqrt(25)=5 → (5±5)/2 = 5, 0 (boundary 0 特征值)$v$, true, $v$a=4, b=2, d=1 → trace=5, sqrt((4-1)²+4·4)=sqrt(25)=5 → (5±5)/2 = 5, 0 (boundary 0 特征值)$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_hessian_offdiag_3$v$, $v$a=5, b=2, d=2 → trace=7, sqrt(9+16)=5 → (7±5)/2 = 6, 1$v$, true, $v$a=5, b=2, d=2 → trace=7, sqrt(9+16)=5 → (7±5)/2 = 6, 1$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_hessian_ordering$v$, $v$大值在前: a=1, b=2, d=4 → trace=5, sqrt(9+16)=5 → (5±5)/2 = 5, 0$v$, true, $v$大值在前: a=1, b=2, d=4 → trace=5, sqrt(9+16)=5 → (5±5)/2 = 5, 0$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_hessian_negative_eigenvalues$v$, $v$a=-1, b=2, d=-4 → trace=-5, sqrt(9+16)=5 → (-5±5)/2 = 0, -5$v$, true, $v$a=-1, b=2, d=-4 → trace=-5, sqrt(9+16)=5 → (-5±5)/2 = 0, -5$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_hessian_raises_on_string$v$, $v$hessian raises on string$v$, true, $v$hessian raises on string$v$, NULL, 29)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
