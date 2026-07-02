-- BD8: HiveQL 查询与优化
-- practice_id=19, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        19,
        $v$HiveQL 查询与优化$v$,
        'PRACTICE',
        1,
        $v$intermediate$v$,
        $v$## HiveQL 查询执行模型

## 1.1 SQL 到分布式计算的翻译

HiveQL `SELECT ... FROM ... JOIN ... WHERE ... GROUP BY ...` 被 Hive 翻译为多阶段 MapReduce/Tez/Spark job:
- **WHERE**: filter, 通常下推到 storage 层 (减少 IO)
- **JOIN**: 跨表关联, 多种实现 (broadcast / shuffle / sort-merge)
- **GROUP BY**: 分组聚合, MR 的 reduce 阶段
- **ORDER BY**: 全局排序, 单 reducer 瓶颈

理解 SQL 的执行计划是 Hive 优化的基础。

## 1.2 分区剪枝 (复习 BD07)

WHERE 涉及分区列时, Hive 仅扫描相关分区。本关函数 `compute_partition_pruning_set(filter, available)` 返回**交集**: filter 中存在且在表实际分区中的分区列表 (升序)。

```
filter = ['2026-04-25', '2026-04-26', '2026-04-30']
available = ['2026-04-25', '2026-04-26', '2026-04-27', '2026-04-28']
intersection = ['2026-04-25', '2026-04-26']  # 实际扫描这 2 个
```

工程实务: 良好的 WHERE 让 99% 查询只扫 1 个分区。

## 1.3 查询代价估算

简化模型 (本关 estimate_query_cost):

$\text{cost} = \text{rows\_scanned} \cdot (\text{num\_joins} + 1)$

含义: 1 次扫描的代价是 rows; 每多 1 个 join, 因为 shuffle 数据膨胀, 代价加倍。

工程实务: 真实代价模型 (Hive CBO) 用统计信息 (基数估计 / 列基数), 但简化模型足以教学。


## Join 策略与 distinct

## 2.1 三种主流 join

Hive 实现 join 有三种策略:
- **Shuffle join (Reduce-side join)**: 两表 shuffle 到同一 reducer, 通用但慢
- **Map-side join (Broadcast join)**: 小表广播到所有 mapper, 大表本地 join, 极快但要求小表能进内存
- **Sort-Merge Bucket (SMB) join**: 两表预先按 key 排序+分桶, 直接合并, 极优但要求建表时配置

## 2.2 Broadcast join 的判定

给定两表大小 (左 left_rows, 右 right_rows), 阈值 broadcast_threshold:
- 若 min(left, right) < threshold → broadcast (小表广播)
- 否则 → shuffle (常规 reduce join)

工程实务: Hive 默认 broadcast_threshold = 25 MB (`hive.mapjoin.smalltable.filesize`)。本关用行数代替字节, 阈值默认 1,000,000 行。

## 2.3 distinct 计数

`SELECT COUNT(DISTINCT user_id) FROM events`: 计数不同值的数量。

简化实现 (本关): `len(set(values))`。

工程实务: 大数据 distinct count 是难题:
- 精确: 全局 shuffle, 内存压力大
- 近似: HyperLogLog (10x 快, 1% 误差)
- 预聚合: 按维度提前算好

本关用精确 set 实现, HLL 是进阶专题。


## 业务案例与工程口诀

## 3.1 业务案例: 大表 Join 优化

场景: 订单表 (1 亿行) JOIN 用户主数据 (500 万行) by user_id:

优化决策:
1. **broadcast join 判定** (本关 should_use_broadcast_join): 用户表 500 万 < 1000 万阈值? Hive 默认 25 MB 大约 50 万行, 所以本关 1M 阈值偏宽松, 假设过 → 选 broadcast
2. **分区剪枝** (本关 compute_partition_pruning_set): 订单 WHERE order_date 在 [...] 中 → 仅扫描相关分区
3. **查询代价** (本关 estimate_query_cost): 假设扫 1000 万行 + 1 个 join → cost = 10M × 2 = 20M
4. **distinct 用户** (本关 count_distinct_simple): GROUP BY user_id COUNT(DISTINCT...)

原查询全扫描 + shuffle join: 30 分钟 → 优化后 partition prune + broadcast: 3 分钟 (10x 提升)。

## 3.2 工程口诀

- **WHERE 必命中分区**: 否则全表扫描
- **小表 < 25 MB → broadcast**: Hive 默认开启
- **JOIN 数越多代价越高**: 减少不必要的 join
- **大数据 distinct 用 HLL**: 99% 场景近似就够
- **EXPLAIN 看执行计划**: 优化前必看

## 3.3 现代趋势

Hive 逐渐被 Spark SQL / Presto / ClickHouse 替代:
- Spark SQL: 内存优化, 查询快 5-50x
- Presto: 交互式低延迟 (秒级)
- ClickHouse: 实时分析 (毫秒级聚合)

但 SQL 优化思想 (分区剪枝 / join 选择 / 代价估算) 在所有 OLAP 系统中通用。

$v$,
        $v${"questions": [{"id": "q08-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd08.py 中的 4 个函数; 评测以 test_bd08.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_pps_overlap_2$v$, $v$filter=[a,b,c], avail=[b,c,d] → [b, c]$v$, false, $v$filter=[a,b,c], avail=[b,c,d] → [b, c]$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_pps_no_overlap$v$, $v$无交集 → []$v$, false, $v$无交集 → []$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_pps_all_in_filter$v$, $v$filter ⊂ available → filter (升序)$v$, false, $v$filter ⊂ available → filter (升序)$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_pps_dedup_filter$v$, $v$filter 含重复 → 输出去重$v$, false, $v$filter 含重复 → 输出去重$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_pps_dates$v$, $v$日期分区交集$v$, false, $v$日期分区交集$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_pps_raises_on_non_list$v$, $v$pps raises on non list$v$, false, $v$pps raises on non list$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_cost_no_join$v$, $v$1000 行, 0 join → 1000$v$, false, $v$1000 行, 0 join → 1000$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_cost_one_join$v$, $v$1000 行, 1 join → 2000$v$, false, $v$1000 行, 1 join → 2000$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_cost_three_joins$v$, $v$500 行, 3 join → 500 × 4 = 2000$v$, false, $v$500 行, 3 join → 500 × 4 = 2000$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_cost_large$v$, $v$1M 行 1 join → 2M$v$, false, $v$1M 行 1 join → 2M$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_cost_raises_on_negative_rows$v$, $v$cost raises on negative rows$v$, false, $v$cost raises on negative rows$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_cost_raises_on_negative_joins$v$, $v$cost raises on negative joins$v$, false, $v$cost raises on negative joins$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_cost_raises_on_non_int$v$, $v$cost raises on non int$v$, true, $v$cost raises on non int$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_bcast_right_small$v$, $v$左 10M, 右 1000 → broadcast$v$, true, $v$左 10M, 右 1000 → broadcast$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_bcast_both_large$v$, $v$左 5M, 右 10M → shuffle$v$, true, $v$左 5M, 右 10M → shuffle$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_bcast_at_threshold$v$, $v$1M == threshold → shuffle (严格 <)$v$, true, $v$1M == threshold → shuffle (严格 <)$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_bcast_custom_threshold$v$, $v$threshold=100, 左 50 → broadcast$v$, true, $v$threshold=100, 左 50 → broadcast$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_bcast_raises_on_zero$v$, $v$bcast raises on zero$v$, true, $v$bcast raises on zero$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_bcast_raises_on_non_int$v$, $v$bcast raises on non int$v$, true, $v$bcast raises on non int$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_dist_typical$v$, $v$[1, 2, 3, 2, 1] → 3$v$, true, $v$[1, 2, 3, 2, 1] → 3$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_dist_all_same$v$, $v$[1, 1, 1] → 1$v$, true, $v$[1, 1, 1] → 1$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_dist_strings$v$, $v$['a', 'b', 'a', 'c'] → 3$v$, true, $v$['a', 'b', 'a', 'c'] → 3$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_dist_empty$v$, $v$[] → 0 (boundary)$v$, true, $v$[] → 0 (boundary)$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_dist_raises_on_non_list$v$, $v$dist raises on non list$v$, true, $v$dist raises on non list$v$, NULL, 24)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
