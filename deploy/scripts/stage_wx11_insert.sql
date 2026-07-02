-- WX11: 清洗质量评估
-- practice_id=5, order_in_practice=11, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$清洗质量评估$v$,
        'PRACTICE',
        11,
        $v$intermediate$v$,
        $v$## 数据质量的多维度量

## 1.1 单维质量指标的局限

单看一个指标会被误导:
- 只看完整性: 漏率低但全是重复值, 数据无效
- 只看唯一性: 全唯一但都是异常值, 数据失真
- 只看有效性: 范围内但大量缺失, 数据稀疏

工程实务: **三维同时看** = 完整性 + 唯一性 + 有效性。

## 1.2 三个核心指标

### 完整性 (completeness)
$\text{completeness} = \frac{\text{非 missing 数}}{\text{总数}}$

复习 WX01 的 quality_ratio, WX02 的 missing 检测。本关函数复用 WX02 的 missing markers。

### 唯一性 (uniqueness)
$\text{uniqueness} = \frac{\text{distinct 数}}{\text{总数}}$

其中 distinct 数是去重后的元素种类数。

### 有效性 (validity)
$\text{validity} = \frac{\text{在 [lo, hi] 范围内的数}}{\text{总数}}$

复习 WX04 的范围概念。本关用统计意义上的有效范围。

## 1.3 三维指标的工程意义

- **completeness < 0.9**: 数据稀疏, 不适合训练 ML
- **uniqueness < 0.1**: 数据高度重复, 信息密度低
- **validity < 0.95**: 含大量异常, 需深度清洗

不同业务场景阈值不同, 但**三维同时看**是工程基本功。


## 三个比率的具体计算

## 2.1 completeness 实现

```
n = len(values)
missing = sum(1 for v in values if v in markers)
return (n - missing) / n
```

边界:
- 空 list → 抛 ValueError
- 全 missing → completeness = 0.0

## 2.2 uniqueness 实现

```
n = len(values)
distinct = len(set(values))
return distinct / n
```

边界:
- 空 list → 抛 ValueError
- 全相同 → uniqueness = 1/n
- 全不同 → uniqueness = 1.0

工程实务: uniqueness 太低 → 字段无信息量; 太高 → 可能是 ID 字段, 不适合做特征。

## 2.3 validity 实现

```
n = len(values)
in_range = sum(1 for v in values if lo <= v <= hi)
return in_range / n
```

边界:
- 非数值元素直接计为 invalid (本关简化: 假设输入都是数值)
- lo > hi → 抛 ValueError

## 2.4 综合质量评估

函数 `quality_summary_dict(completeness, uniqueness, validity)`: 把 3 个比率组装成统一 dict:
```
{
    'completeness': c,
    'uniqueness': u,
    'validity': v,
    'overall': (c + u + v) / 3,
}
```

overall 是简单平均, 工程实务可能用加权平均 (业务定权重)。本关用简单平均。


## 业务案例与工程口诀

## 3.1 业务案例: 数据质量月报

场景: 公司每月对核心业务表 (用户 / 订单 / 商品) 出质量月报, 监控质量趋势。

报告流水线 (一张表):
1. **每个字段算 completeness** (本关): 列出 missing 字段及比例
2. **每个字段算 uniqueness** (本关): 主键应该 1.0, 类别字段应在 0.001-0.1 (有重复但不全同)
3. **数值字段算 validity** (本关): 设业务合理范围
4. **综合 overall** (本关): 单字段三维平均
5. **跨字段聚合**: 整张表的所有字段 overall 取平均

报警规则:
- 单字段 overall < 0.7 → 需立即介入
- 月度趋势下降 > 10% → 数据源出问题

## 3.2 工程口诀

- **三维必须同时看**: 单维易误判
- **completeness 是地基**: missing 太多其他指标都失真
- **uniqueness 看场景**: 主键 = 1, 类别 = 中, 错误时 = 异常
- **validity 必须有业务范围**: 不能用统计 IQR 替代业务规则
- **overall 简单平均易理解**: 加权平均仅在业务有强偏好时

## 3.3 报告自动化与监控

质量指标月度报告应该:
- 自动化生成 (定时任务)
- 入监控系统 (Grafana 等可视化)
- 阈值触发报警 (PagerDuty 等)
- 历史趋势保留 (>= 12 月)

工程经验: 数据质量是**长期习惯**, 不是一次性活动。建立监控比写清洗代码更重要。

## 3.4 与 WX01 的呼应

复习 WX01 的 `quality_ratio = valid / total`, 是 completeness 的简化版。本关把 quality 拆成三维, 是工程级的细化。

## 3.5 进阶: 更多质量维度

除了三维, 工业质量框架还有:
- **一致性 (consistency)**: 跨字段约束 (复习 WX09)
- **及时性 (timeliness)**: 数据更新延迟
- **可解释性 (interpretability)**: 业务有人能解释每个字段

DAMA-DMBOK 数据质量标准列了 8 维度, 本关聚焦最常用的三维。

$v$,
        $v${"questions": [{"id": "q11-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx11.py 中的 4 个函数; 评测以 test_wx11.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_comp_no_missing$v$, $v$comp no missing$v$, false, $v$comp no missing$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_comp_two_missing_in_5$v$, $v$[1, None, 3, "", 5] → 3/5 = 0.6$v$, false, $v$[1, None, 3, "", 5] → 3/5 = 0.6$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_comp_three_missing_in_4$v$, $v$[None, "NA", "null", 1] → 1/4 = 0.25$v$, false, $v$[None, "NA", "null", 1] → 1/4 = 0.25$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_comp_custom_markers$v$, $v$[1, -999, 2, -999] markers={-999} → 2/4 = 0.5$v$, false, $v$[1, -999, 2, -999] markers={-999} → 2/4 = 0.5$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_comp_one_missing_in_3$v$, $v$[1, 2, None] → 2/3$v$, false, $v$[1, 2, None] → 2/3$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_comp_raises_on_empty$v$, $v$comp raises on empty$v$, false, $v$comp raises on empty$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_comp_raises_on_non_list$v$, $v$comp raises on non list$v$, false, $v$comp raises on non list$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_uniq_all_distinct_5$v$, $v$uniq all distinct 5$v$, false, $v$uniq all distinct 5$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_uniq_2_in_4$v$, $v$[1, 2, 1, 2] → 2/4 = 0.5$v$, false, $v$[1, 2, 1, 2] → 2/4 = 0.5$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_uniq_3_in_5$v$, $v$[1, 1, 2, 2, 3] → 3/5 = 0.6$v$, false, $v$[1, 1, 2, 2, 3] → 3/5 = 0.6$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_uniq_1_in_5$v$, $v$[7, 7, 7, 7, 7] → 1/5 = 0.2$v$, false, $v$[7, 7, 7, 7, 7] → 1/5 = 0.2$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_uniq_2_in_3_strings$v$, $v$['a', 'b', 'a'] → 2/3$v$, false, $v$['a', 'b', 'a'] → 2/3$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_uniq_raises_on_empty$v$, $v$uniq raises on empty$v$, false, $v$uniq raises on empty$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_uniq_raises_on_non_list$v$, $v$uniq raises on non list$v$, false, $v$uniq raises on non list$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_valid_all_in_range$v$, $v$[5, 10, 15] in [0, 20] → 3/3 = 1.0$v$, true, $v$[5, 10, 15] in [0, 20] → 3/3 = 1.0$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_valid_two_out_of_three$v$, $v$[5, 100, 15] in [0, 20] → 2/3 (100 超出)$v$, true, $v$[5, 100, 15] in [0, 20] → 2/3 (100 超出)$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_valid_one_in_four$v$, $v$[5, 100, 200, 300] in [0, 50] → 1/4 = 0.25$v$, true, $v$[5, 100, 200, 300] in [0, 50] → 1/4 = 0.25$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_valid_three_in_five$v$, $v$[5, 10, 15, 25, 30] in [0, 20] → 3/5 = 0.6$v$, true, $v$[5, 10, 15, 25, 30] in [0, 20] → 3/5 = 0.6$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_valid_at_boundaries$v$, $v$[0, 20, -1, 21] in [0, 20] → 2/4 = 0.5 (闭区间)$v$, true, $v$[0, 20, -1, 21] in [0, 20] → 2/4 = 0.5 (闭区间)$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_valid_raises_on_empty$v$, $v$valid raises on empty$v$, true, $v$valid raises on empty$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_valid_raises_on_lower_gt_upper$v$, $v$valid raises on lower gt upper$v$, true, $v$valid raises on lower gt upper$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_summary_perfect$v$, $v$summary perfect$v$, true, $v$summary perfect$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_summary_typical$v$, $v$0.9 + 0.5 + 0.8 → overall = 0.733...$v$, true, $v$0.9 + 0.5 + 0.8 → overall = 0.733...$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_summary_low_quality$v$, $v$0.5 + 0.3 + 0.4 → overall = 0.4$v$, true, $v$0.5 + 0.3 + 0.4 → overall = 0.4$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_summary_zero$v$, $v$全 0 → overall = 0$v$, true, $v$全 0 → overall = 0$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_summary_keys_complete$v$, $v$4 个 key 都存在$v$, true, $v$4 个 key 都存在$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_summary_raises_on_out_of_range$v$, $v$summary raises on out of range$v$, true, $v$summary raises on out of range$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_summary_raises_on_non_numeric$v$, $v$summary raises on non numeric$v$, true, $v$summary raises on non numeric$v$, NULL, 28)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
