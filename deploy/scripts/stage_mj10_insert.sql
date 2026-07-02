-- ============================================================
-- MJ10: 模型评估与优化
-- practice_id=7, order_in_practice=10
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$模型评估与优化$v$,
        'PRACTICE',
        10,
        $v$intermediate$v$,
        $v$## 为什么需要交叉验证

## 1.1 单一 train/test 划分的问题

MJ03 用 train_test_split 把数据 80/20 划分, 在测试集上评估。这是入门做法, 但在三种场景下不可靠:

- **样本量小** (< 1000 条): 测试集 200 条, 不同的随机划分可能让分数浮动 5%-10%, 调参时无法判断改动是否真的有效
- **类别不平衡**: 随机划分可能让小类完全跑到训练集或测试集, 评估失真
- **调参时**: 每次调参都看测试集分数, 等于在测试集上"间接训练", 测试集的代表性被消耗

解决思路: **K 折交叉验证** (K-Fold Cross Validation)。

## 1.2 K 折交叉验证的统计原理

把数据分成 K 等份, 每次用 K-1 份训练 + 1 份测试, 循环 K 次得到 K 个分数, 报告 mean ± std。常见 K=5 或 K=10。

优点:
- 每个样本恰好测试 1 次, 训练 K-1 次 — 数据利用率高
- K 个分数的标准差给出"模型稳定性"信号
- 不依赖单一划分

## 1.3 分层 K 折 (Stratified K-Fold)

普通 K 折随机划分时, 类别比例可能在某个 fold 出现偏移。**分层 K 折** 在每个 fold 内强制保持原始类别比例:

原始数据: 80% 类 0 / 20% 类 1, K=5.
普通 K 折: 某个 fold 可能 65% : 35%, 另一个 95% : 5%.
分层 K 折: 每个 fold 都精确 80% : 20% (允许 ±1 个样本误差).

分类问题默认用分层 K 折, 是 sklearn StratifiedKFold 的标准做法。


## Bootstrap 重采样

## 2.1 思想

Bootstrap = 对一份大小为 N 的数据集, 进行 **有放回** 随机抽样 N 次, 得到一份新的"重采样数据集"。每次抽样独立, 因此同一个原始样本可能被抽到 0 次、1 次、2 次, 甚至更多。

## 2.2 关键性质

- **重复**: 一个 5 元素数据集做 size=10 的 bootstrap, 必然出现重复 — 5 个原始值占 10 个位置, 平均每值出现 2 次
- **OOB**: 平均约 36.8% 的原始样本在一次 bootstrap 中**没被抽到** (出现 0 次)。这部分被称为 Out-Of-Bag, 可以作为天然的验证集
- **确定性**: 给定 random_state (随机种子), bootstrap 输出完全确定 — 这是工程复现性的基础

## 2.3 Bootstrap 在不同场景

- **置信区间估计**: 对统计量 (mean / median / 比率) 做 1000 次 bootstrap, 得到分布 → 取 2.5% 与 97.5% 分位数 = 95% 置信区间
- **集成学习的基础**: 随机森林 (MJ05) 每棵树的训练数据就是 bootstrap 来的
- **Bagging 的"Bootstrap Aggregating"中"Bootstrap"部分**

## 2.4 工程提醒

- **种子要固定**: 每次实验用不同 random_state 应该相互独立, 但同一次实验复现时种子要一致
- **size 不一定等于 N**: 学术上多用 size=N, 工程上为了速度 size=N/2 也常见
- **bootstrap 不能凭空产生信息**: 它是从已有数据"重新洗牌", 不能解决数据本身样本量不足


## 网格搜索与学习曲线

## 3.1 网格搜索 (GridSearch) 调参

给定一组超参的候选值, 穷举所有组合, 在每个组合上用 K 折 CV 评估, 取最优组合。

例: 决策树调参网格 (来自 MJ04):
```
max_depth ∈ {3, 5, 7, 10}
min_samples_leaf ∈ {1, 5, 10, 20}
```
共 4 × 4 = 16 个组合, 每个跑 K 折, 总 16 × K 次训练。

规模警告: 6 个参数 × 5 取值 = $5^6 = 15625$ 组合, 是常见的"调参陷阱"。实务上:
- 先对最关键 1-2 个参数粗调
- 找到大致区间后再精调
- 极端高维参数空间用随机搜索 (RandomizedSearchCV)

## 3.2 学习曲线 (Learning Curve)

横轴: 训练样本数 (从 10% 到 100%)
纵轴: 训练分数 与 验证分数 (在每个数据量下重复 K 次得到均值与标准差)

四种典型形态:

| 形态 | 训练 | 验证 | 诊断 | 建议 |
|------|------|------|------|------|
| A | 高且平 | 低且平 | 高方差/过拟合 | 增加数据/正则化/简化模型 |
| B | 低且平 | 低且平 | 高偏差/欠拟合 | 增加特征/复杂模型/调参 |
| C | 训练 ↘ 趋于稳, 验证 ↗ 趋稳, gap 小 | | 拟合恰当 | 不需要再调 |
| D | 训练高, 验证高方差 | | 数据规模不足 | 加数据后再判断 |

学习曲线的产出比单一分数更有诊断价值 — 它告诉你"问题在数据量、还是在模型容量"。


## 业务案例: 信贷风控调参

## 4.1 场景

银行风控部用决策树训了一版违约预测模型, 单划分测试集 AUC=0.78, 业务方质疑"这个数字稳吗"。

## 4.2 走完一遍

**步 1 引入 5 折 CV**: 同样模型同样数据, 5 折 CV AUC = 0.76 ± 0.04 (标准差 0.04 偏大, 说明模型对划分敏感)。说明单划分 0.78 偏乐观。

**步 2 学习曲线诊断**: 训练分数 0.95+ 持续高位, 验证分数 0.76 持平 — 典型形态 A (高方差/过拟合)。决定加正则化或剪枝。

**步 3 GridSearch 调参**:
```
max_depth ∈ {3, 5, 7, 10, None}
min_samples_leaf ∈ {5, 10, 20, 50}
```
20 个组合 × 5 折 = 100 次训练。最优: max_depth=7, min_samples_leaf=20, 5 折 AUC = 0.81 ± 0.02 (mean 上升, std 下降, 同时改善偏差与方差)。

**步 4 Bootstrap 给置信区间**: 对最终模型, 用 1000 次 bootstrap 估计 AUC 分布, 95% 置信区间 [0.78, 0.84]。这给业务方"模型上线后真实表现的合理预期范围"。

**步 5 上线**: 把调好的模型部署, 用同样的 K 折 + bootstrap 框架做月度回评, 如果新月度的 AUC 跌出原 95% 区间, 触发模型漂移告警。

## 4.3 常见陷阱

- **K 太小**: K=3 会让方差估计不可靠; K=5 或 10 是经验最佳
- **K 太大**: K=20+ 训练成本陡增, 但方差降幅有限, 性价比低
- **CV 期间不能 fit 标准化器** (data leakage): 每折内独立 fit_transform
- **GridSearch 嵌套层数**: 同时调 6 个参数 × 5 取值 = $5^6$, 穷举不切实际, 改随机搜索
- **报"测试集分数"误导**: 一定要附 std 或置信区间, 单点数字会让业务方过度乐观

$v$,
        $v${"questions": [{"id": "q10-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj10.py 中的 4 个函数; 评测以 test_mj10.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_kf_balanced_4fold$v$, $v$y=[0]*4+[1]*4 n_splits=4: 每折测试集 train+test=8, 类比例 1:1$v$, false, $v$y=[0]*4+[1]*4 n_splits=4: 每折测试集 train+test=8, 类比例 1:1$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_kf_three_fold_balanced$v$, $v$y=[0]*6+[1]*6 n_splits=3: 每折 test 含 2 of class 0 + 2 of class 1$v$, false, $v$y=[0]*6+[1]*6 n_splits=3: 每折 test 含 2 of class 0 + 2 of class 1$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_kf_imbalanced_2_to_1$v$, $v$y=[0]*8+[1]*4 n_splits=4: 每折 test 含 2 of class 0 + 1 of class 1$v$, false, $v$y=[0]*8+[1]*4 n_splits=4: 每折 test 含 2 of class 0 + 1 of class 1$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_kf_disjoint_test_sets$v$, $v$所有 fold 的 test 集合两两互斥$v$, false, $v$所有 fold 的 test 集合两两互斥$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_kf_2fold_4samples$v$, $v$y=[0,0,1,1] n_splits=2: 每折 test 含 1 of class 0 + 1 of class 1$v$, false, $v$y=[0,0,1,1] n_splits=2: 每折 test 含 1 of class 0 + 1 of class 1$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_kf_raises_on_too_many_splits$v$, $v$n_splits > 某类样本数 → ValueError$v$, false, $v$n_splits > 某类样本数 → ValueError$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_kf_raises_on_empty$v$, $v$kf raises on empty$v$, false, $v$kf raises on empty$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_kf_raises_on_non_list$v$, $v$kf raises on non list$v$, false, $v$kf raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_bs_has_repeat$v$, $v$input 5 个 unique 值, bootstrap n=10 必含重复$v$, false, $v$input 5 个 unique 值, bootstrap n=10 必含重复$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_bs_deterministic_seeds_differ$v$, $v$同 seed 完全相同, 不同 seed 应有差异 (防 D 攻击 identity 不依赖 seed)$v$, false, $v$同 seed 完全相同, 不同 seed 应有差异 (防 D 攻击 identity 不依赖 seed)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_bs_single_element$v$, $v$[42] 任何 n 都是 [42]*n$v$, false, $v$[42] 任何 n 都是 [42]*n$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_bs_n_larger_than_input$v$, $v$n=6 > 输入 size=3, 必含重复$v$, false, $v$n=6 > 输入 size=3, 必含重复$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_bs_size_double_input$v$, $v$input size=2, n=8 (D identity 长度不匹配)$v$, false, $v$input size=2, n=8 (D identity 长度不匹配)$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_bs_raises_on_empty$v$, $v$bs raises on empty$v$, false, $v$bs raises on empty$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_bs_raises_on_negative_n$v$, $v$bs raises on negative n$v$, false, $v$bs raises on negative n$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_bs_raises_on_non_list$v$, $v$bs raises on non list$v$, true, $v$bs raises on non list$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_acvs_three_scores$v$, $v$[0.8, 0.85, 0.9] mean=0.85, min=0.8, max=0.9, std=sqrt(2/3)*0.05 ≈ 0.0408$v$, true, $v$[0.8, 0.85, 0.9] mean=0.85, min=0.8, max=0.9, std=sqrt(2/3)*0.05 ≈ 0.0408$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_acvs_perfect$v$, $v$[1.0]*5 全 1.0, std=0$v$, true, $v$[1.0]*5 全 1.0, std=0$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_acvs_diverse$v$, $v$[0.5, 0.7, 0.6, 0.8] mean=0.65, min=0.5, max=0.8$v$, true, $v$[0.5, 0.7, 0.6, 0.8] mean=0.65, min=0.5, max=0.8$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_acvs_negative$v$, $v$[-0.1, 0.5] mean=0.2, min=-0.1, max=0.5 (含负值, R² 可负)$v$, true, $v$[-0.1, 0.5] mean=0.2, min=-0.1, max=0.5 (含负值, R² 可负)$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_acvs_single$v$, $v$[0.7] mean=min=max=0.7, std=0$v$, true, $v$[0.7] mean=min=max=0.7, std=0$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_acvs_raises_on_empty$v$, $v$acvs raises on empty$v$, true, $v$acvs raises on empty$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_acvs_raises_on_non_list$v$, $v$acvs raises on non list$v$, true, $v$acvs raises on non list$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_lcm_basic$v$, $v$train_scores=[[0.9,0.95],[0.85,0.9]], val_scores=[[0.8,0.82],[0.78,0.82]] train_mean=[0.925, 0.875], val_mean=[0.81, 0.80]$v$, true, $v$train_scores=[[0.9,0.95],[0.85,0.9]], val_scores=[[0.8,0.82],[0.78,0.82]] train_mean=[0.925, 0.875], val_mean=[0.81, 0.80]$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_lcm_constant$v$, $v$全相同分数 → std=0, mean=该值$v$, true, $v$全相同分数 → std=0, mean=该值$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_lcm_three_sizes$v$, $v$3 个数据量, 每个 2 重复$v$, true, $v$3 个数据量, 每个 2 重复$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_lcm_single_size$v$, $v$1 个数据量 1 重复 → 单值, std=0$v$, true, $v$1 个数据量 1 重复 → 单值, std=0$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_lcm_raises_on_empty$v$, $v$lcm raises on empty$v$, true, $v$lcm raises on empty$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_lcm_raises_on_shape_mismatch$v$, $v$lcm raises on shape mismatch$v$, true, $v$lcm raises on shape mismatch$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_lcm_raises_on_non_list$v$, $v$lcm raises on non list$v$, true, $v$lcm raises on non list$v$, NULL, 30)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
