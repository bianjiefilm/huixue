-- MJ05 (task_id=86) function_call task_tests — 32 条

BEGIN;

-- 删除现有错误的 io_based task_tests
DELETE FROM task_tests WHERE task_id=86;

-- 插入新 fc 协议 task_tests
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (86, 'fc_mv_simple_binary', $${"function": "majority_vote", "args": [[[1, 0, 0], [0, 1, 1], [1, 0, 0]]], "kwargs": {}}$$, $${"result": [0, 1, 0]}$$, false, 'function_call', 1),
  (86, 'fc_mv_tie_smaller', $${"function": "majority_vote", "args": [[[1, 0, 0, 1]]], "kwargs": {"tie_break": "smaller"}}$$, $${"result": [0]}$$, true, 'function_call', 2),
  (86, 'fc_mv_three_classes', $${"function": "majority_vote", "args": [[[0, 1, 2, 2, 2]]], "kwargs": {}}$$, $${"result": [2]}$$, true, 'function_call', 3),
  (86, 'fc_mv_first_disagrees', $${"function": "majority_vote", "args": [[[1, 0, 0, 0]]], "kwargs": {}}$$, $${"result": [0]}$$, true, 'function_call', 4),
  (86, 'fc_mv_first_is_minority', $${"function": "majority_vote", "args": [[[2, 1, 1, 1, 1]]], "kwargs": {}}$$, $${"result": [1]}$$, true, 'function_call', 5),
  (86, 'fc_mv_raises_on_empty_outer', $${"function": "majority_vote", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (86, 'fc_mv_raises_on_empty_inner', $${"function": "majority_vote", "args": [[[], []]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (86, 'fc_mv_raises_on_non_list', $${"function": "majority_vote", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (86, 'fc_fi_basic', $${"function": "compute_feature_importance", "args": [[10, 5, 5]], "kwargs": {}}$$, $${"result": [0.5, 0.25, 0.25], "tolerance": 1e-06}$$, false, 'function_call', 9),
  (86, 'fc_fi_uniform', $${"function": "compute_feature_importance", "args": [[1, 1, 1, 1]], "kwargs": {}}$$, $${"result": [0.25, 0.25, 0.25, 0.25], "tolerance": 1e-06}$$, true, 'function_call', 10),
  (86, 'fc_fi_all_one_feature', $${"function": "compute_feature_importance", "args": [[100, 0, 0]], "kwargs": {}}$$, $${"result": [1.0, 0.0, 0.0], "tolerance": 1e-06}$$, true, 'function_call', 11),
  (86, 'fc_fi_proportional', $${"function": "compute_feature_importance", "args": [[2, 4, 6, 8]], "kwargs": {}}$$, $${"result": [0.1, 0.2, 0.3, 0.4], "tolerance": 1e-06}$$, true, 'function_call', 12),
  (86, 'fc_fi_raises_on_all_zero', $${"function": "compute_feature_importance", "args": [[0, 0, 0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (86, 'fc_fi_raises_on_empty', $${"function": "compute_feature_importance", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (86, 'fc_fi_raises_on_negative', $${"function": "compute_feature_importance", "args": [[1, -1, 2]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (86, 'fc_fi_raises_on_non_list', $${"function": "compute_feature_importance", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (86, 'fc_gini_pure', $${"function": "gini_impurity", "args": [[0, 0, 0, 0]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, false, 'function_call', 17),
  (86, 'fc_gini_balanced_binary', $${"function": "gini_impurity", "args": [[0, 0, 1, 1]], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 18),
  (86, 'fc_gini_three_one', $${"function": "gini_impurity", "args": [[0, 0, 0, 1]], "kwargs": {}}$$, $${"result": 0.375, "tolerance": 1e-06}$$, true, 'function_call', 19),
  (86, 'fc_gini_three_classes_equal', $${"function": "gini_impurity", "args": [[0, 1, 2]], "kwargs": {}}$$, $${"result": 0.6666666666666666, "tolerance": 1e-06}$$, true, 'function_call', 20),
  (86, 'fc_gini_four_classes_equal', $${"function": "gini_impurity", "args": [[0, 1, 2, 3]], "kwargs": {}}$$, $${"result": 0.75, "tolerance": 1e-06}$$, true, 'function_call', 21),
  (86, 'fc_gini_unbalanced', $${"function": "gini_impurity", "args": [[0, 0, 0, 1, 1]], "kwargs": {}}$$, $${"result": 0.48, "tolerance": 1e-06}$$, true, 'function_call', 22),
  (86, 'fc_gini_raises_on_empty', $${"function": "gini_impurity", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (86, 'fc_gini_raises_on_non_list', $${"function": "gini_impurity", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24),
  (86, 'fc_residual_perfect_fit', $${"function": "compute_boosting_residual", "args": [[1, 2, 3], [1, 2, 3]], "kwargs": {}}$$, $${"result": [0.0, 0.0, 0.0], "tolerance": 1e-06}$$, false, 'function_call', 25),
  (86, 'fc_residual_constant_diff', $${"function": "compute_boosting_residual", "args": [[10, 20, 30], [5, 15, 25]], "kwargs": {}}$$, $${"result": [5.0, 5.0, 5.0], "tolerance": 1e-06}$$, true, 'function_call', 26),
  (86, 'fc_residual_signed', $${"function": "compute_boosting_residual", "args": [[1, 2, 3], [3, 2, 1]], "kwargs": {}}$$, $${"result": [-2.0, 0.0, 2.0], "tolerance": 1e-06}$$, true, 'function_call', 27),
  (86, 'fc_residual_floats', $${"function": "compute_boosting_residual", "args": [[1.5, 2.5], [1.0, 2.0]], "kwargs": {}}$$, $${"result": [0.5, 0.5], "tolerance": 1e-06}$$, true, 'function_call', 28),
  (86, 'fc_residual_y_pred_zeros', $${"function": "compute_boosting_residual", "args": [[5, 7, 11], [0, 0, 0]], "kwargs": {}}$$, $${"result": [5.0, 7.0, 11.0], "tolerance": 1e-06}$$, true, 'function_call', 29),
  (86, 'fc_residual_raises_on_length_mismatch', $${"function": "compute_boosting_residual", "args": [[1, 2, 3], [1, 2]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (86, 'fc_residual_raises_on_empty', $${"function": "compute_boosting_residual", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (86, 'fc_residual_raises_on_non_list', $${"function": "compute_boosting_residual", "args": ["abc", "def"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 32);

-- 验证
SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=86 GROUP BY task_id;

COMMIT;