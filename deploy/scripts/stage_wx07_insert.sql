-- WX7: 字符串清洗
-- practice_id=5, order_in_practice=7, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$字符串清洗$v$,
        'PRACTICE',
        7,
        $v$intermediate$v$,
        $v$## 字符串噪声与清洗目标

## 1.1 字符串字段的常见问题

文本字段是清洗最常见的对象, 主要问题:
- **前后空白**: " 张三 " → "张三" (复制粘贴常见)
- **内部多空白**: "张  三" / "张\\t三" / "张\\n三" → "张 三"
- **过长**: 用户输入 5000 字商品描述, 系统字段限 1000
- **标点污染**: "iPhone 14 Pro Max!!!" → "iPhone 14 Pro Max"
- **大小写混用**: "iPhone" / "IPHONE" / "iphone"
- **全角半角**: "ＡＢＣ" / "ABC" (复习 WX06 编码主题)

本关聚焦前 4 个问题, 大小写已在 WX05 涉及。

## 1.2 清洗的"好策略"

字符串清洗的策略选择:
- **保留语义信息**: 不要为了归一化把语义丢掉 ("张  三" → "张三" 改变了名字)
- **可逆性**: 清洗记录原始字段, 必要时可回溯
- **性能**: 对千万级数据要选 O(N) 简单方法, 不要用复杂正则

## 1.3 标点的复杂性

英文标点: . , ! ? ; : - " ' ( ) [ ] { }
中文标点: 。 ， ！ ？ ； ： — " " ' ' （ ） 【 】 《 》

工程实务: 标点全去掉是一种粗糙做法; 更精细的策略保留某些 (如保留空格、保留连字符 -)。本关函数实现简单"去标点", 移除一组常见的英文与中文标点字符。


## 空白处理与长度截断

## 2.1 strip 前后空白

Python 的 `str.strip()` 默认去掉**所有 Unicode 空白字符**:
- 空格 (0x20)
- TAB (0x09)
- 换行 (\\n 0x0a, \\r 0x0d)
- 全角空格 (\\u3000)
- 不间断空格 (\\u00a0)

工程实务: 大多数场景用默认行为即可。本关函数封装 `text.strip()`。

## 2.2 collapse internal whitespace

把字符串中**所有连续空白**(任何长度) 压缩成**单个空格**:
- "张  三" (两空格) → "张 三"
- "张\\t三" (TAB) → "张 三"
- "张\\n\\n三" (双换行) → "张 三"
- "张  \\t  三" (混合) → "张 三"

策略: 用 `text.split()` (无参时按所有空白拆分并去掉空段) 然后 `" ".join`。这是 Python 惯用法。

工程实务: 商品名 / 用户名 / 标题等字段必须做 collapse, 否则搜索匹配失败。

## 2.3 截断 (truncate)

简单截断: 如果 `len(text) > max_len`, 返回 `text[:max_len]`; 否则原样返回。

工程实务:
- **数据库字段**: 必须截断到字段长度, 否则插入失败
- **UI 显示**: 截断后加 "..." 但本关只做纯截断
- **多字节字符**: 注意中文一个字符算 1 (Python str 是字符级), 不是字节级

Python 切片对字符串是字符级, 不会切断 UTF-8 多字节字符。


## 标点清理与业务案例

## 3.1 去除标点

函数 `remove_punctuation(text)`: 把字符串中常见英文与中文标点字符全部删除, 其他字符保留。

实现: 遍历每个字符 c, 如果 c 不在标点集合, 保留。

标点集合: ., ! ? ; : - " ' ( ) [ ] { } 。 ， ！ ？ ； ： — " " ' ' （ ） 【 】 《 》 (28 个)

## 3.2 业务案例: 电商商品名称清洗

场景: 商品标题来自多个商家上传, 格式杂乱:

原始: "  iPhone   14  Pro  Max!!!  最新款 "
清洗目标: "iPhone 14 Pro Max 最新款"

流水线:
1. **strip 前后空白** (本关 trim_whitespace): "iPhone   14  Pro  Max!!!  最新款"
2. **去标点** (本关 remove_punctuation): "iPhone   14  Pro  Max  最新款"
3. **collapse 内部空白** (本关 collapse_internal_whitespace): "iPhone 14 Pro Max 最新款"
4. **截断到 200 字** (本关 truncate_to_length): 已 < 200, 不变
5. **大小写归一化** (复习 WX05): 通常不归一化商品名 (品牌大小写有意义)

数字: 1000 万商品 → 标题平均长度 30 字, 清洗后 25 字, 带来 10% 搜索匹配率提升。

## 3.3 工程口诀

- **顺序: trim → 去标点 → collapse → truncate**: 顺序错了效果差
- **strip 用默认参数**: 涵盖所有 Unicode 空白
- **collapse 用 split + join**: O(N) 简洁
- **截断保留字符级**: Python str 切片即可
- **去标点要看场景**: 搜索匹配可去, 显示给用户保留

## 3.4 进阶: 拼写修正与近似匹配

字符串清洗后还可能需要:
- 拼写修正: "iPhonen" → "iPhone" (Levenshtein 距离)
- 近似匹配: 模糊去重 (复习 WX03 模糊重复)

本关只做基础清洗, 拼写与近似匹配是更高级专题。

## 3.5 字符串清洗的副作用

过度清洗会丢失信息:
- 去标点丢失 "C++" 的 "++" → 变成 "C"
- 去空白丢失 "New York" → 变成 "NewYork"
- 截断丢失商品长描述

工程经验: 清洗规则必须**与下游使用方对齐**, 不要单方面决定。

$v$,
        $v${"questions": [{"id": "q07-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx07.py 中的 4 个函数; 评测以 test_wx07.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_trim_spaces$v$, $v$trim spaces$v$, false, $v$trim spaces$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_trim_tabs$v$, $v$trim tabs$v$, false, $v$trim tabs$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_trim_newlines$v$, $v$trim newlines$v$, false, $v$trim newlines$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_trim_mixed$v$, $v$trim mixed$v$, false, $v$trim mixed$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_trim_full_width_space$v$, $v$全角空格也去$v$, false, $v$全角空格也去$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_trim_internal_preserved$v$, $v$内部空白保留: 'a b c' → 'a b c'$v$, false, $v$内部空白保留: 'a b c' → 'a b c'$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_trim_raises_on_non_string$v$, $v$trim raises on non string$v$, false, $v$trim raises on non string$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_collapse_double_space$v$, $v$collapse double space$v$, false, $v$collapse double space$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_collapse_triple_space$v$, $v$collapse triple space$v$, false, $v$collapse triple space$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_collapse_tab$v$, $v$collapse tab$v$, false, $v$collapse tab$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_collapse_newline$v$, $v$collapse newline$v$, false, $v$collapse newline$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_collapse_mixed$v$, $v$混合空白 'a \t \n b' → 'a b'$v$, false, $v$混合空白 'a \t \n b' → 'a b'$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_collapse_with_trim$v$, $v$前后空白也清: '  a  b  ' → 'a b'$v$, false, $v$前后空白也清: '  a  b  ' → 'a b'$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_collapse_three_words$v$, $v$collapse three words$v$, false, $v$collapse three words$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_collapse_raises_on_non_string$v$, $v$collapse raises on non string$v$, false, $v$collapse raises on non string$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_truncate_short_unchanged$v$, $v$短的不截$v$, false, $v$短的不截$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_truncate_long$v$, $v$长的截到 max_len$v$, true, $v$长的截到 max_len$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_truncate_exact_length$v$, $v$长度等于 max_len 不变$v$, true, $v$长度等于 max_len 不变$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_truncate_to_3$v$, $v$truncate to 3$v$, true, $v$truncate to 3$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_truncate_to_1$v$, $v$truncate to 1$v$, true, $v$truncate to 1$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_truncate_chinese$v$, $v$中文 3 字符 max=2 → 取前 2 字符$v$, true, $v$中文 3 字符 max=2 → 取前 2 字符$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_truncate_to_zero$v$, $v$boundary: max_len=0 → ''$v$, true, $v$boundary: max_len=0 → ''$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_truncate_raises_on_negative$v$, $v$truncate raises on negative$v$, true, $v$truncate raises on negative$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_truncate_raises_on_non_string$v$, $v$truncate raises on non string$v$, true, $v$truncate raises on non string$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_punc_english$v$, $v$punc english$v$, true, $v$punc english$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_punc_question$v$, $v$punc question$v$, true, $v$punc question$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_punc_chinese$v$, $v$punc chinese$v$, true, $v$punc chinese$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_punc_mixed$v$, $v$混合英中标点$v$, true, $v$混合英中标点$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_punc_quotes$v$, $v$引号也去$v$, true, $v$引号也去$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_punc_brackets$v$, $v$punc brackets$v$, true, $v$punc brackets$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_punc_no_punctuation$v$, $v$无标点不变$v$, true, $v$无标点不变$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_punc_raises_on_non_string$v$, $v$punc raises on non string$v$, true, $v$punc raises on non string$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
