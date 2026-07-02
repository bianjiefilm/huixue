-- NN09 (task_id=102) function_call task_tests — 32 条

BEGIN;

DELETE FROM task_tests WHERE task_id=102;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (102, 'fc_c1d_textbook', $${"function": "conv1d_single_step", "args": [[1, 2, 3], [0.5, -0.3, 0.1], 0.2], "kwargs": {}}$$, $${"result": 0.4000000000000001, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (102, 'fc_c1d_only_bias', $${"function": "conv1d_single_step", "args": [[0, 0, 0], [1, 2, 3], 5.0], "kwargs": {}}$$, $${"result": 5.0, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (102, 'fc_c1d_unit_kernel', $${"function": "conv1d_single_step", "args": [[2, 3, 4], [1, 1, 1], 0], "kwargs": {}}$$, $${"result": 9.0, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (102, 'fc_c1d_negative', $${"function": "conv1d_single_step", "args": [[1, 2, 3], [-1, -1, -1], 0], "kwargs": {}}$$, $${"result": -6.0, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (102, 'fc_c1d_single_element', $${"function": "conv1d_single_step", "args": [[5], [2], 1.0], "kwargs": {}}$$, $${"result": 11.0, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (102, 'fc_c1d_raises_on_length_mismatch', $${"function": "conv1d_single_step", "args": [[1, 2], [1], 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (102, 'fc_c1d_raises_on_empty', $${"function": "conv1d_single_step", "args": [[], [], 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (102, 'fc_c1d_raises_on_non_list', $${"function": "conv1d_single_step", "args": ["ab", [1, 2], 0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (102, 'fc_cos_basic', $${"function": "compute_output_shape", "args": [10, 3, 0, 1], "kwargs": {}}$$, $${"result": 8}$$, false, 'function_call', 9),
  (102, 'fc_cos_same_padding', $${"function": "compute_output_shape", "args": [10, 3, 1, 1], "kwargs": {}}$$, $${"result": 10}$$, true, 'function_call', 10),
  (102, 'fc_cos_stride_2', $${"function": "compute_output_shape", "args": [10, 3, 0, 2], "kwargs": {}}$$, $${"result": 4}$$, true, 'function_call', 11),
  (102, 'fc_cos_large_input', $${"function": "compute_output_shape", "args": [224, 7, 3, 2], "kwargs": {}}$$, $${"result": 112}$$, true, 'function_call', 12),
  (102, 'fc_cos_K_equals_N', $${"function": "compute_output_shape", "args": [5, 5, 0, 1], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 13),
  (102, 'fc_cos_raises_on_invalid', $${"function": "compute_output_shape", "args": [3, 5, 0, 1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (102, 'fc_cos_raises_on_zero_stride', $${"function": "compute_output_shape", "args": [10, 3, 0, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (102, 'fc_cos_raises_on_non_int', $${"function": "compute_output_shape", "args": [10.5, 3, 0, 1], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (102, 'fc_mp_simple_2x2', $${"function": "max_pool_2x2", "args": [[[1, 2], [3, 4]]], "kwargs": {}}$$, $${"result": [[4]]}$$, false, 'function_call', 17),
  (102, 'fc_mp_4x4', $${"function": "max_pool_2x2", "args": [[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]], "kwargs": {}}$$, $${"result": [[6, 8], [14, 16]]}$$, true, 'function_call', 18),
  (102, 'fc_mp_negative_values', $${"function": "max_pool_2x2", "args": [[[-1, -2], [-3, -4]]], "kwargs": {}}$$, $${"result": [[-1]]}$$, true, 'function_call', 19),
  (102, 'fc_mp_2x4', $${"function": "max_pool_2x2", "args": [[[1, 2, 3, 4], [5, 6, 7, 8]]], "kwargs": {}}$$, $${"result": [[6, 8]]}$$, true, 'function_call', 20),
  (102, 'fc_mp_4x2', $${"function": "max_pool_2x2", "args": [[[1, 2], [3, 4], [5, 6], [7, 8]]], "kwargs": {}}$$, $${"result": [[4], [8]]}$$, true, 'function_call', 21),
  (102, 'fc_mp_raises_on_odd_size', $${"function": "max_pool_2x2", "args": [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (102, 'fc_mp_raises_on_empty', $${"function": "max_pool_2x2", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (102, 'fc_mp_raises_on_non_list', $${"function": "max_pool_2x2", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24),
  (102, 'fc_ccp_basic', $${"function": "count_conv_params", "args": [64, 128, 3], "kwargs": {}}$$, $${"result": 73856}$$, false, 'function_call', 25),
  (102, 'fc_ccp_first_conv', $${"function": "count_conv_params", "args": [3, 32, 3], "kwargs": {}}$$, $${"result": 896}$$, true, 'function_call', 26),
  (102, 'fc_ccp_5x5_kernel', $${"function": "count_conv_params", "args": [3, 16, 5], "kwargs": {}}$$, $${"result": 1216}$$, true, 'function_call', 27),
  (102, 'fc_ccp_1x1_kernel', $${"function": "count_conv_params", "args": [64, 32, 1], "kwargs": {}}$$, $${"result": 2080}$$, true, 'function_call', 28),
  (102, 'fc_ccp_large_layer', $${"function": "count_conv_params", "args": [256, 512, 3], "kwargs": {}}$$, $${"result": 1180160}$$, true, 'function_call', 29),
  (102, 'fc_ccp_raises_on_zero', $${"function": "count_conv_params", "args": [0, 32, 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (102, 'fc_ccp_raises_on_negative', $${"function": "count_conv_params", "args": [3, -1, 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (102, 'fc_ccp_raises_on_non_int', $${"function": "count_conv_params", "args": [3.5, 32, 3], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 32);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=102 GROUP BY task_id;

COMMIT;