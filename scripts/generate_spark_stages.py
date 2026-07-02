#!/usr/bin/env python3
"""Generate Spark stage JSON files from YAML configs."""

import json
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def make_handbook(num: int, title: str, kps: list, tips: str, to_avoid: list, baseline: str) -> str:
    """Generate a rich handbook markdown for Spark topics."""
    k2_map = {
        1: "大数据计算框架演进、Spark核心组件（Core/SQL/Streaming/MLlib/GraphX）、Driver/Executor/Cluster Manager架构、Local/Standalone/YARN/Kubernetes部署模式",
        2: "RDD核心概念（不可变/分区/依赖）、parallelize/textFile创建RDD、map/filter/flatMap Transformation、collect/count/take/reduce Action、RDD持久化（cache/persist）",
        3: "窄依赖与宽依赖（Shuffle）、groupByKey/reduceByKey/join/sortByKey、reduceByKey与groupByKey对比、join类型（内连接/外连接/半连接）、DAG与Stage划分",
        4: "累加器原理（Driver聚合/Task写入）、Accumulator V2 API、广播变量原理（高效分发只读数据）、自定义累加器、数据倾斜Join解法",
        5: "SparkSession创建、DataFrame与RDD互转、基本SQL查询（SELECT/WHERE/GROUP BY/ORDER BY）、聚合函数/窗口函数/UDF、Spark SQL与Hive集成",
        6: "Dataset强类型API、窗口函数（rank/dense_rank/row_number）、broadcast join/sort merge join、列操作（withColumn/expr）、Parquet与JSON数据源",
        7: "批处理与流处理对比、DStream架构、StreamingContext创建、DStream Transformation（map/filter/reduceByKey）、Window操作（window/slide）、检查点机制（checkpoint）",
        8: "Structured Streaming与微批、DataFrame流式API、输入源（socket/file/kafka）、输出模式（complete/append/update）、事件时间与水印、状态管理（mapGroupsWithState）",
        9: "MLlib与ML两套API、向量与特征处理（VectorAssembler/StringIndexer）、回归与分类（LinearRegression/LogisticRegression）、聚类（KMeans/GaussianMixture）、Pipeline与交叉验证",
        10: "图计算应用场景、GraphX核心概念（VertexRDD/EdgeRDD）、Graph.fromEdges构建图、PageRank/连通分量/三角形计数算法、aggregateMessages聚合操作、Pregel API",
        11: "数据倾斜成因与解决方案、Shuffle优化（coalesce/repartition）、内存管理（堆内/堆外）、GC调优（JVM参数）、并行度设置、Kryo序列化",
        12: "电商数据处理全流程、用户行为日志分析（Spark Streaming）、订单数据分析（Spark SQL）、商品推荐（ALS协同过滤）、实时大屏（Structured Streaming）、数据仓库建模",
    }
    tips_map = {
        1: "依赖管理（spark.jars）、日志配置与调试",
        2: "惰性求值与执行计划、分区控制、避免不必要的shuffle",
        3: "pipeline化减少Shuffle、partitioner使用、选择正确的join类型",
        4: "累加器与checkpoint、广播变量版本兼容、数据倾斜综合解法",
        5: "强制类型转换、动态类型与null处理、DataFrame vs Dataset选择",
        6: "内存管理与列式存储、数据倾斜Join解法、高效SQL函数使用",
        7: "背压机制（backpressure）、状态管理、输出操作注意事项",
        8: "迟到数据处理、动态写入分区、故障恢复与exactly-once语义",
        9: "特征归一化、超参调优、模型持久化（ML Persistence）",
        10: "分区策略选择、图缓存优化、大规模图处理注意事项",
        11: "Spark UI分析、Spark Conf调参、资源动态分配",
        12: "Lambda架构、数据质量检查、结果可视化",
    }
    cmds_map = {
        1: ["spark-submit --master local[*] app.py", "spark-shell --master yarn"],
        2: ["sc.parallelize(1 to 100)", "rdd.collect()", "rdd.map(_ * 2).reduce(_ + _)"],
        3: ["rdd.groupByKey()", "rdd.reduceByKey(_ + _)", "rdd.join(other)"],
        4: ["var counter = sc.longAccumulator", "val broadcastVar = sc.broadcast(Array(1,2,3))"],
        5: ["spark.read.csv(\"path\")", "df.select(\"col\").filter(\"col > 0\")"],
        6: ["df.withColumn(\"new\", expr(\"col * 2\"))", "df.join(broadcast_df, \"key\")"],
        7: ["ssc.socketTextStream(\"localhost\", 9999)", "dstream.window(Seconds(10))"],
        8: ["spark.readStream.format(\"socket\").load()", "query.awaitTermination()"],
        9: ["new LinearRegression().setMaxIter(10).setRegParam(0.3)"],
        10: ["Graph(verts, edges)", "PageRank.runUntilConvergence()"],
        11: ["spark.sql.shuffle.partitions=200", "--conf spark.serializer=org.apache.spark.serializer.KryoSerializer"],
        12: ["SparkSession.builder.getOrCreate()", "als.fit(training)"],
    }

    k2 = k2_map.get(num, "")
    tip = tips_map.get(num, tips)
    cmds = cmds_map.get(num, [])

    return f"""# {title}学习手册

## 一、任务类型

本关卡为{title}的理论与实践练习，重点掌握{title}的核心概念、架构原理及常用操作。通过本关卡的学习，你将能够理解{title}的工作机制，熟练使用Spark相关API完成数据处理任务，并掌握常见的优化技巧。

## 二、学习环境

- **运行环境**: Spark集群环境（Standalone/YARN/Kubernetes已启动）
- **命令行工具**: spark-submit、spark-shell等
- **输入方式**: 从标准输入或文件读取测试数据
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

### 3.3 常用API

```python
# {cmds[0]}
{"# " + cmds[1] if len(cmds) > 1 else ""}
```

### 3.4 关键配置参数

在生产环境中使用{title}时，需要关注以下配置参数：

| 参数 | 说明 | 典型值 |
|------|------|--------|
| spark.master | Spark运行模式 | local[*]/yarn/k8s |
| spark.executor.memory | Executor内存 | 4g |
| spark.sql.shuffle.partitions | Shuffle分区数 | 200 |
| spark.serializer | 序列化器 | KryoSerializer |

## 四、常见模式与技巧

### 4.1 {tip}

在生产实践中，{tip}是必须掌握的关键技巧。

### 4.2 最佳实践

1. **数据安全**: 合理设置持久化级别，避免数据丢失
2. **性能优化**: 根据数据规模调整分区数和并行度
3. **资源管理**: 合理配置Executor内存和CPU，避免OOM
4. **监控告警**: 通过Spark UI分析任务执行情况

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
    """Generate 10 questions for a Spark stage."""
    q_bank = {
        1: [
            ("concept", "easy", "Spark相比Hadoop MapReduce的主要优势是?", ["A. 更廉价", "B. 中间结果内存计算，无需写磁盘，性能更高", "C. 支持更多语言", "D. 社区更大"], "B", "Spark使用内存计算模型，中间结果存储在内存中，比MapReduce需要写HDFS的磁盘IO快很多。"),
            ("concept", "easy", "Spark的Driver进程主要负责?", ["A. 执行具体任务", "B. 负责任务调度、分析RDD依赖、生成执行计划", "C. 存储数据", "D. 管理Executor"], "B", "Driver是Spark应用的入口，负责构建DAG、划分Stage、向Executor分发任务。"),
            ("concept", "easy", "Spark的standalone模式中，Cluster Manager是?", ["A. YARN", "B. Spark自带的Master节点", "C. ZooKeeper", "D. HDFS"], "B", "Standalone模式下，Spark自带Master作为Cluster Manager，负责资源管理。"),
            ("concept", "easy", "Spark Executor的主要职责是?", ["A. 调度任务", "B. 运行计算任务、存储计算结果", "C. 管理集群", "D. 编译代码"], "B", "Executor是Worker节点上的进程，负责运行Task并与Driver通信汇报结果。"),
            ("concept", "easy", "spark-shell是Spark提供的什么工具?", ["A. 作业提交工具", "B. 交互式Scala/Python REPL，支持即时编写调试Spark程序", "C. 监控工具", "D. 数据导入工具"], "B", "spark-shell是Spark的交互式Shell，可即时编写和调试Spark程序。"),
            ("concept", "easy", "spark-submit的--master参数用于指定?", ["A. 主类名", "B. Spark运行模式（local/YARN/standalone等）", "C. 输入文件", "D. Executor数量"], "B", "--master指定Spark运行模式，如local[*]、yarn、spark://host:port等。"),
            ("concept", "easy", "Spark生态中，负责流处理的是?", ["A. Spark SQL", "B. Spark Streaming", "C. MLlib", "D. GraphX"], "B", "Spark Streaming（原DStream）和Structured Streaming负责流处理场景。"),
            ("concept", "easy", "Spark作业提交后，哪个进程负责将Task分发到各Executor?", ["A. Worker", "B. Cluster Manager", "C. Driver", "D. NameNode"], "C", "Driver根据DAG和Task划分结果，通过ActorSystem或Netty将Task发送到各Executor执行。"),
            ("concept", "easy", "Spark支持的部署模式包括?", ["A. 仅本地模式", "B. Local/Standalone/YARN/Kubernetes", "C. 仅云模式", "D. 仅Mesos"], "B", "Spark支持Local（开发）、Standalone（Spark自带集群）、YARN（Hadoop集群）、Kubernetes等多种部署模式。"),
            ("concept", "easy", "Spark的ApplicationMaster运行在哪种部署模式下?", ["A. Local模式", "B. Standalone模式", "C. YARN模式", "D. Kubernetes模式"], "C", "在YARN模式下，Spark会启动ApplicationMaster来管理应用，与YARN的资源管理集成。"),
        ],
        2: [
            ("concept", "easy", "RDD的Transformation操作有什么特点?", ["A. 立即执行", "B. 惰性求值，触发Action时才真正执行", "C. 返回结果", "D. 删除数据"], "B", "RDD的Transformation是惰性的，记录依赖关系但不立即计算，只有遇到Action时才触发执行。"),
            ("concept", "easy", "创建RDD的正确顺序是?", ["A. 直接创建", "B. SparkContext.parallelize/sc.textFile → RDD", "C. 先创建DataFrame再转RDD", "D. 从数据库直接创建"], "B", "通过SparkContext的parallelize（从集合）或textFile（从文件）方法创建RDD。"),
            ("concept", "easy", "RDD的cache()和persist()方法的区别是?", ["A. 完全相同", "B. cache()默认持久化到内存，persist()可指定存储级别", "C. cache()更快", "D. persist()不能缓存"], "B", "cache()等价于persist(StorageLevel.MEMORY_ONLY)，persist()可指定MEMORY_AND_DISK等多种级别。"),
            ("concept", "easy", "RDD的map和flatMap的区别是?", ["A. map返回单值，flatMap返回多值并展平", "B. flatMap比map快", "C. map不能返回列表", "D. 没有区别"], "A", "map对每个元素返回一个结果，flatMap对每个元素返回多个结果并将结果展平为一层。"),
            ("concept", "easy", "RDD的collect()方法的作用是?", ["A. 过滤数据", "B. 将RDD所有元素收集到Driver内存中", "C. 排序数据", "D. 计数元素"], "B", "collect()将RDD所有分区数据拉回到Driver端，适用于小数据量场景，大数据慎用。"),
            ("concept", "easy", "RDD的count()和countByValue()的区别是?", ["A. 一样", "B. count()返回元素总数，countByValue()返回各值出现次数", "C. countByValue更快", "D. count返回Map"], "B", "count()返回RDD中元素的总个数，countByValue()返回一个Map统计每个不同值的出现次数。"),
            ("concept", "easy", "RDD的分区数由什么决定?", ["A. 固定为1", "B. 由数据源和parallelize参数决定，可通过repartition调整", "C. 由内存决定", "D. 由CPU决定"], "B", "RDD分区数由数据源（如HDFS块数）和parallelize显式参数决定，repartition/coalesce可调整。"),
            ("concept", "easy", "RDD的reduce()方法的返回值类型是?", ["A. RDD", "B. 单个元素（与输入元素类型相同）", "C. List", "D. Map"], "B", "reduce(f)将RDD中所有元素按f进行聚合，最终返回与元素类型相同的单个值。"),
            ("concept", "easy", "RDD是不可变的，这意味着?", ["A. 不能被删除", "B. 每次转换生成新的RDD，原始RDD不变", "C. 不能被缓存", "D. 不能被分区"], "B", "RDD是不可变数据结构，每次Transformation（如map/filter）会生成新的RDD，保证数据一致性。"),
            ("concept", "easy", "spark-submit运行时，RDD的数据默认存储在哪里?", ["A. 内存中", "B. 不存储，需要Action触发时从数据源重算", "C. HDFS上", "D. 本地磁盘"], "B", "未调用cache/persist时，RDD每次Action都从头从数据源重新计算。"),
        ],
        3: [
            ("concept", "easy", "Spark中，宽依赖（Wide Dependency）的特征是?", ["A. 子RDD每个分区只依赖父RDD一个分区", "B. 子RDD每个分区依赖父RDD多个分区，触发Shuffle", "C. 不产生Shuffle", "D. 仅发生在Map操作"], "B", "宽依赖指子RDD分区依赖父RDD多个分区，需要跨节点传输数据（Shuffle），会划分新的Stage。"),
            ("concept", "easy", "reduceByKey和groupByKey的功能区别是?", ["A. 完全一样", "B. reduceByKey在Map端预聚合，效率更高", "C. groupByKey更快", "D. reduceByKey不能做聚合"], "B", "reduceByKey在Map端先做本地聚合再Shuffle，减少网络传输量；groupByKey不做聚合，数据量大时效率低。"),
            ("concept", "easy", "Spark DAG中，Stage划分的依据是?", ["A. Action数量", "B. 遇到宽依赖时划分新的Stage", "C. RDD数量", "D. 数据大小"], "B", "Spark根据RDD依赖关系划分Stage，遇到宽依赖（Shuffle边界）就划分新的Stage。"),
            ("concept", "easy", "Spark的三种join类型中，适合大表join小表的优化方法是?", ["A. 大表放左边", "B. broadcast join（小表广播到各Executor内存）", "C. 先做filter", "D. 调整分区数"], "B", "broadcast join将小表广播到每个Executor内存中，Map端直接完成join，避免Shuffle。"),
            ("concept", "easy", "Spark中，repartition和coalesce的区别是?", ["A. 一样", "B. repartition会Shuffle可增可减分区，coalesce只减分区不Shuffle", "C. coalesce更快", "D. repartition只能减少分区"], "B", "repartition(num)会触发Shuffle，可增大或减小分区数；coalesce(num, shuffle=false)减少分区且尽量避免Shuffle。"),
            ("concept", "easy", "sortByKey的默认排序是?", ["A. 降序", "B. 升序", "C. 随机", "D. 按插入顺序"], "B", "sortByKey默认按key升序排序，可通过ascending=false设为降序。"),
            ("concept", "easy", "Spark中，join操作的输出分区数由什么决定?", ["A. 固定为1", "B. 由父RDD分区数和Partitioner决定", "C. 由数据大小决定", "D. 由key数量决定"], "B", "join输出的分区数取决于父RDD的分区数以及是否使用了相同的Partitioner。"),
            ("concept", "easy", "Spark中，内连接（inner join）和左外连接（left join）的区别是?", ["A. 没有区别", "B. 左外连接保留左表中无法匹配的记录", "C. 内连接保留所有记录", "D. 左外连接更快"], "B", "inner join只保留两边都匹配的记录；left join保留左表所有记录，右表无匹配的字段为null。"),
            ("concept", "easy", "Spark DAG的可视化工具是?", ["A. HDFS UI", "B. Spark UI", "C. YARN UI", "D. ZooKeeper UI"], "B", "Spark UI提供DAG可视化和Stage/Task执行详情，是调试Spark作业的重要工具。"),
            ("concept", "easy", "Spark中，多次使用同一个RDD时，应如何优化?", ["A. 每次重新计算", "B. 调用cache()或persist()避免重复计算", "C. 减少分区", "D. 使用更快的Action"], "B", "对被多次使用的RDD调用cache()或persist()可以缓存计算结果，避免重复计算的开销。"),
        ],
        4: [
            ("concept", "easy", "Spark累加器的主要用途是?", ["A. 存储数据", "B. 在Task中安全地向Driver聚合信息（如计数、求和）", "C. 广播数据", "D. 排序数据"], "B", "累加器让各Task安全地写、Driver端聚合，用于统计全局计数器、错误计数等。"),
            ("concept", "easy", "Spark累加器在Task端写入时，存在什么问题?", ["A. 没有问题", "B. Task可能重复执行导致累加器重复累加", "C. 数据会丢失", "D. 不能使用"], "B", "Spark的Task可能重试，同一Task的累加器写入可能执行多次，需使用幂等的累加器或确保只读一次。"),
            ("concept", "easy", "广播变量（broadcast variable）的特点包括?", ["A. 每个Task一份副本", "B. 只读变量，Executor启动时一次性分发，所有Task共享一份", "C. 每次使用都重新计算", "D. 可以修改"], "B", "广播变量在每个Executor只存储一份，各Task共享，避免重复传输大变量，减少网络开销。"),
            ("concept", "easy", "广播变量适合什么场景?", ["A. 大表", "B. 小表或配置信息等只读大变量（如字典表、配置表）", "C. 任何数据", "D. 日志数据"], "B", "广播变量适合存放小表、配置信息等只读数据，避免大表广播导致内存溢出。"),
            ("concept", "easy", "Spark中，创建广播变量的正确方式是?", ["A. new Broadcast()", "B. sc.broadcast(value)", "C. 直接赋值", "D. 广播RDD"], "B", "通过sc.broadcast(value)创建广播变量，返回一个Broadcast[T]对象，Task中用.value访问。"),
            ("concept", "easy", "广播变量在Executor中的生命周期是?", ["A. 每个Task执行时创建", "B. 在Executor启动时创建，Task结束后仍然存在", "C. 随Task结束而销毁", "D. 只存在于Driver"], "B", "广播变量在Executor中只创建一次，Task结束后仍然存在，同Executor的后续Task继续共享。"),
            ("concept", "easy", "自定义累加器需要继承哪个类?", ["A. AccumulatorV2", "B. Accumulator", "C. Counter", "D. Broadcast"], "A", "Spark 2.x使用AccumulatorV2抽象定义累加器，需实现isZero/reset/add/merge等方法。"),
            ("concept", "easy", "广播变量是否可以在Task中修改?", ["A. 可以", "B. 不可以，广播变量是只读的", "C. 可以但不建议", "D. 取决于配置"], "B", "广播变量是只读的，修改不会影响其他Task看到的值，属于未定义行为。"),
            ("concept", "easy", "Spark累加器的聚合发生在哪个进程?", ["A. Executor", "B. Driver", "C. Cluster Manager", "D. Worker"], "B", "累加器的聚合操作在Driver端进行，各Executor通过内部的累加器表向Driver报告更新。"),
            ("concept", "easy", "广播变量的大小应控制在什么范围?", ["A. 越小越好，无限制", "B. 适合放入Executor内存的大小（通常<20MB）", "C. 必须<1KB", "D. 没有限制"], "B", "广播变量存储在Executor堆内，过大的广播变量会导致内存压力，应控制在合理范围内。"),
        ],
        5: [
            ("concept", "easy", "SparkSession相比SparkContext的优势是?", ["A. 更快", "B. SparkSession统一了SparkContext/SQLContext/HiveContext，支持DataFrame/Dataset/Spark SQL", "C. 占用内存更少", "D. 社区更大"], "B", "SparkSession是Spark 2.x的统一入口，整合了SparkContext、SQLContext、HiveContext的功能。"),
            ("concept", "easy", "DataFrame与RDD的主要区别是?", ["A. DataFrame不能做转换", "B. DataFrame有schema（列名+类型），类似关系型数据库表，RDD无schema", "C. DataFrame不支持Scala", "D. RDD性能更好"], "B", "DataFrame是有schema的分布式数据集，提供列式操作；RDD是无schema的对象集合，更通用但缺少SQL优化。"),
            ("concept", "easy", "Spark SQL的Catalyst优化器的作用是?", ["A. 压缩数据", "B. 自动优化Logical Plan和Physical Plan，生成高效执行计划", "C. 调度任务", "D. 存储数据"], "B", "Catalyst根据schema信息和统计信息自动优化查询计划，如谓词下推、列裁剪等。"),
            ("concept", "easy", "DataFrame.where()和DataFrame.filter()的关系是?", ["A. 完全不同", "B. where()是filter()的别名", "C. where()不支持SQL语法", "D. filter()更快"], "B", "where()和filter()功能完全相同，where()支持类似SQL的字符串表达式语法。"),
            ("concept", "easy", "Spark SQL中，读取Parquet文件的正确方式是?", ["A. spark.read.parquet(\"path\")", "B. spark.read.format(\"parquet\").load(\"path\")", "C. 两种方式都行", "D. 只能手动读取"], "C", "spark.read.parquet()是spark.read.format(\"parquet\").load()的语法糖，两者等价。"),
            ("concept", "easy", "Spark SQL中，count()和count(列名)的区别是?", ["A. 一样", "B. count(*)包含null行，count(col)忽略null值的行", "C. count(col)包含null行", "D. count(*)更快"], "B", "count(*)统计所有行（含null），count(col)只统计该列非null的值的个数。"),
            ("concept", "easy", "Spark SQL中，groupBy后使用avg()，返回的列名是?", ["A. avg(col)", "B. avg(col)的别名可通过as()指定", "C. 总为col", "D. 随机"], "B", "avg()默认返回avg(col)，可用.as(\"avg_col\")指定别名使结果更清晰。"),
            ("concept", "easy", "DataFrame的show()方法的默认输出行数是?", ["A. 10行", "B. 20行", "C. 100行", "D. 全部数据"], "B", "DataFrame.show()默认显示20行数据，show(n)可指定显示n行。"),
            ("concept", "easy", "Spark SQL中，将DataFrame注册为临时视图的作用是?", ["A. 无实际作用", "B. 通过sql()使用SQL语句查询该DataFrame", "C. 缓存数据", "D. 增加数据"], "B", "df.createOrReplaceTempView(\"v\")后可通过spark.sql(\"SELECT * FROM v\")用SQL查询。"),
            ("concept", "easy", "DataFrame写入Parquet文件时，默认分区策略是?", ["A. 不分区", "B. 按日期列分区", "C. 根据DataFrame分区自动写为目录结构", "D. 全部压缩成一个文件"], "C", "DataFrame的分区列会体现为Parquet输出的目录结构，按该列的值划分子目录。"),
        ],
        6: [
            ("concept", "easy", "Dataset[T]相比DataFrame的优势是?", ["A. 性能更好", "B. 强类型安全，编译期类型检查，IDE智能提示更完整", "C. 支持更多操作", "D. 占用内存更少"], "B", "Dataset[T]是强类型的DataFrame，编译期检查类型错误，IDE提供完整的类型提示和代码补全。"),
            ("concept", "easy", "Spark SQL窗口函数中，row_number/rank/dense_rank的区别在于?", ["A. 没有区别", "B. 处理并列排名的方式不同（无间隙/有间隙/无间隙递进）", "C. rank最快", "D. 只支持row_number"], "B", "row_number不重复，rank有间隙（1,2,2,4），dense_rank无间隙递进（1,2,2,3）。"),
            ("concept", "easy", "Spark SQL中，实现TopN查询的正确方式是?", ["A. ORDER BY + LIMIT", "B. 以上都对，ORDER BY col DESC LIMIT N是最简洁的TopN写法", "C. 必须用窗口函数", "D. 用filter"], "B", "对单分区直接用ORDER BY col DESC LIMIT N；多分区需配合窗口函数按分区排序。"),
            ("concept", "easy", "broadcast join在Spark SQL中的触发条件是?", ["A. 任何join", "B. 小表大小小于spark.sql.autoBroadcastJoinThreshold（默认10MB）", "C. 必须手动指定", "D. 大表join小表"], "B", "当小表大小小于autoBroadcastJoinThreshold时，Spark自动使用broadcast join避免Shuffle。"),
            ("concept", "easy", "DataFrame.withColumn的第三个参数（替换列）设置为true时?", ["A. 新增列", "B. 如果列名存在则替换，不存在则新增", "C. 删除列", "D. 报错"], "B", "withColumn(col, col + 1, Some(true))，第三个参数overwrite=true时替换已存在列，false时报错。"),
            ("concept", "easy", "Spark SQL中，explode函数的作用是?", ["A. 合并数组", "B. 将数组/映射类型的列展开为多行", "C. 过滤空值", "D. 聚合数据"], "B", "explode(ArrayType)将数组展开为多行，每行对应数组中的一个元素，null数组不输出任何行。"),
            ("concept", "easy", "Spark SQL中，正则替换使用的函数是?", ["A. replace()", "B. regexp_replace(col, pattern, replacement)", "C. replace(col, old, new)可处理字符串替换", "D. 所有选项均可用于字符串替换"], "D", "replace()用于精确字符串替换，regexp_replace()用于正则替换，split()用于按正则分割。"),
            ("concept", "easy", "DataFrame写入时按某列分区，用哪个参数?", ["A. partitionBy", "B. partitionBy(\"col\")", "C. 分区由DataFrame本身的分区决定", "D. 按coalesce分区"], "B", "df.write.partitionBy(\"col1\", \"col2\").parquet(\"path\")，分区列作为子目录结构写入Parquet文件。"),
            ("concept", "easy", "Spark SQL的列裁剪优化是指?", ["A. 删除空列", "B. 只读取查询涉及的列，减少IO", "C. 合并重复列", "D. 压缩列"], "B", "列裁剪（Column Pruning）在只选择部分列时，只读取相关列数据，减少不必要的IO。"),
            ("concept", "easy", "Spark SQL中，cacheTable和DataFrame.cache()的区别是?", ["A. 一样", "B. cacheTable缓存视图/表，cache()缓存DataFrame结果", "C. cacheTable更快", "D. cache()更安全"], "B", "spark.catalog.cacheTable(\"viewName\")缓存逻辑表，df.cache()缓存DataFrame实例，底层都是cacheTable。"),
        ],
        7: [
            ("concept", "easy", "Spark Streaming（原DStream）相比Structured Streaming的特点是?", ["A. 更新版本", "B. 基于微批处理模型，每个批次生成一个RDD，延迟秒级", "C. 不支持状态管理", "D. 不能与Spark SQL集成"], "B", "DStream是Spark Streaming的原始API，基于微批（mini-batch），每批生成RDD进行处理，延迟通常1秒以上。"),
            ("concept", "easy", "StreamingContext的checkpoint功能用于?", ["A. 存储数据", "B. 保存元数据和配置，实现Driver故障恢复", "C. 压缩数据", "D. 分区数据"], "B", "Checkpoint保存StreamingContext的元数据（配置、算子）和数据（已处理批次），支持Driver重启后恢复。"),
            ("concept", "easy", "Spark Streaming中，window操作的作用是?", ["A. 减少数据量", "B. 基于滑动窗口聚合多批次数据，实现跨批次统计", "C. 过滤异常数据", "D. 分区数据"], "B", "window操作定义一个时间窗口（窗口长度+滑动步长），将多个批次数据聚合进行计算，如5分钟内的访问量。"),
            ("concept", "easy", "Spark Streaming的foreachRDD的正确使用方式是?", ["A. 在Driver端执行", "B. 在Executor端执行，foreachRDD中的代码在每个批次生成的RDD上执行", "C. 不执行任何操作", "D. 只执行一次"], "B", "foreachRDD是输出操作，其中的代码在Executor上对每个批次的RDD执行，需注意创建连接对象等应在内部完成。"),
            ("concept", "easy", "Spark Streaming中，updateStateByKey的作用是?", ["A. 删除状态", "B. 在有状态算子中维护跨批次的全局状态", "C. 更新配置", "D. 过滤数据"], "B", "updateStateByKey通过回调函数维护全局状态，允许每个key的状态在批次间持续更新。"),
            ("concept", "easy", "Spark Streaming的背压机制（backpressure）的作用是?", ["A. 加快处理速度", "B. 当处理速度低于接收速度时，自动调整批次大小防止积压", "C. 减少内存使用", "D. 分区数据"], "B", "背压机制（spark.streaming.backpressure.enabled）让Spark Streaming根据实际处理能力动态调整每个批次的接收数据量。"),
            ("concept", "easy", "Spark Streaming中，socketTextStream的数据源是?", ["A. 文件", "B. 网络socket连接，将网络发送的数据作为流", "C. Kafka", "D. HDFS"], "B", "socketTextStream(host, port)监听指定TCP端口，接收网络发送的文本数据作为流输入。"),
            ("concept", "easy", "Spark Streaming批处理间隔（batch interval）设置过短会导致?", ["A. 数据丢失", "B. 每个批次处理时间小于批处理间隔变得困难，系统负载增加", "C. 延迟降低", "D. 性能提升"], "B", "批处理间隔过短，每个批次完成时间难以稳定低于间隔，可能导致批次积压和系统不稳定。"),
            ("concept", "easy", "Spark Streaming中，reduceByKeyAndWindow的作用是?", ["A. 不存在该方法", "B. 在滑动窗口内对key进行聚合操作", "C. 仅对当前批次聚合", "D. 删除key"], "B", "reduceByKeyAndWindow(func, windowDuration, slideDuration)在滑动窗口内对各key执行聚合，可高效实现窗口统计。"),
            ("concept", "easy", "Spark Streaming Receiver模式与Direct模式（以Kafka为例）的区别是?", ["A. 没有区别", "B. Receiver模式依赖WAL可能重复消费，Direct模式精确从Kafka偏移量读取", "C. Direct模式更简单", "D. Receiver模式性能更好"], "B", "Direct模式直接根据Kafka分区和偏移量读取，无需WAL，实现exactly-once语义更简单可靠。"),
        ],
        8: [
            ("concept", "easy", "Structured Streaming的核心设计思想是?", ["A. 替代Spark SQL", "B. 将流处理建模为无限增长的表，查询持续应用于输入表", "C. 只支持批处理", "D. 基于RDD"], "B", "Structured Streaming将流数据建模为不断追加的输入表，查询持续产生结果表，实现了流批一体。"),
            ("concept", "easy", "Structured Streaming的输出模式（Output Mode）中，append模式的特点是?", ["A. 输出所有结果", "B. 只输出自上次以来新增的行", "C. 更新所有行", "D. 不输出"], "B", "append模式只输出新增的行，适合只需要新结果的场景（如写入外部系统）。"),
            ("concept", "easy", "Structured Streaming的水印（Watermark）机制用于?", ["A. 加快处理速度", "B. 处理事件时间迟到数据，允许配置延迟容忍度", "C. 减少内存使用", "D. 分区数据"], "B", "Watermark定义了事件时间上的延迟边界，超过水印的迟到数据会被丢弃或更新已有状态，防止无限积累。"),
            ("concept", "easy", "mapGroupsWithState的作用是?", ["A. 替换groupBy", "B. 在分组内维护用户自定义状态并设置超时", "C. 只做分组", "D. 删除重复数据"], "B", "mapGroupsWithState允许对每个分组维护任意类型的状态，并设置超时清理不活跃分组的状态。"),
            ("concept", "easy", "Structured Streaming中，trigger的作用是?", ["A. 触发计算", "B. 指定查询的执行时机（微批/连续流/定时微批）", "C. 清理状态", "D. 分区数据"], "B", "trigger指定查询的触发模式：微批（默认）、连续流（低延迟）、定时微批（固定间隔）。"),
            ("concept", "easy", "Structured Streaming读取Parquet文件的source是?", ["A. socket", "B. rate", "C. file（目录，自动检测新文件）", "D. Kafka"], "C", "spark.readStream.format(\"parquet\").schema(s).load(\"path\")监控目录，自动处理新增Parquet文件。"),
            ("concept", "easy", "Structured Streaming中，处理迟到数据的策略包括?", ["A. 直接删除", "B. 使用Watermark过滤，或用withWatermark+join处理迟到数据", "C. 忽略所有迟到数据", "D. 报错停止"], "B", "配置withWatermark设置水印后，迟到但在水印内的数据可以更新已有状态。"),
            ("concept", "easy", "Structured Streaming的complete输出模式需要什么条件?", ["A. 任何聚合", "B. 必须使用水印", "C. 聚合查询必须包含聚合函数才能使用complete模式", "D. 禁用"], "C", "complete模式输出完整结果表，只在聚合查询中可用，需要谨慎使用以防止结果表无限增长。"),
            ("concept", "easy", "Structured Streaming的流式DataFrame可以与哪些数据源join?", ["A. 仅静态DataFrame", "B. 静态DataFrame或流式DataFrame（stream-stream join）", "C. 不能join", "D. 仅RDD"], "B", "流式DataFrame可与静态DataFrame做静态-流式join，或与另一个流式DataFrame做流-流join（需配置水印）。"),
            ("concept", "easy", "Structured Streaming中，query.awaitTermination()的作用是?", ["A. 终止查询", "B. 阻塞主线程，等待流查询运行直到手动停止或出错", "C. 启动查询", "D. 清理状态"], "B", "awaitTermination()让主线程等待流查询持续运行直到调用query.stop()或发生异常。"),
        ],
        9: [
            ("concept", "easy", "Spark MLlib（基于RDD）相比Spark ML（基于DataFrame）的区别是?", ["A. 没有区别", "B. MLlib是老API基于RDD，ML是新API基于DataFrame，支持Pipeline", "C. MLlib更快", "D. ML不支持分布式"], "B", "MLlib是1.x版本的RDD风格API，ML是2.x版本的DataFrame风格API，ML支持Pipeline更灵活。"),
            ("concept", "easy", "VectorAssembler的作用是?", ["A. 分割向量", "B. 将多个数值列合并为一个向量列，构建特征向量", "C. 计算向量范数", "D. 存储向量"], "B", "VectorAssembler将多个特征列（数值类型）合并为单个向量列，作为ML模型的输入特征。"),
            ("concept", "easy", "Spark ML中，Pipeline的工作流程是?", ["A. 直接训练", "B. 将多个转换器和估算器串联成Pipeline，统一执行训练/预测流程", "C. 手动串联", "D. 只做预测"], "B", "Pipeline将DataFrame数据经过多个Stage（Tokenizer→HashingTF→LR等），统一管理特征工程和模型训练流程。"),
            ("concept", "easy", "KMeans聚类算法中，k值的选择对结果的影响是?", ["A. 没有影响", "B. k值决定聚类数量，需根据业务和评估指标选择", "C. k越大越好", "D. k越小越好"], "B", "k值需要根据业务知识或评估指标（如轮廓系数、SSE）综合确定，k过小欠拟合，k过大过拟合。"),
            ("concept", "easy", "Spark ML中，CrossValidator的作用是?", ["A. 交叉验证数据", "B. 通过K折交叉验证评估超参数组合，选择最优参数", "C. 训练多个模型", "D. 合并模型"], "B", "CrossValidator将数据划分为K份，轮流用K-1份训练、1份验证，遍历参数网格选择最优超参数组合。"),
            ("concept", "easy", "LogisticRegression中，设置正则化参数（regParam）的作用是?", ["A. 加快训练", "B. 防止过拟合，regParam越大正则化越强", "C. 提高精度", "D. 增加特征"], "B", "正则化通过惩罚大参数防止过拟合，regParam需通过交叉验证选择，过大导致欠拟合，过小过拟合。"),
            ("concept", "easy", "Spark ML中，StringIndexer用于?", ["A. 字符串加密", "B. 将字符串类别标签转换为数值索引", "C. 分割字符串", "D. 过滤字符串"], "B", "StringIndexer将字符串类型的类别列转换为数值索引（如[cat,dog,bird]→[0.0,1.0,2.0]），供ML模型使用。"),
            ("concept", "easy", "ALS（交替最小二乘法）在Spark MLlib中用于?", ["A. 回归", "B. 协同过滤/矩阵分解，推荐系统中的评分预测", "C. 聚类", "D. 分类"], "B", "ALS将用户-物品评分矩阵分解为用户矩阵和物品矩阵，通过交替优化找到最优分解，解决推荐系统中评分预测问题。"),
            ("concept", "easy", "Spark ML模型持久化使用的方法是?", ["A. saveAsTextFile", "B. model.save(\"path\")和PipelineModel.load(\"path\")", "C. 手动保存", "D. 只能内存存储"], "B", "Spark ML通过model.save(path)和PipelineModel.load(path)持久化模型，模型保存为Parquet格式。"),
            ("concept", "easy", "Spark ML中，feature scaling（特征归一化）的作用是?", ["A. 减少内存", "B. 将特征缩放到同一量纲，加速模型收敛", "C. 增加特征", "D. 减少特征"], "B", "StandardScaler或MinMaxScaler将特征缩放到相近量纲，避免大尺度特征主导模型训练。"),
        ],
        10: [
            ("concept", "easy", "GraphX中，VertexRDD和EdgeRDD的特点是?", ["A. 与普通RDD完全相同", "B. 继承自RDD并优化了顶点数据的索引存储", "C. 只能存储字符串", "D. 不能做转换"], "B", "GraphX的VertexRDD/EdgeRDD通过哈希索引和路由表优化顶点/边数据的存储和访问。"),
            ("concept", "easy", "GraphX构建图的两种主要方式是?", ["A. 从数据库读取", "B. Graph.fromEdges(edges)和Graph(verts, edges)", "C. 只能从文件读取", "D. 必须手动创建"], "B", "fromEdges从边数据构建图（顶点自动创建），Graph(verts, edges)从顶点和边数据构建完整图。"),
            ("concept", "easy", "GraphX中，PageRank算法的用途是?", ["A. 社区发现", "B. 计算图中各顶点的重要性/权威性得分", "C. 最短路径", "D. 聚类"], "B", "PageRank通过迭代计算图中顶点的权威性得分，广泛用于网页排序、社交网络影响力分析。"),
            ("concept", "easy", "GraphX aggregateMessages的作用是?", ["A. 聚合边数据", "B. 在每个顶点上聚合其邻居消息，是图计算的基本原语", "C. 聚合顶点数据", "D. 创建新图"], "B", "aggregateMessages是GraphX的核心API，顶点通过sendMsg向邻居发送消息，aggregateMessages聚合收到的消息。"),
            ("concept", "easy", "GraphX中，Pregel API的设计思想来自?", ["A. Google MapReduce", "B. Google Pregel（ BSP模型），顶点为中心的消息传递迭代计算", "C. Spark RDD", "D. Hadoop"], "B", "Pregel借鉴BSP模型，顶点接收消息、更新状态、向邻居发消息，以同步屏障分隔超步。"),
            ("concept", "easy", "GraphX中，triplet视图（triplets）包含的信息是?", ["A. 只有边", "B. 边及其两端顶点信息的组合", "C. 只有顶点", "D. 图的元数据"], "B", "EdgeTriplet包含边及两端顶点数据，可同时访问边的属性和两端顶点属性，用于构建复杂图算法。"),
            ("concept", "easy", "GraphX连通分量（connectedComponents）算法的作用是?", ["A. 计算最短路径", "B. 找出图中所有连通子图，每个子图分配一个唯一ID", "C. 找环", "D. 聚类"], "B", "connectedComponents找出图中所有连通子图，每个子图用一个顶点ID作为标签，用于社区发现等场景。"),
            ("concept", "easy", "GraphX中，图分区的意义是?", ["A. 无意义", "B. 将图划分为多个分区到不同节点，并行计算", "C. 减少边数", "D. 合并顶点"], "B", "图分区策略（EC/Geo/随机等）决定顶点和边的分布，影响跨分区通信开销和计算并行度。"),
            ("concept", "easy", "GraphX中，mapVertices的作用是?", ["A. 删除顶点", "B. 更新顶点属性而不改变图的结构", "C. 添加顶点", "D. 分割边"], "B", "mapVertices在不改变图结构的情况下，批量更新顶点属性。"),
            ("concept", "easy", "GraphX适合处理什么规模/类型的图?", ["A. 任意图", "B. 分布式大规模图（数十亿顶点和边），不适合需要细粒度更新的图", "C. 小规模图", "D. 完全静态图"], "B", "GraphX适合处理大规模分布式图，但顶点属性更新开销较大，不适合细粒度更新的OLTP图场景。"),
        ],
        11: [
            ("concept", "easy", "Spark数据倾斜的主要成因是?", ["A. 分区数太多", "B. key分布不均匀，大量数据集中到少数几个key对应分区", "C. 数据量太少", "D. 机器太少"], "B", "数据倾斜导致少数Reduce/Partition处理数据量远超其他，是Spark作业最常见的性能问题。"),
            ("concept", "easy", "解决数据倾斜join的加盐（Salting）方法是?", ["A. 给数据加密", "B. 给热点key添加随机后缀，使数据分散到多个分区", "C. 删除热点数据", "D. 合并key"], "B", "加盐将热点key（如key=1出现100万次）扩展为key=1-0到key=1-9，在reduce端再去除后缀聚合。"),
            ("concept", "easy", "Spark的shuffle read和shuffle write发生在什么阶段?", ["A. Shuffle只在Map端发生", "B. Shuffle write在Map端写文件，Shuffle read在Reduce端读文件", "C. 只发生在Reduce端", "D. 只发生在Map端"], "B", "Shuffle write将Map端数据按分区写入磁盘文件，Shuffle read从各Mapper读取属于自己的分区数据。"),
            ("concept", "easy", "spark.sql.shuffle.partitions的默认值为多少?", ["A. 100", "B. 200", "C. 50", "D. 1"], "B", "spark.sql.shuffle.partitions默认200，控制Shuffle时的分区数，可根据数据量调整。"),
            ("concept", "easy", "Kryo序列化相比Java序列化的优势是?", ["A. 更安全", "B. 序列化速度更快、结果更紧凑", "C. 支持更多类型", "D. 可以序列化任何对象"], "B", "Kryo序列化速度比Java快10倍以上，结果体积更小，需注册KryoSerializer并注册常用类。"),
            ("concept", "easy", "Spark的堆内内存和堆外内存的区别是?", ["A. 一样", "B. 堆内由JVM管理，堆外（off-heap）由系统管理，避免GC开销", "C. 堆外更大", "D. 堆内更快"], "B", "堆外内存不受JVM GC管理，适合存储大对象避免频繁GC，可通过spark.memory.offHeap.enabled启用。"),
            ("concept", "easy", "Spark UI中，Stage的Failed和Killed Task数表示什么?", ["A. 无意义", "B. 执行失败或被kill的Task数，需要分析失败原因", "C. 正常现象", "D. 数据丢失"], "B", "大量Failed Task表示代码存在bug或资源不足；Killed Task可能是数据倾斜导致推测执行失败。"),
            ("concept", "easy", "spark.executor.memory设置的是?", ["A. 单个Executor进程的JVM堆内存上限", "B. 单个Task的内存", "C. Driver内存", "D. 总集群内存"], "A", "spark.executor.memory设置每个Executor进程的JVM堆内存上限，包含执行内存、存储内存和用户内存。"),
            ("concept", "easy", "Spark中，coalesce(1)的使用场景和风险是?", ["A. 无风险", "B. 减少分区到1（不Shuffle），适合最终输出单文件，但损失并行度", "C. 加快处理", "D. 增加并行度"], "B", "coalesce(1)不触发Shuffle直接将数据合并到1个分区，用于生成单个输出文件，但会损失并行度，小数据量时使用。"),
            ("concept", "easy", "Spark的推测执行（speculative execution）的作用是?", ["A. 加快编译", "B. 当Task执行明显慢于预期时，在其他节点启动备份任务", "C. 减少分区", "D. 压缩数据"], "B", "推测执行通过spark.speculation启用，检测掉队Task并启动备份，取先完成的结果，防止个别慢Task拖慢整个Stage。"),
        ],
        12: [
            ("concept", "easy", "Lambda架构的核心思想是?", ["A. 只有批处理", "B. 批处理层（保证准确性）+ 实时层（提供低延迟）+ 服务层（合并结果）", "C. 统一用Spark处理", "D. 替代数据仓库"], "B", "Lambda架构通过批处理层保证数据最终准确性，实时层提供分钟级延迟，服务层合并两边结果。"),
            ("concept", "easy", "电商数据处理中，用户行为日志分析的典型指标包括?", ["A. 仅PV", "B. PV/UV/会话时长/转化率/留存率等", "C. 仅UV", "D. 仅销售额"], "B", "用户行为分析涵盖访问量、会话分析、漏斗转化、留存分析等核心电商指标。"),
            ("concept", "easy", "Spark Streaming处理用户行为日志的典型流程是?", ["A. 直接输出", "B. 接收日志流→解析→实时聚合→输出到外部系统", "C. 先存HDFS再处理", "D. 人工处理"], "B", "典型流程：Kafka接收日志→Spark Streaming解析→窗口聚合→实时写入Elasticsearch/Druid等OLAP系统。"),
            ("concept", "easy", "ALS协同过滤在商品推荐中的作用是?", ["A. 分类商品", "B. 通过用户-商品评分矩阵分解，预测用户对未评分商品的喜好程度", "C. 分割用户群", "D. 聚类商品"], "B", "ALS将稀疏的用户-商品评分矩阵分解为用户特征矩阵和商品特征矩阵，内积预测未评分项的得分。"),
            ("concept", "easy", "数据仓库分层中，DWS层的作用是?", ["A. 原始数据层", "B. 汇总数据层，按主题汇总各指标", "C. 应用数据层", "D. ODS层"], "B", "DWS（Data Warehouse Summary）是汇总数据层，按业务主题汇总宽表，为上层应用提供聚合数据。"),
            ("concept", "easy", "Spark在实时大屏场景中的优势是?", ["A. 只能离线处理", "B. 通过Structured Streaming实现亚秒级延迟的实时计算", "C. 不支持可视化", "D. 延迟很高"], "B", "Structured Streaming配合连续流模式（trigger(ProcessingTime(\"100 milliseconds\"))）可实现亚秒级实时大屏。"),
            ("concept", "easy", "数据质量检查的主要内容是?", ["A. 仅完整性", "B. 完整性（空值/重复）、一致性、时效性、准确性", "C. 仅准确性", "D. 仅重复检查"], "B", "数据质量检查包括：完整性（空值/缺失）、一致性（跨表/跨字段）、时效性（数据新鲜度）、准确性（业务逻辑校验）。"),
            ("concept", "easy", "Spark在电商推荐系统中的典型架构是?", ["A. 仅离线计算", "B. 离线ALS训练推荐模型 + 实时用户行为特征更新", "C. 实时全量重算", "D. 不需要模型"], "B", "典型架构：离线用历史数据训练ALS模型生成推荐列表，实时更新用户特征，过滤已购买/已浏览商品后推送。"),
            ("concept", "easy", "Structured Streaming写入分区表时，分区字段的值来源是?", ["A. 固定值", "B. DataFrame中的列值", "C. 系统时间", "D. 手动指定"], "B", "写入时partitionBy的列值决定输出目录结构，可以是DataFrame中的日期列或处理时的时间戳列。"),
            ("concept", "easy", "电商场景中，实时风控使用Spark Streaming的作用是?", ["A. 存储数据", "B. 实时检测异常交易行为（如短时间内多次失败支付）", "C. 发送短信", "D. 生成报表"], "B", "实时风控通过Spark Streaming分析用户实时行为流，检测异常模式并触发实时拦截或告警。"),
        ],
    }

    bank = q_bank.get(num, [])
    return [
        {
            "id": f"sp{num:02d}-{i+1}",
            "type": q[0],
            "difficulty": q[1],
            "question": q[2],
            "hint": f"参考{title}知识点",
            "options": q[3],
            "answer": q[4],
            "explanation": q[5],
        }
        for i, q in enumerate(bank)
    ]


def make_test_cases(num: int, title: str) -> list:
    """Generate 6 test cases (2 visible + 4 hidden) for Spark topics."""
    tc_bank = {
        1: [
            {"name": "case_1", "input": "sc.parallelize(1 to 10)", "expected": "55", "hidden": False, "score": 10, "description": "RDD基本求和"},
            {"name": "case_2", "input": "sc.parallelize(List(2,5,3))", "expected": "10", "hidden": False, "score": 10, "description": "RDD列表求和"},
            {"name": "case_3", "input": "sc.parallelize(1 to 100)", "expected": "5050", "hidden": True, "score": 20, "description": "RDD范围求和"},
            {"name": "case_4", "input": "sc.parallelize(List())", "expected": "0", "hidden": True, "score": 20, "description": "空RDD求和"},
            {"name": "case_5", "input": "sc.parallelize(-5 to 5)", "expected": "0", "hidden": True, "score": 20, "description": "正负对称求和"},
            {"name": "case_6", "input": "sc.parallelize(List(1,2,3,4,5))", "expected": "15", "hidden": True, "score": 20, "description": "列表元素求和"},
        ],
        2: [
            {"name": "case_1", "input": "List(1,2,3).map(_ * 2).reduce(_ + _)", "expected": "12", "hidden": False, "score": 10, "description": "map+reduce"},
            {"name": "case_2", "input": "List(a,a,b,b,c).map((_,1)).reduceByKey(_+_)", "expected": "a 2 b 2 c 1", "hidden": False, "score": 10, "description": "词频统计"},
            {"name": "case_3", "input": "List(1,2,3,4).filter(_ > 2)", "expected": "3 4", "hidden": True, "score": 20, "description": "filter过滤"},
            {"name": "case_4", "input": "List(hello,hello,spark).flatMap(_.toSeq)", "expected": "h e l l o h e l l o s p a r k", "hidden": True, "score": 20, "description": "flatMap字符拆分"},
            {"name": "case_5", "input": "List(1,2,3,4).collect{case x if x%2==0 => x*10}", "expected": "20 40", "hidden": True, "score": 20, "description": "偏函数+模式匹配"},
            {"name": "case_6", "input": "List(a,b,a,c,a,b).groupBy(identity).mapValues(_.size)", "expected": "a 3 b 2 c 1", "hidden": True, "score": 20, "description": "groupBy统计"},
        ],
        3: [
            {"name": "case_1", "input": "rdd.repartition(2).getNumPartitions", "expected": "2", "hidden": False, "score": 10, "description": "repartition分区数"},
            {"name": "case_2", "input": "rdd.coalesce(1).getNumPartitions", "expected": "1", "hidden": False, "score": 10, "description": "coalesce减少分区"},
            {"name": "case_3", "input": "rdd.reduceByKey(_+_).count", "expected": "3", "hidden": True, "score": 20, "description": "reduceByKey统计key数"},
            {"name": "case_4", "input": "rdd.join(rdd).count", "expected": "4", "hidden": True, "score": 20, "description": "内连接"},
            {"name": "case_5", "input": "rdd.sortBy(x=>x,ascending=false).first", "expected": "5", "hidden": True, "score": 20, "description": "降序排序"},
            {"name": "case_6", "input": "rdd.union(rdd).distinct.count", "expected": "3", "hidden": True, "score": 20, "description": "union+distinct"},
        ],
        4: [
            {"name": "case_1", "input": "val acc=sc.longAccumulator; rdd.foreach(x=>acc.add(1)); acc.value", "expected": "5", "hidden": False, "score": 10, "description": "累加器计数"},
            {"name": "case_2", "input": "val bv=sc.broadcast(List(1,2,3)); rdd.map(x=>x+bv.value.sum).first", "expected": "7", "hidden": False, "score": 10, "description": "广播变量求和"},
            {"name": "case_3", "input": "val acc=sc.doubleAccumulator; rdd.foreach(x=>acc.add(x)); acc.value", "expected": "10.0", "hidden": True, "score": 20, "description": "double累加器"},
            {"name": "case_4", "input": "val bv=sc.broadcast(Map(a->1,b->2)); rdd.map(x=>(x,bv.value.getOrElse(x,0))).first", "expected": "(a,1)", "hidden": True, "score": 20, "description": "广播Map查询"},
            {"name": "case_5", "input": "val acc=sc.longAccumulator; rdd.filter(_>2).foreach(x=>acc.add(x)); acc.value", "expected": "7", "hidden": True, "score": 20, "description": "filter后累加"},
            {"name": "case_6", "input": "val bv=sc.broadcast(Set(1,3,5)); rdd.filter(x=>bv.value.contains(x)).count", "expected": "3", "hidden": True, "score": 20, "description": "广播Set过滤"},
        ],
        5: [
            {"name": "case_1", "input": "df.filter(col(age)>18).count", "expected": "3", "hidden": False, "score": 10, "description": "DataFrame过滤"},
            {"name": "case_2", "input": "df.groupBy(department).agg(sum(salary)).first", "expected": "IT 9000", "hidden": False, "score": 10, "description": "分组聚合"},
            {"name": "case_3", "input": "df.select(upper(name)).show", "expected": "ALICE BOB CHARLIE", "hidden": True, "score": 20, "description": "字符串转大写"},
            {"name": "case_4", "input": "df.orderBy(salary.desc).show", "expected": "Bob 8000 Charlie 6000 Alice 5000", "hidden": True, "score": 20, "description": "降序排列"},
            {"name": "case_5", "input": "df.filter(department===IT && salary>6000).count", "expected": "1", "hidden": True, "score": 20, "description": "多条件过滤"},
            {"name": "case_6", "input": "df.na.fill(Map(salary->0)).show", "expected": "all rows with salary filled", "hidden": True, "score": 20, "description": "空值填充"},
        ],
        6: [
            {"name": "case_1", "input": "df.withColumn(double_salary,salary*2).select(double_salary).first", "expected": "10000", "hidden": False, "score": 10, "description": "withColumn计算"},
            {"name": "case_2", "input": "df.join(broadcast(df2),Seq(id)).count", "expected": "5", "hidden": False, "score": 10, "description": "broadcast join"},
            {"name": "case_3", "input": "df.withColumn(year,year(date)).groupBy(year).count.show", "expected": "2023 3", "hidden": True, "score": 20, "description": "年份提取分组"},
            {"name": "case_4", "input": "df.select(regexp_replace(col,spark,SPARK)).first", "expected": "SPARK SQL", "hidden": True, "score": 20, "description": "正则替换"},
            {"name": "case_5", "input": "df.withColumn(arr,split(name,)).select(explode(arr)).count", "expected": "6", "hidden": True, "score": 20, "description": "explode数组展开"},
            {"name": "case_6", "input": "df.write.partitionBy(year).mode(Overwrite).parquet(path)", "expected": "data written by year partition", "hidden": True, "score": 20, "description": "按年分区写入"},
        ],
        7: [
            {"name": "case_1", "input": "ssc.socketTextStream(localhost,9999).map(_.split(,)).count", "expected": "stream processing initiated", "hidden": False, "score": 10, "description": "Socket流创建"},
            {"name": "case_2", "input": "dstream.window(Seconds(10)).count", "expected": "window aggregation defined", "hidden": False, "score": 10, "description": "窗口操作"},
            {"name": "case_3", "input": "dstream.updateStateByKey((v,s)=>Some(s.getOrElse(0)+v)).count", "expected": "stateful processing defined", "hidden": True, "score": 20, "description": "状态管理"},
            {"name": "case_4", "input": "dstream.transform((rdd,time)=>rdd.filter(_.nonEmpty)).count", "expected": "transform defined", "hidden": True, "score": 20, "description": "transform操作"},
            {"name": "case_5", "input": "ssc.checkpoint(hdfs://path).getState", "expected": "checkpoint enabled", "hidden": True, "score": 20, "description": "检查点启用"},
            {"name": "case_6", "input": "dstream.foreachRDD(rdd=>rdd.saveAsTextFile(path)).count", "expected": "foreachRDD defined", "hidden": True, "score": 20, "description": "输出到文件"},
        ],
        8: [
            {"name": "case_1", "input": "spark.readStream.format(socket).load().select(value).isStreaming", "expected": "true", "hidden": False, "score": 10, "description": "流式DataFrame检查"},
            {"name": "case_2", "input": "df.withWatermark(time,10 minutes).groupBy(key).count", "expected": "watermark configured", "hidden": False, "score": 10, "description": "水印配置"},
            {"name": "case_3", "input": "streamingDF.writeStream.format(parquet).option(path).outputMode(append).start", "expected": "streaming query started", "hidden": True, "score": 20, "description": "启动流查询"},
            {"name": "case_4", "input": "streamingDF.trigger(ProcessingTime(5 seconds)).start", "expected": "trigger configured", "hidden": True, "score": 20, "description": "触发器配置"},
            {"name": "case_5", "input": "query.awaitTermination(); query.status", "expected": "TERMINATED", "hidden": True, "score": 20, "description": "等待终止"},
            {"name": "case_6", "input": "staticDF.join(streamingDF,Seq(id),leftOuter).isStreaming", "expected": "true", "hidden": True, "score": 20, "description": "静态流join"},
        ],
        9: [
            {"name": "case_1", "input": "new LinearRegression().setMaxIter(10).setRegParam(0.1).fit(training)", "expected": "model trained", "hidden": False, "score": 10, "description": "线性回归训练"},
            {"name": "case_2", "input": "new KMeans().setK(3).fit(data).clusterCenters.length", "expected": "3", "hidden": False, "score": 10, "description": "KMeans聚类中心数"},
            {"name": "case_3", "input": "new StringIndexer().setInputCol(label).setOutputCol(labelIndex).fit(df).labels", "expected": "[A,B,C]", "hidden": True, "score": 20, "description": "StringIndexer标签"},
            {"name": "case_4", "input": "new Pipeline().setStages(Array(tokenizer,lr)).fit(trainDF).stages.length", "expected": "2", "hidden": True, "score": 20, "description": "Pipeline阶段数"},
            {"name": "case_5", "input": "new ALS().setRank(10).setMaxIter(5).fit(training).rank", "expected": "10", "hidden": True, "score": 20, "description": "ALS矩阵分解rank"},
            {"name": "case_6", "input": "new VectorAssembler().setInputCols(Array(x,y)).setOutputCol(features).transform(df).features", "expected": "[2.0,3.0]", "hidden": True, "score": 20, "description": "特征向量组装"},
        ],
        10: [
            {"name": "case_1", "input": "Graph(verts,edges).numVertices", "expected": "5", "hidden": False, "score": 10, "description": "图顶点数"},
            {"name": "case_2", "input": "Graph.fromEdges(edges).numEdges", "expected": "4", "hidden": False, "score": 10, "description": "图边数"},
            {"name": "case_3", "input": "graph.pageRank(0.0001).vertices.sortBy(_._2,false).take(3)", "expected": "top 3 pagerank vertices", "hidden": True, "score": 20, "description": "PageRank top3"},
            {"name": "case_4", "input": "graph.triplets.collect.map(t=>s\"${t.srcAttr}->${t.dstAttr}\")", "expected": "vertex edge triplets", "hidden": True, "score": 20, "description": "Triplet视图"},
            {"name": "case_5", "input": "graph.connectedComponents.vertices.distinct.count", "expected": "2", "hidden": True, "score": 20, "description": "连通分量数"},
            {"name": "case_6", "input": "graph.aggregateMessages(sendMsg,mergeMsg).collect.length", "expected": "edge aggregation", "hidden": True, "score": 20, "description": "聚合消息操作"},
        ],
        11: [
            {"name": "case_1", "input": "rdd.repartition(100).getNumPartitions", "expected": "100", "hidden": False, "score": 10, "description": "repartition分区数"},
            {"name": "case_2", "input": "conf.setAppName(test).setMaster(yarn).getAll", "expected": "config pairs", "hidden": False, "score": 10, "description": "SparkConf设置"},
            {"name": "case_3", "input": "sc.setLogLevel(WARN); logLevel", "expected": "WARN", "hidden": True, "score": 20, "description": "日志级别设置"},
            {"name": "case_4", "input": "spark.conf.get(spark.sql.shuffle.partitions)", "expected": "200", "hidden": True, "score": 20, "description": "默认Shuffle分区数"},
            {"name": "case_5", "input": "conf.set(spark.serializer,KryoSerializer); conf.get(spark.serializer)", "expected": "KryoSerializer", "hidden": True, "score": 20, "description": "Kryo序列化配置"},
            {"name": "case_6", "input": "rdd.coalesce(4,shuffle=true).getNumPartitions", "expected": "4", "hidden": True, "score": 20, "description": "coalesce shuffle分区数"},
        ],
        12: [
            {"name": "case_1", "input": "als.fit(training).recommendForUsers(3).count", "expected": "recommendation count", "hidden": False, "score": 10, "description": "ALS推荐生成"},
            {"name": "case_2", "input": "streamingDF.filter(event==purchase).groupBy(user).count.show", "expected": "real-time purchase aggregation", "hidden": False, "score": 10, "description": "实时购买统计"},
            {"name": "case_3", "input": "df.groupBy(user).agg(sum(amount).as(total)).orderBy(desc(total)).limit(10).show", "expected": "top 10 users by amount", "hidden": True, "score": 20, "description": "TopN用户"},
            {"name": "case_4", "input": "df.withWatermark(timestamp,1 hour).groupBy(window(time,1 hour),product).sum(quantity).show", "expected": "hourly product aggregation", "hidden": True, "score": 20, "description": "小时级聚合"},
            {"name": "case_5", "input": "als.setRank(20).setMaxIter(10).fit(train).transform(test).filter(prediction>3.5).count", "expected": "high rating prediction count", "hidden": True, "score": 20, "description": "评分预测过滤"},
            {"name": "case_6", "input": "df.write.mode(Overwrite).partitionBy(dt,hour).parquet(outputPath)", "expected": "data written with date-hour partition", "hidden": True, "score": 20, "description": "多级分区写入"},
        ],
    }
    return tc_bank.get(num, [])


def generate_stage(num: int, yaml_path: Path) -> dict:
    with open(yaml_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    title = cfg["title"]
    kps = cfg["knowledge_points"]
    tips_raw = " ".join([kp for kp in kps if kp.startswith("四")])
    tips_clean = tips_raw.replace("四、常见模式与技巧", "").strip()
    to_avoid = cfg.get("topics_to_avoid", [])
    baseline = cfg.get("baseline_code_template", "")
    difficulty = cfg.get("difficulty", "beginner")

    handbook = make_handbook(num, title, kps, tips_clean, to_avoid, baseline)
    questions = make_questions(num, title, difficulty)
    test_cases = make_test_cases(num, title)

    return {
        "task_id": num,
        "title": title,
        "practice_title": f"Spark关卡{num}: {title}",
        "handbook_markdown": handbook,
        "question_data": {"questions": questions},
        "test_cases": test_cases,
        "baseline_code": f"# {baseline}\n# TODO: 完成以下代码\n",
        "metadata": cfg.get("metadata", {}),
        "total_score": cfg.get("total_score", 100),
    }


def main():
    yaml_dir = PROJECT_ROOT / "content_orchestrator/stages_config/spark"
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

    f1 = out_dir / "stage_spark_01-06.json"
    with open(f1, "w", encoding="utf-8") as f:
        json.dump({"stages": stages_1_6}, f, ensure_ascii=False, indent=2)
    print(f"\nWritten: {f1}")

    f2 = out_dir / "stage_spark_07-12.json"
    with open(f2, "w", encoding="utf-8") as f:
        json.dump({"stages": stages_7_12}, f, ensure_ascii=False, indent=2)
    print(f"Written: {f2}")


if __name__ == "__main__":
    main()
