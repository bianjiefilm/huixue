-- MJ01 (task_id=82) function_call task_tests 转换 — 24 条

BEGIN;

-- 删除现有错误的 io_based task_tests
DELETE FROM task_tests WHERE task_id=82;

-- 插入新 fc 协议 task_tests
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (82, 'fc_phase_business_understanding', $${"function": "map_activity_to_phase", "args": ["明确业务目标和成功标准"], "kwargs": {}}$$, $${"result": "业务理解"}$$, false, 'function_call', 1),
  (82, 'fc_phase_data_preparation', $${"function": "map_activity_to_phase", "args": ["缺失值填充与特征编码"], "kwargs": {}}$$, $${"result": "数据准备"}$$, true, 'function_call', 2),
  (82, 'fc_phase_modeling', $${"function": "map_activity_to_phase", "args": ["调整随机森林超参数"], "kwargs": {}}$$, $${"result": "建模"}$$, true, 'function_call', 3),
  (82, 'fc_phase_deployment', $${"function": "map_activity_to_phase", "args": ["将模型上线监控线上指标"], "kwargs": {}}$$, $${"result": "部署"}$$, true, 'function_call', 4),
  (82, 'fc_phase_unknown_for_empty_string', $${"function": "map_activity_to_phase", "args": [""], "kwargs": {}}$$, $${"result": "未知"}$$, true, 'function_call', 5),
  (82, 'fc_phase_raises_on_non_string', $${"function": "map_activity_to_phase", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (82, 'fc_lt_supervised', $${"function": "classify_learning_type", "args": [true, true], "kwargs": {}}$$, $${"result": "supervised"}$$, false, 'function_call', 7),
  (82, 'fc_lt_unsupervised_when_no_labels', $${"function": "classify_learning_type", "args": [false, false], "kwargs": {}}$$, $${"result": "unsupervised"}$$, true, 'function_call', 8),
  (82, 'fc_lt_semi_supervised_when_partial', $${"function": "classify_learning_type", "args": [true, false], "kwargs": {}}$$, $${"result": "semi-supervised"}$$, true, 'function_call', 9),
  (82, 'fc_lt_unsupervised_dominates_when_no_labels_even_if_all_labeled_true', $${"function": "classify_learning_type", "args": [false, true], "kwargs": {}}$$, $${"result": "unsupervised"}$$, true, 'function_call', 10),
  (82, 'fc_lt_raises_on_non_bool', $${"function": "classify_learning_type", "args": ["yes", true], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 11),
  (82, 'fc_acc_all_correct', $${"function": "compute_accuracy", "args": [[1, 1, 0, 0], [1, 1, 0, 0]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-09}$$, false, 'function_call', 12),
  (82, 'fc_acc_all_wrong', $${"function": "compute_accuracy", "args": [[1, 1, 0, 0], [0, 0, 1, 1]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-09}$$, true, 'function_call', 13),
  (82, 'fc_acc_partial', $${"function": "compute_accuracy", "args": [[1, 1, 0, 0], [1, 0, 0, 0]], "kwargs": {}}$$, $${"result": 0.75, "tolerance": 1e-09}$$, true, 'function_call', 14),
  (82, 'fc_acc_multiclass', $${"function": "compute_accuracy", "args": [[0, 1, 2, 3], [0, 1, 2, 3]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-09}$$, true, 'function_call', 15),
  (82, 'fc_acc_single_sample_correct', $${"function": "compute_accuracy", "args": [[1], [1]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-09}$$, true, 'function_call', 16),
  (82, 'fc_acc_raises_on_empty', $${"function": "compute_accuracy", "args": [[], []], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 17),
  (82, 'fc_acc_raises_on_length_mismatch', $${"function": "compute_accuracy", "args": [[1, 1, 0], [1, 1]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (82, 'fc_of_clearly_overfit', $${"function": "is_overfit", "args": [0.99, 0.6, 0.1], "kwargs": {}}$$, $${"result": {"is_overfitting": true, "gap": 0.39}, "tolerance": 1e-09}$$, false, 'function_call', 19),
  (82, 'fc_of_not_overfit_small_gap', $${"function": "is_overfit", "args": [0.85, 0.83, 0.1], "kwargs": {}}$$, $${"result": {"is_overfitting": false, "gap": 0.02}, "tolerance": 1e-09}$$, true, 'function_call', 20),
  (82, 'fc_of_not_overfit_zero_gap', $${"function": "is_overfit", "args": [0.7, 0.7, 0.1], "kwargs": {}}$$, $${"result": {"is_overfitting": false, "gap": 0.0}, "tolerance": 1e-09}$$, true, 'function_call', 21),
  (82, 'fc_of_threshold_strict_greater', $${"function": "is_overfit", "args": [0.5, 0.4, 0.1], "kwargs": {}}$$, $${"result": {"is_overfitting": false, "gap": 0.1}, "tolerance": 1e-09}$$, true, 'function_call', 22),
  (82, 'fc_of_extreme_gap', $${"function": "is_overfit", "args": [1.0, 0.0, 0.1], "kwargs": {}}$$, $${"result": {"is_overfitting": true, "gap": 1.0}, "tolerance": 1e-09}$$, true, 'function_call', 23),
  (82, 'fc_of_raises_on_non_numeric', $${"function": "is_overfit", "args": ["0.9", 0.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24);

-- 验证
SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=82 GROUP BY task_id;

COMMIT;
