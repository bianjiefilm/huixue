-- BD04 (task_id=133) function_call task_tests — 24 条

BEGIN;

DELETE FROM task_tests WHERE task_id=133;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (133, 'fc_map_single_file', $${"function": "compute_map_task_count", "args": [[314572800]], "kwargs": {}}$$, $${"result": 3}$$, false, 'function_call', 1),
  (133, 'fc_map_two_files', $${"function": "compute_map_task_count", "args": [[104857600, 209715200]], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 2),
  (133, 'fc_map_custom_split_64mb', $${"function": "compute_map_task_count", "args": [[314572800], 67108864], "kwargs": {}}$$, $${"result": 5}$$, true, 'function_call', 3),
  (133, 'fc_map_three_files_default', $${"function": "compute_map_task_count", "args": [[134217728, 268435456, 67108864]], "kwargs": {}}$$, $${"result": 4}$$, true, 'function_call', 4),
  (133, 'fc_map_raises_on_zero_split', $${"function": "compute_map_task_count", "args": [[100], 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 5),
  (133, 'fc_map_raises_on_non_list', $${"function": "compute_map_task_count", "args": ["100"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (133, 'fc_reduce_5gb_default', $${"function": "compute_reduce_task_count", "args": [5120], "kwargs": {}}$$, $${"result": 5}$$, false, 'function_call', 7),
  (133, 'fc_reduce_partial_ceil', $${"function": "compute_reduce_task_count", "args": [1500], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 8),
  (133, 'fc_reduce_custom_target_500mb', $${"function": "compute_reduce_task_count", "args": [5120, 500], "kwargs": {}}$$, $${"result": 11}$$, true, 'function_call', 9),
  (133, 'fc_reduce_raises_on_zero_data', $${"function": "compute_reduce_task_count", "args": [0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 10),
  (133, 'fc_reduce_raises_on_non_int', $${"function": "compute_reduce_task_count", "args": [100.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 11),
  (133, 'fc_part_simple', $${"function": "partition_by_hash", "args": ["a", 5], "kwargs": {}}$$, $${"result": 2}$$, false, 'function_call', 12),
  (133, 'fc_part_word', $${"function": "partition_by_hash", "args": ["hello", 7], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 13),
  (133, 'fc_part_long_word', $${"function": "partition_by_hash", "args": ["mapreduce", 10], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 14),
  (133, 'fc_part_raises_on_empty_key', $${"function": "partition_by_hash", "args": ["", 5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (133, 'fc_part_raises_on_zero_reducers', $${"function": "partition_by_hash", "args": ["a", 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 16),
  (133, 'fc_part_raises_on_non_string', $${"function": "partition_by_hash", "args": [123, 5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 17),
  (133, 'fc_comb_max', $${"function": "is_combinable_operation", "args": ["max"], "kwargs": {}}$$, $${"result": true}$$, false, 'function_call', 18),
  (133, 'fc_comb_min', $${"function": "is_combinable_operation", "args": ["min"], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 19),
  (133, 'fc_comb_avg', $${"function": "is_combinable_operation", "args": ["avg"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 20),
  (133, 'fc_comb_median', $${"function": "is_combinable_operation", "args": ["median"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 21),
  (133, 'fc_comb_distinct', $${"function": "is_combinable_operation", "args": ["distinct"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 22),
  (133, 'fc_comb_raises_on_unknown', $${"function": "is_combinable_operation", "args": ["unknown_op"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (133, 'fc_comb_raises_on_non_string', $${"function": "is_combinable_operation", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=133 GROUP BY task_id;

COMMIT;