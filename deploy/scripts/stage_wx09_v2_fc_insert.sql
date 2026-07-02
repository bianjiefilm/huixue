-- WX09 (task_id=126) function_call task_tests — 23 条

BEGIN;

DELETE FROM task_tests WHERE task_id=126;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (126, 'fc_orphan_some_orphans', $${"function": "find_orphan_keys", "args": [[1, 2, 3, 4], [1, 2, 3]], "kwargs": {}}$$, $${"result": [4]}$$, false, 'function_call', 1),
  (126, 'fc_orphan_multiple', $${"function": "find_orphan_keys", "args": [[1, 2, 5, 7], [1, 2]], "kwargs": {}}$$, $${"result": [5, 7]}$$, true, 'function_call', 2),
  (126, 'fc_orphan_strings', $${"function": "find_orphan_keys", "args": [["a", "b", "c"], ["a", "c"]], "kwargs": {}}$$, $${"result": ["b"]}$$, true, 'function_call', 3),
  (126, 'fc_orphan_with_duplicates', $${"function": "find_orphan_keys", "args": [[4, 4, 5], [1]], "kwargs": {}}$$, $${"result": [4, 4, 5]}$$, true, 'function_call', 4),
  (126, 'fc_orphan_no_orphans', $${"function": "find_orphan_keys", "args": [[1, 2, 3], [1, 2, 3, 4]], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 5),
  (126, 'fc_orphan_raises_on_non_list', $${"function": "find_orphan_keys", "args": ["123", [1, 2, 3]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (126, 'fc_unique_with_duplicate', $${"function": "has_unique_keys", "args": [[1, 2, 3, 2]], "kwargs": {}}$$, $${"result": false}$$, false, 'function_call', 7),
  (126, 'fc_unique_strings', $${"function": "has_unique_keys", "args": [["a", "b", "c"]], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 8),
  (126, 'fc_unique_strings_dup', $${"function": "has_unique_keys", "args": [["a", "b", "a"]], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 9),
  (126, 'fc_unique_all_same', $${"function": "has_unique_keys", "args": [[1, 1, 1]], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 10),
  (126, 'fc_unique_raises_on_non_list', $${"function": "has_unique_keys", "args": ["123"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 11),
  (126, 'fc_crv_two_violations', $${"function": "count_referential_violations", "args": [[1, 2, 5, 7], [1, 2]], "kwargs": {}}$$, $${"result": 2}$$, false, 'function_call', 12),
  (126, 'fc_crv_three_violations', $${"function": "count_referential_violations", "args": [[1, 2, 3, 99, 100, 101], [1, 2, 3]], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 13),
  (126, 'fc_crv_one_violation', $${"function": "count_referential_violations", "args": [[1, 2, 3, 4], [1, 2, 3]], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 14),
  (126, 'fc_crv_with_duplicate_violations', $${"function": "count_referential_violations", "args": [[4, 4, 5], [1]], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 15),
  (126, 'fc_crv_no_violations', $${"function": "count_referential_violations", "args": [[1, 2], [1, 2, 3, 4]], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 16),
  (126, 'fc_crv_raises_on_non_list', $${"function": "count_referential_violations", "args": [123, [1, 2]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 17),
  (126, 'fc_one_to_one_left_dup', $${"function": "is_one_to_one_mapping", "args": [[1, 1, 2], ["a", "b", "c"]], "kwargs": {}}$$, $${"result": false}$$, false, 'function_call', 18),
  (126, 'fc_one_to_one_right_dup', $${"function": "is_one_to_one_mapping", "args": [[1, 2, 3], ["a", "a", "c"]], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 19),
  (126, 'fc_one_to_one_unequal_length', $${"function": "is_one_to_one_mapping", "args": [[1, 2, 3], ["a", "b"]], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 20),
  (126, 'fc_one_to_one_both_dup', $${"function": "is_one_to_one_mapping", "args": [[1, 1], ["a", "a"]], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 21),
  (126, 'fc_one_to_one_single_pair', $${"function": "is_one_to_one_mapping", "args": [[1], ["a"]], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 22),
  (126, 'fc_one_to_one_raises_on_non_list', $${"function": "is_one_to_one_mapping", "args": ["123", [1, 2, 3]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=126 GROUP BY task_id;

COMMIT;