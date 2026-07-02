-- WX1: 数据清洗概述与流程
-- practice_id=5, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$数据清洗概述与流程$v$,
        'PRACTICE',
        1,
        $v$beginner$v$,
        $v$## 数据清洗的本质与必要性

## 1.1 数据为什么"脏"

真实数据采集过程中, 数据质量问题几乎不可避免:
- **采集端**: 传感器漂移、网络抖动、人工录入错误
- **传输端**: 编码转换、字段截断、丢包
- **存储端**: 字段类型变更、约束未生效、并发写入冲突
- **业务端**: 业务规则变化、数据迁移、口径不一致

清洗 (data cleaning) 是把"脏数据"转成"分析可用数据"的工程过程。

## 1.2 数据问题的常见类型

工业实务中主要 5 类问题:
- **缺失值 (missing)**: 字段为 null / 空字符串 / 默认 marker (NA, -1)
- **重复值 (duplicate)**: 同一条记录出现多次 (完全相同或部分键相同)
- **异常值 (outlier)**: 数值远离正常分布 (传感器故障 / 录入错误)
- **格式不一致 (format)**: 日期、电话、邮箱等格式多样
- **逻辑不一致 (consistency)**: 跨字段约束被打破 (begin > end / id 不存在)

不同问题有不同的检测与修复方法, 后续关卡分别展开。

## 1.3 清洗对分析结果的影响

清洗不是"可有可无"的步骤, 数据质量直接影响分析结果:
- 1% 的缺失值可能让模型偏差 5-10%
- 1 个极端 outlier 可能让均值漂移 10x
- 5% 重复数据可能让计数指标膨胀

工程经验: 数据科学家 70-80% 时间花在清洗上 — 这不是浪费, 是必要投入。


## 清洗流水线与优先级

## 2.1 标准清洗流水线

清洗的步骤有**逻辑顺序**, 顺序错了反而引入新问题:

| 序号 | 步骤名 (step name) | 处理什么 |
|---|---|---|
| 1 | missing | 缺失值检测与补全 |
| 2 | duplicate | 重复记录识别与去重 |
| 3 | outlier | 异常值检测与处理 |
| 4 | format | 格式规范化 (日期/电话/邮箱) |
| 5 | consistency | 关系一致性校验 |

为什么这个顺序? 例:
- 先填补 missing 再去 duplicate: 否则两条 missing 记录可能被误判为重复
- 先 duplicate 后 outlier: 重复的极端值会让 outlier 检测算法失真
- 先 outlier 后 format: 极端值往往伴随格式异常 (录入错误)
- format 与 consistency 最后做: 前面步骤可能改变值

## 2.2 数据质量比率公式

清洗前后需要量化, 最常用的指标:

$\text{quality} = \frac{\text{valid}}{\text{total}}$

其中 valid 是通过所有检查的记录数, total 是原始记录总数。范围 $[0, 1]$, 越接近 1 数据越干净。

工程实务: 1.0 几乎不可能, 0.95+ 是优, 0.8-0.95 是良, < 0.8 通常表明数据源有严重问题需要回溯。

## 2.3 决策: 丢弃还是补全

面对 missing, 两条路径:
- **drop (丢弃)**: 删掉含 missing 的行 / 列
- **fill (补全)**: 用某种策略填上 (均值/众数/插值, 后续关卡)

经验决策树:
- missing_ratio > threshold → **drop** (字段质量太差, 留下也没用)
- missing_ratio < threshold → **fill** (用合理策略补全, 保留信息)

阈值不是唯一答案, 业务关键字段可能 missing_ratio > 50% 也要 fill (例: 用户邮箱)。本关函数默认阈值 0.5。


## 业务案例与工程口诀

## 3.1 业务案例: 电商订单数据清洗

场景: 电商平台从多个数据源 (网站日志 / 客服系统 / 物流系统) 汇总订单数据, 用于销售分析。原始数据有以下问题:

- **缺失**: 部分订单 user_id 缺失 (5%), customer_phone 缺失 (15%)
- **重复**: 客服系统重复推送, 同一订单出现 2-3 次 (3%)
- **异常**: 订单金额偶有 -1 / 999999 (传感器或人工录入错误) (1%)
- **格式**: 日期格式有 "2026-04-25" / "2026/04/25" / "Apr 25, 2026" 三种
- **一致性**: order_status='completed' 但 shipping_id 缺失 (业务流程 bug)

清洗流水线:
1. **检测各类问题** (本关分类): 给每个值打标 missing/out_of_range/valid
2. **算质量比率** (本关): 总记录 100000 / 完全 valid 78000 → 0.78
3. **按优先级排序** (本关): missing → duplicate → outlier → format → consistency
4. **决策 drop/fill** (本关): user_id missing 5% → fill 默认值; customer_phone missing 15% → fill 'N/A'
5. **执行各步骤**: 后续关卡展开
6. **再次评估**: 清洗后质量比率 > 0.95, 进入下游分析

## 3.2 工程口诀

- **清洗顺序固定**: missing → duplicate → outlier → format → consistency
- **质量比率是基准**: 清洗前后必须算, 看清洗效果
- **drop 阈值 0.5 是默认**: 业务关键字段可调
- **不要急着改数据**: 先分类, 再决策, 最后改
- **回溯优于硬补**: 数据源问题先反馈再清洗

## 3.3 清洗与下游的关系

清洗后数据后续用于统计分析、机器学习训练、报表可视化等。清洗质量直接影响所有下游, 所以这是数据科学的"基础设施"。

$v$,
        $v${"questions": [{"id": "q01-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx01.py 中的 4 个函数; 评测以 test_wx01.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_cls_valid_in_range$v$, $v$5 ∈ [0, 10] → valid$v$, false, $v$5 ∈ [0, 10] → valid$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_cls_out_of_range_low$v$, $v$-5 < valid_min → out_of_range$v$, false, $v$-5 < valid_min → out_of_range$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_cls_out_of_range_high$v$, $v$100 > valid_max → out_of_range$v$, false, $v$100 > valid_max → out_of_range$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_cls_missing_none$v$, $v$None → missing$v$, false, $v$None → missing$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_cls_missing_empty_string$v$, $v$空字符串 → missing$v$, false, $v$空字符串 → missing$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_cls_missing_custom_marker$v$, $v$custom marker -1 → missing$v$, false, $v$custom marker -1 → missing$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_cls_negative_in_range$v$, $v$-3 ∈ [-10, 5] → valid (boundary 负数有效)$v$, false, $v$-3 ∈ [-10, 5] → valid (boundary 负数有效)$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_cls_raises_on_non_numeric_min$v$, $v$cls raises on non numeric min$v$, false, $v$cls raises on non numeric min$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_qr_perfect$v$, $v$100/100 → 1.0$v$, false, $v$100/100 → 1.0$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_qr_half$v$, $v$50/100 → 0.5$v$, false, $v$50/100 → 0.5$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_qr_partial_78$v$, $v$78/100 → 0.78$v$, false, $v$78/100 → 0.78$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_qr_zero_valid$v$, $v$0/100 → 0.0 (boundary)$v$, false, $v$0/100 → 0.0 (boundary)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_qr_three_quarters$v$, $v$3/4 = 0.75 (整数除法陷阱测试)$v$, false, $v$3/4 = 0.75 (整数除法陷阱测试)$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_qr_raises_on_zero_total$v$, $v$qr raises on zero total$v$, false, $v$qr raises on zero total$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_qr_raises_on_valid_gt_total$v$, $v$qr raises on valid gt total$v$, false, $v$qr raises on valid gt total$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_qr_raises_on_non_int$v$, $v$qr raises on non int$v$, false, $v$qr raises on non int$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_priority_missing$v$, $v$priority missing$v$, true, $v$priority missing$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_priority_duplicate$v$, $v$priority duplicate$v$, true, $v$priority duplicate$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_priority_outlier$v$, $v$priority outlier$v$, true, $v$priority outlier$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_priority_format$v$, $v$priority format$v$, true, $v$priority format$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_priority_consistency$v$, $v$priority consistency$v$, true, $v$priority consistency$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_priority_raises_on_unknown$v$, $v$priority raises on unknown$v$, true, $v$priority raises on unknown$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_priority_raises_on_empty$v$, $v$空字符串 boundary$v$, true, $v$空字符串 boundary$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_priority_raises_on_non_string$v$, $v$priority raises on non string$v$, true, $v$priority raises on non string$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_decide_drop_high_missing$v$, $v$80% missing > 0.5 → drop$v$, true, $v$80% missing > 0.5 → drop$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_decide_fill_low_missing$v$, $v$20% missing < 0.5 → fill$v$, true, $v$20% missing < 0.5 → fill$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_decide_just_above_threshold$v$, $v$51% missing > 0.5 → drop$v$, true, $v$51% missing > 0.5 → drop$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_decide_zero_missing$v$, $v$0 missing → fill (boundary)$v$, true, $v$0 missing → fill (boundary)$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_decide_custom_threshold_03$v$, $v$20% > 0.3? no, → fill; 40% > 0.3? yes → drop$v$, true, $v$20% > 0.3? no, → fill; 40% > 0.3? yes → drop$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_decide_raises_on_zero_total$v$, $v$decide raises on zero total$v$, true, $v$decide raises on zero total$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_decide_raises_on_invalid_threshold$v$, $v$decide raises on invalid threshold$v$, true, $v$decide raises on invalid threshold$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_decide_raises_on_non_int$v$, $v$decide raises on non int$v$, true, $v$decide raises on non int$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
