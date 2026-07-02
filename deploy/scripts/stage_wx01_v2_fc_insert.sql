-- WX01 (task_id=118) function_call task_tests — 33 条

BEGIN;

DELETE FROM task_tests WHERE task_id=118;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (118, 'fc_cls_valid_in_range', $${"function": "classify_value_status", "args": [5, 0, 10], "kwargs": {}}$$, $${"result": "valid"}$$, false, 'function_call', 1),
  (118, 'fc_cls_out_of_range_low', $${"function": "classify_value_status", "args": [-5, 0, 10], "kwargs": {}}$$, $${"result": "out_of_range"}$$, true, 'function_call', 2),
  (118, 'fc_cls_out_of_range_high', $${"function": "classify_value_status", "args": [100, 0, 10], "kwargs": {}}$$, $${"result": "out_of_range"}$$, true, 'function_call', 3),
  (118, 'fc_cls_missing_none', $${"function": "classify_value_status", "args": [null, 0, 10], "kwargs": {}}$$, $${"result": "missing"}$$, true, 'function_call', 4),
  (118, 'fc_cls_missing_empty_string', $${"function": "classify_value_status", "args": ["", 0, 10], "kwargs": {}}$$, $${"result": "missing"}$$, true, 'function_call', 5),
  (118, 'fc_cls_missing_custom_marker', $${"function": "classify_value_status", "args": [-1, 0, 10], "kwargs": {"missing_marker": -1}}$$, $${"result": "missing"}$$, true, 'function_call', 6),
  (118, 'fc_cls_negative_in_range', $${"function": "classify_value_status", "args": [-3, -10, 5], "kwargs": {}}$$, $${"result": "valid"}$$, true, 'function_call', 7),
  (118, 'fc_cls_raises_on_non_numeric_min', $${"function": "classify_value_status", "args": [5, "0", 10], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (118, 'fc_qr_perfect', $${"function": "compute_quality_ratio", "args": [100, 100], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 9),
  (118, 'fc_qr_half', $${"function": "compute_quality_ratio", "args": [50, 100], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 10),
  (118, 'fc_qr_partial_78', $${"function": "compute_quality_ratio", "args": [78, 100], "kwargs": {}}$$, $${"result": 0.78, "tolerance": 1e-06}$$, true, 'function_call', 11),
  (118, 'fc_qr_zero_valid', $${"function": "compute_quality_ratio", "args": [0, 100], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 12),
  (118, 'fc_qr_three_quarters', $${"function": "compute_quality_ratio", "args": [3, 4], "kwargs": {}}$$, $${"result": 0.75, "tolerance": 1e-06}$$, true, 'function_call', 13),
  (118, 'fc_qr_raises_on_zero_total', $${"function": "compute_quality_ratio", "args": [0, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (118, 'fc_qr_raises_on_valid_gt_total', $${"function": "compute_quality_ratio", "args": [101, 100], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (118, 'fc_qr_raises_on_non_int', $${"function": "compute_quality_ratio", "args": [5.0, 10], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (118, 'fc_priority_missing', $${"function": "get_cleaning_priority", "args": ["missing"], "kwargs": {}}$$, $${"result": 1}$$, false, 'function_call', 17),
  (118, 'fc_priority_duplicate', $${"function": "get_cleaning_priority", "args": ["duplicate"], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 18),
  (118, 'fc_priority_outlier', $${"function": "get_cleaning_priority", "args": ["outlier"], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 19),
  (118, 'fc_priority_format', $${"function": "get_cleaning_priority", "args": ["format"], "kwargs": {}}$$, $${"result": 4}$$, true, 'function_call', 20),
  (118, 'fc_priority_consistency', $${"function": "get_cleaning_priority", "args": ["consistency"], "kwargs": {}}$$, $${"result": 5}$$, true, 'function_call', 21),
  (118, 'fc_priority_raises_on_unknown', $${"function": "get_cleaning_priority", "args": ["unknown_step"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (118, 'fc_priority_raises_on_empty', $${"function": "get_cleaning_priority", "args": [""], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (118, 'fc_priority_raises_on_non_string', $${"function": "get_cleaning_priority", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24),
  (118, 'fc_decide_drop_high_missing', $${"function": "decide_drop_or_fill", "args": [80, 100, 0.5], "kwargs": {}}$$, $${"result": "drop"}$$, false, 'function_call', 25),
  (118, 'fc_decide_fill_low_missing', $${"function": "decide_drop_or_fill", "args": [20, 100, 0.5], "kwargs": {}}$$, $${"result": "fill"}$$, true, 'function_call', 26),
  (118, 'fc_decide_just_above_threshold', $${"function": "decide_drop_or_fill", "args": [51, 100, 0.5], "kwargs": {}}$$, $${"result": "drop"}$$, true, 'function_call', 27),
  (118, 'fc_decide_zero_missing', $${"function": "decide_drop_or_fill", "args": [0, 100, 0.5], "kwargs": {}}$$, $${"result": "fill"}$$, true, 'function_call', 28),
  (118, 'fc_decide_custom_threshold_03_a', $${"function": "decide_drop_or_fill", "args": [20, 100, 0.3], "kwargs": {}}$$, $${"result": "fill"}$$, true, 'function_call', 29),
  (118, 'fc_decide_custom_threshold_03_b', $${"function": "decide_drop_or_fill", "args": [40, 100, 0.3], "kwargs": {}}$$, $${"result": "drop"}$$, true, 'function_call', 30),
  (118, 'fc_decide_raises_on_zero_total', $${"function": "decide_drop_or_fill", "args": [0, 0, 0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (118, 'fc_decide_raises_on_invalid_threshold', $${"function": "decide_drop_or_fill", "args": [20, 100, 1.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 32),
  (118, 'fc_decide_raises_on_non_int', $${"function": "decide_drop_or_fill", "args": ["20", 100, 0.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 33);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=118 GROUP BY task_id;

COMMIT;