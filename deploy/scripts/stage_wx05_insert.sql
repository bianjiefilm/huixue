-- WX5: 格式规范化
-- practice_id=5, order_in_practice=5, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$格式规范化$v$,
        'PRACTICE',
        5,
        $v$intermediate$v$,
        $v$## 格式规范化的必要性

## 1.1 多源数据的格式碎片

数据源不同, 同一字段可能有多种格式:

**电话**:
- "138 0000 0000" / "138-0000-0000" / "+86 138 0000 0000" / "13800000000"

**邮箱**:
- "Alice@Gmail.com" / "alice@gmail.com" / " alice@gmail.com  "

**日期**:
- "2026-04-25" / "2026/4/25" / "Apr 25, 2026" / "25/04/2026" / "1714003200" (Unix 时间戳)

**金额**:
- "$1,234.56" / "￥1,234.56" / "1234.56 USD" / "1234.56"

没有规范化, 后续操作 (去重/统计/排序/匹配) 都会因格式差异而失败。

## 1.2 规范化的核心思想

把"同一含义的多种表达"映射到"唯一的规范形式":
- 电话 → 纯数字串
- 邮箱 → 小写 + 无空格
- 日期 → ISO 8601 (YYYY-MM-DD)
- 金额 → 数值 (剥离货币符号)

规范化后, 字符串 == 比较就有意义。

## 1.3 规范化 vs 校验

两个相关但不同的任务:
- **规范化 (normalize)**: 把已有数据转成标准形式
- **校验 (validate)**: 判断是否符合规则, 不修改数据

工程实务: 先校验再规范化, 校验失败的进入"待人工"队列。


## 电话与邮箱规范化

## 2.1 电话: 提取数字

最简单也最常用的归一化策略: 去掉所有**非数字字符**, 只保留数字。

"138-0000-0000" → "13800000000"
"+86 138 0000 0000" → "8613800000000"
"(138) 0000-0000" → "13800000000"

工程实务:
- 国内号码标准是 11 位数字, 转换后长度可校验
- 含 +86 前缀时长度变 13, 需要剥离前缀
- 本关函数只做"去非数字", 前缀剥离与位数校验是更复杂逻辑

## 2.2 邮箱: 小写 + 去空白

邮箱规范化两步:
1. **strip**: 去掉前后空白 (" alice@gmail.com  " → "alice@gmail.com")
2. **lower**: 全部小写 ("Alice@Gmail.com" → "alice@gmail.com")

原因:
- 邮箱**理论上**域名部分大小写不敏感 (RFC 5321), 但用户名部分服务器可能区分
- 工程实务: 大多数邮箱服务器 (Gmail/QQ/163) 全部不区分大小写 → 安全做法是统一小写
- 前后空白来自 CSV 导入或粘贴, 必须 strip

## 2.3 邮箱合法性快速判断

最简校验规则:
- 含 "@"
- "@" 后面至少有一个 "."
- 不空字符串

这不是严格 RFC 5322 校验 (那要写正则), 但工程实务足够拦截 99% 错误输入。

本关函数 `is_valid_email_basic` 实现这个最简规则: 含 "@" 且含 "."。


## 日期解析与业务案例

## 3.1 ISO 8601 日期格式

ISO 8601 是国际标准: **YYYY-MM-DD**, 例如 "2026-04-25"。

优点:
- 字符串排序 = 时间排序 (CSV/JSON 友好)
- 长度固定 10
- 全球通用, 无地区歧义

工程实务: 数据库存日期一律用 ISO, 显示给用户时按地区习惯转换。

## 3.2 解析 ISO 日期

函数 `parse_simple_date_iso(s)` 接受 "YYYY-MM-DD" 字符串, 返回 `(year, month, day)` 三元组。

简化规则 (本关):
- 长度 == 10
- 用 "-" 切成 3 段
- 每段是数字, 转 int
- 不校验月份范围 (1-12) / 天数范围 (1-31) — 这是 WX09 一致性校验

本关只做"格式转换", 不做"语义合法性"。

## 3.3 业务案例: 用户主数据格式归一化

场景: 公司从多个旧系统迁移用户数据到新主数据库, 需要把以下字段归一化:
- phone (5 种格式): 国内 11 位 / 国际带前缀 / 含分隔符 / 含括号
- email (3 种格式): 大小写混合 / 含前后空白 / 含点号变种
- register_date (4 种格式): 中文 / ISO / Unix / 美式

归一化流水线:
1. **phone** (本关): 去非数字 → 11 位或 13 位
2. **email** (本关): strip + lower
3. **register_date** (本关): 解析 ISO (假设源已转 ISO), 报告非 ISO 格式
4. **去重** (复习 WX03): 归一化后重新去重, 找出"伪重复" (实际同一用户)
5. **校验** (本关 is_valid_email_basic): 失败的进入人工队列

数字: 1000 万原始 → 归一化后去重保留 850 万, 其中 50 万邮箱失败需人工。

## 3.4 工程口诀

- **规范化先于去重**: 否则同一用户多个版本被当成不同
- **保留原始字段**: 规范化后的副本入新字段, 原始字段保留 (审计需要)
- **校验失败入人工队列**: 不要直接丢弃可能有效的数据
- **ISO 8601 是日期标准**: 数据库一律 ISO
- **大小写敏感看协议**: 邮箱通常不敏感, 用户名规则视服务器而定

## 3.5 进阶: 国际化考虑

实际跨国业务还有更多格式问题:
- 电话: +1 美国 / +44 英国 / +86 中国
- 日期: 美式 (MM/DD/YYYY) vs 欧式 (DD/MM/YYYY) 容易混淆
- 货币: USD / EUR / CNY 单位不同
- 时区: UTC / 本地, 同一时刻可能跨日

本关只做最基础的格式归一化 (国内场景), 国际化是更复杂专题。

$v$,
        $v${"questions": [{"id": "q05-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx05.py 中的 4 个函数; 评测以 test_wx05.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_phone_dashes_138$v$, $v$phone dashes 138$v$, false, $v$phone dashes 138$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_phone_spaces_186$v$, $v$phone spaces 186$v$, false, $v$phone spaces 186$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_phone_parens_199$v$, $v$phone parens 199$v$, false, $v$phone parens 199$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_phone_intl_prefix_852$v$, $v$phone intl prefix 852$v$, false, $v$phone intl prefix 852$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_phone_alphanumeric_mix$v$, $v$字母混杂: '1abc3xyz8' → '138'$v$, false, $v$字母混杂: '1abc3xyz8' → '138'$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_phone_no_digits$v$, $v$全字母 → 空串 (boundary)$v$, false, $v$全字母 → 空串 (boundary)$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_phone_raises_on_non_string$v$, $v$phone raises on non string$v$, false, $v$phone raises on non string$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_email_bob_163$v$, $v$email bob 163$v$, false, $v$email bob 163$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_email_carol_qq$v$, $v$email carol qq$v$, false, $v$email carol qq$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_email_alice_uppercase_with_spaces$v$, $v$email alice uppercase with spaces$v$, false, $v$email alice uppercase with spaces$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_email_dave_with_tabs$v$, $v$email dave with tabs$v$, false, $v$email dave with tabs$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_email_empty_after_strip$v$, $v$全空白 → '' (boundary)$v$, false, $v$全空白 → '' (boundary)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_email_raises_on_non_string$v$, $v$email raises on non string$v$, true, $v$email raises on non string$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_invalid_no_at$v$, $v$invalid no at$v$, true, $v$invalid no at$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_invalid_just_text$v$, $v$无 @ 无 . → False$v$, true, $v$无 @ 无 . → False$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_invalid_only_dot$v$, $v$invalid only dot$v$, true, $v$invalid only dot$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_valid_typical$v$, $v$1 个 valid 测试$v$, true, $v$1 个 valid 测试$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_valid_raises_on_non_string$v$, $v$valid raises on non string$v$, true, $v$valid raises on non string$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_date_2026_04_25$v$, $v$date 2026 04 25$v$, true, $v$date 2026 04 25$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_date_2000_01_01$v$, $v$date 2000 01 01$v$, true, $v$date 2000 01 01$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_date_2024_12_31$v$, $v$date 2024 12 31$v$, true, $v$date 2024 12 31$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_date_leap_day_2024_02_29$v$, $v$date leap day 2024 02 29$v$, true, $v$date leap day 2024 02 29$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_date_1999_09_09$v$, $v$boundary 年份 < 2000$v$, true, $v$boundary 年份 < 2000$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_date_raises_on_non_numeric$v$, $v$type 负例$v$, true, $v$type 负例$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_date_raises_on_non_string$v$, $v$date raises on non string$v$, true, $v$date raises on non string$v$, NULL, 25)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
