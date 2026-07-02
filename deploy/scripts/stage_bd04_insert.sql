-- BD4: MapReduce 分布式计算原理
-- practice_id=15, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        15,
        $v$MapReduce 分布式计算原理$v$,
        'PRACTICE',
        1,
        $v$intermediate$v$,
        $v$## MapReduce 计算模型

## 1.1 MapReduce 的两阶段

MapReduce 把大数据任务拆成两个阶段:
- **Map**: 输入分片 → 多个 mapper 并行处理 → 中间 key-value 对
- **Reduce**: 按 key 分组 → reducer 聚合 → 最终输出

经典例子 word_count:
- Map: 文档 → (word, 1) 对
- Shuffle: 同 word 聚到同 reducer
- Reduce: 求和 → (word, count)

## 1.2 Map 任务数计算

Map 任务数 = 输入数据切片 (split) 数。给定输入文件大小列表与 split_size:

$\text{map\_count} = \sum_i \lceil \text{file\_size}_i / \text{split\_size} \rceil$

工程实务: split_size 通常等于 HDFS block_size (复习 BD02), 默认 128 MB。这样每个 map 处理一个 block, 数据本地性最大化 (复习 BD03)。

## 1.3 Reduce 任务数计算

Reduce 数没有"自动"算法, 由用户配置或基于数据量估算:

$\text{reduce\_count} = \max(1, \lceil \text{data\_size} / \text{target\_per\_reduce} \rceil)$

经验默认 target_per_reduce = 1024 MB (1 GB), 即每个 reducer 处理约 1 GB shuffle 数据。

工程实务:
- 太少 (1 个 reduce): 单点瓶颈, 无并行
- 太多 (10000+): 启动开销 + 大量小输出文件 (NameNode 元数据压力, 复习 BD02)
- 目标: 每 reducer 处理 0.5-2 GB


## Partition 与 Combiner

## 2.1 哈希分区 (Hash Partitioner)

Shuffle 阶段, mapper 输出按 key 分到不同 reducer。默认策略 hash partition:

$\text{partition\_index} = \text{hash}(\text{key}) \mod \text{num\_reducers}$

Python 内置 `hash()` 是非确定性 (随机化, 防 DoS), 工程上必须用确定性 hash。本关用简化版 (字符串字符 ord 累加):

```
def deterministic_hash(s):
    return sum(ord(c) for c in s)
```

$\text{partition} = \text{sum}(\text{ord}(c) \text{ for } c \text{ in } \text{key}) \mod \text{num\_reducers}$

工程实务: 实际 Hadoop 用 MurmurHash3 (确定性 + 分布均匀)。

## 2.2 Combiner: Map 端预聚合

Reduce 前 shuffle 数据量 = mapper 总输出。如果先在 mapper 本地聚合 (combiner), 可大幅减少 shuffle 数据。

**关键: combiner 必须满足"结合律 + 交换律"**:
- **可用 combiner**: sum, max, min, count (这些满足代数律)
- **不可用**: avg (sum/count, 不能直接合并 partial avg), median, percentile, distinct count

工程实务: 对 sum/max/min/count, combiner 减少 shuffle 50-90%。avg 可以拆成 (sum, count) 两个 combiner 任务, 但需要业务代码改写。

## 2.3 数据倾斜 (Data Skew)

hash partition 的失败模式: key 分布不均, 某个 reducer 接收远多数据 → 拖慢整个 job。

例: 用户 ID 中 99% 是 "guest_user" → reducer "guest" 处理 99% 数据。

解决:
- **加盐 (salt)**: key 加随机后缀, 多个 reducer 处理同一逻辑 key
- **自定义 partitioner**: 根据 key 分布优化分区
- **二阶段聚合**: 先粗聚合再细聚合

本关聚焦基础 hash partition, 倾斜处理是进阶。


## 业务案例与工程口诀

## 3.1 业务案例: 网站日志 word count

场景: 每天 100 GB 的网站日志, 统计每个 URL 被访问次数:

流水线:
1. **输入**: 100 GB 日志, HDFS block_size=128 MB
2. **Map 任务数** (本关): ceil(100GB / 128MB) ≈ 800 maps
3. **Combiner**: 每个 mapper 内先 word_count 聚合 (本关 is_combinable_operation 判定 'sum' 可 combine)
4. **Hash partition** (本关): 所有 (URL, count) 对按 hash(URL) % num_reducers 分
5. **Reduce 任务数** (本关): 假设 shuffle 后约 5 GB, target=1GB → 5 reducers
6. **输出**: 5 个 part-XXXXX 文件, 每个含一部分 URL 的总计数

## 3.2 工程口诀

- **Map 数 = 输入切片数**: 自动计算, 无需配置
- **Reduce 数 = ceil(data / 1GB)**: 经验默认
- **Combiner 是 shuffle 杀手**: sum/max/min/count 必用
- **Hash partition 默认**: 数据倾斜时换自定义
- **每 reduce 处理 0.5-2 GB**: 不能太大或太小

## 3.3 MapReduce 与现代框架

MapReduce (2004 Google paper) 是大数据计算的"祖师爷", 但有局限:
- 中间结果落盘 (慢)
- 复杂任务需要多个 MR job 串联
- 资源利用率低

现代替代:
- **Spark** (BD 后续课程): 内存计算, 5-100x 快
- **Flink**: 流批一体
- **Beam**: 统一批流 API

但 MapReduce 概念 (Map / Shuffle / Reduce / Combiner / Partitioner) 仍是分布式计算的"通用语言", 学习它能快速理解任何分布式计算系统。

$v$,
        $v${"questions": [{"id": "q04-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd04.py 中的 4 个函数; 评测以 test_bd04.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_map_single_file$v$, $v$[300MB] / 128MB → ceil(300/128) = 3$v$, false, $v$[300MB] / 128MB → ceil(300/128) = 3$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_map_two_files$v$, $v$[100MB, 200MB] / 128MB → ceil(100/128)+ceil(200/128) = 1+2 = 3$v$, false, $v$[100MB, 200MB] / 128MB → ceil(100/128)+ceil(200/128) = 1+2 = 3$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_map_custom_split_64mb$v$, $v$[300MB] / 64MB → 5$v$, false, $v$[300MB] / 64MB → 5$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_map_three_files_default$v$, $v$[128MB, 256MB, 64MB] → 1+2+1 = 4$v$, false, $v$[128MB, 256MB, 64MB] → 1+2+1 = 4$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_map_raises_on_zero_split$v$, $v$map raises on zero split$v$, false, $v$map raises on zero split$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_map_raises_on_non_list$v$, $v$map raises on non list$v$, false, $v$map raises on non list$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_reduce_5gb_default$v$, $v$5 GB / 1 GB → 5$v$, false, $v$5 GB / 1 GB → 5$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_reduce_partial_ceil$v$, $v$1500 MB / 1024 MB → ceil = 2$v$, false, $v$1500 MB / 1024 MB → ceil = 2$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_reduce_custom_target_500mb$v$, $v$5 GB / 500 MB → 11 (ceil 5120/500)$v$, false, $v$5 GB / 500 MB → 11 (ceil 5120/500)$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_reduce_raises_on_zero_data$v$, $v$reduce raises on zero data$v$, false, $v$reduce raises on zero data$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_reduce_raises_on_non_int$v$, $v$reduce raises on non int$v$, false, $v$reduce raises on non int$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_part_simple$v$, $v$'a' → ord('a')=97, 97 % 5 = 2$v$, false, $v$'a' → ord('a')=97, 97 % 5 = 2$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_part_word$v$, $v$'hello' → 104+101+108+108+111 = 532, 532 % 7 = 525/7=75 余 7? 7*76=532 余 0$v$, true, $v$'hello' → 104+101+108+108+111 = 532, 532 % 7 = 525/7=75 余 7? 7*76=532 余 0$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_part_long_word$v$, $v$'mapreduce' sum = 109+97+112+114+101+100+117+99+101 = 950, 950 % 10$v$, true, $v$'mapreduce' sum = 109+97+112+114+101+100+117+99+101 = 950, 950 % 10$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_part_raises_on_empty_key$v$, $v$part raises on empty key$v$, true, $v$part raises on empty key$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_part_raises_on_zero_reducers$v$, $v$part raises on zero reducers$v$, true, $v$part raises on zero reducers$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_part_raises_on_non_string$v$, $v$part raises on non string$v$, true, $v$part raises on non string$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_comb_max$v$, $v$comb max$v$, true, $v$comb max$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_comb_min$v$, $v$comb min$v$, true, $v$comb min$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_comb_avg$v$, $v$avg 不可 combine$v$, true, $v$avg 不可 combine$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_comb_median$v$, $v$comb median$v$, true, $v$comb median$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_comb_distinct$v$, $v$comb distinct$v$, true, $v$comb distinct$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_comb_raises_on_unknown$v$, $v$comb raises on unknown$v$, true, $v$comb raises on unknown$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_comb_raises_on_non_string$v$, $v$comb raises on non string$v$, true, $v$comb raises on non string$v$, NULL, 24)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
