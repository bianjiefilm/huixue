-- CV05 (task_id=110) function_call task_tests — 21 条

BEGIN;

DELETE FROM task_tests WHERE task_id=110;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (110, 'fc_sx_full_kernel', $${"function": "compute_sobel_x_kernel", "args": [], "kwargs": {}}$$, $${"result": [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]]}$$, false, 'function_call', 1),
  (110, 'fc_sy_full_kernel', $${"function": "compute_sobel_y_kernel", "args": [], "kwargs": {}}$$, $${"result": [[-1, -2, -1], [0, 0, 0], [1, 2, 1]]}$$, true, 'function_call', 2),
  (110, 'fc_gm_pythagoras_3_4', $${"function": "compute_gradient_magnitude", "args": [3.0, 4.0], "kwargs": {}}$$, $${"result": 5.0, "tolerance": 1e-06}$$, false, 'function_call', 3),
  (110, 'fc_gm_pythagoras_5_12', $${"function": "compute_gradient_magnitude", "args": [5.0, 12.0], "kwargs": {}}$$, $${"result": 13.0, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (110, 'fc_gm_pythagoras_8_15', $${"function": "compute_gradient_magnitude", "args": [8.0, 15.0], "kwargs": {}}$$, $${"result": 17.0, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (110, 'fc_gm_negative_pythagoras', $${"function": "compute_gradient_magnitude", "args": [-3.0, -4.0], "kwargs": {}}$$, $${"result": 5.0, "tolerance": 1e-06}$$, true, 'function_call', 6),
  (110, 'fc_gm_general_1_2', $${"function": "compute_gradient_magnitude", "args": [1.0, 2.0], "kwargs": {}}$$, $${"result": 2.23606797749979, "tolerance": 1e-06}$$, true, 'function_call', 7),
  (110, 'fc_gm_general_2_3', $${"function": "compute_gradient_magnitude", "args": [2.0, 3.0], "kwargs": {}}$$, $${"result": 3.605551275463989, "tolerance": 1e-06}$$, true, 'function_call', 8),
  (110, 'fc_gm_small_values', $${"function": "compute_gradient_magnitude", "args": [0.0001, 0.0002], "kwargs": {}}$$, $${"result": 0.00022360679774997898, "tolerance": 1e-06}$$, true, 'function_call', 9),
  (110, 'fc_gm_raises_on_string', $${"function": "compute_gradient_magnitude", "args": ["3", 4.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 10),
  (110, 'fc_cc_strong_above_high', $${"function": "canny_threshold_classify", "args": [200.0, 50.0, 150.0], "kwargs": {}}$$, $${"result": "strong"}$$, false, 'function_call', 11),
  (110, 'fc_cc_strong_at_high', $${"function": "canny_threshold_classify", "args": [150.0, 50.0, 150.0], "kwargs": {}}$$, $${"result": "strong"}$$, true, 'function_call', 12),
  (110, 'fc_cc_strong_far_above', $${"function": "canny_threshold_classify", "args": [500.0, 50.0, 150.0], "kwargs": {}}$$, $${"result": "strong"}$$, true, 'function_call', 13),
  (110, 'fc_cc_weak_between', $${"function": "canny_threshold_classify", "args": [100.0, 50.0, 150.0], "kwargs": {}}$$, $${"result": "weak"}$$, true, 'function_call', 14),
  (110, 'fc_cc_weak_at_low', $${"function": "canny_threshold_classify", "args": [50.0, 50.0, 150.0], "kwargs": {}}$$, $${"result": "weak"}$$, true, 'function_call', 15),
  (110, 'fc_cc_non_edge_below_low', $${"function": "canny_threshold_classify", "args": [30.0, 50.0, 150.0], "kwargs": {}}$$, $${"result": "non_edge"}$$, true, 'function_call', 16),
  (110, 'fc_cc_non_edge_zero', $${"function": "canny_threshold_classify", "args": [0.0, 50.0, 150.0], "kwargs": {}}$$, $${"result": "non_edge"}$$, true, 'function_call', 17),
  (110, 'fc_cc_non_edge_just_below_low', $${"function": "canny_threshold_classify", "args": [49.999, 50.0, 150.0], "kwargs": {}}$$, $${"result": "non_edge"}$$, true, 'function_call', 18),
  (110, 'fc_cc_raises_on_low_ge_high', $${"function": "canny_threshold_classify", "args": [100.0, 150.0, 100.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 19),
  (110, 'fc_cc_raises_on_negative_magnitude', $${"function": "canny_threshold_classify", "args": [-10.0, 50.0, 150.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 20),
  (110, 'fc_cc_raises_on_string', $${"function": "canny_threshold_classify", "args": ["100", 50.0, 150.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 21);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=110 GROUP BY task_id;

COMMIT;