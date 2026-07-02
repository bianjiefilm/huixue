-- ============================================================
-- MJ5: 监督学习: 分类进阶
-- practice_id=7, order_in_practice=5
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$监督学习: 分类进阶$v$,
        'PRACTICE',
        5,
        $v$intermediate$v$,
        $v$## 从单模型到集成

## 1.1 单模型的局限

逻辑回归只能学线性分隔, 单棵决策树容易过拟合 — 单一模型无论调多少超参, 都有结构上的天花板。集成学习 (ensemble) 通过组合多个基础模型的预测来突破天花板, 思想朴素但效果惊人: **多个独立模型的错误大概率不重叠, 投票或加权能消除大部分错误**。

集成有两条主线:
- **Bagging** (Bootstrap Aggregating): 对训练集随机重采样, 得到 K 个不同的子集, 每个训练一个基础模型, 预测时投票。代表算法: 随机森林 (RF)。
- **Boosting**: 串行训练, 每棵新树专门修正前面树的错误。代表算法: 梯度提升 (XGBoost / LightGBM)。

Bagging 降方差 (减少模型对训练集变化的敏感), Boosting 降偏差 (减少模型表达力的不足) — 这是两个方向的工程互补。

## 1.2 SVM: 最大间隔分类器

SVM (Support Vector Machine) 是 Bagging/Boosting 出现前的"分类强者", 现在仍在小样本+高维场景占有一席之地。核心思想是找一个超平面, 让两类样本到超平面的距离 (间隔) 最大化:

- 距离最大的超平面对噪声最鲁棒
- 边界附近的少数样本 (支持向量) 决定了超平面位置
- 通过核函数 (kernel) 把数据隐式映射到高维, 处理非线性可分

SVM 对特征量纲敏感, 必须先标准化 (复习 MJ03)。本关只要求理解概念, 不实现 SVM 训练。


## Bagging 与随机森林

## 2.1 Bagging 的两层随机

Bagging 在两个维度上引入随机性:
- **行抽样 (Bootstrap)**: 每棵树训练时, 从 N 个样本中**有放回**抽 N 个 — 平均约 63% 的原始样本被抽到, 其余 37% 作为该树的 OOB (Out-Of-Bag) 验证集
- **列抽样**: 每次分裂时, 从全部 d 个特征中随机选 $\sqrt{d}$ (分类) 或 $d/3$ (其它任务) 个候选, 在候选中找最佳分裂

两层随机让每棵树都见到不同视角, 投票时错误倾向不一致, 综合下来更稳。

## 2.2 多数表决与平票处理

K 棵树对一个样本各给一个标签, 综合策略:
- **硬投票**: 直接看哪个标签出现次数最多
- **软投票**: 看每棵树输出的概率均值

硬投票的边界: K 是偶数且恰好票数对半时, 这是平票 (tie)。常见处理规则:
- 选**编号最小**的类 (确定性, 易复现)
- 选**类的先验最大**的那个 (考虑训练集类别分布)
- 随机选 (不推荐, 复现性差)

本关约定: 平票时返回**编号最小**的类。

## 2.3 特征重要性

RF 训练完每棵树后, 可以统计每个特征被用于分裂的次数 (或带权 — 按分裂带来的不纯度下降加权)。把这些计数**归一化为和等于 1 的比例**, 得到该特征对模型的相对重要性。

重要性的业务用法:
- 特征筛选: 重要性接近 0 的特征基本是噪声, 可考虑下次建模剔除
- 业务洞察: 重要性最高的几个特征往往是业务上的关键变量
- 特征工程方向: 围绕高重要性特征做交互或非线性变换


## Boosting 与 XGBoost 残差思想

## 3.1 Boosting 的串行思路

Bagging 是"群策群力" — K 棵树独立训练, 投票综合。Boosting 是"逐步修正":
- 第 1 棵树先粗糙拟合数据, 得到初步预测 $\hat{y}^{(1)}$
- 第 2 棵树专门拟合"上一轮的错误" — 即真值与上一轮预测之差
- 第 t 棵树拟合 $r^{(t)} = y - \hat{y}^{(t-1)}$, 这就是**残差**

最终预测是所有树的累加: $\hat{y} = \sum_t \eta \cdot \hat{y}^{(t)}$, 其中 $\eta$ 是学习率 (步长)。

## 3.2 残差的本质

残差不是单纯的"误差差值" — 它是当前模型还没学会的部分。每多加一棵新树, 就把"还没学会"的那部分往前推一步。这种"逐步把错变对"的过程, 让 Boosting 在偏差降低上能力极强 — 同样数据, 一棵 RF 树可能 76% accuracy, 100 棵 XGBoost 树叠加能到 88%。

代价: 训练只能串行 (每棵依赖前一棵), 不像 Bagging 可以并行。

## 3.3 XGBoost 的常见超参

| 参数 | 含义 | 调优范围 |
|------|------|----------|
| n_estimators | 树的数量 | 100-1000 |
| max_depth | 树深 | 3-10 |
| learning_rate | 学习率 $\eta$ | 0.01-0.3 |
| subsample | 行抽样比 | 0.6-1.0 |
| colsample_bytree | 列抽样比 | 0.6-1.0 |

调优口诀: **learning_rate 和 n_estimators 反向调** — 学习率小一倍, 树数大一倍, 总预算相同但泛化更稳; subsample/colsample 同时小可以再加一层随机性, 进一步降过拟合。

具体调参方法 (网格搜索/随机搜索) 在后续课程介绍。


## Gini 不纯度与业务案例

## 4.1 Gini 不纯度公式

$\text{Gini}(S) = 1 - \sum_{c} p_c^2$

其中 $p_c$ 是类别 $c$ 在节点 $S$ 中的占比。直觉: Gini 衡量"从 S 中随机选两个样本类别不同的概率"。

关键值:
- 单类纯净: Gini = 0
- 二分类均衡 [0,0,1,1]: Gini = 1 - (0.5² + 0.5²) = 0.5 (二分类最大值)
- 三类均衡: Gini = 1 - 3·(1/3)² = 2/3 ≈ 0.667
- 四类均衡: Gini = 0.75
- K 类均衡: Gini = 1 - 1/K, 极限 = 1

Gini 越小越纯, 决策树分裂的目标就是让加权子节点 Gini 最小。

## 4.2 业务案例: 信贷风控特征重要性

银行用 RF 训练违约预测模型, 100 棵树训完, 7 个特征的分裂使用计数:

| 特征 | 使用次数 |
|------|----------|
| tenure (在网时长) | 380 |
| past_default (历史违约次数) | 320 |
| income (月收入) | 180 |
| age (年龄) | 60 |
| education (学历) | 35 |
| gender (性别) | 18 |
| marital_status (婚姻状况) | 7 |

归一化 (除以总和 1000): tenure 0.38, past_default 0.32, income 0.18, age 0.06, education 0.035, gender 0.018, marital 0.007。

业务解读:
- tenure + past_default 占总重要性 70%, 是核心风控信号
- gender 与 marital_status 重要性极低 (< 2%), 应该剔除 — 一方面合规 (反歧视), 一方面噪声
- education 0.035 是边缘特征, 下次建模时可以试试是否剔除后表现稳定
- 这给 BD/产品的反馈: 策略上重点服务长 tenure 用户, 严管 past_default 高的用户

重要性分析的产出不是"该用哪个模型", 而是"业务上哪些信号最值得关注"。

## 4.3 集成模型的代价

集成的好处明显, 但也有代价:
- 模型可解释性下降 (单棵 DT 可读, 100 棵 RF 不可读)
- 推理时间变长 (100 棵树都要预测一遍)
- 内存占用变高
- 调参复杂度上升

工程实务: 业务对解释性强需求 (金融、医疗) 时优先单棵决策树或 SHAP 工具辅助 RF; 业务追求性能且可解释性可妥协 (推荐、广告) 时优先 XGBoost。

$v$,
        $v${"questions": [{"id": "q05-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj05.py 中的 4 个函数; 评测以 test_mj05.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_mv_simple_binary$v$, $v$[[1,0,0],[0,1,1],[1,0,0]] 各行 row[0] 故意与多数不一致 → [0, 1, 0]$v$, false, $v$[[1,0,0],[0,1,1],[1,0,0]] 各行 row[0] 故意与多数不一致 → [0, 1, 0]$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_mv_tie_smaller$v$, $v$[[1,0,0,1]] 平票 tie_break='smaller' → [0] (row[0]=1 与结果不一致)$v$, false, $v$[[1,0,0,1]] 平票 tie_break='smaller' → [0] (row[0]=1 与结果不一致)$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_mv_three_classes$v$, $v$[[0,1,2,2,2]] 类 2 多数 → [2]; row[0]=0 ≠ 2$v$, false, $v$[[0,1,2,2,2]] 类 2 多数 → [2]; row[0]=0 ≠ 2$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_mv_first_disagrees$v$, $v$[[1,0,0,0]] row[0]=1 但多数 0 → [0]$v$, false, $v$[[1,0,0,0]] row[0]=1 但多数 0 → [0]$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_mv_first_is_minority$v$, $v$[[2,1,1,1,1]] row[0]=2 是少数, 多数 1 → [1]$v$, false, $v$[[2,1,1,1,1]] row[0]=2 是少数, 多数 1 → [1]$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_mv_raises_on_empty_outer$v$, $v$边界: 外层空 → ValueError$v$, false, $v$边界: 外层空 → ValueError$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_mv_raises_on_empty_inner$v$, $v$边界: 内层空 → ValueError$v$, false, $v$边界: 内层空 → ValueError$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_mv_raises_on_non_list$v$, $v$负例: 非 list → TypeError$v$, false, $v$负例: 非 list → TypeError$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_fi_basic$v$, $v$[10, 5, 5] → [0.5, 0.25, 0.25]$v$, false, $v$[10, 5, 5] → [0.5, 0.25, 0.25]$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_fi_uniform$v$, $v$[1,1,1,1] → [0.25]*4$v$, false, $v$[1,1,1,1] → [0.25]*4$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_fi_all_one_feature$v$, $v$[100, 0, 0] → [1.0, 0.0, 0.0]$v$, false, $v$[100, 0, 0] → [1.0, 0.0, 0.0]$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_fi_proportional$v$, $v$[2, 4, 6, 8] → [0.1, 0.2, 0.3, 0.4]$v$, false, $v$[2, 4, 6, 8] → [0.1, 0.2, 0.3, 0.4]$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_fi_raises_on_all_zero$v$, $v$边界: 全 0 → ValueError$v$, false, $v$边界: 全 0 → ValueError$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_fi_raises_on_empty$v$, $v$fi raises on empty$v$, false, $v$fi raises on empty$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_fi_raises_on_negative$v$, $v$fi raises on negative$v$, false, $v$fi raises on negative$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_fi_raises_on_non_list$v$, $v$fi raises on non list$v$, false, $v$fi raises on non list$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_gini_pure$v$, $v$单类 → 0.0$v$, true, $v$单类 → 0.0$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_gini_balanced_binary$v$, $v$[0,0,1,1] → 0.5$v$, true, $v$[0,0,1,1] → 0.5$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_gini_three_one$v$, $v$[0,0,0,1] p0=0.75 p1=0.25 → 1 - 0.5625 - 0.0625 = 0.375$v$, true, $v$[0,0,0,1] p0=0.75 p1=0.25 → 1 - 0.5625 - 0.0625 = 0.375$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_gini_three_classes_equal$v$, $v$[0,1,2] → 1 - 3*(1/3)^2 = 2/3$v$, true, $v$[0,1,2] → 1 - 3*(1/3)^2 = 2/3$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_gini_four_classes_equal$v$, $v$[0,1,2,3] → 1 - 4*0.25^2 = 0.75$v$, true, $v$[0,1,2,3] → 1 - 4*0.25^2 = 0.75$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_gini_unbalanced$v$, $v$[0,0,0,1,1] p0=0.6 p1=0.4 → 1 - 0.36 - 0.16 = 0.48$v$, true, $v$[0,0,0,1,1] p0=0.6 p1=0.4 → 1 - 0.36 - 0.16 = 0.48$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_gini_raises_on_empty$v$, $v$gini raises on empty$v$, true, $v$gini raises on empty$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_gini_raises_on_non_list$v$, $v$gini raises on non list$v$, true, $v$gini raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_residual_perfect_fit$v$, $v$[1,2,3], [1,2,3] → [0,0,0]$v$, true, $v$[1,2,3], [1,2,3] → [0,0,0]$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_residual_constant_diff$v$, $v$[10,20,30], [5,15,25] → [5,5,5]$v$, true, $v$[10,20,30], [5,15,25] → [5,5,5]$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_residual_signed$v$, $v$[1,2,3], [3,2,1] → [-2, 0, 2]$v$, true, $v$[1,2,3], [3,2,1] → [-2, 0, 2]$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_residual_floats$v$, $v$[1.5, 2.5], [1.0, 2.0] → [0.5, 0.5]$v$, true, $v$[1.5, 2.5], [1.0, 2.0] → [0.5, 0.5]$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_residual_y_pred_zeros$v$, $v$[5,7,11], [0,0,0] → [5,7,11] (boundary: pred 全 0, residual = y_true)$v$, true, $v$[5,7,11], [0,0,0] → [5,7,11] (boundary: pred 全 0, residual = y_true)$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_residual_raises_on_length_mismatch$v$, $v$residual raises on length mismatch$v$, true, $v$residual raises on length mismatch$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_residual_raises_on_empty$v$, $v$residual raises on empty$v$, true, $v$residual raises on empty$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_residual_raises_on_non_list$v$, $v$residual raises on non list$v$, true, $v$residual raises on non list$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
