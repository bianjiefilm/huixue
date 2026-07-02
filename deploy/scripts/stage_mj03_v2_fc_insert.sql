-- MJ03 (task_id=84) function_call task_tests — 32 条

BEGIN;

-- 删除现有错误的 io_based task_tests
DELETE FROM task_tests WHERE task_id=84;

-- 插入新 fc 协议 task_tests
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (84, 'fc_le_basic', $${"function": "label_encode", "args": [["cat", "dog", "cat", "bird"]], "kwargs": {}}$$, $${"result": [[1, 2, 1, 0], {"bird": 0, "cat": 1, "dog": 2}]}$$, false, 'function_call', 1),
  (84, 'fc_le_two_classes', $${"function": "label_encode", "args": [["x", "y", "x", "y"]], "kwargs": {}}$$, $${"result": [[0, 1, 0, 1], {"x": 0, "y": 1}]}$$, true, 'function_call', 2),
  (84, 'fc_le_single_element', $${"function": "label_encode", "args": [["only"]], "kwargs": {}}$$, $${"result": [[0], {"only": 0}]}$$, true, 'function_call', 3),
  (84, 'fc_le_all_same', $${"function": "label_encode", "args": [["a", "a", "a", "a", "a"]], "kwargs": {}}$$, $${"result": [[0, 0, 0, 0, 0], {"a": 0}]}$$, true, 'function_call', 4),
  (84, 'fc_le_sorted_assignment', $${"function": "label_encode", "args": [["z", "a", "m"]], "kwargs": {}}$$, $${"result": [[2, 0, 1], {"a": 0, "m": 1, "z": 2}]}$$, true, 'function_call', 5),
  (84, 'fc_le_raises_on_empty', $${"function": "label_encode", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (84, 'fc_le_raises_on_non_list', $${"function": "label_encode", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (84, 'fc_le_raises_on_non_string_element', $${"function": "label_encode", "args": [["a", 1, "b"]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (84, 'fc_zscore_basic', $${"function": "z_score_standardize", "args": [[1, 2, 3, 4, 5]], "kwargs": {}}$$, $${"result": [-1.4142135623730951, -0.7071067811865475, 0.0, 0.7071067811865475, 1.4142135623730951], "tolerance": 0.0001}$$, false, 'function_call', 9),
  (84, 'fc_zscore_centered', $${"function": "z_score_standardize", "args": [[-2, -1, 0, 1, 2]], "kwargs": {}}$$, $${"result": [-1.4142135623730951, -0.7071067811865475, 0.0, 0.7071067811865475, 1.4142135623730951], "tolerance": 0.0001}$$, true, 'function_call', 10),
  (84, 'fc_zscore_two_values', $${"function": "z_score_standardize", "args": [[100, 200]], "kwargs": {}}$$, $${"result": [-1.0, 1.0], "tolerance": 1e-06}$$, true, 'function_call', 11),
  (84, 'fc_zscore_known_4', $${"function": "z_score_standardize", "args": [[1, 3, 5, 7]], "kwargs": {}}$$, $${"result": [-1.3416407864998738, -0.4472135954999579, 0.4472135954999579, 1.3416407864998738], "tolerance": 0.0001}$$, true, 'function_call', 12),
  (84, 'fc_zscore_raises_on_constant', $${"function": "z_score_standardize", "args": [[10, 10, 10, 10]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (84, 'fc_zscore_raises_on_single', $${"function": "z_score_standardize", "args": [[42]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (84, 'fc_zscore_raises_on_empty', $${"function": "z_score_standardize", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (84, 'fc_zscore_raises_on_non_list', $${"function": "z_score_standardize", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (84, 'fc_fwm_replace_one', $${"function": "fill_with_median", "args": [[1, 2, null, 4, 5]], "kwargs": {}}$$, $${"result": [1, 2, 3, 4, 5]}$$, false, 'function_call', 17),
  (84, 'fc_fwm_two_nones', $${"function": "fill_with_median", "args": [[null, 1, 2, 3, null]], "kwargs": {}}$$, $${"result": [2, 1, 2, 3, 2]}$$, true, 'function_call', 18),
  (84, 'fc_fwm_one_none_three_values', $${"function": "fill_with_median", "args": [[10, null, 20]], "kwargs": {}}$$, $${"result": [10, 15, 20]}$$, true, 'function_call', 19),
  (84, 'fc_fwm_constant_with_none', $${"function": "fill_with_median", "args": [[5, 5, null, 5, 5]], "kwargs": {}}$$, $${"result": [5, 5, 5, 5, 5]}$$, true, 'function_call', 20),
  (84, 'fc_fwm_known_median', $${"function": "fill_with_median", "args": [[10, 20, null, 40, 50]], "kwargs": {}}$$, $${"result": [10, 20, 30, 40, 50]}$$, true, 'function_call', 21),
  (84, 'fc_fwm_all_none_raises', $${"function": "fill_with_median", "args": [[null, null, null]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (84, 'fc_fwm_empty_raises', $${"function": "fill_with_median", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (84, 'fc_fwm_raises_on_non_list', $${"function": "fill_with_median", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24),
  (84, 'fc_flv_remove_constant', $${"function": "filter_low_variance", "args": [[[1, 2, 3], [2, 2, 4], [3, 2, 5]]], "kwargs": {"threshold": 0.0}}$$, $${"result": [[[1, 3], [2, 4], [3, 5]], [0, 2]]}$$, false, 'function_call', 25),
  (84, 'fc_flv_high_threshold_keeps_high_var', $${"function": "filter_low_variance", "args": [[[1, 2, 3], [5, 2, 7], [10, 2, 11]]], "kwargs": {"threshold": 12.0}}$$, $${"result": [[[1], [5], [10]], [0]]}$$, true, 'function_call', 26),
  (84, 'fc_flv_keep_all', $${"function": "filter_low_variance", "args": [[[1, 2], [3, 4], [5, 6]]], "kwargs": {"threshold": 0.5}}$$, $${"result": [[[1, 2], [3, 4], [5, 6]], [0, 1]]}$$, true, 'function_call', 27),
  (84, 'fc_flv_three_kept_of_four', $${"function": "filter_low_variance", "args": [[[1, 1, 1, 1], [2, 1, 2, 2], [3, 1, 1, 3]]], "kwargs": {"threshold": 0.0}}$$, $${"result": [[[1, 1, 1], [2, 2, 2], [3, 1, 3]], [0, 2, 3]]}$$, true, 'function_call', 28),
  (84, 'fc_flv_threshold_excludes_some', $${"function": "filter_low_variance", "args": [[[1, 1, 1, 1], [2, 1, 2, 2], [3, 1, 1, 3]]], "kwargs": {"threshold": 0.5}}$$, $${"result": [[[1, 1], [2, 2], [3, 3]], [0, 3]]}$$, true, 'function_call', 29),
  (84, 'fc_flv_raises_on_single_sample', $${"function": "filter_low_variance", "args": [[[1, 2, 3]]], "kwargs": {"threshold": 0.0}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 30),
  (84, 'fc_flv_raises_on_empty', $${"function": "filter_low_variance", "args": [[]], "kwargs": {"threshold": 0.0}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (84, 'fc_flv_raises_on_non_list', $${"function": "filter_low_variance", "args": ["abc"], "kwargs": {"threshold": 0.0}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 32);

-- 验证
SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=84 GROUP BY task_id;

COMMIT;