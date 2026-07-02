-- WX10: 数据合并与去重
-- practice_id=5, order_in_practice=10, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$数据合并与去重$v$,
        'PRACTICE',
        10,
        $v$intermediate$v$,
        $v$## 合并的语义

## 1.1 多源数据为什么需要合并

工程实务中, 数据通常分散在多个来源:
- 用户基本信息 (CRM 系统)
- 用户行为日志 (网站埋点)
- 用户订单 (订单系统)
- 用户消费 (支付系统)

合并 = 把多个表按某个共同 key (如 user_id) 拼接成一张宽表, 供下游分析。

## 1.2 三种合并语义

SQL/pandas 标准的 join 类型:
- **inner join** (内连接): 只保留两边都有 key 的记录
- **left join** (左外连接): 保留左表全部记录, 右表无匹配则 NULL
- **right join** (右外连接): 反之, 不常用 (可由 left swap 实现)
- **outer join** (全外连接): 两边并集, 各自缺失填 NULL

本关实现 inner 和 left, 它们是 99% 用例。

## 1.3 合并的副作用

合并不是无损操作:
- **数据膨胀**: 一对多关系下, 1 条左 × 3 条右 = 3 条结果
- **NULL 引入**: left join 引入新的 missing 值 (复习 WX02)
- **重复检测失效**: 合并后部分字段 NULL, 用 WX03 的去重要重新审视

工程经验: 合并前必须先做单表去重 (本关 dedup_dicts_by_key)。


## Inner / Left Join 实现

## 2.1 inner join 算法

```
result = []
for l in left:
    for r in right:
        if l[key] == r[key]:
            merged = {**l, **r}  # 合并字段
            result.append(merged)
return result
```

时间复杂度 $O(N \cdot M)$ 朴素版。优化: 把 right 按 key 索引化为 dict, 降到 $O(N + M)$。

工程实务: pandas/SQL 内部用 hash join, 大数据量必用。本关用朴素版 (≤1000 行无瓶颈)。

## 2.2 left join 算法

```
result = []
for l in left:
    matches = [r for r in right if l[key] == r[key]]
    if matches:
        for r in matches:
            result.append({**l, **r})
    else:
        result.append({**l})  # 右表字段缺失
return result
```

与 inner 不同: 左表无匹配的记录仍保留, 但右表字段不补 NULL (本关简化, 直接缺这些 key)。

## 2.3 按 key 去重 dedup_dicts_by_key

函数 `dedup_dicts_by_key(rows, key)`: 保留每个 key 第一次出现的记录, 后续同 key 丢弃。

```
result = []
seen = set()
for r in rows:
    if r[key] not in seen:
        seen.add(r[key])
        result.append(r)
return result
```

复习 WX03 的 `dedup_preserve_first`, 这里是按特定字段去重的版本。


## 合并尺寸预测与业务案例

## 3.1 合并结果大小预测

给定左表大小 L, 右表大小 R, 共同 key 数 C, 简化模型 (假设每个 key 在两表各最多出现 1 次):
- **inner**: 结果 = C
- **left**: 结果 = L (每条左记录至少 1 行)
- **right**: 结果 = R
- **outer**: 结果 = L + R - C

实际 1:N 关系会膨胀, 但本关用简化模型预测。

## 3.2 业务案例: 用户多源数据合并

场景: 公司每月把 CRM (100 万用户) + 订单 (200 万订单) + 行为 (1 亿事件) 合并成宽表。

合并流水线:
1. **单表去重** (本关 dedup_dicts_by_key): 各源按 user_id 去重 → CRM=99 万, 订单=199 万 (1% 重复)
2. **left join CRM ← 订单** (本关 merge_left): 每个 CRM 用户左连订单。如果用户无订单则保留, 没订单字段。结果 ≥ 99 万。
3. **inner join 上面 ← 行为** (本关 merge_inner): 只看有行为的用户。结果 = 共同用户数。
4. **预测尺寸** (本关 compute_merge_size): 估算合并后表大小, 决定是否可放内存。
5. **入数据仓库**

数字: 99 万 left join 订单 (1:N) → 1.2 亿条 (订单膨胀)。inner 行为后 → 5000 万 (有行为的用户)。

## 3.3 工程口诀

- **合并前必去重**: 否则膨胀失控
- **inner 是最严, left 是最宽**: 选择看下游分析需求
- **预估尺寸防内存爆**: 大表合并必须先估
- **NULL 引入要后续处理**: WX02 补全可能再走一次
- **跨数据源用 hash join**: 朴素 O(NM) 不够快

## 3.4 合并失败的典型问题

- **key 类型不一致**: 一边 int 一边 str → 永不匹配
- **空白 key**: 左 "alice" 右 " alice" → 不匹配 (复习 WX07 trim)
- **大小写**: 一边 "Alice" 一边 "alice" (复习 WX05 normalize_email_lower)
- **NULL key**: 含 None 的记录如何匹配, 业务定 (通常排除)

工程经验: 合并前必须**统一 key 字段格式** (复习 WX05 + WX07)。

$v$,
        $v${"questions": [{"id": "q10-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx10.py 中的 4 个函数; 评测以 test_wx10.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_inner_basic$v$, $v$inner basic$v$, false, $v$inner basic$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_inner_two_matches$v$, $v$inner two matches$v$, false, $v$inner two matches$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_inner_no_match$v$, $v$inner no match$v$, false, $v$inner no match$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_inner_field_merge$v$, $v$字段合并, 右覆盖左$v$, false, $v$字段合并, 右覆盖左$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_inner_raises_on_missing_key$v$, $v$inner raises on missing key$v$, false, $v$inner raises on missing key$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_inner_raises_on_non_list$v$, $v$inner raises on non list$v$, false, $v$inner raises on non list$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_left_with_match$v$, $v$left with match$v$, false, $v$left with match$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_left_no_match_at_all$v$, $v$无匹配 → 全部保留左$v$, false, $v$无匹配 → 全部保留左$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_left_one_to_many$v$, $v$1:N: 左 1 条匹配右 2 条 → 2 条结果$v$, false, $v$1:N: 左 1 条匹配右 2 条 → 2 条结果$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_left_mixed$v$, $v$left mixed$v$, false, $v$left mixed$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_left_raises_on_missing_key$v$, $v$left raises on missing key$v$, false, $v$left raises on missing key$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_dedup_one_dup$v$, $v$dedup one dup$v$, false, $v$dedup one dup$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_dedup_keeps_first$v$, $v$保留首次$v$, false, $v$保留首次$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_dedup_no_duplicates$v$, $v$dedup no duplicates$v$, true, $v$dedup no duplicates$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_dedup_all_same_key$v$, $v$dedup all same key$v$, true, $v$dedup all same key$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_dedup_raises_on_missing_key$v$, $v$dedup raises on missing key$v$, true, $v$dedup raises on missing key$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_size_inner_basic$v$, $v$common_n=5$v$, true, $v$common_n=5$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_size_left_basic$v$, $v$size left basic$v$, true, $v$size left basic$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_size_right_basic$v$, $v$size right basic$v$, true, $v$size right basic$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_size_outer_basic$v$, $v$outer = 10 + 8 - 5 = 13$v$, true, $v$outer = 10 + 8 - 5 = 13$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_size_inner_no_common$v$, $v$common=0$v$, true, $v$common=0$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_size_outer_full_overlap$v$, $v$common = min(L, R), outer = max(L, R)$v$, true, $v$common = min(L, R), outer = max(L, R)$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_size_raises_on_unknown_mode$v$, $v$size raises on unknown mode$v$, true, $v$size raises on unknown mode$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_size_raises_on_negative$v$, $v$size raises on negative$v$, true, $v$size raises on negative$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_size_raises_on_common_too_large$v$, $v$common > min(L, R)$v$, true, $v$common > min(L, R)$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_size_raises_on_non_int$v$, $v$size raises on non int$v$, true, $v$size raises on non int$v$, NULL, 26)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
