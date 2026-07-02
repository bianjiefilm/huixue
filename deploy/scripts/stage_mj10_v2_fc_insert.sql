-- MJ10 (task_id=91) function_call task_tests — 20 条

BEGIN;

DELETE FROM task_tests WHERE task_id=91;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (91, 'fc_kf_raises_on_too_many_splits', $${"function": "stratified_kfold_split", "args": [[0, 0, 1], 5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 1),
  (91, 'fc_kf_raises_on_empty', $${"function": "stratified_kfold_split", "args": [[], 2], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 2),
  (91, 'fc_kf_raises_on_non_list', $${"function": "stratified_kfold_split", "args": ["abc", 2], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 3),
  (91, 'fc_bs_raises_on_empty', $${"function": "bootstrap_sample", "args": [[], 5], "kwargs": {"random_state": 42}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 4),
  (91, 'fc_bs_raises_on_negative_n', $${"function": "bootstrap_sample", "args": [[1, 2], -1], "kwargs": {"random_state": 42}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 5),
  (91, 'fc_bs_raises_on_non_list', $${"function": "bootstrap_sample", "args": ["abc", 5], "kwargs": {"random_state": 42}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (91, 'fc_acvs_three_scores', $${"function": "aggregate_cv_scores", "args": [[0.8, 0.85, 0.9]], "kwargs": {}}$$, $${"result": {"mean": 0.85, "min": 0.8, "max": 0.9, "std": 0.040824829046386304}, "tolerance": 0.0001}$$, false, 'function_call', 7),
  (91, 'fc_acvs_perfect', $${"function": "aggregate_cv_scores", "args": [[1.0, 1.0, 1.0, 1.0, 1.0]], "kwargs": {}}$$, $${"result": {"mean": 1.0, "min": 1.0, "max": 1.0, "std": 0.0}, "tolerance": 1e-06}$$, true, 'function_call', 8),
  (91, 'fc_acvs_diverse', $${"function": "aggregate_cv_scores", "args": [[0.5, 0.7, 0.6, 0.8]], "kwargs": {}}$$, $${"result": {"mean": 0.65, "min": 0.5, "max": 0.8, "std": 0.11180339887498948}, "tolerance": 0.0001}$$, true, 'function_call', 9),
  (91, 'fc_acvs_negative', $${"function": "aggregate_cv_scores", "args": [[-0.1, 0.5]], "kwargs": {}}$$, $${"result": {"mean": 0.2, "min": -0.1, "max": 0.5, "std": 0.3}, "tolerance": 0.0001}$$, true, 'function_call', 10),
  (91, 'fc_acvs_single', $${"function": "aggregate_cv_scores", "args": [[0.7]], "kwargs": {}}$$, $${"result": {"mean": 0.7, "min": 0.7, "max": 0.7, "std": 0.0}, "tolerance": 1e-06}$$, true, 'function_call', 11),
  (91, 'fc_acvs_raises_on_empty', $${"function": "aggregate_cv_scores", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 12),
  (91, 'fc_acvs_raises_on_non_list', $${"function": "aggregate_cv_scores", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 13),
  (91, 'fc_lcm_basic', $${"function": "compute_learning_curve_means", "args": [[[0.9, 0.95], [0.85, 0.9]], [[0.8, 0.82], [0.78, 0.82]]], "kwargs": {}}$$, $${"result": {"train_mean": [0.925, 0.875], "train_std": [0.025, 0.025], "val_mean": [0.81, 0.8], "val_std": [0.01, 0.02]}, "tolerance": 0.0001}$$, false, 'function_call', 14),
  (91, 'fc_lcm_constant', $${"function": "compute_learning_curve_means", "args": [[[0.9, 0.9, 0.9], [0.85, 0.85, 0.85]], [[0.8, 0.8, 0.8], [0.75, 0.75, 0.75]]], "kwargs": {}}$$, $${"result": {"train_mean": [0.9, 0.85], "train_std": [0.0, 0.0], "val_mean": [0.8, 0.75], "val_std": [0.0, 0.0]}, "tolerance": 1e-06}$$, true, 'function_call', 15),
  (91, 'fc_lcm_three_sizes', $${"function": "compute_learning_curve_means", "args": [[[0.5, 0.6], [0.7, 0.8], [0.9, 1.0]], [[0.4, 0.5], [0.6, 0.7], [0.8, 0.9]]], "kwargs": {}}$$, $${"result": {"train_mean": [0.55, 0.75, 0.95], "train_std": [0.05, 0.05, 0.05], "val_mean": [0.45, 0.65, 0.85], "val_std": [0.05, 0.05, 0.05]}, "tolerance": 0.0001}$$, true, 'function_call', 16),
  (91, 'fc_lcm_single_size', $${"function": "compute_learning_curve_means", "args": [[[0.95]], [[0.88]]], "kwargs": {}}$$, $${"result": {"train_mean": [0.95], "train_std": [0.0], "val_mean": [0.88], "val_std": [0.0]}, "tolerance": 1e-06}$$, true, 'function_call', 17),
  (91, 'fc_lcm_raises_on_empty', $${"function": "compute_learning_curve_means", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (91, 'fc_lcm_raises_on_shape_mismatch', $${"function": "compute_learning_curve_means", "args": [[[0.9, 0.95]], [[0.8]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 19),
  (91, 'fc_lcm_raises_on_non_list', $${"function": "compute_learning_curve_means", "args": ["abc", "def"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 20);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=91 GROUP BY task_id;

COMMIT;