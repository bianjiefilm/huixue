-- ============================================================
-- MJ9: 关联规则挖掘
-- practice_id=7, order_in_practice=9
-- ============================================================

BEGIN;

INSERT INTO tasks (
    practice_id, title, task_type, order_in_practice, difficulty,
    handbook_markdown, question_data, created_at, updated_at
) VALUES (
    7,
    $v$关联规则挖掘$v$,
    'PRACTICE',
    9,
    $v$intermediate$v$,
    $v$## 关联规则基础

## 9.1 基本概念

关联规则: $A \\Rightarrow B$, 表示购买了 A 的顾客也倾向于购买 B

| 指标 | 公式 | 含义 |
|------|------|------|
| 支持度 | sup(A→B) = P(A∩B) | A和B同时发生的概率 |
| 置信度 | conf(A→B) = P(B|A) = P(A∩B)/P(A) | A发生时B发生的条件概率 |
| 提升度 | lift(A→B) = P(A∩B)/(P(A)·P(B)) | 提升度>1表示正相关 |

```python
# 手动计算
def support(df, itemsets):
    return df[itemsets].all(axis=1).mean()

def confidence(df, antecedent, consequent):
    sup_ab = support(df, antecedent + consequent)
    sup_a = support(df, antecedent)
    return sup_ab / sup_a if sup_a > 0 else 0

def lift(df, antecedent, consequent):
    sup_ab = support(df, antecedent + consequent)
    sup_a = support(df, antecedent)
    sup_b = support(df, consequent)
    return sup_ab / (sup_a * sup_b) if (sup_a * sup_b) > 0 else 0
```


## Apriori 算法

## 9.2 Apriori 先验性质

先验性质: 若一个项集是频繁的,则其所有子集也必须是频繁的

```python
# mlxtend 实现
!pip install mlxtend
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

transactions = [
    ['牛奶', '面包', '鸡蛋'],
    ['面包', '尿布', '啤酒', '鸡蛋'],
    ['牛奶', '尿布', '啤酒', '可乐'],
    ['面包', '牛奶', '尿布', '啤酒'],
    ['面包', '牛奶', '尿布', '可乐'],
]

te = TransactionEncoder()
te_ary = te.fit(transactions).transform(transactions)
df = pd.DataFrame(te_ary, columns=te.columns_)

frequent = apriori(df, min_support=0.4, use_colnames=True)
rules = association_rules(frequent, metric='confidence', min_threshold=0.6)
rules = rules.sort_values('lift', ascending=False)
print(rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].head(10))
```


## FP-Growth 与规则解读

## 9.3 FP-Growth

FP-Growth 使用 FP-Tree 结构避免产生候选项集,比 Apriori 快一个数量级:

```python
from mlxtend.frequent_patterns import fpgrowth

frequent = fpgrowth(df, min_support=0.4, use_colnames=True)
rules = association_rules(frequent, metric='lift', min_threshold=1.0)
print(rules.head())
```

## 9.4 业务解读

高提升度规则示例:
- {尿布} → {啤酒}: lift=3.2 (买了尿布的顾客买啤酒的可能性是平均的3.2倍)
- {草莓} → {酸奶}: lift=1.1 (提升度低,关联性不强)
$v$,
    $v${"questions": [{"id": "q9-1", "type": "concept", "difficulty": "easy", "question": "MJ9 阶段题目1", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "A", "explanation": "请参考 Handbook 第1章节。"}, {"id": "q9-2", "type": "concept", "difficulty": "easy", "question": "MJ9 阶段题目2", "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D"], "answer": "B", "explanation": "请参考 Handbook 第2章节。"}, {"id": "q9-3", "type": "calculation", "difficulty": "medium", "question": "MJ9 计算题", "options": ["A. 1", "B. 2", "C. 3", "D. 4"], "answer": "C", "explanation": "根据 Handbook 内容计算得出。"}, {"id": "q9-4", "type": "coding", "difficulty": "medium", "question": "请实现 MJ9 相关函数。", "options": null, "answer": null, "explanation": null}]}$v$,
    NOW(),
    NOW()
);

DO $$
DECLARE
    new_task_id INTEGER;
BEGIN
    SELECT MAX(id) INTO new_task_id FROM tasks WHERE practice_id = 7 AND order_in_practice = 9;
        INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order) VALUES
    (new_task_id, 'tc_1', $v$支持度计算$v$, $v$返回0~1$v$, false, $v$支持度$v$, 'CONTAINS', 1),
    (new_task_id, 'tc_2', $v$置信度计算$v$, $v$返回0~1$v$, false, $v$置信度$v$, 'CONTAINS', 2),
    (new_task_id, 'tc_3', $v$提升度计算$v$, $v$返回>0$v$, false, $v$提升度$v$, 'CONTAINS', 3),
    (new_task_id, 'tc_4', $v$Apriori频繁项集$v$, $v$返回项集列表$v$, true, $v$频繁项集$v$, 'CONTAINS', 4);
    RAISE NOTICE 'Inserted task tests for MJ9';
END $$;

COMMIT;
