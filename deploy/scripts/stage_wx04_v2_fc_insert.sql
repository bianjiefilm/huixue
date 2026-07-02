-- WX04 (task_id=121) function_call task_tests — 28 条

BEGIN;

DELETE FROM task_tests WHERE task_id=121;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (121, 'fc_iqr_normal_value', $${"function": "is_outlier_iqr", "args": [15, 10, 20, 1.5], "kwargs": {}}$$, $${"result": false}$$, false, 'function_call', 1),
  (121, 'fc_iqr_low_outlier', $${"function": "is_outlier_iqr", "args": [-10, 10, 20, 1.5], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 2),
  (121, 'fc_iqr_at_upper_boundary', $${"function": "is_outlier_iqr", "args": [35, 10, 20, 1.5], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 3),
  (121, 'fc_iqr_extreme_multiplier', $${"function": "is_outlier_iqr", "args": [40, 10, 20, 3.0], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 4),
  (121, 'fc_iqr_q1_eq_q3_a', $${"function": "is_outlier_iqr", "args": [15, 10, 10, 1.5], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 5),
  (121, 'fc_iqr_q1_eq_q3_b', $${"function": "is_outlier_iqr", "args": [10, 10, 10, 1.5], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 6),
  (121, 'fc_iqr_raises_on_q1_gt_q3', $${"function": "is_outlier_iqr", "args": [15, 20, 10, 1.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (121, 'fc_iqr_raises_on_non_numeric', $${"function": "is_outlier_iqr", "args": ["15", 10, 20, 1.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (121, 'fc_bounds_normal', $${"function": "compute_iqr_bounds", "args": [10, 20, 1.5], "kwargs": {}}$$, $${"result": [-5.0, 35.0], "tolerance": 1e-06}$$, false, 'function_call', 9),
  (121, 'fc_bounds_extreme_multiplier', $${"function": "compute_iqr_bounds", "args": [10, 20, 3.0], "kwargs": {}}$$, $${"result": [-20.0, 50.0], "tolerance": 1e-06}$$, true, 'function_call', 10),
  (121, 'fc_bounds_default', $${"function": "compute_iqr_bounds", "args": [10, 20], "kwargs": {}}$$, $${"result": [-5.0, 35.0], "tolerance": 1e-06}$$, true, 'function_call', 11),
  (121, 'fc_bounds_negative_q1', $${"function": "compute_iqr_bounds", "args": [-5, 5, 1.5], "kwargs": {}}$$, $${"result": [-20.0, 20.0], "tolerance": 1e-06}$$, true, 'function_call', 12),
  (121, 'fc_bounds_q1_eq_q3', $${"function": "compute_iqr_bounds", "args": [10, 10, 1.5], "kwargs": {}}$$, $${"result": [10.0, 10.0], "tolerance": 1e-06}$$, true, 'function_call', 13),
  (121, 'fc_bounds_raises_on_q1_gt_q3', $${"function": "compute_iqr_bounds", "args": [20, 10], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (121, 'fc_bounds_raises_on_non_numeric', $${"function": "compute_iqr_bounds", "args": ["10", 20], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (121, 'fc_clip_in_range', $${"function": "clip_value_to_range", "args": [15, 10, 20], "kwargs": {}}$$, $${"result": 15.0, "tolerance": 1e-06}$$, false, 'function_call', 16),
  (121, 'fc_clip_below_lower', $${"function": "clip_value_to_range", "args": [5, 10, 20], "kwargs": {}}$$, $${"result": 10.0, "tolerance": 1e-06}$$, true, 'function_call', 17),
  (121, 'fc_clip_above_upper', $${"function": "clip_value_to_range", "args": [25, 10, 20], "kwargs": {}}$$, $${"result": 20.0, "tolerance": 1e-06}$$, true, 'function_call', 18),
  (121, 'fc_clip_at_lower_boundary', $${"function": "clip_value_to_range", "args": [10, 10, 20], "kwargs": {}}$$, $${"result": 10.0, "tolerance": 1e-06}$$, true, 'function_call', 19),
  (121, 'fc_clip_negative_range', $${"function": "clip_value_to_range", "args": [-15, -10, -5], "kwargs": {}}$$, $${"result": -10.0, "tolerance": 1e-06}$$, true, 'function_call', 20),
  (121, 'fc_clip_raises_on_lower_gt_upper', $${"function": "clip_value_to_range", "args": [15, 20, 10], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (121, 'fc_co_no_outliers', $${"function": "count_outliers", "args": [[10, 15, 20], 5, 25], "kwargs": {}}$$, $${"result": 0}$$, false, 'function_call', 22),
  (121, 'fc_co_one_high', $${"function": "count_outliers", "args": [[10, 15, 30], 5, 25], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 23),
  (121, 'fc_co_one_low', $${"function": "count_outliers", "args": [[0, 15, 20], 5, 25], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 24),
  (121, 'fc_co_mixed', $${"function": "count_outliers", "args": [[0, 10, 15, 30, 50], 5, 25], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 25),
  (121, 'fc_co_at_boundaries', $${"function": "count_outliers", "args": [[5, 25, 4, 26], 5, 25], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 26),
  (121, 'fc_co_raises_on_lower_gt_upper', $${"function": "count_outliers", "args": [[10, 20], 30, 10], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 27),
  (121, 'fc_co_raises_on_non_list', $${"function": "count_outliers", "args": ["10,20", 0, 100], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 28);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=121 GROUP BY task_id;

COMMIT;