-- BD10: Sqoop 数据迁移工具
-- practice_id=21, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        21,
        $v$Sqoop 数据迁移工具$v$,
        'PRACTICE',
        1,
        $v$intermediate$v$,
        $v$## Sqoop 与异构数据迁移

## 1.1 Sqoop 是什么

Sqoop (SQL-to-Hadoop) 是关系数据库 (MySQL/Oracle/PostgreSQL) 与 Hadoop (HDFS/Hive/HBase) 之间的批量迁移工具:
- **import**: RDBMS → Hadoop (常用)
- **export**: Hadoop → RDBMS (回写报表结果)

为什么需要专用工具? 普通 SQL 单连接 + 单 process 太慢, 千万行表迁移要数小时。Sqoop 用并行 mapper + JDBC 大批量提交。

## 1.2 并行迁移分片

Sqoop 把表按 split 列切成多个分片, 每个 mapper 处理一片。给定表大小 S (MB) 与 mapper 数 M:

$\text{split\_size} = \lceil S / M \rceil \text{ MB}$

工程实务: 默认 4 mapper, 大表可调到 16-32。Sqoop 用 split 列的 min/max 等距划分, 不一定均匀 (受数据分布影响)。

## 1.3 split 列选型

split 列必须满足:
- **高基数 (cardinality)**: 不同值多, 才能均分
- **数值类型 (优先)**: 易于均分 (min/max/range)
- **有索引**: 否则 min/max 查询慢

简化策略 (本关 select_split_column_strategy):
- 输入: 高基数列数 (能用作 split 的候选数)
- 若 >= 1 → 'numeric_pk' (用主键或唯一数值列)
- 若 == 0 → 'manual' (用 --split-by 指定特殊列, 或 --num-mappers 1 单 mapper)

工程实务: 95% 表能用主键 split, 没主键的表 (如纯日志) 走 manual。


## 增量导入与时间估算

## 2.1 增量导入 (Incremental Import)

首次全量导入后, 后续只导入新增数据 (增量), 节省 I/O:

```
sqoop import --incremental append --check-column id --last-value 1000000
```

含义: 只导入 id > 1000000 的行。

合法性 (本关 is_incremental_import_valid):
- current_max > last_value → True (有新数据可导)
- current_max <= last_value → False (无新数据 / last_value 已是最新)

## 2.2 迁移时间估算

迁移耗时 = rows / 吞吐 (rows/sec)。

$\text{time\_seconds} = \text{rows} / \text{rows\_per\_sec}$

经验吞吐 (本关默认 rows_per_sec = 10000):
- 简单表 (无大字段): 50000 rows/sec
- 普通表: 10000 rows/sec
- 大字段表 (含 BLOB / 大文本): 1000 rows/sec

工程实务: 1 亿行业务表迁移 ~ 10000 秒 ≈ 3 小时, 通常凌晨低峰跑。

## 2.3 增量策略对比

Sqoop 支持两种增量模式:
- **append**: 适用于"只插入不修改"的表 (日志类), check-column 是自增 ID
- **lastmodified**: 适用于"会更新"的表, check-column 是更新时间 (modified_at)

工程实务: 选错策略会丢数据 (用 append 处理可更新表会漏掉更新的旧行)。


## 业务案例与工程口诀

## 3.1 业务案例: MySQL 订单表 → Hive

场景: MySQL 订单表 1 亿行 (100 GB), 每天有 100 万新订单, 同步到 Hive 数仓:

迁移流水线:
1. **首次全量**:
   - **split 列选型** (本关 select_split_column_strategy): 主键 order_id 高基数 → numeric_pk
   - **分片大小** (本关 compute_split_size): 100 GB / 16 mapper ≈ 6.25 GB/mapper
   - **时间估算** (本关 compute_migration_time_seconds): 1亿行 / 10000 = 10000 秒 ≈ 3 小时
2. **每日增量**:
   - **last_value 校验** (本关 is_incremental_import_valid): 每日 cron 检查 max(order_id) > 上次 last_value
   - **导入新订单**: 100 万 / 10000 = 100 秒
3. **全量周校准**: 每周凌晨重做全量, 防止增量丢数据

## 3.2 工程口诀

- **首次全量, 后续增量**: 节省 90% I/O
- **--num-mappers 4-16**: 看表大小调
- **split 列必有索引**: 否则 min/max 查询慢
- **append vs lastmodified 选对**: 错了丢数据
- **凌晨低峰跑**: 不影响业务

## 3.3 现代替代

Sqoop 在新项目逐渐被替代:
- **Flink CDC**: 实时增量, 流式同步
- **DataX (阿里)**: 异构数据源大全
- **Debezium**: 基于 binlog 的 CDC
- **AWS DMS / 阿里 DTS**: 托管迁移

但 Sqoop 概念 (并行 split / 增量 / split 列选型) 在所有 ETL 工具中通用。

$v$,
        $v${"questions": [{"id": "q10-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd10.py 中的 4 个函数; 评测以 test_bd10.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_split_typical$v$, $v$100 GB / 16 → ceil(100*1024/16) = 6400 MB$v$, false, $v$100 GB / 16 → ceil(100*1024/16) = 6400 MB$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_split_partial_ceil$v$, $v$100 / 3 → 34 (ceil 33.33)$v$, false, $v$100 / 3 → 34 (ceil 33.33)$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_split_default_mappers$v$, $v$1000 / 4 → 250$v$, false, $v$1000 / 4 → 250$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_split_small_table$v$, $v$10 MB / 4 → 3 (ceil 2.5)$v$, false, $v$10 MB / 4 → 3 (ceil 2.5)$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_split_raises_on_zero_mappers$v$, $v$split raises on zero mappers$v$, false, $v$split raises on zero mappers$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_split_raises_on_zero_table$v$, $v$split raises on zero table$v$, false, $v$split raises on zero table$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_split_raises_on_non_int$v$, $v$split raises on non int$v$, false, $v$split raises on non int$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_inc_valid$v$, $v$1500 > 1000 → True$v$, false, $v$1500 > 1000 → True$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_inc_no_new$v$, $v$current == last → False$v$, false, $v$current == last → False$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_inc_decreased$v$, $v$current < last → False$v$, false, $v$current < last → False$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_inc_raises_on_negative$v$, $v$inc raises on negative$v$, false, $v$inc raises on negative$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_inc_raises_on_non_int$v$, $v$inc raises on non int$v$, true, $v$inc raises on non int$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_mig_1m_default$v$, $v$1M / 10000 = 100 秒$v$, true, $v$1M / 10000 = 100 秒$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_mig_partial$v$, $v$1500 / 10000 = 0.15$v$, true, $v$1500 / 10000 = 0.15$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_mig_custom_throughput$v$, $v$100000 / 50000 = 2$v$, true, $v$100000 / 50000 = 2$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_mig_zero_rows$v$, $v$0 行 → 0 秒$v$, true, $v$0 行 → 0 秒$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_mig_large$v$, $v$1 亿 / 10000 = 10000$v$, true, $v$1 亿 / 10000 = 10000$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_mig_raises_on_zero_throughput$v$, $v$mig raises on zero throughput$v$, true, $v$mig raises on zero throughput$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_mig_raises_on_non_int$v$, $v$mig raises on non int$v$, true, $v$mig raises on non int$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_sel_one_col$v$, $v$sel one col$v$, true, $v$sel one col$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_sel_no_cols$v$, $v$sel no cols$v$, true, $v$sel no cols$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_sel_raises_on_negative$v$, $v$sel raises on negative$v$, true, $v$sel raises on negative$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_sel_raises_on_non_int$v$, $v$sel raises on non int$v$, true, $v$sel raises on non int$v$, NULL, 23)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
