-- WX02 (task_id=119) function_call task_tests — 26 条

BEGIN;

DELETE FROM task_tests WHERE task_id=119;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (119, 'fc_im_none', $${"function": "is_missing", "args": [null], "kwargs": {}}$$, $${"result": true}$$, false, 'function_call', 1),
  (119, 'fc_im_empty_string', $${"function": "is_missing", "args": [""], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 2),
  (119, 'fc_im_real_number_not_missing', $${"function": "is_missing", "args": [5], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 3),
  (119, 'fc_im_zero_not_missing', $${"function": "is_missing", "args": [0], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 4),
  (119, 'fc_im_normal_string_not_missing', $${"function": "is_missing", "args": ["hello"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 5),
  (119, 'fc_im_custom_markers_a', $${"function": "is_missing", "args": [-999], "kwargs": {"markers": [-999, null]}}$$, $${"result": true}$$, true, 'function_call', 6),
  (119, 'fc_im_custom_markers_b', $${"function": "is_missing", "args": [-1], "kwargs": {"markers": [-999]}}$$, $${"result": false}$$, true, 'function_call', 7),
  (119, 'fc_cm_no_missing', $${"function": "count_missing", "args": [[1, 2, 3]], "kwargs": {}}$$, $${"result": 0}$$, false, 'function_call', 8),
  (119, 'fc_cm_some_missing', $${"function": "count_missing", "args": [[1, null, 2, "NA", 3]], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 9),
  (119, 'fc_cm_all_missing', $${"function": "count_missing", "args": [[null, "", "NA"]], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 10),
  (119, 'fc_cm_zero_not_missing', $${"function": "count_missing", "args": [[0, 1, 2]], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 11),
  (119, 'fc_cm_with_custom_markers', $${"function": "count_missing", "args": [[1, -999, 2, -999]], "kwargs": {"markers": [-999]}}$$, $${"result": 2}$$, true, 'function_call', 12),
  (119, 'fc_cm_raises_on_non_list', $${"function": "count_missing", "args": ["not a list"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 13),
  (119, 'fc_fm_one_missing_middle', $${"function": "fill_missing_with_mean", "args": [[1.0, null, 3.0]], "kwargs": {}}$$, $${"result": [1.0, 2.0, 3.0], "tolerance": 1e-06}$$, false, 'function_call', 14),
  (119, 'fc_fm_two_missing', $${"function": "fill_missing_with_mean", "args": [[1.0, null, 5.0, null, 3.0]], "kwargs": {}}$$, $${"result": [1.0, 3.0, 5.0, 3.0, 3.0], "tolerance": 1e-06}$$, true, 'function_call', 15),
  (119, 'fc_fm_string_marker', $${"function": "fill_missing_with_mean", "args": [[1.0, "NA", 3.0, 5.0]], "kwargs": {}}$$, $${"result": [1.0, 3.0, 3.0, 5.0], "tolerance": 1e-06}$$, true, 'function_call', 16),
  (119, 'fc_fm_decimal_mean', $${"function": "fill_missing_with_mean", "args": [[1.0, null, 2.0]], "kwargs": {}}$$, $${"result": [1.0, 1.5, 2.0], "tolerance": 1e-06}$$, true, 'function_call', 17),
  (119, 'fc_fm_negative_values', $${"function": "fill_missing_with_mean", "args": [[-2.0, null, 4.0]], "kwargs": {}}$$, $${"result": [-2.0, 1.0, 4.0], "tolerance": 1e-06}$$, true, 'function_call', 18),
  (119, 'fc_fm_raises_on_all_missing', $${"function": "fill_missing_with_mean", "args": [[null, "NA", null]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 19),
  (119, 'fc_fm_raises_on_empty', $${"function": "fill_missing_with_mean", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 20),
  (119, 'fc_fm_raises_on_non_list', $${"function": "fill_missing_with_mean", "args": ["1,2,3"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 21),
  (119, 'fc_fc_basic', $${"function": "fill_missing_with_constant", "args": [[1, null, 3], 0], "kwargs": {}}$$, $${"result": [1, 0, 3]}$$, false, 'function_call', 22),
  (119, 'fc_fc_string_constant', $${"function": "fill_missing_with_constant", "args": [[null, "x", "NA", "y"], "unknown"], "kwargs": {}}$$, $${"result": ["unknown", "x", "unknown", "y"]}$$, true, 'function_call', 23),
  (119, 'fc_fc_zero_constant', $${"function": "fill_missing_with_constant", "args": [[1, null, 2, "NA"], 0], "kwargs": {}}$$, $${"result": [1, 0, 2, 0]}$$, true, 'function_call', 24),
  (119, 'fc_fc_negative_constant', $${"function": "fill_missing_with_constant", "args": [[null, 5], -1], "kwargs": {}}$$, $${"result": [-1, 5]}$$, true, 'function_call', 25),
  (119, 'fc_fc_raises_on_non_list', $${"function": "fill_missing_with_constant", "args": ["None", 0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 26);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=119 GROUP BY task_id;

COMMIT;