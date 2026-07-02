-- WX8: 数值清洗
-- practice_id=5, order_in_practice=8, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        5,
        $v$数值清洗$v$,
        'PRACTICE',
        8,
        $v$intermediate$v$,
        $v$## 数值字段的清洗问题

## 1.1 数值表达的多样性

数值字段在文本数据源里有多种表达形式:
- "1234.56" (纯数字)
- "1,234.56" (带千分位)
- "$1,234.56" (含货币符号)
- "￥1234.56" (中文货币)
- "1.234,56" (欧洲风格, 逗号是小数点)
- "1234.56 USD" (单位后缀)
- " 1234.56 " (含空白)

存到数据库前必须统一为 float, 否则数学运算 (sum/avg) 都会失败。

## 1.2 千分位与小数点

不同地区的约定不同:
- **美式**: "1,234.56" (逗号千分位, 点小数)
- **欧式**: "1.234,56" (点千分位, 逗号小数)

工程实务: 中国系统通常用美式 (受美元影响), 欧洲系统用欧式。本关函数按**美式**解析。

## 1.3 范围与精度

数值字段的两个常见后处理:
- **范围截断 (clip)**: 把值限制在 [lo, hi]
- **精度控制 (round)**: 限制小数位数

复习 WX04 的 clip 逻辑, 本关复用相同语义。


## 解析与截断

## 2.1 数值字符串解析

函数 `parse_numeric_string(s)`: 把含货币符号 / 千分位 / 空白的字符串解析为 float。

策略:
1. strip 前后空白
2. 移除货币符号 ($ ¥ ￥)
3. 移除千分位逗号
4. 转 float

简化规则 (本关):
- 接受字符: 数字 0-9, 一个 . (小数点), 一个 - (负号在最前), 货币符号 $ / ¥ / ￥, 千分位 ,
- 不接受: 字母, 多个 ., 字母后缀 (如 "USD")
- 失败 → 抛 ValueError

## 2.2 是否合法数值字符串

函数 `is_numeric_string(s)`: 判断字符串能否解析为合法数值, 不抛异常 (返回 False)。

逻辑同 parse 但用 try/except 模式或显式校验。

## 2.3 范围截断

函数 `clip_to_range(value, lo, hi)`: 复用 WX04 的截断逻辑。

公式: $\hat{x} = \max(\min(x, hi), lo)$

与 WX04 不同的是这里 value 类型是 float, 入口已假设是数值。


## 四舍五入与业务案例

## 3.1 四舍五入 round_half_up

Python 的 `round()` 使用**银行家舍入** (Banker's rounding): 0.5 时向偶数舍入。
- `round(0.5) == 0` (向偶数舍 0)
- `round(1.5) == 2`
- `round(2.5) == 2` (向偶数舍 2)

工程实务: 财务/统计常需要"四舍五入" (half-up):
- half-up: 0.5 总是向上 (`0.5 → 1`, `1.5 → 2`, `2.5 → 3`)

实现: `floor(value * 10^d + 0.5) / 10^d` 用 Decimal 库或手动计算。

简化方案 (本关): 加 1e-9 容差再用 round, 处理浮点误差。

## 3.2 业务案例: 财务数据清洗

场景: 公司收到供应商账单 CSV, 金额字段格式杂乱:
- "$1,234.56" (美元)
- "￥9,876.5" (人民币)
- "100.00 USD" (后缀)
- "1234.567" (超精度)

清洗流水线:
1. **判断是否合法** (本关 is_numeric_string): 含 USD 后缀的拒绝, 走人工
2. **解析** (本关 parse_numeric_string): 去货币 + 千分位 → float
3. **范围合理性** (本关 clip_to_range): 截断到合理范围 [0, 10000000], 防止录入错误
4. **精度控制** (本关 round_half_up): 限制小数 2 位 (财务标准)
5. **入库**

## 3.3 工程口诀

- **数值清洗顺序**: 解析 → 范围 → 精度
- **千分位与小数点必看场景**: 美式 vs 欧式
- **银行家舍入是 Python 默认**: 财务必须显式 half-up
- **货币符号的多样性**: 中文系统额外处理 ¥ / ￥
- **失败 fallback**: 解析失败入人工队列, 不要静默丢弃

## 3.4 进阶: Decimal 替代 float

浮点数有精度问题 (0.1 + 0.2 != 0.3), 财务关键场景应使用 `decimal.Decimal`:
- 精确 (任意精度)
- 可指定舍入规则 (ROUND_HALF_UP)
- 慢 5-10 倍

本关用 float (教学简化), 实际项目财务字段强制 Decimal。

## 3.5 范围合理性的设计

数值字段的合理范围因业务而异:
- 年龄: [0, 150]
- 商品价格: [0, 10000000]
- 温度 (C): [-273.15, 1000]
- 概率: [0.0, 1.0]

工程经验: 范围**外** = 数据错误, 必须 clip 或 reject。配合 WX04 的 IQR 法可发现统计异常 (业务范围内但概率低)。

## 3.6 业务规则与一致性

数值字段还可能与其他字段相关:
- "discount_amount <= original_price"
- "quantity * unit_price == total_amount"

跨字段一致性是后续关卡的内容, 本关只看单字段数值。

## 3.7 数值清洗的 ROI

数值字段错误的代价:
- 金额错 1 元 → 财务对账失败 → 重对账成本 ≥ 100 元
- 温度错 10 度 → 报警系统误判 → 设备损失 ≥ 1 万
- 用户年龄错 → 推荐失效, 商业损失难量化

投资 1 小时数值清洗代码, 节省的 ROI 通常是 100x+。

$v$,
        $v${"questions": [{"id": "q08-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_wx08.py 中的 4 个函数; 评测以 test_wx08.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_parse_dollar_thousands$v$, $v$parse dollar thousands$v$, false, $v$parse dollar thousands$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_parse_yuan_thousands$v$, $v$parse yuan thousands$v$, false, $v$parse yuan thousands$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_parse_yen$v$, $v$parse yen$v$, false, $v$parse yen$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_parse_dollar_no_thousands$v$, $v$parse dollar no thousands$v$, false, $v$parse dollar no thousands$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_parse_multi_thousands$v$, $v$parse multi thousands$v$, false, $v$parse multi thousands$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_parse_simple_with_thousands$v$, $v$parse simple with thousands$v$, false, $v$parse simple with thousands$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_parse_raises_on_letters$v$, $v$parse raises on letters$v$, false, $v$parse raises on letters$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_parse_raises_on_unit_suffix$v$, $v$parse raises on unit suffix$v$, false, $v$parse raises on unit suffix$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_parse_raises_on_non_string$v$, $v$parse raises on non string$v$, false, $v$parse raises on non string$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_clip_below$v$, $v$50 截到 [100, 200] → 100 (low)$v$, false, $v$50 截到 [100, 200] → 100 (low)$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_clip_above$v$, $v$300 截到 [0, 100] → 100$v$, false, $v$300 截到 [0, 100] → 100$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_clip_negative_below$v$, $v$-50 截到 [-10, 10] → -10$v$, false, $v$-50 截到 [-10, 10] → -10$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_clip_raises_on_lower_gt_upper$v$, $v$clip raises on lower gt upper$v$, false, $v$clip raises on lower gt upper$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_round_half_up_05$v$, $v$0.5 → 1.0$v$, false, $v$0.5 → 1.0$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_round_half_up_15$v$, $v$1.5 → 2.0 (banker would also give 2)$v$, true, $v$1.5 → 2.0 (banker would also give 2)$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_round_half_up_25$v$, $v$2.5 → 3.0 (kills banker)$v$, true, $v$2.5 → 3.0 (kills banker)$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_round_half_up_45$v$, $v$4.5 → 5.0 (kills banker, banker would give 4)$v$, true, $v$4.5 → 5.0 (kills banker, banker would give 4)$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_round_half_up_with_decimals_2$v$, $v$1.235 round 2 → 1.24$v$, true, $v$1.235 round 2 → 1.24$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_round_half_up_055$v$, $v$0.55 round 1 → 0.6 (kills banker)$v$, true, $v$0.55 round 1 → 0.6 (kills banker)$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_round_half_up_raises_on_negative_decimals$v$, $v$round half up raises on negative decimals$v$, true, $v$round half up raises on negative decimals$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_round_half_up_raises_on_non_numeric$v$, $v$round half up raises on non numeric$v$, true, $v$round half up raises on non numeric$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_isn_dollar$v$, $v$isn dollar$v$, true, $v$isn dollar$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_isn_yen$v$, $v$isn yen$v$, true, $v$isn yen$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_isn_yuan_thousands$v$, $v$isn yuan thousands$v$, true, $v$isn yuan thousands$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_isn_negative$v$, $v$isn negative$v$, true, $v$isn negative$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_isn_invalid_letters$v$, $v$isn invalid letters$v$, true, $v$isn invalid letters$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_isn_invalid_unit_suffix$v$, $v$isn invalid unit suffix$v$, true, $v$isn invalid unit suffix$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_isn_raises_on_non_string$v$, $v$isn raises on non string$v$, true, $v$isn raises on non string$v$, NULL, 28)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
