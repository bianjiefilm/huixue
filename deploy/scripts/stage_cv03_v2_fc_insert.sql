-- CV03 (task_id=108) function_call task_tests — 28 条

BEGIN;

DELETE FROM task_tests WHERE task_id=108;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (108, 'fc_t_basic', $${"function": "translate_point", "args": [1, 2, 3, 4], "kwargs": {}}$$, $${"result": [4, 6]}$$, false, 'function_call', 1),
  (108, 'fc_t_zero', $${"function": "translate_point", "args": [5, 5, 0, 0], "kwargs": {}}$$, $${"result": [5, 5]}$$, true, 'function_call', 2),
  (108, 'fc_t_negative', $${"function": "translate_point", "args": [10, 10, -5, -3], "kwargs": {}}$$, $${"result": [5, 7]}$$, true, 'function_call', 3),
  (108, 'fc_t_floats', $${"function": "translate_point", "args": [1.5, 2.5, 0.5, 1.0], "kwargs": {}}$$, $${"result": [2.0, 3.5], "tolerance": 1e-06}$$, true, 'function_call', 4),
  (108, 'fc_t_origin', $${"function": "translate_point", "args": [0, 0, 5, 7], "kwargs": {}}$$, $${"result": [5, 7]}$$, true, 'function_call', 5),
  (108, 'fc_t_raises_on_non_numeric', $${"function": "translate_point", "args": ["1", 2, 3, 4], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (108, 'fc_r_zero_angle', $${"function": "rotate_point", "args": [3, 4, 0], "kwargs": {}}$$, $${"result": [3.0, 4.0], "tolerance": 1e-06}$$, false, 'function_call', 7),
  (108, 'fc_r_90_around_origin', $${"function": "rotate_point", "args": [1, 0, 90], "kwargs": {}}$$, $${"result": [0.0, -1.0], "tolerance": 1e-06}$$, true, 'function_call', 8),
  (108, 'fc_r_180_around_origin', $${"function": "rotate_point", "args": [3, 4, 180], "kwargs": {}}$$, $${"result": [-3.0, -4.0], "tolerance": 1e-06}$$, true, 'function_call', 9),
  (108, 'fc_r_around_custom_center', $${"function": "rotate_point", "args": [2, 0, 180], "kwargs": {"cx": 1, "cy": 0}}$$, $${"result": [0.0, 0.0], "tolerance": 1e-06}$$, true, 'function_call', 10),
  (108, 'fc_r_360_returns', $${"function": "rotate_point", "args": [3, 4, 360], "kwargs": {}}$$, $${"result": [3.0, 4.0], "tolerance": 1e-09}$$, true, 'function_call', 11),
  (108, 'fc_r_raises_on_non_numeric', $${"function": "rotate_point", "args": ["1", 0, 90], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 12),
  (108, 'fc_sd_basic', $${"function": "scale_dimensions", "args": [100, 50, 2.0, 3.0], "kwargs": {}}$$, $${"result": [200, 150]}$$, false, 'function_call', 13),
  (108, 'fc_sd_half', $${"function": "scale_dimensions", "args": [1920, 1080, 0.5, 0.5], "kwargs": {}}$$, $${"result": [960, 540]}$$, true, 'function_call', 14),
  (108, 'fc_sd_anisotropic', $${"function": "scale_dimensions", "args": [100, 100, 2.0, 0.5], "kwargs": {}}$$, $${"result": [200, 50]}$$, true, 'function_call', 15),
  (108, 'fc_sd_floor', $${"function": "scale_dimensions", "args": [101, 201, 0.5, 0.5], "kwargs": {}}$$, $${"result": [50, 100]}$$, true, 'function_call', 16),
  (108, 'fc_sd_no_change', $${"function": "scale_dimensions", "args": [224, 224, 1.0, 1.0], "kwargs": {}}$$, $${"result": [224, 224]}$$, true, 'function_call', 17),
  (108, 'fc_sd_raises_on_zero', $${"function": "scale_dimensions", "args": [0, 100, 1.0, 1.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (108, 'fc_sd_raises_on_negative_factor', $${"function": "scale_dimensions", "args": [100, 100, -1.0, 1.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 19),
  (108, 'fc_sd_raises_on_non_int', $${"function": "scale_dimensions", "args": [100.5, 100, 1.0, 1.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 20),
  (108, 'fc_aff_identity', $${"function": "apply_affine_transform", "args": [3, 4, [[1, 0, 0], [0, 1, 0]]], "kwargs": {}}$$, $${"result": [3.0, 4.0], "tolerance": 1e-06}$$, false, 'function_call', 21),
  (108, 'fc_aff_translation', $${"function": "apply_affine_transform", "args": [3, 4, [[1, 0, 5], [0, 1, 7]]], "kwargs": {}}$$, $${"result": [8.0, 11.0], "tolerance": 1e-06}$$, true, 'function_call', 22),
  (108, 'fc_aff_scale', $${"function": "apply_affine_transform", "args": [3, 4, [[2, 0, 0], [0, 3, 0]]], "kwargs": {}}$$, $${"result": [6.0, 12.0], "tolerance": 1e-06}$$, true, 'function_call', 23),
  (108, 'fc_aff_rotation_90', $${"function": "apply_affine_transform", "args": [1, 0, [[0, 1, 0], [-1, 0, 0]]], "kwargs": {}}$$, $${"result": [0.0, -1.0], "tolerance": 1e-06}$$, true, 'function_call', 24),
  (108, 'fc_aff_complex', $${"function": "apply_affine_transform", "args": [1, 1, [[2, 0, 1], [0, 3, 2]]], "kwargs": {}}$$, $${"result": [3.0, 5.0], "tolerance": 1e-06}$$, true, 'function_call', 25),
  (108, 'fc_aff_raises_on_wrong_shape', $${"function": "apply_affine_transform", "args": [1, 1, [[1, 0]]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 26),
  (108, 'fc_aff_raises_on_non_list', $${"function": "apply_affine_transform", "args": [1, 1, "abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 27),
  (108, 'fc_aff_negative_input', $${"function": "apply_affine_transform", "args": [-2, -3, [[2, 0, 0], [0, 2, 0]]], "kwargs": {}}$$, $${"result": [-4.0, -6.0], "tolerance": 1e-06}$$, true, 'function_call', 28);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=108 GROUP BY task_id;

COMMIT;