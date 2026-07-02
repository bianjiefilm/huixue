-- WX2: 缺失值检测与补全
-- practice_id=5, order_in_practice=2, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$缺失值检测与补全$v$,
        'PRACTICE',
        2,
        $v$beginner$v$,
        $v$## 缺失值的多种表达

## 1.1 为什么 missing 不只是 None

不同数据源对"缺失"的表达方式五花八门:
- **None / null**: 编程语言默认空值
- **空字符串 ""**: CSV 字段为空时常见
- **特定字符串**: "NA", "N/A", "null", "-", "NaN", "?"
- **特殊数值**: -1, 999999, 0 (业务约定的"无效值")
- **NaN**: 浮点 not-a-number, 数值列特有

工程实务: 必须根据数据源的"约定"识别 missing, 不能只看 None。一个项目里 missing 的表达可能在 5+ 种之间切换。

**典型案例**: 用户信息表的 phone 字段, 某些行是空字符串, 某些行是 "未填", 某些行是 "0000000000"。统一识别为 missing 后才能算正确的 missing 比例。

## 1.1.1 为什么不统一用 None

理论上后端可以把所有 missing 转成 None, 但实际工程难做到:
- 历史数据已经存在 (不可改)
- 第三方数据源 (爬虫/API) 不受控
- CSV/Excel 等文本格式天然有空字符串
- 业务约定的 marker 有语义 (如 -1 表示"传感器掉线")

所以"识别多种 marker"是清洗的必备技能。

## 1.2 missing 检测的统一接口

理想的 missing 检测函数应该接受 value 与"missing 候选集合", 返回 bool。本关函数:
- 单值: `is_missing(value, marker_set)` → bool
- 列表统计: `count_missing(values, marker_set)` → int

默认 marker_set 包含: None, "", "NA", "null", "NaN"。

## 1.3 missing 比例的工程意义

算 missing 比例后, 决策路径 (复习 WX01):
- missing < 5%: 数据相对干净, 用统计补全策略
- missing 5%-30%: 必须补全, 选合适策略
- missing > 50%: 考虑 drop 字段或回溯数据源

不同 missing 比例对应不同策略, 没有一刀切。


## 补全策略: 统计值与常量

## 2.1 三种统计补全

数值列的标准补全策略:

**均值补全**: $\hat{x} = \bar{x} = \frac{1}{|V|} \sum_{i \in V} x_i$

其中 $V$ 是非 missing 索引集合。均值补全保留**总体均值不变**, 但会**收缩方差** (所有 missing 都填同一个值)。

**中位数补全**: $\hat{x} = \text{median}(\{x_i : i \in V\})$

对极端值更鲁棒。如果列有强偏态分布或离群点, 中位数比均值更合理。

**常量补全**: $\hat{x} = c$ (用户给定)

用业务默认值 (例: 价格未填则 0, 状态未填则 "unknown")。是最可解释的策略, 但不一定最准确。

## 2.2 何时用哪种

- **正态分布数值列**: 均值
- **偏态/有离群点**: 中位数
- **业务有默认含义**: 常量 (如 "未填"、"unknown")
- **类别列**: 众数 (本关不实现, 后续学)

工程实务: 同一项目不同字段往往用不同策略, 没有统一答案。

## 2.3 删除策略 (drop)

除补全外, 还可以**删除整行**:
- 删除任一字段 missing 的行: 保留最干净, 但样本量减少
- 删除超过 N 个字段 missing 的行: 平衡保留与质量

删除适用场景: 总样本量充足 (> 10000) 且 missing 行不多 (< 10%)。否则建议补全。


## 业务案例与工程口诀

## 3.1 业务案例: 工业传感器数据补全

场景: 工厂传感器每秒采样温度、压力、流量, 偶尔丢包导致 missing。每天数据量 86400 条 × 3 列, missing 比例约 1-3%。

清洗流水线:
1. **检测 missing** (本关): 把 -999 (传感器丢包 marker) 与 None 都识别为 missing
2. **统计 missing 比例** (本关 count_missing): 每列分别算
3. **选策略**: 温度列正态分布 → 均值补全 (本关); 压力列偏态 → 中位数; 流量列业务默认 0 → 常量
4. **补全后再检验**: 补全后 missing 比例应该是 0%
5. **下游使用**: 滑动窗口聚合分析

工程实务:
- 传感器丢包通常**短暂连续**, 用前后值插值更合理 (后续关卡)
- 长时间 (> 30 秒) 丢包可能是**设备故障**, 这种 missing 不该补全, 应该报警

## 3.2 工程口诀

- **missing 不只是 None**: 必须看数据源约定的 marker
- **统计补全前必须排除 missing**: 否则均值/中位数被污染
- **均值 ≠ 中位数**: 偏态数据用中位数
- **常量补全是底线**: 不知道用什么策略时, 用业务默认
- **补全后必须再检验**: missing_count 应该回到 0

## 3.3 补全的副作用

所有补全策略都会**影响后续分析**:
- 均值补全降低方差 (估计置信区间偏窄)
- 中位数补全在小样本下不稳
- 常量补全在分布上引入"尖峰"

工程经验: 重要分析必须报告"补全前后对比", 让分析者意识到补全的影响。

## 3.4 进阶: missing 模式分析

除了简单计数, 还可以分析 missing 的"模式":
- **完全随机**: 任一字段缺失独立, 是真随机 (MCAR)
- **依赖其他字段**: 如 status='completed' 时 shipping_id 不缺, 但 status='pending' 时常缺
- **依赖自身**: 数值越大越易缺失 (如收入字段)

模式不同, 补全策略不同。本关只做简单识别+补全, 模式分析是进阶。

$v$,
        $v${"questions": [{"id": "q02-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx02.py 中的 4 个函数; 评测以 test_wx02.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_im_none$v$, $v$im none$v$, false, $v$im none$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_im_empty_string$v$, $v$im empty string$v$, false, $v$im empty string$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_im_real_number_not_missing$v$, $v$5 不是 missing$v$, false, $v$5 不是 missing$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_im_zero_not_missing$v$, $v$0 不是 missing (重要边界)$v$, false, $v$0 不是 missing (重要边界)$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_im_normal_string_not_missing$v$, $v$普通字符串不是 missing$v$, false, $v$普通字符串不是 missing$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_im_custom_markers$v$, $v$自定义 markers 集合$v$, false, $v$自定义 markers 集合$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_cm_no_missing$v$, $v$[1, 2, 3] → 0$v$, false, $v$[1, 2, 3] → 0$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_cm_some_missing$v$, $v$[1, None, 2, "NA", 3] → 2$v$, false, $v$[1, None, 2, "NA", 3] → 2$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_cm_all_missing$v$, $v$全 missing → len$v$, false, $v$全 missing → len$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_cm_zero_not_missing$v$, $v$[0, 1, 2] → 0 (0 不是 missing)$v$, false, $v$[0, 1, 2] → 0 (0 不是 missing)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_cm_with_custom_markers$v$, $v$[1, -999, 2, -999] markers={-999} → 2$v$, false, $v$[1, -999, 2, -999] markers={-999} → 2$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_cm_raises_on_non_list$v$, $v$cm raises on non list$v$, false, $v$cm raises on non list$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_fm_one_missing_middle$v$, $v$[1, None, 3] → mean=2, → [1, 2, 3]$v$, true, $v$[1, None, 3] → mean=2, → [1, 2, 3]$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_fm_two_missing$v$, $v$[1, None, 5, None, 3] → mean=(1+5+3)/3=3 → [1,3,5,3,3]$v$, true, $v$[1, None, 5, None, 3] → mean=(1+5+3)/3=3 → [1,3,5,3,3]$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_fm_string_marker$v$, $v$[1, 'NA', 3, 5] → mean=3 → [1,3,3,5]$v$, true, $v$[1, 'NA', 3, 5] → mean=3 → [1,3,3,5]$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_fm_decimal_mean$v$, $v$[1, None, 2] → mean=1.5 → [1,1.5,2]$v$, true, $v$[1, None, 2] → mean=1.5 → [1,1.5,2]$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_fm_negative_values$v$, $v$[-2, None, 4] → mean=1, → [-2, 1, 4]$v$, true, $v$[-2, None, 4] → mean=1, → [-2, 1, 4]$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_fm_raises_on_all_missing$v$, $v$fm raises on all missing$v$, true, $v$fm raises on all missing$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_fm_raises_on_empty$v$, $v$fm raises on empty$v$, true, $v$fm raises on empty$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_fm_raises_on_non_list$v$, $v$fm raises on non list$v$, true, $v$fm raises on non list$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_fc_basic$v$, $v$[1, None, 3] const=0 → [1, 0, 3]$v$, true, $v$[1, None, 3] const=0 → [1, 0, 3]$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_fc_string_constant$v$, $v$混合 None 与 'NA' const='unknown'$v$, true, $v$混合 None 与 'NA' const='unknown'$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_fc_zero_constant$v$, $v$const=0, missing 全填 0$v$, true, $v$const=0, missing 全填 0$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_fc_negative_constant$v$, $v$const=-1, missing 全填 -1$v$, true, $v$const=-1, missing 全填 -1$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_fc_raises_on_non_list$v$, $v$fc raises on non list$v$, true, $v$fc raises on non list$v$, NULL, 25)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
