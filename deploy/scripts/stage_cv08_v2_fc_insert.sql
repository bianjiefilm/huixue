-- CV08 (task_id=113) function_call task_tests — 31 条

BEGIN;

DELETE FROM task_tests WHERE task_id=113;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (113, 'fc_ssd_identical', $${"function": "template_match_ssd", "args": [[1.0, 2.0, 3.0], [1.0, 2.0, 3.0]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (113, 'fc_ssd_off_by_two', $${"function": "template_match_ssd", "args": [[1.0, 2.0, 3.0], [3.0, 4.0, 5.0]], "kwargs": {}}$$, $${"result": 12.0, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (113, 'fc_ssd_general', $${"function": "template_match_ssd", "args": [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], "kwargs": {}}$$, $${"result": 27.0, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (113, 'fc_ssd_negative_diff', $${"function": "template_match_ssd", "args": [[5.0, 5.0], [3.0, 2.0]], "kwargs": {}}$$, $${"result": 13.0, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (113, 'fc_ssd_single_element', $${"function": "template_match_ssd", "args": [[10.0], [3.0]], "kwargs": {}}$$, $${"result": 49.0, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (113, 'fc_ssd_raises_on_length_mismatch', $${"function": "template_match_ssd", "args": [[1.0, 2.0], [1.0, 2.0, 3.0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (113, 'fc_ssd_raises_on_non_list', $${"function": "template_match_ssd", "args": ["abc", [1.0, 2.0, 3.0]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (113, 'fc_argmax_simple', $${"function": "find_max_correlation", "args": [[1.0, 5.0, 3.0]], "kwargs": {}}$$, $${"result": 1}$$, false, 'function_call', 8),
  (113, 'fc_argmax_at_start', $${"function": "find_max_correlation", "args": [[10.0, 5.0, 3.0, 1.0]], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 9),
  (113, 'fc_argmax_at_end', $${"function": "find_max_correlation", "args": [[1.0, 2.0, 3.0, 10.0]], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 10),
  (113, 'fc_argmax_with_negatives', $${"function": "find_max_correlation", "args": [[-5.0, -1.0, -3.0]], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 11),
  (113, 'fc_argmax_ties_first', $${"function": "find_max_correlation", "args": [[5.0, 5.0, 3.0]], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 12),
  (113, 'fc_argmax_single', $${"function": "find_max_correlation", "args": [[42.0]], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 13),
  (113, 'fc_argmax_raises_on_empty', $${"function": "find_max_correlation", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (113, 'fc_argmax_raises_on_non_list', $${"function": "find_max_correlation", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (113, 'fc_nms_radius_1_simple', $${"function": "non_max_suppression_1d", "args": [[1.0, 5.0, 1.0, 3.0, 1.0], 1], "kwargs": {}}$$, $${"result": [1, 3]}$$, false, 'function_call', 16),
  (113, 'fc_nms_radius_2', $${"function": "non_max_suppression_1d", "args": [[1.0, 5.0, 1.0, 3.0, 1.0], 2], "kwargs": {}}$$, $${"result": [1, 4]}$$, true, 'function_call', 17),
  (113, 'fc_nms_single_peak', $${"function": "non_max_suppression_1d", "args": [[1.0, 1.0, 10.0, 1.0, 1.0], 1], "kwargs": {}}$$, $${"result": [0, 2, 4]}$$, true, 'function_call', 18),
  (113, 'fc_nms_all_same', $${"function": "non_max_suppression_1d", "args": [[3.0, 3.0, 3.0, 3.0, 3.0], 1], "kwargs": {}}$$, $${"result": [0, 2, 4]}$$, true, 'function_call', 19),
  (113, 'fc_nms_large_radius_kills_others', $${"function": "non_max_suppression_1d", "args": [[1.0, 5.0, 1.0, 3.0, 1.0], 10], "kwargs": {}}$$, $${"result": [1]}$$, true, 'function_call', 20),
  (113, 'fc_nms_raises_on_empty', $${"function": "non_max_suppression_1d", "args": [[], 1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (113, 'fc_nms_raises_on_non_list', $${"function": "non_max_suppression_1d", "args": ["abc", 1], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 22),
  (113, 'fc_sw_simple', $${"function": "sliding_window_count", "args": [10, 3, 1], "kwargs": {}}$$, $${"result": 8}$$, false, 'function_call', 23),
  (113, 'fc_sw_stride_2', $${"function": "sliding_window_count", "args": [10, 3, 2], "kwargs": {}}$$, $${"result": 4}$$, true, 'function_call', 24),
  (113, 'fc_sw_stride_3', $${"function": "sliding_window_count", "args": [15, 4, 3], "kwargs": {}}$$, $${"result": 4}$$, true, 'function_call', 25),
  (113, 'fc_sw_window_equals_image', $${"function": "sliding_window_count", "args": [5, 5, 1], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 26),
  (113, 'fc_sw_large_image', $${"function": "sliding_window_count", "args": [100, 10, 5], "kwargs": {}}$$, $${"result": 19}$$, true, 'function_call', 27),
  (113, 'fc_sw_stride_5', $${"function": "sliding_window_count", "args": [20, 5, 4], "kwargs": {}}$$, $${"result": 4}$$, true, 'function_call', 28),
  (113, 'fc_sw_raises_on_window_gt_image', $${"function": "sliding_window_count", "args": [3, 10, 1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 29),
  (113, 'fc_sw_raises_on_zero_stride', $${"function": "sliding_window_count", "args": [10, 3, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (113, 'fc_sw_raises_on_non_int', $${"function": "sliding_window_count", "args": [10.0, 3, 1], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 31);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=113 GROUP BY task_id;

COMMIT;