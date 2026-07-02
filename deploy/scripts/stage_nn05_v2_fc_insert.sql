-- NN05 (task_id=98) function_call task_tests — 32 条

BEGIN;

DELETE FROM task_tests WHERE task_id=98;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (98, 'fc_fp_zero_input', $${"function": "forward_propagate", "args": [[[0]], [[1]], [0], [[1]], [0]], "kwargs": {}}$$, $${"result": [[[0]], [[0.0]], [[0.0]], [[0.5]]], "tolerance": 0.0001}$$, false, 'function_call', 1),
  (98, 'fc_fp_unit_input', $${"function": "forward_propagate", "args": [[[1]], [[1]], [0], [[1]], [0]], "kwargs": {}}$$, $${"result": [[[1]], [[1]], [[1]], [[0.7310585786300049]]], "tolerance": 0.0001}$$, true, 'function_call', 2),
  (98, 'fc_fp_negative_z1_relu_zeros', $${"function": "forward_propagate", "args": [[[-2]], [[1]], [0], [[1]], [0]], "kwargs": {}}$$, $${"result": [[[-2]], [[0.0]], [[0.0]], [[0.5]]], "tolerance": 0.0001}$$, true, 'function_call', 3),
  (98, 'fc_fp_two_by_two', $${"function": "forward_propagate", "args": [[[1, 0], [0, 1]], [[1, 0], [0, 1]], [0, 0], [[1], [1]], [0]], "kwargs": {}}$$, $${"result": [[[1, 0], [0, 1]], [[1, 0.0], [0.0, 1]], [[1.0], [1.0]], [[0.7310585786300049], [0.7310585786300049]]], "tolerance": 0.0001}$$, true, 'function_call', 4),
  (98, 'fc_fp_with_bias', $${"function": "forward_propagate", "args": [[[0]], [[1]], [5], [[1]], [3]], "kwargs": {}}$$, $${"result": [[[5]], [[5]], [[8]], [[0.9996646498695336]]], "tolerance": 0.0001}$$, true, 'function_call', 5),
  (98, 'fc_fp_raises_on_dim_mismatch', $${"function": "forward_propagate", "args": [[[1, 2]], [[1]], [0], [[1]], [0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (98, 'fc_fp_raises_on_empty', $${"function": "forward_propagate", "args": [[], [[1]], [0], [[1]], [0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (98, 'fc_fp_raises_on_non_list', $${"function": "forward_propagate", "args": ["abc", [[1]], [0], [[1]], [0]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (98, 'fc_bp_textbook_2x2', $${"function": "backward_propagate", "args": [[[1, 0], [0, 1]], [1, 0], [[1, 0], [0, 1]], [[1, 0.0], [0.0, 1]], [[0.7310585786300049], [0.7310585786300049]], [[1], [1]]], "kwargs": {}}$$, $${"result": [[[-0.13447071068499755, 0.0], [0.0, 0.36552928931500245]], [-0.13447071068499755, 0.36552928931500245], [[-0.13447071068499755], [0.36552928931500245]], [0.2310585786300049]], "tolerance": 0.0001}$$, false, 'function_call', 9),
  (98, 'fc_bp_zero_loss_gradient', $${"function": "backward_propagate", "args": [[[1], [1]], [1, 0], [[1], [1]], [[1], [1]], [[0.7310585786300049], [0.7310585786300049]], [[1]]], "kwargs": {}}$$, $${"result": [[[0.2310585786300049]], [0.2310585786300049], [[0.2310585786300049]], [0.2310585786300049]], "tolerance": 0.0001}$$, true, 'function_call', 10),
  (98, 'fc_bp_dW2_shape', $${"function": "backward_propagate", "args": [[[1, 1], [1, 1]], [1, 0], [[2, 2], [2, 2]], [[2, 2], [2, 2]], [[0.9820137900379085], [0.9820137900379085]], [[1], [1]]], "kwargs": {}}$$, $${"result": [[[0.48201379003790845, 0.48201379003790845], [0.48201379003790845, 0.48201379003790845]], [0.48201379003790845, 0.48201379003790845], [[0.9640275800758169], [0.9640275800758169]], [0.48201379003790845]], "tolerance": 0.0001}$$, true, 'function_call', 11),
  (98, 'fc_bp_relu_mask', $${"function": "backward_propagate", "args": [[[1]], [1], [[-2]], [[0.0]], [[0.5]], [[1]]], "kwargs": {}}$$, $${"result": [[[0.0]], [0.0], [[0.0]], [-0.5]], "tolerance": 0.0001}$$, true, 'function_call', 12),
  (98, 'fc_bp_basic_simple', $${"function": "backward_propagate", "args": [[[1]], [1], [[1]], [[1]], [[0.7310585786300049]], [[1]]], "kwargs": {}}$$, $${"result": [[[-0.2689414213699951]], [-0.2689414213699951], [[-0.2689414213699951]], [-0.2689414213699951]], "tolerance": 0.0001}$$, true, 'function_call', 13),
  (98, 'fc_bp_raises_on_dim_mismatch', $${"function": "backward_propagate", "args": [[[1]], [1, 0], [[1]], [[1]], [[0.5]], [[1]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (98, 'fc_bp_raises_on_empty', $${"function": "backward_propagate", "args": [[], [], [], [], [], [[1]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (98, 'fc_bp_raises_on_non_list', $${"function": "backward_propagate", "args": ["ab", [0, 1], [[1]], [[1]], [[0.5]], [[1]]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (98, 'fc_pl_basic', $${"function": "predict_labels", "args": [[[0.1], [0.5], [0.9]]], "kwargs": {}}$$, $${"result": [0, 1, 1]}$$, false, 'function_call', 17),
  (98, 'fc_pl_high_threshold', $${"function": "predict_labels", "args": [[[0.5], [0.99]]], "kwargs": {"threshold": 0.95}}$$, $${"result": [0, 1]}$$, true, 'function_call', 18),
  (98, 'fc_pl_low_threshold', $${"function": "predict_labels", "args": [[[0.05], [0.2]]], "kwargs": {"threshold": 0.1}}$$, $${"result": [0, 1]}$$, true, 'function_call', 19),
  (98, 'fc_pl_all_above', $${"function": "predict_labels", "args": [[[0.6], [0.7], [0.8]]], "kwargs": {}}$$, $${"result": [1, 1, 1]}$$, true, 'function_call', 20),
  (98, 'fc_pl_all_below', $${"function": "predict_labels", "args": [[[0.1], [0.2], [0.3]]], "kwargs": {}}$$, $${"result": [0, 0, 0]}$$, true, 'function_call', 21),
  (98, 'fc_pl_raises_on_wrong_shape', $${"function": "predict_labels", "args": [[[0.5, 0.5]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (98, 'fc_pl_raises_on_empty', $${"function": "predict_labels", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (98, 'fc_pl_raises_on_non_list', $${"function": "predict_labels", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24),
  (98, 'fc_acc_perfect', $${"function": "compute_accuracy_binary", "args": [[1, 0, 1, 0], [1, 0, 1, 0]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 0.0001}$$, false, 'function_call', 25),
  (98, 'fc_acc_all_wrong', $${"function": "compute_accuracy_binary", "args": [[1, 0, 1, 0], [0, 1, 0, 1]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 0.0001}$$, true, 'function_call', 26),
  (98, 'fc_acc_three_quarters', $${"function": "compute_accuracy_binary", "args": [[1, 0, 1, 0], [1, 0, 1, 1]], "kwargs": {}}$$, $${"result": 0.75, "tolerance": 0.0001}$$, true, 'function_call', 27),
  (98, 'fc_acc_half', $${"function": "compute_accuracy_binary", "args": [[1, 1, 0, 0], [1, 0, 1, 0]], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 0.0001}$$, true, 'function_call', 28),
  (98, 'fc_acc_one_third', $${"function": "compute_accuracy_binary", "args": [[1, 1, 1], [1, 0, 0]], "kwargs": {}}$$, $${"result": 0.3333333333333333, "tolerance": 0.0001}$$, true, 'function_call', 29),
  (98, 'fc_acc_raises_on_length_mismatch', $${"function": "compute_accuracy_binary", "args": [[1, 0], [1]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (98, 'fc_acc_raises_on_empty', $${"function": "compute_accuracy_binary", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (98, 'fc_acc_raises_on_invalid_label', $${"function": "compute_accuracy_binary", "args": [[1, 2], [1, 0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 32);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=98 GROUP BY task_id;

COMMIT;