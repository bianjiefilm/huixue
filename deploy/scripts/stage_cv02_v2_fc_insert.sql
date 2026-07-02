-- CV02 (task_id=107) function_call task_tests — 26 条

BEGIN;

DELETE FROM task_tests WHERE task_id=107;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (107, 'fc_g_pure_red', $${"function": "rgb_to_grayscale", "args": [[255, 0, 0]], "kwargs": {}}$$, $${"result": 76.245, "tolerance": 0.0001}$$, false, 'function_call', 1),
  (107, 'fc_g_pure_green', $${"function": "rgb_to_grayscale", "args": [[0, 255, 0]], "kwargs": {}}$$, $${"result": 149.685, "tolerance": 0.0001}$$, true, 'function_call', 2),
  (107, 'fc_g_pure_blue', $${"function": "rgb_to_grayscale", "args": [[0, 0, 255]], "kwargs": {}}$$, $${"result": 29.07, "tolerance": 0.0001}$$, true, 'function_call', 3),
  (107, 'fc_g_white', $${"function": "rgb_to_grayscale", "args": [[255, 255, 255]], "kwargs": {}}$$, $${"result": 255.0, "tolerance": 0.0001}$$, true, 'function_call', 4),
  (107, 'fc_g_black', $${"function": "rgb_to_grayscale", "args": [[0, 0, 0]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 0.0001}$$, true, 'function_call', 5),
  (107, 'fc_g_raises_on_wrong_length', $${"function": "rgb_to_grayscale", "args": [[255, 0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (107, 'fc_g_raises_on_out_of_range', $${"function": "rgb_to_grayscale", "args": [[300, 0, 0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (107, 'fc_hsv_pure_red', $${"function": "rgb_to_hsv", "args": [[1.0, 0.0, 0.0]], "kwargs": {}}$$, $${"result": [0.0, 1.0, 1.0], "tolerance": 0.0001}$$, false, 'function_call', 8),
  (107, 'fc_hsv_pure_green', $${"function": "rgb_to_hsv", "args": [[0.0, 1.0, 0.0]], "kwargs": {}}$$, $${"result": [120.0, 1.0, 1.0], "tolerance": 0.0001}$$, true, 'function_call', 9),
  (107, 'fc_hsv_pure_blue', $${"function": "rgb_to_hsv", "args": [[0.0, 0.0, 1.0]], "kwargs": {}}$$, $${"result": [240.0, 1.0, 1.0], "tolerance": 0.0001}$$, true, 'function_call', 10),
  (107, 'fc_hsv_white', $${"function": "rgb_to_hsv", "args": [[1.0, 1.0, 1.0]], "kwargs": {}}$$, $${"result": [0.0, 0.0, 1.0], "tolerance": 0.0001}$$, true, 'function_call', 11),
  (107, 'fc_hsv_black', $${"function": "rgb_to_hsv", "args": [[0.0, 0.0, 0.0]], "kwargs": {}}$$, $${"result": [0.0, 0.0, 0.0], "tolerance": 0.0001}$$, true, 'function_call', 12),
  (107, 'fc_hsv_raises_on_wrong_length', $${"function": "rgb_to_hsv", "args": [[1.0, 0.5]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (107, 'fc_hsv_raises_on_out_of_range', $${"function": "rgb_to_hsv", "args": [[1.5, 0.5, 0.5]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (107, 'fc_thresh_basic', $${"function": "apply_threshold", "args": [[100, 150, 200], 128], "kwargs": {}}$$, $${"result": [0, 255, 255]}$$, false, 'function_call', 15),
  (107, 'fc_thresh_at_boundary', $${"function": "apply_threshold", "args": [[127, 128, 129], 128], "kwargs": {}}$$, $${"result": [0, 0, 255]}$$, true, 'function_call', 16),
  (107, 'fc_thresh_low_threshold', $${"function": "apply_threshold", "args": [[5, 50, 100, 200], 10], "kwargs": {}}$$, $${"result": [0, 255, 255, 255]}$$, true, 'function_call', 17),
  (107, 'fc_thresh_high_threshold', $${"function": "apply_threshold", "args": [[100, 200, 250], 240], "kwargs": {}}$$, $${"result": [0, 0, 255]}$$, true, 'function_call', 18),
  (107, 'fc_thresh_default_128', $${"function": "apply_threshold", "args": [[50, 200]], "kwargs": {}}$$, $${"result": [0, 255]}$$, true, 'function_call', 19),
  (107, 'fc_thresh_raises_on_empty', $${"function": "apply_threshold", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 20),
  (107, 'fc_thresh_raises_on_invalid_threshold', $${"function": "apply_threshold", "args": [[100], 300], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (107, 'fc_thresh_raises_on_non_list', $${"function": "apply_threshold", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 22),
  (107, 'fc_hist_extremes', $${"function": "compute_histogram", "args": [[0, 0, 255, 255]], "kwargs": {"n_bins": 2, "max_value": 255}}$$, $${"result": [2, 2]}$$, false, 'function_call', 23),
  (107, 'fc_hist_raises_on_empty', $${"function": "compute_histogram", "args": [[]], "kwargs": {"n_bins": 5}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 24),
  (107, 'fc_hist_raises_on_zero_bins', $${"function": "compute_histogram", "args": [[100]], "kwargs": {"n_bins": 0}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 25),
  (107, 'fc_hist_raises_on_non_list', $${"function": "compute_histogram", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 26);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=107 GROUP BY task_id;

COMMIT;