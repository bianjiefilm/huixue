-- NN04 (task_id=97) function_call task_tests — 31 条

BEGIN;

DELETE FROM task_tests WHERE task_id=97;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (97, 'fc_sd_zero_max', $${"function": "sigmoid_derivative", "args": [[0]], "kwargs": {}}$$, $${"result": [0.25], "tolerance": 0.0001}$$, false, 'function_call', 1),
  (97, 'fc_sd_diverse', $${"function": "sigmoid_derivative", "args": [[0, 1, -1, 2, -2]], "kwargs": {}}$$, $${"result": [0.25, 0.19661193, 0.19661193, 0.10499359, 0.10499359], "tolerance": 0.0001}$$, true, 'function_call', 2),
  (97, 'fc_sd_extreme_saturation', $${"function": "sigmoid_derivative", "args": [[10, -10]], "kwargs": {}}$$, $${"result": [0.0, 0.0], "tolerance": 0.0001}$$, true, 'function_call', 3),
  (97, 'fc_sd_half_values', $${"function": "sigmoid_derivative", "args": [[0.5, -0.5]], "kwargs": {}}$$, $${"result": [0.23500371, 0.23500371], "tolerance": 0.0001}$$, true, 'function_call', 4),
  (97, 'fc_sd_empty', $${"function": "sigmoid_derivative", "args": [[]], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 5),
  (97, 'fc_sd_raises_on_non_list', $${"function": "sigmoid_derivative", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (97, 'fc_sd_raises_on_non_numeric', $${"function": "sigmoid_derivative", "args": [[1, "a"]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (97, 'fc_mg_perfect', $${"function": "compute_mse_gradient", "args": [[1, 2, 3], [1, 2, 3]], "kwargs": {}}$$, $${"result": [0.0, 0.0, 0.0], "tolerance": 0.0001}$$, false, 'function_call', 8),
  (97, 'fc_mg_known', $${"function": "compute_mse_gradient", "args": [[3, 5], [5, 3]], "kwargs": {}}$$, $${"result": [2.0, -2.0], "tolerance": 0.0001}$$, true, 'function_call', 9),
  (97, 'fc_mg_four_samples', $${"function": "compute_mse_gradient", "args": [[0, 0, 0, 0], [1, 2, 3, 4]], "kwargs": {}}$$, $${"result": [0.5, 1.0, 1.5, 2.0], "tolerance": 0.0001}$$, true, 'function_call', 10),
  (97, 'fc_mg_negative_pred', $${"function": "compute_mse_gradient", "args": [[5], [3]], "kwargs": {}}$$, $${"result": [-4.0], "tolerance": 0.0001}$$, true, 'function_call', 11),
  (97, 'fc_mg_floats', $${"function": "compute_mse_gradient", "args": [[1.5, 2.5], [2.0, 2.0]], "kwargs": {}}$$, $${"result": [0.5, -0.5], "tolerance": 0.0001}$$, true, 'function_call', 12),
  (97, 'fc_mg_raises_on_length_mismatch', $${"function": "compute_mse_gradient", "args": [[1, 2], [1]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (97, 'fc_mg_raises_on_empty', $${"function": "compute_mse_gradient", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (97, 'fc_mg_raises_on_non_list', $${"function": "compute_mse_gradient", "args": ["abc", "def"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (97, 'fc_lbs_textbook', $${"function": "linear_backward_single", "args": [2.0, [3, 4], [1, 1]], "kwargs": {}}$$, $${"result": [[6.0, 8.0], [2.0, 2.0], 2.0], "tolerance": 0.0001}$$, false, 'function_call', 16),
  (97, 'fc_lbs_unit_dz', $${"function": "linear_backward_single", "args": [1.0, [1, 2, 3], [0.5, 0.5, 0.5]], "kwargs": {}}$$, $${"result": [[1.0, 2.0, 3.0], [0.5, 0.5, 0.5], 1.0], "tolerance": 0.0001}$$, true, 'function_call', 17),
  (97, 'fc_lbs_negative_dz', $${"function": "linear_backward_single", "args": [-3.0, [2], [5]], "kwargs": {}}$$, $${"result": [[-6.0], [-15.0], -3.0], "tolerance": 0.0001}$$, true, 'function_call', 18),
  (97, 'fc_lbs_zero_dz', $${"function": "linear_backward_single", "args": [0.0, [1, 2, 3], [4, 5, 6]], "kwargs": {}}$$, $${"result": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.0], "tolerance": 0.0001}$$, true, 'function_call', 19),
  (97, 'fc_lbs_zero_x', $${"function": "linear_backward_single", "args": [2.0, [0, 0], [1, 2]], "kwargs": {}}$$, $${"result": [[0.0, 0.0], [2.0, 4.0], 2.0], "tolerance": 0.0001}$$, true, 'function_call', 20),
  (97, 'fc_lbs_raises_on_dim_mismatch', $${"function": "linear_backward_single", "args": [1.0, [1, 2], [3]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (97, 'fc_lbs_raises_on_empty', $${"function": "linear_backward_single", "args": [1.0, [], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (97, 'fc_lbs_raises_on_non_list', $${"function": "linear_backward_single", "args": [1.0, "abc", [1, 2]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23),
  (97, 'fc_gds_textbook', $${"function": "gradient_descent_step", "args": [[0.5, 1.0], [-40, -4], 0.01], "kwargs": {}}$$, $${"result": [0.9, 1.04], "tolerance": 0.0001}$$, false, 'function_call', 24),
  (97, 'fc_gds_multiple_params', $${"function": "gradient_descent_step", "args": [[1, 2, 3], [0.1, 0.2, 0.3], 10.0], "kwargs": {}}$$, $${"result": [0.0, 0.0, 0.0], "tolerance": 0.0001}$$, true, 'function_call', 25),
  (97, 'fc_gds_unit_step', $${"function": "gradient_descent_step", "args": [[10], [5], 1.0], "kwargs": {}}$$, $${"result": [5.0], "tolerance": 0.0001}$$, true, 'function_call', 26),
  (97, 'fc_gds_negative_grad_increases', $${"function": "gradient_descent_step", "args": [[5], [-2], 0.5], "kwargs": {}}$$, $${"result": [6.0], "tolerance": 0.0001}$$, true, 'function_call', 27),
  (97, 'fc_gds_positive_grad_decreases', $${"function": "gradient_descent_step", "args": [[5], [2], 0.5], "kwargs": {}}$$, $${"result": [4.0], "tolerance": 0.0001}$$, true, 'function_call', 28),
  (97, 'fc_gds_raises_on_length_mismatch', $${"function": "gradient_descent_step", "args": [[1, 2], [0.1], 0.01], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 29),
  (97, 'fc_gds_raises_on_empty', $${"function": "gradient_descent_step", "args": [[], [], 0.01], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (97, 'fc_gds_raises_on_non_list', $${"function": "gradient_descent_step", "args": ["ab", [0.1, 0.2], 0.01], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 31);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=97 GROUP BY task_id;

COMMIT;