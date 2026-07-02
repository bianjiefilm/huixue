-- BD5: MapReduce 编程实战
-- practice_id=16, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        16,
        $v$MapReduce 编程实战$v$,
        'PRACTICE',
        1,
        $v$intermediate$v$,
        $v$## Word Count: 经典 MR 算法

## 1.1 Word Count 的 MR 思想

word_count 是 MR 入门必学经典:
- **Map**: 文档 → (word, 1) 对
- **Combine**: 同一 mapper 内 (word, count) 聚合
- **Reduce**: 跨 mapper 同 word 求和

Python 单机版思想:
- 遍历每个文档
- 对每个 word 累加计数
- 返回 dict[word, count]

工程实务: 真实 MR 把 documents 切片到多个 mapper, 但单机版思想相同。

## 1.2 单词切分约定

本关简化规则:
- 用 Python 默认 split() 按空白拆分
- 大小写敏感 ("Hello" ≠ "hello")
- 不去标点 (假设输入已预处理)

工程实务: 实际 word_count 通常先做格式归一化 (复习 WX05 / WX07 字符串清洗)。

## 1.3 Word Count 的扩展

简单 word_count 是基础, 实际业务常需要:
- **过滤停用词**: "the", "a", "of" 等高频但无信息词
- **大小写归一**: "Hello"/"hello" 统一
- **去标点**: "hello!" → "hello"

本关聚焦核心算法, 扩展是 NLP 范畴。


## 倒排索引与 Top-K

## 2.1 倒排索引 (Inverted Index)

搜索引擎的核心数据结构: word → [doc_id_list]。

给定文档列表 (每文档已 tokenize 为 word list), 构建索引的思想:
- 遍历 (doc_id, words) 对
- 对每个 word, 把 doc_id 加入该 word 的列表
- **去重**: 同 word 在同 doc 多次出现只记一次
- **升序**: 输出列表按 doc_id 升序

工程实务: Lucene / Elasticsearch / 百度搜索引擎都基于倒排索引, 是文本检索的基础设施。

## 2.2 Top-K 频率词

给定 word→count dict 与 k, 返回出现次数最多的 k 个词。

排序规则 (本关):
- 频率降序优先
- 同频按字母升序 (确定性, 否则结果不稳定)

经典实现思想: sorted by (-count, word), 取前 k。

工程实务: top-K 是文本分析 / 推荐系统的基础。大数据规模有 heap 优化版可达 O(N log K), 本关用 O(N log N) 完整排序版。

## 2.3 与 word_count 的组合

典型流水线:
1. word_count(documents) → counts dict
2. top_k_frequent(counts, k=5) → [top_5_words]

例: 1 万搜索日志 → 5 万词 → top 5 = ['the', 'and', 'of', 'a', 'to']。


## 共现矩阵与业务案例

## 3.1 共现矩阵 (Co-occurrence Matrix)

共现矩阵 captures 词对在同一文档/窗口内同时出现的次数。

简化定义 (本关): 给定 documents (list of word lists), 计算每对**有序词对** (a, b, a≠b) 在同一文档共现的次数。

规则:
- 同一文档内的每对不同位置词 (i, j, i≠j) 算一次共现
- (a, b) 与 (b, a) 是不同的有序对, 各自计数
- 跨文档共现累加

例: documents = [['the', 'cat', 'sat']]:
- (the, cat), (cat, the), (the, sat), (sat, the), (cat, sat), (sat, cat) 各算 1 次

工程实务: 共现矩阵是 NLP 词嵌入 (word2vec) 的输入, 也用于关联规则挖掘。大词表下矩阵稀疏 (99% 词对从未共现), 用 hash 而非 dense matrix。

## 3.2 业务案例: 网站搜索日志分析

场景: 1 亿条搜索日志, 要做关键词分析:
1. **word_count** (本关): 统计每个词出现次数 → 找热搜
2. **inverted_index** (本关): 词 → 搜索 session_id list, 用于"搜了 X 的人也搜了 Y"
3. **top_k_frequent** (本关 k=100): 找当日 top 100 热搜
4. **compute_co_occurrence** (本关): 词对共现 → 推荐相关搜索

数字: 1 亿日志 / 2 千万 unique 词 / top-100 热搜实时更新 / 共现矩阵 GB 级稀疏存储。

## 3.3 工程口诀

- **MR 经典必会**: word_count / inverted_index / top_k / co-occurrence
- **倒排索引去重**: 同文档同词只算一次
- **top-K 同频要确定排序**: 字母序是默认
- **共现矩阵稀疏**: 99% 词对从不共现, 用 hash 不用 dense matrix

## 3.4 现代替代

Spark / Flink (BD 后续课程) 提供 DataFrame API, word_count 可写成 flatMap → map → reduceByKey 链式调用。但底层仍是 Map/Reduce 思想, 学习 MR 是掌握所有现代框架的基础。

## 3.5 数据规模与算法选择

不同数据量适合不同实现:
- **MB-GB 级**: Python 单机 dict 即可 (本关使用)
- **GB-TB 级**: 单机不够, 用 MapReduce / Spark
- **PB 级**: 分布式 + 多轮 shuffle 优化

算法**思想**不变, 只是规模触发不同实现选择。本关学算法本质, 规模问题是 BD06 (YARN 调度) 与现代框架课程的内容。

$v$,
        $v${"questions": [{"id": "q05-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_bd05.py 中的 4 个函数; 评测以 test_bd05.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_wc_basic$v$, $v$['the cat', 'cat sat'] → {'the':1, 'cat':2, 'sat':1}$v$, false, $v$['the cat', 'cat sat'] → {'the':1, 'cat':2, 'sat':1}$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_wc_three_words_same$v$, $v$['a a a'] → {'a': 3}$v$, false, $v$['a a a'] → {'a': 3}$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_wc_case_sensitive$v$, $v$['Hello hello'] → {'Hello': 1, 'hello': 1}$v$, false, $v$['Hello hello'] → {'Hello': 1, 'hello': 1}$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_wc_three_docs$v$, $v$['x y z', 'x y', 'x'] → {'x':3, 'y':2, 'z':1}$v$, false, $v$['x y z', 'x y', 'x'] → {'x':3, 'y':2, 'z':1}$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_wc_empty_doc$v$, $v$['', 'a b'] → {'a':1, 'b':1}$v$, false, $v$['', 'a b'] → {'a':1, 'b':1}$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_wc_raises_on_non_list$v$, $v$wc raises on non list$v$, false, $v$wc raises on non list$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_ii_basic$v$, $v$[[a,b], [b,c]] → {'a':[0], 'b':[0,1], 'c':[1]}$v$, false, $v$[[a,b], [b,c]] → {'a':[0], 'b':[0,1], 'c':[1]}$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_ii_dedup_within_doc$v$, $v$[[a,a,b]] → {'a':[0], 'b':[0]} (a 在 doc 0 多次, 只算一次)$v$, false, $v$[[a,a,b]] → {'a':[0], 'b':[0]} (a 在 doc 0 多次, 只算一次)$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_ii_three_docs$v$, $v$[[x],[x,y],[y,z]] → {'x':[0,1], 'y':[1,2], 'z':[2]}$v$, false, $v$[[x],[x,y],[y,z]] → {'x':[0,1], 'y':[1,2], 'z':[2]}$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_ii_empty_doc$v$, $v$[[a], [], [a]] → {'a': [0, 2]}$v$, false, $v$[[a], [], [a]] → {'a': [0, 2]}$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_ii_raises_on_non_list$v$, $v$ii raises on non list$v$, false, $v$ii raises on non list$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_tk_basic$v$, $v${'a':3, 'b':2, 'c':1} k=2 → ['a', 'b']$v$, false, $v${'a':3, 'b':2, 'c':1} k=2 → ['a', 'b']$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_tk_tie_alphabetical$v$, $v${'b':2, 'a':2, 'c':1} k=2 → ['a', 'b'] (同频按字母升序)$v$, true, $v${'b':2, 'a':2, 'c':1} k=2 → ['a', 'b'] (同频按字母升序)$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_tk_k_equals_size$v$, $v$k = len, 全返回排序$v$, true, $v$k = len, 全返回排序$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_tk_k_larger_than_size$v$, $v$k > len, 返回全部$v$, true, $v$k > len, 返回全部$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_tk_all_same_freq$v$, $v$全同频, 字母升序$v$, true, $v$全同频, 字母升序$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_tk_raises_on_negative_k$v$, $v$tk raises on negative k$v$, true, $v$tk raises on negative k$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_tk_raises_on_negative_count$v$, $v$tk raises on negative count$v$, true, $v$tk raises on negative count$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_tk_raises_on_non_dict$v$, $v$tk raises on non dict$v$, true, $v$tk raises on non dict$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_co_basic$v$, $v$[['a','b']] → {('a','b'):1, ('b','a'):1}$v$, true, $v$[['a','b']] → {('a','b'):1, ('b','a'):1}$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_co_three_words$v$, $v$[['a','b','c']] → 6 对各 1 (有序对)$v$, true, $v$[['a','b','c']] → 6 对各 1 (有序对)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_co_two_docs_accumulate$v$, $v$[['a','b'], ['a','b']] → ('a','b'):2 ('b','a'):2$v$, true, $v$[['a','b'], ['a','b']] → ('a','b'):2 ('b','a'):2$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_co_repeated_word$v$, $v$[['a','a','b']] → 不同位置算 (i!=j): (a,a) 来自 idx 0 与 1, 1 与 0 → 2 次. (a,b),(b,a)各 2 次 (a 出现 2 次)$v$, true, $v$[['a','a','b']] → 不同位置算 (i!=j): (a,a) 来自 idx 0 与 1, 1 与 0 → 2 次. (a,b),(b,a)各 2 次 (a 出现 2 次)$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_co_single_word_doc$v$, $v$[['a']] → {} (没有 i != j)$v$, true, $v$[['a']] → {} (没有 i != j)$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_co_raises_on_non_list$v$, $v$co raises on non list$v$, true, $v$co raises on non list$v$, NULL, 25)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
