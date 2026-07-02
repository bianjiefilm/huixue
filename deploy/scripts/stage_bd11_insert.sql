-- BD11: Kafka 流数据平台
-- practice_id=22, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        22,
        $v$Kafka 流数据平台$v$,
        'PRACTICE',
        1,
        $v$intermediate$v$,
        $v$## Kafka 与流数据

## 1.1 Kafka 是什么

Kafka (LinkedIn 2011, Apache 2012) 是分布式发布订阅消息系统:
- **Producer**: 生产消息到 topic
- **Topic**: 逻辑消息分类
- **Partition**: topic 的物理分片 (并行单元)
- **Consumer**: 订阅 topic, 从 partition 读消息

用途: 日志收集 / 实时数据管道 / 流处理输入 / 消息队列。

## 1.2 Partition 与 Consumer Group

关键设计: 一个 topic 多个 partition, 一个 consumer group 多个 consumer:
- **同一 group 内**: 每个 partition 由唯一 consumer 消费 (并行)
- **不同 group**: 互相独立, 各自从头消费

给定 N 个 consumer 和 P 个 partition (N <= P 时), 分配策略 round-robin:

简化逻辑 (本关 assign_consumer_partitions):
- 按顺序遍历 partition, 用 i % N 分给 consumer
- 输出: dict[consumer_id, [partition list]]
- consumer 列表保持原顺序

工程实务: 实际还有 sticky / range 等策略, round-robin 最简单。

## 1.3 副本因子设计

Kafka partition 有多个副本 (replicas) 防止 broker 故障。

最小副本因子 (本关 compute_minimum_replication):
- 想容忍 ft 个 broker 同时故障
- 需要副本数 ≥ ft + 1
- 副本数不能超过 broker 数

公式: $\text{min\_RF} = \max(1, \min(\text{ft} + 1, \text{num\_brokers}))$

若 ft + 1 > num_brokers → 抛 ValueError (集群规模不够)。

工程实务: 生产标准 RF=3 (容忍 2 broker 故障), 关键业务 RF=5。


## 消费滞后与吞吐量

## 2.1 消费滞后 (Consumer Lag)

Kafka 监控核心指标: 当前 consumer offset 与 partition log_end_offset (最新消息 offset) 的差。

$\text{lag} = \text{log\_end\_offset} - \text{consumer\_offset}$

lag 严重判定 (本关 is_message_lag_critical):
- lag > threshold (默认 1000) → True (严重滞后, 报警)
- lag <= threshold → False

工程实务:
- lag = 0: 实时消费
- lag < 1000: 正常波动
- lag > 10000: consumer 跟不上 producer, 必须扩容

## 2.2 吞吐量估算

给定每秒消息数 m 与平均消息大小 s (字节):

$\text{throughput\_bytes\_per\_sec} = m \cdot s$

工程实务:
- 单 broker 网络: 1 Gbps = 125 MB/s
- 实际吞吐: 60-80% 网络上限 (留 OS / 其他流量)
- 1 broker 跑 100 MB/s 流量是经验值

若吞吐 > 单 broker 上限 → 必须扩 broker 或增 partition。

## 2.3 partition 数选择

partition 数决定并行度上限:
- **太少 (1)**: 单消费者瓶颈, 无并行
- **太多 (10000+)**: 元数据压力 + 文件句柄
- **经验**: partition 数 ≈ 期望并行 consumer 数

例: 期望 10 个 consumer 并行 → 至少 10 partition。


## 业务案例与工程口诀

## 3.1 业务案例: 实时埋点平台

场景: 公司前端埋点 100 万事件/秒, Kafka 集群 3 broker, 接收并供下游消费:

设计:
1. **副本因子** (本关 compute_minimum_replication): ft=2, 3 broker → RF=3 (容忍 2 故障)
2. **partition 数**: 期望 100 个 consumer 并行 → 100 partitions
3. **吞吐量** (本关 compute_throughput_bytes_per_sec): 1M × 200 B = 200 MB/s, 单 broker 100 MB/s → 至少 2 broker 分担, 实际 3 broker 留余量
4. **consumer 分配** (本关 assign_consumer_partitions): 100 consumers vs 100 partitions = 1:1
5. **lag 监控** (本关 is_message_lag_critical): threshold=1000 触发报警

## 3.2 工程口诀

- **RF=3 是默认**: 容忍 2 故障
- **partition 数 = 期望并行 consumer 数**
- **lag > 1000 报警**: 早发现消费瓶颈
- **吞吐看网络**: 单 broker ~ 100 MB/s
- **生产端 ack=all + min.insync.replicas=2**: 强一致

## 3.3 现代趋势

Kafka 仍是流处理首选, 但有挑战:
- **Pulsar (Apache)**: 存算分离, 支持 multi-tenancy
- **Redpanda**: C++ 重写, 单 broker 性能 10x
- **AWS Kinesis / 阿里 LogService**: 托管流服务

Kafka 概念 (Topic / Partition / Consumer Group / Lag) 是所有流处理的"通用术语"。

$v$,
        $v${"questions": [{"id": "q11-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd11.py 中的 4 个函数; 评测以 test_bd11.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_assign_3c_3p$v$, $v$3 consumer / 3 partition → 1:1$v$, false, $v$3 consumer / 3 partition → 1:1$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_assign_2c_4p$v$, $v$2 consumer / 4 partition: c1 → [0,2], c2 → [1,3]$v$, false, $v$2 consumer / 4 partition: c1 → [0,2], c2 → [1,3]$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_assign_3c_5p$v$, $v$3c/5p: c1 → [0,3], c2 → [1,4], c3 → [2]$v$, false, $v$3c/5p: c1 → [0,3], c2 → [1,4], c3 → [2]$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_assign_more_consumers_than_partitions$v$, $v$4 consumer / 2 partition: c3, c4 没分配, 仍要在 dict 中$v$, false, $v$4 consumer / 2 partition: c3, c4 没分配, 仍要在 dict 中$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_assign_one_consumer$v$, $v$1c / 5p → 全给 c1$v$, false, $v$1c / 5p → 全给 c1$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_assign_raises_on_empty_consumers$v$, $v$assign raises on empty consumers$v$, false, $v$assign raises on empty consumers$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_assign_raises_on_non_list$v$, $v$assign raises on non list$v$, false, $v$assign raises on non list$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_repl_basic_3broker_ft2$v$, $v$ft=2, broker=3 → min(3, 3) = 3$v$, false, $v$ft=2, broker=3 → min(3, 3) = 3$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_repl_ft0$v$, $v$ft=0, broker=5 → max(1, min(1, 5)) = 1$v$, false, $v$ft=0, broker=5 → max(1, min(1, 5)) = 1$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_repl_ft1$v$, $v$ft=1, broker=3 → 2$v$, false, $v$ft=1, broker=3 → 2$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_repl_more_brokers$v$, $v$ft=2, broker=10 → 3$v$, false, $v$ft=2, broker=10 → 3$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_repl_raises_when_insufficient_brokers$v$, $v$ft=5, broker=3: ft+1=6 > 3 → ValueError$v$, false, $v$ft=5, broker=3: ft+1=6 > 3 → ValueError$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_repl_raises_on_negative_ft$v$, $v$repl raises on negative ft$v$, false, $v$repl raises on negative ft$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_repl_raises_on_zero_brokers$v$, $v$repl raises on zero brokers$v$, false, $v$repl raises on zero brokers$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_repl_raises_on_non_int$v$, $v$repl raises on non int$v$, true, $v$repl raises on non int$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_lag_normal$v$, $v$offset=900, log_end=1000, lag=100 < 1000 → False$v$, true, $v$offset=900, log_end=1000, lag=100 < 1000 → False$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_lag_critical$v$, $v$offset=0, log_end=2000, lag=2000 > 1000 → True$v$, true, $v$offset=0, log_end=2000, lag=2000 > 1000 → True$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_lag_at_threshold$v$, $v$lag=1000 == threshold → False (>, 严格)$v$, true, $v$lag=1000 == threshold → False (>, 严格)$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_lag_just_above$v$, $v$lag=1001 → True$v$, true, $v$lag=1001 → True$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_lag_zero$v$, $v$offset == log_end → lag=0, False$v$, true, $v$offset == log_end → lag=0, False$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_lag_custom_threshold$v$, $v$threshold=100, lag=200 → True$v$, true, $v$threshold=100, lag=200 → True$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_lag_raises_on_consumer_gt_log_end$v$, $v$lag raises on consumer gt log end$v$, true, $v$lag raises on consumer gt log end$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_lag_raises_on_non_int$v$, $v$lag raises on non int$v$, true, $v$lag raises on non int$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_tput_typical$v$, $v$1M msg/s × 200B = 200,000,000 = 200 MB/s$v$, true, $v$1M msg/s × 200B = 200,000,000 = 200 MB/s$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_tput_small$v$, $v$1000 msg/s × 100B = 100,000$v$, true, $v$1000 msg/s × 100B = 100,000$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_tput_large_messages$v$, $v$100 msg/s × 1MB = 100 MB/s$v$, true, $v$100 msg/s × 1MB = 100 MB/s$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_tput_minimum$v$, $v$1 msg/s × 1B = 1$v$, true, $v$1 msg/s × 1B = 1$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_tput_raises_on_zero$v$, $v$tput raises on zero$v$, true, $v$tput raises on zero$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_tput_raises_on_non_int$v$, $v$tput raises on non int$v$, true, $v$tput raises on non int$v$, NULL, 29)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
