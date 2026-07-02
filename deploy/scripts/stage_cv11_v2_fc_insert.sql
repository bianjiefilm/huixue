-- CV11 (task_id=116) function_call task_tests — 34 条

BEGIN;

DELETE FROM task_tests WHERE task_id=116;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (116, 'fc_seg_basic', $${"function": "binary_threshold_segment", "args": [[0.1, 0.5, 0.9], 0.5], "kwargs": {}}$$, $${"result": [0, 1, 1]}$$, false, 'function_call', 1),
  (116, 'fc_seg_at_threshold', $${"function": "binary_threshold_segment", "args": [[0.5, 0.4, 0.5, 0.6], 0.5], "kwargs": {}}$$, $${"result": [1, 0, 1, 1]}$$, true, 'function_call', 2),
  (116, 'fc_seg_all_below', $${"function": "binary_threshold_segment", "args": [[0.1, 0.2, 0.3], 0.5], "kwargs": {}}$$, $${"result": [0, 0, 0]}$$, true, 'function_call', 3),
  (116, 'fc_seg_all_above', $${"function": "binary_threshold_segment", "args": [[0.6, 0.7, 0.8], 0.5], "kwargs": {}}$$, $${"result": [1, 1, 1]}$$, true, 'function_call', 4),
  (116, 'fc_seg_negative_values', $${"function": "binary_threshold_segment", "args": [[-0.1, -0.5, 0.5, 1.0], 0.0], "kwargs": {}}$$, $${"result": [0, 0, 1, 1]}$$, true, 'function_call', 5),
  (116, 'fc_seg_mixed_decimals', $${"function": "binary_threshold_segment", "args": [[0.49, 0.51, 0.5, 0.4], 0.5], "kwargs": {}}$$, $${"result": [0, 1, 1, 0]}$$, true, 'function_call', 6),
  (116, 'fc_seg_single_above', $${"function": "binary_threshold_segment", "args": [[0.7], 0.5], "kwargs": {}}$$, $${"result": [1]}$$, true, 'function_call', 7),
  (116, 'fc_seg_raises_on_empty', $${"function": "binary_threshold_segment", "args": [[], 0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 8),
  (116, 'fc_seg_raises_on_non_list', $${"function": "binary_threshold_segment", "args": ["0.5", 0.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 9),
  (116, 'fc_cc_no_ones', $${"function": "connected_components_count_1d", "args": [[0, 0, 0]], "kwargs": {}}$$, $${"result": 0}$$, false, 'function_call', 10),
  (116, 'fc_cc_all_ones', $${"function": "connected_components_count_1d", "args": [[1, 1, 1, 1]], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 11),
  (116, 'fc_cc_two_segments', $${"function": "connected_components_count_1d", "args": [[1, 1, 0, 0, 1, 1]], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 12),
  (116, 'fc_cc_alternating', $${"function": "connected_components_count_1d", "args": [[1, 0, 1, 0, 1]], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 13),
  (116, 'fc_cc_start_with_one', $${"function": "connected_components_count_1d", "args": [[1, 1, 0, 1]], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 14),
  (116, 'fc_cc_two_long', $${"function": "connected_components_count_1d", "args": [[1, 1, 1, 0, 1, 1]], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 15),
  (116, 'fc_cc_single_one', $${"function": "connected_components_count_1d", "args": [[0, 0, 1, 0]], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 16),
  (116, 'fc_cc_raises_on_invalid_value', $${"function": "connected_components_count_1d", "args": [[0, 1, 2]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 17),
  (116, 'fc_cc_raises_on_non_list', $${"function": "connected_components_count_1d", "args": ["01001"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 18),
  (116, 'fc_dice_perfect', $${"function": "dice_coefficient", "args": [[1, 0, 1, 1, 0], [1, 0, 1, 1, 0]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 19),
  (116, 'fc_dice_disjoint', $${"function": "dice_coefficient", "args": [[1, 1, 0, 0], [0, 0, 1, 1]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 20),
  (116, 'fc_dice_partial', $${"function": "dice_coefficient", "args": [[1, 1, 1, 0], [1, 1, 0, 0]], "kwargs": {}}$$, $${"result": 0.8, "tolerance": 1e-06}$$, true, 'function_call', 21),
  (116, 'fc_dice_one_pred_three_gt', $${"function": "dice_coefficient", "args": [[1, 0, 0, 0], [1, 1, 1, 0]], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 22),
  (116, 'fc_dice_both_empty', $${"function": "dice_coefficient", "args": [[0, 0, 0], [0, 0, 0]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, true, 'function_call', 23),
  (116, 'fc_dice_one_overlap_in_5', $${"function": "dice_coefficient", "args": [[1, 1, 0, 1, 0], [0, 1, 1, 0, 1]], "kwargs": {}}$$, $${"result": 0.3333333333333333, "tolerance": 1e-06}$$, true, 'function_call', 24),
  (116, 'fc_dice_raises_on_length_mismatch', $${"function": "dice_coefficient", "args": [[1, 0], [1, 0, 1]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 25),
  (116, 'fc_dice_raises_on_non_list', $${"function": "dice_coefficient", "args": ["10", [1, 0]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 26),
  (116, 'fc_pa_perfect', $${"function": "pixel_accuracy", "args": [[1, 0, 1, 1, 0], [1, 0, 1, 1, 0]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 27),
  (116, 'fc_pa_all_wrong', $${"function": "pixel_accuracy", "args": [[1, 1, 1, 1], [0, 0, 0, 0]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 28),
  (116, 'fc_pa_one_quarter', $${"function": "pixel_accuracy", "args": [[1, 1, 1, 1], [1, 0, 0, 0]], "kwargs": {}}$$, $${"result": 0.25, "tolerance": 1e-06}$$, true, 'function_call', 29),
  (116, 'fc_pa_three_of_four', $${"function": "pixel_accuracy", "args": [[1, 1, 0, 1], [1, 1, 1, 1]], "kwargs": {}}$$, $${"result": 0.75, "tolerance": 1e-06}$$, true, 'function_call', 30),
  (116, 'fc_pa_two_of_five', $${"function": "pixel_accuracy", "args": [[1, 1, 1, 1, 1], [1, 0, 0, 0, 1]], "kwargs": {}}$$, $${"result": 0.4, "tolerance": 1e-06}$$, true, 'function_call', 31),
  (116, 'fc_pa_imbalanced_class', $${"function": "pixel_accuracy", "args": [[0, 0, 0, 0, 1], [0, 0, 0, 0, 0]], "kwargs": {}}$$, $${"result": 0.8, "tolerance": 1e-06}$$, true, 'function_call', 32),
  (116, 'fc_pa_raises_on_length_mismatch', $${"function": "pixel_accuracy", "args": [[1, 0], [1]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 33),
  (116, 'fc_pa_raises_on_empty', $${"function": "pixel_accuracy", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 34);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=116 GROUP BY task_id;

COMMIT;