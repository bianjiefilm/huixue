-- BD05 F4 重生 (task_id=134) — 加 6 cases (Stage 3 _values_equal __pairs__ marker)

BEGIN;

-- 删除可能存在的 fc_co_* cases (重跑安全)
DELETE FROM task_tests WHERE task_id=134 AND case_id LIKE 'fc_co_%';

-- 加 6 个 F4 cases (test_order 从 20 起)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (134, 'fc_co_basic', $${"function": "compute_co_occurrence", "args": [[["a", "b"]]], "kwargs": {}}$$, $${"result": {"__pairs__": [[["a", "b"], 1], [["b", "a"], 1]]}}$$, false, 'function_call', 20),
  (134, 'fc_co_three_words', $${"function": "compute_co_occurrence", "args": [[["a", "b", "c"]]], "kwargs": {}}$$, $${"result": {"__pairs__": [[["a", "b"], 1], [["a", "c"], 1], [["b", "a"], 1], [["b", "c"], 1], [["c", "a"], 1], [["c", "b"], 1]]}}$$, true, 'function_call', 21),
  (134, 'fc_co_two_docs_accumulate', $${"function": "compute_co_occurrence", "args": [[["a", "b"], ["a", "b"]]], "kwargs": {}}$$, $${"result": {"__pairs__": [[["a", "b"], 2], [["b", "a"], 2]]}}$$, true, 'function_call', 22),
  (134, 'fc_co_repeated_word', $${"function": "compute_co_occurrence", "args": [[["a", "a", "b"]]], "kwargs": {}}$$, $${"result": {"__pairs__": [[["a", "a"], 2], [["a", "b"], 2], [["b", "a"], 2]]}}$$, true, 'function_call', 23),
  (134, 'fc_co_single_word_doc', $${"function": "compute_co_occurrence", "args": [[["a"]]], "kwargs": {}}$$, $${"result": {}}$$, true, 'function_call', 24),
  (134, 'fc_co_raises_on_non_list', $${"function": "compute_co_occurrence", "args": ["not a list"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 25);

-- 验证: BD05 应有 25 cases (19 旧 + 6 新)
SELECT task_id, COUNT(*) AS total, SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden
  FROM task_tests WHERE task_id=134 GROUP BY task_id;

COMMIT;
