-- CV2: 图像基础与色彩空间
-- practice_id=9, order_in_practice=2, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$图像基础与色彩空间$v$,
        'PRACTICE',
        2,
        $v$beginner$v$,
        $v$## RGB 与灰度

## 1.1 RGB 三通道

数字图像最常用 RGB (红绿蓝) 三通道表示。每个像素是 (R, G, B) 三元组, 各分量取值 0-255 (uint8) 或 0-1 (归一化 fp32)。

RGB 是"加色光" 模型 — (255, 255, 255) 是白, (0, 0, 0) 是黑, (255, 0, 0) 是纯红。这与人眼三色锥细胞 (L/M/S) 大致对应, 但不完全等同人类视觉。

## 1.2 RGB 到灰度的加权平均

把彩色图转灰度有多种方法, 最常用的是基于人眼亮度感知的加权:

$\text{gray} = 0.299 R + 0.587 G + 0.114 B$

系数反映人眼对绿色最敏感、对蓝色最不敏感。简单平均 $(R+G+B)/3$ 看起来接近, 但绿色草地等场景明显偏暗。

工程实务: OpenCV 的 cvtColor BGR→GRAY 用的是同一公式 (R/G/B 系数对应)。

## 1.3 灰度图的优势

- **存储**: 单通道, 是 RGB 的 1/3 大小
- **计算**: 很多 CV 算法 (边缘/形态学/特征点) 只需灰度
- **抗光照**: 灰度对色调变化不敏感, 比 RGB 鲁棒

但会丢失色彩信息, 业务任务需要色彩判别 (如交通灯识别) 时不能转灰度。


## HSV 色彩空间

## 2.1 RGB 的不足

RGB 是设备友好 (显示器、相机) 但人类不友好 — 用户描述颜色时说"暖红色"、"深红色"、"鲜红色", 这些与 R/G/B 数值的关系不直观。

## 2.2 HSV 三分量

- **H (Hue, 色相)**: 0-360°, 红=0, 绿=120, 蓝=240
- **S (Saturation, 饱和度)**: 0-1, 0 是灰色, 1 是纯色
- **V (Value, 亮度)**: 0-1, 0 是黑, 1 是最亮

HSV 把"颜色种类" (H) 与"鲜艳/暗淡" (S) 与"亮/暗" (V) 解耦, 业务上更易用 — 例如"识别红色物体"用 H ∈ [0, 10] ∪ [350, 360] 即可, 不论物体在什么光照下。

## 2.3 RGB → HSV 公式

给定 (R, G, B) ∈ [0, 1]:

$V = \max(R, G, B)$
$S = (V - \min(R, G, B)) / V$ 当 $V > 0$, 否则 $S = 0$
$H = \begin{cases} 60 \cdot (G - B) / (V - \min) & V = R \\ 60 \cdot (2 + (B - R) / (V - \min)) & V = G \\ 60 \cdot (4 + (R - G) / (V - \min)) & V = B \end{cases}$

$H$ 取值在 0-360°, 计算结果如果为负要加 360。

公式看起来复杂, 核心是: 用 max/min 算亮度与饱和度, 用三角形位置算色相。本关只要求实现单个像素的 RGB→HSV 转换。


## 二值化与直方图

## 3.1 二值化

二值化 (Binarization) 把灰度图变成只有 0 和 255 (或 0/1) 两种值, 是边缘检测、形态学等算法的预处理步骤。

$b = \begin{cases} 255 & x > T \\ 0 & x \leq T \end{cases}$

$T$ 是阈值, 默认 128 (灰度范围 0-255 的中点)。

工程实务: 固定阈值简单但对光照敏感, 进阶方法 (Otsu / 自适应阈值) 自动选择 — 后续课程展开。本关只要求固定阈值。

## 3.2 直方图

像素值分布的统计图, 横轴是值 (或 bin), 纵轴是该值的出现频次。

给定像素列表与 bin 数 $K$, 直方图把 [0, max_value] 等分成 $K$ 段, 每段统计落入的像素数。

公式:
$\text{bin}_i$ 范围 = $[i \cdot \text{step}, (i+1) \cdot \text{step})$, 其中 $\text{step} = \frac{\text{max\_value} + 1}{K}$

最后一个 bin 包含 max_value (闭区间)。

用途:
- 看图像曝光: 直方图集中在低值 → 暗; 集中在高值 → 亮; 分散均匀 → 对比度好
- 选阈值: 直方图双峰分布 (前景 + 背景) 时, 双峰之间的谷值就是好阈值


## 业务案例: 交通灯识别

## 4.1 场景

自动驾驶系统识别红绿灯状态 (红/黄/绿), 输入摄像头帧 (1280×720 RGB), 输出当前灯色。

传统 (非神经网络) 流水线:
1. RGB → HSV (色彩空间更易判别)
2. 取 H 通道, 按色相阈值分类:
   - H ∈ [0, 15] ∪ [345, 360] → 红灯候选
   - H ∈ [40, 75] → 黄灯候选 (绿黄之间)
   - H ∈ [75, 165] → 绿灯候选
3. 对每色相候选区取像素数, 最大者 = 当前灯色

## 4.2 为什么不直接用 RGB

- 太阳光照变化让 RGB 数值剧变 (如阴天的红 (180, 30, 30) vs 晴天 (255, 50, 50)), 阈值难定
- HSV 把光照 (V) 解耦, 红色就是 H 接近 0/360, 不论亮度

工程实务: 现代 CV 用神经网络 (NN09 CNN) 直接从 RGB 学色彩判别, 鲁棒性更高但需要大量标注数据。传统色彩空间方法在数据少 / 实时性高的场景仍有用武之地。

## 4.3 工程口诀

- **任务先选色彩空间**: 判别色彩用 HSV, 计算结构用灰度
- **二值化前先归一化**: 不同来源图像范围不同 (0-255 vs 0-1)
- **直方图是诊断工具**: 看图像质量第一步看直方图分布
- **不要 RGB 等权平均做灰度**: 用感知加权 (0.299/0.587/0.114) 才是标准

$v$,
        $v${"questions": [{"id": "q02-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv02.py 中的 4 个函数; 评测以 test_cv02.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_g_pure_red$v$, $v$R=255 → 0.299*255 = 76.245$v$, false, $v$R=255 → 0.299*255 = 76.245$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_g_pure_green$v$, $v$G=255 → 0.587*255 = 149.685$v$, false, $v$G=255 → 0.587*255 = 149.685$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_g_pure_blue$v$, $v$B=255 → 0.114*255 = 29.07$v$, false, $v$B=255 → 0.114*255 = 29.07$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_g_white$v$, $v$255,255,255 → 255$v$, false, $v$255,255,255 → 255$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_g_black$v$, $v$0,0,0 → 0$v$, false, $v$0,0,0 → 0$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_g_raises_on_wrong_length$v$, $v$g raises on wrong length$v$, false, $v$g raises on wrong length$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_g_raises_on_out_of_range$v$, $v$g raises on out of range$v$, false, $v$g raises on out of range$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_g_raises_on_non_tuple$v$, $v$g raises on non tuple$v$, false, $v$g raises on non tuple$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_hsv_pure_red$v$, $v$(1,0,0) → H=0, S=1, V=1$v$, false, $v$(1,0,0) → H=0, S=1, V=1$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_hsv_pure_green$v$, $v$(0,1,0) → H=120, S=1, V=1$v$, false, $v$(0,1,0) → H=120, S=1, V=1$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_hsv_pure_blue$v$, $v$(0,0,1) → H=240, S=1, V=1$v$, false, $v$(0,0,1) → H=240, S=1, V=1$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_hsv_white$v$, $v$(1,1,1) → S=0, V=1, H 不重要 (灰色)$v$, false, $v$(1,1,1) → S=0, V=1, H 不重要 (灰色)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_hsv_black$v$, $v$(0,0,0) → V=0, S=0$v$, false, $v$(0,0,0) → V=0, S=0$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_hsv_raises_on_wrong_length$v$, $v$hsv raises on wrong length$v$, false, $v$hsv raises on wrong length$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_hsv_raises_on_out_of_range$v$, $v$hsv raises on out of range$v$, false, $v$hsv raises on out of range$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_hsv_raises_on_non_tuple$v$, $v$hsv raises on non tuple$v$, false, $v$hsv raises on non tuple$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_thresh_basic$v$, $v$[100, 150, 200] T=128 → [0, 255, 255]$v$, true, $v$[100, 150, 200] T=128 → [0, 255, 255]$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_thresh_at_boundary$v$, $v$T=128: x=128 → 0 (>= 不算), x=129 → 255$v$, true, $v$T=128: x=128 → 0 (>= 不算), x=129 → 255$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_thresh_low_threshold$v$, $v$T=10: 大部分都是 255$v$, true, $v$T=10: 大部分都是 255$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_thresh_high_threshold$v$, $v$T=240: 大部分都是 0$v$, true, $v$T=240: 大部分都是 0$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_thresh_default_128$v$, $v$默认 threshold=128$v$, true, $v$默认 threshold=128$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_thresh_raises_on_empty$v$, $v$thresh raises on empty$v$, true, $v$thresh raises on empty$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_thresh_raises_on_invalid_threshold$v$, $v$thresh raises on invalid threshold$v$, true, $v$thresh raises on invalid threshold$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_thresh_raises_on_non_list$v$, $v$thresh raises on non list$v$, true, $v$thresh raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_hist_uniform$v$, $v$[0, 50, 100, 150, 200, 255] n_bins=5: 每 bin 范围 ~51, 大致均匀$v$, true, $v$[0, 50, 100, 150, 200, 255] n_bins=5: 每 bin 范围 ~51, 大致均匀$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_hist_all_same$v$, $v$[100]*10 n_bins=4 max=255: 全在一个 bin$v$, true, $v$[100]*10 n_bins=4 max=255: 全在一个 bin$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_hist_extremes$v$, $v$[0, 0, 255, 255] n_bins=2 max=255: 各 bin 2 个$v$, true, $v$[0, 0, 255, 255] n_bins=2 max=255: 各 bin 2 个$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_hist_max_value_inclusive$v$, $v$max_value 必须落在最后 bin$v$, true, $v$max_value 必须落在最后 bin$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_hist_smaller_max$v$, $v$[0, 8, 16] n_bins=4 max=16: step=17/4≈4.25 bin 0: 0-3, bin 1: 4-8, bin 2: 9-12, bin 3: 13-16$v$, true, $v$[0, 8, 16] n_bins=4 max=16: step=17/4≈4.25 bin 0: 0-3, bin 1: 4-8, bin 2: 9-12, bin 3: 13-16$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_hist_raises_on_empty$v$, $v$hist raises on empty$v$, true, $v$hist raises on empty$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_hist_raises_on_zero_bins$v$, $v$hist raises on zero bins$v$, true, $v$hist raises on zero bins$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_hist_raises_on_non_list$v$, $v$hist raises on non list$v$, true, $v$hist raises on non list$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
