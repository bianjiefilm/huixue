-- CV10 (task_id=115) function_call task_tests — 33 条

BEGIN;

DELETE FROM task_tests WHERE task_id=115;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (115, 'fc_bbox_area_unit', $${"function": "bbox_area", "args": [[0.0, 0.0, 1.0, 1.0]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (115, 'fc_bbox_area_2x3', $${"function": "bbox_area", "args": [[0.0, 0.0, 2.0, 3.0]], "kwargs": {}}$$, $${"result": 6.0, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (115, 'fc_bbox_area_offset', $${"function": "bbox_area", "args": [[10.0, 20.0, 30.0, 50.0]], "kwargs": {}}$$, $${"result": 600.0, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (115, 'fc_bbox_area_small', $${"function": "bbox_area", "args": [[0.0, 0.0, 0.5, 0.5]], "kwargs": {}}$$, $${"result": 0.25, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (115, 'fc_bbox_area_negative_corner', $${"function": "bbox_area", "args": [[-1.0, -2.0, 3.0, 4.0]], "kwargs": {}}$$, $${"result": 24.0, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (115, 'fc_bbox_area_minimal', $${"function": "bbox_area", "args": [[0.0, 0.0, 0.001, 0.001]], "kwargs": {}}$$, $${"result": 1e-06, "tolerance": 1e-09}$$, true, 'function_call', 6),
  (115, 'fc_bbox_area_raises_on_x1_ge_x2', $${"function": "bbox_area", "args": [[3.0, 0.0, 1.0, 1.0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (115, 'fc_bbox_area_raises_on_wrong_length', $${"function": "bbox_area", "args": [[1.0, 2.0, 3.0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 8),
  (115, 'fc_bbox_area_raises_on_non_list', $${"function": "bbox_area", "args": ["0,0,1,1"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 9),
  (115, 'fc_iou_b_contained_in_a_2', $${"function": "compute_iou", "args": [[0.0, 0.0, 4.0, 4.0], [0.0, 0.0, 2.0, 2.0]], "kwargs": {}}$$, $${"result": 0.25, "tolerance": 1e-06}$$, false, 'function_call', 10),
  (115, 'fc_iou_no_overlap', $${"function": "compute_iou", "args": [[0.0, 0.0, 1.0, 1.0], [10.0, 10.0, 11.0, 11.0]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 11),
  (115, 'fc_iou_half_overlap_x', $${"function": "compute_iou", "args": [[0.0, 0.0, 2.0, 2.0], [1.0, 0.0, 3.0, 2.0]], "kwargs": {}}$$, $${"result": 0.3333333333333333, "tolerance": 1e-06}$$, true, 'function_call', 12),
  (115, 'fc_iou_quarter_overlap', $${"function": "compute_iou", "args": [[0.0, 0.0, 2.0, 2.0], [1.0, 1.0, 3.0, 3.0]], "kwargs": {}}$$, $${"result": 0.14285714285714285, "tolerance": 1e-06}$$, true, 'function_call', 13),
  (115, 'fc_iou_b_contained_in_a', $${"function": "compute_iou", "args": [[0.0, 0.0, 4.0, 4.0], [1.0, 1.0, 2.0, 2.0]], "kwargs": {}}$$, $${"result": 0.0625, "tolerance": 1e-06}$$, true, 'function_call', 14),
  (115, 'fc_iou_touching_edge', $${"function": "compute_iou", "args": [[0.0, 0.0, 1.0, 1.0], [1.0, 0.0, 2.0, 1.0]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 15),
  (115, 'fc_iou_raises_on_wrong_box_length', $${"function": "compute_iou", "args": [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0, 1.0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 16),
  (115, 'fc_iou_raises_on_non_list', $${"function": "compute_iou", "args": ["0,0,1,1", [0.0, 0.0, 1.0, 1.0]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 17),
  (115, 'fc_filter_simple', $${"function": "confidence_threshold_filter", "args": [[0.1, 0.6, 0.3, 0.8], 0.5], "kwargs": {}}$$, $${"result": [1, 3]}$$, false, 'function_call', 18),
  (115, 'fc_filter_at_threshold_partial', $${"function": "confidence_threshold_filter", "args": [[0.4, 0.5, 0.6], 0.5], "kwargs": {}}$$, $${"result": [1, 2]}$$, true, 'function_call', 19),
  (115, 'fc_filter_first_only', $${"function": "confidence_threshold_filter", "args": [[0.9, 0.2, 0.1], 0.5], "kwargs": {}}$$, $${"result": [0]}$$, true, 'function_call', 20),
  (115, 'fc_filter_all_below', $${"function": "confidence_threshold_filter", "args": [[0.3, 0.5, 0.7], 0.99], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 21),
  (115, 'fc_filter_just_one', $${"function": "confidence_threshold_filter", "args": [[0.1, 0.2, 0.9], 0.5], "kwargs": {}}$$, $${"result": [2]}$$, true, 'function_call', 22),
  (115, 'fc_filter_two_kept', $${"function": "confidence_threshold_filter", "args": [[0.6, 0.3, 0.7], 0.5], "kwargs": {}}$$, $${"result": [0, 2]}$$, true, 'function_call', 23),
  (115, 'fc_filter_raises_on_empty', $${"function": "confidence_threshold_filter", "args": [[], 0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 24),
  (115, 'fc_filter_raises_on_non_list', $${"function": "confidence_threshold_filter", "args": ["0.5,0.6", 0.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 25),
  (115, 'fc_nms_full_overlap_kill_lower', $${"function": "nms_2d", "args": [[[0.0, 0.0, 2.0, 2.0], [0.0, 0.0, 2.0, 2.0]], [0.5, 0.9], 0.5], "kwargs": {}}$$, $${"result": [1]}$$, false, 'function_call', 26),
  (115, 'fc_nms_two_separate_kill', $${"function": "nms_2d", "args": [[[0.0, 0.0, 2.0, 2.0], [0.05, 0.05, 2.05, 2.05], [10.0, 10.0, 12.0, 12.0], [10.05, 10.05, 12.05, 12.05]], [0.9, 0.5, 0.7, 0.6], 0.5], "kwargs": {}}$$, $${"result": [0, 2]}$$, true, 'function_call', 27),
  (115, 'fc_nms_high_iou_kill', $${"function": "nms_2d", "args": [[[0.0, 0.0, 2.0, 2.0], [0.1, 0.1, 2.1, 2.1], [10.0, 10.0, 12.0, 12.0]], [0.9, 0.85, 0.7], 0.5], "kwargs": {}}$$, $${"result": [0, 2]}$$, true, 'function_call', 28),
  (115, 'fc_nms_single_box', $${"function": "nms_2d", "args": [[[0.0, 0.0, 1.0, 1.0]], [0.5], 0.5], "kwargs": {}}$$, $${"result": [0]}$$, true, 'function_call', 29),
  (115, 'fc_nms_strict_threshold', $${"function": "nms_2d", "args": [[[0.0, 0.0, 2.0, 2.0], [0.5, 0.5, 2.5, 2.5], [10.0, 10.0, 12.0, 12.0]], [0.9, 0.8, 0.7], 0.3], "kwargs": {}}$$, $${"result": [0, 2]}$$, true, 'function_call', 30),
  (115, 'fc_nms_raises_on_length_mismatch', $${"function": "nms_2d", "args": [[[0.0, 0.0, 1.0, 1.0]], [0.5, 0.6], 0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (115, 'fc_nms_raises_on_invalid_threshold', $${"function": "nms_2d", "args": [[[0.0, 0.0, 1.0, 1.0]], [0.5], 2.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 32),
  (115, 'fc_nms_raises_on_non_list', $${"function": "nms_2d", "args": ["not a list", [0.5], 0.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 33);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=115 GROUP BY task_id;

COMMIT;