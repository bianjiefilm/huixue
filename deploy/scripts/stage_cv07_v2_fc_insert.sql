-- CV07 (task_id=112) function_call task_tests — 29 条

BEGIN;

DELETE FROM task_tests WHERE task_id=112;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (112, 'fc_harris_corner_strong', $${"function": "harris_response_single", "args": [10.0, 10.0, 0.0, 0.04], "kwargs": {}}$$, $${"result": 84.0, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (112, 'fc_harris_flat_region', $${"function": "harris_response_single", "args": [0.0, 0.0, 0.0, 0.04], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (112, 'fc_harris_edge_one_direction', $${"function": "harris_response_single", "args": [100.0, 0.01, 0.0, 0.04], "kwargs": {}}$$, $${"result": -399.08000400000003, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (112, 'fc_harris_with_cross_term', $${"function": "harris_response_single", "args": [5.0, 5.0, 2.0, 0.04], "kwargs": {}}$$, $${"result": 17.0, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (112, 'fc_harris_default_k', $${"function": "harris_response_single", "args": [2.0, 2.0, 0.0], "kwargs": {}}$$, $${"result": 3.36, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (112, 'fc_harris_custom_k', $${"function": "harris_response_single", "args": [2.0, 2.0, 0.0, 0.06], "kwargs": {}}$$, $${"result": 3.04, "tolerance": 1e-06}$$, true, 'function_call', 6),
  (112, 'fc_harris_raises_on_string', $${"function": "harris_response_single", "args": ["10", 10.0, 0.0, 0.04], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (112, 'fc_sift_standard_8x16', $${"function": "sift_block_descriptor_dim", "args": [8, 16], "kwargs": {}}$$, $${"result": 128}$$, false, 'function_call', 8),
  (112, 'fc_sift_smaller_4x16', $${"function": "sift_block_descriptor_dim", "args": [4, 16], "kwargs": {}}$$, $${"result": 64}$$, true, 'function_call', 9),
  (112, 'fc_sift_8x8', $${"function": "sift_block_descriptor_dim", "args": [8, 8], "kwargs": {}}$$, $${"result": 64}$$, true, 'function_call', 10),
  (112, 'fc_sift_larger_16x16', $${"function": "sift_block_descriptor_dim", "args": [16, 16], "kwargs": {}}$$, $${"result": 256}$$, true, 'function_call', 11),
  (112, 'fc_sift_minimum', $${"function": "sift_block_descriptor_dim", "args": [1, 1], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 12),
  (112, 'fc_sift_raises_on_zero', $${"function": "sift_block_descriptor_dim", "args": [0, 16], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (112, 'fc_sift_raises_on_negative', $${"function": "sift_block_descriptor_dim", "args": [8, -1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (112, 'fc_sift_raises_on_non_int', $${"function": "sift_block_descriptor_dim", "args": [8.0, 16], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (112, 'fc_extrema_max', $${"function": "extrema_check_3x3", "args": [[[1, 2, 3], [4, 10, 5], [6, 7, 8]]], "kwargs": {}}$$, $${"result": "max"}$$, false, 'function_call', 16),
  (112, 'fc_extrema_min', $${"function": "extrema_check_3x3", "args": [[[1, 2, 3], [4, -1, 5], [6, 7, 8]]], "kwargs": {}}$$, $${"result": "min"}$$, true, 'function_call', 17),
  (112, 'fc_extrema_neither_tied_max', $${"function": "extrema_check_3x3", "args": [[[1, 2, 3], [4, 5, 5], [6, 7, 8]]], "kwargs": {}}$$, $${"result": "neither"}$$, true, 'function_call', 18),
  (112, 'fc_extrema_neither_tied_min', $${"function": "extrema_check_3x3", "args": [[[1, 1, 3], [4, 1, 5], [6, 7, 8]]], "kwargs": {}}$$, $${"result": "neither"}$$, true, 'function_call', 19),
  (112, 'fc_extrema_neither_middle', $${"function": "extrema_check_3x3", "args": [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]], "kwargs": {}}$$, $${"result": "neither"}$$, true, 'function_call', 20),
  (112, 'fc_extrema_max_negative', $${"function": "extrema_check_3x3", "args": [[[-2, -3, -4], [-5, -1, -6], [-7, -8, -9]]], "kwargs": {}}$$, $${"result": "max"}$$, true, 'function_call', 21),
  (112, 'fc_extrema_raises_on_wrong_shape', $${"function": "extrema_check_3x3", "args": [[[1, 2], [3, 4]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (112, 'fc_extrema_raises_on_non_list', $${"function": "extrema_check_3x3", "args": ["not a list"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23),
  (112, 'fc_hessian_with_offdiag_symmetric', $${"function": "hessian_2x2_eigenvalues", "args": [2.0, 1.0, 2.0], "kwargs": {}}$$, $${"result": [3.0, 1.0], "tolerance": 1e-06}$$, false, 'function_call', 24),
  (112, 'fc_hessian_with_offdiag_general', $${"function": "hessian_2x2_eigenvalues", "args": [4.0, 2.0, 1.0], "kwargs": {}}$$, $${"result": [5.0, 0.0], "tolerance": 1e-06}$$, true, 'function_call', 25),
  (112, 'fc_hessian_offdiag_3', $${"function": "hessian_2x2_eigenvalues", "args": [5.0, 2.0, 2.0], "kwargs": {}}$$, $${"result": [6.0, 1.0], "tolerance": 1e-06}$$, true, 'function_call', 26),
  (112, 'fc_hessian_ordering', $${"function": "hessian_2x2_eigenvalues", "args": [1.0, 2.0, 4.0], "kwargs": {}}$$, $${"result": [5.0, 0.0], "tolerance": 1e-06}$$, true, 'function_call', 27),
  (112, 'fc_hessian_negative_eigenvalues', $${"function": "hessian_2x2_eigenvalues", "args": [-1.0, 2.0, -4.0], "kwargs": {}}$$, $${"result": [0.0, -5.0], "tolerance": 1e-06}$$, true, 'function_call', 28),
  (112, 'fc_hessian_raises_on_string', $${"function": "hessian_2x2_eigenvalues", "args": ["1", 0.0, 1.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 29);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=112 GROUP BY task_id;

COMMIT;