-- NN08 (task_id=101) function_call task_tests — 28 条

BEGIN;

DELETE FROM task_tests WHERE task_id=101;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (101, 'fc_l1_basic', $${"function": "l1_regularization", "args": [[1, -2, 3], 0.1], "kwargs": {}}$$, $${"result": 0.6, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (101, 'fc_l1_zero_weights', $${"function": "l1_regularization", "args": [[0, 0, 0], 0.5], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (101, 'fc_l1_zero_alpha', $${"function": "l1_regularization", "args": [[1, 2, 3], 0.0], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (101, 'fc_l1_negative_weights', $${"function": "l1_regularization", "args": [[-1, -2, -3], 1.0], "kwargs": {}}$$, $${"result": 6.0, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (101, 'fc_l1_decimals', $${"function": "l1_regularization", "args": [[0.5, -0.5, 0.25], 2.0], "kwargs": {}}$$, $${"result": 2.5, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (101, 'fc_l1_raises_on_empty', $${"function": "l1_regularization", "args": [[], 0.1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (101, 'fc_l1_raises_on_negative_alpha', $${"function": "l1_regularization", "args": [[1, 2], -0.1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (101, 'fc_l1_raises_on_non_list', $${"function": "l1_regularization", "args": ["ab", 0.1], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (101, 'fc_l2_basic', $${"function": "l2_regularization", "args": [[1, -2, 3], 0.1], "kwargs": {}}$$, $${"result": 1.4, "tolerance": 1e-06}$$, false, 'function_call', 9),
  (101, 'fc_l2_zero_weights', $${"function": "l2_regularization", "args": [[0, 0, 0], 0.5], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 10),
  (101, 'fc_l2_zero_alpha', $${"function": "l2_regularization", "args": [[1, 2, 3], 0.0], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 11),
  (101, 'fc_l2_known_simple', $${"function": "l2_regularization", "args": [[2, 2], 0.5], "kwargs": {}}$$, $${"result": 4.0, "tolerance": 1e-06}$$, true, 'function_call', 12),
  (101, 'fc_l2_decimals', $${"function": "l2_regularization", "args": [[0.1, 0.2], 10.0], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 13),
  (101, 'fc_l2_raises_on_empty', $${"function": "l2_regularization", "args": [[], 0.1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (101, 'fc_l2_raises_on_negative_alpha', $${"function": "l2_regularization", "args": [[1], -0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (101, 'fc_l2_raises_on_non_list', $${"function": "l2_regularization", "args": ["a", 0.1], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (101, 'fc_dropout_zero_rate_identity', $${"function": "apply_dropout", "args": [[1.0, 2.0, 3.0, 4.0], 0.0], "kwargs": {"seed": 42}}$$, $${"result": [1.0, 2.0, 3.0, 4.0], "tolerance": 1e-06}$$, false, 'function_call', 17),
  (101, 'fc_dropout_raises_on_invalid_rate', $${"function": "apply_dropout", "args": [[1, 2], 1.0], "kwargs": {"seed": 0}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (101, 'fc_dropout_raises_on_empty', $${"function": "apply_dropout", "args": [[], 0.5], "kwargs": {"seed": 0}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 19),
  (101, 'fc_dropout_raises_on_non_list', $${"function": "apply_dropout", "args": ["ab", 0.5], "kwargs": {"seed": 0}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 20),
  (101, 'fc_cos_healthy', $${"function": "check_overfit_signal", "args": [[0.8, 0.6, 0.4, 0.3, 0.25, 0.22, 0.2, 0.18, 0.17, 0.16], [0.85, 0.65, 0.45, 0.35, 0.3, 0.27, 0.25, 0.23, 0.22, 0.21]], "kwargs": {"patience": 3}}$$, $${"result": {"has_overfit": false, "best_val_epoch": 9, "gap": -0.04999999999999999, "is_diverging": false}, "tolerance": 1e-06}$$, false, 'function_call', 21),
  (101, 'fc_cos_overfit', $${"function": "check_overfit_signal", "args": [[0.8, 0.6, 0.4, 0.3, 0.2, 0.15, 0.1, 0.08, 0.06, 0.05], [0.85, 0.65, 0.45, 0.4, 0.38, 0.42, 0.45, 0.48, 0.5, 0.52]], "kwargs": {"patience": 3}}$$, $${"result": {"has_overfit": true, "best_val_epoch": 4, "gap": -0.47000000000000003, "is_diverging": true}, "tolerance": 1e-06}$$, true, 'function_call', 22),
  (101, 'fc_cos_gap_signed', $${"function": "check_overfit_signal", "args": [[0.5, 0.3], [0.5, 0.4]], "kwargs": {"patience": 2}}$$, $${"result": {"has_overfit": false, "best_val_epoch": 1, "gap": -0.10000000000000003, "is_diverging": false}, "tolerance": 1e-06}$$, true, 'function_call', 23),
  (101, 'fc_cos_best_val_first', $${"function": "check_overfit_signal", "args": [[0.5, 0.4, 0.3], [0.3, 0.4, 0.5]], "kwargs": {"patience": 2}}$$, $${"result": {"has_overfit": true, "best_val_epoch": 0, "gap": -0.2, "is_diverging": true}, "tolerance": 1e-06}$$, true, 'function_call', 24),
  (101, 'fc_cos_diverging_false_small_uptick', $${"function": "check_overfit_signal", "args": [[0.4, 0.3, 0.2], [0.35, 0.3, 0.31]], "kwargs": {"patience": 2}}$$, $${"result": {"has_overfit": false, "best_val_epoch": 1, "gap": -0.10999999999999999, "is_diverging": false}, "tolerance": 1e-06}$$, true, 'function_call', 25),
  (101, 'fc_cos_raises_on_length_mismatch', $${"function": "check_overfit_signal", "args": [[0.5, 0.3], [0.5]], "kwargs": {"patience": 2}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 26),
  (101, 'fc_cos_raises_on_empty', $${"function": "check_overfit_signal", "args": [[], []], "kwargs": {"patience": 2}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 27),
  (101, 'fc_cos_raises_on_non_list', $${"function": "check_overfit_signal", "args": ["ab", [0.5, 0.4]], "kwargs": {"patience": 2}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 28);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=101 GROUP BY task_id;

COMMIT;