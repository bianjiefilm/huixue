-- ============================================================
-- MJ9: 关联规则挖掘
-- practice_id=7, order_in_practice=9
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$关联规则挖掘$v$,
        'PRACTICE',
        9,
        $v$intermediate$v$,
        $v$## 关联规则任务的位置

## 1.1 与监督/聚类的区别

关联规则挖掘 (Association Rule Mining) 是无监督学习的另一支 — 与聚类不同, 它不寻找"分组", 而是寻找"共现规律": "顾客买了 X, 经常也会买 Y"。这种规律在零售、电商、医疗共现诊断、安全日志关联里大量出现。

数据形式: **事务列表** (list of transactions), 每个事务是一个项的集合, 例如:

$T_1 = \{ \text{牛奶}, \text{面包}, \text{鸡蛋} \}$

$T_2 = \{ \text{面包}, \text{尿布}, \text{啤酒} \}$

...

任务: 在大量事务里挖出"高频共现的项集"和"具有商业可解释性的规则"。

## 1.2 三大指标

| 指标 | 公式 | 直观含义 |
|------|------|----------|
| 支持度 | $\text{sup}(A) = \frac{包含 A 的事务数}{总事务数}$ | A 在数据中出现的普遍程度 |
| 置信度 | $\text{conf}(A \to B) = \frac{\text{sup}(A \cup B)}{\text{sup}(A)}$ | A 出现时 B 也出现的条件概率 |
| 提升度 | $\text{lift}(A \to B) = \frac{\text{sup}(A \cup B)}{\text{sup}(A) \cdot \text{sup}(B)}$ | A 与 B 的相关强度 |

支持度低的项集即使置信度高也不可信 (样本太少, 偶然事件); 置信度高但提升度接近 1 也意义有限 (B 本身就高频, 与 A 无关)。**只有支持度足够 + 提升度显著 > 1 的规则才有业务价值**。


## 支持度的计算细节

## 2.1 单项支持度

给定 4 个事务: $T_1=\{A,B\}, T_2=\{A,C\}, T_3=\{B,C\}, T_4=\{A,B,C\}$

- $\text{sup}(\{A\}) = 3/4 = 0.75$ (A 出现在 $T_1, T_2, T_4$)
- $\text{sup}(\{B\}) = 3/4 = 0.75$
- $\text{sup}(\{C\}) = 3/4 = 0.75$

## 2.2 多项支持度

- $\text{sup}(\{A, B\}) = 2/4 = 0.5$ (A 和 B 同时出现在 $T_1, T_4$)
- $\text{sup}(\{A, B, C\}) = 1/4 = 0.25$
- $\text{sup}(\{Z\}) = 0$ (从未出现的项)

## 2.3 边界约定

- **空项集的支持度**: 数学上 $\text{sup}(\emptyset) = 1$ (空集是任何集合的子集), 但工程上通常不参与挖掘, 直接报错或跳过
- **空事务列表**: 没有数据无法计算, 应报错


## Apriori 算法的先验性质

## 3.1 频繁项集的定义

给定阈值 min_support, 一个项集是**频繁的** $\iff$ 它的支持度 $\geq$ min_support。

在 4 个事务的例子里, 设 min_support = 0.5:
- 频繁单项: $\{A\}, \{B\}, \{C\}$ (都 0.75)
- 频繁两项: $\{A,B\}, \{A,C\}, \{B,C\}$ (都 0.5)
- 频繁三项: 无 (\{A,B,C\} 只有 0.25)

共 6 个频繁项集。

## 3.2 Apriori 先验性质

关键观察: **如果一个项集是频繁的, 它的所有子集也必须是频繁的; 反过来, 如果一个项集不频繁, 它的所有超集也不可能频繁**。

这是 Apriori 算法的核心剪枝依据 — 不必枚举所有 $2^d$ 个项集, 而是从单项开始, 逐层扩展, 用上一层的频繁项集生成下一层候选, 提前剪枝任何包含非频繁子集的候选。

## 3.3 朴素 Apriori 流程 (伪代码)

```
L1 ← 所有频繁单项
k ← 2
while L_{k-1} 非空:
    C_k ← 由 L_{k-1} 自连接生成 (k 项候选)
    剪枝: 删除任何含非频繁子集的候选
    扫描事务计算 C_k 的支持度
    L_k ← C_k 中支持度 ≥ min_support 的项集
    k ← k + 1
return ⋃ L_k
```

## 3.4 FP-Growth 的优化

FP-Growth 用 FP-Tree 数据结构避免显式生成候选项集, 在密集数据集上比 Apriori 快一个数量级。本关聚焦原理与朴素实现, 工程上使用现成实现 (mlxtend 等)。


## 业务案例: 超市购物篮分析

## 4.1 场景

某连锁超市 100 万笔交易, 想找出"买 A 同时买 B"的高价值规则, 用于商品摆放、促销组合、关联推荐。

## 4.2 走完一遍

**步 1 数据预处理**: 把每笔订单变成项集 (商品名集合)。原始扫码记录里 1 笔订单可能含几十个 SKU, 需要先聚合到品类级别 (例: "牛奶_400ml" 与 "牛奶_1L" 合并为 "牛奶")。

**步 2 设阈值**: min_support = 0.01 (项在 1% 以上事务出现) 是常见起点。100 万笔下, 这意味着至少 10000 笔包含该项 — 统计上有意义。

**步 3 挖掘**: 跑 FP-Growth 得到约 5000 个频繁项集。

**步 4 生成规则与排序**:
- 按 lift 降序看 Top 50 — 通常前几条是经典:
  - {尿布} → {啤酒}: lift = 3.2 (经典案例, 周末爸爸们一起买)
  - {刮胡刀} → {剃须膏}: lift = 4.1
  - {火锅底料} → {毛肚}: lift = 5.5
- 按 confidence 看: 即使 lift 不极端, confidence 高的规则也有业务价值

**步 5 业务行动**:
- 商品摆放: 高 lift 规则的商品物理相邻 (尿布架旁放小瓶啤酒)
- 促销组合: 把 {A, B} 做"搭售折扣"
- 推荐: 用户加 A 进购物车, 提示加 B

## 4.3 常见陷阱

- **lift 高 但样本少**: 一笔事务里 {鱼子酱, 香槟} 共现, lift 可能极高但支持度极低, 不可推广
- **季节性偏置**: 春节前数据里 {白酒, 海鲜} 高频不代表全年通用
- **品类聚合粒度错**: 太细 (按 SKU) 会让大部分规则支持度过低, 太粗 (按部门) 失去可操作性
- **混淆相关与因果**: {孕妇用品, 婴儿车} 高 lift 是因为同一类用户购买, 不是孕妇用品"导致"购买婴儿车

关联规则的产出是**业务假设**, 不是结论。每条规则上线前都需要 A/B 测试验证。

$v$,
        $v${"questions": [{"id": "q09-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj09.py 中的 4 个函数; 评测以 test_mj09.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_sup_a_three_quarters$v$, $v${A} 在 3/4 事务中 → 0.75$v$, false, $v${A} 在 3/4 事务中 → 0.75$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_sup_ab_half$v$, $v${A,B} 在 2/4 事务中 → 0.5$v$, false, $v${A,B} 在 2/4 事务中 → 0.5$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_sup_abc_quarter$v$, $v${A,B,C} 在 1/4 → 0.25$v$, false, $v${A,B,C} 在 1/4 → 0.25$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_sup_zero$v$, $v${Z} 不在任何事务 → 0.0$v$, false, $v${Z} 不在任何事务 → 0.0$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_sup_full$v$, $v$5 笔事务 [A] × 5 中 {A} 支持度 1.0$v$, false, $v$5 笔事务 [A] × 5 中 {A} 支持度 1.0$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_sup_two_fifths$v$, $v$5 笔事务 {B} 在 2 笔 → 0.4$v$, false, $v$5 笔事务 {B} 在 2 笔 → 0.4$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_sup_raises_on_empty_trans$v$, $v$sup raises on empty trans$v$, false, $v$sup raises on empty trans$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_sup_raises_on_non_list$v$, $v$sup raises on non list$v$, false, $v$sup raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_conf_a_to_b$v$, $v$conf({A}→{B}) = sup(A∪B)/sup(A) = 0.5/0.75 = 2/3$v$, false, $v$conf({A}→{B}) = sup(A∪B)/sup(A) = 0.5/0.75 = 2/3$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_conf_b_to_a$v$, $v$conf({B}→{A}) = 0.5/0.75 = 2/3$v$, false, $v$conf({B}→{A}) = 0.5/0.75 = 2/3$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_conf_a_to_z$v$, $v$A 出现 3 次, A∩Z 出现 0 次 → 0.0$v$, false, $v$A 出现 3 次, A∩Z 出现 0 次 → 0.0$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_conf_full_implication$v$, $v$trans=[{A,B},{A,B}] conf({A}→{B}) = 1.0$v$, false, $v$trans=[{A,B},{A,B}] conf({A}→{B}) = 1.0$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_conf_partial$v$, $v$trans=[{A,B},{A},{A,B},{A}] conf({A}→{B}) = sup(AB)/sup(A) = 0.5/1.0 = 0.5$v$, false, $v$trans=[{A,B},{A},{A,B},{A}] conf({A}→{B}) = sup(AB)/sup(A) = 0.5/1.0 = 0.5$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_conf_raises_on_zero_antecedent$v$, $v$antecedent 支持度 0 → ValueError$v$, false, $v$antecedent 支持度 0 → ValueError$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_conf_raises_on_non_list$v$, $v$conf raises on non list$v$, false, $v$conf raises on non list$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_lift_independent$v$, $v$trans=[{A,B},{A},{B},{}] sup(A)=0.5 sup(B)=0.5 sup(AB)=0.25 → lift=1.0$v$, true, $v$trans=[{A,B},{A},{B},{}] sup(A)=0.5 sup(B)=0.5 sup(AB)=0.25 → lift=1.0$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_lift_positive$v$, $v$完全相关: trans=[{A,B},{A,B},{C}] sup(A)=2/3 sup(B)=2/3 sup(AB)=2/3 → lift=1.5$v$, true, $v$完全相关: trans=[{A,B},{A,B},{C}] sup(A)=2/3 sup(B)=2/3 sup(AB)=2/3 → lift=1.5$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_lift_classic_4trans$v$, $v$4 trans: lift({A}→{B}) = sup(AB)/(sup(A)*sup(B)) = 0.5/(0.75*0.75) = 8/9$v$, true, $v$4 trans: lift({A}→{B}) = sup(AB)/(sup(A)*sup(B)) = 0.5/(0.75*0.75) = 8/9$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_lift_negative$v$, $v${A,B} 完全互斥: trans=[{A},{A},{B},{B}] sup(A)=0.5 sup(B)=0.5 sup(AB)=0 → lift=0$v$, true, $v${A,B} 完全互斥: trans=[{A},{A},{B},{B}] sup(A)=0.5 sup(B)=0.5 sup(AB)=0 → lift=0$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_lift_double_classical$v$, $v$trans=[{A,B},{A,B},{A,C},{A,C}] sup(A)=1, sup(B)=0.5, sup(AB)=0.5 → lift=1.0$v$, true, $v$trans=[{A,B},{A,B},{A,C},{A,C}] sup(A)=1, sup(B)=0.5, sup(AB)=0.5 → lift=1.0$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_lift_raises_on_zero_consequent$v$, $v$lift raises on zero consequent$v$, true, $v$lift raises on zero consequent$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_lift_raises_on_non_list$v$, $v$lift raises on non list$v$, true, $v$lift raises on non list$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_ffi_classic_4trans_half$v$, $v$min_support=0.5: 应有 6 个频繁项集 (3 单项 + 3 双项)$v$, true, $v$min_support=0.5: 应有 6 个频繁项集 (3 单项 + 3 双项)$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_ffi_classic_4trans_three_quarter$v$, $v$min_support=0.75: 仅 3 个单项$v$, true, $v$min_support=0.75: 仅 3 个单项$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_ffi_classic_4trans_one$v$, $v$min_support=1.0: 必须出现在所有事务 → 空$v$, true, $v$min_support=1.0: 必须出现在所有事务 → 空$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_ffi_3trans_high_support$v$, $v$trans=[{A,B},{A,B},{A,B}] min_support=1.0 → {A},{B},{A,B}$v$, true, $v$trans=[{A,B},{A,B},{A,B}] min_support=1.0 → {A},{B},{A,B}$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_ffi_specific_pair$v$, $v$trans=[{A,B},{A,C},{B,C},{A,B,C}] min_support=0.4 → 应含 {A,B}$v$, true, $v$trans=[{A,B},{A,C},{B,C},{A,B,C}] min_support=0.4 → 应含 {A,B}$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_ffi_raises_on_empty_trans$v$, $v$ffi raises on empty trans$v$, true, $v$ffi raises on empty trans$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_ffi_raises_on_invalid_threshold$v$, $v$ffi raises on invalid threshold$v$, true, $v$ffi raises on invalid threshold$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_ffi_raises_on_non_list$v$, $v$ffi raises on non list$v$, true, $v$ffi raises on non list$v$, NULL, 30)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
