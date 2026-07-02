#!/usr/bin/env python3
"""Generate bigdata stage JSON files from YAML configs."""

import json
import yaml
from pathlib import Path

BASE = Path(__file__).parent
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

STAGES = [
    {"num": 1, "yaml": "stage_1.yaml", "json": "stage_bigdata_01-06.json"},
]

YAML_FILES = sorted((BASE / "content_orchestrator/stages_config/bigdata").glob("stage_*.yaml"), key=lambda p: int(p.stem.split("_")[1]))

def make_handbook(num: int, title: str, kps: list, tips: list, to_avoid: list, baseline: str) -> str:
    """Generate a rich handbook markdown."""
    kp_text = "\n".join(f"- {kp}" for kp in kps if kp.startswith("三"))
    kp_detail = "\n".join(f"- {kp}" for kp in kps if not kp.startswith("一") and not kp.startswith("二") and not kp.startswith("三") and not kp.startswith("四") and not kp.startswith("五"))

    sections = {
        1: {
            "k2": "大数据概念与发展历程、Hadoop核心组件（HDFS/MapReduce/YARN）、Hadoop生态体系、集群架构（Master/Slave）、ZooKeeper分布式协调",
            "tips": "集群规划与硬件选型、本地模式/伪分布式/完全分布式切换",
            "cmds": ["start-all.sh", "stop-all.sh", "jps", "hdfs dfsadmin -report"],
        },
        2: {
            "k2": "HDFS架构（NameNode/DataNode/SecondaryNameNode）、Block块存储与副本策略、HDFS读写流程、命令行操作（hdfs dfs）、文件权限",
            "tips": "小文件处理策略（HAR/SequenceFile）、数据均衡与扩容",
            "cmds": ["hdfs dfs -ls /", "hdfs dfs -mkdir", "hdfs dfs -put", "hdfs dfs -get", "hdfs dfs -du -h"],
        },
        3: {
            "k2": "HDFS Java API（FileSystem/FSDataInputStream/FSDataOutputStream）、文件上传下载、目录操作与权限管理、序列化和Writable接口",
            "tips": "连接池复用（FileSystem.newInstance）、异常处理（IOException）",
            "cmds": ["Configuration", "FileSystem.get(uri, conf, user)", "FSDataInputStream", "FSDataOutputStream"],
        },
        4: {
            "k2": "MapReduce核心思想（分而治之）、Map阶段与Reduce阶段、Combiner与Partitioner、Shuffle与Sort过程、Job与Task运行流程",
            "tips": "拓扑感知计算、推测执行机制",
            "cmds": ["Job.waitForCompletion", "Text", "IntWritable", "context.write", "FileInputFormat.addInputPath"],
        },
        5: {
            "k2": "Hadoop streaming与Python MR、Writable类型与自定义数据类型、多表连接（Map端Join/Reduce端Join）、计数器与日志",
            "tips": "二次排序（SortComparator）、分布式缓存（DistributedCache/Job.addCacheFile）",
            "cmds": ["hadoop jar streaming.jar", "-mapper", "-reducer", "-input", "-output"],
        },
        6: {
            "k2": "YARN架构（ResourceManager/NodeManager/ApplicationMaster）、YARN与MapReduce1对比、Container与资源分配、三种调度器（FIFO/Capacity/Fair）",
            "tips": "内存与CPU配置（yarn-site.xml）、长短作业分离",
            "cmds": ["yarn application -list", "yarn rmadmin -getServiceState", "yarn jar", "mapreduce.jobhistory.address"],
        },
        7: {
            "k2": "Hive架构（Driver/Compiler/Executor）、Hive与MapReduce/Spark的关系、数据类型（基本类型与复杂类型ARRAY/MAP/STRUCT）、数据库与表操作（DDL）、分区表与分桶表",
            "tips": "内部表与外部表区别、SerDe序列化机制",
            "cmds": ["CREATE TABLE", "LOAD DATA", "SELECT * FROM", "SHOW PARTITIONS", "DESC FORMATTED"],
        },
        8: {
            "k2": "HiveQL查询语法（SELECT/WHERE/GROUP BY/ORDER BY）、聚合函数与窗口函数、JOIN类型与优化（MAPJOIN/SMB）、视图与子查询",
            "tips": "数据倾斜处理（skew join）、向量化执行（set hive.vectorized.execution）",
            "cmds": ["SELECT ... GROUP BY", "SELECT ... OVER (PARTITION BY)", "EXPLAIN", "ANALYZE TABLE"],
        },
        9: {
            "k2": "HBase数据模型（RowKey/ColumnFamily/Column/Version）、HBase架构（Master/RegionServer/ZooKeeper）、读写流程（MemStore/StoreFile/HFile）、Shell操作与Java API",
            "tips": "RowKey设计原则（散列性/简短性/有序性）、布隆过滤器优化读性能",
            "cmds": ["create 't','f'", "put 't','r1','f:c1','v1'", "get 't','r1'", "scan 't'", "count 't'"],
        },
        10: {
            "k2": "Sqoop架构与工作原理、关系型数据库与HDFS/Hive/HBase互导、Sqoop导入（import）流程、Sqoop导出（export）流程、增量导入策略",
            "tips": "自由查询导入（--query）、数据压缩（--as-textfile）与并行度（-m）",
            "cmds": ["sqoop import", "--connect", "--table", "--target-dir", "--warehouse-dir", "--incremental"],
        },
        11: {
            "k2": "Kafka架构（Broker/Topic/Partition/Replica）、生产者（Producer）与消费者（Consumer）、偏移量（Offset）与消费组、分区策略与副本机制",
            "tips": "消息顺序保证（单分区+key）、幂等性生产者（enable.idempotence=true）、消费者再均衡（rebalance）",
            "cmds": ["kafka-topics.sh --create", "kafka-console-producer.sh", "kafka-console-consumer.sh", "kafka-consumer-groups.sh"],
        },
        12: {
            "k2": "数据采集层（Sqoop/Flume/Kafka）、数据存储层（HDFS/Hive/HBase）、数据处理层（MapReduce/HiveQL/Spark）、数据可视化与分析",
            "tips": "数据仓库分层设计（ODS/DWD/DWS/ADS）、数据质量保障（空值/重复/一致性）、作业调度（Oozie/Airflow）",
            "cmds": ["Sqoop import", "Hive CREATE TABLE ... STORED AS PARQUET", "Spark SQL", "Azkaban job.dag"],
        },
    }

    s = sections[num]
    k2 = s["k2"]
    tips = s["tips"]
    cmds = s["cmds"]

    return f"""# {title}学习手册

## 一、任务类型

本关卡为{title}的理论与实践练习，重点掌握{title}的核心概念、架构原理及常用操作。通过本关卡的学习，你将能够理解{title}的工作机制，熟练使用相关命令完成数据处理任务，并掌握常见的优化技巧。

## 二、学习环境

- **运行环境**: Hadoop集群环境（HDFS/YARN/ZooKeeper已启动）
- **命令行工具**: hdfs、yarn、hive、hbase、kafka等命令（取决于关卡）
- **输入方式**: 从标准输入读取测试数据，或通过文件输入
- **输出方式**: 使用print()输出结果到标准输出
- **评分系统**: 评测程序会对比你的输出与期望结果是否完全一致

## 三、知识点讲解

### 3.1 核心概念

{title}涉及以下核心概念：

**{k2}**

### 3.2 架构原理

```python
# {title} 典型使用示例
# {cmds[0]}
# 根据具体关卡不同，代码示例会有所变化
```

### 3.3 常用命令

```bash
# {cmds[0]}
# {cmds[1] if len(cmds) > 1 else ''}
# {cmds[2] if len(cmds) > 2 else ''}
```

### 3.4 关键参数与配置

在生产环境中使用{title}时，需要关注以下配置参数：

| 参数 | 说明 | 典型值 |
|------|------|--------|
| dfs.replication | 数据块副本数 | 3 |
| dfs.blocksize | HDFS块大小 | 128MB |
| mapreduce.map.memory.mb | Map任务内存 | 1024MB |
| yarn.nodemanager.resource.memory-mb | NodeManager总内存 | 8192MB |

## 四、常见模式与技巧

### 4.1 {tips}

在生产实践中，{tips}是必须掌握的关键技巧。

### 4.2 最佳实践

1. **数据安全**: 合理设置副本数，确保数据可靠性
2. **性能优化**: 根据数据规模调整分区数和副本策略
3. **资源管理**: 合理配置内存和CPU资源，避免资源争用
4. **监控告警**: 建立完善的监控体系，及时发现异常

### 4.3 注意事项

**需要避免的操作:**
{chr(10).join(f'- {x}' for x in to_avoid)}

## 五、评测标准

1. **正确性**: 输出结果必须与期望输出完全一致
2. **性能**: 在规定时间内完成处理
3. **代码规范**: 使用标准API，不使用废弃接口
4. **异常处理**: 妥善处理边界情况和异常输入
"""


def make_questions(num: int, title: str, difficulty: str) -> list:
    """Generate 10 questions for a stage."""
    q_templates = {
        1: [
            ("concept", "easy", "以下哪个不是Hadoop生态系统的组件?", ["A. HDFS", "B. MapReduce", "C. Spark", "D. Oracle"], "C", "Spark不是Hadoop原生组件，它是独立的大数据处理框架。"),
            ("concept", "easy", "Hadoop集群中，NameNode的主要作用是什么?", ["A. 存储数据块", "B. 管理文件系统的命名空间和块映射信息", "C. 负责任务调度", "D. 提供计算资源"], "B", "NameNode是HDFS的主节点，负责管理元数据，不存储实际数据。"),
            ("concept", "easy", "HDFS的默认副本数是多少?", ["A. 1", "B. 2", "C. 3", "D. 可配置"], "C", "HDFS默认每个数据块保存3份副本，存储在不同的DataNode上。"),
            ("concept", "easy", "ZooKeeper在Hadoop集群中的作用是什么?", ["A. 存储大数据", "B. 分布式协调服务", "C. 执行MapReduce任务", "D. 提供Web界面"], "B", "ZooKeeper提供分布式协调服务，用于NameNode选举、故障检测等。"),
            ("concept", "easy", "Hadoop支持以下哪种部署模式?", ["A. 仅本地模式", "B. 仅分布式模式", "C. 本地模式、伪分布式、完全分布式", "D. 仅云模式"], "C", "Hadoop支持本地模式（开发测试）、伪分布式（单机模拟集群）和完全分布式（生产环境）。"),
            ("concept", "easy", "Hadoop Common提供哪些基础功能?", ["A. 文件系统API", "B. RPC序列化", "C. 配置管理和日志", "D. 以上全部"], "D", "Hadoop Common提供RPC、序列化、配置管理、日志等核心基础功能。"),
            ("concept", "easy", "启动Hadoop集群的命令是?", ["A. start-hadoop.sh", "B. start-all.sh", "C. hadoop-start.sh", "D. bin/start.sh"], "B", "执行$sHADOOP_HOME/sbin/start-all.sh可以启动所有Hadoop守护进程。"),
            ("concept", "easy", "查看Hadoop集群状态的命令是?", ["A. hadoop status", "B. hdfs admin -report", "C. hdfs dfsadmin -report", "D. yarn report"], "C", "使用hdfs dfsadmin -report可以查看HDFS集群状态，包括DataNode信息。"),
            ("concept", "easy", "HDFS适合存储什么类型的文件?", ["A. 小文件（<1KB）", "B. 大文件（GB/TB级别）", "C. 频繁修改的文件", "D. 实时性要求高的数据"], "B", "HDFS专为存储超大文件设计，通过大块存储和流式访问提高吞吐量。"),
            ("concept", "easy", "SecondaryNameNode的作用是什么?", ["A. NameNode的热备", "B. 协助合并fsimage和edits日志", "C. 存储数据块副本", "D. 负责任务调度"], "B", "SecondaryNameNode定期合并fsimage和edits日志，帮助NameNode减轻负担。"),
        ],
        2: [
            ("concept", "easy", "HDFS中，文件数据块默认大小是?", ["A. 32MB", "B. 64MB", "C. 128MB", "D. 256MB"], "C", "Hadoop 2.x起默认Block大小为128MB，可通过dfs.blocksize配置。"),
            ("concept", "easy", "HDFS写数据的流程是?", ["A. 直接写入所有DataNode", "B. 流水线复制写入", "C. 批量写入", "D. 随机写入"], "B", "HDFS采用流水线复制：客户端依次写入管道中的DataNode，每个节点同步转发。"),
            ("concept", "easy", "查看HDFS根目录下所有文件的命令是?", ["A. hdfs ls /", "B. hdfs dfs -ls /", "C. hadoop fs -ls /", "D. hdfs dfsadmin -ls /"], "B", "使用hdfs dfs -ls /可以列出HDFS根目录下的所有文件和目录。"),
            ("concept", "easy", "HDFS文件权限检查是基于?", ["A. POSIX ACL", "B. 用户名匹配", "C. 数字UID", "D. Kerberos认证"], "B", "HDFS的权限模型与Linux类似，通过用户名和组进行权限校验。"),
            ("concept", "easy", "HDFS读取数据时，NameNode返回的是什么?", ["A. 数据块内容", "B. 数据块存储的DataNode地址列表", "C. 数据块校验和", "D. 数据块大小"], "B", "读取时NameNode返回包含该文件块的所有DataNode地址，客户端直接与DataNode通信获取数据。"),
            ("concept", "easy", "hdfs dfs -du -h /命令的作用是?", ["A. 列出目录", "B. 显示文件大小", "C. 显示目录或文件大小（人类可读）", "D. 显示磁盘使用情况"], "C", "-du显示目录或文件的磁盘使用量，-h以人类可读格式（KB/MB/GB）展示。"),
            ("concept", "easy", "SecondaryNameNode与NameNode的关系是?", ["A. 主备关系，可自动切换", "B. 独立进程，定期合并元数据", "C. 备用NameNode", "D. 没有任何关系"], "B", "SecondaryNameNode不是热备，只是定期帮助合并fsimage和editslog。"),
            ("concept", "easy", "HDFS中，副本放置策略第一副本放在?", ["A. 任意DataNode", "B. 客户端所在的节点（本地）", "C. 随机选择", "D. 固定在某个节点"], "B", "第一个副本通常放在提交写请求的客户端所在节点，减少网络开销。"),
            ("concept", "easy", "小文件问题对HDFS的影响是?", ["A. 没有影响", "B. 占用大量NameNode内存", "C. 提高存储效率", "D. 加快读写速度"], "B", "每个小文件都会产生元数据记录，大量小文件会耗尽NameNode内存。"),
            ("concept", "easy", "HDFS快照的作用是?", ["A. 备份数据到其他集群", "B. 保存文件系统在某一时刻的只读副本", "C. 压缩数据文件", "D. 同步到云存储"], "B", "HDFS快照是文件系统的只读时间点副本，用于数据恢复和备份。"),
        ],
        3: [
            ("concept", "easy", "使用HDFS Java API读取文件的步骤是?", ["A. 直接打开文件流", "B. 获取FileSystem实例 → 打开输入流 → 读取数据 → 关闭流", "C. 绕过NameNode直接读DataNode", "D. 只能使用HDFS命令读取"], "B", "标准流程：获取FileSystem → open(path)获取FSDataInputStream → 读取 → close()。"),
            ("concept", "easy", "FileSystem.get(uri, conf, user)方法中user参数的作用是?", ["A. 指定运行用户", "B. 指定HDFS版本", "C. 指定连接超时", "D. 指定缓存大小"], "A", "user参数指定以哪个Linux用户身份访问HDFS，用于权限校验。"),
            ("concept", "easy", "FSDataOutputStream和FSDataInputStream的特点是?", ["A. 都是同步的", "B. 都是装饰器流，封装底层流", "C. 只能在本地文件系统使用", "D. 不支持seek操作"], "B", "FSDataOutputStream和FSDataInputStream是装饰器流，添加了HDFS特有的位置信息和同步方法。"),
            ("concept", "easy", "HDFS写入时出现异常，需要在哪里处理?", ["A. 只在客户端处理", "B. 只在DataNode处理", "C. 客户端和DataNode都需要异常处理", "D. 不需要异常处理"], "C", "IOException可能在任何IO操作时抛出，客户端需要捕获并处理写入失败的情况。"),
            ("concept", "easy", "使用Java API创建目录的命令等价于?", ["A. hdfs dfs -mkdir", "B. hdfs dfs -touchz", "C. hdfs dfs -chmod", "D. hdfs dfsadmin"], "A", "FileSystem.mkdirs()等价于hdfs dfs -mkdir命令。"),
            ("concept", "easy", "HDFS Java API中Configuration类的作用是?", ["A. 存储文件内容", "B. 加载Hadoop配置文件（hdfs-site.xml等）", "C. 管理用户认证", "D. 调度任务"], "B", "Configuration加载XML配置文件，获取HDFS相关参数。"),
            ("concept", "easy", "HDFS写入流程中，第三个副本放置在哪里?", ["A. 与第一个副本相同机架", "B. 与第二个副本相同机架", "C. 与前两个副本不同机架", "D. 随机放置"], "C", "为保证容错，第三个副本通常放在与前两个不同的机架上。"),
            ("concept", "easy", "HDFS Java API中追加写入使用哪个方法?", ["A. create()", "B. append()", "C. write()", "D. open()"], "B", "append()方法用于在已有文件末尾追加数据。"),
            ("concept", "easy", "使用FileSystem.delete()删除文件时，第二个参数表示?", ["A. 是否强制删除", "B. 是否递归删除目录", "C. 是否跳过回收站", "D. 是否异步删除"], "B", "delete(path, recursive)中的recursive参数为true时，删除目录及其下所有文件。"),
            ("concept", "easy", "HDFS文件操作的权限异常是?", ["A. AccessControlException", "B. IOException", "C. FileNotFoundException", "D. SocketTimeoutException"], "A", "当用户没有足够权限访问文件时，会抛出AccessControlException。"),
        ],
        4: [
            ("concept", "easy", "MapReduce的核心思想是?", ["A. 递归调用", "B. 分而治之", "C. 循环迭代", "D. 贪心算法"], "B", "MapReduce将大任务分解为小任务分别处理，再合并结果，即分而治之。"),
            ("concept", "easy", "MapReduce中，Map函数的输入是?", ["A. 整个文件", "B. 每行数据作为一个key-value对", "C. 所有数据聚合后输入", "D. 用户自定义"], "B", "默认情况下，TextInputFormat将每行文本作为一条记录，key为行偏移量，value为行内容。"),
            ("concept", "easy", "Combiner的作用是?", ["A. 增加数据量", "B. 在Map端做本地Reduce，减少网络传输", "C. 替代Reduce阶段", "D. 排序数据"], "B", "Combiner在Map端做本地聚合，减少溢写次数和网络传输量。"),
            ("concept", "easy", "Partitioner的作用是?", ["A. 合并数据", "B. 决定每条记录应该交给哪个Reduce处理", "C. 排序数据", "D. 过滤数据"], "B", "Partitioner根据key的hash值决定记录发送到哪个分区，默认使用HashPartitioner。"),
            ("concept", "easy", "Shuffle阶段的主要工作是?", ["A. 执行Map逻辑", "B. 将Map输出传输到Reduce，包括分区、排序、合并", "C. 写入HDFS", "D. 创建Job"], "B", "Shuffle将Map输出按照分区收集、排序、合并后传输给对应的Reduce。"),
            ("concept", "easy", "MapReduce中，key的相等性判断用于?", ["A. 分区计算", "B. 分组和排序", "C. 数据压缩", "D. 任务调度"], "B", "key的hashCode()用于分区，equals()用于分组和排序比较。"),
            ("concept", "easy", "一个MapReduce Job由什么组成?", ["A. 多个Mapper", "B. 多个Reducer", "C. 一个Job调度，管理多个Map和Reduce任务", "D. 一个主程序"], "C", "Job由一个ApplicationMaster管理，内含多个Map Task和Reduce Task。"),
            ("concept", "easy", "推测执行机制的作用是?", ["A. 加快Job提交", "B. 当某个Task执行过慢时，启动备份任务", "C. 优化内存使用", "D. 减少Map数量"], "B", "推测执行在检测到Task执行明显慢于预期时，在其他节点启动相同任务，取先完成的结果。"),
            ("concept", "easy", "MapReduce中，Context.write()的作用是?", ["A. 写入文件", "B. 输出key-value对给后续阶段", "C. 打印日志", "D. 关闭任务"], "B", "Context.write(key, value)将Map或Reduce的输出写入到指定的输出路径。"),
            ("concept", "easy", "MapReduce 2.x与1.x的主要区别是?", ["A. 编程模型变了", "B. YARN替代了JobTracker，ResourceManager负责资源管理", "C. 不再支持MapReduce", "D. 去掉了Reduce阶段"], "B", "MRv2引入YARN，将资源管理与任务调度分离，ResourceManager管理集群资源，ApplicationMaster管理单个Job。"),
        ],
        5: [
            ("concept", "easy", "Hadoop streaming支持哪些语言?", ["A. 仅Java", "B. 任何可读标准输入/写标准输出的语言", "C. 仅Python", "D. 仅Scala"], "B", "Streaming使用标准输入输出作为Map/Reduce的接口，任何语言都可以实现。"),
            ("concept", "easy", "Hadoop streaming中，-mapper参数的作用是?", ["A. 指定输入文件", "B. 指定Map阶段的执行命令或脚本", "C. 指定输出目录", "D. 指定Reduce数量"], "B", "-mapper指定Map任务的执行命令，streaming通过调用该命令处理输入数据。"),
            ("concept", "easy", "二次排序解决的是什么问题?", ["A. 加快Map速度", "B. 在Reduce阶段对key内的多个字段进行排序", "C. 减少Reduce数量", "D. 优化网络传输"], "B", "二次排序通过自定义SortComparator，实现对key内的组合字段进行优先级排序。"),
            ("concept", "easy", "分布式缓存（DistributedCache）用于?", ["A. 存储中间结果", "B. 分发小体积的只读文件给所有Map/Reduce任务", "C. 增加存储空间", "D. 缓存查询结果"], "B", "DistributedCache在Job启动时将小文件（词典、配置文件等）复制到各节点本地。"),
            ("concept", "easy", "计数器（Counters）的作用是?", ["A. 统计代码行数", "B. 在Job运行时统计自定义指标", "C. 限制任务执行时间", "D. 统计文件数量"], "B", "Counters用于在Map/Reduce过程中统计各种指标，如特定条件的记录数。"),
            ("concept", "easy", "Map端Join（MAPJOIN）的优势是?", ["A. 需要Reduce阶段", "B. 将小表加载到内存，在Map端直接完成连接", "C. 需要排序", "D. 只能用于等值连接"], "B", "MAPJOIN将小表缓存在内存中，Map端直接完成join，避免shuffle过程。"),
            ("concept", "easy", "Hadoop streaming中，使用Python时，sys.stdin读取的是什么?", ["A. HDFS文件内容", "B. 每行数据", "C. JSON格式数据", "D. 序列化对象"], "B", "Streaming框架将HDFS上的数据按行传递给stdin，每行作为一条输入记录。"),
            ("concept", "easy", "Reduce端Join的缺点是?", ["A. 需要Map阶段", "B. 所有参与join的表都需要经过Shuffle，网络开销大", "C. 不支持多表连接", "D. 需要自定义Partitioner"], "B", "Reduce端join需要将所有表的数据shuffle到Reduce，网络开销大，可能造成数据倾斜。"),
            ("concept", "easy", "Writable接口的作用是?", ["A. 定义MapReduce任务", "B. 自定义数据类型实现序列化/反序列化", "C. 定义文件操作", "D. 实现网络通信"], "B", "Writable接口定义了write()和readFields()方法，用于MR中数据的序列化和反序列化。"),
            ("concept", "easy", "Hadoop streaming中，多个Reducer的输出是什么结构?", ["A. 合并为一个文件", "B. 每个Reducer输出一个part-xxxxx文件", "C. 按key分组输出", "D. 压缩为单个文件"], "B", "每个Reducer输出一个文件，命名为part-r-xxxxx，其中xxxxx为分区号。"),
        ],
        6: [
            ("concept", "easy", "YARN中，ResourceManager的主要职责是?", ["A. 存储数据", "B. 集群资源管理与任务调度", "C. 执行具体的Map/Reduce任务", "D. 管理文件系统"], "B", "ResourceManager是YARN的主节点，负责整个集群的资源管理和作业调度。"),
            ("concept", "easy", "YARN中Container的概念是?", ["A. Docker容器", "B. 封装了CPU、内存等资源的运行单元", "C. 一个完整的Hadoop集群", "D. 存储数据的单元"], "B", "Container是YARN中的资源分配单位，封装了CPU、内存等资源，任务在Container中运行。"),
            ("concept", "easy", "YARN的三种调度器中，哪个支持多租户资源隔离?", ["A. FIFO", "B. Capacity", "C. Fair", "D. 所有调度器都支持"], "B", "Capacity调度器为每个队列分配独立容量，实现多租户资源隔离。"),
            ("concept", "easy", "YARN与MapReduce 1.x的主要区别是?", ["A. 编程模型不同", "B. YARN将资源管理与任务调度分离，支持多种计算框架", "C. HDFS架构变了", "D. 不再支持Java"], "B", "YARN将JobTracker的资源管理和任务调度职责分离，支持Spark、Tez等多种计算框架。"),
            ("concept", "easy", "NodeManager的主要职责是?", ["A. 管理NameNode", "B. 管理节点上的计算资源，向ResourceManager汇报", "C. 存储数据块", "D. 调度任务"], "B", "NodeManager是YARN的工作节点，管理本节点的资源并向ResourceManager汇报。"),
            ("concept", "easy", "YARN中，ApplicationMaster的作用是?", ["A. 管理整个集群", "B. 与ResourceManager协商资源，协调单个应用程序的执行", "C. 存储配置", "D. 监控HDFS"], "B", "ApplicationMaster为每个应用程序（Job）运行，负责向RM申请资源、协调任务执行。"),
            ("concept", "easy", "FIFO调度器的特点是?", ["A. 公平分配资源", "B. 按提交顺序先后调度，先进先出", "C. 按用户分配资源", "D. 动态分配资源"], "B", "FIFO调度器按作业提交顺序调度，先提交的作业优先获得资源。"),
            ("concept", "easy", "Capacity调度器中，队列的capacity属性表示?", ["A. 队列中的任务数量上限", "B. 队列可以使用的集群资源比例", "C. 队列的最大优先级", "D. 队列的最小内存"], "B", "capacity定义队列可以使用的集群资源百分比，各队列capacity之和可以小于100%。"),
            ("concept", "easy", "yarn application -list命令的作用是?", ["A. 列出所有文件", "B. 列出所有运行中的YARN应用程序", "C. 列出所有队列", "D. 列出所有节点"], "B", "yarn application -list显示当前提交的YARN应用程序及其状态。"),
            ("concept", "easy", "长作业和短作业混合运行时，推荐哪个调度器?", ["A. FIFO", "B. Capacity或Fair", "C. 只有FIFO支持混合", "D. 不支持混合"], "B", "Capacity和Fair调度器支持为长、短作业配置不同队列，实现资源隔离和公平分配。"),
        ],
        7: [
            ("concept", "easy", "Hive与传统关系型数据库的主要区别是?", ["A. Hive使用SQL查询但底层是MapReduce/Spark", "B. Hive不支持SQL", "C. Hive实时性更好", "D. Hive不支持分区"], "A", "Hive将SQL编译为MapReduce/Tez/Spark任务执行，适合大规模数据分析而非实时查询。"),
            ("concept", "easy", "Hive中，EXTERNAL关键字的作用是?", ["A. 加快查询速度", "B. 创建外部表，数据不被DROP TABLE删除", "C. 支持事务", "D. 启用压缩"], "B", "外部表的数据由用户管理，DROP TABLE只删除元数据，不删除实际数据文件。"),
            ("concept", "easy", "Hive分区表的作用是?", ["A. 提高写入速度", "B. 按分区字段将数据存储在不同目录，优化查询", "C. 支持事务", "D. 压缩数据"], "B", "分区表按分区字段将数据组织到不同子目录，查询时可只扫描相关分区。"),
            ("concept", "easy", "Hive的SerDe用于?", ["A. 数据压缩", "B. 序列化和反序列化行数据", "C. 数据加密", "D. 索引构建"], "B", "SerDe（Serializer/Deserializer）定义如何序列化和反序列化数据，决定了表的读写格式。"),
            ("concept", "easy", "Hive中，MAP和STRUCT是哪种数据类型?", ["A. 基本类型", "B. 复杂类型", "C. 数值类型", "D. 日期类型"], "B", "MAP、ARRAY、STRUCT是Hive的复杂类型，用于存储嵌套结构化数据。"),
            ("concept", "easy", "HiveQL中，LOAD DATA LOCAL INPATH的作用是?", ["A. 从HDFS加载数据到表", "B. 从本地文件系统加载数据到表", "C. 复制数据文件", "D. 创建视图"], "B", "LOAD DATA LOCAL INPATH从本地文件复制数据到Hive表对应目录。"),
            ("concept", "easy", "Hive分桶表（CLUSTERED BY）的作用是?", ["A. 加快数据导入", "B. 将数据按字段哈希分成多个桶，优化采样和连接", "C. 压缩数据", "D. 分区的一种"], "B", "分桶表将数据按字段哈希分成多个桶，常用于采样和高效连接（SMB Join）。"),
            ("concept", "easy", "Hive Driver的作用是?", ["A. 执行MapReduce", "B. 编译SQL、解析执行计划、管理生命周期", "C. 存储元数据", "D. 管理HDFS"], "B", "Hive Driver负责SQL编译、解析、优化和执行计划管理，是Hive的核心组件。"),
            ("concept", "easy", "Hive中，查看表结构的命令是?", ["A. SHOW TABLES", "B. DESC [FORMATTED] table_name", "C. SELECT *", "D. EXPLAIN"], "B", "DESC FORMATTED table_name显示表的详细结构信息，包括列、分区、存储信息等。"),
            ("concept", "easy", "Hive内部表与外部表DROP时的区别是?", ["A. 没有区别", "B. 内部表删除数据和元数据，外部表只删除元数据", "C. 外部表删除数据和元数据", "D. 只有内部表支持DROP"], "B", "DROP内部表会删除元数据和HDFS数据文件；DROP外部表只删除元数据，数据保留。"),
        ],
        8: [
            ("concept", "easy", "HiveQL中，GROUP BY和PARTITION BY的区别是?", ["A. 没有区别", "B. GROUP BY聚合数据，PARTITION BY不聚合", "C. PARTITION BY用于排序", "D. GROUP BY只用于数字列"], "B", "GROUP BY对数据进行聚合计算，PARTITION BY在窗口函数中分组但不减少行数。"),
            ("concept", "easy", "Hive窗口函数中，OVER()的作用是?", ["A. 定义窗口的边界和计算方式", "B. 过滤数据", "C. 连接表", "D. 创建视图"], "A", "OVER()定义窗口的分区、排序和框架规则，决定了窗口函数计算的范围。"),
            ("concept", "easy", "数据倾斜是指?", ["A. 数据从HDFS读取", "B. 数据在各个节点分布不均匀，部分节点处理数据量远大于其他节点", "C. 数据压缩", "D. 数据格式错误"], "B", "数据倾斜导致部分Reduce处理数据量远超其他Reduce，成为性能瓶颈。处理方法包括加盐、开启skew join等。"),
            ("concept", "easy", "Hive中，EXPLAIN命令的作用是?", ["A. 执行查询", "B. 显示查询执行计划", "C. 统计表大小", "D. 创建索引"], "B", "EXPLAIN显示HiveQL编译后的物理执行计划，用于分析和优化查询。"),
            ("concept", "easy", "Hive中，向量化执行（Vectorization）的作用是?", ["A. 支持向量化数据类型", "B. 按批处理数据而非逐行，提高CPU缓存命中率", "C. 加快数据加载", "D. 压缩存储"], "B", "向量化执行一次处理1024行数据，利用CPU SIMD指令提升性能。"),
            ("concept", "easy", "Hive中，SMB Join（SMB Map Join）适用于什么场景?", ["A. 大表与大表Join", "B. 小表与大表Join，两表均按Join Key分桶", "C. 表内聚合", "D. 子查询优化"], "B", "SMB Join要求两表都按Join Key分桶，小表加载到内存，Map端完成Join。"),
            ("concept", "easy", "Hive窗口函数中，ROW_NUMBER、RANK、DENSE_RANK的区别是?", ["A. 没有区别", "B. 处理并列排名的方式不同", "C. RANK最快", "D. 只支持ROW_NUMBER"], "B", "ROW_NUMBER不重复、RANK有间隙、DENSE_RANK无间隙，处理并列数据的方式不同。"),
            ("concept", "easy", "Hive中，ANALYZE TABLE的作用是?", ["A. 分析查询性能", "B. 收集表统计信息，帮助优化器生成更优计划", "C. 删除重复数据", "D. 压缩表"], "B", "ANALYZE TABLE收集表的统计信息（行数、文件数等），供查询优化器使用。"),
            ("concept", "easy", "Hive中，COALESCE函数的作用是?", ["A. 连接字符串", "B. 返回参数中第一个非NULL值", "C. 统计行数", "D. 去重"], "B", "COALESCE(v1, v2, ...)返回第一个非NULL的值，常用于赋默认值。"),
            ("concept", "easy", "Hive子查询中，以下哪个必须加别名?", ["A. FROM子句中的子查询", "B. SELECT中的标量子查询", "C. WHERE中的IN子查询", "D. GROUP BY中的子查询"], "A", "FROM子句中的子查询必须加别名，Hive要求派生表必须有名称。"),
        ],
        9: [
            ("concept", "easy", "HBase数据模型中，RowKey的作用是?", ["A. 列族名称", "B. 唯一标识一行数据，决定数据存储顺序", "C. 版本号", "D. 时间戳"], "B", "RowKey是HBase中一行的主键，按字典序排序，决定了数据的物理存储位置。"),
            ("concept", "easy", "HBase中，列族（ColumnFamily）的特点是?", ["A. 每行都有相同的列", "B. 同一列族的数据存储在一起，物理上连续", "C. 列族可以动态增加", "D. 列族不占用存储空间"], "B", "HBase按列族存储数据，同一列族的所有列数据物理上相邻存储于HFile中。"),
            ("concept", "easy", "HBase架构中，ZooKeeper的作用是?", ["A. 存储数据", "B. 协调管理、选举主节点、传递元数据", "C. 执行MapReduce", "D. 提供SQL接口"], "B", "ZooKeeper维护HBase集群的元数据、根表位置，负责Master选举和协调。"),
            ("concept", "easy", "HBase写入流程中，数据首先写入哪里?", ["A. HFile", "B. MemStore（内存）", "C. ZooKeeper", "D. HDFS"], "B", "HBase写入时先写入MemStore（内存），异步刷写到HFile，提高写入性能。"),
            ("concept", "easy", "HBase读取数据时，查找顺序是?", ["A. MemStore → HFile → BlockCache", "B. BlockCache → MemStore → HFile", "C. HFile → MemStore → BlockCache", "D. 直接读HFile"], "B", "读取优先查BlockCache（缓存热点数据），再查MemStore（最近写入），最后查HFile。"),
            ("concept", "easy", "HBase中，布隆过滤器（BloomFilter）的作用是?", ["A. 加密数据", "B. 快速判断某个Key是否可能存在于HFile中，减少IO", "C. 压缩数据", "D. 排序数据"], "B", "BloomFilter通过位数组快速判断数据不存在，避免不必要的HFile扫描，提高读性能。"),
            ("concept", "easy", "HBase RowKey设计应避免?", ["A. 随机字符串", "B. 顺序递增的ID（如时间戳）导致热点写入", "C. 短小精悍", "D. 哈希打散"], "B", "顺序递增RowKey导致所有写入集中在同一RegionServer，造成热点写入问题。"),
            ("concept", "easy", "HBase中，scan命令获取多行数据的命令是?", ["A. get 't','r1'", "B. scan 't', {COLUMNS => 'f:c'}", "C. put 't'", "D. delete 't'"], "B", "scan用于范围扫描，可以指定STARTROW、ENDROW、LIMIT等参数获取多行数据。"),
            ("concept", "easy", "HBase中，一个列可以存储多个版本是通过什么实现的?", ["A. 多个Column", "B. 不同的timestamp（时间戳）", "C. 不同的RowKey", "D. 不同的表"], "B", "HBase同一单元格通过不同时间戳存储多个版本，读取时可指定版本数。"),
            ("concept", "easy", "HBase的StoreFile（HFile）是在哪里产生的?", ["A. 直接从客户端写入", "B. MemStore刷写（flush）时生成", "C. ZooKeeper生成", "D. RegionServer启动时生成"], "B", "当MemStore内存达到阈值时，会刷写生成HFile，持久化到HDFS。"),
        ],
        10: [
            ("concept", "easy", "Sqoop的主要用途是?", ["A. 在HDFS和关系型数据库之间传输数据", "B. 压缩数据", "C. 实时流处理", "D. 数据清洗"], "A", "Sqoop是Hadoop与传统关系型数据库之间的数据传输工具，支持import和export。"),
            ("concept", "easy", "Sqoop import默认将数据导入到HDFS哪个目录?", ["A. /user/root/表名", "B. /sqoop/表名", "C. /tmp/表名", "D. /data/表名"], "A", "Sqoop默认将数据导入到HDFS的/user/<user>/<table-name>目录下。"),
            ("concept", "easy", "Sqoop增量导入的模式有?", ["A. 仅append模式", "B. append模式和lastmodified模式", "C. 仅lastmodified模式", "D. 实时模式"], "B", "Sqoop支持append（基于自增ID）和lastmodified（基于时间戳）两种增量导入策略。"),
            ("concept", "easy", "Sqoop中，--as-avrodatafile选项表示?", ["A. 导入为文本文件", "B. 导入为Avro格式文件", "C. 导入为SequenceFile", "D. 导入为Parquet格式"], "B", "Sqoop支持多种导入格式，Avro是自描述的二进制格式，支持压缩和schema演进。"),
            ("concept", "easy", "Sqoop export中，目标表必须先?", ["A. 截断", "B. 创建并定义正确的列和数据类型", "C. 导入数据", "D. 设置主键"], "B", "Sqoop export要求目标表已存在，且列类型与导入数据匹配。"),
            ("concept", "easy", "Sqoop中，--query参数的作用是?", ["A. 指定表名", "B. 使用SQL自由查询导入，满足更灵活的数据抽取需求", "C. 指定列名", "D. 指定目标目录"], "B", "--query允许指定任意SQL查询，可做字段筛选、条件过滤和多表关联。"),
            ("concept", "easy", "Sqoop并行导入是通过什么实现的?", ["A. 多线程", "B. 指定-m或--num-mappers参数启动多个Map Task", "C. Spark", "D. FIFO调度"], "B", "通过-m参数指定Mapper数量，每个Mapper处理数据的一个子集，实现并行导入。"),
            ("concept", "easy", "Sqoop的direct模式的优点是?", ["A. 支持所有数据库", "B. 使用数据库原生批量导出工具，更高效", "C. 不需要数据库驱动", "D. 支持事务"], "B", "direct模式使用MySQL mysqldump和PostgreSQL pg_dump等原生工具，性能优于JDBC方式。"),
            ("concept", "easy", "Sqoop在导入时指定--null-string '\\\\N'的作用是?", ["A. 空字符串用\\N表示，便于后续处理", "B. 压缩数据", "C. 加密数据", "D. 指定编码"], "A", "Sqoop导入时将NULL值转换为\\N，导出时反向转换，保证NULL值的正确处理。"),
            ("concept", "easy", "Sqoop job的作用是?", ["A. 创建数据管道", "B. 保存增量导入的参数配置，方便重复执行", "C. 调度任务", "D. 监控数据质量"], "B", "Sqoop job保存import/export任务的配置和状态信息（检查点），方便后续重复执行增量导入。"),
        ],
        11: [
            ("concept", "easy", "Kafka中，Topic的作用是?", ["A. 存储消息", "B. 按主题分类管理消息，每类消息一个Topic", "C. 用户认证", "D. 数据压缩"], "B", "Topic是Kafka中消息的逻辑分类，生产者向Topic发送消息，消费者从Topic消费。"),
            ("concept", "easy", "Kafka中，Partition的作用是?", ["A. 备份数据", "B. 实现并行处理和水平扩展，每个Partition有序但Topic整体不一定有序", "C. 压缩消息", "D. 存储元数据"], "B", "Partition是Topic的物理分区，每个Partition可独立消费，实现并行处理和水平扩展。"),
            ("concept", "easy", "Kafka消费者组（Consumer Group）的作用是?", ["A. 管理用户权限", "B. 组内消费者负载均衡消费同一Topic的不同Partition", "C. 备份数据", "D. 存储配置"], "B", "同一Consumer Group内的消费者共同消费一个Topic，各消费不同Partition，实现负载均衡。"),
            ("concept", "easy", "Kafka中，Offset的作用是?", ["A. 消息大小", "B. 记录消费者在Partition中的消费位置", "C. 分区编号", "D. 时间戳"], "B", "Offset是Consumer在Partition中的消费进度标识，提交Offset表示已成功消费到该位置。"),
            ("concept", "easy", "Kafka的消息持久化机制是?", ["A. 存储在内存中", "B. 顺序写入磁盘文件，通过OS缓存加速", "C. 不做持久化", "D. 压缩后存储"], "B", "Kafka将消息追加写入磁盘文件，顺序IO性能高，通过OS PageCache缓存提高读写速度。"),
            ("concept", "easy", "Kafka生产者的分区策略中，指定key的作用是?", ["A. 加密消息", "B. 决定消息发送到哪个Partition（相同key发送到同一Partition）", "C. 设置优先级", "D. 指定编码"], "B", "Producer使用key的hash决定分区，相同key的消息保证有序且发送到同一Partition。"),
            ("concept", "easy", "Kafka的副本（Replica）机制用于?", ["A. 数据压缩", "B. 数据冗余备份，提高容错能力", "C. 加快消费速度", "D. 数据加密"], "B", "Kafka每个Partition有多个副本分布在不同Broker，实现数据冗余，提高可用性。"),
            ("concept", "easy", "Kafka中，ISR（In-Sync Replicas）是指?", ["A. 所有副本", "B. 与Leader保持同步的副本集合", "C. 异步复制的副本", "D. 备份副本"], "B", "ISR是与Leader保持同步的副本集合，只有ISR中的副本才能被选为新Leader。"),
            ("concept", "easy", "Kafka消费者的再均衡（Rebalance）是?", ["A. 重新压缩数据", "B. Consumer Group成员变化时重新分配Partition归属", "C. 重启集群", "D. 清理过期消息"], "B", "当Consumer加入或离开Group时，触发Rebalance重新分配Partition，可能导致短暂消费暂停。"),
            ("concept", "easy", "Kafka幂等性生产者（idempotent producer）的作用是?", ["A. 加快发送速度", "B. 保证单次发送不会因重试产生重复消息", "C. 减少网络带宽", "D. 支持更多分区"], "B", "启用幂等性后，Producer为每个PID+序列号组合分配唯一消息ID，Broker端自动去重。"),
        ],
        12: [
            ("concept", "easy", "数据仓库分层中，ODS层的作用是?", ["A. 数据分析报表", "B. 原始数据层，保持数据原貌，不做清洗", "C. 聚合汇总层", "D. 数据质量监控"], "B", "ODS（Operational Data Store）是原始数据层，存放各源系统的原始数据，作为数据加工的起点。"),
            ("concept", "easy", "数据仓库分层中，DWD层是?", ["A. 原始数据层", "B. 明细数据层，对ODS层数据进行清洗和规范化", "C. 应用数据层", "D. 实时数据层"], "B", "DWD（Data Warehouse Detail）是明细数据层，进行数据清洗、脱敏、规范化处理。"),
            ("concept", "easy", "数据质量保障的主要检查项包括?", ["A. 数据压缩率", "B. 完整性（空值/重复）、一致性、时效性、准确性", "C. 数据格式", "D. 存储空间"], "B", "数据质量检查包括：完整性（空值/重复/null）、一致性（跨表/跨字段）、时效性、准确性。"),
            ("concept", "easy", "ELT和ETL的主要区别是?", ["A. 没有区别", "B. ETL先转换再加载，ELT先加载到数据仓库再转换", "C. ELT不支持转换", "D. ETL不支持清洗"], "B", "ETL在抽取后先转换再加载，ELT先加载原始数据再在数据仓库内用SQL转换。"),
            ("concept", "easy", "数据可视化中，常见的图表类型对应关系是?", ["A. 趋势分析用饼图", "B. 趋势分析用折线图，对比用柱状图，分布用直方图，关系用散点图", "C. 所有数据用柱状图", "D. 占比用折线图"], "B", "不同分析目的使用不同图表：趋势用折线图，对比用柱状图，占比用饼图，分布用直方图，关系用散点图。"),
            ("concept", "easy", "作业调度系统中，Oozie的workflow用于?", ["A. 实时监控", "B. 定义有向无环图（DAG）的任务执行流程", "C. 数据存储", "D. 用户认证"], "B", "Oozie Workflow定义DAG任务流，控制任务的执行顺序、依赖和条件分支。"),
            ("concept", "easy", "数据湖（Data Lake）的特点是?", ["A. 只存储结构化数据", "B. 存储各种格式（结构化/半结构化/非结构化）的原始数据", "C. 必须使用HDFS", "D. 不支持机器学习数据"], "B", "数据湖以原始格式存储各种类型的数据，保留数据全量，支持多种分析场景。"),
            ("concept", "easy", "Lambda架构的组成部分包括?", ["A. 仅批处理层", "B. 批处理层（Batch Layer）+ 实时层（Speed Layer）+ 服务层（Serving Layer）", "C. 仅实时层", "D. 存储层和计算层"], "B", "Lambda架构通过批处理层保证数据准确性，实时层提供低延迟，数据最终合并到服务层。"),
            ("concept", "easy", "数据仓库中，缓慢变化维度（SCD）的处理策略包括?", ["A. 仅覆盖更新", "B. 类型1（覆盖）、类型2（新增行）、类型3（新增列）", "C. 不处理", "D. 仅删除旧数据"], "B", "SCD处理历史变化：类型1直接覆盖，类型2保留历史新增行，类型3同时保存新旧值。"),
            ("concept", "easy", "实时数据处理中，Spark Streaming与Flink的主要区别是?", ["A. Spark Streaming是微批处理，Flink是逐条实时处理", "B. 没有区别", "C. Flink不支持容错", "D. Spark Streaming延迟更低"], "A", "Spark Streaming采用微批处理（mini-batch），延迟秒级；Flink是真正的流处理，延迟毫秒级。"),
        ],
    }

    return [
        {
            "id": f"bd{num:02d}-{i+1}",
            "type": q_templates[num][i][0],
            "difficulty": q_templates[num][i][1],
            "question": q_templates[num][i][2],
            "hint": f"参考{title}知识点",
            "options": q_templates[num][i][3],
            "answer": q_templates[num][i][4],
            "explanation": q_templates[num][i][5],
        }
        for i in range(10)
    ]


def make_test_cases(num: int, title: str) -> list:
    """Generate 6 test cases (2 visible + 4 hidden)."""
    tc_templates = {
        1: [
            {"name": "case_1", "input": "3\n2", "expected": "6", "hidden": False, "score": 10, "description": "基本整数求和"},
            {"name": "case_2", "input": "10\n20", "expected": "30", "hidden": False, "score": 10, "description": "整数求和"},
            {"name": "case_3", "input": "100\n200", "expected": "300", "hidden": True, "score": 20, "description": "较大整数求和"},
            {"name": "case_4", "input": "0\n0", "expected": "0", "hidden": True, "score": 20, "description": "边界情况0+0"},
            {"name": "case_5", "input": "-5\n10", "expected": "5", "hidden": True, "score": 20, "description": "负数求和"},
            {"name": "case_6", "input": "999999\n1", "expected": "1000000", "hidden": True, "score": 20, "description": "大整数边界"},
        ],
        2: [
            {"name": "case_1", "input": "hello world", "expected": "world hello", "hidden": False, "score": 10, "description": "单词交换"},
            {"name": "case_2", "input": "Hadoop HDFS", "expected": "HDFS Hadoop", "hidden": False, "score": 10, "description": "Hadoop组件交换"},
            {"name": "case_3", "input": "big data", "expected": "data big", "hidden": True, "score": 20, "description": "简单单词交换"},
            {"name": "case_4", "input": "one two three", "expected": "three one two", "hidden": True, "score": 20, "description": "三个单词循环"},
            {"name": "case_5", "input": "a b", "expected": "b a", "hidden": True, "score": 20, "description": "最小输入"},
            {"name": "case_6", "input": "NameNode DataNode", "expected": "DataNode NameNode", "hidden": True, "score": 20, "description": "HDFS组件"},
        ],
        3: [
            {"name": "case_1", "input": "hello", "expected": "5", "hidden": False, "score": 10, "description": "字符串长度"},
            {"name": "case_2", "input": "HDFS", "expected": "4", "hidden": False, "score": 10, "description": "HDFS长度"},
            {"name": "case_3", "input": "MapReduce", "expected": "9", "hidden": True, "score": 20, "description": "MapReduce长度"},
            {"name": "case_4", "input": "YARN", "expected": "4", "hidden": True, "score": 20, "description": "YARN长度"},
            {"name": "case_5", "input": "a", "expected": "1", "hidden": True, "score": 20, "description": "单字符"},
            {"name": "case_6", "input": "HiveQL", "expected": "6", "hidden": True, "score": 20, "description": "HiveQL长度"},
        ],
        4: [
            {"name": "case_1", "input": "cat dog", "expected": "cat 1\ndog 1", "hidden": False, "score": 10, "description": "基本词频统计"},
            {"name": "case_2", "input": "hello hello world", "expected": "hello 2\nworld 1", "hidden": False, "score": 10, "description": "重复单词统计"},
            {"name": "case_3", "input": "hadoop hadoop hadoop", "expected": "hadoop 3", "hidden": True, "score": 20, "description": "Hadoop词频"},
            {"name": "case_4", "input": "a b c", "expected": "a 1\nb 1\nc 1", "hidden": True, "score": 20, "description": "各单词出现一次"},
            {"name": "case_5", "input": "spark spark spark spark", "expected": "spark 4", "hidden": True, "score": 20, "description": "高词频"},
            {"name": "case_6", "input": "kafka kafka flink flink spark", "expected": "kafka 2\nflink 2\nspark 1", "hidden": True, "score": 20, "description": "多词频"},
        ],
        5: [
            {"name": "case_1", "input": "a b c a b", "expected": "a 2\nb 2\nc 1", "hidden": False, "score": 10, "description": "词频统计"},
            {"name": "case_2", "input": "hdfs hdfs hdfs mapreduce", "expected": "hdfs 3\nmapreduce 1", "hidden": False, "score": 10, "description": "Hadoop词频"},
            {"name": "case_3", "input": "1 2 3 1 2", "expected": "1 2\n2 2\n3 1", "hidden": True, "score": 20, "description": "数字词频"},
            {"name": "case_4", "input": "x x x x x", "expected": "x 5", "hidden": True, "score": 20, "description": "单元素高频"},
            {"name": "case_5", "input": "p y t h o n p y t h o n", "expected": "p 2\ny 2\nt 2\nh 2\no 2\nn 2", "hidden": True, "score": 20, "description": "Python等频"},
            {"name": "case_6", "input": "big big bigdata data", "expected": "big 2\nbigdata 1\ndata 1", "hidden": True, "score": 20, "description": "混合词频"},
        ],
        6: [
            {"name": "case_1", "input": "3 5", "expected": "8", "hidden": False, "score": 10, "description": "基本加法"},
            {"name": "case_2", "input": "10 20 30", "expected": "60", "hidden": False, "score": 10, "description": "三个数求和"},
            {"name": "case_3", "input": "100 200 300 400", "expected": "1000", "hidden": True, "score": 20, "description": "四个数求和"},
            {"name": "case_4", "input": "50 50 50 50 50", "expected": "250", "hidden": True, "score": 20, "description": "五个数求和"},
            {"name": "case_5", "input": "1 2", "expected": "3", "hidden": True, "score": 20, "description": "最小输入"},
            {"name": "case_6", "input": "999 1", "expected": "1000", "hidden": True, "score": 20, "description": "大数边界"},
        ],
        7: [
            {"name": "case_1", "input": "Alice\n90", "expected": "Alice: 90", "hidden": False, "score": 10, "description": "基本学生信息"},
            {"name": "case_2", "input": "Bob\n85", "expected": "Bob: 85", "hidden": False, "score": 10, "description": "学生成绩输出"},
            {"name": "case_3", "input": "Charlie\n78", "expected": "Charlie: 78", "hidden": True, "score": 20, "description": "学生成绩"},
            {"name": "case_4", "input": "David\n100", "expected": "David: 100", "hidden": True, "score": 20, "description": "满分学生"},
            {"name": "case_5", "input": "Eve\n0", "expected": "Eve: 0", "hidden": True, "score": 20, "description": "零分学生"},
            {"name": "case_6", "input": "Frank\n65", "expected": "Frank: 65", "hidden": True, "score": 20, "description": "及格线"},
        ],
        8: [
            {"name": "case_1", "input": "3 2 1", "expected": "3", "hidden": False, "score": 10, "description": "最大值"},
            {"name": "case_2", "input": "10 20 30", "expected": "30", "hidden": False, "score": 10, "description": "最大值"},
            {"name": "case_3", "input": "100 200 300 400 500", "expected": "500", "hidden": True, "score": 20, "description": "五个数最大值"},
            {"name": "case_4", "input": "50 50 50", "expected": "50", "hidden": True, "score": 20, "description": "全部相等"},
            {"name": "case_5", "input": "1 2", "expected": "2", "hidden": True, "score": 20, "description": "两个数最大"},
            {"name": "case_6", "input": "-10 -5 -1", "expected": "-1", "hidden": True, "score": 20, "description": "负数最大值"},
        ],
        9: [
            {"name": "case_1", "input": "row001 cf1 q1 v1", "expected": "row001", "hidden": False, "score": 10, "description": "基本RowKey提取"},
            {"name": "case_2", "input": "user001 age 25 1", "expected": "user001", "hidden": False, "score": 10, "description": "用户RowKey"},
            {"name": "case_3", "input": "order001 product apple 1", "expected": "order001", "hidden": True, "score": 20, "description": "订单RowKey"},
            {"name": "case_4", "input": "event001 timestamp 123456789 1", "expected": "event001", "hidden": True, "score": 20, "description": "事件RowKey"},
            {"name": "case_5", "input": "key001", "expected": "key001", "hidden": True, "score": 20, "description": "纯Key输入"},
            {"name": "case_6", "input": "session1234567890 metadata length 10", "expected": "session1234567890", "hidden": True, "score": 20, "description": "会话ID"},
        ],
        10: [
            {"name": "case_1", "input": "mysql://localhost:3306 db table", "expected": "mysql://localhost:3306", "hidden": False, "score": 10, "description": "提取JDBC URL"},
            {"name": "case_2", "input": "postgresql://localhost:5432 warehouse sales", "expected": "postgresql://localhost:5432", "hidden": False, "score": 10, "description": "PostgreSQL URL"},
            {"name": "case_3", "input": "oracle://localhost:1521 sid", "expected": "oracle://localhost:1521", "hidden": True, "score": 20, "description": "Oracle URL"},
            {"name": "case_4", "input": "jdbc:sqlserver://localhost:1433 db", "expected": "jdbc:sqlserver://localhost:1433", "hidden": True, "score": 20, "description": "SQLServer URL"},
            {"name": "case_5", "input": "sqlite:///test.db test", "expected": "sqlite:///", "hidden": True, "score": 20, "description": "SQLite URL"},
            {"name": "case_6", "input": "mongodb://localhost:27017 db coll", "expected": "mongodb://localhost:27017", "hidden": True, "score": 20, "description": "MongoDB URL"},
        ],
        11: [
            {"name": "case_1", "input": "topic001 3", "expected": "topic001-0\ntopic001-1\ntopic001-2", "hidden": False, "score": 10, "description": "基本Topic分区"},
            {"name": "case_2", "input": "events 5", "expected": "events-0\nevents-1\nevents-2\nevents-3\nevents-4", "hidden": False, "score": 10, "description": "多分区Topic"},
            {"name": "case_3", "input": "logs 2", "expected": "logs-0\nlogs-1", "hidden": True, "score": 20, "description": "两分区"},
            {"name": "case_4", "input": "metrics 10", "expected": "metrics-0\nmetrics-1\nmetrics-2\nmetrics-3\nmetrics-4\nmetrics-5\nmetrics-6\nmetrics-7\nmetrics-8\nmetrics-9", "hidden": True, "score": 20, "description": "十分区"},
            {"name": "case_5", "input": "kafka 1", "expected": "kafka-0", "hidden": True, "score": 20, "description": "单分区"},
            {"name": "case_6", "input": "clickstream 8", "expected": "clickstream-0\nclickstream-1\nclickstream-2\nclickstream-3\nclickstream-4\nclickstream-5\nclickstream-6\nclickstream-7", "hidden": True, "score": 20, "description": "八分区"},
        ],
        12: [
            {"name": "case_1", "input": "sales.csv 2023-01-01", "expected": "sales_2023-01-01.csv", "hidden": False, "score": 10, "description": "基本ETL命名"},
            {"name": "case_2", "input": "orders.csv 2023-06-15", "expected": "orders_2023-06-15.csv", "hidden": False, "score": 10, "description": "订单ETL"},
            {"name": "case_3", "input": "users.parquet 2023-03-20", "expected": "users_2023-03-20.parquet", "hidden": True, "score": 20, "description": "Parquet ETL"},
            {"name": "case_4", "input": "logs.json 2023-12-31", "expected": "logs_2023-12-31.json", "hidden": True, "score": 20, "description": "日志ETL"},
            {"name": "case_5", "input": "events.csv 2023-01-01", "expected": "events_2023-01-01.csv", "hidden": True, "score": 20, "description": "事件ETL"},
            {"name": "case_6", "input": "products.parquet 2023-09-01", "expected": "products_2023-09-01.parquet", "hidden": True, "score": 20, "description": "产品ETL"},
        ],
    }
    return tc_templates[num]


def generate_stage(num: int, yaml_path: Path) -> dict:
    with open(yaml_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    title = cfg["title"]
    kps = cfg["knowledge_points"]
    tips_list = [kp for kp in kps if kp.startswith("四")]
    to_avoid = cfg.get("topics_to_avoid", [])
    baseline = cfg.get("baseline_code_template", "")
    difficulty = cfg.get("difficulty", "beginner")

    handbook = make_handbook(num, title, kps, tips_list, to_avoid, baseline)
    questions = make_questions(num, title, difficulty)
    test_cases = make_test_cases(num, title)

    return {
        "task_id": num,
        "title": title,
        "practice_title": f"大数据关卡{num}: {title}",
        "handbook_markdown": handbook,
        "question_data": {"questions": questions},
        "test_cases": test_cases,
        "baseline_code": f"# {baseline}\n# TODO: 完成以下代码\n",
        "metadata": cfg.get("metadata", {}),
        "total_score": cfg.get("total_score", 100),
    }


PROJECT_ROOT = Path(__file__).parent.parent

def main():
    yaml_dir = PROJECT_ROOT / "content_orchestrator/stages_config/bigdata"
    out_dir = PROJECT_ROOT / "output"
    out_dir.mkdir(exist_ok=True)

    stages = []
    for yf in sorted(yaml_dir.glob("stage_*.yaml"), key=lambda p: int(p.stem.split("_")[1])):
        num = int(yf.stem.split("_")[1])
        stage = generate_stage(num, yf)
        stages.append(stage)
        print(f"Generated stage {num}: {stage['title']}")

    # Split into two files (1-6 and 7-12)
    stages_1_6 = stages[0:6]
    stages_7_12 = stages[6:12]

    f1 = out_dir / "stage_bigdata_01-06.json"
    with open(f1, "w", encoding="utf-8") as f:
        json.dump({"stages": stages_1_6}, f, ensure_ascii=False, indent=2)
    print(f"\nWritten: {f1}")

    f2 = out_dir / "stage_bigdata_07-12.json"
    with open(f2, "w", encoding="utf-8") as f:
        json.dump({"stages": stages_7_12}, f, ensure_ascii=False, indent=2)
    print(f"Written: {f2}")


if __name__ == "__main__":
    main()
