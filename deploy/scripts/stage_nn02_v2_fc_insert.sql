-- NN02 (task_id=95) function_call task_tests — 30 条

BEGIN;

DELETE FROM task_tests WHERE task_id=95;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (95, 'fc_sig_five_diverse', $${"function": "sigmoid_activation", "args": [[0, 1, -1, 2, -2]], "kwargs": {}}$$, $${"result": [0.5, 0.7310585786, 0.2689414214, 0.8807970779, 0.1192029221], "tolerance": 0.0001}$$, false, 'function_call', 1),
  (95, 'fc_sig_extreme_positive', $${"function": "sigmoid_activation", "args": [[10, 100]], "kwargs": {}}$$, $${"result": [0.9999546, 1.0], "tolerance": 0.0001}$$, true, 'function_call', 2),
  (95, 'fc_sig_extreme_negative', $${"function": "sigmoid_activation", "args": [[-10, -100]], "kwargs": {}}$$, $${"result": [4.53979e-05, 0.0], "tolerance": 0.0001}$$, true, 'function_call', 3),
  (95, 'fc_sig_half_values', $${"function": "sigmoid_activation", "args": [[0.5, -0.5, 1.5, -1.5]], "kwargs": {}}$$, $${"result": [0.6224593312, 0.3775406688, 0.8175744762, 0.1824255238], "tolerance": 0.0001}$$, true, 'function_call', 4),
  (95, 'fc_sig_empty', $${"function": "sigmoid_activation", "args": [[]], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 5),
  (95, 'fc_sig_raises_on_non_list', $${"function": "sigmoid_activation", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (95, 'fc_sig_raises_on_non_numeric', $${"function": "sigmoid_activation", "args": [[1, "a", 2]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (95, 'fc_tanh_diverse', $${"function": "tanh_activation", "args": [[0, 1, -1, 2, -2]], "kwargs": {}}$$, $${"result": [0.0, 0.761594156, -0.761594156, 0.9640275801, -0.9640275801], "tolerance": 0.0001}$$, false, 'function_call', 8),
  (95, 'fc_tanh_one_nontrivial', $${"function": "tanh_activation", "args": [[1]], "kwargs": {}}$$, $${"result": [0.761594156], "tolerance": 0.0001}$$, true, 'function_call', 9),
  (95, 'fc_tanh_extreme', $${"function": "tanh_activation", "args": [[10, -10]], "kwargs": {}}$$, $${"result": [1.0, -1.0], "tolerance": 0.0001}$$, true, 'function_call', 10),
  (95, 'fc_tanh_symmetric', $${"function": "tanh_activation", "args": [[0.5, -0.5]], "kwargs": {}}$$, $${"result": [0.4621171573, -0.4621171573], "tolerance": 0.0001}$$, true, 'function_call', 11),
  (95, 'fc_tanh_empty', $${"function": "tanh_activation", "args": [[]], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 12),
  (95, 'fc_tanh_raises_on_non_list', $${"function": "tanh_activation", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 13),
  (95, 'fc_tanh_raises_on_non_numeric', $${"function": "tanh_activation", "args": [[1, null, 2]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 14),
  (95, 'fc_relu_mixed', $${"function": "relu_activation", "args": [[-2, 0, 1, 5, -10, 0.5]], "kwargs": {}}$$, $${"result": [0.0, 0.0, 1.0, 5.0, 0.0, 0.5], "tolerance": 0.0001}$$, false, 'function_call', 15),
  (95, 'fc_relu_negatives_zeroed', $${"function": "relu_activation", "args": [[-1, -2, -3]], "kwargs": {}}$$, $${"result": [0.0, 0.0, 0.0], "tolerance": 0.0001}$$, true, 'function_call', 16),
  (95, 'fc_relu_zero_boundary', $${"function": "relu_activation", "args": [[0.0, -0.0001, 0.0001]], "kwargs": {}}$$, $${"result": [0.0, 0.0, 0.0001], "tolerance": 0.0001}$$, true, 'function_call', 17),
  (95, 'fc_relu_large_negative', $${"function": "relu_activation", "args": [[-100, 100]], "kwargs": {}}$$, $${"result": [0.0, 100.0], "tolerance": 0.0001}$$, true, 'function_call', 18),
  (95, 'fc_relu_with_decimals', $${"function": "relu_activation", "args": [[-0.5, 0.5]], "kwargs": {}}$$, $${"result": [0.0, 0.5], "tolerance": 0.0001}$$, true, 'function_call', 19),
  (95, 'fc_relu_empty', $${"function": "relu_activation", "args": [[]], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 20),
  (95, 'fc_relu_raises_on_non_list', $${"function": "relu_activation", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 21),
  (95, 'fc_relu_raises_on_non_numeric', $${"function": "relu_activation", "args": [[1, "a"]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 22),
  (95, 'fc_lrelu_default_alpha', $${"function": "leaky_relu_activation", "args": [[-10, 0, 10]], "kwargs": {}}$$, $${"result": [-0.1, 0.0, 10.0], "tolerance": 0.0001}$$, false, 'function_call', 23),
  (95, 'fc_lrelu_alpha_01', $${"function": "leaky_relu_activation", "args": [[-5, 5]], "kwargs": {"alpha": 0.1}}$$, $${"result": [-0.5, 5.0], "tolerance": 0.0001}$$, true, 'function_call', 24),
  (95, 'fc_lrelu_alpha_05', $${"function": "leaky_relu_activation", "args": [[-2, 0, 2]], "kwargs": {"alpha": 0.5}}$$, $${"result": [-1.0, 0.0, 2.0], "tolerance": 0.0001}$$, true, 'function_call', 25),
  (95, 'fc_lrelu_alpha_zero_equals_relu', $${"function": "leaky_relu_activation", "args": [[-3, -1, 0, 1, 3]], "kwargs": {"alpha": 0.0}}$$, $${"result": [0.0, 0.0, 0.0, 1.0, 3.0], "tolerance": 0.0001}$$, true, 'function_call', 26),
  (95, 'fc_lrelu_mixed_decimals', $${"function": "leaky_relu_activation", "args": [[-100, -1, 0, 1, 100]], "kwargs": {"alpha": 0.01}}$$, $${"result": [-1.0, -0.01, 0.0, 1.0, 100.0], "tolerance": 0.0001}$$, true, 'function_call', 27),
  (95, 'fc_lrelu_empty', $${"function": "leaky_relu_activation", "args": [[]], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 28),
  (95, 'fc_lrelu_raises_on_non_list', $${"function": "leaky_relu_activation", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 29),
  (95, 'fc_lrelu_raises_on_non_numeric_alpha', $${"function": "leaky_relu_activation", "args": [[1, 2]], "kwargs": {"alpha": "x"}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 30);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=95 GROUP BY task_id;

COMMIT;