-- CV06 (task_id=111) function_call task_tests — 26 条

BEGIN;

DELETE FROM task_tests WHERE task_id=111;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (111, 'fc_erode_1d_one_zero_left', $${"function": "erode_1d", "args": [[0, 1, 1, 1, 1], 3], "kwargs": {}}$$, $${"result": [0, 1, 1]}$$, false, 'function_call', 1),
  (111, 'fc_erode_1d_one_zero_right', $${"function": "erode_1d", "args": [[1, 1, 1, 1, 0], 3], "kwargs": {}}$$, $${"result": [1, 1, 0]}$$, true, 'function_call', 2),
  (111, 'fc_erode_1d_long_mixed', $${"function": "erode_1d", "args": [[1, 1, 1, 0, 1, 1, 1], 3], "kwargs": {}}$$, $${"result": [1, 0, 0, 0, 1]}$$, true, 'function_call', 3),
  (111, 'fc_erode_1d_partial_5', $${"function": "erode_1d", "args": [[1, 1, 1, 1, 0, 1], 3], "kwargs": {}}$$, $${"result": [1, 1, 0, 0]}$$, true, 'function_call', 4),
  (111, 'fc_erode_1d_all_zeros', $${"function": "erode_1d", "args": [[0, 0, 0, 0, 0], 3], "kwargs": {}}$$, $${"result": [0, 0, 0]}$$, true, 'function_call', 5),
  (111, 'fc_erode_1d_kernel_5_mixed', $${"function": "erode_1d", "args": [[1, 0, 1, 1, 1, 1, 1], 5], "kwargs": {}}$$, $${"result": [0, 0, 1]}$$, true, 'function_call', 6),
  (111, 'fc_erode_1d_raises_on_even_kernel', $${"function": "erode_1d", "args": [[1, 1, 1, 1], 2], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (111, 'fc_erode_1d_raises_on_invalid_value', $${"function": "erode_1d", "args": [[1, 2, 1, 1], 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 8),
  (111, 'fc_erode_1d_raises_on_non_list', $${"function": "erode_1d", "args": ["11011", 3], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 9),
  (111, 'fc_dilate_1d_one_one_left', $${"function": "dilate_1d", "args": [[1, 0, 0, 0, 0], 3], "kwargs": {}}$$, $${"result": [1, 0, 0]}$$, false, 'function_call', 10),
  (111, 'fc_dilate_1d_one_one_right', $${"function": "dilate_1d", "args": [[0, 0, 0, 0, 1], 3], "kwargs": {}}$$, $${"result": [0, 0, 1]}$$, true, 'function_call', 11),
  (111, 'fc_dilate_1d_long_sparse', $${"function": "dilate_1d", "args": [[0, 0, 0, 1, 0, 0, 0], 3], "kwargs": {}}$$, $${"result": [0, 1, 1, 1, 0]}$$, true, 'function_call', 12),
  (111, 'fc_dilate_1d_partial_5', $${"function": "dilate_1d", "args": [[0, 0, 1, 0, 0, 1], 3], "kwargs": {}}$$, $${"result": [1, 1, 1, 1]}$$, true, 'function_call', 13),
  (111, 'fc_dilate_1d_all_zeros', $${"function": "dilate_1d", "args": [[0, 0, 0, 0, 0], 3], "kwargs": {}}$$, $${"result": [0, 0, 0]}$$, true, 'function_call', 14),
  (111, 'fc_dilate_1d_kernel_5_mixed', $${"function": "dilate_1d", "args": [[0, 0, 1, 0, 0, 0, 1], 5], "kwargs": {}}$$, $${"result": [1, 1, 1]}$$, true, 'function_call', 15),
  (111, 'fc_dilate_1d_raises_on_even_kernel', $${"function": "dilate_1d", "args": [[1, 1, 1, 1], 2], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 16),
  (111, 'fc_dilate_1d_raises_on_invalid_value', $${"function": "dilate_1d", "args": [[0, 0, 3, 0, 0], 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 17),
  (111, 'fc_dilate_1d_raises_on_non_list', $${"function": "dilate_1d", "args": [123, 3], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 18),
  (111, 'fc_order_erosion', $${"function": "get_morph_operation_order", "args": ["erosion"], "kwargs": {}}$$, $${"result": "erosion"}$$, false, 'function_call', 19),
  (111, 'fc_order_dilation', $${"function": "get_morph_operation_order", "args": ["dilation"], "kwargs": {}}$$, $${"result": "dilation"}$$, true, 'function_call', 20),
  (111, 'fc_order_opening', $${"function": "get_morph_operation_order", "args": ["opening"], "kwargs": {}}$$, $${"result": "erosion_then_dilation"}$$, true, 'function_call', 21),
  (111, 'fc_order_closing', $${"function": "get_morph_operation_order", "args": ["closing"], "kwargs": {}}$$, $${"result": "dilation_then_erosion"}$$, true, 'function_call', 22),
  (111, 'fc_order_raises_on_unknown', $${"function": "get_morph_operation_order", "args": ["invalid_op"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (111, 'fc_order_raises_on_empty', $${"function": "get_morph_operation_order", "args": [""], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 24),
  (111, 'fc_order_raises_on_non_string', $${"function": "get_morph_operation_order", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 25),
  (111, 'fc_cross_full_match', $${"function": "get_cross_se_3x3", "args": [], "kwargs": {}}$$, $${"result": [[0, 1, 0], [1, 1, 1], [0, 1, 0]]}$$, false, 'function_call', 26);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=111 GROUP BY task_id;

COMMIT;