-- BD05 (task_id=134) function_call task_tests — 19 条

BEGIN;

DELETE FROM task_tests WHERE task_id=134;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (134, 'fc_wc_basic', $${"function": "word_count", "args": [["the cat", "cat sat"]], "kwargs": {}}$$, $${"result": {"the": 1, "cat": 2, "sat": 1}}$$, false, 'function_call', 1),
  (134, 'fc_wc_three_words_same', $${"function": "word_count", "args": [["a a a"]], "kwargs": {}}$$, $${"result": {"a": 3}}$$, true, 'function_call', 2),
  (134, 'fc_wc_case_sensitive', $${"function": "word_count", "args": [["Hello hello"]], "kwargs": {}}$$, $${"result": {"Hello": 1, "hello": 1}}$$, true, 'function_call', 3),
  (134, 'fc_wc_three_docs', $${"function": "word_count", "args": [["x y z", "x y", "x"]], "kwargs": {}}$$, $${"result": {"x": 3, "y": 2, "z": 1}}$$, true, 'function_call', 4),
  (134, 'fc_wc_empty_doc', $${"function": "word_count", "args": [["", "a b"]], "kwargs": {}}$$, $${"result": {"a": 1, "b": 1}}$$, true, 'function_call', 5),
  (134, 'fc_wc_raises_on_non_list', $${"function": "word_count", "args": ["not a list"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (134, 'fc_ii_basic', $${"function": "inverted_index", "args": [[["a", "b"], ["b", "c"]]], "kwargs": {}}$$, $${"result": {"a": [0], "b": [0, 1], "c": [1]}}$$, false, 'function_call', 7),
  (134, 'fc_ii_dedup_within_doc', $${"function": "inverted_index", "args": [[["a", "a", "b"]]], "kwargs": {}}$$, $${"result": {"a": [0], "b": [0]}}$$, true, 'function_call', 8),
  (134, 'fc_ii_three_docs', $${"function": "inverted_index", "args": [[["x"], ["x", "y"], ["y", "z"]]], "kwargs": {}}$$, $${"result": {"x": [0, 1], "y": [1, 2], "z": [2]}}$$, true, 'function_call', 9),
  (134, 'fc_ii_empty_doc', $${"function": "inverted_index", "args": [[["a"], [], ["a"]]], "kwargs": {}}$$, $${"result": {"a": [0, 2]}}$$, true, 'function_call', 10),
  (134, 'fc_ii_raises_on_non_list', $${"function": "inverted_index", "args": ["not a list"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 11),
  (134, 'fc_tk_basic', $${"function": "top_k_frequent", "args": [{"a": 3, "b": 2, "c": 1}, 2], "kwargs": {}}$$, $${"result": ["a", "b"]}$$, false, 'function_call', 12),
  (134, 'fc_tk_tie_alphabetical', $${"function": "top_k_frequent", "args": [{"b": 2, "a": 2, "c": 1}, 2], "kwargs": {}}$$, $${"result": ["a", "b"]}$$, true, 'function_call', 13),
  (134, 'fc_tk_k_equals_size', $${"function": "top_k_frequent", "args": [{"a": 3, "b": 1, "c": 2}, 3], "kwargs": {}}$$, $${"result": ["a", "c", "b"]}$$, true, 'function_call', 14),
  (134, 'fc_tk_k_larger_than_size', $${"function": "top_k_frequent", "args": [{"a": 3, "b": 2}, 10], "kwargs": {}}$$, $${"result": ["a", "b"]}$$, true, 'function_call', 15),
  (134, 'fc_tk_all_same_freq', $${"function": "top_k_frequent", "args": [{"c": 1, "a": 1, "b": 1}, 2], "kwargs": {}}$$, $${"result": ["a", "b"]}$$, true, 'function_call', 16),
  (134, 'fc_tk_raises_on_negative_k', $${"function": "top_k_frequent", "args": [{"a": 1}, -1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 17),
  (134, 'fc_tk_raises_on_negative_count', $${"function": "top_k_frequent", "args": [{"a": -1}, 1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (134, 'fc_tk_raises_on_non_dict', $${"function": "top_k_frequent", "args": [[["a", 1]], 1], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 19);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=134 GROUP BY task_id;

COMMIT;