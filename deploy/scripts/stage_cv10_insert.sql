-- CV10: 目标检测 (BBox / IoU / NMS)
-- practice_id=9, order_in_practice=10, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$目标检测 (BBox / IoU / NMS)$v$,
        'PRACTICE',
        10,
        $v$hard$v$,
        $v$## 目标检测的本质

## 1.1 分类 vs 定位 vs 检测

理解目标检测先要分清三种任务:
- **分类 (Classification)**: 一张图一个类别 (复习 CV09 的 softmax)
- **定位 (Localization)**: 一张图一个目标, 输出位置 (BBox)
- **检测 (Detection)**: 一张图多个目标, 每个输出 BBox + 类别

检测 = 定位 + 分类 + 多目标。难度大幅高于纯分类。

## 1.2 BBox 表示

Bounding Box (BBox / 边界框) 是检测任务的标准输出格式:
- **坐标格式**: $[x_1, y_1, x_2, y_2]$ — 左上角与右下角
- **替代格式**: $[x_c, y_c, w, h]$ — 中心 + 宽高 (YOLO 格式)
- **归一化**: 坐标除以图像宽高, 范围 $[0, 1]$ (尺度无关)

本关用左上右下格式 $[x_1, y_1, x_2, y_2]$, 满足 $x_1 < x_2$, $y_1 < y_2$。

## 1.3 BBox 面积

面积 = $(x_2 - x_1) \cdot (y_2 - y_1)$

工程实务: 检测输出过小或过大的 BBox 通常是错误, 需要面积过滤。

## 1.4 检测系统的输出形式

标准检测器对一张图输出:
- **N 个候选 BBox**: 例如 N=1000 (Faster R-CNN) 或 N=8000 (YOLO)
- 每个 BBox 附带:
  - 4 个坐标 $(x_1, y_1, x_2, y_2)$
  - 1 个置信度 score (该位置有目标的概率)
  - 类别概率 (复习 CV09 softmax)

但 N 这么大不合理 — 一张图实际目标只有几个。需要后处理:
1. **置信度阈值过滤**: 丢掉 score < 阈值 (本关函数)
2. **NMS**: 同一目标多个重叠框去重 (本关函数)


## IoU 与 NMS

## 2.1 IoU (Intersection over Union)

两个 BBox 的"重叠度", 是检测任务的核心度量。

$\text{IoU}(A, B) = \frac{|A \cap B|}{|A \cup B|} = \frac{\text{交集面积}}{\text{并集面积}}$

**交集计算** (两个 BBox $A = [a_1, b_1, a_2, b_2], B = [c_1, d_1, c_2, d_2]$):

$\text{inter\_x1} = \max(a_1, c_1)$
$\text{inter\_y1} = \max(b_1, d_1)$
$\text{inter\_x2} = \min(a_2, c_2)$
$\text{inter\_y2} = \min(b_2, d_2)$

若 inter_x2 > inter_x1 且 inter_y2 > inter_y1, 交集面积 = $(\text{inter\_x2} - \text{inter\_x1}) \cdot (\text{inter\_y2} - \text{inter\_y1})$, 否则交集面积 = 0 (不重叠)。

**并集面积** = $|A| + |B| - |A \cap B|$。

**范围**: IoU $\in [0, 1]$, 0 = 完全不重叠, 1 = 完全一致。

工程默认: IoU > 0.5 算"高度重叠", IoU > 0.7 算"几乎相同 BBox"。

## 2.2 NMS (Non-Max Suppression) 2D

检测结果中同一目标会有多个重叠 BBox (滑窗或 anchor 偏移生成的)。NMS 算法:

```
1. 按 score 降序排序所有 BBox
2. 取最大 score 的 BBox 加入"保留"列表
3. 把与该 BBox IoU > 阈值的其他 BBox 全部丢弃
4. 在剩余 BBox 中重复 2-3, 直到所有 BBox 被处理
5. 返回保留列表的索引 (升序)
```

经验阈值: IoU 阈值 = 0.5 (主流) 或 0.3 (更激进抑制) 或 0.7 (保守)。

## 2.3 NMS 与 CV08 模板匹配 NMS 的区别

复习 CV08 用过 1D NMS — 处理相关度图局部极值。本关 NMS 是 **2D BBox NMS** — 用 IoU 度量重叠。两者是同一思想 (抑制重叠) 在不同维度的应用。

工程实务: 检测器的 NMS 阈值是关键超参, 必须根据评测集调。


## 置信度过滤与业务案例

## 3.1 置信度阈值过滤

检测器输出大量低置信度 BBox (大部分是背景假阳性)。先用阈值过滤:

$\text{kept indices} = \{i : \text{score}_i \geq \text{thresh}\}$

阈值常用 0.05 (训练时评测) 或 0.5 (部署推理)。

工程实务:
- 太低: 太多假阳性进入 NMS, 拖慢速度
- 太高: 漏检低置信度的真目标

## 3.2 完整后处理流水线

```
Detector 原始输出 (1000 BBox + scores)
  → confidence_threshold_filter (thresh=0.5) → 100 BBox
  → NMS (IoU=0.5) → 10 BBox
  → 最终预测
```

先 thresh 后 NMS 是标配, 因为 NMS 计算量是 $O(N^2)$, 先过滤减少 N。

## 3.3 业务案例: 工业流水线缺陷检测

场景: 流水线相机拍每件产品, 检测产品上的缺陷 (划痕、污点、裂纹), 输出每个缺陷的位置和类别。

检测流水线:
1. 灰度 + 滤波 + 边缘 (CV02-05 复习)
2. 滑窗 + 模板/分类器 (CV08 + CV09 复习) → 候选 BBox + scores
3. **置信度过滤** (本关) → 保留 score ≥ 0.6 的候选
4. **NMS** (本关 IoU=0.5) → 同位置去重得到稀疏缺陷框
5. 每个 BBox 算面积 (本关), 太小或太大的丢掉
6. 输出: 缺陷位置 + 类别 + 面积

工程实务:
- **小目标 (划痕)**: BBox 小, NMS 阈值要保守 (= 0.3)
- **大目标 (污点)**: NMS 阈值可以激进 (= 0.5)
- **多类别**: 每个类别独立 NMS, 不跨类抑制

## 3.4 工程口诀

- **检测 = 定位 + 分类 + 多目标**: 不要混淆与单目标分类
- **BBox 必须满足 x1 < x2, y1 < y2**: 不合法 BBox 要校验
- **IoU 是度量, 不是损失**: IoU 不可微, 训练用近似 (GIoU, CIoU)
- **NMS 阈值 0.5 是默认**: 现场调
- **先过滤后 NMS**: O(N²) 性能优化关键

$v$,
        $v${"questions": [{"id": "q10-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv10.py 中的 4 个函数; 评测以 test_cv10.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_bbox_area_unit$v$, $v$[0,0,1,1] → 1$v$, false, $v$[0,0,1,1] → 1$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_bbox_area_2x3$v$, $v$[0,0,2,3] → 6$v$, false, $v$[0,0,2,3] → 6$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_bbox_area_offset$v$, $v$[10,20,30,50] → 20*30 = 600$v$, false, $v$[10,20,30,50] → 20*30 = 600$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_bbox_area_small$v$, $v$[0,0,0.5,0.5] → 0.25$v$, false, $v$[0,0,0.5,0.5] → 0.25$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_bbox_area_negative_corner$v$, $v$[-1,-2,3,4] → 4*6 = 24$v$, false, $v$[-1,-2,3,4] → 4*6 = 24$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_bbox_area_minimal$v$, $v$[0, 0, 0.001, 0.001] → 1e-6 (boundary 极小)$v$, false, $v$[0, 0, 0.001, 0.001] → 1e-6 (boundary 极小)$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_bbox_area_raises_on_x1_ge_x2$v$, $v$bbox area raises on x1 ge x2$v$, false, $v$bbox area raises on x1 ge x2$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_bbox_area_raises_on_wrong_length$v$, $v$bbox area raises on wrong length$v$, false, $v$bbox area raises on wrong length$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_bbox_area_raises_on_non_list$v$, $v$bbox area raises on non list$v$, false, $v$bbox area raises on non list$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_iou_b_contained_in_a_2$v$, $v$A=[0,0,4,4] B=[0,0,2,2]: inter=4, A=16, B=4, IoU=4/16=0.25 (IoMin=1.0 不同)$v$, false, $v$A=[0,0,4,4] B=[0,0,2,2]: inter=4, A=16, B=4, IoU=4/16=0.25 (IoMin=1.0 不同)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_iou_no_overlap$v$, $v$完全不重叠 → IoU = 0$v$, false, $v$完全不重叠 → IoU = 0$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_iou_half_overlap_x$v$, $v$[0,0,2,2] 与 [1,0,3,2]: 交=1*2=2, A=4, B=4, 并=4+4-2=6, IoU=2/6=1/3$v$, false, $v$[0,0,2,2] 与 [1,0,3,2]: 交=1*2=2, A=4, B=4, 并=4+4-2=6, IoU=2/6=1/3$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_iou_quarter_overlap$v$, $v$[0,0,2,2] 与 [1,1,3,3]: 交=1*1=1, A=4, B=4, 并=7, IoU=1/7$v$, false, $v$[0,0,2,2] 与 [1,1,3,3]: 交=1*1=1, A=4, B=4, 并=7, IoU=1/7$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_iou_b_contained_in_a$v$, $v$A 包含 B: A=[0,0,4,4], B=[1,1,2,2], 交=1, A=16, B=1, 并=16, IoU=1/16$v$, false, $v$A 包含 B: A=[0,0,4,4], B=[1,1,2,2], 交=1, A=16, B=1, 并=16, IoU=1/16$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_iou_touching_edge$v$, $v$边界接触不算重叠: A=[0,0,1,1], B=[1,0,2,1], 交=0 (x_overlap=0), IoU=0 (boundary)$v$, false, $v$边界接触不算重叠: A=[0,0,1,1], B=[1,0,2,1], 交=0 (x_overlap=0), IoU=0 (boundary)$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_iou_raises_on_wrong_box_length$v$, $v$iou raises on wrong box length$v$, false, $v$iou raises on wrong box length$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_iou_raises_on_non_list$v$, $v$iou raises on non list$v$, true, $v$iou raises on non list$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_filter_simple$v$, $v$[0.1, 0.6, 0.3, 0.8], thresh=0.5 → [1, 3]$v$, true, $v$[0.1, 0.6, 0.3, 0.8], thresh=0.5 → [1, 3]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_filter_at_threshold_partial$v$, $v$[0.4, 0.5, 0.6] thresh=0.5 → [1, 2] (>= 测试)$v$, true, $v$[0.4, 0.5, 0.6] thresh=0.5 → [1, 2] (>= 测试)$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_filter_first_only$v$, $v$[0.9, 0.2, 0.1] thresh=0.5 → [0]$v$, true, $v$[0.9, 0.2, 0.1] thresh=0.5 → [0]$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_filter_all_below$v$, $v$thresh=0.99, 全过低 → [] (boundary 全 reject)$v$, true, $v$thresh=0.99, 全过低 → [] (boundary 全 reject)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_filter_just_one$v$, $v$[0.1, 0.2, 0.9], thresh=0.5 → [2]$v$, true, $v$[0.1, 0.2, 0.9], thresh=0.5 → [2]$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_filter_two_kept$v$, $v$[0.6, 0.3, 0.7] thresh=0.5 → [0, 2]$v$, true, $v$[0.6, 0.3, 0.7] thresh=0.5 → [0, 2]$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_filter_raises_on_empty$v$, $v$filter raises on empty$v$, true, $v$filter raises on empty$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_filter_raises_on_non_list$v$, $v$filter raises on non list$v$, true, $v$filter raises on non list$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_nms_full_overlap_kill_lower$v$, $v$两 BBox 完全相同 → 保留高分$v$, true, $v$两 BBox 完全相同 → 保留高分$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_nms_two_separate_kill$v$, $v$4 个框 2 对重叠 → 各保留高分$v$, true, $v$4 个框 2 对重叠 → 各保留高分$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_nms_high_iou_kill$v$, $v$A B 高重叠 → 保留高分 A$v$, true, $v$A B 高重叠 → 保留高分 A$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_nms_single_box$v$, $v$单 BBox → 保留 (boundary)$v$, true, $v$单 BBox → 保留 (boundary)$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_nms_strict_threshold$v$, $v$阈值 0.3 (激进): 三个相邻 BBox 中两个被抑制$v$, true, $v$阈值 0.3 (激进): 三个相邻 BBox 中两个被抑制$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_nms_raises_on_length_mismatch$v$, $v$nms raises on length mismatch$v$, true, $v$nms raises on length mismatch$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_nms_raises_on_invalid_threshold$v$, $v$nms raises on invalid threshold$v$, true, $v$nms raises on invalid threshold$v$, NULL, 32),
    ($v$tc_33$v$, $v$test_nms_raises_on_non_list$v$, $v$nms raises on non list$v$, true, $v$nms raises on non list$v$, NULL, 33)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
