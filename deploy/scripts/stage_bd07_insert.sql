-- BD7: Hive 数据仓库基础
-- practice_id=18, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        18,
        $v$Hive 数据仓库基础$v$,
        'PRACTICE',
        1,
        $v$intermediate$v$,
        $v$## Hive 与数据仓库设计

## 1.1 Hive 是什么

Hive (2010-) 是基于 Hadoop 的数据仓库:
- **SQL 接口**: HiveQL 类 SQL 语法, 把 SQL 翻译成 MapReduce / Tez / Spark job
- **存储**: 数据存 HDFS (复习 BD02-03)
- **元数据**: Metastore (MySQL/PostgreSQL) 维护表 schema / 分区信息

为什么需要 Hive: SQL 是数据分析的通用语言, 数据工程师不可能都写 MapReduce Java 代码 (复习 BD05)。Hive 让 SQL 用户也能查询大数据。

## 1.2 分区 (Partitioning)

分区是 Hive 性能的灵魂。原理: 把表按字段 (常按时间) 切成多个子目录。

例: orders 表按 order_date 分区, HDFS 目录:
```
/hive/orders/order_date=2026-04-25/
/hive/orders/order_date=2026-04-26/
...
```

给定总行数 R 与单分区目标行数 P:

$\text{partition\_count} = \lceil R / P \rceil$

工程实务: 单分区 100 万行 - 1 亿行是常见目标 (太小: 元数据膨胀; 太大: 扫描慢)。

## 1.3 分区剪枝 (Partition Pruning)

查询 `WHERE order_date = '2026-04-25'` 时, Hive 只扫描该分区目录, 跳过其他, 称为 partition pruning。

剪枝有效性: 查询涉及分区数 / 总分区数 < threshold。

简化判定 (本关 is_partition_pruning_helpful, threshold=0.5):
- 查询 < 50% 分区 → 有效 (跳过 > 50% 数据)
- 查询 ≥ 50% 分区 → 无效 (差不多全表扫)

工程实务: 良好的分区设计能让 99% 的查询只扫 1 个分区, 性能提升 100x+。


## 存储估算与格式选型

## 2.1 数据仓库存储估算

给定原始数据大小 S (GB), 副本因子 R, 压缩率 c (压缩后/原始):

$\text{warehouse\_size} = S \cdot R \cdot c$

压缩率经验值:
- **TextFile**: c = 1.0 (不压缩) 或 0.3 (gzip)
- **ORC**: c = 0.2 (内置高效压缩)
- **Parquet**: c = 0.25

例: 1 TB 原始日志, R=3, ORC 压缩 → 1 × 3 × 0.2 = 0.6 TB 实际占用。

工程实务: 副本占用是固定 (HDFS), 压缩是可选, 但生产几乎都开启压缩 (节省 5-10x 存储 + 提升查询性能因为 IO 是瓶颈)。

## 2.2 三种主流存储格式

Hive 支持多种存储格式, 三种最常用:

**TextFile**:
- 优: 兼容性好 (普通文本), 易于查看
- 劣: 无压缩, 全文件扫描慢
- 用途: 日志原始数据 / 临时表 / 与外部系统兼容

**Parquet** (Apache Parquet):
- 优: 列存, 跨引擎兼容 (Spark / Presto / Impala)
- 劣: 压缩率不如 ORC
- 用途: 跨引擎数据交换

**ORC** (Optimized Row Columnar):
- 优: 列存, Hive 原生最优, 压缩率高 + 索引快
- 劣: 主要 Hive 生态用
- 用途: 大表 / 分析查询 / Hive only

简化选型 (本关 get_hive_storage_format):
- 'analytical' (分析查询) → 'orc'
- 'compatibility' (跨引擎) → 'parquet'
- 'simple' (临时 / 兼容) → 'textfile'

## 2.3 列存 vs 行存

为什么列存对分析快? 分析查询通常只用少数列 (`SELECT user_id, amount FROM orders`), 列存只读这两列, 跳过其他列, IO 减少 5-50x。

行存适合 OLTP (一行多字段全用), 列存适合 OLAP (聚合分析)。


## 业务案例与工程口诀

## 3.1 业务案例: 电商日志数仓

场景: 电商平台日产 10 GB 订单日志, 90 天保留, 业务分析:

数仓设计:
1. **总行数估算** (本关 compute_partition_count): 100 GB × 90 天 / 单分区 1 GB → 9000 partitions, 太多
2. **重新设计**: 按 day 分区 → 90 partitions ✓
3. **存储格式** (本关 get_hive_storage_format): analytical → ORC
4. **存储估算** (本关 compute_data_warehouse_size): 9 TB × 3 × 0.2 = 5.4 TB
5. **查询模式**: 90% 查询 WHERE order_date = X (本关 is_partition_pruning_helpful: 1/90 < 0.5 → 剪枝有效)

## 3.2 工程口诀

- **分区按时间**: day / month / year, 兼顾粒度与查询模式
- **单分区 100 万-1 亿行**: 太小元数据多, 太大扫描慢
- **存储用 ORC**: 分析最优, 没特殊要求都用
- **跨引擎用 Parquet**: 兼容性
- **永远开启压缩**: 节省 5-10x 存储

## 3.3 Hive 与现代

Hive 老牌但仍在用:
- 互联网公司大数据仓库标配 (字节 / 阿里 / 美团)
- 替代品: Spark SQL (内存快) / Presto (交互式) / ClickHouse (实时分析)

但 Hive 概念 (分区 / 列存 / 数据仓库) 是所有 OLAP 系统的基础, 学习 Hive 等于学习"数仓思维"。

$v$,
        $v${"questions": [{"id": "q07-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd07.py 中的 4 个函数; 评测以 test_bd07.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_part_typical$v$, $v$100M 行 / 1M 每分区 → 100$v$, false, $v$100M 行 / 1M 每分区 → 100$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_part_partial_ceil$v$, $v$1.5M / 1M → 2 (ceil)$v$, false, $v$1.5M / 1M → 2 (ceil)$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_part_just_one$v$, $v$500K / 1M → 1$v$, false, $v$500K / 1M → 1$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_part_zero_rows$v$, $v$boundary: 0 行 → 0$v$, false, $v$boundary: 0 行 → 0$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_part_exact$v$, $v$3M / 1M → 3$v$, false, $v$3M / 1M → 3$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_part_raises_on_zero_per_partition$v$, $v$part raises on zero per partition$v$, false, $v$part raises on zero per partition$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_part_raises_on_non_int$v$, $v$part raises on non int$v$, false, $v$part raises on non int$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_prune_helpful_1_of_90$v$, $v$1/90 < 0.5 → True$v$, false, $v$1/90 < 0.5 → True$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_prune_not_helpful_60_of_90$v$, $v$60/90 = 0.66 > 0.5 → False$v$, false, $v$60/90 = 0.66 > 0.5 → False$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_prune_at_threshold$v$, $v$45/90 = 0.5 == threshold → False (严格 <)$v$, false, $v$45/90 = 0.5 == threshold → False (严格 <)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_prune_custom_threshold_03$v$, $v$20/100 = 0.2 < 0.3 → True$v$, false, $v$20/100 = 0.2 < 0.3 → True$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_prune_raises_on_zero_total$v$, $v$prune raises on zero total$v$, false, $v$prune raises on zero total$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_dw_default_orc$v$, $v$1000 × 3 × 0.2 = 600$v$, false, $v$1000 × 3 × 0.2 = 600$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_dw_no_compression$v$, $v$1000 × 3 × 1.0 = 3000$v$, true, $v$1000 × 3 × 1.0 = 3000$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_dw_replication_1$v$, $v$500 × 1 × 0.5 = 250$v$, true, $v$500 × 1 × 0.5 = 250$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_dw_zero_size$v$, $v$0 × * × * = 0$v$, true, $v$0 × * × * = 0$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_dw_decimal_compression$v$, $v$100 × 3 × 0.25 = 75$v$, true, $v$100 × 3 × 0.25 = 75$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_dw_raises_on_negative_size$v$, $v$dw raises on negative size$v$, true, $v$dw raises on negative size$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_dw_raises_on_zero_replication$v$, $v$dw raises on zero replication$v$, true, $v$dw raises on zero replication$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_dw_raises_on_zero_compression$v$, $v$dw raises on zero compression$v$, true, $v$dw raises on zero compression$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_format_analytical$v$, $v$format analytical$v$, true, $v$format analytical$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_format_compatibility$v$, $v$format compatibility$v$, true, $v$format compatibility$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_format_simple$v$, $v$format simple$v$, true, $v$format simple$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_format_raises_on_unknown$v$, $v$format raises on unknown$v$, true, $v$format raises on unknown$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_format_raises_on_empty$v$, $v$format raises on empty$v$, true, $v$format raises on empty$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_format_raises_on_non_string$v$, $v$format raises on non string$v$, true, $v$format raises on non string$v$, NULL, 26)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
