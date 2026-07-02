-- WX4: 异常值检测与处理
-- practice_id=5, order_in_practice=4, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$异常值检测与处理$v$,
        'PRACTICE',
        4,
        $v$intermediate$v$,
        $v$## 异常值的定义与影响

## 1.1 异常值是什么

异常值 (outlier) 是数据集中**显著偏离正常分布**的值。常见来源:
- **测量错误**: 传感器故障、读数失真
- **录入错误**: 把 25 岁录成 250 岁
- **真实异常**: 极端天气下的销售数据 / 双 11 流量
- **数据迁移问题**: 字段错位、单位混淆

异常值的处理策略要看场景:
- 测量错误 → 删除或截断
- 真实异常 → 保留 (业务有意义)

## 1.2 异常值对统计的影响

均值和方差对异常值**极敏感**:
- 100 个值, 均值 50, std 10
- 加入一个 999 → 均值变成 ~59 (变 18%)
- 加入一个 99999 → 均值变成 ~1040 (变 20 倍)

中位数对异常值**鲁棒** (复习 WX02 中位数补全)。所以工程上, 报告均值的同时必须报告中位数, 检测异常前考虑用中位数代表。

## 1.3 单变量 vs 多变量异常

- **单变量 outlier**: 单字段值在统计上偏离 (例: 年龄 = 200)
- **多变量 outlier**: 多字段组合不合理 (例: 年龄 = 5 + 月薪 = 50000)

本关聚焦单变量 outlier (最简单), 多变量异常需要 ML 算法 (如 Isolation Forest), 是进阶专题。


## IQR 检测法

## 2.1 四分位数与 IQR

把数据排序后:
- **Q1 (25% 分位数)**: 排在 25% 位置的值
- **Q2 (中位数)**: 50% 位置
- **Q3 (75% 分位数)**: 75% 位置

$IQR = Q3 - Q1$ 表示中间 50% 数据的"扩散范围"。

## 2.2 IQR 异常判定公式

经典的 Tukey 1977 定义:

$\text{lower} = Q1 - k \cdot IQR$
$\text{upper} = Q3 + k \cdot IQR$

值 $x$ 是异常 ⇔ $x < \text{lower}$ 或 $x > \text{upper}$。

$k$ 是 multiplier, 工程默认:
- $k = 1.5$: "mild outlier" (温和, 默认)
- $k = 3.0$: "extreme outlier" (极端, 仅检测极离谱)

本关函数默认 $k = 1.5$。

## 2.3 IQR 法的优劣

**优点**:
- 鲁棒于已存在的异常 (Q1/Q3 不被极端值拉偏)
- 无需假设分布 (不依赖正态)
- 公式简单, 易解释

**缺点**:
- 不区分"测量错误"和"真实极端" (业务判断需要人工)
- 单变量, 不捕捉多字段组合异常
- 对小样本不稳定 (Q1/Q3 受少量数据影响)

## 2.4 与其他方法对比 (拓展)

- **3σ 法**: $|x - \mu| > 3 \sigma$ → 异常。前提: 数据近正态。受异常值反向影响 (异常拉大 σ)。
- **Z-score 改良**: 用中位数和 MAD 替换均值和 σ
- **机器学习**: Isolation Forest, LOF (Local Outlier Factor) — 不要求分布假设, 多字段组合, 但需训练

工程默认 IQR (本关), 数据量大且需自动化时上 ML。


## 处理策略与业务案例

## 3.1 异常值处理的三种策略

检测出 outlier 后处理选择:

**删除 (drop)**: 直接丢弃异常行 / 列
- 适用: 异常确认是错误 + 总量充足
- 副作用: 减少样本量, 可能引入选择偏差

**截断 (clip / winsorize)**: 把异常值改到上下界
- $\hat{x} = \max(\min(x, \text{upper}), \text{lower})$
- 适用: 不想丢数据但想削弱异常影响
- 副作用: 边界处会出现"尖峰" (多个值都在 lower/upper)

**替换为 NaN 后补全**: 把异常变成 missing, 再走补全 (WX02 复习)
- 适用: 想用其他统计量替代极端值
- 副作用: 引入"补全"的不确定性

本关函数 `clip_value_to_range` 实现截断策略, 是最常用的工程方案。

## 3.2 业务案例: 工厂传感器异常温度

场景: 工厂车间温度传感器每分钟采样, 偶尔传感器故障会输出 999 度或 -999 度 (传感器掉线 marker)。

检测+处理流水线:
1. **历史数据算 Q1/Q3** (本关需要的输入): 历史 7 天数据, Q1=22, Q3=28, IQR=6
2. **算上下界** (本关): k=1.5, lower = 22 - 9 = 13, upper = 28 + 9 = 37
3. **判断每条新数据是否异常** (本关 is_outlier_iqr)
4. **统计异常计数** (本关 count_outliers): 1 小时内 > 5 个异常 → 设备报警
5. **截断处理** (本关 clip): 异常值截断到 [13, 37], 或替换为 NaN 走补全

工程实务: 异常报警阈值 (5 个 / 小时) 是经验值, 具体业务现场调。

## 3.3 工程口诀

- **IQR 是默认**: 不假设分布, 鲁棒
- **k=1.5 是默认 multiplier**: 大数据可调到 3.0 减少误报
- **删除 vs 截断**: 看场景, 工业默认截断
- **检测前看分布**: 直方图 / 箱线图必须先看
- **异常报警与异常清洗分开**: 报警是实时, 清洗是事后

## 3.4 异常值的合理性判断

不是所有 IQR 检测出的"异常"都该清洗:
- **物理不可能**: 年龄 -1 / 200 → 必清洗
- **统计极端但物理合理**: 双 11 流量 100x → 保留 (业务有意义)
- **测量带宽边界**: 传感器最大测量 50 度, 输出 50 → 截断到 50 不一定对

工程经验: 清洗前必须**人工抽样**几条 outlier 看, 不要盲目清洗。

$v$,
        $v${"questions": [{"id": "q04-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx04.py 中的 4 个函数; 评测以 test_wx04.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_iqr_normal_value$v$, $v$Q1=10, Q3=20, IQR=10, mult=1.5: lower=-5, upper=35. value=15 → not outlier$v$, false, $v$Q1=10, Q3=20, IQR=10, mult=1.5: lower=-5, upper=35. value=15 → not outlier$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_iqr_low_outlier$v$, $v$value=-10 < lower=-5 → outlier$v$, false, $v$value=-10 < lower=-5 → outlier$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_iqr_at_upper_boundary$v$, $v$value=35 == upper → not outlier (>, 严格大)$v$, false, $v$value=35 == upper → not outlier (>, 严格大)$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_iqr_extreme_multiplier$v$, $v$mult=3.0: lower=-20, upper=50. value=40 → not outlier$v$, false, $v$mult=3.0: lower=-20, upper=50. value=40 → not outlier$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_iqr_q1_eq_q3$v$, $v$Q1==Q3 → IQR=0, lower=upper=q1. 任何不等于 q1 都是 outlier$v$, false, $v$Q1==Q3 → IQR=0, lower=upper=q1. 任何不等于 q1 都是 outlier$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_iqr_raises_on_q1_gt_q3$v$, $v$iqr raises on q1 gt q3$v$, false, $v$iqr raises on q1 gt q3$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_iqr_raises_on_non_numeric$v$, $v$iqr raises on non numeric$v$, false, $v$iqr raises on non numeric$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_bounds_normal$v$, $v$Q1=10, Q3=20, mult=1.5 → (-5, 35)$v$, false, $v$Q1=10, Q3=20, mult=1.5 → (-5, 35)$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_bounds_extreme_multiplier$v$, $v$mult=3.0 → (-20, 50)$v$, false, $v$mult=3.0 → (-20, 50)$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_bounds_default$v$, $v$default 1.5$v$, false, $v$default 1.5$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_bounds_negative_q1$v$, $v$Q1=-5, Q3=5, mult=1.5: IQR=10, → (-20, 20)$v$, false, $v$Q1=-5, Q3=5, mult=1.5: IQR=10, → (-20, 20)$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_bounds_q1_eq_q3$v$, $v$Q1==Q3=10 → IQR=0, (10, 10) (boundary)$v$, false, $v$Q1==Q3=10 → IQR=0, (10, 10) (boundary)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_bounds_raises_on_q1_gt_q3$v$, $v$bounds raises on q1 gt q3$v$, false, $v$bounds raises on q1 gt q3$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_bounds_raises_on_non_numeric$v$, $v$bounds raises on non numeric$v$, true, $v$bounds raises on non numeric$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_clip_in_range$v$, $v$clip in range$v$, true, $v$clip in range$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_clip_below_lower$v$, $v$clip below lower$v$, true, $v$clip below lower$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_clip_above_upper$v$, $v$clip above upper$v$, true, $v$clip above upper$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_clip_at_lower_boundary$v$, $v$clip at lower boundary$v$, true, $v$clip at lower boundary$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_clip_negative_range$v$, $v$clip negative range$v$, true, $v$clip negative range$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_clip_raises_on_lower_gt_upper$v$, $v$clip raises on lower gt upper$v$, true, $v$clip raises on lower gt upper$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_co_no_outliers$v$, $v$全在范围内 → 0$v$, true, $v$全在范围内 → 0$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_co_one_high$v$, $v$co one high$v$, true, $v$co one high$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_co_one_low$v$, $v$co one low$v$, true, $v$co one low$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_co_mixed$v$, $v$co mixed$v$, true, $v$co mixed$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_co_at_boundaries$v$, $v$5 == lower 不算 outlier (< 严格)$v$, true, $v$5 == lower 不算 outlier (< 严格)$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_co_raises_on_lower_gt_upper$v$, $v$co raises on lower gt upper$v$, true, $v$co raises on lower gt upper$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_co_raises_on_non_list$v$, $v$co raises on non list$v$, true, $v$co raises on non list$v$, NULL, 27)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
