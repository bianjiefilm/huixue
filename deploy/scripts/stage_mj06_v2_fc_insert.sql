-- MJ06 (task_id=87) function_call task_tests — 32 条

BEGIN;

-- 删除现有错误的 io_based task_tests
DELETE FROM task_tests WHERE task_id=87;

-- 插入新 fc 协议 task_tests
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (87, 'fc_mse_textbook', $${"function": "compute_mse", "args": [[3, -0.5, 2, 7], [2.5, 0.0, 2, 8]], "kwargs": {}}$$, $${"result": 0.375, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (87, 'fc_mse_perfect', $${"function": "compute_mse", "args": [[1, 2, 3], [1, 2, 3]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (87, 'fc_mse_large', $${"function": "compute_mse", "args": [[10, 20], [0, 0]], "kwargs": {}}$$, $${"result": 250.0, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (87, 'fc_mse_doubled', $${"function": "compute_mse", "args": [[1, 2, 3], [2, 4, 6]], "kwargs": {}}$$, $${"result": 4.666666666666667, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (87, 'fc_mse_half_off', $${"function": "compute_mse", "args": [[5, 5, 5, 5], [4, 5, 5, 4]], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (87, 'fc_mse_raises_on_empty', $${"function": "compute_mse", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (87, 'fc_mse_raises_on_length_mismatch', $${"function": "compute_mse", "args": [[1, 2, 3], [1, 2]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (87, 'fc_mse_raises_on_non_list', $${"function": "compute_mse", "args": ["abc", "def"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (87, 'fc_r2_perfect', $${"function": "compute_r2", "args": [[1, 2, 3], [1, 2, 3]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 9),
  (87, 'fc_r2_096', $${"function": "compute_r2", "args": [[10, 20, 30, 40], [12, 18, 32, 38]], "kwargs": {}}$$, $${"result": 0.968, "tolerance": 1e-06}$$, true, 'function_call', 10),
  (87, 'fc_r2_negative', $${"function": "compute_r2", "args": [[1, 2, 3], [3, 3, 3]], "kwargs": {}}$$, $${"result": -1.5, "tolerance": 1e-06}$$, true, 'function_call', 11),
  (87, 'fc_r2_080', $${"function": "compute_r2", "args": [[2, 4, 6, 8], [3, 5, 7, 9]], "kwargs": {}}$$, $${"result": 0.8, "tolerance": 1e-06}$$, true, 'function_call', 12),
  (87, 'fc_r2_098', $${"function": "compute_r2", "args": [[1, 2, 3, 4, 5], [1.1, 2.1, 2.9, 4.2, 4.8]], "kwargs": {}}$$, $${"result": 0.989, "tolerance": 1e-06}$$, true, 'function_call', 13),
  (87, 'fc_r2_raises_on_zero_variance', $${"function": "compute_r2", "args": [[5, 5, 5], [5, 5, 5]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (87, 'fc_r2_raises_on_empty', $${"function": "compute_r2", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (87, 'fc_r2_raises_on_non_list', $${"function": "compute_r2", "args": ["abc", "def"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (87, 'fc_lp_textbook', $${"function": "linear_predict", "args": [[[1, 2], [3, 4]], [0.5, -0.3], 0.1], "kwargs": {}}$$, $${"result": [0.0, 0.4], "tolerance": 1e-06}$$, false, 'function_call', 17),
  (87, 'fc_lp_simple_doubling', $${"function": "linear_predict", "args": [[[1], [2], [3]], [2.0], 0.0], "kwargs": {}}$$, $${"result": [2.0, 4.0, 6.0], "tolerance": 1e-06}$$, true, 'function_call', 18),
  (87, 'fc_lp_three_features', $${"function": "linear_predict", "args": [[[1, 1, 1]], [1.0, 1.0, 1.0], 0.0], "kwargs": {}}$$, $${"result": [3.0], "tolerance": 1e-06}$$, true, 'function_call', 19),
  (87, 'fc_lp_only_bias', $${"function": "linear_predict", "args": [[[0, 0], [0, 0]], [1.0, 2.0], 5.0], "kwargs": {}}$$, $${"result": [5.0, 5.0], "tolerance": 1e-06}$$, true, 'function_call', 20),
  (87, 'fc_lp_negative_weights', $${"function": "linear_predict", "args": [[[10]], [-2.0], 3.0], "kwargs": {}}$$, $${"result": [-17.0], "tolerance": 1e-06}$$, true, 'function_call', 21),
  (87, 'fc_lp_raises_on_empty', $${"function": "linear_predict", "args": [[], [1.0], 0.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (87, 'fc_lp_raises_on_dim_mismatch', $${"function": "linear_predict", "args": [[[1, 2]], [1.0], 0.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (87, 'fc_lp_raises_on_non_list', $${"function": "linear_predict", "args": ["abc", [1.0], 0.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24),
  (87, 'fc_ne_y_equals_x', $${"function": "normal_equation", "args": [[[1, 1], [1, 2], [1, 3], [1, 4]], [1, 2, 3, 4]], "kwargs": {}}$$, $${"result": [0.0, 1.0], "tolerance": 0.0001}$$, false, 'function_call', 25),
  (87, 'fc_ne_y_2plus_x', $${"function": "normal_equation", "args": [[[1, 0], [1, 1], [1, 2]], [2, 3, 4]], "kwargs": {}}$$, $${"result": [2.0, 1.0], "tolerance": 0.0001}$$, true, 'function_call', 26),
  (87, 'fc_ne_y_1plus_2x', $${"function": "normal_equation", "args": [[[1, 1], [1, 2], [1, 3]], [3, 5, 7]], "kwargs": {}}$$, $${"result": [1.0, 2.0], "tolerance": 0.0001}$$, true, 'function_call', 27),
  (87, 'fc_ne_two_features', $${"function": "normal_equation", "args": [[[1, 1, 2], [1, 2, 1], [1, 3, 4], [1, 4, 3]], [0.0, 2.5, 2.0, 3.5]], "kwargs": {}}$$, $${"result": [1.0, 1.0, -0.5], "tolerance": 0.0001}$$, true, 'function_call', 28),
  (87, 'fc_ne_single_sample', $${"function": "normal_equation", "args": [[[1]], [5]], "kwargs": {}}$$, $${"result": [5.0], "tolerance": 0.0001}$$, true, 'function_call', 29),
  (87, 'fc_ne_raises_on_singular', $${"function": "normal_equation", "args": [[[1, 1], [1, 1]], [1, 2]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (87, 'fc_ne_raises_on_empty', $${"function": "normal_equation", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (87, 'fc_ne_raises_on_non_list', $${"function": "normal_equation", "args": ["abc", "def"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 32);

-- 验证
SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=87 GROUP BY task_id;

COMMIT;