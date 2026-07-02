-- NN01 (task_id=94) function_call task_tests — 33 条

BEGIN;

DELETE FROM task_tests WHERE task_id=94;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (94, 'fc_dp_two_layers', $${"function": "count_dense_parameters", "args": [[3, 4]], "kwargs": {}}$$, $${"result": 16}$$, false, 'function_call', 1),
  (94, 'fc_dp_three_layers', $${"function": "count_dense_parameters", "args": [[3, 4, 2]], "kwargs": {}}$$, $${"result": 26}$$, true, 'function_call', 2),
  (94, 'fc_dp_typical_mnist', $${"function": "count_dense_parameters", "args": [[784, 128, 10]], "kwargs": {}}$$, $${"result": 101770}$$, true, 'function_call', 3),
  (94, 'fc_dp_minimal', $${"function": "count_dense_parameters", "args": [[1, 1]], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 4),
  (94, 'fc_dp_four_layers', $${"function": "count_dense_parameters", "args": [[100, 50, 25, 10]], "kwargs": {}}$$, $${"result": 6585}$$, true, 'function_call', 5),
  (94, 'fc_dp_single_layer', $${"function": "count_dense_parameters", "args": [[5]], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 6),
  (94, 'fc_dp_raises_on_empty', $${"function": "count_dense_parameters", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (94, 'fc_dp_raises_on_non_list', $${"function": "count_dense_parameters", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (94, 'fc_cim_tabular', $${"function": "classify_input_modality", "args": [[1000]], "kwargs": {}}$$, $${"result": "tabular"}$$, false, 'function_call', 9),
  (94, 'fc_cim_sequence', $${"function": "classify_input_modality", "args": [[50, 64]], "kwargs": {}}$$, $${"result": "sequence"}$$, true, 'function_call', 10),
  (94, 'fc_cim_image', $${"function": "classify_input_modality", "args": [[224, 224, 3]], "kwargs": {}}$$, $${"result": "image"}$$, true, 'function_call', 11),
  (94, 'fc_cim_video', $${"function": "classify_input_modality", "args": [[16, 224, 224, 3]], "kwargs": {}}$$, $${"result": "video"}$$, true, 'function_call', 12),
  (94, 'fc_cim_short_tabular', $${"function": "classify_input_modality", "args": [[5]], "kwargs": {}}$$, $${"result": "tabular"}$$, true, 'function_call', 13),
  (94, 'fc_cim_long_video', $${"function": "classify_input_modality", "args": [[32, 96, 128, 3]], "kwargs": {}}$$, $${"result": "video"}$$, true, 'function_call', 14),
  (94, 'fc_cim_raises_on_empty_tuple', $${"function": "classify_input_modality", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (94, 'fc_cim_raises_on_5d', $${"function": "classify_input_modality", "args": [[10, 16, 224, 224, 3]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 16),
  (94, 'fc_cdss_70_15_15', $${"function": "compute_data_split_sizes", "args": [100, [0.7, 0.15, 0.15]], "kwargs": {}}$$, $${"result": [70, 15, 15]}$$, false, 'function_call', 17),
  (94, 'fc_cdss_50_50', $${"function": "compute_data_split_sizes", "args": [10, [0.5, 0.5]], "kwargs": {}}$$, $${"result": [5, 5]}$$, true, 'function_call', 18),
  (94, 'fc_cdss_remainder_to_last', $${"function": "compute_data_split_sizes", "args": [99, [0.6, 0.2, 0.2]], "kwargs": {}}$$, $${"result": [59, 19, 21]}$$, true, 'function_call', 19),
  (94, 'fc_cdss_8_2_split', $${"function": "compute_data_split_sizes", "args": [4, [0.8, 0.2]], "kwargs": {}}$$, $${"result": [3, 1]}$$, true, 'function_call', 20),
  (94, 'fc_cdss_large', $${"function": "compute_data_split_sizes", "args": [1000, [0.6, 0.2, 0.2]], "kwargs": {}}$$, $${"result": [600, 200, 200]}$$, true, 'function_call', 21),
  (94, 'fc_cdss_zero_total', $${"function": "compute_data_split_sizes", "args": [0, [0.5, 0.5]], "kwargs": {}}$$, $${"result": [0, 0]}$$, true, 'function_call', 22),
  (94, 'fc_cdss_raises_on_bad_ratios', $${"function": "compute_data_split_sizes", "args": [100, [0.5, 0.4]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (94, 'fc_cdss_raises_on_negative_total', $${"function": "compute_data_split_sizes", "args": [-10, [0.5, 0.5]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 24),
  (94, 'fc_cdss_raises_on_non_list', $${"function": "compute_data_split_sizes", "args": [100, "abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 25),
  (94, 'fc_espm_one_million', $${"function": "estimate_param_size_mb", "args": [1000000], "kwargs": {}}$$, $${"result": 3.8147, "tolerance": 0.0001}$$, false, 'function_call', 26),
  (94, 'fc_espm_zero', $${"function": "estimate_param_size_mb", "args": [0], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 0.0001}$$, true, 'function_call', 27),
  (94, 'fc_espm_small_thousand', $${"function": "estimate_param_size_mb", "args": [1000], "kwargs": {}}$$, $${"result": 0.003814697, "tolerance": 0.0001}$$, true, 'function_call', 28),
  (94, 'fc_espm_resnet50', $${"function": "estimate_param_size_mb", "args": [25000000], "kwargs": {}}$$, $${"result": 95.367, "tolerance": 0.01}$$, true, 'function_call', 29),
  (94, 'fc_espm_hundred_million', $${"function": "estimate_param_size_mb", "args": [100000000], "kwargs": {}}$$, $${"result": 381.4697, "tolerance": 0.01}$$, true, 'function_call', 30),
  (94, 'fc_espm_mobilenet', $${"function": "estimate_param_size_mb", "args": [3500000], "kwargs": {}}$$, $${"result": 13.3514, "tolerance": 0.01}$$, true, 'function_call', 31),
  (94, 'fc_espm_raises_on_negative', $${"function": "estimate_param_size_mb", "args": [-1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 32),
  (94, 'fc_espm_raises_on_non_int', $${"function": "estimate_param_size_mb", "args": [1.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 33);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=94 GROUP BY task_id;

COMMIT;