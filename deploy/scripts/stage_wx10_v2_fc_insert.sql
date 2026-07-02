-- WX10 (task_id=127) function_call task_tests — 26 条

BEGIN;

DELETE FROM task_tests WHERE task_id=127;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (127, 'fc_inner_basic', $${"function": "merge_inner_by_key", "args": [[{"id": 1, "name": "a"}, {"id": 2, "name": "b"}], [{"id": 1, "age": 10}, {"id": 3, "age": 30}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1, "name": "a", "age": 10}]}$$, false, 'function_call', 1),
  (127, 'fc_inner_two_matches', $${"function": "merge_inner_by_key", "args": [[{"id": 1}, {"id": 2}], [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]}$$, true, 'function_call', 2),
  (127, 'fc_inner_no_match', $${"function": "merge_inner_by_key", "args": [[{"id": 1}], [{"id": 2}], "id"], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 3),
  (127, 'fc_inner_field_merge', $${"function": "merge_inner_by_key", "args": [[{"id": 1, "name": "alice", "x": 0}], [{"id": 1, "x": 99}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1, "name": "alice", "x": 99}]}$$, true, 'function_call', 4),
  (127, 'fc_inner_raises_on_missing_key', $${"function": "merge_inner_by_key", "args": [[{"id": 1}], [{"foo": 1}], "id"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 5),
  (127, 'fc_inner_raises_on_non_list', $${"function": "merge_inner_by_key", "args": ["left", [], "id"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (127, 'fc_left_with_match', $${"function": "merge_left_by_key", "args": [[{"id": 1, "n": "a"}, {"id": 2, "n": "b"}], [{"id": 1, "v": 10}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1, "n": "a", "v": 10}, {"id": 2, "n": "b"}]}$$, false, 'function_call', 7),
  (127, 'fc_left_no_match_at_all', $${"function": "merge_left_by_key", "args": [[{"id": 1}, {"id": 2}], [{"id": 99}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1}, {"id": 2}]}$$, true, 'function_call', 8),
  (127, 'fc_left_one_to_many', $${"function": "merge_left_by_key", "args": [[{"id": 1}], [{"id": 1, "v": "a"}, {"id": 1, "v": "b"}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1, "v": "a"}, {"id": 1, "v": "b"}]}$$, true, 'function_call', 9),
  (127, 'fc_left_mixed', $${"function": "merge_left_by_key", "args": [[{"id": 1, "n": "a"}, {"id": 2, "n": "b"}, {"id": 3, "n": "c"}], [{"id": 1, "v": 10}, {"id": 3, "v": 30}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1, "n": "a", "v": 10}, {"id": 2, "n": "b"}, {"id": 3, "n": "c", "v": 30}]}$$, true, 'function_call', 10),
  (127, 'fc_left_raises_on_missing_key', $${"function": "merge_left_by_key", "args": [[{"foo": 1}], [{"id": 1}], "id"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 11),
  (127, 'fc_dedup_one_dup', $${"function": "dedup_dicts_by_key", "args": [[{"id": 1, "v": "x"}, {"id": 2, "v": "y"}, {"id": 1, "v": "x2"}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1, "v": "x"}, {"id": 2, "v": "y"}]}$$, false, 'function_call', 12),
  (127, 'fc_dedup_keeps_first', $${"function": "dedup_dicts_by_key", "args": [[{"id": 1, "v": "first"}, {"id": 1, "v": "second"}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1, "v": "first"}]}$$, true, 'function_call', 13),
  (127, 'fc_dedup_no_duplicates', $${"function": "dedup_dicts_by_key", "args": [[{"id": 1}, {"id": 2}, {"id": 3}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1}, {"id": 2}, {"id": 3}]}$$, true, 'function_call', 14),
  (127, 'fc_dedup_all_same_key', $${"function": "dedup_dicts_by_key", "args": [[{"id": 1, "v": "a"}, {"id": 1, "v": "b"}, {"id": 1, "v": "c"}], "id"], "kwargs": {}}$$, $${"result": [{"id": 1, "v": "a"}]}$$, true, 'function_call', 15),
  (127, 'fc_dedup_raises_on_missing_key', $${"function": "dedup_dicts_by_key", "args": [[{"foo": 1}], "id"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 16),
  (127, 'fc_size_inner_basic', $${"function": "compute_merge_size", "args": [10, 8, 5, "inner"], "kwargs": {}}$$, $${"result": 5}$$, false, 'function_call', 17),
  (127, 'fc_size_left_basic', $${"function": "compute_merge_size", "args": [10, 8, 5, "left"], "kwargs": {}}$$, $${"result": 10}$$, true, 'function_call', 18),
  (127, 'fc_size_right_basic', $${"function": "compute_merge_size", "args": [10, 8, 5, "right"], "kwargs": {}}$$, $${"result": 8}$$, true, 'function_call', 19),
  (127, 'fc_size_outer_basic', $${"function": "compute_merge_size", "args": [10, 8, 5, "outer"], "kwargs": {}}$$, $${"result": 13}$$, true, 'function_call', 20),
  (127, 'fc_size_inner_no_common', $${"function": "compute_merge_size", "args": [10, 8, 0, "inner"], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 21),
  (127, 'fc_size_outer_full_overlap', $${"function": "compute_merge_size", "args": [10, 8, 8, "outer"], "kwargs": {}}$$, $${"result": 10}$$, true, 'function_call', 22),
  (127, 'fc_size_raises_on_unknown_mode', $${"function": "compute_merge_size", "args": [10, 8, 5, "weird"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (127, 'fc_size_raises_on_negative', $${"function": "compute_merge_size", "args": [-1, 8, 5, "inner"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 24),
  (127, 'fc_size_raises_on_common_too_large', $${"function": "compute_merge_size", "args": [5, 3, 10, "inner"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 25),
  (127, 'fc_size_raises_on_non_int', $${"function": "compute_merge_size", "args": [10.0, 8, 5, "inner"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 26);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=127 GROUP BY task_id;

COMMIT;