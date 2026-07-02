-- BD6: YARN 资源管理与调度
-- practice_id=17, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        17,
        $v$YARN 资源管理与调度$v$,
        'PRACTICE',
        1,
        $v$intermediate$v$,
        $v$## YARN 架构与 Container

## 1.1 YARN 出现的背景

Hadoop 1.x 的 MapReduce 把"资源管理"和"任务调度"耦合, 问题:
- 只能跑 MapReduce, 不能跑 Spark / Flink
- 资源利用率低 (slot 模型, 内存 CPU 不解耦)
- 调度器单点瓶颈

Hadoop 2.x 引入 YARN (Yet Another Resource Negotiator) 解耦:
- **ResourceManager (RM)**: 集群级资源管理
- **NodeManager (NM)**: 节点级 container 管理
- **ApplicationMaster (AM)**: 每应用一个, 向 RM 申请资源

## 1.2 Container: 资源抽象

Container 是 YARN 的资源分配单元:
- **内存 (memory)**: GB
- **CPU (vCore)**: 虚拟核
- **网络 / GPU** (扩展)

集群总资源 = 所有节点资源总和。给定单 container 配置 (例: 8 GB):
- 总 container 数 = $\lfloor \text{total\_memory} / \text{container\_memory} \rfloor$

工程实务: 通常按内存做主要约束, CPU 是次要约束 (内存比 CPU 易耗尽)。

## 1.3 资源请求合法性

AM 向 RM 申请 container 时, 必须满足:
- 请求内存 ≤ 单 container 最大内存 (常 32 GB)
- 请求 CPU ≤ 单 container 最大 vCore (常 16)
- 请求资源 > 0

不合法请求被 RM 拒绝, AM 必须降低请求重试。

`is_resource_request_valid(req_mem, req_cpu, max_mem, max_cpu)`: 1 ≤ req ≤ max → True。


## 队列与公平调度

## 2.1 多队列设计

生产 YARN 集群通常有多个队列, 按业务/优先级划分:
- **production**: 高优先级业务任务 (如生产报表)
- **default**: 中等任务 (开发/测试)
- **low**: 低优先级 (探索性查询)

简化策略 (本关 assign_yarn_queue):
- priority ≥ 8 → 'production'
- 4 ≤ priority < 8 → 'default'
- priority < 4 → 'low'

工程实务: 实际队列配置由集群管理员定义, 业务方申请使用某个队列。

## 2.2 三种主流调度器

YARN 内置三种调度器:
- **FIFO Scheduler**: 先到先得, 简单但易饥饿
- **Capacity Scheduler**: 队列固定容量, 队列内 FIFO (Yahoo 默认)
- **Fair Scheduler**: 按权重公平分配 (Facebook 默认)

本关聚焦 Fair Scheduler 的核心思想: 公平分配。

## 2.3 公平调度的份额计算

给定一组 job, 每个有权重 w_i, 总资源 R:

$\text{share}_i = \lfloor R \cdot w_i / \sum_j w_j \rfloor$

简化版 (本关 compute_fair_share_for_job): 给定单 job 权重, 总权重和, 总资源, 返回 floor 份额。

工程实务: 高优先级 job 设高权重 (如 weight=10), 低优先级 weight=1。Fair Scheduler 保证每个 job 至少获得权重比例的资源。


## 业务案例与工程口诀

## 3.1 业务案例: 多租户调度

场景: 100 节点集群, 总内存 8 TB, 6 个业务部门共享, 每部门权重不同:

| 部门 | 权重 | 公平份额 (本关 compute_fair_share) |
|---|---:|---:|
| 实时风控 | 10 | 8000 × 10/30 = 2666 GB |
| 报表 BI | 8 | 8000 × 8/30 ≈ 2133 GB |
| 推荐算法 | 6 | 8000 × 6/30 = 1600 GB |
| 数据科学 | 3 | 8000 × 3/30 = 800 GB |
| 测试环境 | 2 | 8000 × 2/30 ≈ 533 GB |
| 临时任务 | 1 | 8000 × 1/30 ≈ 266 GB |

运维流水线:
1. **集群容量** (本关 compute_yarn_container_count): 总 8 TB / 8 GB = 1024 containers
2. **资源请求审核** (本关 is_resource_request_valid): 拒绝 > 32 GB 或 > 16 CPU 的非法请求
3. **队列分配** (本关 assign_yarn_queue): 风控 priority=10 → production
4. **公平份额** (本关 compute_fair_share_for_job): 每业务按权重分配

## 3.2 工程口诀

- **Container 是资源单元**: mem + CPU 解耦
- **队列分级是多租户基础**: 没有队列就是混战
- **Fair Scheduler 是默认**: Facebook/字节 在用
- **权重控制公平比例**: 高优先级 weight 高
- **资源请求要审核**: 防止 1 个 job 占满集群

## 3.3 现代云原生

YARN 在云原生时代的位置:
- K8s + Kueue 替代 YARN 调度容器化大数据
- Spark on K8s 不需要 YARN
- Hadoop on EMR 仍用 YARN, 但是托管的

但 YARN 概念 (Container / Queue / Fair Scheduler / 资源解耦) 仍是分布式资源管理的"通用术语"。

$v$,
        $v${"questions": [{"id": "q06-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd06.py 中的 4 个函数; 评测以 test_bd06.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_cont_8tb_8gb$v$, $v$8000 GB / 8 GB = 1000$v$, false, $v$8000 GB / 8 GB = 1000$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_cont_partial$v$, $v$100 GB / 8 GB = floor(12.5) = 12$v$, false, $v$100 GB / 8 GB = floor(12.5) = 12$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_cont_exact$v$, $v$64 GB / 16 GB = 4$v$, false, $v$64 GB / 16 GB = 4$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_cont_uneven$v$, $v$50 GB / 4 GB = floor(12.5) = 12$v$, false, $v$50 GB / 4 GB = floor(12.5) = 12$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_cont_raises_on_zero_total$v$, $v$cont raises on zero total$v$, false, $v$cont raises on zero total$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_cont_raises_on_zero_container$v$, $v$cont raises on zero container$v$, false, $v$cont raises on zero container$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_cont_raises_on_non_int$v$, $v$cont raises on non int$v$, false, $v$cont raises on non int$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_req_too_much_mem$v$, $v$req mem 50 > max 32 → False$v$, false, $v$req mem 50 > max 32 → False$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_req_too_much_cpu$v$, $v$req cpu 20 > max 16 → False$v$, false, $v$req cpu 20 > max 16 → False$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_req_zero_mem$v$, $v$req mem = 0 → False$v$, false, $v$req mem = 0 → False$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_req_at_max_boundary$v$, $v$req == max → True (boundary)$v$, false, $v$req == max → True (boundary)$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_req_custom_limits$v$, $v$custom: max=(16, 8), req=(10, 6) → True$v$, false, $v$custom: max=(16, 8), req=(10, 6) → True$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_req_raises_on_non_int$v$, $v$req raises on non int$v$, false, $v$req raises on non int$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_queue_production_high$v$, $v$priority=10 → production$v$, false, $v$priority=10 → production$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_queue_production_at_8$v$, $v$priority=8 → production (boundary)$v$, false, $v$priority=8 → production (boundary)$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_queue_default_at_4$v$, $v$priority=4 → default$v$, true, $v$priority=4 → default$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_queue_default_at_7$v$, $v$priority=7 → default$v$, true, $v$priority=7 → default$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_queue_low_at_3$v$, $v$priority=3 → low$v$, true, $v$priority=3 → low$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_queue_low_at_0$v$, $v$priority=0 → low$v$, true, $v$priority=0 → low$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_queue_low_negative$v$, $v$priority=-5 → low$v$, true, $v$priority=-5 → low$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_queue_raises_on_non_int$v$, $v$queue raises on non int$v$, true, $v$queue raises on non int$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_share_third$v$, $v$w=10, total_w=30, R=8000 → 8000*10/30 = 2666.67 → 2666$v$, true, $v$w=10, total_w=30, R=8000 → 8000*10/30 = 2666.67 → 2666$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_share_quarter$v$, $v$w=2, total_w=8, R=1000 → 250$v$, true, $v$w=2, total_w=8, R=1000 → 250$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_share_half$v$, $v$w=5, total_w=10, R=100 → 50$v$, true, $v$w=5, total_w=10, R=100 → 50$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_share_full$v$, $v$w=10, total_w=10, R=500 → 500 (单一 job 占全部)$v$, true, $v$w=10, total_w=10, R=500 → 500 (单一 job 占全部)$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_share_floor_truncate$v$, $v$w=1, total_w=3, R=100 → 33 (floor 33.33)$v$, true, $v$w=1, total_w=3, R=100 → 33 (floor 33.33)$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_share_zero_resources$v$, $v$R=0 → 0$v$, true, $v$R=0 → 0$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_share_raises_on_zero_weight$v$, $v$share raises on zero weight$v$, true, $v$share raises on zero weight$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_share_raises_on_zero_total$v$, $v$share raises on zero total$v$, true, $v$share raises on zero total$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_share_raises_on_non_int$v$, $v$share raises on non int$v$, true, $v$share raises on non int$v$, NULL, 30)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
