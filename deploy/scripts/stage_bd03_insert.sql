-- BD3: HDFS 操作与 Block 调度
-- practice_id=14, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        14,
        $v$HDFS 操作与 Block 调度$v$,
        'PRACTICE',
        1,
        $v$intermediate$v$,
        $v$## HDFS 副本放置与数据本地性

## 1.1 副本放置策略 (rack-aware)

HDFS NameNode 决定每个 block 的副本放在哪些 DataNode。默认策略 (rack-aware replica placement):

- **第 1 个副本**: 优先写入客户端所在节点 (本地写入快)
- **第 2 个副本**: 不同机架的随机节点 (机架级容错)
- **第 3 个副本**: 与第 2 个相同机架的不同节点 (减少跨机架流量)
- **超过 3 个副本**: 随机分布

为什么这么设计? 兼顾**写入性能 (本地)** + **机架容错 (跨机架)** + **网络带宽 (本地优先)**。

## 1.2 数据本地性 (Data Locality)

MapReduce 任务调度时, NameNode 优先把任务分配到 block 副本所在的节点 (移动计算而非数据)。

数据本地性得分:

$\text{locality} = \frac{\text{在本地节点的副本数}}{\text{总副本数}}$

值域 [0, 1]:
- 1.0: 任务在所有副本节点上都能本地执行
- 0.0: 没有任何副本在本地, 必须跨节点拉数据

工程实务: 数据本地性 < 0.5 → 调度问题, 检查 YARN 配置 (BD06 复习)。

## 1.3 副本因子合法性

副本因子必须满足:
- **副本数 ≥ 1**: 至少 1 份, 否则丢数据
- **副本数 ≤ DataNode 数**: 不能比节点还多 (无处放)
- **生产推荐 = 3**: 1 个性能 + 2 个容错

`is_replication_factor_valid(replicas, datanodes)`: 满足 1 ≤ replicas ≤ datanodes → True。


## 副本不足检测与机架分配

## 2.1 副本不足 (under-replicated) 检测

DataNode 故障 / 网络分区会导致部分 block 副本数低于配置目标 (如 3)。NameNode 周期性扫描发现这些 block, 触发副本恢复。

给定每个 block 当前副本数列表, 计数副本 < 目标值的 block:

```
count = sum(1 for r in replicas_per_block if r < target)
```

工程实务:
- **正常**: 0 个 under-replicated
- **临时 (DataNode 重启)**: < 1000 (复习 BD01 安全模式阈值)
- **持续 > 1000**: 集群异常, 必须运维介入

## 2.2 机架分配 (round-robin)

简化的副本机架分配: round-robin 把 N 个副本分到 R 个机架。

```
rack_indices = [i % R for i in range(N)]
```

例: N=4, R=3 → [0, 1, 2, 0]
例: N=2, R=4 → [0, 1]

工程实务: 实际策略更复杂 (rack-awareness + 节点容量 + 网络距离), 但 round-robin 是基础理解。

## 2.3 副本管理的运维指标

NameNode 提供的关键指标:
- **Live DataNodes**: 在线节点数
- **Under-replicated Blocks**: 副本不足
- **Missing Blocks**: 完全丢失 (无任何副本)
- **Corrupt Blocks**: 校验和不一致

Missing > 0 → 数据丢失, 严重事故。Corrupt > 0 → 立即从其他副本恢复。


## 业务案例与工程口诀

## 3.1 业务案例: HDFS 集群运维

场景: 100 节点 HDFS 集群, 50 个机架, 每天读 5 PB 数据:

运维监控:
1. **数据本地性** (本关 compute_data_locality_score): 目标 > 0.7, 实际 0.85 ✓
2. **副本因子** (本关 is_replication_factor_valid): R=3, 100 DataNode → 合法
3. **副本不足扫描** (本关 count_blocks_to_re_replicate): 每周报告 under-replicated < 100 块 OK
4. **机架分配审计** (本关 assign_replicas_round_robin): 副本均匀分布 50 个机架

## 3.2 工程口诀

- **本地性 > 0.7 是健康线**: < 0.5 立即调查
- **副本因子默认 3, 关键数据 5**: 平衡可靠 + 成本
- **under-replicated > 1000 报警**: 集群有故障
- **机架分布要均匀**: round-robin 是基础, 不能集中在少数机架
- **Missing block 是大事故**: 立即响应

## 3.3 现代云原生对比

AWS S3 / 阿里 OSS 等对象存储:
- 自动 11 个 9 持久性 (无需配置副本)
- 跨可用区 (AZ) 自动复制
- 计算与存储分离

但 HDFS 概念 (副本因子 / 数据本地性 / 机架感知) 仍是分布式存储的"通用术语", 现代云原生只是把这些抽象到底层。

## 3.4 EC (Erasure Coding) 替代副本

HDFS 3.x 支持纠删码 (EC):
- 不再 3 份副本 (300% 存储开销)
- 改用 6+3 EC: 6 份数据 + 3 份校验, 共 9 份, 容忍 3 份丢失
- 存储开销 = 9/6 = 150% (节省 50%)

代价: 编码计算开销 + 单 block 不能本地读 (需要其他 block 一起解码)。冷数据用 EC, 热数据仍用副本。本关聚焦传统副本, EC 是进阶专题。

$v$,
        $v${"questions": [{"id": "q03-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd03.py 中的 4 个函数; 评测以 test_bd03.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_loc_one_third$v$, $v$1 / 3 = 0.333...$v$, false, $v$1 / 3 = 0.333...$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_loc_two_thirds$v$, $v$2 / 3 = 0.666...$v$, false, $v$2 / 3 = 0.666...$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_loc_three_in_5$v$, $v$3 / 5 = 0.6$v$, false, $v$3 / 5 = 0.6$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_loc_perfect$v$, $v$3 / 3 = 1.0 (boundary)$v$, false, $v$3 / 3 = 1.0 (boundary)$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_loc_raises_on_zero_total$v$, $v$loc raises on zero total$v$, false, $v$loc raises on zero total$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_loc_raises_on_local_gt_total$v$, $v$loc raises on local gt total$v$, false, $v$loc raises on local gt total$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_loc_raises_on_non_int$v$, $v$loc raises on non int$v$, false, $v$loc raises on non int$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_repl_too_many$v$, $v$5 副本, 3 DataNode → False$v$, false, $v$5 副本, 3 DataNode → False$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_repl_zero$v$, $v$0 副本 → False$v$, false, $v$0 副本 → False$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_repl_raises_on_negative$v$, $v$repl raises on negative$v$, false, $v$repl raises on negative$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_repl_raises_on_non_int$v$, $v$repl raises on non int$v$, false, $v$repl raises on non int$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_re_repl_one_under$v$, $v$[3, 2, 3] target=3 → 1$v$, false, $v$[3, 2, 3] target=3 → 1$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_re_repl_three_under$v$, $v$[1, 2, 3, 1, 4] target=3 → 3 (1, 2, 1 都 < 3)$v$, true, $v$[1, 2, 3, 1, 4] target=3 → 3 (1, 2, 1 都 < 3)$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_re_repl_default_target$v$, $v$default target=3$v$, true, $v$default target=3$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_re_repl_custom_target_5$v$, $v$target=5: [3, 4, 5, 6] → 2 (3, 4 < 5)$v$, true, $v$target=5: [3, 4, 5, 6] → 2 (3, 4 < 5)$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_re_repl_raises_on_negative_count$v$, $v$re repl raises on negative count$v$, true, $v$re repl raises on negative count$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_re_repl_raises_on_non_list$v$, $v$re repl raises on non list$v$, true, $v$re repl raises on non list$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_rr_3_replicas_3_racks$v$, $v$3 副本 3 机架 → [0, 1, 2]$v$, true, $v$3 副本 3 机架 → [0, 1, 2]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_rr_4_replicas_3_racks$v$, $v$4 副本 3 机架 → [0, 1, 2, 0]$v$, true, $v$4 副本 3 机架 → [0, 1, 2, 0]$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_rr_2_replicas_4_racks$v$, $v$2 副本 4 机架 → [0, 1]$v$, true, $v$2 副本 4 机架 → [0, 1]$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_rr_5_replicas_2_racks$v$, $v$5 副本 2 机架 → [0, 1, 0, 1, 0]$v$, true, $v$5 副本 2 机架 → [0, 1, 0, 1, 0]$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_rr_raises_on_zero_racks$v$, $v$rr raises on zero racks$v$, true, $v$rr raises on zero racks$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_rr_raises_on_negative_replicas$v$, $v$rr raises on negative replicas$v$, true, $v$rr raises on negative replicas$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_rr_raises_on_non_int$v$, $v$rr raises on non int$v$, true, $v$rr raises on non int$v$, NULL, 24)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
