-- MJ04 (task_id=85) function_call task_tests — 31 条

BEGIN;

-- 删除现有错误的 io_based task_tests
DELETE FROM task_tests WHERE task_id=85;

-- 插入新 fc 协议 task_tests
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (85, 'fc_sig_positive_two', $${"function": "sigmoid", "args": [[2]], "kwargs": {}}$$, $${"result": [0.8807970779], "tolerance": 0.0001}$$, false, 'function_call', 1),
  (85, 'fc_sig_three_values', $${"function": "sigmoid", "args": [[0, 1, -1]], "kwargs": {}}$$, $${"result": [0.5, 0.7310585786, 0.2689414214], "tolerance": 0.0001}$$, true, 'function_call', 2),
  (85, 'fc_sig_extreme_values', $${"function": "sigmoid", "args": [[10, -10]], "kwargs": {}}$$, $${"result": [0.9999546021, 4.53979e-05], "tolerance": 0.0001}$$, true, 'function_call', 3),
  (85, 'fc_sig_half_values', $${"function": "sigmoid", "args": [[0.5, -0.5]], "kwargs": {}}$$, $${"result": [0.6224593312, 0.3775406688], "tolerance": 0.0001}$$, true, 'function_call', 4),
  (85, 'fc_sig_empty', $${"function": "sigmoid", "args": [[]], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 5),
  (85, 'fc_sig_negative_extreme', $${"function": "sigmoid", "args": [[-100]], "kwargs": {}}$$, $${"result": [0.0], "tolerance": 0.0001}$$, true, 'function_call', 6),
  (85, 'fc_sig_raises_on_non_list', $${"function": "sigmoid", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (85, 'fc_sig_raises_on_non_numeric', $${"function": "sigmoid", "args": [[1, "a", 2]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (85, 'fc_cm_all_correct', $${"function": "compute_confusion_matrix", "args": [[1, 1, 0, 0], [1, 1, 0, 0]], "kwargs": {}}$$, $${"result": {"tp": 2, "fp": 0, "tn": 2, "fn": 0}}$$, false, 'function_call', 9),
  (85, 'fc_cm_all_wrong', $${"function": "compute_confusion_matrix", "args": [[1, 1, 0, 0], [0, 0, 1, 1]], "kwargs": {}}$$, $${"result": {"tp": 0, "fp": 2, "tn": 0, "fn": 2}}$$, true, 'function_call', 10),
  (85, 'fc_cm_mixed', $${"function": "compute_confusion_matrix", "args": [[1, 1, 0, 0], [1, 0, 1, 0]], "kwargs": {}}$$, $${"result": {"tp": 1, "fp": 1, "tn": 1, "fn": 1}}$$, true, 'function_call', 11),
  (85, 'fc_cm_unbalanced', $${"function": "compute_confusion_matrix", "args": [[1, 1, 1, 1, 1, 0, 0, 0, 0, 0], [1, 1, 1, 1, 1, 1, 1, 1, 0, 0]], "kwargs": {}}$$, $${"result": {"tp": 5, "fp": 3, "tn": 2, "fn": 0}}$$, true, 'function_call', 12),
  (85, 'fc_cm_all_negative', $${"function": "compute_confusion_matrix", "args": [[0, 0, 0], [0, 0, 0]], "kwargs": {}}$$, $${"result": {"tp": 0, "fp": 0, "tn": 3, "fn": 0}}$$, true, 'function_call', 13),
  (85, 'fc_cm_raises_on_empty', $${"function": "compute_confusion_matrix", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (85, 'fc_cm_raises_on_length_mismatch', $${"function": "compute_confusion_matrix", "args": [[1, 0, 1], [1, 0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (85, 'fc_cm_raises_on_non_list', $${"function": "compute_confusion_matrix", "args": ["01", "01"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (85, 'fc_m_typical', $${"function": "compute_metrics", "args": [50, 10, 30, 10], "kwargs": {}}$$, $${"result": {"accuracy": 0.8, "precision": 0.8333333333333334, "recall": 0.8333333333333334, "f1": 0.8333333333333334}, "tolerance": 0.0001}$$, false, 'function_call', 17),
  (85, 'fc_m_perfect', $${"function": "compute_metrics", "args": [10, 0, 90, 0], "kwargs": {}}$$, $${"result": {"accuracy": 1.0, "precision": 1.0, "recall": 1.0, "f1": 1.0}, "tolerance": 0.0001}$$, true, 'function_call', 18),
  (85, 'fc_m_zero_tp_with_fp', $${"function": "compute_metrics", "args": [0, 100, 0, 0], "kwargs": {}}$$, $${"result": {"accuracy": 0.0, "precision": 0.0, "recall": 0.0, "f1": 0.0}, "tolerance": 0.0001}$$, true, 'function_call', 19),
  (85, 'fc_m_balanced_half', $${"function": "compute_metrics", "args": [5, 5, 5, 5], "kwargs": {}}$$, $${"result": {"accuracy": 0.5, "precision": 0.5, "recall": 0.5, "f1": 0.5}, "tolerance": 0.0001}$$, true, 'function_call', 20),
  (85, 'fc_m_raises_on_all_zero', $${"function": "compute_metrics", "args": [0, 0, 0, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (85, 'fc_m_raises_on_negative', $${"function": "compute_metrics", "args": [-1, 0, 0, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (85, 'fc_m_raises_on_non_int', $${"function": "compute_metrics", "args": [1.5, 0, 0, 0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23),
  (85, 'fc_cbt_basic', $${"function": "classify_by_threshold", "args": [[0.1, 0.5, 0.9], 0.5], "kwargs": {}}$$, $${"result": [0, 1, 1]}$$, false, 'function_call', 24),
  (85, 'fc_cbt_near_extremes', $${"function": "classify_by_threshold", "args": [[0.05, 0.95], 0.5], "kwargs": {}}$$, $${"result": [0, 1]}$$, true, 'function_call', 25),
  (85, 'fc_cbt_at_boundary', $${"function": "classify_by_threshold", "args": [[0.5, 0.5], 0.5], "kwargs": {}}$$, $${"result": [1, 1]}$$, true, 'function_call', 26),
  (85, 'fc_cbt_around_threshold', $${"function": "classify_by_threshold", "args": [[0.4, 0.6], 0.5], "kwargs": {}}$$, $${"result": [0, 1]}$$, true, 'function_call', 27),
  (85, 'fc_cbt_high_threshold', $${"function": "classify_by_threshold", "args": [[0.1, 0.5, 0.9], 0.95], "kwargs": {}}$$, $${"result": [0, 0, 0]}$$, true, 'function_call', 28),
  (85, 'fc_cbt_negative_with_zero_threshold', $${"function": "classify_by_threshold", "args": [[-0.5, 0.5], 0.0], "kwargs": {}}$$, $${"result": [0, 1]}$$, true, 'function_call', 29),
  (85, 'fc_cbt_empty', $${"function": "classify_by_threshold", "args": [[], 0.5], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 30),
  (85, 'fc_cbt_raises_on_non_list', $${"function": "classify_by_threshold", "args": ["abc", 0.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 31);

-- 验证
SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=85 GROUP BY task_id;

COMMIT;