-- CV8: 模板匹配与目标检测基础
-- practice_id=9, order_in_practice=8, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$模板匹配与目标检测基础$v$,
        'PRACTICE',
        8,
        $v$hard$v$,
        $v$## 模板匹配的原理

## 1.1 什么是模板匹配

模板匹配 (Template Matching) 是经典的目标定位方法: 给定一张**目标模板** (template, 小图) 和一张**待搜索图** (大图), 在大图上滑动模板, 计算每个位置的"相似度", 找到最相似的位置 = 模板出现的地方。

用途:
- **工业 OCR / 读码**: 在产品标签上找已知 logo / 数字模板
- **打印缺陷检测**: 找出与标准模板偏差最大的位置
- **简单跟踪**: 给定上一帧目标的小图, 在下一帧搜索

模板匹配是**"已知目标外观"**的方法, 无法处理目标外观大幅变化 (旋转、放缩、形变), 这些场景需要 CV07 的特征匹配或更强的方法。

## 1.2 滑动窗口扫描

给定大图 $W \times H$ 和模板 $w \times h$, 滑动窗口需要遍历所有可能位置:

- 模板左上角 $(x, y)$, $x \in [0, W - w]$, $y \in [0, H - h]$
- 步长 stride = $s$ (常用 1 = 全密集扫描)
- 总窗口数 = $\lfloor (W - w) / s \rfloor + 1$ 沿 x 方向, 类似沿 y。

工程实务: stride > 1 加速但漏检风险增大, 一般用 stride = 1 或 2。

## 1.3 滑窗输出形状公式

1D 简化版: 信号长 $N$, 模板长 $K$, 步长 $s$, valid 模式:
- 输出长度 = $\lfloor (N - K) / s \rfloor + 1$

复习 CV04 的 valid 卷积公式 — 同一个公式。


## 相似度公式

## 2.1 SSD (Sum of Squared Differences)

最简单的相似度度量, 实际上是"距离"的平方和 — **越小越相似**。

给定模板 $T$ 与图块 $P$ (同尺寸), 都展开成 N 维向量:

$\text{SSD}(T, P) = \sum_{i} (T_i - P_i)^2$

性质:
- SSD = 0: 完全一致
- SSD 越大: 越不相似
- 对**亮度变化**敏感: 模板与图块整体亮度差 5 单位, SSD 已经显著

## 2.2 SAD (Sum of Absolute Differences)

$\text{SAD}(T, P) = \sum_{i} |T_i - P_i|$

性质: 同 SSD 但用绝对值, 计算更快 (无平方), 但对极端值更鲁棒 (不放大大差异)。工业现场常用 SAD 替代 SSD。

## 2.3 NCC (Normalized Cross Correlation)

$\text{NCC}(T, P) = \frac{\sum_i (T_i - \bar{T})(P_i - \bar{P})}{\sqrt{\sum_i (T_i - \bar{T})^2 \sum_i (P_i - \bar{P})^2}}$

其中 $\bar{T}, \bar{P}$ 是均值。

性质:
- 范围 $[-1, 1]$, 1 表示完全相关 (最相似)
- **对亮度/对比度不变**: 减均值除标准差消掉了
- 对噪声鲁棒
- 计算量比 SAD/SSD 大 5-10 倍

工程实务: 工业 OCR 用 NCC (光照不稳定), 速度优先用 SAD。本关函数实现 SSD (最简单)。

## 2.4 选型口诀

- **快速 + 光照稳定**: SAD
- **慢但抗光照变化**: NCC
- **教学 / 推导基础**: SSD
- **现场调阈值**: 必试三种, 没有"哪个永远最好"


## 局部极值与业务案例

## 3.1 相关度图与 argmax

滑窗扫描完成后, 每个位置一个相似度值, 形成"相关度图":
- SSD/SAD: 用 argmin (最小最相似)
- NCC: 用 argmax (最大最相似)

简化为 1D 列表, 函数 `find_max_correlation` 返回最大值的索引位置。

## 3.2 局部极值筛选 (1D NMS)

实际工程中, 一个目标在相关度图周围多个位置都有较高响应 — 不是说有多个目标, 而是滑窗位置略微偏移仍然部分匹配。需要**非极大值抑制 (NMS)** 只保留每个局部最大。

1D NMS 算法:
1. 找全局最大值, 记录位置 $p$
2. 在 $[p - r, p + r]$ 范围内, 把其他位置抑制 (置 0 或小值, 或标记不输出)
3. 找剩余最大值, 重复。直到没有响应或达到上限。

$r$ 是抑制半径, 通常等于模板尺寸的一半。

本关函数 `non_max_suppression_1d` 用简化版: 给定 1D scores 与抑制半径, 返回保留的索引列表。

## 3.3 业务案例: 印刷品标签读码

场景: 流水线上经过的产品有印刷标签, 标签上印了序列号 (0-9), 每个数字是已知模板, 要识别整串。

流水线:
1. 灰度 + 滤波 (CV02, CV04)
2. 边缘检测找标签区域 (CV05)
3. **模板匹配**: 用 0-9 数字模板在标签区域滑窗, 算 SSD 或 NCC (本关 SSD 公式)
4. **每个位置的相关度图最大值** (本关 argmax) → 候选数字位置
5. **1D NMS** 沿水平方向 (本关 NMS) → 去重得到稀疏数字位置
6. 每个位置看哪个模板分数最高 → 识别数字

工程实务:
- **模板归一化必做**: 减均值除标准差, 否则光照不稳定全乱
- **多模板**: 同一个数字"0"准备多个尺寸/字体的模板
- **失败 fallback**: 模板匹配失败时降级到边缘特征匹配

## 3.4 工程口诀

- **滑窗是基本盘**: 任何"找已知图样"任务都从滑窗开始
- **SSD 教学, SAD 工程, NCC 抗扰**: 三选一看场景
- **NMS 是输出后处理标配**: 没 NMS 的相关度图无法用
- **抑制半径 = 模板半尺寸**: 是经验起点, 现场可调
- **模板匹配的死穴是变形**: 旋转 / 缩放变化必须换 SIFT 或更复杂的方法

$v$,
        $v${"questions": [{"id": "q08-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv08.py 中的 4 个函数; 评测以 test_cv08.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_ssd_identical$v$, $v$完全相同 → 0$v$, false, $v$完全相同 → 0$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_ssd_off_by_two$v$, $v$每个元素差 2, 长度 3 → (4*3) = 12 (SAD 会给 6 不同)$v$, false, $v$每个元素差 2, 长度 3 → (4*3) = 12 (SAD 会给 6 不同)$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_ssd_general$v$, $v$[1,2,3] vs [4,5,6]: (3²+3²+3²) = 27$v$, false, $v$[1,2,3] vs [4,5,6]: (3²+3²+3²) = 27$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_ssd_negative_diff$v$, $v$[5,5] vs [3,2]: (4+9) = 13$v$, false, $v$[5,5] vs [3,2]: (4+9) = 13$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_ssd_single_element$v$, $v$[10] vs [3]: 49 (boundary 单元素)$v$, false, $v$[10] vs [3]: 49 (boundary 单元素)$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_ssd_raises_on_length_mismatch$v$, $v$ssd raises on length mismatch$v$, false, $v$ssd raises on length mismatch$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_ssd_raises_on_non_list$v$, $v$ssd raises on non list$v$, false, $v$ssd raises on non list$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_argmax_simple$v$, $v$[1, 5, 3] → 1$v$, false, $v$[1, 5, 3] → 1$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_argmax_at_start$v$, $v$[10, 5, 3, 1] → 0$v$, false, $v$[10, 5, 3, 1] → 0$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_argmax_at_end$v$, $v$[1, 2, 3, 10] → 3$v$, false, $v$[1, 2, 3, 10] → 3$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_argmax_with_negatives$v$, $v$[-5, -1, -3] → 1$v$, false, $v$[-5, -1, -3] → 1$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_argmax_ties_first$v$, $v$[5, 5, 3] → 0 (ties returns smallest index)$v$, false, $v$[5, 5, 3] → 0 (ties returns smallest index)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_argmax_single$v$, $v$[42] → 0 (boundary)$v$, false, $v$[42] → 0 (boundary)$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_argmax_raises_on_empty$v$, $v$argmax raises on empty$v$, false, $v$argmax raises on empty$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_argmax_raises_on_non_list$v$, $v$argmax raises on non list$v$, false, $v$argmax raises on non list$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_nms_radius_1_simple$v$, $v$[1, 5, 1, 3, 1] r=1: 取 idx 1 (val 5), 抑制 0,2; 剩 [_, _, _, 3, 1], 取 idx 3 (val 3), 抑制 2,4; → [1, 3]$v$, true, $v$[1, 5, 1, 3, 1] r=1: 取 idx 1 (val 5), 抑制 0,2; 剩 [_, _, _, 3, 1], 取 idx 3 (val 3), 抑制 2,4; → [1, 3]$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_nms_radius_2$v$, $v$[1, 5, 1, 3, 1] r=2: 取 idx 1 抑制 [-1,3]即0,1,2,3; 剩 [_,_,_,_,1] 取 idx 4. → [1, 4]$v$, true, $v$[1, 5, 1, 3, 1] r=2: 取 idx 1 抑制 [-1,3]即0,1,2,3; 剩 [_,_,_,_,1] 取 idx 4. → [1, 4]$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_nms_single_peak$v$, $v$[1, 1, 10, 1, 1] r=1: idx 2 抑制 1,3; 剩 0,4 → [0,2,4]$v$, true, $v$[1, 1, 10, 1, 1] r=1: idx 2 抑制 1,3; 剩 0,4 → [0,2,4]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_nms_all_same$v$, $v$全同值, r=1: 取 idx 0 抑制 1; 取 idx 2 抑制 3; 取 idx 4. → [0, 2, 4]$v$, true, $v$全同值, r=1: 取 idx 0 抑制 1; 取 idx 2 抑制 3; 取 idx 4. → [0, 2, 4]$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_nms_large_radius_kills_others$v$, $v$r=10 大于 list len, 只剩 argmax: [1, 5, 1, 3, 1] → [1]$v$, true, $v$r=10 大于 list len, 只剩 argmax: [1, 5, 1, 3, 1] → [1]$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_nms_raises_on_empty$v$, $v$nms raises on empty$v$, true, $v$nms raises on empty$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_nms_raises_on_non_list$v$, $v$nms raises on non list$v$, true, $v$nms raises on non list$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_sw_simple$v$, $v$img=10, win=3, stride=1 → (10-3)/1+1 = 8$v$, true, $v$img=10, win=3, stride=1 → (10-3)/1+1 = 8$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_sw_stride_2$v$, $v$img=10, win=3, stride=2 → (10-3)/2+1 = 4 (floor 7/2=3, +1=4)$v$, true, $v$img=10, win=3, stride=2 → (10-3)/2+1 = 4 (floor 7/2=3, +1=4)$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_sw_stride_3$v$, $v$img=15, win=4, stride=3 → (15-4)/3+1 = floor(11/3)+1 = 3+1 = 4 (SAD: 15//3=5 不同)$v$, true, $v$img=15, win=4, stride=3 → (15-4)/3+1 = floor(11/3)+1 = 3+1 = 4 (SAD: 15//3=5 不同)$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_sw_window_equals_image$v$, $v$img=5, win=5, stride=1 → 1 (boundary)$v$, true, $v$img=5, win=5, stride=1 → 1 (boundary)$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_sw_large_image$v$, $v$img=100, win=10, stride=5 → (100-10)/5+1 = 19$v$, true, $v$img=100, win=10, stride=5 → (100-10)/5+1 = 19$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_sw_stride_5$v$, $v$img=20, win=5, stride=4 → (20-5)/4+1 = floor(15/4)+1 = 3+1 = 4 (SAD: 20//4=5 不同)$v$, true, $v$img=20, win=5, stride=4 → (20-5)/4+1 = floor(15/4)+1 = 3+1 = 4 (SAD: 20//4=5 不同)$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_sw_raises_on_window_gt_image$v$, $v$sw raises on window gt image$v$, true, $v$sw raises on window gt image$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_sw_raises_on_zero_stride$v$, $v$sw raises on zero stride$v$, true, $v$sw raises on zero stride$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_sw_raises_on_non_int$v$, $v$sw raises on non int$v$, true, $v$sw raises on non int$v$, NULL, 31)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
