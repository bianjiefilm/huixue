-- BD9: HBase NoSQL 数据库
-- practice_id=20, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        20,
        $v$HBase NoSQL 数据库$v$,
        'PRACTICE',
        1,
        $v$intermediate$v$,
        $v$## HBase 与 NoSQL 数据模型

## 1.1 HBase 是什么

HBase (2008-) 是 Google BigTable 的开源实现, 大数据生态的列存 NoSQL:
- **存储**: HDFS (复习 BD02-03), 自动分片
- **数据模型**: row → column family → column → value, 多维稀疏
- **特点**: 支持随机读写 (HDFS 不支持), 强一致性, 横向扩展

与 Hive 区别:
- Hive: 数据仓库, SQL 接口, 全表扫描分析
- HBase: NoSQL, key-value 接口, 单 row 随机读写

## 1.2 Row Key: 设计的核心

HBase 的 row 按 row key 字典序存储, row key 设计直接决定性能:
- **range 查询**: 邻近 row key 物理相邻, 范围扫描快
- **热点**: 所有写入集中到 1 个 region (1 个机器), 性能瓶颈

经典模式: timestamp 做 row key → 写入永远在最新 region → 热点。

解决: **加盐 (salting)** — 给 row key 加随机/hash 前缀, 写入分散到多个 region。

## 1.3 加盐设计

简单加盐方案 (本关 design_row_key_with_salt):
- 输入: prefix (业务前缀, 如 "user"), timestamp (整数), salt_count (盐桶数)
- salt = timestamp % salt_count
- row key 格式: "{salt}-{prefix}-{timestamp}"

例: prefix="event", timestamp=1714003200, salt_count=4:
- salt = 1714003200 % 4 = 0
- row_key = "0-event-1714003200"

工程实务: salt_count 通常等于 region 数, 让写入均匀分布到所有 region。


## Region 容量与热点检测

## 2.1 Region: HBase 的分片单元

表按 row key 范围切成多个 region, 每个 region 由一台 RegionServer 服务。给定表大小 T 与单 region 目标大小 r (默认 10 GB):

$\text{region\_count} = \lceil T / r \rceil$

工程实务:
- region 太小 (< 1 GB): region 数过多, master 元数据膨胀
- region 太大 (> 50 GB): 单 region 故障恢复慢, hot region 难拆分
- 默认 10 GB 是经验最优

## 2.2 热点 row key 检测

生产环境定期统计 row key 前缀分布。给定前缀计数 dict 与总 row 数, 若**任一前缀** > total × threshold (默认 50%) → 存在热点。

简化逻辑 (本关 is_hot_row_key):
- 遍历每个前缀的 count
- 任一 count 超过 total × threshold → True (存在热点)
- 全部都不超过 → False

工程实务: 检测到热点 → (a) 加盐重新设计, (b) 拆分 region, (c) 热点缓存。

## 2.3 Region 拆分 (Split)

当某个 region > region_max_size (默认 10 GB), HBase 自动拆分:
- 找中间 row key
- 拆成两个 region
- 重新分配到 RegionServer

工程实务: 频繁 split 影响性能, 设计阶段 row key 加盐避免热点是更好做法。


## Block Cache 与业务案例

## 3.1 Block Cache 命中率

HBase RegionServer 维护内存 Block Cache, 缓存最近读取的 HFile block。

命中率:
$\text{hit\_rate} = \text{cache\_hits} / \text{total\_reads}$

简化实现 (本关 compute_block_cache_hit_rate)。

工程实务:
- hit_rate > 0.9: 缓存配置优秀
- 0.5-0.9: 正常工作
- < 0.5: 缓存太小或 row key 设计差 (随机读太多)

## 3.2 业务案例: 时序数据存储

场景: IoT 平台, 100 万设备, 每秒上报数据 1 条, 每天 86 亿条:

设计:
1. **Row key 加盐** (本关 design_row_key_with_salt): salt-device_id-timestamp, salt_count=16
2. **表规划**:
   - 日数据量: 86 亿 × 100 字节 = 800 GB
   - 90 天保留: 72 TB
3. **Region 数** (本关 compute_region_count): 72 TB / 10 GB = 7200 regions
4. **集群规模**: 100 RegionServer × 72 region/RS = 100 节点
5. **热点检测** (本关): 监控 device_id 前缀分布, > 50% 单设备 → 加盐有效防止
6. **缓存命中率** (本关 compute_block_cache_hit_rate): 目标 > 0.9, 监控

## 3.3 工程口诀

- **Row key 必加盐**: 防热点
- **Region 默认 10 GB**: 经验最优
- **Block cache > 90%**: 健康线
- **HBase ≠ MySQL**: 不要做关系型操作 (没有 join, 弱事务)
- **HBase 适合时序 / 用户画像 / 高写入**: 不适合分析查询

## 3.4 现代替代

HBase 在新项目较少用了:
- **Cassandra**: 多主架构, 分布式更彻底
- **TiKV / TiDB**: 强一致 + 分布式 SQL
- **DynamoDB**: AWS 托管 NoSQL
- **MongoDB**: 文档 NoSQL

但 HBase 概念 (row key 加盐 / region 拆分 / block cache) 在所有 LSM-tree NoSQL 中通用。

$v$,
        $v${"questions": [{"id": "q09-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd09.py 中的 4 个函数; 评测以 test_bd09.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_salt_typical$v$, $v$prefix='event', ts=1714003200, salt=4 → salt=0, '0-event-1714003200'$v$, false, $v$prefix='event', ts=1714003200, salt=4 → salt=0, '0-event-1714003200'$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_salt_with_remainder$v$, $v$ts=10, salt=4 → 10%4=2, '2-user-10'$v$, false, $v$ts=10, salt=4 → 10%4=2, '2-user-10'$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_salt_count_8$v$, $v$ts=15, salt=8 → 15%8=7$v$, false, $v$ts=15, salt=8 → 15%8=7$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_salt_zero_timestamp$v$, $v$ts=0 → salt=0$v$, false, $v$ts=0 → salt=0$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_salt_count_1$v$, $v$salt_count=1 → salt 总是 0$v$, false, $v$salt_count=1 → salt 总是 0$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_salt_raises_on_empty_prefix$v$, $v$salt raises on empty prefix$v$, false, $v$salt raises on empty prefix$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_salt_raises_on_zero_salt_count$v$, $v$salt raises on zero salt count$v$, false, $v$salt raises on zero salt count$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_salt_raises_on_non_string$v$, $v$salt raises on non string$v$, false, $v$salt raises on non string$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_region_typical$v$, $v$100 GB / 10 GB → 10$v$, false, $v$100 GB / 10 GB → 10$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_region_partial_ceil$v$, $v$15 GB / 10 GB → 2$v$, false, $v$15 GB / 10 GB → 2$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_region_custom_size$v$, $v$100 GB / 20 GB → 5$v$, false, $v$100 GB / 20 GB → 5$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_region_just_above_one$v$, $v$11 GB / 10 GB → 2$v$, false, $v$11 GB / 10 GB → 2$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_region_minimum$v$, $v$1 GB → 1 (boundary)$v$, false, $v$1 GB → 1 (boundary)$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_region_raises_on_zero$v$, $v$region raises on zero$v$, false, $v$region raises on zero$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_region_raises_on_zero_region_size$v$, $v$region raises on zero region size$v$, false, $v$region raises on zero region size$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_hot_yes$v$, $v${'a': 60, 'b': 30, 'c': 10} total=100, threshold=0.5: a=60>50 → True$v$, true, $v${'a': 60, 'b': 30, 'c': 10} total=100, threshold=0.5: a=60>50 → True$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_hot_no$v$, $v${'a': 30, 'b': 30, 'c': 40} total=100: 都 <= 50 → False$v$, true, $v${'a': 30, 'b': 30, 'c': 40} total=100: 都 <= 50 → False$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_hot_at_threshold$v$, $v$count == total * threshold → False (>, 严格)$v$, true, $v$count == total * threshold → False (>, 严格)$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_hot_just_above$v$, $v$count = 51, total=100 → True$v$, true, $v$count = 51, total=100 → True$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_hot_custom_threshold$v$, $v$threshold=0.3, {'a':40} total=100 → True$v$, true, $v$threshold=0.3, {'a':40} total=100 → True$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_hot_empty_dict$v$, $v$空 dict → False (no hot)$v$, true, $v$空 dict → False (no hot)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_hot_raises_on_zero_total$v$, $v$hot raises on zero total$v$, true, $v$hot raises on zero total$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_hot_raises_on_non_dict$v$, $v$hot raises on non dict$v$, true, $v$hot raises on non dict$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_hr_typical$v$, $v$900 / 1000 = 0.9$v$, true, $v$900 / 1000 = 0.9$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_hr_half$v$, $v$500 / 1000 = 0.5$v$, true, $v$500 / 1000 = 0.5$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_hr_perfect$v$, $v$100 / 100 = 1.0$v$, true, $v$100 / 100 = 1.0$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_hr_all_miss$v$, $v$100 / 100 reads but 0 hits → 0$v$, true, $v$100 / 100 reads but 0 hits → 0$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_hr_decimal$v$, $v$3 / 4 = 0.75$v$, true, $v$3 / 4 = 0.75$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_hr_raises_on_zero_reads$v$, $v$hr raises on zero reads$v$, true, $v$hr raises on zero reads$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_hr_raises_on_hits_gt_reads$v$, $v$hr raises on hits gt reads$v$, true, $v$hr raises on hits gt reads$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_hr_raises_on_non_int$v$, $v$hr raises on non int$v$, true, $v$hr raises on non int$v$, NULL, 31)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
