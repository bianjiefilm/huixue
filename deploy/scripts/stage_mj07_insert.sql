-- ============================================================
-- MJ7: 无监督学习: 聚类
-- practice_id=7, order_in_practice=7
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$无监督学习: 聚类$v$,
        'PRACTICE',
        7,
        $v$intermediate$v$,
        $v$## 聚类的位置与基本概念

## 1.1 无监督学习的特点

监督学习 (MJ04-06) 有 (输入, 标签) 对作为训练信号; 无监督学习只有输入, 没有标签 — 任务变成"在没有正确答案的情况下找数据的内在结构"。无监督学习不是"弱化版监督学习", 它解决的是不同类型的问题:

- 监督: 给定历史数据预测未来标签
- 无监督: 探索数据本身, 发现自然分组、典型形态、异常点

聚类 (Clustering) 是无监督学习的代表任务: **把样本分成若干组, 使组内相似度高、组间相似度低**。

## 1.2 相似度的定义

聚类的核心是"相似度", 而相似度依赖于距离度量。最常用的是**欧氏距离**:

$d(\mathbf{x}_i, \mathbf{x}_j) = \sqrt{\sum_{k=1}^{d} (x_{ik} - x_{jk})^2}$

欧氏距离假设所有特征量纲一致、地位相等。如果特征量纲差异大, 必须先标准化 (复习 MJ03 的 z-score), 否则距离会被高量纲特征主导, 聚类结果失真。

其他距离: 曼哈顿距离 (L1), 余弦相似度 (角度), 马氏距离 (考虑协方差) — 不同业务用不同度量, 但本关聚焦欧氏距离 + K-Means。


## K-Means 的两步迭代

## 2.1 算法骨架

K-Means 是聚类的入门算法, 核心是两步循环:

1. **分配步骤**: 给定 K 个中心, 把每个样本分配给距离它最近的中心 (得到簇标签)
2. **更新步骤**: 给定簇标签, 把每个簇的中心更新为该簇所有样本的均值 (重新得到 K 个中心)

重复以上两步, 直到中心不再移动 (或达到迭代上限)。算法保证 inertia (簇内平方和) 单调下降, 但不一定收敛到全局最优 — 不同初始中心会得到不同结果。

## 2.2 簇内平方和 (Inertia)

给定每个样本的标签和簇中心, 模型质量用 inertia 衡量:

$\text{Inertia} = \sum_{i=1}^{N} \| \mathbf{x}_i - \boldsymbol{\mu}_{c_i} \|^2$

其中 $c_i$ 是样本 $i$ 的簇标签, $\boldsymbol{\mu}_{c_i}$ 是该簇中心。inertia 越小, 簇内越紧凑。

## 2.3 K 值的选择 (肘部法)

K-Means 不能自动决定簇数 K, 需要外部指定。**肘部法**: 对 K=2,3,4,...,10 分别跑算法, 画 inertia vs K 曲线 — 曲线下降速度变缓的"拐点" 通常是合理的 K 值。

工程提醒: 肘部法只是参考, 业务上 K 的选择应该结合业务可解释性。比如客户分群, 业务团队最多管 5-7 个分层, 即使数学上 K=12 inertia 更低, 也应限制在 5-7 之内。


## K-Means 的限制与 DBSCAN / 层次聚类

## 3.1 K-Means 的工程局限

- **必须先指定 K**: 业务真实分组数未知时, K 的选择是难题
- **对初始中心敏感**: 不同初始化得到不同结果 (实务通常用 K-Means++ 等启发式初始化)
- **假设簇是凸的**: 月牙形、嵌套环形分布会被错分
- **对异常值敏感**: 一个极端样本会把它所在簇的中心拉偏

## 3.2 DBSCAN: 基于密度的聚类

DBSCAN 不预设 K, 用两个超参 (邻域半径 ε 与最小样本数 minPts) 自动发现密度足够的"核心区域", 把孤立点标记为噪声 (-1)。优势:
- 自动发现簇数
- 能发现任意形状簇 (月牙、环形)
- 自动检测异常点

代价: 对高维数据效果差 (距离度量在高维下失效); ε 难选。

## 3.3 层次聚类

层次聚类 (Agglomerative / Divisive) 不需要指定 K, 而是构造一棵聚类树 (dendrogram), 用户可以根据树的剪枝高度来选不同粒度的分组。优势是可视化直观、灵活; 代价是 O(N²) 内存、O(N³) 时间, 大数据无法用。

## 3.4 三种聚类的取舍

| 算法 | 何时用 |
|------|--------|
| K-Means | 数据量大、维度中等、簇数大致已知 |
| DBSCAN | 簇形状复杂、需要异常检测、维度低 |
| 层次聚类 | 数据量小、需要灵活分层、需要可视化 |


## 业务案例: 电商客户分群

## 4.1 场景

电商运营拿到 50 万活跃用户的 RFM 数据 (Recency 最近购买距今天数, Frequency 90 天内购买频次, Monetary 90 天累计消费金额), 想做客户分群指导差异化运营。

## 4.2 走完聚类全流程

**步 1 标准化**: RFM 三个特征量纲完全不同 (R 是天数 [1,90], F 是次数 [1,30], M 是金额 [10,5000])。z-score 标准化后再做距离, 否则金额特征会完全主导。

**步 2 选 K**: 跑 K=2..10 的 K-Means, inertia 在 K=4 后下降变缓 — 肘部明显在 4。业务团队接受 K=4 (4 个分群正好匹配运营策略层级)。

**步 3 训练 + 结果**: K=4 跑完得到 4 个簇:
- **簇 A** (R 小、F 高、M 高): "VIP 高频" — 最近购买、频繁、高客单, 占用户 5%, 贡献 GMV 的 60%
- **簇 B** (R 大、F 低、M 中): "流失风险" — 很久没买、过去消费一般, 占 30%, 是召回重点
- **簇 C** (R 小、F 低、M 低): "新客试探" — 最近第一次买, 还在观察期, 占 25%, 需要次单激活
- **簇 D** (R 中、F 中、M 中): "稳定主力" — 中等指标全维度, 占 40%, 是基本盘

**步 4 业务行动**:
- VIP 高频: 推 1v1 客户经理 + 高端会员权益
- 流失风险: 折扣召回券 + 精准品类推送
- 新客试探: 次单优惠 + 新人专享
- 稳定主力: 维持当前节奏, 不打扰

## 4.3 核心提醒

聚类结果好坏不光看 inertia 与轮廓系数 — 业务可解释性是更高优先级:
- 簇的特征要能用业务语言描述 (例: "VIP 高频" 而不是"簇 0")
- 簇的规模要适中 (1-2 个超大簇 + 几个小簇 通常意味着 K 选错)
- 同一簇里的样本业务行为要一致, 不同簇之间要有可执行差异

聚类不是终点, 是业务运营策略分层的起点。

$v$,
        $v${"questions": [{"id": "q07-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj07.py 中的 4 个函数; 评测以 test_mj07.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_ed_three_four_five$v$, $v$[0,0], [3,4] → 5.0$v$, false, $v$[0,0], [3,4] → 5.0$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_ed_one_d$v$, $v$[0], [7] → 7.0$v$, false, $v$[0], [7] → 7.0$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_ed_zero$v$, $v$同点 → 0.0$v$, false, $v$同点 → 0.0$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_ed_three_d$v$, $v$[1,2,3], [4,6,8] → sqrt(9+16+25) = sqrt(50)$v$, false, $v$[1,2,3], [4,6,8] → sqrt(9+16+25) = sqrt(50)$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_ed_negative$v$, $v$[-1,-1], [1,1] → sqrt(8)$v$, false, $v$[-1,-1], [1,1] → sqrt(8)$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_ed_raises_on_empty$v$, $v$ed raises on empty$v$, false, $v$ed raises on empty$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_ed_raises_on_length_mismatch$v$, $v$ed raises on length mismatch$v$, false, $v$ed raises on length mismatch$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_ed_raises_on_non_list$v$, $v$ed raises on non list$v$, false, $v$ed raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_ac_two_clear_clusters$v$, $v$两明显分离簇 [0,0],[1,1] vs [10,10],[11,11], centroids=[[0,0],[10,10]] → [0,0,1,1]$v$, false, $v$两明显分离簇 [0,0],[1,1] vs [10,10],[11,11], centroids=[[0,0],[10,10]] → [0,0,1,1]$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_ac_three_clusters_permuted$v$, $v$centroids 顺序与样本最近顺序错开, expected [1,0,2] 而非 [0,1,2] (防 D 攻击 list(range(n)) 巧合)$v$, false, $v$centroids 顺序与样本最近顺序错开, expected [1,0,2] 而非 [0,1,2] (防 D 攻击 list(range(n)) 巧合)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_ac_mixed_assignment$v$, $v$[3,3], [4,4] 分别更靠近 [0,0] 与 [10,10]$v$, false, $v$[3,3], [4,4] 分别更靠近 [0,0] 与 [10,10]$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_ac_tie_smaller_index$v$, $v$两样本同距两 centroid, 平票取小索引 → [0,0] (而非 D 的 [0,1])$v$, false, $v$两样本同距两 centroid, 平票取小索引 → [0,0] (而非 D 的 [0,1])$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_ac_single_centroid$v$, $v$k=1, 全分配到簇 0 → [0,0,0]$v$, false, $v$k=1, 全分配到簇 0 → [0,0,0]$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_ac_raises_on_empty_X$v$, $v$ac raises on empty X$v$, false, $v$ac raises on empty X$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_ac_raises_on_empty_centroids$v$, $v$ac raises on empty centroids$v$, false, $v$ac raises on empty centroids$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_ac_raises_on_non_list$v$, $v$ac raises on non list$v$, false, $v$ac raises on non list$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_uc_two_clusters$v$, $v$X=[[0,0],[2,0],[10,10],[12,10]] labels=[0,0,1,1] k=2 → [[1,0],[11,10]]$v$, true, $v$X=[[0,0],[2,0],[10,10],[12,10]] labels=[0,0,1,1] k=2 → [[1,0],[11,10]]$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_uc_three_clusters$v$, $v$X=[[1],[2],[5],[6],[100]] labels=[0,0,1,1,2] k=3 → [[1.5],[5.5],[100]]$v$, true, $v$X=[[1],[2],[5],[6],[100]] labels=[0,0,1,1,2] k=3 → [[1.5],[5.5],[100]]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_uc_single_cluster$v$, $v$全在簇 0 → 中心是均值$v$, true, $v$全在簇 0 → 中心是均值$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_uc_empty_cluster_zeros$v$, $v$labels 都是 0, k=2 → 簇 1 空, 用 0 占位$v$, true, $v$labels 都是 0, k=2 → 簇 1 空, 用 0 占位$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_uc_negative_values$v$, $v$X=[[-1,-2],[1,2]] labels=[0,0] k=1 → [[0,0]]$v$, true, $v$X=[[-1,-2],[1,2]] labels=[0,0] k=1 → [[0,0]]$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_uc_raises_on_empty_X$v$, $v$uc raises on empty X$v$, true, $v$uc raises on empty X$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_uc_raises_on_length_mismatch$v$, $v$uc raises on length mismatch$v$, true, $v$uc raises on length mismatch$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_uc_raises_on_non_list$v$, $v$uc raises on non list$v$, true, $v$uc raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_ci_well_clustered$v$, $v$X=[[0,0],[2,0],[10,10],[12,10]] labels=[0,0,1,1] centroids=[[1,0],[11,10]] inertia = 1+1+1+1 = 4$v$, true, $v$X=[[0,0],[2,0],[10,10],[12,10]] labels=[0,0,1,1] centroids=[[1,0],[11,10]] inertia = 1+1+1+1 = 4$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_ci_perfect_centers$v$, $v$sample == centroid → inertia=0$v$, true, $v$sample == centroid → inertia=0$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_ci_single_cluster$v$, $v$[[0,0],[3,4]] labels=[0,0] centroid=[[0,0]] → 0+25 = 25$v$, true, $v$[[0,0],[3,4]] labels=[0,0] centroid=[[0,0]] → 0+25 = 25$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_ci_three_clusters$v$, $v$X=[[0],[1],[10],[11],[20]] labels=[0,0,1,1,2] centroids=[[0.5],[10.5],[20]] inertia = 0.25+0.25+0.25+0.25+0 = 1.0$v$, true, $v$X=[[0],[1],[10],[11],[20]] labels=[0,0,1,1,2] centroids=[[0.5],[10.5],[20]] inertia = 0.25+0.25+0.25+0.25+0 = 1.0$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_ci_far_centers$v$, $v$X=[[0,0]] labels=[0] centroid=[[3,4]] → 25$v$, true, $v$X=[[0,0]] labels=[0] centroid=[[3,4]] → 25$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_ci_raises_on_empty$v$, $v$ci raises on empty$v$, true, $v$ci raises on empty$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_ci_raises_on_label_out_of_range$v$, $v$labels 含越界值$v$, true, $v$labels 含越界值$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_ci_raises_on_non_list$v$, $v$ci raises on non list$v$, true, $v$ci raises on non list$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
