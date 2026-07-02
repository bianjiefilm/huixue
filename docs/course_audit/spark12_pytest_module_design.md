# Spark12 pytest_module 设计文档

日期: 2026-04-30
状态: 设计已审,实施中,未入库,未部署
目标任务: task_id=37, Spark电商数据处理项目

## 1. 学校 DB 当前实查

Phase 0 已通过:

```text
nginx /api OPTIONS /api/v1/auth/login -> 404 (非 000,路由可达)
实践_practice_rows=20
项目实训BI_rows=10
项目实训代码_rows=0
业务快照=8 课程实践 + 10 BI = 18 门
```

Spark12 当前状态:

```text
tasks.id=37
title=Spark电商数据处理项目
handbook_chars=4973
task_tests=6 rows
match_rule=exact
case_id=case_1..case_6
```

当前 6 个 exact case 本质是字符串识别:

| case | input_data | expected_output | hidden |
|---|---|---|---|
| case_1 | `0` | `recommendation count` | false |
| case_2 | `streamingDF.filter(event==purchase).groupBy(user).count.show` | `real-time purchase aggregation` | false |
| case_3 | `df.groupBy(user).agg(sum(amount).as(total)).orderBy(desc(total)).limit(10).show` | `top 10 users by amount` | true |
| case_4 | `df.withWatermark(timestamp,1 hour).groupBy(window(time,1 hour),product).sum(quantity).show` | `hourly product aggregation` | true |
| case_5 | `als.setRank(20).setMaxIter(10).fit(train).transform(test).filter(prediction>3.5).count` | `high rating prediction count` | true |
| case_6 | `df.write.mode(Overwrite).partitionBy(dt,hour).parquet(outputPath)` | `data written with date-hour partition` | true |

结论: 当前 Spark12 是 `exact` 字符串映射,不满足综合关 pytest_module 质量线。升级目标是与 MJ12 / NN12 / CV12 / WX12 / BD12 同类:1 行 `pytest_module` task_test + backend 内置 `test_spark12_comprehensive.py`。

## 2. 设计边界

### 2.1 不引入 pyspark

学校 backend musl 容器不保证 pyspark 可用,且综合关应保持和现有 5 个 pytest_module 一致的轻量执行方式。因此本关不 import pyspark,不启动 JVM,不依赖 SparkSession。
审查决策:接受。ref、test、学生模板均不得 import pyspark / pandas / numpy。

实现采用纯 Python list/dict 模拟 Spark 语义:

- RDD: list of event dicts 上的 map/filter/reduceByKey/groupByKey 思维
- DataFrame: list of dict rows + schema key 校验 + group by 聚合
- Structured Streaming: 按 `event_time` 做窗口聚合,模拟 watermark 丢弃迟到过久事件
- MLlib ALS: 用用户-商品交互表构造协同过滤式简化推荐分数,不泄露真实 ALS 公式
- 写出分区: 返回分区计划 dict,验证 partition columns 和文件分布,不写真实文件

### 2.2 与 Spark01-11 的知识边界

Spark12 只整合已有概念,不引入新算法:

| Spark12 用到 | 来源关 |
|---|---|
| RDD map/filter/reduceByKey 思维 | Spark02 / Spark03 |
| 广播变量与累加器思维 | Spark04 |
| SQL/DataFrame groupBy/agg/orderBy | Spark05 / Spark06 |
| Streaming 窗口与 watermark 思维 | Spark07 / Spark08 |
| MLlib 推荐任务概念 | Spark09 |
| 性能优化: 分区、shuffle、缓存 | Spark11 |

跨关泄题红线:

- handbook 不贴完整参考实现。
- 学生 docstring 只写函数输入输出和返回字段,不写具体算法步骤。
- 不出现后续课程算法名,不写 ALS 完整矩阵分解公式。
- 测试中可构造数据,但不把期望实现逻辑暴露进题面。

## 3. 拟替换 handbook

目标长度:约 3000-3500 中文字。结构采用 5 章,覆盖业务场景、数据流水线、RDD/DataFrame/Streaming/推荐/分区写出、评测要求。

```markdown
# Spark电商数据处理项目

## 一、项目背景

本关是 Spark 编程基础课程的综合项目。你将面对一组电商行为日志:用户浏览商品、加入购物车、下单、支付,并在不同时间产生事件。真实生产环境中,这些日志通常来自埋点系统或消息队列,会先进入离线数据湖,再进入 Spark 批处理、Spark SQL 和流式计算链路。本关不要求你启动真实 Spark 集群,而是用 Python 的 list/dict 数据结构模拟 Spark 的核心计算语义,把前面关卡学过的 RDD、DataFrame、Structured Streaming、MLlib 推荐和分区写出串成一个端到端流程。

为什么不用真实 pyspark?因为在线评测容器必须轻量、稳定、可重复。SparkSession 依赖 JVM 和集群环境,不同机器上容易出现版本和资源差异。本关关注的是 Spark 思维:如何把一批日志转换为结构化记录,如何按 key 聚合,如何处理窗口,如何根据历史行为生成推荐候选,以及如何设计落地分区。只要这些能力清楚,迁移到真实 Spark API 时就是把 list/filter/group 的思路改写成 DataFrame 或 RDD 操作。

## 二、数据模型

本关使用的电商日志是一组字典。每条记录至少包含 `user_id`、`item_id`、`event_type`、`event_time`、`amount`、`quantity`、`dt`、`hour` 等字段。`event_type` 可能是 `view`、`cart`、`purchase`、`refund`。`amount` 表示交易金额,非交易事件可以为 0。`event_time` 使用整数分钟模拟时间戳,便于窗口计算。`dt` 和 `hour` 用来模拟 Hive/Spark 常见的日期小时分区。

你需要注意三件事。第一,日志可能包含缺字段、错类型或负数金额,因此输入校验是数据流水线的第一步。第二,不是所有事件都参与同一种指标:GMV 只看 purchase,曝光量可看 view,推荐候选要综合 view/cart/purchase 权重。第三,流式窗口计算中,迟到数据不能无限保留。本关使用简化 watermark:如果事件时间早于当前最大事件时间减去 `watermark_minutes`,则视为迟到过久,不计入窗口聚合。

在真实项目里,电商日志往往会经历"采集、清洗、宽表加工、指标聚合、推荐候选、数据落盘"几个阶段。Spark 的价值不只是 API 很多,而是能把这些阶段拆成可维护的数据转换。你在本关看到的是一个缩小版流水线:先保证输入记录可信,再从事件流中抽取业务含义,最后把结果组织成下游可以继续消费的结构。请把每个函数都当作流水线里的一个稳定节点,它应该对异常输入有清晰反应,对正常输入有稳定输出,并且不依赖样例数据的顺序。

## 三、核心任务

第一步是清洗和聚合订单日志。你要实现按用户统计 GMV、购买次数和客单价的函数。它对应 Spark SQL 中的 `groupBy(user_id).agg(sum(amount), count(...))`。返回结果要按 GMV 降序、用户 id 升序稳定排序,这样线上评分可以重复验证。边界情况包括空日志、只有浏览无购买、退款或负金额输入。

第二步是模拟 Structured Streaming 的窗口聚合。你要按固定窗口统计商品销量。例如窗口大小 60 分钟时,0-59 分钟属于窗口 0,60-119 分钟属于窗口 60。只有 purchase 事件参与销量统计。实现时要先根据 watermark 过滤迟到过久事件,再按 `(window_start, item_id)` 聚合 quantity。返回结果应包含窗口、商品和销量,并按窗口、销量、商品稳定排序。

第三步是构造推荐候选。真实 Spark MLlib 中 ALS 会根据用户-商品矩阵学习隐向量。本关不要求实现 ALS 公式,而是用可解释的行为权重模拟推荐思路:purchase 权重大于 cart,cart 大于 view;已购买商品不再推荐;候选分数可来自同一用户的历史兴趣和全局热门度。函数需要返回每个用户 top N 商品推荐,并保证分数可比较、排序稳定、没有重复商品。

第四步是设计分区写出计划。真实生产中,电商明细通常按 `dt/hour` 写入 Parquet,方便下游按日期小时过滤。本关不写文件,而是根据清洗后的记录返回一个分区计划:每个分区包含分区键、记录数和估算大小。评测会检查你是否正确使用 `dt` 和 `hour`,是否处理空数据,是否拒绝非法分区字段。

这四个任务连起来,对应一条完整的 Spark 作业思路:先从原始日志得到用户购买指标,再从事件时间视角得到窗口销量,然后利用行为历史生成推荐候选,最后为结果落盘设计分区。你不需要追求复杂模型,也不需要模拟 Spark 的执行引擎。更重要的是保持数据契约清晰:哪些字段必须存在,哪些事件会被忽略,哪些异常应该抛出,排序规则如何保证可重复。真实生产排障时,这些契约比"看起来像 Spark 代码"更重要。

## 四、工程质量要求

你的函数必须返回结构化 Python 对象,不要打印结果。所有浮点数保留到可比较的精度即可,评测会用容差比较。请优先写清楚数据流:输入校验、过滤、分组、聚合、排序、返回。不要为了通过某个样例硬编码用户或商品 id,因为隐藏测试会替换数据分布。不要假设日志已经有序,也不要假设事件类型只出现训练样例里的几个值;未知事件可以忽略,但字段类型错误应明确抛出异常。

本关的重点不是写很长的代码,而是把 Spark 的核心抽象讲清楚:批处理指标、流式窗口、推荐候选、分区落地。你实现的是这些抽象的最小可运行版本。进入真实 Spark 环境后,它们分别对应 DataFrame groupBy/agg、Structured Streaming window/watermark、MLlib 推荐流程和 DataFrameWriter partitionBy。

评分系统会从多个角度检查你的实现。公开样例只覆盖一部分路径,隐藏样例会替换用户、商品和时间分布,也会检查空输入、非法参数和异常字段。请不要返回固定答案,不要只凑齐字段名,也不要把输入原样返回。一个好的实现应该能在用户 id 或商品 id 改变后仍然计算正确,在窗口边界事件出现时仍然归入正确窗口,在推荐候选里排除已经购买过的商品,并且在分区计划中用真实记录内容估算大小。

## 五、提交要求

请在 `student_spark12.py` 中实现四个函数:

1. `aggregate_user_purchase_metrics(events)`
2. `compute_window_product_sales(events, window_minutes=60, watermark_minutes=120)`
3. `build_recommendation_candidates(events, top_n=3)`
4. `plan_partitioned_output(rows, partition_cols=("dt", "hour"))`

每个函数都必须有输入校验和稳定排序。返回值必须是 list 或 dict,不要返回自定义对象。评测会包含公开样例、隐藏样例、空输入、错类型输入、迟到事件、hardcode 攻击和 shape-only 攻击。只有端到端逻辑正确,才能通过全部测试。
```

## 4. 学生函数签名与 docstring

```python
def aggregate_user_purchase_metrics(events):
    """按 user_id 汇总 purchase 事件。

    Args:
        events: list[dict], 每条含 user_id/event_type/amount 等字段。

    Returns:
        list[dict]: 每项包含 user_id, purchase_count, total_amount, avg_order_value。
    """


def compute_window_product_sales(events, window_minutes=60, watermark_minutes=120):
    """按窗口和 item_id 汇总 purchase quantity。

    Args:
        events: list[dict], 每条含 item_id/event_type/event_time/quantity。
        window_minutes: 正整数窗口大小。
        watermark_minutes: 正整数迟到容忍时间。

    Returns:
        list[dict]: 每项包含 window_start, item_id, quantity。
    """


def build_recommendation_candidates(events, top_n=3):
    """基于用户行为和全局热度返回推荐候选。

    Args:
        events: list[dict], 每条含 user_id/item_id/event_type。
        top_n: 每个用户最多返回的候选数。

    Returns:
        dict[str, list[dict]]: key 为 user_id, value 为推荐 item_id/score 列表。
    """


def plan_partitioned_output(rows, partition_cols=("dt", "hour")):
    """生成按分区字段写出数据的计划。

    Args:
        rows: list[dict], 每条至少包含 partition_cols 中的字段。
        partition_cols: 分区字段列表或元组。

    Returns:
        list[dict]: 每项包含 partition, row_count, estimated_size。
    """
```

Docstring 红线:不写 groupBy 具体代码、不写推荐打分权重、不写 watermark 过滤公式,只描述输入输出。
审查决策:推荐行为权重允许在 ref 内部使用,但 handbook / docstring / test 只验证排序与行为差异,不泄露具体权重数值。

## 5. 数据合成示例

测试模块内置 `_make_events(seed=42, n=220)`,生成 200-240 行电商日志。字段:

```python
{
    "user_id": "u001",
    "item_id": "sku023",
    "event_type": "purchase",
    "event_time": 135,
    "amount": 129.90,
    "quantity": 2,
    "dt": "2026-04-30",
    "hour": "10",
}
```

数据分布:

- 用户 12-16 个,商品 20-30 个。
- `view/cart/purchase/refund` 混合,其中 purchase 约 25%-35%。
- 部分用户只有 view/cart,验证推荐不能只依赖 purchase。
- event_time 覆盖 0-360 分钟,插入少量迟到事件。
- amount 与 quantity 只在 purchase 中有效。
- dt/hour 从 event_time 派生,用于分区计划。

隐藏测试会使用不同 seed、不同用户/商品数量、空输入、异常输入。

## 6. pytest 模块设计

文件名: `test_spark12_comprehensive.py`

学生模块名: `student_spark12`

目标 case 数: 31 cases。

### F1 aggregate_user_purchase_metrics (7 cases)

| case | 目的 |
|---|---|
| test_aup_basic_metrics | 多用户 purchase 汇总正确 |
| test_aup_ignores_non_purchase | view/cart/refund 不计 GMV |
| test_aup_sorting | total_amount 降序,user_id 升序 |
| test_aup_empty | 空输入返回空 list |
| test_aup_avg_order_value | 客单价用 total/count,浮点容差 |
| test_aup_raises_on_non_list | 非 list 抛 TypeError |
| test_aup_raises_on_bad_amount | amount 非数值或负数抛 ValueError |

### F2 compute_window_product_sales (8 cases)

| case | 目的 |
|---|---|
| test_cwps_basic_window | 60 分钟窗口聚合 |
| test_cwps_multiple_items | 同窗口多商品分别汇总 |
| test_cwps_watermark_filters_late | 迟到过久事件被过滤 |
| test_cwps_ignores_non_purchase | 只统计 purchase |
| test_cwps_sorting | window_start 升序,quantity 降序,item_id 升序 |
| test_cwps_boundary_event_on_window_edge | 60 分钟边界事件落入正确窗口 |
| test_cwps_raises_bad_window | window_minutes <= 0 抛 ValueError |
| test_cwps_raises_bad_quantity | quantity 非正数抛 ValueError |

### F3 build_recommendation_candidates (8 cases)

| case | 目的 |
|---|---|
| test_brc_returns_dict | 返回 dict |
| test_brc_top_n_limit | 每用户最多 top_n |
| test_brc_excludes_purchased | 已购买商品不推荐 |
| test_brc_score_ordering | score 降序,item_id 升序 |
| test_brc_user_specific | 不同用户推荐不同 |
| test_brc_empty | 空输入返回空 dict |
| test_brc_uses_global_popularity_for_sparse_user | 稀疏用户仍可获得热门候选 |
| test_brc_raises_bad_top_n | top_n <= 0 抛 ValueError |

### F4 plan_partitioned_output (8 cases)

| case | 目的 |
|---|---|
| test_ppo_basic_dt_hour | 按 dt/hour 生成分区 |
| test_ppo_counts | row_count 正确 |
| test_ppo_estimated_size | estimated_size 为正且随分区内容变化 |
| test_ppo_estimated_size_uses_json_bytes | estimated_size=sum(len(json.dumps(row,sort_keys=True))) |
| test_ppo_custom_partition | 支持自定义分区字段 |
| test_ppo_empty | 空输入返回空 list |
| test_ppo_raises_missing_partition | 缺分区字段抛 ValueError |
| test_ppo_raises_non_list | rows 非 list 抛 TypeError |

## 7. v2 攻击验证设计

### 攻击表

| 类型 | 学生提交模式 | 期望 fail 率 | 触发点 |
|---|---|---:|---|
| A Stub | `pass` / `return None` | 100% | 所有返回类型与异常 case fail |
| B Hardcode | 固定返回公开样例用户/商品/窗口 | >=80%,最多 9/31 通过 | hidden seed、排序、动态聚合、异常输入 |
| C Shape-only | 返回字段齐全但值全 0/空 | >=80%,最多 6/31 通过 | GMV、窗口销量、推荐 score、row_count 都验值 |
| D Identity | 直接 return events/rows | >=80%,最多 6/31 通过 | 返回结构、聚合粒度、已购买过滤、分区计划 fail |

### 红线表

| 函数 | >=3 独立输入 | >=1 边界 | >=1 负例 type | 浮点容差 | dict/list 全字段 |
|---|---|---|---|---|---|
| aggregate_user_purchase_metrics | yes | 空输入/无 purchase | 非 list/bad amount | avg_order_value | user_id/count/total/avg |
| compute_window_product_sales | yes | 空/迟到事件 | bad window/bad quantity | 不涉及或 quantity 容差可扩展 | window_start/item_id/quantity |
| build_recommendation_candidates | yes | 空/top_n=1 | bad top_n/non list | score 容差 | item_id/score 全验 |
| plan_partitioned_output | yes | 空/单分区 | rows 非 list/缺字段 | estimated_size 容差 | partition/row_count/estimated_size |

## 8. 预期入库方案(审后执行)

审过后才执行以下步骤:

1. 新增 `student_spark12_ref.py` 与 `student_spark12.py` stub。
2. 新增 `test_spark12_comprehensive.py`。
3. 本地红绿 TDD:
   - 红: 先写测试,ref 未实现时失败。
   - 绿: 实现 ref,31 cases 全 pass。
   - 攻击: stub 0/31,hardcode <= 9/31,shape-only <= 6/31,identity <= 6/31。
4. SQL:
   ```sql
   BEGIN;
   DELETE FROM task_tests WHERE task_id=37;
   INSERT INTO task_tests
     (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order)
   VALUES
     (37, 'pytest_spark12',
      '{"test_module":"test_spark12_comprehensive.py","student_module_name":"student_spark12"}',
      '{"placeholder":"pytest_module 31 cases"}',
      false, 'pytest_module', 1);
   COMMIT;
   ```
5. 部署测试模块到学校 `huixue-backend:/app/app/services/pytest_modules/test_spark12_comprehensive.py`。
6. 学校 canary:
   - C2-B stub -> 0/31
   - C2-B ref -> 31/31
   - Browser Use student1 Spark12 页面看到完成态。

## 9. 审查决策与剩余风险

1. 不引入 pyspark:已审通过。ref + test 也不 import。
2. 推荐函数行为权重:已审通过,仅内部使用,handbook / docstring / test 不泄露具体数值。
3. estimated_size:已审修改为 `sum(len(json.dumps(row, sort_keys=True, ensure_ascii=False)) for row in partition_rows)`,不是 `row_count * 100`。
4. 函数名:保持现状,不改 Spark API 风格。
5. case 数:从 28 增至 31,F2/F3/F4 各加 1 case。
6. 剩余风险:学校容器 pytest stdout 解析与 sandbox 已是既有 KNOWN_ISSUES,本次不改 code_executor。
