-- MJ09 全 fc 转换: 30 cases (F1=8 + F2=7 + F3=7 + F4=8)
BEGIN;
DELETE FROM task_tests WHERE task_id=90;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (90, 'fc_sup_a_three_quarters', $${"function": "compute_support", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], ["A"]], "kwargs": {}}$$, $${"result": 0.75, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (90, 'fc_sup_ab_half', $${"function": "compute_support", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], ["A", "B"]], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (90, 'fc_sup_abc_quarter', $${"function": "compute_support", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], ["A", "B", "C"]], "kwargs": {}}$$, $${"result": 0.25, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (90, 'fc_sup_zero', $${"function": "compute_support", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], ["Z"]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (90, 'fc_sup_full', $${"function": "compute_support", "args": [[["A"], ["A"], ["A"], ["A"], ["A"]], ["A"]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (90, 'fc_sup_two_fifths', $${"function": "compute_support", "args": [[["A"], ["A", "B"], ["A"], ["B"], ["A"]], ["B"]], "kwargs": {}}$$, $${"result": 0.4, "tolerance": 1e-06}$$, true, 'function_call', 6),
  (90, 'fc_sup_raises_on_empty', $${"function": "compute_support", "args": [[], ["A"]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (90, 'fc_sup_raises_on_non_list', $${"function": "compute_support", "args": ["abc", ["A"]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (90, 'fc_conf_a_to_b', $${"function": "compute_confidence", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], ["A"], ["B"]], "kwargs": {}}$$, $${"result": 0.6666666666666666, "tolerance": 1e-06}$$, false, 'function_call', 9),
  (90, 'fc_conf_b_to_a', $${"function": "compute_confidence", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], ["B"], ["A"]], "kwargs": {}}$$, $${"result": 0.6666666666666666, "tolerance": 1e-06}$$, true, 'function_call', 10),
  (90, 'fc_conf_a_to_z', $${"function": "compute_confidence", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], ["A"], ["Z"]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 11),
  (90, 'fc_conf_full', $${"function": "compute_confidence", "args": [[["A", "B"], ["A", "B"]], ["A"], ["B"]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, true, 'function_call', 12),
  (90, 'fc_conf_partial', $${"function": "compute_confidence", "args": [[["A", "B"], ["A"], ["A", "B"], ["A"]], ["A"], ["B"]], "kwargs": {}}$$, $${"result": 0.5, "tolerance": 1e-06}$$, true, 'function_call', 13),
  (90, 'fc_conf_zero_ante', $${"function": "compute_confidence", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], ["Z"], ["A"]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (90, 'fc_conf_non_list', $${"function": "compute_confidence", "args": ["abc", ["A"], ["B"]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (90, 'fc_lift_independent', $${"function": "compute_lift", "args": [[["A", "B"], ["A"], ["B"], []], ["A"], ["B"]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 16),
  (90, 'fc_lift_positive', $${"function": "compute_lift", "args": [[["A", "B"], ["A", "B"], ["C"]], ["A"], ["B"]], "kwargs": {}}$$, $${"result": 1.5, "tolerance": 1e-06}$$, true, 'function_call', 17),
  (90, 'fc_lift_classic_4trans', $${"function": "compute_lift", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], ["A"], ["B"]], "kwargs": {}}$$, $${"result": 0.8888888888888888, "tolerance": 1e-06}$$, true, 'function_call', 18),
  (90, 'fc_lift_negative', $${"function": "compute_lift", "args": [[["A"], ["A"], ["B"], ["B"]], ["A"], ["B"]], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 19),
  (90, 'fc_lift_double_classical', $${"function": "compute_lift", "args": [[["A", "B"], ["A", "B"], ["A", "C"], ["A", "C"]], ["A"], ["B"]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, true, 'function_call', 20),
  (90, 'fc_lift_zero_cons', $${"function": "compute_lift", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], ["A"], ["Z"]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 21),
  (90, 'fc_lift_non_list', $${"function": "compute_lift", "args": ["abc", ["A"], ["B"]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 22),
  (90, 'fc_ffi_half', $${"function": "find_frequent_itemsets", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], 0.5], "kwargs": {}}$$, $${"result": {"__set__": [{"__set__": ["A", "B"]}, {"__set__": ["A", "C"]}, {"__set__": ["A"]}, {"__set__": ["B", "C"]}, {"__set__": ["B"]}, {"__set__": ["C"]}]}}$$, false, 'function_call', 23),
  (90, 'fc_ffi_three_quarter', $${"function": "find_frequent_itemsets", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], 0.75], "kwargs": {}}$$, $${"result": {"__set__": [{"__set__": ["A"]}, {"__set__": ["B"]}, {"__set__": ["C"]}]}}$$, true, 'function_call', 24),
  (90, 'fc_ffi_one_empty', $${"function": "find_frequent_itemsets", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], 1.0], "kwargs": {}}$$, $${"result": {"__set__": []}}$$, true, 'function_call', 25),
  (90, 'fc_ffi_3trans_high', $${"function": "find_frequent_itemsets", "args": [[["A", "B"], ["A", "B"], ["A", "B"]], 1.0], "kwargs": {}}$$, $${"result": {"__set__": [{"__set__": ["A", "B"]}, {"__set__": ["A"]}, {"__set__": ["B"]}]}}$$, true, 'function_call', 26),
  (90, 'fc_ffi_specific_low', $${"function": "find_frequent_itemsets", "args": [[["A"], ["B"], ["A", "B"], ["C"]], 0.5], "kwargs": {}}$$, $${"result": {"__set__": [{"__set__": ["A"]}, {"__set__": ["B"]}]}}$$, true, 'function_call', 27),
  (90, 'fc_ffi_empty', $${"function": "find_frequent_itemsets", "args": [[], 0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 28),
  (90, 'fc_ffi_threshold', $${"function": "find_frequent_itemsets", "args": [[["A", "B"], ["A", "C"], ["B", "C"], ["A", "B", "C"]], 1.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 29),
  (90, 'fc_ffi_non_list', $${"function": "find_frequent_itemsets", "args": ["abc", 0.5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 30);

-- 验证: 30 cases + match_rule=function_call
SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules, STRING_AGG(DISTINCT match_rule,',') AS rule_set, SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden FROM task_tests WHERE task_id=90 GROUP BY task_id;
COMMIT;

-- 30 cases generated
