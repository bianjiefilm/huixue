-- NN06 (task_id=99) function_call task_tests — 20 条

BEGIN;

DELETE FROM task_tests WHERE task_id=99;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (99, 'fc_xavier_raises_on_zero_fan', $${"function": "xavier_init", "args": [0, 5], "kwargs": {"seed": 0}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 1),
  (99, 'fc_xavier_raises_on_non_int', $${"function": "xavier_init", "args": [3.5, 4], "kwargs": {"seed": 0}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 2),
  (99, 'fc_he_raises_on_zero_fan', $${"function": "he_init", "args": [5, 0], "kwargs": {"seed": 0}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 3),
  (99, 'fc_he_raises_on_non_int', $${"function": "he_init", "args": [3, "4"], "kwargs": {"seed": 0}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 4),
  (99, 'fc_cgh_healthy', $${"function": "check_gradient_health", "args": [[0.1, -0.2, 0.05]], "kwargs": {}}$$, $${"result": {"mean": -0.016666666666666666, "std": 0.13123346456686352, "max_abs": 0.2, "has_vanishing": false, "has_exploding": false}, "tolerance": 0.0001}$$, false, 'function_call', 5),
  (99, 'fc_cgh_vanishing', $${"function": "check_gradient_health", "args": [[1e-09, -1e-09, 5e-10]], "kwargs": {}}$$, $${"result": {"mean": 1.6666666666666669e-10, "std": 8.498365855987974e-10, "max_abs": 1e-09, "has_vanishing": true, "has_exploding": false}, "tolerance": 0.0001}$$, true, 'function_call', 6),
  (99, 'fc_cgh_exploding', $${"function": "check_gradient_health", "args": [[0.1, 100000.0, -0.2]], "kwargs": {}}$$, $${"result": {"mean": 33333.3, "std": 47140.475649488304, "max_abs": 100000.0, "has_vanishing": false, "has_exploding": true}, "tolerance": 1.0}$$, true, 'function_call', 7),
  (99, 'fc_cgh_specific_values', $${"function": "check_gradient_health", "args": [[1, 2, 3]], "kwargs": {}}$$, $${"result": {"mean": 2.0, "std": 0.816496580927726, "max_abs": 3.0, "has_vanishing": false, "has_exploding": false}, "tolerance": 0.0001}$$, true, 'function_call', 8),
  (99, 'fc_cgh_negative_max_abs', $${"function": "check_gradient_health", "args": [[-5, -3, -1]], "kwargs": {}}$$, $${"result": {"mean": -3.0, "std": 1.632993161855452, "max_abs": 5.0, "has_vanishing": false, "has_exploding": false}, "tolerance": 0.0001}$$, true, 'function_call', 9),
  (99, 'fc_cgh_zero_grad', $${"function": "check_gradient_health", "args": [[0, 0, 0]], "kwargs": {}}$$, $${"result": {"mean": 0.0, "std": 0.0, "max_abs": 0.0, "has_vanishing": true, "has_exploding": false}, "tolerance": 0.0001}$$, true, 'function_call', 10),
  (99, 'fc_cgh_raises_on_empty', $${"function": "check_gradient_health", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 11),
  (99, 'fc_cgh_raises_on_non_list', $${"function": "check_gradient_health", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 12),
  (99, 'fc_fd_two_layers_relu_sigmoid', $${"function": "forward_deep", "args": [[[1]], [[[1]], [[1]]], [[0], [0]], ["relu", "sigmoid"]], "kwargs": {}}$$, $${"result": [[0.7310585786300049]], "tolerance": 0.0001}$$, false, 'function_call', 13),
  (99, 'fc_fd_three_layers_all_relu', $${"function": "forward_deep", "args": [[[1]], [[[2]], [[2]], [[2]]], [[0], [0], [0]], ["relu", "relu", "relu"]], "kwargs": {}}$$, $${"result": [[8.0]], "tolerance": 0.0001}$$, true, 'function_call', 14),
  (99, 'fc_fd_with_negative_relu_kills_then_bias', $${"function": "forward_deep", "args": [[[-1]], [[[1]], [[5]]], [[0], [3]], ["relu", "linear"]], "kwargs": {}}$$, $${"result": [[3.0]], "tolerance": 0.0001}$$, true, 'function_call', 15),
  (99, 'fc_fd_linear_activation', $${"function": "forward_deep", "args": [[[2]], [[[3]]], [[1]], ["linear"]], "kwargs": {}}$$, $${"result": [[7.0]], "tolerance": 0.0001}$$, true, 'function_call', 16),
  (99, 'fc_fd_tanh_layer', $${"function": "forward_deep", "args": [[[1]], [[[1]]], [[0]], ["tanh"]], "kwargs": {}}$$, $${"result": [[0.7615941559557649]], "tolerance": 0.0001}$$, true, 'function_call', 17),
  (99, 'fc_fd_raises_on_length_mismatch', $${"function": "forward_deep", "args": [[[1]], [[[1]]], [[0], [0]], ["relu"]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (99, 'fc_fd_raises_on_invalid_activation', $${"function": "forward_deep", "args": [[[1]], [[[1]]], [[0]], ["xxx"]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 19),
  (99, 'fc_fd_raises_on_non_list', $${"function": "forward_deep", "args": ["abc", [[[1]]], [[0]], ["relu"]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 20);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=99 GROUP BY task_id;

COMMIT;