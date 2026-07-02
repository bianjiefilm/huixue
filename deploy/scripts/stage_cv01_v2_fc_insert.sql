-- CV01 (task_id=106) function_call task_tests — 31 条

BEGIN;

DELETE FROM task_tests WHERE task_id=106;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (106, 'fc_cls_classification', $${"function": "classify_cv_task", "args": [[224, 224, 3], "label"], "kwargs": {}}$$, $${"result": "classification"}$$, false, 'function_call', 1),
  (106, 'fc_cls_detection', $${"function": "classify_cv_task", "args": [[224, 224, 3], "boxes"], "kwargs": {}}$$, $${"result": "detection"}$$, true, 'function_call', 2),
  (106, 'fc_cls_pixel_annotation', $${"function": "classify_cv_task", "args": [[224, 224, 3], "mask"], "kwargs": {}}$$, $${"result": "pixel_annotation"}$$, true, 'function_call', 3),
  (106, 'fc_cls_recognition', $${"function": "classify_cv_task", "args": [[224, 224, 3], "id"], "kwargs": {}}$$, $${"result": "recognition"}$$, true, 'function_call', 4),
  (106, 'fc_cls_different_size_image', $${"function": "classify_cv_task", "args": [[128, 256, 3], "label"], "kwargs": {}}$$, $${"result": "classification"}$$, true, 'function_call', 5),
  (106, 'fc_cls_raises_on_wrong_shape_length', $${"function": "classify_cv_task", "args": [[224, 224], "label"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (106, 'fc_cls_raises_on_invalid_output_type', $${"function": "classify_cv_task", "args": [[224, 224, 3], "unknown"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (106, 'fc_bytes_uint8_rgb', $${"function": "compute_image_size_bytes", "args": [1920, 1080, 3], "kwargs": {}}$$, $${"result": 6220800}$$, false, 'function_call', 8),
  (106, 'fc_bytes_uint8_grayscale', $${"function": "compute_image_size_bytes", "args": [28, 28, 1], "kwargs": {}}$$, $${"result": 784}$$, true, 'function_call', 9),
  (106, 'fc_bytes_fp32', $${"function": "compute_image_size_bytes", "args": [224, 224, 3, 4], "kwargs": {}}$$, $${"result": 602112}$$, true, 'function_call', 10),
  (106, 'fc_bytes_fp16', $${"function": "compute_image_size_bytes", "args": [512, 512, 3, 2], "kwargs": {}}$$, $${"result": 1572864}$$, true, 'function_call', 11),
  (106, 'fc_bytes_minimal', $${"function": "compute_image_size_bytes", "args": [1, 1, 1], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 12),
  (106, 'fc_bytes_raises_on_zero', $${"function": "compute_image_size_bytes", "args": [0, 1080, 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (106, 'fc_bytes_raises_on_negative', $${"function": "compute_image_size_bytes", "args": [1920, -1, 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (106, 'fc_bytes_raises_on_non_int', $${"function": "compute_image_size_bytes", "args": [1920.0, 1080, 3], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (106, 'fc_rar_landscape', $${"function": "resize_aspect_ratio", "args": [1920, 1080, 224], "kwargs": {}}$$, $${"result": [224, 126]}$$, false, 'function_call', 16),
  (106, 'fc_rar_portrait', $${"function": "resize_aspect_ratio", "args": [1080, 1920, 224], "kwargs": {}}$$, $${"result": [126, 224]}$$, true, 'function_call', 17),
  (106, 'fc_rar_square', $${"function": "resize_aspect_ratio", "args": [500, 500, 300], "kwargs": {}}$$, $${"result": [300, 300]}$$, true, 'function_call', 18),
  (106, 'fc_rar_no_resize_needed', $${"function": "resize_aspect_ratio", "args": [100, 50, 100], "kwargs": {}}$$, $${"result": [100, 50]}$$, true, 'function_call', 19),
  (106, 'fc_rar_2_to_1_ratio', $${"function": "resize_aspect_ratio", "args": [800, 400, 200], "kwargs": {}}$$, $${"result": [200, 100]}$$, true, 'function_call', 20),
  (106, 'fc_rar_raises_on_zero', $${"function": "resize_aspect_ratio", "args": [0, 1080, 224], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (106, 'fc_rar_raises_on_negative_target', $${"function": "resize_aspect_ratio", "args": [1920, 1080, -1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (106, 'fc_rar_raises_on_non_int', $${"function": "resize_aspect_ratio", "args": ["1920", 1080, 224], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23),
  (106, 'fc_npa_basic', $${"function": "normalize_pixel_array", "args": [[0, 127, 255]], "kwargs": {}}$$, $${"result": [0.0, 0.4980392156862745, 1.0], "tolerance": 1e-06}$$, false, 'function_call', 24),
  (106, 'fc_npa_all_zeros', $${"function": "normalize_pixel_array", "args": [[0, 0, 0]], "kwargs": {}}$$, $${"result": [0.0, 0.0, 0.0], "tolerance": 1e-06}$$, true, 'function_call', 25),
  (106, 'fc_npa_all_max', $${"function": "normalize_pixel_array", "args": [[255, 255, 255]], "kwargs": {}}$$, $${"result": [1.0, 1.0, 1.0], "tolerance": 1e-06}$$, true, 'function_call', 26),
  (106, 'fc_npa_custom_max', $${"function": "normalize_pixel_array", "args": [[0, 8, 16]], "kwargs": {"max_value": 16}}$$, $${"result": [0.0, 0.5, 1.0], "tolerance": 1e-06}$$, true, 'function_call', 27),
  (106, 'fc_npa_intermediate', $${"function": "normalize_pixel_array", "args": [[64, 128, 192]], "kwargs": {}}$$, $${"result": [0.25098039215686274, 0.5019607843137255, 0.7529411764705882], "tolerance": 1e-06}$$, true, 'function_call', 28),
  (106, 'fc_npa_raises_on_empty', $${"function": "normalize_pixel_array", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 29),
  (106, 'fc_npa_raises_on_out_of_range', $${"function": "normalize_pixel_array", "args": [[0, 300]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (106, 'fc_npa_raises_on_non_list', $${"function": "normalize_pixel_array", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 31);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=106 GROUP BY task_id;

COMMIT;