-- NN07 (task_id=100) function_call task_tests — 29 条

BEGIN;

DELETE FROM task_tests WHERE task_id=100;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (100, 'fc_sgd_textbook', $${"function": "sgd_update", "args": [[1.0, 2.0, 3.0], [0.1, 0.2, 0.3], 10.0], "kwargs": {}}$$, $${"result": [0.0, 0.0, 0.0], "tolerance": 1e-06}$$, false, 'function_call', 1),
  (100, 'fc_sgd_negative_grad', $${"function": "sgd_update", "args": [[5.0], [-2.0], 0.5], "kwargs": {}}$$, $${"result": [6.0], "tolerance": 1e-06}$$, true, 'function_call', 2),
  (100, 'fc_sgd_small_lr', $${"function": "sgd_update", "args": [[10.0], [1.0], 0.01], "kwargs": {}}$$, $${"result": [9.99], "tolerance": 1e-06}$$, true, 'function_call', 3),
  (100, 'fc_sgd_multi_param', $${"function": "sgd_update", "args": [[1, 2, 3, 4], [1, 1, 1, 1], 0.5], "kwargs": {}}$$, $${"result": [0.5, 1.5, 2.5, 3.5], "tolerance": 1e-06}$$, true, 'function_call', 4),
  (100, 'fc_sgd_raises_on_length_mismatch', $${"function": "sgd_update", "args": [[1, 2], [1], 0.1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 5),
  (100, 'fc_sgd_raises_on_empty', $${"function": "sgd_update", "args": [[], [], 0.1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (100, 'fc_sgd_raises_on_non_list', $${"function": "sgd_update", "args": ["ab", [0.1, 0.2], 0.01], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (100, 'fc_mom_first_step', $${"function": "momentum_update", "args": [[10.0], [1.0], [0.0], 0.1, 0.9], "kwargs": {}}$$, $${"result": [[9.9], [1.0]], "tolerance": 1e-06}$$, false, 'function_call', 8),
  (100, 'fc_mom_second_step', $${"function": "momentum_update", "args": [[10.0], [1.0], [1.0], 0.1, 0.9], "kwargs": {}}$$, $${"result": [[9.81], [1.9]], "tolerance": 1e-06}$$, true, 'function_call', 9),
  (100, 'fc_mom_zero_momentum_equals_sgd', $${"function": "momentum_update", "args": [[10.0], [2.0], [5.0], 0.5, 0.0], "kwargs": {}}$$, $${"result": [[9.0], [2.0]], "tolerance": 1e-06}$$, true, 'function_call', 10),
  (100, 'fc_mom_multi_param', $${"function": "momentum_update", "args": [[1, 2], [0.1, 0.2], [0, 0], 1.0, 0.5], "kwargs": {}}$$, $${"result": [[0.9, 1.8], [0.1, 0.2]], "tolerance": 1e-06}$$, true, 'function_call', 11),
  (100, 'fc_mom_negative_grad', $${"function": "momentum_update", "args": [[5.0], [-1.0], [0.0], 0.5, 0.0], "kwargs": {}}$$, $${"result": [[5.5], [-1.0]], "tolerance": 1e-06}$$, true, 'function_call', 12),
  (100, 'fc_mom_raises_on_length_mismatch', $${"function": "momentum_update", "args": [[1, 2], [0.1], [0, 0], 0.1, 0.9], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (100, 'fc_mom_raises_on_empty', $${"function": "momentum_update", "args": [[], [], [], 0.1, 0.9], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (100, 'fc_mom_raises_on_non_list', $${"function": "momentum_update", "args": ["ab", [0.1], [0], 0.1, 0.9], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (100, 'fc_adam_first_step', $${"function": "adam_update", "args": [[1.0], [1.0], [0.0], [0.0]], "kwargs": {"lr": 0.001, "beta1": 0.9, "beta2": 0.999, "t": 1}}$$, $${"result": [[0.99900000001], [0.1], [0.001]], "tolerance": 0.001}$$, false, 'function_call', 16),
  (100, 'fc_adam_zero_grad', $${"function": "adam_update", "args": [[5.0, 3.0], [0.0, 0.0], [0.5, 0.3], [0.1, 0.2]], "kwargs": {"lr": 0.001, "beta1": 0.9, "beta2": 0.999, "t": 10}}$$, $${"result": [[4.9997818990490845, 2.999907467603089], [0.45, 0.27], [0.0999, 0.1998]], "tolerance": 0.0001}$$, true, 'function_call', 17),
  (100, 'fc_adam_known_step_t10', $${"function": "adam_update", "args": [[1.0], [1.0], [0.0], [0.0]], "kwargs": {"lr": 0.001, "beta1": 0.9, "beta2": 0.999, "t": 10}}$$, $${"result": [[0.9995155736289468], [0.1], [0.001]], "tolerance": 0.0001}$$, true, 'function_call', 18),
  (100, 'fc_adam_dimensions_consistent', $${"function": "adam_update", "args": [[1, 2, 3], [0.1, 0.2, 0.3], [0, 0, 0], [0, 0, 0]], "kwargs": {"lr": 0.001, "beta1": 0.9, "beta2": 0.999, "t": 1}}$$, $${"result": [[0.9990000001, 1.99900000005, 2.9990000000333334], [0.01, 0.02, 0.03], [1e-05, 4e-05, 9e-05]], "tolerance": 0.0001}$$, true, 'function_call', 19),
  (100, 'fc_adam_raises_on_length_mismatch', $${"function": "adam_update", "args": [[1, 2], [0.1], [0, 0], [0, 0]], "kwargs": {"lr": 0.001, "beta1": 0.9, "beta2": 0.999, "t": 1}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 20),
  (100, 'fc_adam_raises_on_zero_t', $${"function": "adam_update", "args": [[1], [0.1], [0], [0]], "kwargs": {"lr": 0.001, "beta1": 0.9, "beta2": 0.999, "t": 0}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (100, 'fc_adam_raises_on_non_list', $${"function": "adam_update", "args": ["ab", [0.1], [0], [0]], "kwargs": {"lr": 0.001, "beta1": 0.9, "beta2": 0.999, "t": 1}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 22),
  (100, 'fc_lrd_step', $${"function": "apply_lr_decay", "args": [1.0, 3, 0.5, "step"], "kwargs": {}}$$, $${"result": 0.125, "tolerance": 1e-06}$$, false, 'function_call', 23),
  (100, 'fc_lrd_step_epoch_zero', $${"function": "apply_lr_decay", "args": [0.5, 0, 0.9, "step"], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 24),
  (100, 'fc_lrd_exp', $${"function": "apply_lr_decay", "args": [1.0, 5, 0.1, "exp"], "kwargs": {}}$$, $${"result": 0.6065306597126334, "tolerance": 1e-06}$$, true, 'function_call', 25),
  (100, 'fc_lrd_inverse', $${"function": "apply_lr_decay", "args": [1.0, 9, 0.1, "inverse"], "kwargs": {}}$$, $${"result": 0.5263157894736842, "tolerance": 1e-06}$$, true, 'function_call', 26),
  (100, 'fc_lrd_raises_on_negative_epoch', $${"function": "apply_lr_decay", "args": [1.0, -1, 0.5, "step"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 27),
  (100, 'fc_lrd_raises_on_invalid_type', $${"function": "apply_lr_decay", "args": [1.0, 5, 0.5, "unknown"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 28),
  (100, 'fc_lrd_raises_on_non_numeric', $${"function": "apply_lr_decay", "args": ["1.0", 5, 0.5, "step"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 29);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=100 GROUP BY task_id;

COMMIT;