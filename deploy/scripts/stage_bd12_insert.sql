-- BD12: 大数据综合项目实战
-- practice_id=23, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        23,
        $v$大数据综合项目实战$v$,
        'PRACTICE',
        1,
        $v$hard$v$,
        $v$## 大数据流水线的整合

## 1.1 全课程概念回顾

BD 课程涵盖:
- **BD01-03**: Hadoop / HDFS 基础 — 分布式存储
- **BD04-05**: MapReduce — 分布式计算
- **BD06**: YARN — 资源调度
- **BD07-08**: Hive — 数据仓库
- **BD09**: HBase — NoSQL
- **BD10**: Sqoop — 数据迁移
- **BD11**: Kafka — 流数据

本关把这些"零件"组合成系统级流水线。

## 1.2 端到端大数据流水线

标准电商数据平台流水线:
1. **migration** (BD10): MySQL → Hive (每日全量/增量)
2. **streaming** (BD11): Kafka 实时埋点 → Hive
3. **storage** (BD02): HDFS 存原始数据
4. **compute** (BD05): MapReduce 离线分析
5. **sql** (BD07/08): Hive 数仓 SQL 查询
6. **nosql** (BD09): HBase 实时查询
7. **scheduling** (BD06): YARN 协调资源
8. **报告组装** (本关 F4): 输出执行报告

本关聚焦"系统骨架": F1 (输入校验) → F2 (purpose → tool 映射) → F3 (尺寸累加) → F4 (报告组装)。

## 1.3 Purpose 到工具的映射 (本关 F2)

| 子任务 (purpose) | BD 工具 (tool) |
|---|---|
| storage | hdfs |
| compute | mapreduce |
| scheduling | yarn |
| sql | hive |
| nosql | hbase |
| streaming | kafka |
| migration | sqoop |

把 7 个 purpose 各自映射到对应工具。这是"系统配置"的代码化表达。


## Schema 校验与尺寸估算

## 2.1 Stage Schema 校验

函数 `validate_pipeline_input_schema(stages)`: 每个 stage dict 必须包含:
- `name` (str): 阶段名
- `tool` (str): 使用的工具 (复习 BD01 组件)
- `output_size_gb` (int / float): 输出数据大小, >= 0

所有 stage 都满足 → True; 任一缺字段或类型错 → False。
允许额外字段 (扩展性)。

工程实务: 流水线 YAML 配置文件必须先校验 schema, 否则启动后失败更难诊断。

## 2.2 总尺寸估算

函数 `compute_pipeline_total_size(stages)`: 累加所有 stage 的 output_size_gb。

公式: $\text{total} = \sum_i \text{stage}_i[\text{output\_size\_gb}]$

用途:
- 容量规划 (复习 BD01 集群规模)
- 成本估算 (云上按 GB 计费)
- 监控告警 (实际超估算 → 异常)

## 2.3 与 BD01-11 的呼应

- BD01 集群规模 = 总数据 × 副本因子 / 单节点容量
- 本关 F3 算的是数据总量, 喂给 BD01 的公式可得集群规模
- BD02 副本扩展, BD07 压缩降低, BD11 流式增加 — 都影响最终 storage 估算


## 执行报告与业务案例

## 3.1 执行报告 schema

函数 `combine_bd_pipeline_report(stages_done, stages_total, errors)`: 组装报告 dict:

```
{
    'stages_done': 8,
    'stages_total': 10,
    'progress_ratio': 0.8,
    'errors': {'hive_load': 1, 'kafka_consumer': 2},
    'total_errors': 3,
    'is_success': False,  # progress_ratio == 1.0 AND total_errors == 0
}
```

字段说明:
- progress_ratio = stages_done / stages_total
- total_errors = sum(errors.values())
- is_success = (progress_ratio == 1.0 AND total_errors == 0)

## 3.2 业务案例: 电商每日大数据流水线

场景: 公司每日凌晨跑 10 个 stage 的大数据流水线:

流水线设计:
1. **schema 校验** (本关 F1): 必须含 name/tool/output_size_gb
2. **执行各 stage**: BD01-11 工具组合
3. **统计 errors** (本关 F4 输入): 每 stage 报告异常数
4. **算总尺寸** (本关 F3): 累加 output_size_gb 估算 HDFS 容量
5. **报告组装** (本关 F4): 给运维 + 业务

数字: 100 GB MySQL → migration → 100 GB Hive 数据 → MapReduce 聚合 → 5 GB 报表 → HBase 实时查询; total = 205 GB; 8/10 success → progress_ratio = 0.8。

## 3.3 工程口诀

- **流水线 = schema + purpose 映射 + 尺寸估算 + 报告**: 4 部分
- **schema 校验最先**: 不合法直接退回
- **purpose 映射不要硬编码**: 用 dict 易维护
- **报告 dict 标准化**: 下游消费方便
- **复用 BD01-11 概念**: 综合不引入新工具

## 3.4 综合项目对学习的意义

综合项目 = "概念回归整合":
- 知道每个 purpose 用哪个工具 (本关 F2)
- 知道 schema 校验长什么样 (本关 F1)
- 知道流水线总量 = 各 stage 累加 (本关 F3)
- 知道报告是 schema 化 dict (本关 F4)

数据工程师从"会用单个工具"到"能搭 7 工具协同的流水线", 这是必经之路。

$v$,
        $v${"questions": [{"id": "q12-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd12.py 中的 4 个函数; 评测以 test_bd12.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_validate_all_present$v$, $v$validate all present$v$, false, $v$validate all present$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_validate_missing_name$v$, $v$validate missing name$v$, false, $v$validate missing name$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_validate_missing_tool$v$, $v$validate missing tool$v$, false, $v$validate missing tool$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_validate_missing_size$v$, $v$validate missing size$v$, false, $v$validate missing size$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_validate_wrong_type_name$v$, $v$name 不是 str$v$, false, $v$name 不是 str$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_validate_negative_size$v$, $v$size 负数$v$, false, $v$size 负数$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_validate_raises_on_non_list$v$, $v$validate raises on non list$v$, false, $v$validate raises on non list$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_purpose_compute$v$, $v$purpose compute$v$, false, $v$purpose compute$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_purpose_scheduling$v$, $v$purpose scheduling$v$, false, $v$purpose scheduling$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_purpose_sql$v$, $v$purpose sql$v$, false, $v$purpose sql$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_purpose_nosql$v$, $v$purpose nosql$v$, false, $v$purpose nosql$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_purpose_streaming$v$, $v$purpose streaming$v$, false, $v$purpose streaming$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_purpose_migration$v$, $v$purpose migration$v$, false, $v$purpose migration$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_purpose_raises_on_unknown$v$, $v$purpose raises on unknown$v$, false, $v$purpose raises on unknown$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_purpose_raises_on_empty$v$, $v$purpose raises on empty$v$, false, $v$purpose raises on empty$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_purpose_raises_on_non_string$v$, $v$purpose raises on non string$v$, true, $v$purpose raises on non string$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_total_simple$v$, $v$[10, 20, 30] → 60$v$, true, $v$[10, 20, 30] → 60$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_total_decimal$v$, $v$total decimal$v$, true, $v$total decimal$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_total_one_stage$v$, $v$total one stage$v$, true, $v$total one stage$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_total_empty$v$, $v$空 → 0$v$, true, $v$空 → 0$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_total_raises_on_missing_size$v$, $v$total raises on missing size$v$, true, $v$total raises on missing size$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_total_raises_on_negative$v$, $v$total raises on negative$v$, true, $v$total raises on negative$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_report_partial$v$, $v$report partial$v$, true, $v$report partial$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_report_success$v$, $v$全 done + 无 errors → success$v$, true, $v$全 done + 无 errors → success$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_report_done_but_errors$v$, $v$全 done 但有 errors → 仍非 success$v$, true, $v$全 done 但有 errors → 仍非 success$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_report_keys_complete$v$, $v$report keys complete$v$, true, $v$report keys complete$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_report_zero_done$v$, $v$report zero done$v$, true, $v$report zero done$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_report_raises_on_done_gt_total$v$, $v$report raises on done gt total$v$, true, $v$report raises on done gt total$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_report_raises_on_zero_total$v$, $v$report raises on zero total$v$, true, $v$report raises on zero total$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_report_raises_on_negative_error$v$, $v$report raises on negative error$v$, true, $v$report raises on negative error$v$, NULL, 30)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
