-- NN11 (task_id=104) function_call task_tests — 29 条

BEGIN;

DELETE FROM task_tests WHERE task_id=104;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (104, 'fc_tsl_textbook', $${"function": "train_step_linear", "args": [[0.5], 1.0, [[10]], [8.0], 0.01], "kwargs": {}}$$, $${"result": [[0.9], 1.04, 4.0], "tolerance": 0.0001}$$, false, 'function_call', 1),
  (104, 'fc_tsl_loss_nonzero', $${"function": "train_step_linear", "args": [[1.0], 0.0, [[1]], [3.0], 0.5], "kwargs": {}}$$, $${"result": [[3.0], 2.0, 4.0], "tolerance": 0.0001}$$, true, 'function_call', 2),
  (104, 'fc_tsl_zero_lr', $${"function": "train_step_linear", "args": [[0.5], 0.0, [[10]], [8.0], 0.0], "kwargs": {}}$$, $${"result": [[0.5], 0.0, 9.0], "tolerance": 0.0001}$$, true, 'function_call', 3),
  (104, 'fc_tsl_two_features', $${"function": "train_step_linear", "args": [[1.0, 1.0], 0.0, [[1, 2]], [5.0], 0.1], "kwargs": {}}$$, $${"result": [[1.4, 1.8], 0.4, 4.0], "tolerance": 0.0001}$$, true, 'function_call', 4),
  (104, 'fc_tsl_batch_two_samples', $${"function": "train_step_linear", "args": [[1.0], 0.0, [[1], [2]], [2.0, 4.0], 0.1], "kwargs": {}}$$, $${"result": [[1.5], 0.3, 2.5], "tolerance": 0.0001}$$, true, 'function_call', 5),
  (104, 'fc_tsl_raises_on_dim_mismatch', $${"function": "train_step_linear", "args": [[1.0, 2.0], 0.0, [[1]], [2.0], 0.1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (104, 'fc_tsl_raises_on_empty', $${"function": "train_step_linear", "args": [[], 0.0, [], [], 0.1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (104, 'fc_tsl_raises_on_non_list', $${"function": "train_step_linear", "args": ["ab", 0.0, [[1]], [2.0], 0.1], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (104, 'fc_es_too_short', $${"function": "early_stopping_check", "args": [[0.5, 0.4]], "kwargs": {"patience": 5}}$$, $${"result": false}$$, false, 'function_call', 9),
  (104, 'fc_es_still_improving', $${"function": "early_stopping_check", "args": [[0.6, 0.5, 0.4, 0.3, 0.2, 0.1]], "kwargs": {"patience": 3}}$$, $${"result": false}$$, true, 'function_call', 10),
  (104, 'fc_es_stagnant', $${"function": "early_stopping_check", "args": [[0.5, 0.4, 0.3, 0.3, 0.3, 0.3]], "kwargs": {"patience": 3}}$$, $${"result": true}$$, true, 'function_call', 11),
  (104, 'fc_es_diverging', $${"function": "early_stopping_check", "args": [[0.5, 0.4, 0.3, 0.4, 0.5, 0.6]], "kwargs": {"patience": 3}}$$, $${"result": true}$$, true, 'function_call', 12),
  (104, 'fc_es_raises_on_empty', $${"function": "early_stopping_check", "args": [[]], "kwargs": {"patience": 3}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (104, 'fc_es_raises_on_zero_patience', $${"function": "early_stopping_check", "args": [[0.5, 0.4]], "kwargs": {"patience": 0}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (104, 'fc_es_raises_on_non_list', $${"function": "early_stopping_check", "args": ["ab"], "kwargs": {"patience": 3}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (104, 'fc_cvm_perfect', $${"function": "compute_validation_metrics", "args": [[1, 1, 0, 0], [1, 1, 0, 0]], "kwargs": {}}$$, $${"result": {"accuracy": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0, "specificity": 1.0}, "tolerance": 0.0001}$$, false, 'function_call', 16),
  (104, 'fc_cvm_all_wrong', $${"function": "compute_validation_metrics", "args": [[1, 1, 0, 0], [0, 0, 1, 1]], "kwargs": {}}$$, $${"result": {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0, "specificity": 0.0}, "tolerance": 0.0001}$$, true, 'function_call', 17),
  (104, 'fc_cvm_specific', $${"function": "compute_validation_metrics", "args": [[1, 1, 0, 0, 1], [1, 0, 0, 0, 1]], "kwargs": {}}$$, $${"result": {"accuracy": 0.8, "precision": 1.0, "recall": 0.6666666666666666, "f1": 0.8, "specificity": 1.0}, "tolerance": 0.0001}$$, true, 'function_call', 18),
  (104, 'fc_cvm_imbalanced', $${"function": "compute_validation_metrics", "args": [[0, 0, 0, 0, 1], [0, 0, 0, 0, 0]], "kwargs": {}}$$, $${"result": {"accuracy": 0.8, "precision": 0.0, "recall": 0.0, "f1": 0.0, "specificity": 1.0}, "tolerance": 0.0001}$$, true, 'function_call', 19),
  (104, 'fc_cvm_dict_keys', $${"function": "compute_validation_metrics", "args": [[1, 0], [1, 0]], "kwargs": {}}$$, $${"result": {"accuracy": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0, "specificity": 1.0}, "tolerance": 0.0001}$$, true, 'function_call', 20),
  (104, 'fc_cvm_raises_on_length_mismatch', $${"function": "compute_validation_metrics", "args": [[1, 0], [1]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (104, 'fc_cvm_raises_on_invalid_label', $${"function": "compute_validation_metrics", "args": [[1, 2], [1, 0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (104, 'fc_cvm_raises_on_non_list', $${"function": "compute_validation_metrics", "args": ["ab", "ab"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23),
  (104, 'fc_ftl_basic', $${"function": "format_training_log", "args": [0, 0.69, 0.68, {"accuracy": 0.55, "f1": 0.5}], "kwargs": {}}$$, $${"result": "Epoch 0 | train_loss=0.6900 | val_loss=0.6800 | acc=0.550 | f1=0.500"}$$, false, 'function_call', 24),
  (104, 'fc_ftl_format_precision', $${"function": "format_training_log", "args": [10, 0.123456, 0.234567, {"accuracy": 0.892345, "f1": 0.901234}], "kwargs": {}}$$, $${"result": "Epoch 10 | train_loss=0.1235 | val_loss=0.2346 | acc=0.892 | f1=0.901"}$$, true, 'function_call', 25),
  (104, 'fc_ftl_full_format_string', $${"function": "format_training_log", "args": [7, 0.3456, 0.4123, {"accuracy": 0.756, "f1": 0.701}], "kwargs": {}}$$, $${"result": "Epoch 7 | train_loss=0.3456 | val_loss=0.4123 | acc=0.756 | f1=0.701"}$$, true, 'function_call', 26),
  (104, 'fc_ftl_raises_on_negative_epoch', $${"function": "format_training_log", "args": [-1, 0.5, 0.5, {"accuracy": 0.5, "f1": 0.5}], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 27),
  (104, 'fc_ftl_raises_on_missing_metric', $${"function": "format_training_log", "args": [0, 0.5, 0.5, {"accuracy": 0.5}], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 28),
  (104, 'fc_ftl_raises_on_non_int_epoch', $${"function": "format_training_log", "args": ["0", 0.5, 0.5, {"accuracy": 0.5, "f1": 0.5}], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 29);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=104 GROUP BY task_id;

COMMIT;