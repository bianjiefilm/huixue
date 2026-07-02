-- WX11 (task_id=128) function_call task_tests — 28 条

BEGIN;

DELETE FROM task_tests WHERE task_id=128;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (128, 'fc_comp_no_missing', $${"function": "compute_completeness", "args": [[1, 2, 3, 4]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (128, 'fc_comp_two_missing_in_5', $${"function": "compute_completeness", "args": [[1, null, 3, "", 5]], "kwargs": {}}$$, $${"result": 0.6, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (128, 'fc_comp_three_missing_in_4', $${"function": "compute_completeness", "args": [[null, "NA", "null", 1]], "kwargs": {}}$$, $${"result": 0.25, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (128, 'fc_comp_custom_markers', $${"function": "compute_completeness", "args": [[1, -999, 2, -999]], "kwargs": {"markers": [-999]}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (128, 'fc_comp_one_missing_in_3', $${"function": "compute_completeness", "args": [[1, 2, null]], "kwargs": {}}$$, $${"result": 0.6666666666666666, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (128, 'fc_comp_raises_on_empty', $${"function": "compute_completeness", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (128, 'fc_comp_raises_on_non_list', $${"function": "compute_completeness", "args": ["123"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (128, 'fc_uniq_all_distinct_5', $${"function": "compute_uniqueness", "args": [[1, 2, 3, 4, 5]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 8),
  (128, 'fc_uniq_2_in_4', $${"function": "compute_uniqueness", "args": [[1, 2, 1, 2]], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 9),
  (128, 'fc_uniq_3_in_5', $${"function": "compute_uniqueness", "args": [[1, 1, 2, 2, 3]], "kwargs": {}}$$, $${"result": 0.6, "tolerance": 1e-06}$$, true, 'function_call', 10),
  (128, 'fc_uniq_1_in_5', $${"function": "compute_uniqueness", "args": [[7, 7, 7, 7, 7]], "kwargs": {}}$$, $${"result": 0.2, "tolerance": 1e-06}$$, true, 'function_call', 11),
  (128, 'fc_uniq_2_in_3_strings', $${"function": "compute_uniqueness", "args": [["a", "b", "a"]], "kwargs": {}}$$, $${"result": 0.6666666666666666, "tolerance": 1e-06}$$, true, 'function_call', 12),
  (128, 'fc_uniq_raises_on_empty', $${"function": "compute_uniqueness", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (128, 'fc_uniq_raises_on_non_list', $${"function": "compute_uniqueness", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 14),
  (128, 'fc_valid_all_in_range', $${"function": "compute_validity_in_range", "args": [[5, 10, 15], 0, 20], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 15),
  (128, 'fc_valid_two_out_of_three', $${"function": "compute_validity_in_range", "args": [[5, 100, 15], 0, 20], "kwargs": {}}$$, $${"result": 0.6666666666666666, "tolerance": 1e-06}$$, true, 'function_call', 16),
  (128, 'fc_valid_one_in_four', $${"function": "compute_validity_in_range", "args": [[5, 100, 200, 300], 0, 50], "kwargs": {}}$$, $${"result": 0.25, "tolerance": 1e-06}$$, true, 'function_call', 17),
  (128, 'fc_valid_three_in_five', $${"function": "compute_validity_in_range", "args": [[5, 10, 15, 25, 30], 0, 20], "kwargs": {}}$$, $${"result": 0.6, "tolerance": 1e-06}$$, true, 'function_call', 18),
  (128, 'fc_valid_at_boundaries', $${"function": "compute_validity_in_range", "args": [[0, 20, -1, 21], 0, 20], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 19),
  (128, 'fc_valid_raises_on_empty', $${"function": "compute_validity_in_range", "args": [[], 0, 100], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 20),
  (128, 'fc_valid_raises_on_lower_gt_upper', $${"function": "compute_validity_in_range", "args": [[1, 2, 3], 10, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (128, 'fc_summary_perfect', $${"function": "quality_summary_dict", "args": [1.0, 1.0, 1.0], "kwargs": {}}$$, $${"result": {"completeness": 1.0, "uniqueness": 1.0, "validity": 1.0, "overall": 1.0}, "tolerance": 1e-06}$$, false, 'function_call', 22),
  (128, 'fc_summary_typical', $${"function": "quality_summary_dict", "args": [0.9, 0.5, 0.8], "kwargs": {}}$$, $${"result": {"completeness": 0.9, "uniqueness": 0.5, "validity": 0.8, "overall": 0.7333333333333334}, "tolerance": 1e-06}$$, true, 'function_call', 23),
  (128, 'fc_summary_low_quality', $${"function": "quality_summary_dict", "args": [0.5, 0.3, 0.4], "kwargs": {}}$$, $${"result": {"completeness": 0.5, "uniqueness": 0.3, "validity": 0.4, "overall": 0.4}, "tolerance": 1e-06}$$, true, 'function_call', 24),
  (128, 'fc_summary_zero', $${"function": "quality_summary_dict", "args": [0.0, 0.0, 0.0], "kwargs": {}}$$, $${"result": {"completeness": 0.0, "uniqueness": 0.0, "validity": 0.0, "overall": 0.0}, "tolerance": 1e-06}$$, true, 'function_call', 25),
  (128, 'fc_summary_keys_complete', $${"function": "quality_summary_dict", "args": [0.5, 0.5, 0.5], "kwargs": {}}$$, $${"result": {"completeness": 0.5, "uniqueness": 0.5, "validity": 0.5, "overall": 0.5}, "tolerance": 1e-06}$$, true, 'function_call', 26),
  (128, 'fc_summary_raises_on_out_of_range', $${"function": "quality_summary_dict", "args": [1.5, 0.5, 0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 27),
  (128, 'fc_summary_raises_on_non_numeric', $${"function": "quality_summary_dict", "args": ["0.5", 0.5, 0.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 28);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=128 GROUP BY task_id;

COMMIT;