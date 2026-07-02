-- BD09 (task_id=138) function_call task_tests — 31 条

BEGIN;

DELETE FROM task_tests WHERE task_id=138;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (138, 'fc_salt_typical', $${"function": "design_row_key_with_salt", "args": ["event", 1714003200, 4], "kwargs": {}}$$, $${"result": "0-event-1714003200"}$$, false, 'function_call', 1),
  (138, 'fc_salt_with_remainder', $${"function": "design_row_key_with_salt", "args": ["user", 10, 4], "kwargs": {}}$$, $${"result": "2-user-10"}$$, true, 'function_call', 2),
  (138, 'fc_salt_count_8', $${"function": "design_row_key_with_salt", "args": ["device", 15, 8], "kwargs": {}}$$, $${"result": "7-device-15"}$$, true, 'function_call', 3),
  (138, 'fc_salt_zero_timestamp', $${"function": "design_row_key_with_salt", "args": ["x", 0, 4], "kwargs": {}}$$, $${"result": "0-x-0"}$$, true, 'function_call', 4),
  (138, 'fc_salt_count_1', $${"function": "design_row_key_with_salt", "args": ["y", 100, 1], "kwargs": {}}$$, $${"result": "0-y-100"}$$, true, 'function_call', 5),
  (138, 'fc_salt_raises_on_empty_prefix', $${"function": "design_row_key_with_salt", "args": ["", 100, 4], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (138, 'fc_salt_raises_on_zero_salt_count', $${"function": "design_row_key_with_salt", "args": ["x", 100, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (138, 'fc_salt_raises_on_non_string', $${"function": "design_row_key_with_salt", "args": [123, 100, 4], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (138, 'fc_region_typical', $${"function": "compute_region_count", "args": [100.0], "kwargs": {}}$$, $${"result": 10}$$, false, 'function_call', 9),
  (138, 'fc_region_partial_ceil', $${"function": "compute_region_count", "args": [15.0], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 10),
  (138, 'fc_region_custom_size', $${"function": "compute_region_count", "args": [100.0, 20.0], "kwargs": {}}$$, $${"result": 5}$$, true, 'function_call', 11),
  (138, 'fc_region_just_above_one', $${"function": "compute_region_count", "args": [11.0], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 12),
  (138, 'fc_region_minimum', $${"function": "compute_region_count", "args": [1.0], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 13),
  (138, 'fc_region_raises_on_zero', $${"function": "compute_region_count", "args": [0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (138, 'fc_region_raises_on_zero_region_size', $${"function": "compute_region_count", "args": [10, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (138, 'fc_hot_yes', $${"function": "is_hot_row_key", "args": [{"a": 60, "b": 30, "c": 10}, 100], "kwargs": {}}$$, $${"result": true}$$, false, 'function_call', 16),
  (138, 'fc_hot_no', $${"function": "is_hot_row_key", "args": [{"a": 30, "b": 30, "c": 40}, 100], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 17),
  (138, 'fc_hot_at_threshold', $${"function": "is_hot_row_key", "args": [{"a": 50, "b": 50}, 100], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 18),
  (138, 'fc_hot_just_above', $${"function": "is_hot_row_key", "args": [{"a": 51, "b": 49}, 100], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 19),
  (138, 'fc_hot_custom_threshold', $${"function": "is_hot_row_key", "args": [{"a": 40, "b": 60}, 100, 0.3], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 20),
  (138, 'fc_hot_empty_dict', $${"function": "is_hot_row_key", "args": [{}, 100], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 21),
  (138, 'fc_hot_raises_on_zero_total', $${"function": "is_hot_row_key", "args": [{"a": 1}, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (138, 'fc_hot_raises_on_non_dict', $${"function": "is_hot_row_key", "args": ["counts", 100], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23),
  (138, 'fc_hr_typical', $${"function": "compute_block_cache_hit_rate", "args": [1000, 900], "kwargs": {}}$$, $${"result": 0.9, "tolerance": 1e-06}$$, false, 'function_call', 24),
  (138, 'fc_hr_half', $${"function": "compute_block_cache_hit_rate", "args": [1000, 500], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 25),
  (138, 'fc_hr_perfect', $${"function": "compute_block_cache_hit_rate", "args": [100, 100], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, true, 'function_call', 26),
  (138, 'fc_hr_all_miss', $${"function": "compute_block_cache_hit_rate", "args": [100, 0], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 27),
  (138, 'fc_hr_decimal', $${"function": "compute_block_cache_hit_rate", "args": [4, 3], "kwargs": {}}$$, $${"result": 0.75, "tolerance": 1e-06}$$, true, 'function_call', 28),
  (138, 'fc_hr_raises_on_zero_reads', $${"function": "compute_block_cache_hit_rate", "args": [0, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 29),
  (138, 'fc_hr_raises_on_hits_gt_reads', $${"function": "compute_block_cache_hit_rate", "args": [100, 200], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (138, 'fc_hr_raises_on_non_int', $${"function": "compute_block_cache_hit_rate", "args": [100.0, 50], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 31);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=138 GROUP BY task_id;

COMMIT;