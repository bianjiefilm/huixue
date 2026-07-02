-- MJ11 (task_id=92) function_call task_tests — 32 条

BEGIN;

DELETE FROM task_tests WHERE task_id=92;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (92, 'fc_bp_user_example', $${"function": "bagging_predict", "args": [[[0, 1, 1], [1, 1, 0], [1, 1, 1]]], "kwargs": {}}$$, $${"result": [1, 1, 1]}$$, false, 'function_call', 1),
  (92, 'fc_bp_first_estimator_minority', $${"function": "bagging_predict", "args": [[[1, 1], [0, 0], [0, 0]]], "kwargs": {}}$$, $${"result": [0, 0]}$$, true, 'function_call', 2),
  (92, 'fc_bp_unanimous_mixed', $${"function": "bagging_predict", "args": [[[0], [1], [1]]], "kwargs": {}}$$, $${"result": [1]}$$, true, 'function_call', 3),
  (92, 'fc_bp_tie_smaller', $${"function": "bagging_predict", "args": [[[0, 1], [1, 0]]], "kwargs": {}}$$, $${"result": [0, 0]}$$, true, 'function_call', 4),
  (92, 'fc_bp_three_estimators_three_samples', $${"function": "bagging_predict", "args": [[[1, 0, 0], [0, 1, 1], [1, 1, 0]]], "kwargs": {}}$$, $${"result": [1, 1, 0]}$$, true, 'function_call', 5),
  (92, 'fc_bp_raises_on_empty', $${"function": "bagging_predict", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (92, 'fc_bp_raises_on_inconsistent_rows', $${"function": "bagging_predict", "args": [[[0, 1], [1]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (92, 'fc_bp_raises_on_non_list', $${"function": "bagging_predict", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (92, 'fc_wv_user_example', $${"function": "weighted_vote", "args": [[[0, 1, 1], [1, 1, 0]], [0.3, 0.7]], "kwargs": {}}$$, $${"result": [1, 1, 0]}$$, false, 'function_call', 9),
  (92, 'fc_wv_dominant_first', $${"function": "weighted_vote", "args": [[[1, 0], [0, 1]], [1.0, 0.0]], "kwargs": {}}$$, $${"result": [1, 0]}$$, true, 'function_call', 10),
  (92, 'fc_wv_dominant_second', $${"function": "weighted_vote", "args": [[[1, 0], [0, 1]], [0.0, 1.0]], "kwargs": {}}$$, $${"result": [0, 1]}$$, true, 'function_call', 11),
  (92, 'fc_wv_balanced_50_50', $${"function": "weighted_vote", "args": [[[0, 1], [1, 0]], [0.5, 0.5]], "kwargs": {}}$$, $${"result": [1, 1]}$$, true, 'function_call', 12),
  (92, 'fc_wv_three_estimators', $${"function": "weighted_vote", "args": [[[1, 0, 0], [1, 1, 0], [0, 1, 1]], [0.5, 0.3, 0.2]], "kwargs": {}}$$, $${"result": [1, 1, 0]}$$, true, 'function_call', 13),
  (92, 'fc_wv_raises_on_empty', $${"function": "weighted_vote", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (92, 'fc_wv_raises_on_dim_mismatch', $${"function": "weighted_vote", "args": [[[1, 0]], [0.5, 0.5]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (92, 'fc_wv_raises_on_non_list', $${"function": "weighted_vote", "args": ["abc", [0.5, 0.5]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (92, 'fc_sp_basic', $${"function": "stacking_predict", "args": [[[0.8, 0.2], [0.3, 0.7]], [0.6, 0.4]], "kwargs": {}}$$, $${"result": [0.56, 0.46], "tolerance": 1e-06}$$, false, 'function_call', 17),
  (92, 'fc_sp_single_estimator', $${"function": "stacking_predict", "args": [[[0.7], [0.3], [0.5]], [1.0]], "kwargs": {}}$$, $${"result": [0.7, 0.3, 0.5], "tolerance": 1e-06}$$, true, 'function_call', 18),
  (92, 'fc_sp_zero_weights', $${"function": "stacking_predict", "args": [[[0.5, 0.5], [0.9, 0.1]], [0.0, 0.0]], "kwargs": {}}$$, $${"result": [0.0, 0.0], "tolerance": 1e-06}$$, true, 'function_call', 19),
  (92, 'fc_sp_three_estimators', $${"function": "stacking_predict", "args": [[[0.5, 0.6, 0.7], [0.2, 0.3, 0.4]], [0.2, 0.3, 0.5]], "kwargs": {}}$$, $${"result": [0.63, 0.33], "tolerance": 1e-06}$$, true, 'function_call', 20),
  (92, 'fc_sp_negative_weights', $${"function": "stacking_predict", "args": [[[0.8, 0.2]], [1.0, -0.5]], "kwargs": {}}$$, $${"result": [0.7], "tolerance": 1e-06}$$, true, 'function_call', 21),
  (92, 'fc_sp_raises_on_empty', $${"function": "stacking_predict", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (92, 'fc_sp_raises_on_dim_mismatch', $${"function": "stacking_predict", "args": [[[0.5, 0.5]], [0.3]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (92, 'fc_sp_raises_on_non_list', $${"function": "stacking_predict", "args": ["abc", [0.5, 0.5]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24),
  (92, 'fc_bc_lr_one', $${"function": "boosting_combine", "args": [[[0.5, 0.7], [0.3, 0.4]], 1.0], "kwargs": {}}$$, $${"result": [0.8, 1.1], "tolerance": 1e-06}$$, false, 'function_call', 25),
  (92, 'fc_bc_lr_half', $${"function": "boosting_combine", "args": [[[0.5, 0.7], [0.3, 0.4]], 0.5], "kwargs": {}}$$, $${"result": [0.4, 0.55], "tolerance": 1e-06}$$, true, 'function_call', 26),
  (92, 'fc_bc_three_stages', $${"function": "boosting_combine", "args": [[[0.1], [0.2], [0.3]], 0.5], "kwargs": {}}$$, $${"result": [0.3], "tolerance": 1e-06}$$, true, 'function_call', 27),
  (92, 'fc_bc_single_stage', $${"function": "boosting_combine", "args": [[[1.0, 2.0]], 1.0], "kwargs": {}}$$, $${"result": [1.0, 2.0], "tolerance": 1e-06}$$, true, 'function_call', 28),
  (92, 'fc_bc_lr_zero', $${"function": "boosting_combine", "args": [[[1.0, 2.0], [3.0, 4.0]], 0.0], "kwargs": {}}$$, $${"result": [0.0, 0.0], "tolerance": 1e-06}$$, true, 'function_call', 29),
  (92, 'fc_bc_raises_on_empty', $${"function": "boosting_combine", "args": [[], 0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (92, 'fc_bc_raises_on_inconsistent_rows', $${"function": "boosting_combine", "args": [[[1.0, 2.0], [3.0]], 0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (92, 'fc_bc_raises_on_non_list', $${"function": "boosting_combine", "args": ["abc", 0.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 32);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=92 GROUP BY task_id;

COMMIT;