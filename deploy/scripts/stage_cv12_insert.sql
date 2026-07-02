-- CV12: 综合项目 - 物体识别端到端
-- practice_id=9, order_in_practice=12, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$综合项目 - 物体识别端到端$v$,
        'PRACTICE',
        12,
        $v$hard$v$,
        $v$## 端到端物体识别流水线

## 1.1 CV 任务的整合

CV 课程到目前为止已经讲了:
- **CV01-02**: 图像基础 / 色彩空间 / 像素归一化
- **CV03-04**: 几何变换 / 滤波降噪
- **CV05-06**: 边缘检测 / 形态学
- **CV07-08**: 特征点 / 模板匹配
- **CV09-11**: CNN 分类 / 目标检测 / 图像分割

这些是 CV 的"元件箱", 真实工业系统是把多个元件按特定顺序组合起来, 形成端到端流水线。本关学如何把这些元件抽象成"子任务 → 算法选择"的映射, 写出系统级代码骨架。

## 1.2 标准物体识别流水线

给定一张待识别的图像, 标准流水线:

1. **输入校验** (本关 F1): 检查 shape 是否合法 (通道数 1 或 3, 尺寸不太小)
2. **预处理**: 灰度化 (CV02) → 高斯滤波 (CV04) → 标准化
3. **特征提取或前向**:
   - 经典 CV: 边缘 + 形态学 + 特征 (CV05-07)
   - 深度学习: CNN 前向 (CV09)
4. **任务输出**:
   - 分类: softmax + argmax (CV09)
   - 检测: BBox + score + NMS (CV10)
   - 分割: 阈值 + 连通域 (CV11)
5. **后处理**: NMS / 置信度过滤 / 形态学清理
6. **指标计算** (本关 F3): precision / recall / F1
7. **统一输出** (本关 F4): 把多个任务的输出整合成统一格式

## 1.3 子任务到算法的映射 (本关 F2)

不同子任务对应不同的算法:

| 子任务 (subtask) | 经典算法名 (CV 课程已学) |
|------|------|
| denoise | gaussian_filter (CV04) |
| edge | sobel_canny (CV05) |
| feature | harris_response (CV07) |
| classify | cnn_softmax (CV09) |
| detect | bbox_nms (CV10) |
| segment | binary_threshold (CV11) |

本关函数把这 6 个子任务名映射到对应算法名, 是"系统配置"的代码化形式。


## 输入校验与指标计算

## 2.1 图像输入 schema

物体识别系统的输入必须满足:
- **通道数** ∈ {1, 3}: 灰度或彩色 (CV01 概念)
- **最小尺寸**: H >= 8, W >= 8 (太小无法做有意义的 CV 处理)
- **shape 格式**: (H, W, C) 三元组

系统级校验是"防御性编程" — 工业系统的输入往往不可信, 必须先 validate 再处理。

## 2.2 precision / recall / F1

给定真实正样本 (positives) 与模型预测正样本, 三个常见指标:
- **TP** (True Positive): 真实正, 预测正
- **FP** (False Positive): 真实负, 预测正
- **FN** (False Negative): 真实正, 预测负
- (TN 不参与本关公式)

公式:

$\text{precision} = \frac{TP}{TP + FP}$ (查准率)
$\text{recall} = \frac{TP}{TP + FN}$ (查全率)
$\text{F1} = \frac{2 \cdot \text{precision} \cdot \text{recall}}{\text{precision} + \text{recall}}$ (调和平均)

**特殊情况**:
- TP=0 且 FP=0: precision = 0 (约定避免 0/0)
- TP=0 且 FN=0: recall = 0 (约定避免 0/0)
- precision + recall = 0: F1 = 0 (约定避免 0/0)

## 2.3 与已学指标的关系

复习:
- CV09 准确率 (Accuracy): correct/total, 只看主流类
- CV11 Dice 系数: 2|A∩B|/(|A|+|B|), 像素级
- **本关 F1**: precision/recall 的调和平均, 类别级

F1 与 Dice 在二分类下是同一个公式 (验证作业): F1 = 2·TP / (2·TP + FP + FN), Dice = 2|A∩B|/(|A|+|B|), 当 |A|=TP+FP, |B|=TP+FN, |A∩B|=TP, 则 Dice = 2·TP/(2·TP+FP+FN) = F1。这是分割与分类指标的内在统一性。


## 统一输出格式与业务案例

## 3.1 统一识别输出 schema

工业系统的"识别结果"通常包含:
- **类别预测** (class_pred): int, 0 ~ num_classes-1
- **位置** (bbox): [x1, y1, x2, y2], 4 元素 list
- **置信度** (score): float, [0, 1]
- **附加 metadata** (可选): 时间戳、ID 等

本关 F4 把这三个核心字段组合成统一 dict: {'class': c, 'bbox': [x1,y1,x2,y2], 'score': s}。

标准化后, 下游系统 (报警、数据库、UI) 可以统一消费, 无论上游是检测/分类/分割。

## 3.2 业务案例: 工业流水线物体识别

场景: 流水线相机连续拍每件产品, 要识别产品**类别** + **位置** + **缺陷** + **质量评分**, 输出给质控系统:

端到端流水线:
1. **输入校验** (本关 F1): 相机给的 shape 校验
2. **预处理**: CV02 灰度 + CV04 高斯滤波 (本关 F2 映射 denoise → gaussian_filter)
3. **缺陷分割** (本关 F2 映射 segment → binary_threshold + CV11)
4. **物体检测** (本关 F2 映射 detect → bbox_nms + CV10)
5. **类别识别** (本关 F2 映射 classify → cnn_softmax + CV09)
6. **指标计算** (本关 F3): 与历史标注对比, 算 precision/recall/F1
7. **统一输出** (本关 F4): 把 class + bbox + score 组成 dict, 给上层

工程实务: 流水线代码要做到模块化 (每个步骤独立函数) + schema 严格 (输入输出有合约) + 错误隔离 (一个步骤失败不影响其他)。

## 3.3 综合项目对学习的意义

综合项目不是"再学一个新算法", 而是**让学过的算法各就其位**:
- 知道哪个子任务用哪个 CV 概念 (本关 F2)
- 知道系统级输入校验长什么样 (本关 F1)
- 知道指标是 precision/recall/F1, 不是单一 accuracy (本关 F3)
- 知道输出是 schema 化的, 不是裸 array (本关 F4)

这些都是"工程师从学算法到落地系统"的必经之路。

## 3.4 工程口诀

- **流水线 = 子任务 + 映射 + 顺序**: 每个子任务对应一个算法
- **输入校验先于一切**: 没校验过的输入是定时炸弹
- **指标是多维的**: 单看 accuracy 会被类别不平衡欺骗
- **统一 schema 是接口设计的灵魂**: 下游不应关心是哪个上游算法产出的
- **CV12 是 CV 课程的"复习+整合"**: 概念回到 CV01-11, 不引入新公式

$v$,
        $v${"questions": [{"id": "q12-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv12.py 中的 4 个函数; 评测以 test_cv12.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_shape_rgb_valid$v$, $v$(28, 28, 3) → True$v$, false, $v$(28, 28, 3) → True$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_shape_grayscale_valid$v$, $v$(28, 28, 1) → True$v$, false, $v$(28, 28, 1) → True$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_shape_too_small_h$v$, $v$H < min_h → False$v$, false, $v$H < min_h → False$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_shape_too_small_w$v$, $v$W < min_w → False$v$, false, $v$W < min_w → False$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_shape_invalid_channels$v$, $v$C=2 不合法 → False$v$, false, $v$C=2 不合法 → False$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_shape_4_channels$v$, $v$C=4 (RGBA) 不合法 → False$v$, false, $v$C=4 (RGBA) 不合法 → False$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_shape_custom_min$v$, $v$(64, 64, 3), min_h=64 min_w=64 → True (boundary 边界)$v$, false, $v$(64, 64, 3), min_h=64 min_w=64 → True (boundary 边界)$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_shape_wrong_length$v$, $v$长度 != 3 → False$v$, false, $v$长度 != 3 → False$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_shape_raises_on_non_tuple$v$, $v$shape raises on non tuple$v$, false, $v$shape raises on non tuple$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_subtask_denoise$v$, $v$subtask denoise$v$, false, $v$subtask denoise$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_subtask_edge$v$, $v$subtask edge$v$, false, $v$subtask edge$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_subtask_feature$v$, $v$subtask feature$v$, false, $v$subtask feature$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_subtask_classify$v$, $v$subtask classify$v$, false, $v$subtask classify$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_subtask_detect$v$, $v$subtask detect$v$, false, $v$subtask detect$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_subtask_segment$v$, $v$subtask segment$v$, false, $v$subtask segment$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_subtask_raises_on_unknown$v$, $v$subtask raises on unknown$v$, false, $v$subtask raises on unknown$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_subtask_raises_on_empty$v$, $v$空字符串 boundary$v$, false, $v$空字符串 boundary$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_subtask_raises_on_non_string$v$, $v$subtask raises on non string$v$, true, $v$subtask raises on non string$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_metrics_perfect$v$, $v$TP=10, FP=0, FN=0 → precision=1, recall=1, f1=1$v$, true, $v$TP=10, FP=0, FN=0 → precision=1, recall=1, f1=1$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_metrics_typical$v$, $v$TP=8, FP=2, FN=4: p=8/10=0.8, r=8/12≈0.667, f1=2*0.8*0.667/(0.8+0.667)≈0.727$v$, true, $v$TP=8, FP=2, FN=4: p=8/10=0.8, r=8/12≈0.667, f1=2*0.8*0.667/(0.8+0.667)≈0.727$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_metrics_high_fp$v$, $v$TP=5, FP=15, FN=0: p=5/20=0.25, r=5/5=1, f1=2*0.25*1/1.25=0.4$v$, true, $v$TP=5, FP=15, FN=0: p=5/20=0.25, r=5/5=1, f1=2*0.25*1/1.25=0.4$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_metrics_high_fn$v$, $v$TP=2, FP=0, FN=8: p=1, r=2/10=0.2, f1=2*1*0.2/1.2=1/3$v$, true, $v$TP=2, FP=0, FN=8: p=1, r=2/10=0.2, f1=2*1*0.2/1.2=1/3$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_metrics_zero_tp_fp$v$, $v$TP=0, FP=0, FN=5: p=0 (约定), r=0, f1=0$v$, true, $v$TP=0, FP=0, FN=5: p=0 (约定), r=0, f1=0$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_metrics_all_zero$v$, $v$全 0 → 全 0 (boundary)$v$, true, $v$全 0 → 全 0 (boundary)$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_metrics_raises_on_negative$v$, $v$metrics raises on negative$v$, true, $v$metrics raises on negative$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_metrics_raises_on_non_int$v$, $v$metrics raises on non int$v$, true, $v$metrics raises on non int$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_combine_basic$v$, $v$基本组装$v$, true, $v$基本组装$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_combine_class_five$v$, $v$class=5 (非 hardcode 默认 0)$v$, true, $v$class=5 (非 hardcode 默认 0)$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_combine_score_zero$v$, $v$score=0 boundary$v$, true, $v$score=0 boundary$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_combine_score_one$v$, $v$score=1 boundary$v$, true, $v$score=1 boundary$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_combine_keys_present$v$, $v$返回 dict 必须包含三个 key 'class' / 'bbox' / 'score'$v$, true, $v$返回 dict 必须包含三个 key 'class' / 'bbox' / 'score'$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_combine_bbox_unchanged$v$, $v$bbox 应原样保留 (元素一一相同)$v$, true, $v$bbox 应原样保留 (元素一一相同)$v$, NULL, 32),
    ($v$tc_33$v$, $v$test_combine_raises_on_bad_bbox_length$v$, $v$combine raises on bad bbox length$v$, true, $v$combine raises on bad bbox length$v$, NULL, 33),
    ($v$tc_34$v$, $v$test_combine_raises_on_score_out_of_range$v$, $v$combine raises on score out of range$v$, true, $v$combine raises on score out of range$v$, NULL, 34),
    ($v$tc_35$v$, $v$test_combine_raises_on_negative_class$v$, $v$combine raises on negative class$v$, true, $v$combine raises on negative class$v$, NULL, 35)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
