-- ============================================================
-- MJ1: 数据挖掘概述与流程
-- practice_id=7, order_in_practice=1
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$数据挖掘概述与流程$v$,
        'PRACTICE',
        1,
        $v$beginner$v$,
        $v$## CRISP-DM 标准流程

## 1.1 六阶段定义

Cross-Industry Standard Process for Data Mining 是业界最权威的数据挖掘方法论, 共 6 阶段:

| 阶段 | 核心任务 |
|------|---------|
| 业务理解 | 明确业务目标、确定挖掘目标、评估资源 |
| 数据理解 | 收集数据、描述数据、探索数据质量 |
| 数据准备 | 清洗数据、缺失值处理、构建特征 |
| 建模 | 选择算法、训练模型、调整超参数 |
| 评估 | 模型评估、结果解释、业务验证 |
| 部署 | 上线、监控、维护 |

流程不是单向的: 业务理解 ↔ 数据理解 之间有迭代回路; 评估发现问题可回到数据准备; 部署后的监控反馈可触发新一轮业务理解。

## 1.2 活动到阶段的映射

实务中要识别"现在做的事属于哪个阶段", 才能正确投入资源。下表给出关键词参考:

| 关键词 | 阶段 |
|--------|------|
| 业务目标 / 项目章程 / KPI / ROI | 业务理解 |
| 数据字典 / 描述统计 / 缺失分布 / 字段含义 | 数据理解 |
| 缺失值填充 / 编码 / 标准化 / 划分训练测试集 | 数据准备 |
| 选模型 / 训练 / 拟合 / 超参数 / 调参 | 建模 |
| 测试集得分 / 业务对齐 / 错误案例分析 | 评估 |
| 上线 / 推理服务 / 监控 / 运维 | 部署 |

## 1.3 业务案例: 信贷违约预测走完 CRISP-DM

银行风控部要建立违约预测模型, 6 阶段如下:

**业务理解**: 风控负责人提出"30 天逾期作为违约定义", 业务目标"违约率从 4% 降到 2%", 关键 KPI 是"对违约样本的识别能力", 资源约束 6 周开发周期 + 3 名工程师。在这一阶段就要敲定: 漏掉一个真违约的代价 (坏账损失) 远大于错杀一个正常客户 (一次拒贷), 这决定了后续评估指标的取舍。

**数据理解**: 收集 3 年历史申贷数据 (50 万条), 字段含义对齐: tenure (在网月数)、income (月收入)、past_default (历史违约次数)、current_balance (当前余额)。先做单字段描述统计与缺失率扫描 — 发现 income 缺失率 12%, 这条线索决定了后续数据准备如何处理。

**数据准备**: 数值特征做缺失值填充与标准化, 类别特征做编码, 划分训练/测试集时注意类别比例 (违约样本只占 4%, 不分层划分会让测试集小类几乎消失)。这一阶段占整个项目时间约 60%, 是最耗时的环节。

**建模**: 选若干分类算法分别训练, 比较测试集表现。同一份数据, 不同算法的强项不同 — 这一阶段不追求一次到位, 而是建立对比基线。

**评估**: 测试集得分要和业务目标对齐 — 风控关心的不是 accuracy 高低, 而是"在召回 80% 违约样本的前提下, 误伤率有多低"。如果模型测试得分高但业务方说"不可用", 评估阶段就要回到数据准备或建模。

**部署**: 模型上线后接入实时申贷系统, 定期对比"模型预测违约率 vs 实际违约率"; 出现明显漂移就触发新一轮业务理解 (是否市场环境变了, 是否字段定义变了)。


## 监督 / 无监督 / 半监督 学习的判别

## 2.1 三类学习的判别表

| 是否有标签 | 是否全部标注 | 学习类型 |
|------------|--------------|----------|
| 否         | (无关)       | 无监督 (unsupervised) |
| 是         | 是           | 监督 (supervised) |
| 是         | 否 (部分)    | 半监督 (semi-supervised) |

边界情况: "无标签" 不论 `all_labeled` 取何值, 结论都是无监督 — 因为根本没有标签可言。

## 2.2 三类学习的典型场景

- **监督**: 信贷违约预测 (历史违约记录 = 标签)、垃圾邮件识别 (人工标注 = 标签)、销售额回归
- **无监督**: 客户分群 (没有"正确分组"标签)、异常检测 (没有"异常/正常"标签)
- **半监督**: 医学影像识别 (人工标注成本高, 通常 5%-10% 标注 + 90%+ 未标注)

为什么半监督场景越来越重要: 业务现实中拿到大量未标注数据是常态, 而把每条都标注成本极高。半监督让"有限的人工标注 + 海量自然数据"可以一起利用。


## Accuracy 与过拟合诊断

## 3.1 Accuracy 公式

最基础的分类评估指标:

$\text{Accuracy} = \frac{\text{预测正确的样本数}}{\text{总样本数}}$

实现要点:
- 预测列表与真实列表长度必须一致 (不一致应视为输入错误)
- 空输入应视为异常 (没有样本无法计算比例)
- 多分类与二分类计算方式相同, 只看 `y_true[i] == y_pred[i]` 是否成立

## 3.2 Accuracy 在类别不平衡时的失效

回到信贷违约 4% 的例子: 一个"无脑全部预测为不违约"的"模型", accuracy = 96%, 看似漂亮。但它对违约样本的识别能力 = 0%, 业务上完全无用。

这说明 accuracy 在类别极度不平衡时会被多数类主导, 给出虚假的"高分"信号。这种场景下需要更细致的分类指标 — 区分"对每一类的识别能力" — 这部分进阶指标在后续章节展开, 本关只要求能识别 accuracy 的局限。

口诀: **类别比例越偏离 50:50, accuracy 越不可信**。1:1 时 accuracy 是好指标; 96:4 时 accuracy 必须被替换或与其他指标搭配。

## 3.3 过拟合判断

用 "训练集得分 - 测试集得分" 的差值 (gap) 与阈值比较:

$\text{gap} = \text{train\_acc} - \text{test\_acc}$

$\text{is\_overfit} = (\text{gap} > \text{threshold})$

默认 threshold=0.1。**严格大于**, 等于阈值不算过拟合。

## 3.4 为什么不能只看 train_acc

新手常犯的错误: 训练得分 99%, 直接交付。这种模型在生产中通常表现极差 — 它把训练样本的噪声/巧合也学进去了, 看到从未见过的样本就懵。

gap 揭示的是模型的泛化能力: 一个 train=0.99 / test=0.60 的模型, gap=0.39, 极严重过拟合; 一个 train=0.85 / test=0.83 的模型, gap=0.02, 反而是更可靠的"训练充分但没记噪声"。

## 3.5 threshold=0.1 的来源

0.1 是工程经验值, 不是数学公式得出的。背后有三个考量:
- **样本噪声**: 即使是同一数据集, 不同随机划分, train 与 test 也会有几个百分点的自然波动 (3%-5% 常见), threshold 必须高于这个噪声底
- **统计显著性**: gap < 0.05 几乎一定在自然波动范围内, gap > 0.10 则大概率是真过拟合
- **业务容忍**: 0.10 是一个保守门槛, 业务关键场景 (医疗、风控) 实际上会用更严的 0.05; 探索性建模可放宽到 0.15

所以 threshold=0.1 不是真理, 是默认值。在你自己的项目中, 应根据数据量、业务容忍度调整。

$v$,
        $v${"questions": [{"id": "q01-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj01.py 中的 4 个函数; 评测以 test_mj01.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_phase_business_understanding$v$, $v$phase business understanding$v$, false, $v$phase business understanding$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_phase_data_preparation$v$, $v$phase data preparation$v$, false, $v$phase data preparation$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_phase_modeling$v$, $v$phase modeling$v$, false, $v$phase modeling$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_phase_deployment$v$, $v$phase deployment$v$, false, $v$phase deployment$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_phase_unknown_for_empty_string$v$, $v$边界: 空字符串 → 未知$v$, false, $v$边界: 空字符串 → 未知$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_phase_raises_on_non_string$v$, $v$负例: 非字符串输入 → TypeError$v$, false, $v$负例: 非字符串输入 → TypeError$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_lt_supervised$v$, $v$lt supervised$v$, false, $v$lt supervised$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_lt_unsupervised_when_no_labels$v$, $v$lt unsupervised when no labels$v$, false, $v$lt unsupervised when no labels$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_lt_semi_supervised_when_partial$v$, $v$lt semi supervised when partial$v$, false, $v$lt semi supervised when partial$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_lt_unsupervised_dominates_when_no_labels_even_if_all_labeled_true$v$, $v$边界: has_labels=False 时 all_labeled 取何值都是 unsupervised$v$, false, $v$边界: has_labels=False 时 all_labeled 取何值都是 unsupervised$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_lt_raises_on_non_bool$v$, $v$负例: 非 bool 输入 → TypeError$v$, false, $v$负例: 非 bool 输入 → TypeError$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_acc_all_correct$v$, $v$acc all correct$v$, false, $v$acc all correct$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_acc_all_wrong$v$, $v$acc all wrong$v$, true, $v$acc all wrong$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_acc_partial$v$, $v$acc partial$v$, true, $v$acc partial$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_acc_multiclass$v$, $v$acc multiclass$v$, true, $v$acc multiclass$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_acc_single_sample_correct$v$, $v$边界: 单样本$v$, true, $v$边界: 单样本$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_acc_raises_on_empty$v$, $v$边界: 空列表 → ValueError$v$, true, $v$边界: 空列表 → ValueError$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_acc_raises_on_length_mismatch$v$, $v$负例: 长度不一致 → ValueError$v$, true, $v$负例: 长度不一致 → ValueError$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_of_clearly_overfit$v$, $v$of clearly overfit$v$, true, $v$of clearly overfit$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_of_not_overfit_small_gap$v$, $v$of not overfit small gap$v$, true, $v$of not overfit small gap$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_of_not_overfit_zero_gap$v$, $v$of not overfit zero gap$v$, true, $v$of not overfit zero gap$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_of_threshold_strict_greater$v$, $v$边界: gap 等于 threshold 不算过拟合 (严格 >)$v$, true, $v$边界: gap 等于 threshold 不算过拟合 (严格 >)$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_of_extreme_gap$v$, $v$边界: 极值 gap=1.0$v$, true, $v$边界: 极值 gap=1.0$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_of_raises_on_non_numeric$v$, $v$负例: 非数值 → TypeError$v$, true, $v$负例: 非数值 → TypeError$v$, NULL, 24)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
