-- BD03 (task_id=132) function_call task_tests — 24 条

BEGIN;

DELETE FROM task_tests WHERE task_id=132;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (132, 'fc_loc_one_third', $${"function": "compute_data_locality_score", "args": [1, 3], "kwargs": {}}$$, $${"result": 0.3333333333333333, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (132, 'fc_loc_two_thirds', $${"function": "compute_data_locality_score", "args": [2, 3], "kwargs": {}}$$, $${"result": 0.6666666666666666, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (132, 'fc_loc_three_in_5', $${"function": "compute_data_locality_score", "args": [3, 5], "kwargs": {}}$$, $${"result": 0.6, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (132, 'fc_loc_perfect', $${"function": "compute_data_locality_score", "args": [3, 3], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (132, 'fc_loc_raises_on_zero_total', $${"function": "compute_data_locality_score", "args": [0, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 5),
  (132, 'fc_loc_raises_on_local_gt_total', $${"function": "compute_data_locality_score", "args": [5, 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (132, 'fc_loc_raises_on_non_int', $${"function": "compute_data_locality_score", "args": [1.0, 3], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (132, 'fc_repl_too_many', $${"function": "is_replication_factor_valid", "args": [5, 3], "kwargs": {}}$$, $${"result": false}$$, false, 'function_call', 8),
  (132, 'fc_repl_zero', $${"function": "is_replication_factor_valid", "args": [0, 10], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 9),
  (132, 'fc_repl_raises_on_negative', $${"function": "is_replication_factor_valid", "args": [-1, 10], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 10),
  (132, 'fc_repl_raises_on_non_int', $${"function": "is_replication_factor_valid", "args": [3.0, 10], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 11),
  (132, 'fc_re_repl_one_under', $${"function": "count_blocks_to_re_replicate", "args": [[3, 2, 3], 3], "kwargs": {}}$$, $${"result": 1}$$, false, 'function_call', 12),
  (132, 'fc_re_repl_three_under', $${"function": "count_blocks_to_re_replicate", "args": [[1, 2, 3, 1, 4], 3], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 13),
  (132, 'fc_re_repl_default_target', $${"function": "count_blocks_to_re_replicate", "args": [[3, 4, 5]], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 14),
  (132, 'fc_re_repl_custom_target_5', $${"function": "count_blocks_to_re_replicate", "args": [[3, 4, 5, 6], 5], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 15),
  (132, 'fc_re_repl_raises_on_negative_count', $${"function": "count_blocks_to_re_replicate", "args": [[3, -1, 3]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 16),
  (132, 'fc_re_repl_raises_on_non_list', $${"function": "count_blocks_to_re_replicate", "args": ["123"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 17),
  (132, 'fc_rr_3_replicas_3_racks', $${"function": "assign_replicas_round_robin", "args": [3, 3], "kwargs": {}}$$, $${"result": [0, 1, 2]}$$, false, 'function_call', 18),
  (132, 'fc_rr_4_replicas_3_racks', $${"function": "assign_replicas_round_robin", "args": [4, 3], "kwargs": {}}$$, $${"result": [0, 1, 2, 0]}$$, true, 'function_call', 19),
  (132, 'fc_rr_2_replicas_4_racks', $${"function": "assign_replicas_round_robin", "args": [2, 4], "kwargs": {}}$$, $${"result": [0, 1]}$$, true, 'function_call', 20),
  (132, 'fc_rr_5_replicas_2_racks', $${"function": "assign_replicas_round_robin", "args": [5, 2], "kwargs": {}}$$, $${"result": [0, 1, 0, 1, 0]}$$, true, 'function_call', 21),
  (132, 'fc_rr_raises_on_zero_racks', $${"function": "assign_replicas_round_robin", "args": [3, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (132, 'fc_rr_raises_on_negative_replicas', $${"function": "assign_replicas_round_robin", "args": [-1, 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (132, 'fc_rr_raises_on_non_int', $${"function": "assign_replicas_round_robin", "args": [3.0, 3], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=132 GROUP BY task_id;

COMMIT;