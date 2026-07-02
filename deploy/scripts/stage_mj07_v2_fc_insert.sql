-- MJ07 (task_id=88) function_call task_tests — 33 条

BEGIN;

-- 删除现有错误的 io_based task_tests
DELETE FROM task_tests WHERE task_id=88;

-- 插入新 fc 协议 task_tests
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (88, 'fc_ed_three_four_five', $${"function": "euclidean_distance", "args": [[0, 0], [3, 4]], "kwargs": {}}$$, $${"result": 5.0, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (88, 'fc_ed_one_d', $${"function": "euclidean_distance", "args": [[0], [7]], "kwargs": {}}$$, $${"result": 7.0, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (88, 'fc_ed_zero', $${"function": "euclidean_distance", "args": [[1, 1, 1], [1, 1, 1]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (88, 'fc_ed_three_d', $${"function": "euclidean_distance", "args": [[1, 2, 3], [4, 6, 8]], "kwargs": {}}$$, $${"result": 7.0710678118654755, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (88, 'fc_ed_negative', $${"function": "euclidean_distance", "args": [[-1, -1], [1, 1]], "kwargs": {}}$$, $${"result": 2.8284271247461903, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (88, 'fc_ed_raises_on_empty', $${"function": "euclidean_distance", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (88, 'fc_ed_raises_on_length_mismatch', $${"function": "euclidean_distance", "args": [[1, 2], [1, 2, 3]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (88, 'fc_ed_raises_on_non_list', $${"function": "euclidean_distance", "args": ["ab", "cd"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (88, 'fc_ac_two_clear_clusters', $${"function": "assign_clusters", "args": [[[0, 0], [1, 1], [10, 10], [11, 11]], [[0, 0], [10, 10]]], "kwargs": {}}$$, $${"result": [0, 0, 1, 1]}$$, false, 'function_call', 9),
  (88, 'fc_ac_three_clusters_permuted', $${"function": "assign_clusters", "args": [[[50, 0], [0, 0], [0, 50]], [[0, 0], [50, 0], [0, 50]]], "kwargs": {}}$$, $${"result": [1, 0, 2]}$$, true, 'function_call', 10),
  (88, 'fc_ac_mixed_assignment_a', $${"function": "assign_clusters", "args": [[[3, 3], [4, 4]], [[0, 0], [10, 10]]], "kwargs": {}}$$, $${"result": [0, 0]}$$, true, 'function_call', 11),
  (88, 'fc_ac_mixed_assignment_b', $${"function": "assign_clusters", "args": [[[6, 6], [7, 7]], [[0, 0], [10, 10]]], "kwargs": {}}$$, $${"result": [1, 1]}$$, true, 'function_call', 12),
  (88, 'fc_ac_tie_smaller_index', $${"function": "assign_clusters", "args": [[[5, 5], [5, 5]], [[0, 0], [10, 10]]], "kwargs": {}}$$, $${"result": [0, 0]}$$, true, 'function_call', 13),
  (88, 'fc_ac_single_centroid', $${"function": "assign_clusters", "args": [[[1, 2], [3, 4], [5, 6]], [[0, 0]]], "kwargs": {}}$$, $${"result": [0, 0, 0]}$$, true, 'function_call', 14),
  (88, 'fc_ac_raises_on_empty_X', $${"function": "assign_clusters", "args": [[], [[0, 0]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (88, 'fc_ac_raises_on_empty_centroids', $${"function": "assign_clusters", "args": [[[1, 2]], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 16),
  (88, 'fc_ac_raises_on_non_list', $${"function": "assign_clusters", "args": ["abc", [[0, 0]]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 17),
  (88, 'fc_uc_two_clusters', $${"function": "update_centroids", "args": [[[0, 0], [2, 0], [10, 10], [12, 10]], [0, 0, 1, 1], 2], "kwargs": {}}$$, $${"result": [[1.0, 0.0], [11.0, 10.0]], "tolerance": 1e-06}$$, false, 'function_call', 18),
  (88, 'fc_uc_three_clusters', $${"function": "update_centroids", "args": [[[1], [2], [5], [6], [100]], [0, 0, 1, 1, 2], 3], "kwargs": {}}$$, $${"result": [[1.5], [5.5], [100.0]], "tolerance": 1e-06}$$, true, 'function_call', 19),
  (88, 'fc_uc_single_cluster', $${"function": "update_centroids", "args": [[[1, 1], [3, 3], [5, 5]], [0, 0, 0], 1], "kwargs": {}}$$, $${"result": [[3.0, 3.0]], "tolerance": 1e-06}$$, true, 'function_call', 20),
  (88, 'fc_uc_empty_cluster_zeros', $${"function": "update_centroids", "args": [[[2, 2], [4, 4]], [0, 0], 2], "kwargs": {}}$$, $${"result": [[3.0, 3.0], [0.0, 0.0]], "tolerance": 1e-06}$$, true, 'function_call', 21),
  (88, 'fc_uc_negative_values', $${"function": "update_centroids", "args": [[[-1, -2], [1, 2]], [0, 0], 1], "kwargs": {}}$$, $${"result": [[0.0, 0.0]], "tolerance": 1e-06}$$, true, 'function_call', 22),
  (88, 'fc_uc_raises_on_empty_X', $${"function": "update_centroids", "args": [[], [], 2], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (88, 'fc_uc_raises_on_length_mismatch', $${"function": "update_centroids", "args": [[[1, 2], [3, 4]], [0], 2], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 24),
  (88, 'fc_uc_raises_on_non_list', $${"function": "update_centroids", "args": ["abc", [0, 1, 2], 2], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 25),
  (88, 'fc_ci_well_clustered', $${"function": "compute_inertia", "args": [[[0, 0], [2, 0], [10, 10], [12, 10]], [0, 0, 1, 1], [[1, 0], [11, 10]]], "kwargs": {}}$$, $${"result": 4.0, "tolerance": 1e-06}$$, false, 'function_call', 26),
  (88, 'fc_ci_perfect_centers', $${"function": "compute_inertia", "args": [[[5, 5], [10, 10]], [0, 1], [[5, 5], [10, 10]]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 27),
  (88, 'fc_ci_single_cluster', $${"function": "compute_inertia", "args": [[[0, 0], [3, 4]], [0, 0], [[0, 0]]], "kwargs": {}}$$, $${"result": 25.0, "tolerance": 1e-06}$$, true, 'function_call', 28),
  (88, 'fc_ci_three_clusters', $${"function": "compute_inertia", "args": [[[0], [1], [10], [11], [20]], [0, 0, 1, 1, 2], [[0.5], [10.5], [20]]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, true, 'function_call', 29),
  (88, 'fc_ci_far_centers', $${"function": "compute_inertia", "args": [[[0, 0]], [0], [[3, 4]]], "kwargs": {}}$$, $${"result": 25.0, "tolerance": 1e-06}$$, true, 'function_call', 30),
  (88, 'fc_ci_raises_on_empty', $${"function": "compute_inertia", "args": [[], [], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (88, 'fc_ci_raises_on_label_out_of_range', $${"function": "compute_inertia", "args": [[[1, 2]], [5], [[0, 0]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 32),
  (88, 'fc_ci_raises_on_non_list', $${"function": "compute_inertia", "args": ["abc", [0], [[0, 0]]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 33);

-- 验证
SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=88 GROUP BY task_id;

COMMIT;