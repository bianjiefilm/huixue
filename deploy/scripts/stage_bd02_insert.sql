-- BD2: HDFS 分布式文件系统
-- practice_id=13, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        13,
        $v$HDFS 分布式文件系统$v$,
        'PRACTICE',
        1,
        $v$beginner$v$,
        $v$## HDFS 的核心设计

## 1.1 为什么需要 HDFS

传统单机文件系统 (ext4 / NTFS) 的局限:
- **容量上限**: 单盘 20 TB, 单机 ≤ 200 TB
- **吞吐瓶颈**: 单机磁盘读写 ≤ 1 GB/s
- **可靠性**: 单点故障 = 数据丢失

HDFS (Hadoop Distributed File System) 解决方案:
- **分块存储**: 文件切成固定大小 block, 分散到多节点
- **副本机制**: 每个 block 复制 N 份 (默认 3) 到不同节点
- **元数据集中**: NameNode 维护文件→block→节点的索引

## 1.2 Block 切片机制

HDFS 把文件切成固定大小的 block, 默认 **128 MB** (Hadoop 2.x+, 旧版本 64 MB)。

给定文件大小 F (字节), block 大小 B:
- block 数 = $\lceil F / B \rceil$ (向上取整)
- 最后一个 block 不补齐, 实际大小可能 < B

例: F = 300 MB, B = 128 MB → ⌈300/128⌉ = 3 blocks (128 + 128 + 44 MB)。

为什么 block 这么大 (128 MB)?
- 单 block 内顺序读优势, 寻道开销可忽略
- 减少 NameNode 元数据条目数 (后续讨论)
- MapReduce 调度粒度匹配 (一个 block 一个 map task)

## 1.3 副本与存储占用

副本因子 R (默认 3) 决定每个 block 复制几份。实际存储:

$\text{实际存储} = F \cdot R$

例: F = 300 MB, R = 3 → 900 MB 实际占用。

工程实务: 1 PB 业务数据 + R=3 → 3 PB 实际存储, 这是规划集群容量的基础 (复习 BD01)。


## Block 大小与元数据规模

## 2.1 Block 大小的合法性

HDFS block 大小不是任意值, 实际约束:
- **最小**: 1 MB (太小元数据膨胀)
- **最大**: 1 GB (太大单 block 失效代价高)
- **必须是 2 的幂**: 工程惯例 (64MB, 128MB, 256MB, 512MB, 1GB)

工程实务: 默认 128 MB 适配 99% 场景, 大文件 (4K 视频) 可调到 256 MB / 512 MB; 小文件多 (日志) 不应改 block_size, 应该用 SequenceFile 或 HAR 合并。

## 2.2 NameNode 元数据规模

NameNode 维护所有文件/目录/block 的元数据 (索引), 全部存内存。

经验估算 (本关用): 每个文件平均占用 **~150 字节** NameNode 内存 (含文件名 / 权限 / 时间戳 / block 列表)。

$\text{NameNode 内存 (字节)} = \text{文件数} \cdot 150$

例: 1000 万文件 → 1.5 GB 内存。1 亿文件 → 15 GB (NameNode 单机内存常见上限)。

## 2.3 小文件问题

如果文件大量小于 block_size (例: 1 MB 日志文件), 问题:
- **NameNode 内存压力**: 文件数多 = 元数据多
- **MapReduce 浪费**: 一个文件至少一个 map, 启动开销 > 处理开销
- **磁盘碎片**: 小 block 占用一个完整 block 槽位 (128 MB 容量)

解决方案 (BD05 复习): SequenceFile 合并 / HAR (Hadoop Archive) / 业务层批量。


## 业务案例与工程口诀

## 3.1 业务案例: 日志归档存储规划

场景: 公司每天产生 10 TB 日志, 保留 90 天, 用 HDFS 归档:

规划步骤:
1. **总数据量** (本关 compute_cluster_node_count 复习 BD01): 10 TB × 90 天 = 900 TB 业务数据
2. **副本存储** (本关 compute_storage_with_replication): 900 TB × 3 = 2700 TB
3. **平均文件大小**: 假设按小时切, 1 文件/小时 × 24 × 90 × 10 服务 = 21600 文件
4. **NameNode 内存** (本关 compute_namenode_metadata_size): 21600 × 150 = 3.24 MB (足够小)
5. **block_size 选择** (本关 is_block_size_valid): 默认 128 MB 合适 (日志文件平均 GB 级)
6. **block 数** (本关 compute_hdfs_block_count): 总 = 900 TB / 128 MB ≈ 7M blocks

## 3.2 工程口诀

- **默认 block 128 MB**: 不要随便改
- **副本默认 3**: 重要数据可调 5, 临时数据 2
- **小文件是 NameNode 杀手**: 必须合并
- **NameNode 内存 ~150 字节/文件**: 估算容量必记
- **block 大小必须 2 的幂**: 64/128/256 MB

## 3.3 HDFS 与对象存储 (S3) 的对比

现代云原生倾向用 S3 / OSS 替代 HDFS:
- S3: 无 NameNode 瓶颈, 11 个 9 持久性, 按需付费
- HDFS: 计算与存储紧耦合, 适合迭代计算 (MapReduce)

但 HDFS 概念 (block / replication / NameNode) 仍是分布式文件系统的"经典模型", 学习它是大数据工程师必修。

$v$,
        $v${"questions": [{"id": "q02-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd02.py 中的 4 个函数; 评测以 test_bd02.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_block_300mb$v$, $v$300 MB / 128 MB → ceil(300/128) = 3$v$, false, $v$300 MB / 128 MB → ceil(300/128) = 3$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_block_just_over$v$, $v$129 MB / 128 MB → 2$v$, false, $v$129 MB / 128 MB → 2$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_block_default_blocksize$v$, $v$default 128 MB$v$, false, $v$default 128 MB$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_block_custom_64mb$v$, $v$300 MB / 64 MB → 5$v$, false, $v$300 MB / 64 MB → 5$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_block_zero_file$v$, $v$0 文件 → 0 block (boundary)$v$, false, $v$0 文件 → 0 block (boundary)$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_block_raises_on_zero_blocksize$v$, $v$block raises on zero blocksize$v$, false, $v$block raises on zero blocksize$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_block_raises_on_negative_filesize$v$, $v$block raises on negative filesize$v$, false, $v$block raises on negative filesize$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_block_raises_on_non_int$v$, $v$block raises on non int$v$, false, $v$block raises on non int$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_storage_default$v$, $v$100 MB × 3 = 300 MB$v$, false, $v$100 MB × 3 = 300 MB$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_storage_replication_1$v$, $v$100 × 1 = 100$v$, false, $v$100 × 1 = 100$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_storage_replication_5$v$, $v$100 × 5 = 500$v$, false, $v$100 × 5 = 500$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_storage_large_file$v$, $v$1 GB × 3 = 3 GB$v$, false, $v$1 GB × 3 = 3 GB$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_storage_raises_on_negative_replication$v$, $v$storage raises on negative replication$v$, false, $v$storage raises on negative replication$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_storage_raises_on_non_int$v$, $v$storage raises on non int$v$, true, $v$storage raises on non int$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_block_size_64mb_valid$v$, $v$1 个 True 测试 (默认推荐值)$v$, true, $v$1 个 True 测试 (默认推荐值)$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_block_size_too_small$v$, $v$< 1 MB$v$, true, $v$< 1 MB$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_block_size_too_big$v$, $v$> 1 GB$v$, true, $v$> 1 GB$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_block_size_not_power_of_2$v$, $v$100 MB 不是 2 的幂$v$, true, $v$100 MB 不是 2 的幂$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_block_size_raises_on_non_int$v$, $v$block size raises on non int$v$, true, $v$block size raises on non int$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_meta_one_million$v$, $v$100 万 × 150 = 1.5 亿字节$v$, true, $v$100 万 × 150 = 1.5 亿字节$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_meta_100_files$v$, $v$100 × 150 = 15000$v$, true, $v$100 × 150 = 15000$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_meta_custom_bytes$v$, $v$100 × 200 = 20000$v$, true, $v$100 × 200 = 20000$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_meta_zero_files$v$, $v$0 → 0 (boundary)$v$, true, $v$0 → 0 (boundary)$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_meta_default_bytes$v$, $v$default 150$v$, true, $v$default 150$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_meta_raises_on_negative_files$v$, $v$meta raises on negative files$v$, true, $v$meta raises on negative files$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_meta_raises_on_zero_bytes$v$, $v$meta raises on zero bytes$v$, true, $v$meta raises on zero bytes$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_meta_raises_on_non_int$v$, $v$meta raises on non int$v$, true, $v$meta raises on non int$v$, NULL, 27)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
