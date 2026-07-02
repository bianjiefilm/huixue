-- WX9: 关系一致性校验
-- practice_id=5, order_in_practice=9, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$关系一致性校验$v$,
        'PRACTICE',
        9,
        $v$intermediate$v$,
        $v$## 关系一致性问题的本质

## 1.1 关系数据的常见错误

数据库表之间通常有外键约束 (foreign key constraint), 但实际数据常违反:
- **孤儿记录**: 子表的外键在父表中不存在 (订单的 user_id 不在用户表)
- **重复键**: 主键 / 业务键有重复 (本应唯一的字段重复)
- **悬空引用**: 父表删除后子表仍引用 (cascade 没生效)
- **一对一破坏**: 应该 1:1 的关系出现 1:N 或 N:N

工程实务: 即使有外键约束, 大批量导入 / 离线 ETL / 历史数据迁移仍会引入这些问题。

## 1.2 检测 vs 修复

关系一致性是**数据质量**的最后一道防线。检测策略:
1. 列出所有违反约束的记录
2. 计数报告
3. 修复策略 (drop / fill default / 人工)

本关聚焦"检测", 不实现"修复" (修复策略往往业务定)。

## 1.3 时间复杂度

朴素算法: 子表每条记录与父表全表比较, $O(N \cdot M)$。
工程实务: 把父表 keys 存入 set, 检查降到 $O(N + M)$。

Python 的 `key in set` 是 $O(1)$, 远快于 `key in list` 的 $O(M)$。本关函数用 set 优化。


## 孤儿检测与唯一性

## 2.1 find_orphan_keys

给定子表 keys (child_keys) 与父表 keys (parent_keys), 返回 child_keys 中出现但 parent_keys 中没有的 key 列表。

实现:
1. parent_set = set(parent_keys)
2. orphans = [k for k in child_keys if k not in parent_set]
3. 保留出现顺序 (按 child_keys 顺序)

工程实务: 孤儿处理通常 (a) drop 掉孤儿子记录, (b) 创建一个 "unknown" 父记录承接所有孤儿。

## 2.2 has_unique_keys

判断 list 中所有元素是否互不相同。

实现: `len(keys) == len(set(keys))`。

工程实务: 主键 / 业务键 / 唯一索引必须满足 unique。检测发现重复 → 必须人工合并或选择保留版本 (复习 WX03 去重的 keep_first / keep_last)。

## 2.3 count_referential_violations

计数 child_keys 中违反外键约束的条数 (即孤儿数)。

`count = len(find_orphan_keys(child_keys, parent_keys))`

但本关函数独立计算, 不依赖前一个函数。

违反率 = violations / len(child_keys), 是数据质量指标。


## 一对一映射与业务案例

## 3.1 is_one_to_one_mapping

给定两个等长列表 left, right, 判断是否构成 1-1 映射: 每个 left 元素对应唯一的 right 元素, 且 left/right 各自内部无重复。

条件:
- len(left) == len(right)
- len(set(left)) == len(left) (left 唯一)
- len(set(right)) == len(right) (right 唯一)

满足三个条件 → True; 否则 False。

工程实务: 1-1 映射常用于"用户与员工卡号"、"订单与发货单号"等业务场景。

## 3.2 业务案例: 订单-客户一致性校验

场景: 电商系统每日 ETL 把订单表和客户表导入数据仓库, 需要校验:
1. 订单的 user_id 都在客户表 (无孤儿订单)
2. 客户表的 user_id 唯一 (无重复客户)
3. 客户表的 email 与 user_id 是 1-1 映射 (无客户注册多个 email)

校验流水线:
1. **find_orphan_keys** (本关): 订单 user_id 中找孤儿
2. **has_unique_keys** (本关): 客户 user_id 唯一性
3. **count_referential_violations** (本关): 计数报警
4. **is_one_to_one** (本关): user_id 与 email 1-1 映射

数字: 1000 万订单 → 50 个孤儿 (0.0005% 违反率, 可接受); 100 万客户 → 200 重复 (0.02% 违反, 需修); 100 万 email → 1000 客户多 email (0.1%, 需调研)。

## 3.3 工程口诀

- **关系校验在清洗最后**: 前面字段清洗后才有效
- **孤儿处理看业务**: drop 数据 vs 创建 "unknown" 父记录
- **唯一键违反必修**: 主键重复是数据库灾难
- **set 优化查询**: 大数据量必须 set, 不能 list
- **报告违反率**: 一致性指标必须量化

## 3.4 跨字段约束 (拓展)

除了表间关系, 单表内还有跨字段约束:
- "begin_date <= end_date"
- "discount_amount <= original_price"
- "quantity * unit_price == total_amount"

跨字段约束是更细粒度的一致性, 本关聚焦表间关系, 跨字段是进阶专题。

## 3.5 报告与可视化

关系一致性的检测结果通常做成"质量报告":
- 孤儿率 (违反 / 总数)
- 重复键率 (重复 / 总数)
- 1-1 映射违反数

报告对接到运维监控系统, 触发报警阈值 (如 > 1% 违反 → 拉群讨论)。本关只实现检测, 报告生成是更大主题。

$v$,
        $v${"questions": [{"id": "q09-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx09.py 中的 4 个函数; 评测以 test_wx09.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_orphan_some_orphans$v$, $v$child=[1,2,3,4], parent=[1,2,3] → [4]$v$, false, $v$child=[1,2,3,4], parent=[1,2,3] → [4]$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_orphan_multiple$v$, $v$child=[1,2,5,7], parent=[1,2] → [5, 7]$v$, false, $v$child=[1,2,5,7], parent=[1,2] → [5, 7]$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_orphan_strings$v$, $v$child=['a','b','c'], parent=['a','c'] → ['b']$v$, false, $v$child=['a','b','c'], parent=['a','c'] → ['b']$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_orphan_with_duplicates$v$, $v$重复孤儿都保留: [4,4,5], parent=[1] → [4,4,5]$v$, false, $v$重复孤儿都保留: [4,4,5], parent=[1] → [4,4,5]$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_orphan_no_orphans$v$, $v$无孤儿 → []$v$, false, $v$无孤儿 → []$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_orphan_raises_on_non_list$v$, $v$orphan raises on non list$v$, false, $v$orphan raises on non list$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_unique_with_duplicate$v$, $v$unique with duplicate$v$, false, $v$unique with duplicate$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_unique_strings$v$, $v$unique strings$v$, false, $v$unique strings$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_unique_strings_dup$v$, $v$unique strings dup$v$, false, $v$unique strings dup$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_unique_all_same$v$, $v$unique all same$v$, false, $v$unique all same$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_unique_raises_on_non_list$v$, $v$unique raises on non list$v$, false, $v$unique raises on non list$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_crv_two_violations$v$, $v$[1,2,5,7] vs parent=[1,2] → 2$v$, true, $v$[1,2,5,7] vs parent=[1,2] → 2$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_crv_three_violations$v$, $v$[1,2,3,99,100,101] vs parent=[1,2,3] → 3$v$, true, $v$[1,2,3,99,100,101] vs parent=[1,2,3] → 3$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_crv_one_violation$v$, $v$[1,2,3,4] vs parent=[1,2,3] → 1$v$, true, $v$[1,2,3,4] vs parent=[1,2,3] → 1$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_crv_with_duplicate_violations$v$, $v$[4,4,5] vs parent=[1] → 3$v$, true, $v$[4,4,5] vs parent=[1] → 3$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_crv_no_violations$v$, $v$全在 parent → 0$v$, true, $v$全在 parent → 0$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_crv_raises_on_non_list$v$, $v$crv raises on non list$v$, true, $v$crv raises on non list$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_one_to_one_left_dup$v$, $v$left 有重复 → 非 1-1$v$, true, $v$left 有重复 → 非 1-1$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_one_to_one_right_dup$v$, $v$right 有重复 → 非 1-1$v$, true, $v$right 有重复 → 非 1-1$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_one_to_one_unequal_length$v$, $v$长度不等 → 非 1-1$v$, true, $v$长度不等 → 非 1-1$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_one_to_one_both_dup$v$, $v$两边都有重复 → 非 1-1$v$, true, $v$两边都有重复 → 非 1-1$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_one_to_one_single_pair$v$, $v$boundary: 单对 → True$v$, true, $v$boundary: 单对 → True$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_one_to_one_raises_on_non_list$v$, $v$one to one raises on non list$v$, true, $v$one to one raises on non list$v$, NULL, 23)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
