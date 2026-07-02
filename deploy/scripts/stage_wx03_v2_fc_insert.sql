-- WX03 (task_id=120) function_call task_tests — 25 条

BEGIN;

DELETE FROM task_tests WHERE task_id=120;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (120, 'fc_dup_identical_3', $${"function": "is_exact_duplicate", "args": [[1, 2, 3], [1, 2, 3]], "kwargs": {}}$$, $${"result": true}$$, false, 'function_call', 1),
  (120, 'fc_dup_eq_len_diff_one_value', $${"function": "is_exact_duplicate", "args": [[1, 2, 3], [1, 2, 4]], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 2),
  (120, 'fc_dup_eq_len_diff_first', $${"function": "is_exact_duplicate", "args": [[5, 2, 3], [1, 2, 3]], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 3),
  (120, 'fc_dup_eq_len_diff_strings', $${"function": "is_exact_duplicate", "args": [["a", "b"], ["a", "c"]], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 4),
  (120, 'fc_dup_eq_len_case_sensitive', $${"function": "is_exact_duplicate", "args": [["A", "b"], ["a", "b"]], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 5),
  (120, 'fc_dup_eq_len_zero_vs_one', $${"function": "is_exact_duplicate", "args": [[0, 0], [1, 1]], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 6),
  (120, 'fc_dup_empty_lists', $${"function": "is_exact_duplicate", "args": [[], []], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 7),
  (120, 'fc_dup_raises_on_non_list', $${"function": "is_exact_duplicate", "args": ["123", [1, 2, 3]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (120, 'fc_cdr_one_pair', $${"function": "count_duplicate_rows", "args": [[[1], [1], [2]]], "kwargs": {}}$$, $${"result": 1}$$, false, 'function_call', 9),
  (120, 'fc_cdr_three_of_one', $${"function": "count_duplicate_rows", "args": [[[1], [1], [1], [2], [3]]], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 10),
  (120, 'fc_cdr_all_same', $${"function": "count_duplicate_rows", "args": [[[1], [1], [1]]], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 11),
  (120, 'fc_cdr_complex', $${"function": "count_duplicate_rows", "args": [[["x"], ["x"], ["y"], ["z"], ["x"]]], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 12),
  (120, 'fc_cdr_multi_field', $${"function": "count_duplicate_rows", "args": [[[1, "a"], [1, "a"], [1, "b"]]], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 13),
  (120, 'fc_cdr_two_pairs', $${"function": "count_duplicate_rows", "args": [[[1], [1], [2], [2], [3]]], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 14),
  (120, 'fc_cdr_raises_on_non_list', $${"function": "count_duplicate_rows", "args": ["rows"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (120, 'fc_dpf_simple', $${"function": "dedup_preserve_first", "args": [[[1], [1], [2]]], "kwargs": {}}$$, $${"result": [[1], [2]]}$$, false, 'function_call', 16),
  (120, 'fc_dpf_repeated', $${"function": "dedup_preserve_first", "args": [[[1], [2], [1], [3], [1]]], "kwargs": {}}$$, $${"result": [[1], [2], [3]]}$$, true, 'function_call', 17),
  (120, 'fc_dpf_complex', $${"function": "dedup_preserve_first", "args": [[["a"], ["b"], ["c"], ["a"], ["b"], ["d"]]], "kwargs": {}}$$, $${"result": [["a"], ["b"], ["c"], ["d"]]}$$, true, 'function_call', 18),
  (120, 'fc_dpf_multi_field', $${"function": "dedup_preserve_first", "args": [[[1, "x"], [1, "y"], [1, "x"], [2, "z"]]], "kwargs": {}}$$, $${"result": [[1, "x"], [1, "y"], [2, "z"]]}$$, true, 'function_call', 19),
  (120, 'fc_dpf_all_same', $${"function": "dedup_preserve_first", "args": [[[1], [1], [1]]], "kwargs": {}}$$, $${"result": [[1]]}$$, true, 'function_call', 20),
  (120, 'fc_dkl_repeated_three', $${"function": "dedup_keep_last", "args": [[["a"], ["b"], ["a"], ["c"], ["b"]]], "kwargs": {}}$$, $${"result": [["a"], ["c"], ["b"]]}$$, false, 'function_call', 21),
  (120, 'fc_dkl_two_groups', $${"function": "dedup_keep_last", "args": [[[1], [2], [1]]], "kwargs": {}}$$, $${"result": [[2], [1]]}$$, true, 'function_call', 22),
  (120, 'fc_dkl_back_and_forth', $${"function": "dedup_keep_last", "args": [[[2], [1], [2]]], "kwargs": {}}$$, $${"result": [[1], [2]]}$$, true, 'function_call', 23),
  (120, 'fc_dkl_complex', $${"function": "dedup_keep_last", "args": [[["a"], ["b"], ["c"], ["a"], ["b"]]], "kwargs": {}}$$, $${"result": [["c"], ["a"], ["b"]]}$$, true, 'function_call', 24),
  (120, 'fc_dkl_raises_on_non_list', $${"function": "dedup_keep_last", "args": ["rows"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 25);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=120 GROUP BY task_id;

COMMIT;