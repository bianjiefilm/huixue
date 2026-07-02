-- WX3: 重复数据识别与去重
-- practice_id=5, order_in_practice=3, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$重复数据识别与去重$v$,
        'PRACTICE',
        3,
        $v$beginner$v$,
        $v$## 重复数据的来源与代价

## 1.1 数据为什么会重复

数据重复在工业系统中极常见, 来源:
- **多次写入**: 客户端重试、消息队列重发
- **跨系统同步**: A 系统插入后 B 系统再次拉取
- **人工录入**: 同一客户被两个销售员各录入一次
- **历史合并**: 多个旧库合并到新库, 部分键冲突
- **日志重放**: 故障恢复时重放消息队列

工程实务: 即使有"主键约束", 重复仍会以"非键字段相同, 主键不同"的形式出现 (例: 同一个客户两个 user_id)。

## 1.2 完全重复 vs 部分重复

根据"哪些字段相同"分类:
- **完全重复 (exact duplicate)**: 所有字段都相同, 简单去重
- **部分重复 (key duplicate)**: 业务键 (如手机号) 相同, 但其他字段可能不同
- **模糊重复 (fuzzy duplicate)**: 字段值相似但不完全相同 (如 "John Smith" vs "Jonh Smith")

本关聚焦完全重复 (最简单), 部分重复需结合业务键, 模糊重复需相似度算法 (是更高级专题)。

## 1.3 重复带来的代价

- **统计偏差**: 重复让计数膨胀 (3 条相同 → 看起来 3 个客户)
- **训练集泄漏**: 重复样本同时进入训练 + 测试集, 模型评估失真
- **存储浪费**: 5% 重复 = 5% 存储费用浪费
- **计算浪费**: 重复样本走完整 pipeline 浪费 CPU


## 去重策略与保留规则

## 2.1 完全相等的判定

两条记录 (本关用 list[float] 或 list[any] 简化模型) 完全相等 = 长度相同 + 元素逐个相等。Python 的 `==` 在 list 上正是这个语义。

工程实务:
- **数值列**: 浮点比较要带容差 (1e-9), 严格 == 容易因精度差异误判
- **字符串列**: 注意大小写、空格、Unicode 归一化
- **日期列**: 建议先标准化格式再比较 (后续关卡)

本关函数 `is_exact_duplicate(row_a, row_b)` 用 list `==`, 不引入容差 (默认严格)。

## 2.2 重复行计数

给定 N 条记录, 重复行数 = "所有出现 ≥ 2 次的记录的总出现数 - 不同种类的重复记录种数"。

简化定义 (本关): 重复行数 = 总记录数 - 不同记录种类数。

例: [A, A, B, C, A] → 5 - 3 = 2 条重复 (A 出现 3 次, 多出 2 条)。

工程实务: 重复行计数是质量监控的关键指标, 入库前后 + 清洗前后都要算。

## 2.3 去重保留规则

去重时保留哪一条? 两种主流策略:

**保留首次 (preserve first / keep first)**: 按数据原始顺序, 保留第一次出现的记录。后续重复全部丢弃。
- 适合: 数据按时间顺序到达, 第一次出现是"最早"信息
- 优点: 保留最多上下文 (创建时间)
- 缺点: 后续修正不会被保留

**保留末次 (keep last)**: 保留最后一次出现的记录。
- 适合: 数据按更新时间排序, 末次是"最新"
- 优点: 反映最新状态
- 缺点: 丢失历史轨迹

工程实务: 根据数据语义选择。例如客户主数据用 keep_last (最新地址有效), 订单流水用 keep_first (最早成单时间)。


## 业务案例与工程口诀

## 3.1 业务案例: 客户主数据去重

场景: 公司有 5 个销售系统 (CRM/客服/网站/小程序/线下), 每个系统都有客户表, 总计 1000 万行客户记录。同一客户在多个系统重复出现, 需要统一为一个"主数据"。

去重流水线:
1. **统一字段**: 所有系统的字段名规范化 (后续关卡)
2. **完全重复检测** (本关): 所有字段都相同 → 直接去重
3. **业务键去重**: 手机号或邮箱相同 → 保留最近修改时间的一条 (本关 keep_last)
4. **模糊重复**: 名字相似 + 同一地区 + 同一手机号尾 4 位 → 人工审核
5. **合并主数据**: 选定保留版本, 其他打"已合并"标记

数字: 10M 行原始 → 完全去重后 8.5M (1.5M 完全重复) → 业务键去重后 7.2M → 模糊去重审核后 7M (10M → 7M, 30% 减少)。

## 3.2 工程口诀

- **去重必须有顺序**: 默认保留首次, 业务上看场景
- **完全重复优先**: 简单且最安全
- **业务键去重要业务确认**: 同手机不同名? 可能是夫妇共用
- **模糊去重要人工**: 算法判错代价大
- **去重前后必须算质量比率**: 验证去重效果

## 3.3 去重的副作用

去重会"丢失数据", 即使是相同数据, 业务上可能仍有价值:
- 重复出现次数本身是信号 (例: 3 次提交订单 → 高意向客户)
- 历史副本可用于追溯 (审计/合规)

工程经验: 不要直接 DELETE 重复行, 标记 + 索引隔离更安全。

## 3.4 去重前的预处理

重复检测对"输入预处理"敏感:
- 原始: "John Smith" / "john smith" → 完全重复检测会判为不同
- 预处理 (lowercase + strip) 后: 相同, 重复正确识别

所以**预处理 + 去重**是组合操作。本关函数假设输入已预处理 (本关只做 list ==), 实际系统中需要先做格式归一化才能正确去重。

## 3.5 重复检测的复杂度

朴素算法是 $O(N^2)$ (两两比较), 大数据量下不可行。优化方案:
- **hash 方案**: 对每行算 hash, 把比较降到 $O(N)$
- **排序后扫**: 排序 $O(N \log N)$, 然后扫描 $O(N)$, 总 $O(N \log N)$

工程实务: pandas 的 drop_duplicates 内部用 hash, 1000 万行能在秒级完成。本关函数实现简单 list 版, 不优化复杂度。

$v$,
        $v${"questions": [{"id": "q03-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx03.py 中的 4 个函数; 评测以 test_wx03.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_dup_identical_3$v$, $v$dup identical 3$v$, false, $v$dup identical 3$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_dup_eq_len_diff_one_value$v$, $v$长度相同但值不同 → False (kills 'len equal == True' shape)$v$, false, $v$长度相同但值不同 → False (kills 'len equal == True' shape)$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_dup_eq_len_diff_first$v$, $v$dup eq len diff first$v$, false, $v$dup eq len diff first$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_dup_eq_len_diff_strings$v$, $v$dup eq len diff strings$v$, false, $v$dup eq len diff strings$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_dup_eq_len_case_sensitive$v$, $v$dup eq len case sensitive$v$, false, $v$dup eq len case sensitive$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_dup_eq_len_zero_vs_one$v$, $v$dup eq len zero vs one$v$, false, $v$dup eq len zero vs one$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_dup_empty_lists$v$, $v$boundary 空 list$v$, false, $v$boundary 空 list$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_dup_raises_on_non_list$v$, $v$dup raises on non list$v$, false, $v$dup raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_cdr_one_pair$v$, $v$[A, A, B] → 1$v$, false, $v$[A, A, B] → 1$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_cdr_three_of_one$v$, $v$[A, A, A, B, C] → 5 - 3 = 2$v$, false, $v$[A, A, A, B, C] → 5 - 3 = 2$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_cdr_all_same$v$, $v$[A, A, A] → 3 - 1 = 2$v$, false, $v$[A, A, A] → 3 - 1 = 2$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_cdr_complex$v$, $v$[A,A,B,C,A] → 2$v$, false, $v$[A,A,B,C,A] → 2$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_cdr_multi_field$v$, $v$多字段: [[1,a], [1,a], [1,b]] → 1$v$, true, $v$多字段: [[1,a], [1,a], [1,b]] → 1$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_cdr_two_pairs$v$, $v$[A, A, B, B, C] → 5 - 3 = 2$v$, true, $v$[A, A, B, B, C] → 5 - 3 = 2$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_cdr_raises_on_non_list$v$, $v$cdr raises on non list$v$, true, $v$cdr raises on non list$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_dpf_simple$v$, $v$[A, A, B] → [A, B]$v$, true, $v$[A, A, B] → [A, B]$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_dpf_repeated$v$, $v$[A, B, A, C, A] → [A, B, C]$v$, true, $v$[A, B, A, C, A] → [A, B, C]$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_dpf_complex$v$, $v$dpf complex$v$, true, $v$dpf complex$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_dpf_multi_field$v$, $v$dpf multi field$v$, true, $v$dpf multi field$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_dpf_all_same$v$, $v$[A, A, A] → [A]$v$, true, $v$[A, A, A] → [A]$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_dkl_repeated_three$v$, $v$[A, B, A, C, B] → [A, C, B] (A末次=2, C=3, B=4)$v$, true, $v$[A, B, A, C, B] → [A, C, B] (A末次=2, C=3, B=4)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_dkl_two_groups$v$, $v$[A, B, A] → [B, A] (A末次=2 在 B 之后)$v$, true, $v$[A, B, A] → [B, A] (A末次=2 在 B 之后)$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_dkl_back_and_forth$v$, $v$[B, A, B] → [A, B] (B末次=2, A末次=1)$v$, true, $v$[B, A, B] → [A, B] (B末次=2, A末次=1)$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_dkl_complex$v$, $v$[A, B, C, A, B] → [C, A, B]$v$, true, $v$[A, B, C, A, B] → [C, A, B]$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_dkl_raises_on_non_list$v$, $v$dkl raises on non list$v$, true, $v$dkl raises on non list$v$, NULL, 25)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
