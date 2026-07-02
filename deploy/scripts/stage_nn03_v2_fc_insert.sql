-- NN03 (task_id=96) function_call task_tests — 30 条

BEGIN;

DELETE FROM task_tests WHERE task_id=96;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (96, 'fc_lf_textbook', $${"function": "linear_forward", "args": [[1, 2], [0.5, -0.3], 0.1], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 0.0001}$$, false, 'function_call', 1),
  (96, 'fc_lf_simple_doubling', $${"function": "linear_forward", "args": [[3], [2.0], 0.0], "kwargs": {}}$$, $${"result": 6.0, "tolerance": 0.0001}$$, true, 'function_call', 2),
  (96, 'fc_lf_only_bias', $${"function": "linear_forward", "args": [[0, 0], [1.0, 2.0], 5.0], "kwargs": {}}$$, $${"result": 5.0, "tolerance": 0.0001}$$, true, 'function_call', 3),
  (96, 'fc_lf_three_features', $${"function": "linear_forward", "args": [[1, 1, 1], [0.5, 0.5, 0.5], 0.5], "kwargs": {}}$$, $${"result": 2.0, "tolerance": 0.0001}$$, true, 'function_call', 4),
  (96, 'fc_lf_negative_result', $${"function": "linear_forward", "args": [[2], [-1.0], 0.0], "kwargs": {}}$$, $${"result": -2.0, "tolerance": 0.0001}$$, true, 'function_call', 5),
  (96, 'fc_lf_raises_on_length_mismatch', $${"function": "linear_forward", "args": [[1, 2], [0.5], 0.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (96, 'fc_lf_raises_on_empty', $${"function": "linear_forward", "args": [[], [], 0.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (96, 'fc_lf_raises_on_non_list', $${"function": "linear_forward", "args": ["ab", [0.5, 0.5], 0.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (96, 'fc_lfb_textbook', $${"function": "linear_forward_batch", "args": [[[1, 2]], [[3], [4]], [5]], "kwargs": {}}$$, $${"result": [[16.0]], "tolerance": 0.0001}$$, false, 'function_call', 9),
  (96, 'fc_lfb_two_samples_two_outputs', $${"function": "linear_forward_batch", "args": [[[1, 0], [0, 1]], [[1, 2], [3, 4]], [0, 0]], "kwargs": {}}$$, $${"result": [[1.0, 2.0], [3.0, 4.0]], "tolerance": 0.0001}$$, true, 'function_call', 10),
  (96, 'fc_lfb_with_bias_broadcast', $${"function": "linear_forward_batch", "args": [[[1, 1]], [[1], [1]], [10]], "kwargs": {}}$$, $${"result": [[12.0]], "tolerance": 0.0001}$$, true, 'function_call', 11),
  (96, 'fc_lfb_three_samples_one_output', $${"function": "linear_forward_batch", "args": [[[1], [2], [3]], [[2]], [1]], "kwargs": {}}$$, $${"result": [[3.0], [5.0], [7.0]], "tolerance": 0.0001}$$, true, 'function_call', 12),
  (96, 'fc_lfb_zero_input', $${"function": "linear_forward_batch", "args": [[[0, 0, 0]], [[1], [2], [3]], [7]], "kwargs": {}}$$, $${"result": [[7.0]], "tolerance": 0.0001}$$, true, 'function_call', 13),
  (96, 'fc_lfb_raises_on_dim_mismatch', $${"function": "linear_forward_batch", "args": [[[1, 2]], [[1]], [0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (96, 'fc_lfb_raises_on_empty', $${"function": "linear_forward_batch", "args": [[], [[1]], [0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (96, 'fc_lfb_raises_on_non_list', $${"function": "linear_forward_batch", "args": ["abc", [[1]], [0]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (96, 'fc_bce_perfect', $${"function": "binary_cross_entropy", "args": [[1, 0], [0.99999999, 1e-08]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 0.0001}$$, false, 'function_call', 17),
  (96, 'fc_bce_uniform_half', $${"function": "binary_cross_entropy", "args": [[1, 0], [0.5, 0.5]], "kwargs": {}}$$, $${"result": 0.6931472, "tolerance": 0.0001}$$, true, 'function_call', 18),
  (96, 'fc_bce_known_specific', $${"function": "binary_cross_entropy", "args": [[1, 0, 1, 0], [0.9, 0.1, 0.8, 0.2]], "kwargs": {}}$$, $${"result": 0.164252033486018, "tolerance": 0.0001}$$, true, 'function_call', 19),
  (96, 'fc_bce_all_correct_high_conf', $${"function": "binary_cross_entropy", "args": [[1, 1, 0, 0], [0.99, 0.99, 0.01, 0.01]], "kwargs": {}}$$, $${"result": 0.01005033585350145, "tolerance": 0.0001}$$, true, 'function_call', 20),
  (96, 'fc_bce_raises_on_length_mismatch', $${"function": "binary_cross_entropy", "args": [[1, 0], [0.5]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (96, 'fc_bce_raises_on_empty', $${"function": "binary_cross_entropy", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (96, 'fc_bce_raises_on_non_list', $${"function": "binary_cross_entropy", "args": ["01", "01"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23),
  (96, 'fc_cce_perfect', $${"function": "categorical_cross_entropy", "args": [[0, 1, 2], [[0.99999999, 1e-09, 1e-09], [1e-09, 0.99999999, 1e-09], [1e-09, 1e-09, 0.99999999]]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 0.0001}$$, false, 'function_call', 24),
  (96, 'fc_cce_uniform_3class', $${"function": "categorical_cross_entropy", "args": [[0, 1, 2], [[0.3333333333333333, 0.3333333333333333, 0.3333333333333333], [0.3333333333333333, 0.3333333333333333, 0.3333333333333333], [0.3333333333333333, 0.3333333333333333, 0.3333333333333333]]], "kwargs": {}}$$, $${"result": 1.0986122886681098, "tolerance": 0.0001}$$, true, 'function_call', 25),
  (96, 'fc_cce_two_class', $${"function": "categorical_cross_entropy", "args": [[0, 1], [[0.7, 0.3], [0.4, 0.6]]], "kwargs": {}}$$, $${"result": 0.4337502838523616, "tolerance": 0.0001}$$, true, 'function_call', 26),
  (96, 'fc_cce_specific_known', $${"function": "categorical_cross_entropy", "args": [[1, 2, 0], [[0.1, 0.8, 0.1], [0.2, 0.3, 0.5], [0.6, 0.3, 0.1]]], "kwargs": {}}$$, $${"result": 0.47570545188004854, "tolerance": 0.0001}$$, true, 'function_call', 27),
  (96, 'fc_cce_raises_on_index_out_of_range', $${"function": "categorical_cross_entropy", "args": [[5], [[0.5, 0.5]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 28),
  (96, 'fc_cce_raises_on_length_mismatch', $${"function": "categorical_cross_entropy", "args": [[0, 1], [[0.5, 0.5]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 29),
  (96, 'fc_cce_raises_on_non_list', $${"function": "categorical_cross_entropy", "args": ["01", [[0.5, 0.5]]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 30);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=96 GROUP BY task_id;

COMMIT;