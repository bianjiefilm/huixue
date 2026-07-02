-- CV04 (task_id=109) function_call task_tests — 28 条

BEGIN;

DELETE FROM task_tests WHERE task_id=109;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (109, 'fc_mean_basic', $${"function": "apply_mean_filter", "args": [[1, 2, 3, 4, 5]], "kwargs": {}}$$, $${"result": 3.0, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (109, 'fc_mean_with_outlier', $${"function": "apply_mean_filter", "args": [[10, 20, 200]], "kwargs": {}}$$, $${"result": 76.66666666666667, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (109, 'fc_mean_zeros', $${"function": "apply_mean_filter", "args": [[0, 0, 0]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (109, 'fc_mean_two_distinct', $${"function": "apply_mean_filter", "args": [[42, 100]], "kwargs": {}}$$, $${"result": 71.0, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (109, 'fc_mean_negative', $${"function": "apply_mean_filter", "args": [[-1, 1, 0]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (109, 'fc_mean_raises_on_empty', $${"function": "apply_mean_filter", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (109, 'fc_mean_raises_on_non_list', $${"function": "apply_mean_filter", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (109, 'fc_med_odd', $${"function": "apply_median_filter", "args": [[1, 2, 3, 4, 5]], "kwargs": {}}$$, $${"result": 3.0, "tolerance": 1e-06}$$, false, 'function_call', 8),
  (109, 'fc_med_even', $${"function": "apply_median_filter", "args": [[1, 2, 3, 4]], "kwargs": {}}$$, $${"result": 2.5, "tolerance": 1e-06}$$, true, 'function_call', 9),
  (109, 'fc_med_outlier_ignored', $${"function": "apply_median_filter", "args": [[10, 20, 200]], "kwargs": {}}$$, $${"result": 20.0, "tolerance": 1e-06}$$, true, 'function_call', 10),
  (109, 'fc_med_unsorted', $${"function": "apply_median_filter", "args": [[5, 1, 3, 2, 4]], "kwargs": {}}$$, $${"result": 3.0, "tolerance": 1e-06}$$, true, 'function_call', 11),
  (109, 'fc_med_two_distinct', $${"function": "apply_median_filter", "args": [[42, 100]], "kwargs": {}}$$, $${"result": 71.0, "tolerance": 1e-06}$$, true, 'function_call', 12),
  (109, 'fc_med_raises_on_empty', $${"function": "apply_median_filter", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (109, 'fc_med_raises_on_non_list', $${"function": "apply_median_filter", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 14),
  (109, 'fc_gauss_size1', $${"function": "compute_gaussian_kernel_1d", "args": [1, 1.0], "kwargs": {}}$$, $${"result": [1.0], "tolerance": 1e-06}$$, false, 'function_call', 15),
  (109, 'fc_gauss_size3_sigma1', $${"function": "compute_gaussian_kernel_1d", "args": [3, 1.0], "kwargs": {}}$$, $${"result": [0.274068619061197, 0.45186276187760605, 0.274068619061197], "tolerance": 1e-06}$$, true, 'function_call', 16),
  (109, 'fc_gauss_size5_sigma1', $${"function": "compute_gaussian_kernel_1d", "args": [5, 1.0], "kwargs": {}}$$, $${"result": [0.054488684549642945, 0.24420134200323335, 0.40261994689424746, 0.24420134200323335, 0.054488684549642945], "tolerance": 1e-06}$$, true, 'function_call', 17),
  (109, 'fc_gauss_raises_on_even_size', $${"function": "compute_gaussian_kernel_1d", "args": [4, 1.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (109, 'fc_gauss_raises_on_zero_sigma', $${"function": "compute_gaussian_kernel_1d", "args": [3, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 19),
  (109, 'fc_gauss_raises_on_non_int_size', $${"function": "compute_gaussian_kernel_1d", "args": [3.0, 1.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 20),
  (109, 'fc_f1d_simple', $${"function": "apply_filter_1d", "args": [[1, 2, 3], [1, 1]], "kwargs": {}}$$, $${"result": [3, 5]}$$, false, 'function_call', 21),
  (109, 'fc_f1d_identity_kernel', $${"function": "apply_filter_1d", "args": [[1, 2, 3], [1]], "kwargs": {}}$$, $${"result": [1, 2, 3]}$$, true, 'function_call', 22),
  (109, 'fc_f1d_average_kernel', $${"function": "apply_filter_1d", "args": [[1, 2, 3, 4, 5], [0.3333333333333333, 0.3333333333333333, 0.3333333333333333]], "kwargs": {}}$$, $${"result": [2.0, 3.0, 4.0], "tolerance": 1e-06}$$, true, 'function_call', 23),
  (109, 'fc_f1d_kernel_equals_input', $${"function": "apply_filter_1d", "args": [[1, 2, 3], [0.5, 0.5, 0.5]], "kwargs": {}}$$, $${"result": [3.0], "tolerance": 1e-06}$$, true, 'function_call', 24),
  (109, 'fc_f1d_negative_kernel', $${"function": "apply_filter_1d", "args": [[1, 2, 3, 4], [1, -1]], "kwargs": {}}$$, $${"result": [-1, -1, -1]}$$, true, 'function_call', 25),
  (109, 'fc_f1d_raises_on_kernel_too_long', $${"function": "apply_filter_1d", "args": [[1, 2], [1, 1, 1]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 26),
  (109, 'fc_f1d_raises_on_empty', $${"function": "apply_filter_1d", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 27),
  (109, 'fc_f1d_raises_on_non_list', $${"function": "apply_filter_1d", "args": ["ab", [1]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 28);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=109 GROUP BY task_id;

COMMIT;