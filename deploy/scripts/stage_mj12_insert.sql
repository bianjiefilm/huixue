-- ============================================================
-- MJ12: 综合项目: 客户流失预测全流程
-- practice_id=7, order_in_practice=12
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$综合项目: 客户流失预测全流程$v$,
        'PRACTICE',
        12,
        $v$advanced$v$,
        $v$## 项目目标与数据约定

## 1.1 业务背景

电信运营商的核心 KPI 是用户保有率。客户流失 (Churn) 是指用户停止使用服务、转网或销户。每年流失率通常在 15%-25%, 召回一个老客户的成本远低于获取一个新客户, 因此流失预警是运营商的关键分析任务。

本关任务: 构造一份小规模但有代表性的客户流失数据, 走完一遍端到端建模, 重点验证你对前 11 关知识的整合能力。

## 1.2 数据 schema (5 个字段)

| 字段名 | 类型 | 含义 | 取值约束 |
|--------|------|------|----------|
| tenure | int | 在网月数 | 1-72 (新客最少 1 月, 上限按业务设定) |
| monthly_charges | float | 月费用 (元) | 30.0-150.0 |
| contract_type | str | 合同类型 | {"Month-to-month", "One year", "Two year"} |
| tech_support | str | 是否订阅技术支持 | {"Yes", "No"} |
| churn | int | 流失标签 | 0 (未流失) 或 1 (流失) |

数据规模: **100 行**。  类别比例: **80 行 churn=0, 20 行 churn=1** (与真实业务的 4:1 比例一致, 复习 MJ01 类别不平衡)。

## 1.3 流失数据的生成原则

- 不能是完美随机 — 要让特征与 churn 之间有可学习的相关 (例: 短 tenure 的用户更容易流失, Month-to-month 合同流失率高)
- 不能完全确定 — 加入合理噪声, 否则任何模型都 100% 准确, 失去对比意义
- 数值字段范围合理, 类别字段取值符合 schema


## 复用前 11 关的预处理

## 2.1 步 1 类别编码 (复用 MJ03)

`contract_type` 是有序类别 (Month-to-month < One year < Two year, 反映承诺时长), 适合**标签编码**:
$\{$ Month-to-month: 0, One year: 1, Two year: 2 $\}$

`tech_support` 是二值类别 (Yes/No), 标签编码或独热都行, 本关用标签编码以保持简单。

## 2.2 步 2 数值标准化 (复用 MJ03)

`tenure` 与 `monthly_charges` 量纲完全不同 (月数 1-72 vs 元 30-150), 必须 z-score 标准化, 否则月费会主导距离/梯度。

关键: **必须先 train/test split, 再用 train 的均值方差 fit_transform; test 只 transform**。这是 MJ03 的核心陷阱。

## 2.3 步 3 训练测试集划分 (复用 MJ03/MJ10)

80/20 划分。**类别不平衡时必须用 `stratify=y` 保证 train 和 test 都保持 4:1 比例**, 否则 test 集可能小类完全消失, 评估失真。

工程提醒: 如果数据量更大 (≥1000), 应该用 5 折分层 CV (复习 MJ10) 而非单一划分, 但本关数据量小, 单一划分 + 固定 seed 即可。


## 多模型对比 (复用 MJ04/05/11)

## 3.1 选 3 种差异化算法

集成的本质是利用模型差异 (复习 MJ11), 单关比较也应选差异化算法:

| 算法 | 来源关 | 强项 |
|------|--------|------|
| LogisticRegression | MJ04 | 线性可分场景 + 概率输出 + 高解释性 |
| DecisionTree | MJ04 | 非线性交互 + 决策路径可读 |
| RandomForest | MJ05 | Bagging 降方差 + 特征重要性 + 鲁棒 |

不要选 3 个 RF 或 3 个 LR — 那不是模型对比, 是冗余实验。

## 3.2 训练流程

对每个算法:
1. 在标准化后的训练集 fit
2. 在标准化后的测试集 predict
3. 计算测试集 accuracy (本关用 accuracy 做粗筛, 评估细节在下一节)

返回 dict $\{$ "LogisticRegression": acc1, "DecisionTree": acc2, "RandomForest": acc3 $\}$ 让业务方一眼对比。

## 3.3 类别不平衡的诊断

4:1 不平衡时, 一个**永远预测 0** 的"模型"也能拿 80% accuracy 看起来很好。本关里 accuracy=0.80 的模型其实毫无价值, accuracy=0.85 才算开始有信号。

复用 MJ01 的口诀: **类别不平衡时 accuracy 不可信**, 必须看 precision/recall/F1, 这是下一节的内容。


## 5 指标评估 + 业务建议

## 4.1 5 指标定义 (前 4 个来自 MJ04, 第 5 个是 MJ04 confusion matrix 的直接派生)

给定 confusion matrix (TP, FP, TN, FN):

$\text{accuracy} = \frac{TP + TN}{TP + FP + TN + FN}$

$\text{precision} = \frac{TP}{TP + FP}$ (预测为流失中真流失的比例)

$\text{recall} = \frac{TP}{TP + FN}$ (真流失中被识别出来的比例)

$\text{F1} = \frac{2 \cdot \text{precision} \cdot \text{recall}}{\text{precision} + \text{recall}}$

$\text{specificity} = \frac{TN}{TN + FP}$ (真不流失中正确识别的比例 — 即"不打扰好客户"的能力)

specificity 是 recall 的"另一面" — recall 强调小类识别率, specificity 强调大类不被误判率。两者一起看就是完整的 ROC 曲线两轴。

## 4.2 不平衡场景下的指标取舍

电信流失的业务考量:
- **漏掉一个真流失** = 损失一个长期 ARPU 用户
- **错判一个好客户为流失** = 多发一张召回券 (成本几元到几十元)

因此 **recall (漏报代价) > precision (误报代价)**, 阈值应调低优先 recall。F1 是综合, specificity 是补充诊断。

## 4.3 业务建议输出

模型上线后, 给业务方的输出不是"AUC 0.85", 而是:

- **Top-K 流失预测名单**: 把概率最高的 K 个用户给客户经理重点维护
- **细分挽留策略**: 月付用户给优惠券, 长合同用户给增值服务, tech_support=No 用户主动推送技术支持
- **A/B 测试**: 用模型预测的高流失用户分两组, 一组接受挽留行动, 一组对照, 看实际流失率差异 — 这是验证"模型是否真创造业务价值"的金标准

模型不是答案的终点, 是业务行动的起点。客户挽留的真实战场在客户经理的电话里、在客服优惠券推送里、在产品体验改进里 — 模型只是把"该重点关注谁"挑出来。

## 4.4 整合检查清单

做完这一关你应该:
- 自己生成 100 行 80/20 不平衡数据 (复用 MJ01 类别不平衡概念)
- 类别编码 + 标准化 + 分层划分 (复用 MJ03)
- 至少 3 种分类算法对比 (复用 MJ04/05)
- 5 指标全验, 不光 accuracy (复用 MJ04 + 派生 specificity)
- 业务可解释的输出 (复用 MJ02 EDA 思维 + MJ11 集成思想)

做不到任何一条, 说明前面某关的概念没真正掌握, 这是综合项目的诊断价值。

$v$,
        $v${"questions": [{"id": "q12-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj12.py 中的 4 个函数; 评测以 test_mj12.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_load_dict_5_keys$v$, $v$返回 dict 含 5 个特定键$v$, false, $v$返回 dict 含 5 个特定键$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_load_100_rows_each_field$v$, $v$每个字段都是 100 行$v$, false, $v$每个字段都是 100 行$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_load_churn_imbalance_80_20$v$, $v$churn 80 个 0 + 20 个 1 (4:1 不平衡)$v$, false, $v$churn 80 个 0 + 20 个 1 (4:1 不平衡)$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_load_tenure_range$v$, $v$tenure 在 1-72 月$v$, false, $v$tenure 在 1-72 月$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_load_charges_range$v$, $v$monthly_charges 在 30.0-150.0$v$, false, $v$monthly_charges 在 30.0-150.0$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_load_contract_type_values$v$, $v$contract_type 只能在 3 取值内$v$, false, $v$contract_type 只能在 3 取值内$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_load_tech_support_values$v$, $v$tech_support 只能 Yes 或 No$v$, false, $v$tech_support 只能 Yes 或 No$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_load_tenure_correlates_with_churn$v$, $v$handbook 要求: 短 tenure 用户更易流失 → avg(tenure | churn=1) < avg(tenure | churn=0)$v$, false, $v$handbook 要求: 短 tenure 用户更易流失 → avg(tenure | churn=1) < avg(tenure | churn=0)$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_load_charges_correlates_with_churn$v$, $v$handbook 要求: 高月费用户更易流失 → avg(charges | churn=1) > avg(charges | churn=0)$v$, false, $v$handbook 要求: 高月费用户更易流失 → avg(charges | churn=1) > avg(charges | churn=0)$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_load_month_to_month_correlates_with_churn$v$, $v$handbook 要求: Month-to-month 合同流失率高 → P(M-to-M|churn=1) > P(M-to-M|churn=0)$v$, false, $v$handbook 要求: Month-to-month 合同流失率高 → P(M-to-M|churn=1) > P(M-to-M|churn=0)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_pre_returns_4tuple$v$, $v$返回 4 元组$v$, false, $v$返回 4 元组$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_pre_split_ratio$v$, $v$80 / 20 划分: train 80 + test 20$v$, false, $v$80 / 20 划分: train 80 + test 20$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_pre_stratified_class_balance$v$, $v$分层划分后 train 和 test 都保持 4:1 比例$v$, false, $v$分层划分后 train 和 test 都保持 4:1 比例$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_pre_features_numeric$v$, $v$编码后所有 X 元素都是数值 (无字符串), 且 X_train 至少有 1 行$v$, false, $v$编码后所有 X 元素都是数值 (无字符串), 且 X_train 至少有 1 行$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_pre_standardized$v$, $v$标准化后 train 的数值列均值≈0, std>0$v$, true, $v$标准化后 train 的数值列均值≈0, std>0$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_pre_raises_on_missing_target$v$, $v$target_col 不在 data → ValueError$v$, true, $v$target_col 不在 data → ValueError$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_tcm_returns_dict_3_models$v$, $v$至少 3 个模型$v$, true, $v$至少 3 个模型$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_tcm_accuracies_in_range$v$, $v$每个模型 accuracy ∈ [0, 1]$v$, true, $v$每个模型 accuracy ∈ [0, 1]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_tcm_above_baseline$v$, $v$至少有 1 个模型 accuracy > 0.5 (优于全猜 0 的多数类基线... 实际上 4:1 多数类是 0.8) 要求至少 1 个模型 acc > 0.5 — 排除全无效模型$v$, true, $v$至少有 1 个模型 accuracy > 0.5 (优于全猜 0 的多数类基线... 实际上 4:1 多数类是 0.8) 要求至少 1 个模型 acc > 0.5 — 排除全无效模型$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_tcm_includes_classic_names$v$, $v$模型名应包含 LogisticRegression / DecisionTree / RandomForest 中至少 2 个$v$, true, $v$模型名应包含 LogisticRegression / DecisionTree / RandomForest 中至少 2 个$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_eval_perfect$v$, $v$全对: y=[1,1,0,0] pred=[1,1,0,0] → 全部 1.0 (含 specificity)$v$, true, $v$全对: y=[1,1,0,0] pred=[1,1,0,0] → 全部 1.0 (含 specificity)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_eval_all_wrong$v$, $v$全错: y=[1,1,0,0] pred=[0,0,1,1] → 全部 0.0$v$, true, $v$全错: y=[1,1,0,0] pred=[0,0,1,1] → 全部 0.0$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_eval_specific_confusion$v$, $v$y=[1,1,0,0,1] pred=[1,0,0,0,1] tp=2 fp=0 tn=2 fn=1 accuracy=4/5=0.8, precision=2/2=1.0, recall=2/3≈0.667 f1=2*1.0*(2/3)/(1.0+2/3)=4/3/(5/3)=4/5=0.8 specificity=2/(2+0)=1.0$v$, true, $v$y=[1,1,0,0,1] pred=[1,0,0,0,1] tp=2 fp=0 tn=2 fn=1 accuracy=4/5=0.8, precision=2/2=1.0, recall=2/3≈0.667 f1=2*1.0*(2/3)/(1.0+2/3)=4/3/(5/3)=4/5=0.8 specificity=2/(2+0)=1.0$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_eval_imbalanced_majority_pred$v$, $v$4:1 不平衡, 全猜 0: y=[1]*1+[0]*4 pred=[0]*5 → tp=0 fp=0 tn=4 fn=1 accuracy=4/5=0.8, precision=0 (除零), recall=0, f1=0, specificity=4/4=1.0$v$, true, $v$4:1 不平衡, 全猜 0: y=[1]*1+[0]*4 pred=[0]*5 → tp=0 fp=0 tn=4 fn=1 accuracy=4/5=0.8, precision=0 (除零), recall=0, f1=0, specificity=4/4=1.0$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_eval_specificity_distinguishes_imbalance$v$, $v$y=[0,0,0,0,1,1] pred=[0,0,1,1,1,1] tp=2 fp=2 tn=2 fn=0 accuracy=4/6≈0.667, precision=2/4=0.5, recall=2/2=1.0 f1=2*0.5*1/1.5=2/3, specificity=2/(2+2)=0.5$v$, true, $v$y=[0,0,0,0,1,1] pred=[0,0,1,1,1,1] tp=2 fp=2 tn=2 fn=0 accuracy=4/6≈0.667, precision=2/4=0.5, recall=2/2=1.0 f1=2*0.5*1/1.5=2/3, specificity=2/(2+2)=0.5$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_eval_raises_on_empty$v$, $v$eval raises on empty$v$, true, $v$eval raises on empty$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_eval_raises_on_length_mismatch$v$, $v$eval raises on length mismatch$v$, true, $v$eval raises on length mismatch$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_eval_raises_on_non_list$v$, $v$eval raises on non list$v$, true, $v$eval raises on non list$v$, NULL, 28)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
