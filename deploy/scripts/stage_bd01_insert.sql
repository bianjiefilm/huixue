-- BD1: Hadoop 概述与集群搭建
-- practice_id=12, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        12,
        $v$Hadoop 概述与集群搭建$v$,
        'PRACTICE',
        1,
        $v$beginner$v$,
        $v$## Hadoop 生态系统总览

## 1.1 大数据时代的核心问题

传统单机数据库到 21 世纪初已经无法处理:
- **数据规模**: 单机 RDBMS 上限 TB 级, 互联网公司日产 TB-PB
- **数据增速**: 日志/传感器数据每天翻倍, 索引性能 / 备份策略全部失效
- **数据多样**: 结构化 (订单) + 半结构化 (日志) + 非结构化 (图片/视频), 单一表模型容纳不下

Hadoop (2006-) 是第一个工业级开源大数据生态, 解决这些问题用三个核心思想:
- **分布式存储**: 文件切块, 多节点冗余存储
- **分布式计算**: 计算逻辑下放到数据节点 (移动计算而非数据)
- **横向扩展**: 加节点 = 加容量 + 加算力, 线性增长

## 1.2 生态组件与角色

Hadoop 生态由多个组件协作, 每个组件有清晰角色:

| 组件 | 角色 (role) |
|---|---|
| hdfs | storage (分布式文件系统) |
| mapreduce | compute (批处理计算引擎) |
| yarn | scheduling (资源管理与任务调度) |
| hive | data_warehouse (数据仓库, SQL 接口) |
| hbase | nosql (NoSQL 数据库, 随机读写) |
| kafka | streaming (流式数据平台) |
| sqoop | migration (关系数据库迁移工具) |

本关函数 `get_hadoop_component_role(component)` 实现这个映射, 是后续所有关卡的"角色定位"基础。

## 1.3 集群规模与容量规划

给定业务数据规模 D (TB), 单节点磁盘容量 C (TB), 副本因子 R (默认 3), 所需节点数:

$N = \lceil \frac{D \cdot R}{C} \rceil$

例: D = 100 TB, C = 10 TB, R = 3 → N = ⌈30⌉ = 30 节点。

工程实务: 实际还要加 30-50% 缓冲 (机器故障 / 临时数据), 按公式估算后向上调。本关函数只算理论最小值。


## 安全模式与服务端口

## 2.1 HDFS 安全模式 (Safe Mode)

Hadoop 集群启动时自动进入"安全模式": 此时 HDFS 只读, 等待所有 DataNode 上报已有 block, NameNode 校验副本数。

何时退出安全模式:
- 99.9% 的 block 都至少有 1 个副本
- 在线 DataNode ≥ 配置的最小阈值
- 可手动触发 (运维介入)

实务判定 (本关简化): `under_replicated_blocks <= threshold` → 安全模式可退出。

工程实务: 大集群启动可能 5-30 分钟才退出安全模式, 期间必须监控。

## 2.2 服务默认端口

Hadoop 各服务的默认端口 (运维必记):

| 服务 (service) | 端口 (port) |
|---|---|
| namenode | 9000 (RPC) |
| datanode | 9866 (data transfer) |
| namenode_ui | 9870 (Web UI) |
| resourcemanager | 8088 (YARN UI) |
| jobhistory | 19888 |

本关函数 `get_hadoop_default_port(service)` 返回这些默认值。

工程实务: 默认端口在多 Hadoop 实例并存场景必改, 但学习与单集群时按默认值。

## 2.3 集群高可用 (HA)

生产集群必上 HA 配置:
- NameNode HA: 主备 NameNode + ZooKeeper 协调
- YARN ResourceManager HA: 类似主备
- JournalNode 集群: 共享编辑日志

本关不实现 HA 算法, 但**理解 HA 的原因**是必修: 单点 NameNode 故障 = 整个集群瘫痪。


## 业务案例与工程口诀

## 3.1 业务案例: 中型企业 Hadoop 集群规划

场景: 100 人公司从 0 搭一个数据平台, 业务需求:
- 日新增数据: 1 TB (业务日志 + 数据库 binlog)
- 数据保留 90 天: 90 TB 历史数据 + 1 TB 日新增
- 副本因子 3 (生产标准)
- 单节点磁盘 10 TB (机架式服务器标配)

规划:
1. **数据规模** (本关): D = 90 TB, R = 3 → 270 TB 实际存储
2. **节点数** (本关 compute_cluster_node_count): N = ⌈270 / 10⌉ = 27 节点
3. **加 30% 缓冲**: ≈ 35 节点 (生产实际数)
4. **服务部署**: NameNode HA 用 3 节点 (主备 + ZK), DataNode 32 节点
5. **端口配置** (本关 get_hadoop_default_port): NameNode 9000, DataNode 9866, UI 9870
6. **启动检查** (本关 is_hadoop_safe_mode_ok): under_replicated < 1000 才上线

## 3.2 工程口诀

- **R=3 是默认**: 一份原始 + 两份冗余, 工业标准
- **节点数 = 容量 × R / 单节点容量**: 不要忘乘 R
- **缓冲 30%**: 故障 + 临时数据
- **安全模式不要急退出**: 强退可能丢数据
- **服务端口必记**: 9000 / 9866 / 9870 / 8088

## 3.3 Hadoop 与现代云原生的对比

Hadoop 是 2010 年代王者, 现代趋势:
- **存算分离**: S3/OSS 替代 HDFS, EMR/Databricks 替代 YARN
- **托管服务**: AWS EMR / 阿里 EMR 一键集群
- **容器化**: Kubernetes 替代 YARN 调度

但 Hadoop 概念 (block / replication / NameNode / DataNode) 仍是大数据工程的"通用语言", 学习它能快速理解任何分布式存储/计算系统。

$v$,
        $v${"questions": [{"id": "q01-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd01.py 中的 4 个函数; 评测以 test_bd01.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_role_hdfs$v$, $v$role hdfs$v$, false, $v$role hdfs$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_role_mapreduce$v$, $v$role mapreduce$v$, false, $v$role mapreduce$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_role_yarn$v$, $v$role yarn$v$, false, $v$role yarn$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_role_hive$v$, $v$role hive$v$, false, $v$role hive$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_role_hbase$v$, $v$role hbase$v$, false, $v$role hbase$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_role_kafka$v$, $v$role kafka$v$, false, $v$role kafka$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_role_sqoop$v$, $v$role sqoop$v$, false, $v$role sqoop$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_role_raises_on_unknown$v$, $v$role raises on unknown$v$, false, $v$role raises on unknown$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_role_raises_on_empty$v$, $v$role raises on empty$v$, false, $v$role raises on empty$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_role_raises_on_non_string$v$, $v$role raises on non string$v$, false, $v$role raises on non string$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_node_typical$v$, $v$100TB, 10TB/node, R=3 → ceil(300/10) = 30$v$, false, $v$100TB, 10TB/node, R=3 → ceil(300/10) = 30$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_node_partial_ceil$v$, $v$95TB, 10TB/node, R=3 → ceil(285/10) = 29 (向上)$v$, false, $v$95TB, 10TB/node, R=3 → ceil(285/10) = 29 (向上)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_node_default_replication$v$, $v$default R=3$v$, false, $v$default R=3$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_node_replication_1$v$, $v$R=1: 100TB → 10 节点$v$, false, $v$R=1: 100TB → 10 节点$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_node_replication_2$v$, $v$R=2: 100TB → 20 节点$v$, false, $v$R=2: 100TB → 20 节点$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_node_small_data$v$, $v$1TB, 10TB/node, R=3 → ceil(3/10) = 1$v$, false, $v$1TB, 10TB/node, R=3 → ceil(3/10) = 1$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_node_raises_on_zero_data$v$, $v$node raises on zero data$v$, true, $v$node raises on zero data$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_node_raises_on_zero_capacity$v$, $v$node raises on zero capacity$v$, true, $v$node raises on zero capacity$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_node_raises_on_non_numeric$v$, $v$node raises on non numeric$v$, true, $v$node raises on non numeric$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_safe_at_threshold$v$, $v$1000 == 1000 → True (<=)$v$, true, $v$1000 == 1000 → True (<=)$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_safe_above_threshold$v$, $v$1500 > 1000 → False$v$, true, $v$1500 > 1000 → False$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_safe_zero$v$, $v$0 → True (boundary)$v$, true, $v$0 → True (boundary)$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_safe_custom_threshold$v$, $v$100, threshold=50 → False$v$, true, $v$100, threshold=50 → False$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_safe_raises_on_negative$v$, $v$safe raises on negative$v$, true, $v$safe raises on negative$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_safe_raises_on_non_int$v$, $v$safe raises on non int$v$, true, $v$safe raises on non int$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_port_namenode$v$, $v$port namenode$v$, true, $v$port namenode$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_port_datanode$v$, $v$port datanode$v$, true, $v$port datanode$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_port_namenode_ui$v$, $v$port namenode ui$v$, true, $v$port namenode ui$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_port_resourcemanager$v$, $v$port resourcemanager$v$, true, $v$port resourcemanager$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_port_jobhistory$v$, $v$port jobhistory$v$, true, $v$port jobhistory$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_port_raises_on_unknown$v$, $v$port raises on unknown$v$, true, $v$port raises on unknown$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_port_raises_on_non_string$v$, $v$port raises on non string$v$, true, $v$port raises on non string$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
