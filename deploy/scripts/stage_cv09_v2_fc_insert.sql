-- CV09 (task_id=114) function_call task_tests — 29 条

BEGIN;

DELETE FROM task_tests WHERE task_id=114;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (114, 'fc_conv_param_lenet_conv1', $${"function": "conv_layer_param_count", "args": [1, 6, 5, 5, true], "kwargs": {}}$$, $${"result": 156}$$, false, 'function_call', 1),
  (114, 'fc_conv_param_vgg_block', $${"function": "conv_layer_param_count", "args": [64, 128, 3, 3, true], "kwargs": {}}$$, $${"result": 73856}$$, true, 'function_call', 2),
  (114, 'fc_conv_param_no_bias', $${"function": "conv_layer_param_count", "args": [1, 6, 5, 5, false], "kwargs": {}}$$, $${"result": 150}$$, true, 'function_call', 3),
  (114, 'fc_conv_param_1x1', $${"function": "conv_layer_param_count", "args": [32, 64, 1, 1, true], "kwargs": {}}$$, $${"result": 2112}$$, true, 'function_call', 4),
  (114, 'fc_conv_param_boundary_small', $${"function": "conv_layer_param_count", "args": [1, 2, 3, 1, false], "kwargs": {}}$$, $${"result": 6}$$, true, 'function_call', 5),
  (114, 'fc_conv_param_default_bias_true', $${"function": "conv_layer_param_count", "args": [1, 6, 5, 5], "kwargs": {}}$$, $${"result": 156}$$, true, 'function_call', 6),
  (114, 'fc_conv_param_raises_on_zero', $${"function": "conv_layer_param_count", "args": [0, 6, 5, 5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (114, 'fc_conv_param_raises_on_non_int', $${"function": "conv_layer_param_count", "args": [1.0, 6, 5, 5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (114, 'fc_conv_output_lenet', $${"function": "conv_output_size_2d", "args": [28, 28, 5, 0, 1], "kwargs": {}}$$, $${"result": [24, 24]}$$, false, 'function_call', 9),
  (114, 'fc_conv_output_same_padding', $${"function": "conv_output_size_2d", "args": [32, 32, 3, 1, 1], "kwargs": {}}$$, $${"result": [32, 32]}$$, true, 'function_call', 10),
  (114, 'fc_conv_output_stride_2', $${"function": "conv_output_size_2d", "args": [32, 32, 3, 1, 2], "kwargs": {}}$$, $${"result": [16, 16]}$$, true, 'function_call', 11),
  (114, 'fc_conv_output_imagenet', $${"function": "conv_output_size_2d", "args": [224, 224, 7, 3, 2], "kwargs": {}}$$, $${"result": [112, 112]}$$, true, 'function_call', 12),
  (114, 'fc_conv_output_raises_on_too_small', $${"function": "conv_output_size_2d", "args": [3, 3, 5, 0, 1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (114, 'fc_conv_output_raises_on_non_int', $${"function": "conv_output_size_2d", "args": [28.0, 28, 3, 0, 1], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 14),
  (114, 'fc_softmax_simple', $${"function": "softmax_predict", "args": [[1.0, 5.0, 3.0]], "kwargs": {}}$$, $${"result": 1}$$, false, 'function_call', 15),
  (114, 'fc_softmax_last', $${"function": "softmax_predict", "args": [[1.0, 2.0, 9.0]], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 16),
  (114, 'fc_softmax_negative_argmax_middle', $${"function": "softmax_predict", "args": [[-5.0, -1.0, -3.0]], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 17),
  (114, 'fc_softmax_ties_first', $${"function": "softmax_predict", "args": [[3.0, 5.0, 5.0]], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 18),
  (114, 'fc_softmax_two_class', $${"function": "softmax_predict", "args": [[0.5, 2.0]], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 19),
  (114, 'fc_softmax_raises_on_empty', $${"function": "softmax_predict", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 20),
  (114, 'fc_softmax_raises_on_non_list', $${"function": "softmax_predict", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 21),
  (114, 'fc_ce_high_conf_label_1', $${"function": "cross_entropy_loss_single", "args": [[0.05, 0.9, 0.05], 1], "kwargs": {}}$$, $${"result": 0.10536051565782628, "tolerance": 1e-06}$$, false, 'function_call', 22),
  (114, 'fc_ce_high_conf_label_2', $${"function": "cross_entropy_loss_single", "args": [[0.05, 0.05, 0.9], 2], "kwargs": {}}$$, $${"result": 0.10536051565782628, "tolerance": 1e-06}$$, true, 'function_call', 23),
  (114, 'fc_ce_wrong_class', $${"function": "cross_entropy_loss_single", "args": [[0.9, 0.05, 0.05], 1], "kwargs": {}}$$, $${"result": 2.995732273553991, "tolerance": 1e-06}$$, true, 'function_call', 24),
  (114, 'fc_ce_two_class_label_1', $${"function": "cross_entropy_loss_single", "args": [[0.7, 0.3], 1], "kwargs": {}}$$, $${"result": 1.2039728043259361, "tolerance": 1e-06}$$, true, 'function_call', 25),
  (114, 'fc_ce_skewed_label_3', $${"function": "cross_entropy_loss_single", "args": [[0.1, 0.2, 0.3, 0.4], 3], "kwargs": {}}$$, $${"result": 0.916290731874155, "tolerance": 1e-06}$$, true, 'function_call', 26),
  (114, 'fc_ce_skewed_label_2', $${"function": "cross_entropy_loss_single", "args": [[0.1, 0.2, 0.3, 0.4], 2], "kwargs": {}}$$, $${"result": 1.2039728043259361, "tolerance": 1e-06}$$, true, 'function_call', 27),
  (114, 'fc_ce_raises_on_label_out_of_range', $${"function": "cross_entropy_loss_single", "args": [[0.5, 0.5], 2], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 28),
  (114, 'fc_ce_raises_on_non_list', $${"function": "cross_entropy_loss_single", "args": ["abc", 0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 29);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=114 GROUP BY task_id;

COMMIT;