-- ============================================================
-- MJ3: 数据预处理与特征工程
-- practice_id=7, order_in_practice=3
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$数据预处理与特征工程$v$,
        'PRACTICE',
        3,
        $v$intermediate$v$,
        $v$## 为什么需要预处理

## 1.1 预处理在 CRISP-DM 中的位置

预处理 (Data Preparation) 是 CRISP-DM 的第三阶段, 承接数据理解 (EDA) 的产出, 为后续建模做数据规整。它通常占整个项目时间的 50%-70%, 是分析师投入最大的环节, 也是决定建模上限的关键 — 下游算法再强, 也救不回严重缺陷的数据。

预处理的产出是 "建模就绪的数据集": 没有缺失、特征类型统一、量纲对齐、噪声列已剔除。

## 1.2 预处理的四个核心动作

| 动作 | 解决的问题 | 典型方法 |
|------|----------|----------|
| 缺失值处理 | 数据不完整 | 删除 / 中位数填充 / 众数填充 / 模型预测填充 |
| 类别编码 | 字符串/类别无法直接计算 | 标签编码 (有序) / 独热编码 (无序) |
| 数值标准化 | 不同量纲特征数值差异大 | z-score / Min-Max / 鲁棒标准化 |
| 特征筛选 | 噪声列、常量列、冗余列 | 方差阈值 / 与目标低相关删除 |

四个动作有顺序依赖: 缺失值不处理, 后续标准化会出 NaN; 类别不编码, 标准化会报错; 没筛掉零方差列, 标准化时除以 0 直接崩。**正确顺序: 缺失填充 → 类别编码 → 数值标准化 → 特征筛选**。


## 缺失值处理

## 2.1 中位数 vs 均值 vs 众数

数值列的缺失填充, 三种最常用策略:

| 策略 | 适用 | 风险 |
|------|------|------|
| 均值填充 | 分布对称、无极端值 | 长尾分布会被极值拉偏 |
| **中位数填充** | 分布偏斜或含极端值 | 引入更密集的中位数附近样本 |
| 众数填充 | 类别变量 | 加剧多数类的主导 |

工程实践口诀: **数值列优先中位数, 类别列用众数**。中位数对异常值鲁棒, 是无脑安全选择。均值只在你确认分布无长尾时才用。

## 2.2 边界情况

- **全部缺失**: 列里没有任何非 None 值, 中位数无法计算 — 这种列直接删, 不填
- **只有一个非 None 值**: 中位数 = 那个值本身, 但这种列的方差为 0, 后续会被特征筛选删掉
- **混入类型**: 列里既有数字又有字符串, 不是统计学问题, 是数据质量问题, 必须先清洗类型再填充


## 类别编码

## 3.1 标签编码 (Label Encoding)

把字符串类别映射为整数。规则:

- 收集去重 → 排序 (保证确定性) → 顺序编号 0, 1, 2, ...
- 同一字符串多次出现, 编号一致

原始: `['cat', 'dog', 'cat', 'bird']` → 去重排序 `['bird', 'cat', 'dog']` → 编号 `{'bird':0, 'cat':1, 'dog':2}` → 编码后 `[1, 2, 1, 0]`

关键陷阱: **必须基于排序后的去重列表分配编号, 不是原始出现顺序**。否则不同的训练/测试集会得到不同的编码, 产生数据泄漏。

## 3.2 标签编码的语义陷阱

标签编码引入了"序"的假设: 0 < 1 < 2。这对**有序类别** (small < medium < large) 是合理的, 对**无序类别** (red, blue, green) 是错误的 — 模型会把"红 < 蓝 < 绿"当成数值大小关系学习, 进而产生奇怪的决策边界。

实务规则: 有序类别用标签编码, 无序类别必须用独热编码 (One-Hot)。本关只实现标签编码, 学生需要自己识别业务上是否有序。


## 标准化与方差过滤

## 4.1 z-score 标准化

把一列数值变换为均值 0、标准差 1 的分布:

$z_i = \frac{x_i - \bar{x}}{\sigma}$

其中 $\bar{x}$ 是均值, $\sigma$ 是 (总体) 标准差。注意标准差用 N 作分母 (population std), 而不是 N-1 (sample std) — 不同库默认值不同, 必须显式约定一种。本关约定 N。

## 4.2 标准化的边界条件

- $\sigma = 0$ 时分母为零, 必须报错 (这种列其实是常量列, 不该到这一步)
- 单元素列 $\sigma$ 也是 0, 同上
- 空列直接报错

## 4.3 方差阈值过滤

多列数据 (矩阵) 中, 某列**方差很小或为 0** 通常意味着信息量极少 — 对所有样本都是同一个值, 学习不出任何模式。这种列在建模前应过滤掉。

规则: 给定阈值 $T$, 保留**方差严格大于 $T$** 的列, 删除其余列。返回值通常是 (过滤后的矩阵, 保留的列索引)。

经验阈值:
- $T = 0.0$: 仅删常量列 (最保守)
- $T = 0.01$: 删几乎是常量的列
- $T \geq 1.0$: 比较激进, 适合特征数极多的高维数据


## 业务案例: 信贷风控数据预处理

## 5.1 场景

银行风控部拿到 50 万条申贷数据, 字段含 `age`、`income`、`education`、`tenure`、`past_default`、`gender`。原始数据问题:

- `income` 缺失率 12% (用户不愿填)
- `education` 是字符串 "high_school"/"bachelor"/"master"/"phd"
- `gender` 是字符串 "M"/"F"
- `tenure` 与 `age` 量纲完全不同 (月 vs 岁), 数值跨度 [0, 50] vs [18, 80]
- `past_default` 中 90% 都是 0, 几乎是常量列

## 5.2 走完预处理流水线

**步 1 缺失填充**: `income` 用中位数填充 (申贷收入分布右偏长尾, 用 mean 会被高收入大客户拉偏)。

**步 2 类别编码**: `education` 是有序类别 (学历有高低), 用标签编码 `{high_school:0, bachelor:1, master:2, phd:3}`。`gender` 是无序类别, 本关只覆盖标签编码所以暂用 `{F:0, M:1}` (但实务中应改用独热编码避免引入 "F < M" 的假象)。

**步 3 数值标准化**: 对 `age`、`income`、`tenure` 三列分别做 z-score, 让它们量纲对齐。

**步 4 方差过滤**: `past_default` 90% 都是 0, 方差极低, 设阈值 0.05 删除。

## 5.3 常见陷阱

- 顺序错: 先标准化再填充 → 标准化时 NaN 传播, 整列变 NaN
- 量纲未对齐就直接训练: 高量纲特征主导损失, 模型只学到这一个特征
- 类别编码时基于"出现顺序": 训练集和测试集编码不一致, 上线后报错
- 删除常量列前没看业务: 有些"常量列"其实是采样偏差, 业务上还需要它

预处理不是机械流水线, 每一步都要带着业务判断 — 数据告诉你"这列有 12% 缺失", 业务告诉你"这 12% 是高收入隐瞒, 不是随机缺失"。两者结合才是合格预处理。

$v$,
        $v${"questions": [{"id": "q03-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj03.py 中的 4 个函数; 评测以 test_mj03.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_le_basic$v$, $v$le basic$v$, false, $v$le basic$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_le_two_classes$v$, $v$le two classes$v$, false, $v$le two classes$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_le_single_element$v$, $v$le single element$v$, false, $v$le single element$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_le_all_same$v$, $v$le all same$v$, false, $v$le all same$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_le_sorted_assignment$v$, $v$关键: 编号基于去重排序$v$, false, $v$关键: 编号基于去重排序$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_le_raises_on_empty$v$, $v$le raises on empty$v$, false, $v$le raises on empty$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_le_raises_on_non_list$v$, $v$le raises on non list$v$, false, $v$le raises on non list$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_le_raises_on_non_string_element$v$, $v$le raises on non string element$v$, false, $v$le raises on non string element$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_zscore_basic$v$, $v$[1,2,3,4,5] mean=3, std=sqrt(2), 中心元素 0.0$v$, false, $v$[1,2,3,4,5] mean=3, std=sqrt(2), 中心元素 0.0$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_zscore_centered$v$, $v$[-2,-1,0,1,2] 已中心化$v$, false, $v$[-2,-1,0,1,2] 已中心化$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_zscore_two_values$v$, $v$[100, 200] mean=150 std=50 → [-1, 1]$v$, false, $v$[100, 200] mean=150 std=50 → [-1, 1]$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_zscore_known_4$v$, $v$[1,3,5,7] mean=4 std=sqrt(5) → known$v$, false, $v$[1,3,5,7] mean=4 std=sqrt(5) → known$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_zscore_raises_on_constant$v$, $v$边界: 全相同 std=0 → ValueError$v$, false, $v$边界: 全相同 std=0 → ValueError$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_zscore_raises_on_single$v$, $v$边界: 单元素 std=0 → ValueError$v$, false, $v$边界: 单元素 std=0 → ValueError$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_zscore_raises_on_empty$v$, $v$边界: 空列表 → ValueError$v$, false, $v$边界: 空列表 → ValueError$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_zscore_raises_on_non_list$v$, $v$zscore raises on non list$v$, false, $v$zscore raises on non list$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_fwm_replace_one$v$, $v$[1,2,None,4,5] median=3 → [1,2,3,4,5]$v$, true, $v$[1,2,None,4,5] median=3 → [1,2,3,4,5]$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_fwm_two_nones$v$, $v$[None,1,2,3,None] median=2 → [2,1,2,3,2]$v$, true, $v$[None,1,2,3,None] median=2 → [2,1,2,3,2]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_fwm_one_none_three_values$v$, $v$[10,None,20] median(of [10,20])=15 → [10,15,20]$v$, true, $v$[10,None,20] median(of [10,20])=15 → [10,15,20]$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_fwm_constant_with_none$v$, $v$[5,5,None,5,5] median=5 → [5,5,5,5,5]$v$, true, $v$[5,5,None,5,5] median=5 → [5,5,5,5,5]$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_fwm_known_median$v$, $v$[10,20,None,40,50] median(of 4 even-count)=(20+40)/2=30 → [10,20,30,40,50]$v$, true, $v$[10,20,None,40,50] median(of 4 even-count)=(20+40)/2=30 → [10,20,30,40,50]$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_fwm_all_none_raises$v$, $v$边界: 全部 None → ValueError$v$, true, $v$边界: 全部 None → ValueError$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_fwm_empty_raises$v$, $v$边界: 空列表 → ValueError$v$, true, $v$边界: 空列表 → ValueError$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_fwm_raises_on_non_list$v$, $v$fwm raises on non list$v$, true, $v$fwm raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_flv_remove_constant$v$, $v$col 1 是常量 [2,2,2] var=0, threshold=0 严格大于, 删除$v$, true, $v$col 1 是常量 [2,2,2] var=0, threshold=0 严格大于, 删除$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_flv_high_threshold_keeps_high_var$v$, $v$matrix var: col0≈13.56, col1=0, col2≈10.67. threshold=12.0 → 仅 col 0$v$, true, $v$matrix var: col0≈13.56, col1=0, col2≈10.67. threshold=12.0 → 仅 col 0$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_flv_keep_all$v$, $v$全 var > threshold, 全保留$v$, true, $v$全 var > threshold, 全保留$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_flv_three_kept_of_four$v$, $v$4 列: col0 var=2/3, col1=0, col2≈0.222, col3 var=2/3, threshold=0.0 → 删 col1$v$, true, $v$4 列: col0 var=2/3, col1=0, col2≈0.222, col3 var=2/3, threshold=0.0 → 删 col1$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_flv_threshold_excludes_some$v$, $v$4 列, threshold=0.5: col0 var=2/3>0.5, col2 var≈0.222<0.5 → 删 col1+col2$v$, true, $v$4 列, threshold=0.5: col0 var=2/3>0.5, col2 var≈0.222<0.5 → 删 col1+col2$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_flv_raises_on_single_sample$v$, $v$边界: 单样本无法算方差 → ValueError$v$, true, $v$边界: 单样本无法算方差 → ValueError$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_flv_raises_on_empty$v$, $v$边界: 空矩阵 → ValueError$v$, true, $v$边界: 空矩阵 → ValueError$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_flv_raises_on_non_list$v$, $v$负例: 非 list → TypeError$v$, true, $v$负例: 非 list → TypeError$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
