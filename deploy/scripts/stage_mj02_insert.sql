-- ============================================================
-- MJ2: 数据探索与特征理解
-- practice_id=7, order_in_practice=2
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$数据探索与特征理解$v$,
        'PRACTICE',
        2,
        $v$beginner$v$,
        $v$## 数据概况与摘要统计

## 1.1 EDA 在 CRISP-DM 中的位置

探索性数据分析 (Exploratory Data Analysis, EDA) 属于 CRISP-DM 的"数据理解"阶段, 在建模之前完成。它不直接产生模型, 但决定后续每一步: 哪些字段值得用, 哪些字段需要清洗, 哪些样本是异常, 哪些假设可能不成立。

新手的常见错误是跳过 EDA 直接建模 — 结果模型表现差, 也找不到原因。EDA 给出的不是答案, 而是问题清单。

## 1.2 摘要统计的五个核心指标

| 指标 | 含义 | 用途 |
|------|------|------|
| count / 缺失数 | 非空样本数 | 判断数据完整性 |
| mean | 算术平均 | 中心趋势 (受极端值影响) |
| median | 中位数 | 中心趋势 (鲁棒) |
| std | 标准差 | 数据波动 |
| range | 极差 (max - min) | 跨度与可能极值 |

## 1.3 mean vs median 的取舍

数据是单峰对称分布时 mean 与 median 接近, 用任何一个都行。但**数据有长尾或极端值时 mean 会被拉偏**, median 才是更可信的中心指示。

电商订单金额是典型例子: 100 个用户里 5 个 VIP 各下了 1 万的订单, 95 个普通用户各下 100。mean ≈ 595, 远高于 median = 100。如果你用 mean 给运营部 "客单价 600" 做促销策略, 会严重误导。

口诀: 怀疑长尾或极值时, 优先汇报 median; 同时贴 mean / median 比值 — 比值远离 1 就是分布失称的信号。


## 相关性分析

## 2.1 Pearson 相关系数

Pearson 衡量两个数值变量的**线性**关系强度。

$r = \frac{\sum_{i=1}^{n} (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2 \sum (y_i - \bar{y})^2}}$

取值区间 $r \in [-1, 1]$:

| r 区间 | 解读 |
|---------|------|
| 0.8 ~ 1.0 | 强正相关 |
| 0.5 ~ 0.8 | 中等正相关 |
| 0.2 ~ 0.5 | 弱正相关 |
| -0.2 ~ 0.2 | 几乎无关 |
| -0.5 ~ -0.2 | 弱负相关 |
| -0.8 ~ -0.5 | 中等负相关 |
| -1.0 ~ -0.8 | 强负相关 |

## 2.2 解读陷阱

**陷阱 1: 相关 ≠ 因果**。 冰淇淋销量与溺水人数高度正相关 — 但不是冰淇淋导致溺水, 是夏天 (混淆变量) 导致两者同时上升。

**陷阱 2: 非线性关系下 Pearson 失效**。 $y = x^2$ 在 $x \in [-5, 5]$ 上 Pearson 接近 0, 看似不相关, 但其实是完美的二次关系。诊断方法: 怀疑非线性时, 散点图比相关数值更可靠; 也可以用 Spearman 秩相关补充 (Spearman 对单调非线性敏感)。

**陷阱 3: 一个极端值能颠覆 r**。 一个比其他样本大 100 倍的离群点可以让 r 从 0.1 跳到 0.9。计算 r 之前要先看分布, 必要时排除极端值再计算或对比两版结果。

**陷阱 4: 零方差导致未定义**。 当 x 或 y 所有值相同 (方差为 0) 时, 公式分母为零。实现上必须显式处理 — 抛错或返回 NaN, 不能让后续代码用一个错误数继续算下去。


## 异常值与四分位数

## 3.1 四分位数

把排序后的数据等分成 4 段, 三个分割点叫四分位数:

- **Q1** (第一四分位数, 25% 分位): 数据的 25% 在它以下
- **Q2** (中位数, 50% 分位): 数据的 50% 在它以下
- **Q3** (第三四分位数, 75% 分位): 数据的 75% 在它以下

五数概括 (5-number summary) = $[\min, Q_1, Q_2, Q_3, \max]$, 是描述分布的最常用形态。箱线图就是它的可视化。

## 3.2 IQR 异常值规则

$IQR = Q_3 - Q_1$ (中间 50% 数据的跨度)

异常值定义:
$x < Q_1 - 1.5 \times IQR$ 或 $x > Q_3 + 1.5 \times IQR$

为什么是 1.5? 这是经验阈值 (与 MJ01 过拟合 threshold=0.1 同样的工程哲学): 在正态分布下覆盖约 99.3% 的样本, 让 0.7% 落在外面被标记。**1.5 不是数学定律, 而是 Tukey 当年提出的折中值**。需要更严的场景 (金融风控) 改 3.0; 需要更宽 (探索性分析) 改 1.0。

## 3.3 异常值不等于错误

新手最常见的错误是看到异常值就删除。实际上异常值有三种:

1. **录入错误**: 比如年龄 200, 应该删或修
2. **真实极端**: 大客户、暴雨天的销量、欺诈交易 — 这些是数据集中最有信息量的部分, 删了等于把分析价值扔掉
3. **测量噪声**: 设备故障产生的离群读数 — 视情况而定

处理顺序: **先看原始数据 → 理解业务上下文 → 再决定丢/留/修**。在不知道异常来源时直接 `drop` 是分析事故的常见原因。


## 业务案例: 电商用户行为 EDA

## 4.1 场景背景

电商运营拿到 10 万条用户购买记录, 想理解"用户购买金额"的分布特征, 为 VIP 分级和营销活动提供数据基础。

## 4.2 EDA 流程走一遍

**第 1 步 看摘要统计**: count=100000 (无缺失), mean=200, median=80, std=350, range=[10, 5000]。第一眼看到 mean (200) 远高于 median (80), 立即提示分布右偏。

**第 2 步 看分布形态**: 画直方图发现典型长尾分布 — 大部分用户金额集中在 50-150, 一小撮高金额订单拉到 1000-5000。**5% 的用户贡献了 80% 的收入** (帕累托定律在电商上的常态)。

**第 3 步 看相关性**: "浏览时长" vs "购买金额", Pearson r=0.15, 看似几乎无关。但散点图揭示是 J 型曲线 — 浏览太短 (冲动购买) 和浏览太长 (反复比价) 都买得多, 中段反而少。Pearson 在这种非单调关系下失效, 必须配散点图。

**第 4 步 看异常值**: $Q_3 + 1.5 \times IQR$ 阈值 ≈ 600。超过 600 的"超大订单" 800 条。先不要 drop — 业务侧确认这些是企业客户批量采购, 应单独建一个 VIP 分群, 而不是当噪声删掉。

## 4.3 EDA 的直觉口诀

- **mean 单独看不可信**, 一定配 median 看分布是否对称
- **相关数值不能脱离散点图**, 数值好看不代表关系存在
- **异常值先理解再处理**, 业务上下文优先于统计规则
- **EDA 的产出不是结论, 是后续建模的问题清单与假设清单**

做完 EDA 你应该带着 "客单价应按 median 而非 mean 上报"、"浏览时长非单调, 不能直接当线性特征"、"VIP 客户需要单独分析" 这类业务可操作的结论, 进入下一阶段。

$v$,
        $v${"questions": [{"id": "q02-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj02.py 中的 4 个函数; 评测以 test_mj02.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_corr_perfect_positive$v$, $v$corr perfect positive$v$, false, $v$corr perfect positive$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_corr_perfect_negative$v$, $v$corr perfect negative$v$, false, $v$corr perfect negative$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_corr_known_value_0_8$v$, $v$x=[1,2,3,4], y=[1,3,2,4] 的 Pearson r = 0.8 (手算验证)$v$, false, $v$x=[1,2,3,4], y=[1,3,2,4] 的 Pearson r = 0.8 (手算验证)$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_corr_zero$v$, $v$x=[1,2,3,4,5], y=[1,4,5,4,1] 对称分布, r = 0.0$v$, false, $v$x=[1,2,3,4,5], y=[1,4,5,4,1] 对称分布, r = 0.0$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_corr_linear_scaled$v$, $v$y = 2x, 应得 r = 1.0$v$, false, $v$y = 2x, 应得 r = 1.0$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_corr_raises_on_zero_variance$v$, $v$边界: x 方差为 0 (全相同) → ValueError$v$, false, $v$边界: x 方差为 0 (全相同) → ValueError$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_corr_raises_on_length_mismatch$v$, $v$边界: 长度不一致 → ValueError$v$, false, $v$边界: 长度不一致 → ValueError$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_corr_raises_on_non_list$v$, $v$负例: 非 list 输入 → TypeError$v$, false, $v$负例: 非 list 输入 → TypeError$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_iqr_high_outlier$v$, $v$[1,2,3,4,5,100] 中 100 是异常值, 索引 5$v$, false, $v$[1,2,3,4,5,100] 中 100 是异常值, 索引 5$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_iqr_low_outlier$v$, $v$[-100,1,2,3,4,5] 中 -100 是异常值, 索引 0$v$, false, $v$[-100,1,2,3,4,5] 中 -100 是异常值, 索引 0$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_iqr_both_extremes$v$, $v$[1,2,3,4,5,100,-50] 两端各一异常, 升序索引 [5,6]$v$, false, $v$[1,2,3,4,5,100,-50] 两端各一异常, 升序索引 [5,6]$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_iqr_no_outliers$v$, $v$无异常值 → 空列表$v$, false, $v$无异常值 → 空列表$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_iqr_middle_extreme$v$, $v$[10,20,1000,30,40] 中 1000 在索引 2$v$, false, $v$[10,20,1000,30,40] 中 1000 在索引 2$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_iqr_two_high_outliers$v$, $v$密集正常值+末尾两极端: 200 与 300 都是异常 (索引 9,10)$v$, false, $v$密集正常值+末尾两极端: 200 与 300 都是异常 (索引 9,10)$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_iqr_raises_on_empty$v$, $v$边界: 空列表 → ValueError$v$, false, $v$边界: 空列表 → ValueError$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_iqr_raises_on_non_list$v$, $v$负例: 非 list → TypeError$v$, true, $v$负例: 非 list → TypeError$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_summary_basic$v$, $v$summary basic$v$, true, $v$summary basic$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_summary_constant$v$, $v$边界: 全相同值, std=0, range=0$v$, true, $v$边界: 全相同值, std=0, range=0$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_summary_signed$v$, $v$summary signed$v$, true, $v$summary signed$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_summary_single_element$v$, $v$边界: 单元素$v$, true, $v$边界: 单元素$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_summary_even_count_median$v$, $v$偶数个元素, median 取中间两个的平均$v$, true, $v$偶数个元素, median 取中间两个的平均$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_summary_raises_on_empty$v$, $v$边界: 空列表 → ValueError$v$, true, $v$边界: 空列表 → ValueError$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_summary_raises_on_non_list$v$, $v$负例: 非 list → TypeError$v$, true, $v$负例: 非 list → TypeError$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_quartiles_unsorted_5$v$, $v$未排序输入 [3,1,4,1,5] 的 5-num = [1,1,3,4,5]$v$, true, $v$未排序输入 [3,1,4,1,5] 的 5-num = [1,1,3,4,5]$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_quartiles_ten_values$v$, $v$10 元素, numpy 默认线性插值$v$, true, $v$10 元素, numpy 默认线性插值$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_quartiles_single_element$v$, $v$边界: 单元素 → 5 个值都等于该元素$v$, true, $v$边界: 单元素 → 5 个值都等于该元素$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_quartiles_constant$v$, $v$边界: 全相同 → 5 个值全等$v$, true, $v$边界: 全相同 → 5 个值全等$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_quartiles_two_values$v$, $v$2 元素 [0, 100] → [0, 25, 50, 75, 100]$v$, true, $v$2 元素 [0, 100] → [0, 25, 50, 75, 100]$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_quartiles_negative_values_unsorted$v$, $v$未排序负值 [10, -10, 5, -5, 0] 的 5-num = [-10,-5,0,5,10] (防 D 攻击巧合)$v$, true, $v$未排序负值 [10, -10, 5, -5, 0] 的 5-num = [-10,-5,0,5,10] (防 D 攻击巧合)$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_quartiles_raises_on_empty$v$, $v$边界: 空列表 → ValueError$v$, true, $v$边界: 空列表 → ValueError$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_quartiles_raises_on_non_list$v$, $v$负例: 非 list → TypeError$v$, true, $v$负例: 非 list → TypeError$v$, NULL, 31)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
