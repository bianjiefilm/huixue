-- CV3: 图像几何变换
-- practice_id=9, order_in_practice=3, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$图像几何变换$v$,
        'PRACTICE',
        3,
        $v$intermediate$v$,
        $v$## 几何变换在 CV 中的位置

## 1.1 几何变换是什么

几何变换 (Geometric Transformation) 是图像处理的基础工具 — 改变像素的空间位置, 不改变像素值。三种基本变换:

- **平移 (Translation)**: 把图像整体移动 $(\Delta x, \Delta y)$
- **旋转 (Rotation)**: 绕一个中心点旋转 $\theta$ 角度
- **缩放 (Scaling)**: 沿 x/y 轴各向异性缩放 $(f_x, f_y)$

复合变换 (先旋转再平移) 用**仿射变换 (Affine)** 统一表达。

## 1.2 几何变换的工程用途

- **数据增强**: 训练时随机平移/旋转/缩放, 让模型学到平移/旋转不变的特征
- **图像配准**: 把不同时间/角度的图像对齐到同一坐标系
- **校正**: 拍照时倾斜的文档校正成正面
- **图像拼接**: 多张照片拼成全景

在传统 CV (无神经网络) 时代, 几何变换是几乎所有任务的预处理步骤。神经网络时代仍然重要, 因为数据增强是训练的标配。

## 1.3 像素值如何随坐标变化

几何变换改变坐标 $(x, y) \to (x', y')$。新位置的像素值通过**反向插值**得到:

1. 对每个目标像素 $(x', y')$ 计算它对应的原图坐标 $(x, y)$ (反向变换)
2. 在原图坐标 $(x, y)$ 处插值取像素值

插值方法: 最近邻 (nearest, 快但锐) / 双线性 (bilinear, 默认) / 双三次 (bicubic, 慢但平滑)。本关只关注坐标变换公式, 像素值插值在工程框架 (cv2.warpAffine) 自动处理。


## 平移、旋转、缩放公式

## 2.1 平移

最简单: $(x', y') = (x + \Delta x, y + \Delta y)$

没有什么需要解释的, 但工程中要注意"平移之后像素是否还在图像范围内" — 超出范围的部分通常用 0 (黑) 或 reflect 填充。

## 2.2 旋转

绕原点 (0, 0) 顺时针旋转 $\theta$ 度:

$x' = x \cos\theta + y \sin\theta$
$y' = -x \sin\theta + y \cos\theta$

绕任意中心 $(c_x, c_y)$ 旋转: 先平移到原点 → 旋转 → 平移回:

$x' = (x - c_x) \cos\theta + (y - c_y) \sin\theta + c_x$
$y' = -(x - c_x) \sin\theta + (y - c_y) \cos\theta + c_y$

工程实务: $\theta$ 单位是度还是弧度要明确, OpenCV 用度, numpy 用弧度。本关函数接收度, 内部转弧度。

## 2.3 缩放

各向异性 (x/y 缩放因子可不同):

$x' = f_x \cdot x$
$y' = f_y \cdot y$

新图尺寸: $W' = \lfloor W \cdot f_x \rfloor$, $H' = \lfloor H \cdot f_y \rfloor$ (向下取整, 避免溢出)。

$f_x = f_y$ 时是各向同性缩放 (CV01 已介绍 "保持长宽比" 是 $f_x = f_y$ 的特例)。

## 2.4 三种变换的复合

多个变换的顺序非常重要 — 旋转后再平移与平移后再旋转结果不同。复合变换通常用矩阵表达统一处理 (下一节)。


## 仿射变换的矩阵表达

## 3.1 仿射矩阵

把"平移 + 旋转 + 缩放"用一个 2×3 矩阵 $A$ 统一表达:

$\begin{pmatrix} x' \\ y' \end{pmatrix} = A \begin{pmatrix} x \\ y \\ 1 \end{pmatrix}$

其中 $A = \begin{pmatrix} a_{00} & a_{01} & a_{02} \\ a_{10} & a_{11} & a_{12} \end{pmatrix}$

具体:
$x' = a_{00} \cdot x + a_{01} \cdot y + a_{02}$
$y' = a_{10} \cdot x + a_{11} \cdot y + a_{12}$

## 3.2 几种典型矩阵

**平移** $(\Delta x, \Delta y)$:
$A = \begin{pmatrix} 1 & 0 & \Delta x \\ 0 & 1 & \Delta y \end{pmatrix}$

**缩放** $(f_x, f_y)$:
$A = \begin{pmatrix} f_x & 0 & 0 \\ 0 & f_y & 0 \end{pmatrix}$

**旋转 (绕原点) $\theta$**:
$A = \begin{pmatrix} \cos\theta & \sin\theta & 0 \\ -\sin\theta & \cos\theta & 0 \end{pmatrix}$

## 3.3 复合变换通过矩阵乘法

把多个仿射矩阵合并成一个矩阵, 一次变换完成所有效果。这是 OpenCV warpAffine 的工作方式 — 你给一个 2×3 矩阵, 它把多个变换的效果一次施加。

工程实务: 复合变换不要逐步算, 矩阵直接乘起来计算量小且数值更稳。


## 业务案例: 图像数据增强

## 4.1 场景

某医疗影像公司训练肺部 CT 异常检测网络, 标注成本高, 只有 1000 张标注图像。直接训练会过拟合 (NN08), 用数据增强扩充到等效 5000-10000 张。

## 4.2 数据增强的几何部分

对每张原图, 训练时随机施加:
- 平移: $\Delta x, \Delta y \sim U(-20, 20)$ 像素 (模拟拍摄位置偏移)
- 旋转: $\theta \sim U(-15°, 15°)$ (模拟拍摄角度差)
- 缩放: $f \sim U(0.9, 1.1)$ (模拟距离差异)

合并成一个 2×3 仿射矩阵, 一次施加。注意: 标注 (病灶位置) 也要做相同变换才能保持对齐。

## 4.3 增强的边界

- **过度增强**: 旋转 90° 让"猫"变成"竖向猫", 类别仍是猫 — 但医学影像旋转会让"右肺"变成"左肺", 改变语义, 不能这么做
- **超出范围**: 平移 100 像素让肺消失出图像, 训练样本无效
- **保持标注一致性**: 增强必须连同标注一起变换, 否则学错位置

不同任务对增强强度的容忍度不同, 需要业务侧介入决定。

## 4.4 工程口诀

- **数据增强是标配**: 现代 CV 训练都做, 通常 +5-10 个百分点准确率
- **变换前先校验语义**: 旋转/翻转可能改变标签语义, 必须人工审
- **批量用矩阵, 不要逐步施加**: 多次插值会累积模糊
- **角度单位要明确**: 度 vs 弧度搞错, debug 数小时

$v$,
        $v${"questions": [{"id": "q03-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv03.py 中的 4 个函数; 评测以 test_cv03.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_t_basic$v$, $v$t basic$v$, false, $v$t basic$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_t_zero$v$, $v$t zero$v$, false, $v$t zero$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_t_negative$v$, $v$t negative$v$, false, $v$t negative$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_t_floats$v$, $v$t floats$v$, false, $v$t floats$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_t_origin$v$, $v$t origin$v$, false, $v$t origin$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_t_raises_on_non_numeric$v$, $v$t raises on non numeric$v$, false, $v$t raises on non numeric$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_r_zero_angle$v$, $v$0° 旋转 → 不变$v$, false, $v$0° 旋转 → 不变$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_r_90_around_origin$v$, $v$点 (1, 0) 绕原点顺时针 90° → (0, -1)$v$, false, $v$点 (1, 0) 绕原点顺时针 90° → (0, -1)$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_r_180_around_origin$v$, $v$点 (3, 4) 绕原点 180° → (-3, -4)$v$, false, $v$点 (3, 4) 绕原点 180° → (-3, -4)$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_r_around_custom_center$v$, $v$点 (2, 0) 绕 (1, 0) 旋转 180° → (0, 0)$v$, false, $v$点 (2, 0) 绕 (1, 0) 旋转 180° → (0, 0)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_r_360_returns$v$, $v$360° → 不变 (含浮点精度容差)$v$, false, $v$360° → 不变 (含浮点精度容差)$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_r_raises_on_non_numeric$v$, $v$r raises on non numeric$v$, false, $v$r raises on non numeric$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_sd_basic$v$, $v$100×50, fx=2.0, fy=3.0 → (200, 150)$v$, false, $v$100×50, fx=2.0, fy=3.0 → (200, 150)$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_sd_half$v$, $v$1920×1080, fx=fy=0.5 → (960, 540)$v$, false, $v$1920×1080, fx=fy=0.5 → (960, 540)$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_sd_anisotropic$v$, $v$100×100, fx=2.0, fy=0.5 → (200, 50)$v$, true, $v$100×100, fx=2.0, fy=0.5 → (200, 50)$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_sd_floor$v$, $v$101×201, fx=fy=0.5 → (50, 100) (向下取整)$v$, true, $v$101×201, fx=fy=0.5 → (50, 100) (向下取整)$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_sd_no_change$v$, $v$fx=fy=1 → 不变$v$, true, $v$fx=fy=1 → 不变$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_sd_raises_on_zero$v$, $v$sd raises on zero$v$, true, $v$sd raises on zero$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_sd_raises_on_negative_factor$v$, $v$sd raises on negative factor$v$, true, $v$sd raises on negative factor$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_sd_raises_on_non_int$v$, $v$sd raises on non int$v$, true, $v$sd raises on non int$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_aff_identity$v$, $v$单位矩阵 [[1,0,0],[0,1,0]] → (x, y) 不变$v$, true, $v$单位矩阵 [[1,0,0],[0,1,0]] → (x, y) 不变$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_aff_translation$v$, $v$平移矩阵 [[1,0,5],[0,1,7]] → (x+5, y+7)$v$, true, $v$平移矩阵 [[1,0,5],[0,1,7]] → (x+5, y+7)$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_aff_scale$v$, $v$缩放矩阵 [[2,0,0],[0,3,0]] → (2x, 3y)$v$, true, $v$缩放矩阵 [[2,0,0],[0,3,0]] → (2x, 3y)$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_aff_rotation_90$v$, $v$旋转 90° 矩阵 [[0,1,0],[-1,0,0]] → 点 (1, 0) → (0, -1)$v$, true, $v$旋转 90° 矩阵 [[0,1,0],[-1,0,0]] → 点 (1, 0) → (0, -1)$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_aff_complex$v$, $v$复合: 缩放 + 平移 [[2,0,1],[0,3,2]] 点 (1, 1) → (2*1+0+1, 0+3*1+2) = (3, 5)$v$, true, $v$复合: 缩放 + 平移 [[2,0,1],[0,3,2]] 点 (1, 1) → (2*1+0+1, 0+3*1+2) = (3, 5)$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_aff_raises_on_wrong_shape$v$, $v$matrix 不是 2×3 → ValueError$v$, true, $v$matrix 不是 2×3 → ValueError$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_aff_raises_on_non_list$v$, $v$aff raises on non list$v$, true, $v$aff raises on non list$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_aff_negative_input$v$, $v$点 (-2, -3) 缩放矩阵 [[2,0,0],[0,2,0]] → (-4, -6)$v$, true, $v$点 (-2, -3) 缩放矩阵 [[2,0,0],[0,2,0]] → (-4, -6)$v$, NULL, 28)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
