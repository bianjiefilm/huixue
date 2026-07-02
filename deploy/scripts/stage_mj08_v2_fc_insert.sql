-- MJ08 (task_id=89) function_call task_tests — 32 条

BEGIN;

-- 删除现有错误的 io_based task_tests
DELETE FROM task_tests WHERE task_id=89;

-- 插入新 fc 协议 task_tests
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (89, 'fc_cd_3x2_known_mean', $${"function": "center_data", "args": [[[1, 2], [3, 4], [5, 6]]], "kwargs": {}}$$, $${"result": [[[-2.0, -2.0], [0.0, 0.0], [2.0, 2.0]], [3.0, 4.0]], "tolerance": 1e-06}$$, false, 'function_call', 1),
  (89, 'fc_cd_1d_4_samples', $${"function": "center_data", "args": [[[1], [2], [3], [4]]], "kwargs": {}}$$, $${"result": [[[-1.5], [-0.5], [0.5], [1.5]], [2.5]], "tolerance": 1e-06}$$, true, 'function_call', 2),
  (89, 'fc_cd_3d', $${"function": "center_data", "args": [[[1, 2, 3], [4, 5, 6]]], "kwargs": {}}$$, $${"result": [[[-1.5, -1.5, -1.5], [1.5, 1.5, 1.5]], [2.5, 3.5, 4.5]], "tolerance": 1e-06}$$, true, 'function_call', 3),
  (89, 'fc_cd_constant_data', $${"function": "center_data", "args": [[[5, 5], [5, 5]]], "kwargs": {}}$$, $${"result": [[[0.0, 0.0], [0.0, 0.0]], [5.0, 5.0]], "tolerance": 1e-06}$$, true, 'function_call', 4),
  (89, 'fc_cd_single_sample', $${"function": "center_data", "args": [[[10, 20]]], "kwargs": {}}$$, $${"result": [[[0.0, 0.0]], [10.0, 20.0]], "tolerance": 1e-06}$$, true, 'function_call', 5),
  (89, 'fc_cd_raises_on_empty', $${"function": "center_data", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (89, 'fc_cd_raises_on_inconsistent_rows', $${"function": "center_data", "args": [[[1, 2], [3]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (89, 'fc_cd_raises_on_non_list', $${"function": "center_data", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (89, 'fc_cov_y_2x', $${"function": "compute_covariance", "args": [[[-2, -4], [-1, -2], [0, 0], [1, 2], [2, 4]]], "kwargs": {}}$$, $${"result": [[2.0, 4.0], [4.0, 8.0]], "tolerance": 1e-06}$$, false, 'function_call', 9),
  (89, 'fc_cov_diagonal', $${"function": "compute_covariance", "args": [[[1, 0], [-1, 0]]], "kwargs": {}}$$, $${"result": [[1.0, 0.0], [0.0, 0.0]], "tolerance": 1e-06}$$, true, 'function_call', 10),
  (89, 'fc_cov_3d', $${"function": "compute_covariance", "args": [[[1, 1, 1], [-1, -1, -1]]], "kwargs": {}}$$, $${"result": [[1.0, 1.0, 1.0], [1.0, 1.0, 1.0], [1.0, 1.0, 1.0]], "tolerance": 1e-06}$$, true, 'function_call', 11),
  (89, 'fc_cov_identity_data', $${"function": "compute_covariance", "args": [[[1, 0], [0, 1], [-1, 0], [0, -1]]], "kwargs": {}}$$, $${"result": [[0.5, 0.0], [0.0, 0.5]], "tolerance": 1e-06}$$, true, 'function_call', 12),
  (89, 'fc_cov_anti_correlated', $${"function": "compute_covariance", "args": [[[1, -1], [-1, 1]]], "kwargs": {}}$$, $${"result": [[1.0, -1.0], [-1.0, 1.0]], "tolerance": 1e-06}$$, true, 'function_call', 13),
  (89, 'fc_cov_raises_on_empty', $${"function": "compute_covariance", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (89, 'fc_cov_raises_on_inconsistent_rows', $${"function": "compute_covariance", "args": [[[1, 2], [3]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (89, 'fc_cov_raises_on_non_list', $${"function": "compute_covariance", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (89, 'fc_pt_project_to_first_axis', $${"function": "pca_transform", "args": [[[1, 2], [3, 4]], [[1, 0]]], "kwargs": {}}$$, $${"result": [[1.0], [3.0]], "tolerance": 1e-06}$$, false, 'function_call', 17),
  (89, 'fc_pt_project_to_y_axis', $${"function": "pca_transform", "args": [[[1, 2], [3, 4]], [[0, 1]]], "kwargs": {}}$$, $${"result": [[2.0], [4.0]], "tolerance": 1e-06}$$, true, 'function_call', 18),
  (89, 'fc_pt_project_diagonal', $${"function": "pca_transform", "args": [[[1, 2]], [[0.7071067811865475, 0.7071067811865475]]], "kwargs": {}}$$, $${"result": [[2.1213203435596424]], "tolerance": 1e-06}$$, true, 'function_call', 19),
  (89, 'fc_pt_two_components_3d', $${"function": "pca_transform", "args": [[[1, 2, 3]], [[1, 0, 0], [0, 1, 0]]], "kwargs": {}}$$, $${"result": [[1.0, 2.0]], "tolerance": 1e-06}$$, true, 'function_call', 20),
  (89, 'fc_pt_zero_input', $${"function": "pca_transform", "args": [[[0, 0]], [[1, 0]]], "kwargs": {}}$$, $${"result": [[0.0]], "tolerance": 1e-06}$$, true, 'function_call', 21),
  (89, 'fc_pt_raises_on_empty_X', $${"function": "pca_transform", "args": [[], [[1, 0]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (89, 'fc_pt_raises_on_dim_mismatch', $${"function": "pca_transform", "args": [[[1, 2]], [[1, 0, 0]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (89, 'fc_pt_raises_on_non_list', $${"function": "pca_transform", "args": ["abc", [[1, 0]]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24),
  (89, 'fc_evr_y_2x_perfect', $${"function": "explained_variance_ratio", "args": [[10, 0]], "kwargs": {}}$$, $${"result": [1.0, 0.0], "tolerance": 1e-06}$$, false, 'function_call', 25),
  (89, 'fc_evr_uniform', $${"function": "explained_variance_ratio", "args": [[1, 1, 1, 1]], "kwargs": {}}$$, $${"result": [0.25, 0.25, 0.25, 0.25], "tolerance": 1e-06}$$, true, 'function_call', 26),
  (89, 'fc_evr_proportional', $${"function": "explained_variance_ratio", "args": [[2, 4, 6, 8]], "kwargs": {}}$$, $${"result": [0.1, 0.2, 0.3, 0.4], "tolerance": 1e-06}$$, true, 'function_call', 27),
  (89, 'fc_evr_typical_pca', $${"function": "explained_variance_ratio", "args": [[50, 30, 15, 5]], "kwargs": {}}$$, $${"result": [0.5, 0.3, 0.15, 0.05], "tolerance": 1e-06}$$, true, 'function_call', 28),
  (89, 'fc_evr_decimals', $${"function": "explained_variance_ratio", "args": [[0.5, 0.5]], "kwargs": {}}$$, $${"result": [0.5, 0.5], "tolerance": 1e-06}$$, true, 'function_call', 29),
  (89, 'fc_evr_raises_on_all_zero', $${"function": "explained_variance_ratio", "args": [[0, 0, 0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (89, 'fc_evr_raises_on_negative', $${"function": "explained_variance_ratio", "args": [[1, -1, 2]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (89, 'fc_evr_raises_on_non_list', $${"function": "explained_variance_ratio", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 32);

-- 验证
SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=89 GROUP BY task_id;

COMMIT;