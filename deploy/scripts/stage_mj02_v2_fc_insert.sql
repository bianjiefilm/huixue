-- MJ02 (task_id=83) function_call task_tests — 31 条

BEGIN;

-- 删除现有错误的 io_based task_tests
DELETE FROM task_tests WHERE task_id=83;

-- 插入新 fc 协议 task_tests
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (83, 'fc_corr_perfect_positive', $${"function": "compute_correlation", "args": [[1, 2, 3, 4, 5], [1, 2, 3, 4, 5]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (83, 'fc_corr_perfect_negative', $${"function": "compute_correlation", "args": [[1, 2, 3, 4, 5], [5, 4, 3, 2, 1]], "kwargs": {}}$$, $${"result": -1.0, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (83, 'fc_corr_known_value_0_8', $${"function": "compute_correlation", "args": [[1, 2, 3, 4], [1, 3, 2, 4]], "kwargs": {}}$$, $${"result": 0.8, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (83, 'fc_corr_zero', $${"function": "compute_correlation", "args": [[1, 2, 3, 4, 5], [1, 4, 5, 4, 1]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (83, 'fc_corr_linear_scaled', $${"function": "compute_correlation", "args": [[1, 2, 3, 4, 5], [2, 4, 6, 8, 10]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (83, 'fc_corr_raises_on_zero_variance', $${"function": "compute_correlation", "args": [[5, 5, 5, 5], [1, 2, 3, 4]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (83, 'fc_corr_raises_on_length_mismatch', $${"function": "compute_correlation", "args": [[1, 2, 3], [1, 2]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (83, 'fc_corr_raises_on_non_list', $${"function": "compute_correlation", "args": ["abc", "xyz"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (83, 'fc_iqr_high_outlier', $${"function": "find_outliers_iqr", "args": [[1, 2, 3, 4, 5, 100]], "kwargs": {}}$$, $${"result": [5]}$$, false, 'function_call', 9),
  (83, 'fc_iqr_low_outlier', $${"function": "find_outliers_iqr", "args": [[-100, 1, 2, 3, 4, 5]], "kwargs": {}}$$, $${"result": [0]}$$, true, 'function_call', 10),
  (83, 'fc_iqr_both_extremes', $${"function": "find_outliers_iqr", "args": [[1, 2, 3, 4, 5, 100, -50]], "kwargs": {}}$$, $${"result": [5, 6]}$$, true, 'function_call', 11),
  (83, 'fc_iqr_no_outliers', $${"function": "find_outliers_iqr", "args": [[1, 2, 3, 4, 5]], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 12),
  (83, 'fc_iqr_middle_extreme', $${"function": "find_outliers_iqr", "args": [[10, 20, 1000, 30, 40]], "kwargs": {}}$$, $${"result": [2]}$$, true, 'function_call', 13),
  (83, 'fc_iqr_two_high_outliers', $${"function": "find_outliers_iqr", "args": [[1, 2, 2, 3, 3, 3, 4, 4, 5, 200, 300]], "kwargs": {}}$$, $${"result": [9, 10]}$$, true, 'function_call', 14),
  (83, 'fc_iqr_raises_on_empty', $${"function": "find_outliers_iqr", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (83, 'fc_iqr_raises_on_non_list', $${"function": "find_outliers_iqr", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (83, 'fc_summary_basic', $${"function": "summarize_distribution", "args": [[1, 2, 3, 4, 5]], "kwargs": {}}$$, $${"result": {"mean": 3.0, "median": 3.0, "std": 1.4142135623730951, "range": 4.0}, "tolerance": 0.0001}$$, false, 'function_call', 17),
  (83, 'fc_summary_constant', $${"function": "summarize_distribution", "args": [[7, 7, 7, 7]], "kwargs": {}}$$, $${"result": {"mean": 7.0, "median": 7.0, "std": 0.0, "range": 0.0}, "tolerance": 1e-06}$$, true, 'function_call', 18),
  (83, 'fc_summary_signed', $${"function": "summarize_distribution", "args": [[-5, -1, 0, 1, 5]], "kwargs": {}}$$, $${"result": {"mean": 0.0, "median": 0.0, "std": 3.22490309931942, "range": 10.0}, "tolerance": 0.0001}$$, true, 'function_call', 19),
  (83, 'fc_summary_single_element', $${"function": "summarize_distribution", "args": [[42]], "kwargs": {}}$$, $${"result": {"mean": 42.0, "median": 42.0, "std": 0.0, "range": 0.0}, "tolerance": 1e-06}$$, true, 'function_call', 20),
  (83, 'fc_summary_even_count_median', $${"function": "summarize_distribution", "args": [[1, 2, 3, 4, 5, 6]], "kwargs": {}}$$, $${"result": {"mean": 3.5, "median": 3.5, "std": 1.707825127659933, "range": 5.0}, "tolerance": 0.0001}$$, true, 'function_call', 21),
  (83, 'fc_summary_raises_on_empty', $${"function": "summarize_distribution", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (83, 'fc_summary_raises_on_non_list', $${"function": "summarize_distribution", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23),
  (83, 'fc_quartiles_unsorted_5', $${"function": "compute_quartiles", "args": [[3, 1, 4, 1, 5]], "kwargs": {}}$$, $${"result": [1.0, 1.0, 3.0, 4.0, 5.0], "tolerance": 1e-06}$$, false, 'function_call', 24),
  (83, 'fc_quartiles_ten_values', $${"function": "compute_quartiles", "args": [[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]], "kwargs": {}}$$, $${"result": [10.0, 32.5, 55.0, 77.5, 100.0], "tolerance": 1e-06}$$, true, 'function_call', 25),
  (83, 'fc_quartiles_single_element', $${"function": "compute_quartiles", "args": [[42]], "kwargs": {}}$$, $${"result": [42.0, 42.0, 42.0, 42.0, 42.0], "tolerance": 1e-06}$$, true, 'function_call', 26),
  (83, 'fc_quartiles_constant', $${"function": "compute_quartiles", "args": [[3, 3, 3, 3]], "kwargs": {}}$$, $${"result": [3.0, 3.0, 3.0, 3.0, 3.0], "tolerance": 1e-06}$$, true, 'function_call', 27),
  (83, 'fc_quartiles_two_values', $${"function": "compute_quartiles", "args": [[0, 100]], "kwargs": {}}$$, $${"result": [0.0, 25.0, 50.0, 75.0, 100.0], "tolerance": 1e-06}$$, true, 'function_call', 28),
  (83, 'fc_quartiles_negative_values_unsorted', $${"function": "compute_quartiles", "args": [[10, -10, 5, -5, 0]], "kwargs": {}}$$, $${"result": [-10.0, -5.0, 0.0, 5.0, 10.0], "tolerance": 1e-06}$$, true, 'function_call', 29),
  (83, 'fc_quartiles_raises_on_empty', $${"function": "compute_quartiles", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (83, 'fc_quartiles_raises_on_non_list', $${"function": "compute_quartiles", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 31);

-- 验证
SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=83 GROUP BY task_id;

COMMIT;