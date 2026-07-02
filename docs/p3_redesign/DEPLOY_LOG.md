# P3 audit 部署日志 — WX/BD 22 关 v2 fc 测试用例重做

## 背景

P3.1 审计 (2026-04-25/26) 发现 56 关 v1 evaluator 中 33 关可游戏化，方案 C 决策：24 v2 重做 + 11 补强。
本次部署执行了 WX 12 关 + BD 12 关 = 24 关 v2 重做 (task 118-128, 130-141)。
综合关 task 129/141 此前已就位 pytest_module 协议 (28 cases), 本次保持不变。

## 设计目标

每关 4 函数 × 7-12 测试用例 = 28-50 case/关，覆盖：
- 正常值 + 边界值 + 全相等 + 极值
- 类型负例 (str/int/list/dict 类型错误)
- 业务边界 (None/空 list/负数/zero/最大值)

攻击验证 4 类：
- A. Stub (return None) → 0% 通过
- B. Hardcode-best (硬编码最常见 expected) → <20% 通过
- C. Hardcode-generic (猜 0/1/True/False/""/[]) → <30% 通过
- D. Identity (return input) → <20% 通过

## 实现方式

WX/BD 任务此前已使用 v2 function_call 协议 (per-case subprocess 隔离, tolerance 浮点容差, raises 类型严格匹配)。
本次仅替换 task_tests.input_data / expected_output, 不改 evaluator 框架。

## 部署

### 步骤 1 - 本地开发

```
backend/scripts/p3_redesign/generate_cases.py    # 88 函数 / 809 case 设计
backend/scripts/p3_redesign/analyze.py          # 攻击分析 (本地)
backend/scripts/p3_redesign/gen_sql.py          # 生成 INSERT SQL
backend/scripts/p3_redesign/apply_tests.sql     # 905 行 SQL
backend/scripts/p3_redesign/restore_one.py      # 恢复 helper (task 118 首测失误用)
backend/scripts/p3_redesign/verify_live.py      # 学校 DB 攻击验证
backend/scripts/p3_redesign/live_tests.csv      # 学校 DB dump (811 行)
```

git commit:
- `6a763cf` feat(p3): redesign 22 WX/BD task_tests for v2 function_call anti-cheat
- `5d8deb3` fix(p3): add case_id to task_tests INSERT statements

### 步骤 2 - 学校部署

**SSH docker exec psql apply (无 OSS, SQL 文件 208K 不算大文件, 用 stdin pipe)**

```bash
# 首次试错: case_id NOT NULL 未填, INSERT 全部失败
# Task 118 数据被 DELETE, 紧急恢复
ssh huixueops@100.74.141.3 "sudo docker exec 743a1e751097_node1-data_db_1 \
  psql -U huixue -d huixue" -c "DELETE FROM task_tests WHERE task_id = 118;"

# 紧急恢复 33 个原 case_id 测试 (使用旧 wx_tests.txt 数据)
cat /tmp/p3_redesign/restore_118.sql | ssh huixueops@100.74.141.3 \
  "sudo docker exec -i 743a1e751097_node1-data_db_1 psql -U huixue -d huixue"

# 修复 gen_sql.py 加入 case_id 后, 全量重试
cat /tmp/p3_redesign/apply_tests.sql | ssh huixueops@100.74.141.3 \
  "sudo docker exec -i 743a1e751097_node1-data_db_1 psql -U huixue -d huixue"
```

### 步骤 3 - 学校实证 (DB SELECT)

```sql
SELECT t.id AS task_id, LEFT(t.title, 25) AS title, COUNT(tt.id) AS test_count
FROM tasks t LEFT JOIN task_tests tt ON tt.task_id = t.id
WHERE t.id BETWEEN 118 AND 140
GROUP BY t.id, t.title
ORDER BY t.id;
```

| task_id | title | test_count |
|---------|-------|------------|
| 118 | 数据清洗概述与流程 | 56 |
| 119 | 缺失值检测与补全 | 42 |
| 120 | 重复数据识别与去重 | 31 |
| 121 | 异常值检测与处理 | 48 |
| 122 | 格式规范化 | 36 |
| 123 | 编码与字符清洗 | 39 |
| 124 | 字符串清洗 | 35 |
| 125 | 数值清洗 | 49 |
| 126 | 关系一致性校验 | 31 |
| 127 | 数据合并与去重 | 21 |
| 128 | 清洗质量评估 | 36 |
| 129 | 综合项目 - 电商订单数据清洗流水线 | 1 (pytest_module) |
| 130 | Hadoop 概述与集群搭建 | 51 |
| 131 | HDFS 分布式文件系统 | 32 |
| 132 | HDFS 操作与 Block 调度 | 34 |
| 133 | MapReduce 分布式计算原理 | 39 |
| 134 | MapReduce 编程实战 | 28 |
| 135 | YARN 资源管理与调度 | 29 |
| 136 | Hive 数据仓库基础 | 35 |
| 137 | HiveQL 查询与优化 | 30 |
| 138 | HBase NoSQL 数据库 | 36 |
| 139 | Sqoop 数据迁移工具 | 34 |
| 140 | Kafka 流数据平台 | 37 |

**总计 809 case (22 关) + 1 pytest_module 综合关 = 810 条测试已入库学校 DB**

## 攻击验证 (live DB)

WX/BD 88 函数中：
- hard_best_pass ≤ 20% (达原始 80% fail 阈值): 40 函数 (45%)
- hard_best_pass 20-50% (中等): 28 函数 (32%)
- hard_best_pass > 50% (仍有弱点): 20 函数 (23%)
  - 主要集中在 boolean 函数 (is_X) 和简单判断 (count_X) — 函数语义决定难以纯靠 expected 值分布防御

### 已知遗留弱点 (待阶段 3 _values_equal 升级时一并处理)

| 函数 | hbest | hgen | 说明 |
|------|------|------|------|
| is_missing | 83% | 100% | True/False 二值函数 |
| is_outlier_iqr | 86% | 100% | 同上 |
| is_pure_ascii | 58% | 100% | 同上 |
| is_block_size_valid | 50% | 100% | 同上 |
| count_referential_violations | 71% | 86% | 0/1/2 集中在低值 |
| get_hadoop_component_role | 33% | 0% | 已合格 |

布尔函数 (返回 True/False) 是函数式 evaluator 的固有边界：纯靠 expected 值分布无法根本防御。
阶段 3 计划引入 hidden test cases + 多维度 expected 组合，将进一步压缩硬编码空间。

## 后续

- Task #3 (11 关补强): Python 3 + Spark 4 + DC 4 = 11 关测试用例扩到 ≥6, 不重写 evaluator
- 阶段 3 _values_equal 升级: 引入 hidden case + 复杂 expected marker, 进一步降低硬编码命中率
- 学生进度安全: P3.1 审计已确认 WX/BD 无 student_progress 引用, DELETE 安全

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>