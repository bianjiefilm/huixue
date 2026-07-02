-- WX12: 综合项目 - 电商订单数据清洗流水线
-- practice_id=5, order_in_practice=12, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$综合项目 - 电商订单数据清洗流水线$v$,
        'PRACTICE',
        12,
        $v$hard$v$,
        $v$## 清洗流水线的整合

## 1.1 全课程概念回顾

WX 课程已涵盖:
- **WX01**: 概述与流程, 5 类问题分类, 优先级
- **WX02**: 缺失值检测与补全
- **WX03**: 重复识别与去重
- **WX04**: 异常值 IQR 检测与截断
- **WX05**: 电话/邮箱/日期格式归一化
- **WX06**: 编码与字符清洗
- **WX07**: 字符串清洗 (空白/标点/截断)
- **WX08**: 数值清洗 (解析/截断/舍入)
- **WX09**: 关系一致性 (orphan/unique/1-1)
- **WX10**: 数据合并 (inner/left join + 去重)
- **WX11**: 质量评估 (completeness/uniqueness/validity)

本关把这些"零件"组合成系统级流水线。

## 1.2 端到端流水线 (电商订单)

标准电商订单清洗流水线:
1. **输入校验** (本关 F1): schema 合法性
2. **缺失补全** (WX02 复习): missing → fillna
3. **去重** (WX03 复习): 完全重复 → drop
4. **异常截断** (WX04 复习): outlier → clip
5. **格式归一化** (WX05 复习): 电话 / 邮箱 / 日期统一
6. **字符清洗** (WX07 复习): 空白 / 标点 / 截断
7. **数值清洗** (WX08 复习): 货币 → float
8. **一致性校验** (WX09 复习): user_id → 用户表
9. **质量评估** (WX11 复习): 三维比率
10. **报告组装** (本关 F4): 输出清洗报告 dict

本关聚焦"系统骨架": F1 (输入校验) → F2 (问题→步骤映射) → F3 (健康评分) → F4 (报告组装)。

## 1.3 问题到步骤的映射 (本关 F2)

| 问题类型 (issue) | 清洗步骤 (step) |
|---|---|
| missing | fillna |
| duplicate | drop_dup |
| outlier | clip |
| format | normalize |
| consistency | validate_fk |

把 5 类问题各自映射到对应的清洗算法名。这是"系统配置"的代码化表达。


## Schema 校验与健康评分

## 2.1 schema 校验

函数 `validate_pipeline_input(rows, required_keys)`:
- 必须是 list[dict]
- 每条 dict 必须包含 required_keys 中的所有 key
- 不要求其他 key 不存在 (允许 extra keys)

```
for row in rows:
    for k in required_keys:
        if k not in row: return False
return True
```

边界:
- 空 rows → True (vacuously)
- 空 required_keys → True
- 任一行缺 key → False

## 2.2 健康评分加权平均

函数 `compute_pipeline_health_score(quality_dict, weights=None)`:
- quality_dict: 含 'completeness', 'uniqueness', 'validity' 三个 float ∈ [0, 1]
- weights: 同 3 key 的权重 dict, 默认 {'completeness': 1, 'uniqueness': 1, 'validity': 1}
- 返回: weighted average = sum(w·q) / sum(w)

默认权重相等 → 与 WX11 的 `overall` 相同。
自定义权重 → 业务可调 (如 completeness 权重 2 表示更重视完整性)。

## 2.3 与 WX11 的呼应

WX11 的 `quality_summary_dict` 输出包含 'overall' = 三维简单平均。
本关 F3 是其加权扩展。

工程实务: 重要业务字段 (订单 ID / 金额) 的 completeness 权重 ≥ 5, 不重要字段 (备注) 权重 ≤ 0.5。


## 清洗报告与业务案例

## 3.1 清洗报告 schema

函数 `combine_cleaning_report(rows_in, rows_out, issues_fixed)`: 把清洗执行情况组装成报告 dict:

```
{
    'rows_in': 1000000,
    'rows_out': 950000,
    'rows_dropped': 50000,
    'issues_fixed': {'missing': 30000, 'duplicate': 20000, ...},
    'total_issues': 50000,
}
```

字段说明:
- rows_in: 清洗前行数
- rows_out: 清洗后行数
- rows_dropped: rows_in - rows_out
- issues_fixed: 各类问题修复数 (输入参数)
- total_issues: sum(issues_fixed.values())

## 3.2 业务案例: 电商订单端到端清洗

场景: 公司每天 100 万订单, 月底做一次"深度清洗" + 质量月报。

流水线:
1. **schema 校验** (本关 F1): 必须含 order_id, user_id, amount, created_at
2. **执行各步骤**: WX02-09 各自处理对应问题
3. **统计 issues_fixed** (本关 F4 输入): 每步报告修复数
4. **算健康评分** (本关 F3): completeness * 0.4 + uniqueness * 0.3 + validity * 0.3
5. **报告组装** (本关 F4): 给运维团队

数字: 100 万订单 → 校验 schema 通过 → 修复 5 万问题 (3万 missing + 1.5 万 duplicate + 5千 outlier) → 95 万有效订单 → 健康评分 0.92 → 报告入库。

## 3.3 工程口诀

- **流水线 = schema + 步骤映射 + 评分 + 报告**: 4 部分缺一不可
- **schema 校验最先**: 不合法直接退回
- **健康评分加权**: 业务自定义权重, 不要硬编码
- **报告 dict 标准化**: 下游消费方便
- **复用 WX01-11 概念**: 综合不引入新算法

## 3.4 综合项目对学习的意义

综合项目 = "概念回归整合", 不是新算法:
- 知道每类问题用哪个算法 (本关 F2)
- 知道 schema 校验长什么样 (本关 F1)
- 知道质量评分是加权平均 (本关 F3)
- 知道报告是 schema 化 dict (本关 F4)

这些是数据工程师从"会写算法"到"能搭流水线"的必经之路。

$v$,
        $v${"questions": [{"id": "q12-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx12.py 中的 4 个函数; 评测以 test_wx12.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_validate_all_present$v$, $v$validate all present$v$, false, $v$validate all present$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_validate_extra_keys_ok$v$, $v$额外字段允许$v$, false, $v$额外字段允许$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_validate_missing_one_key$v$, $v$validate missing one key$v$, false, $v$validate missing one key$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_validate_missing_in_first_row$v$, $v$validate missing in first row$v$, false, $v$validate missing in first row$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_validate_empty_rows$v$, $v$空 rows → True (vacuously)$v$, false, $v$空 rows → True (vacuously)$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_validate_raises_on_non_list$v$, $v$validate raises on non list$v$, false, $v$validate raises on non list$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_step_missing$v$, $v$step missing$v$, false, $v$step missing$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_step_duplicate$v$, $v$step duplicate$v$, false, $v$step duplicate$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_step_outlier$v$, $v$step outlier$v$, false, $v$step outlier$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_step_format$v$, $v$step format$v$, false, $v$step format$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_step_consistency$v$, $v$step consistency$v$, false, $v$step consistency$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_step_raises_on_unknown$v$, $v$step raises on unknown$v$, false, $v$step raises on unknown$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_step_raises_on_empty$v$, $v$step raises on empty$v$, false, $v$step raises on empty$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_step_raises_on_non_string$v$, $v$step raises on non string$v$, false, $v$step raises on non string$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_health_default_weights$v$, $v$default weights = (1+1+1)/3 = 简单平均$v$, false, $v$default weights = (1+1+1)/3 = 简单平均$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_health_custom_weights$v$, $v$weights={c:2, u:1, v:1}: (2*0.9 + 1*0.5 + 1*0.8) / 4 = 3.1/4 = 0.775$v$, true, $v$weights={c:2, u:1, v:1}: (2*0.9 + 1*0.5 + 1*0.8) / 4 = 3.1/4 = 0.775$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_health_extreme_weight$v$, $v$w={c:1, u:0.001, v:0.001}: 几乎完全是 completeness$v$, true, $v$w={c:1, u:0.001, v:0.001}: 几乎完全是 completeness$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_health_perfect$v$, $v$health perfect$v$, true, $v$health perfect$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_health_raises_on_missing_key$v$, $v$health raises on missing key$v$, true, $v$health raises on missing key$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_health_raises_on_quality_out_of_range$v$, $v$health raises on quality out of range$v$, true, $v$health raises on quality out of range$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_health_raises_on_non_dict$v$, $v$health raises on non dict$v$, true, $v$health raises on non dict$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_report_basic$v$, $v$report basic$v$, true, $v$report basic$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_report_all_5_keys$v$, $v$report all 5 keys$v$, true, $v$report all 5 keys$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_report_no_drops$v$, $v$rows_in == rows_out → dropped=0$v$, true, $v$rows_in == rows_out → dropped=0$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_report_empty_issues$v$, $v$issues_fixed 空 → total=0$v$, true, $v$issues_fixed 空 → total=0$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_report_multiple_issues$v$, $v$report multiple issues$v$, true, $v$report multiple issues$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_report_raises_on_negative_rows$v$, $v$report raises on negative rows$v$, true, $v$report raises on negative rows$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_report_raises_on_rows_out_gt_in$v$, $v$report raises on rows out gt in$v$, true, $v$report raises on rows out gt in$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_report_raises_on_negative_issue_count$v$, $v$report raises on negative issue count$v$, true, $v$report raises on negative issue count$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_report_raises_on_non_int$v$, $v$report raises on non int$v$, true, $v$report raises on non int$v$, NULL, 30)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
