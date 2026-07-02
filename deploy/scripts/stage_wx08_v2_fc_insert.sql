-- WX08 (task_id=125) function_call task_tests — 28 条

BEGIN;

DELETE FROM task_tests WHERE task_id=125;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (125, 'fc_parse_dollar_thousands', $${"function": "parse_numeric_string", "args": ["$1,234.56"], "kwargs": {}}$$, $${"result": 1234.56, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (125, 'fc_parse_yuan_thousands', $${"function": "parse_numeric_string", "args": ["￥9,876.5"], "kwargs": {}}$$, $${"result": 9876.5, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (125, 'fc_parse_yen', $${"function": "parse_numeric_string", "args": ["¥500"], "kwargs": {}}$$, $${"result": 500.0, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (125, 'fc_parse_dollar_no_thousands', $${"function": "parse_numeric_string", "args": ["$50"], "kwargs": {}}$$, $${"result": 50.0, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (125, 'fc_parse_multi_thousands', $${"function": "parse_numeric_string", "args": ["1,234,567.89"], "kwargs": {}}$$, $${"result": 1234567.89, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (125, 'fc_parse_simple_with_thousands', $${"function": "parse_numeric_string", "args": ["1,000"], "kwargs": {}}$$, $${"result": 1000.0, "tolerance": 1e-06}$$, true, 'function_call', 6),
  (125, 'fc_parse_raises_on_letters', $${"function": "parse_numeric_string", "args": ["abc"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (125, 'fc_parse_raises_on_unit_suffix', $${"function": "parse_numeric_string", "args": ["100.00 USD"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 8),
  (125, 'fc_parse_raises_on_non_string', $${"function": "parse_numeric_string", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 9),
  (125, 'fc_clip_below', $${"function": "clip_to_range", "args": [50.0, 100.0, 200.0], "kwargs": {}}$$, $${"result": 100.0, "tolerance": 1e-06}$$, false, 'function_call', 10),
  (125, 'fc_clip_above', $${"function": "clip_to_range", "args": [300.0, 0.0, 100.0], "kwargs": {}}$$, $${"result": 100.0, "tolerance": 1e-06}$$, true, 'function_call', 11),
  (125, 'fc_clip_negative_below', $${"function": "clip_to_range", "args": [-50.0, -10.0, 10.0], "kwargs": {}}$$, $${"result": -10.0, "tolerance": 1e-06}$$, true, 'function_call', 12),
  (125, 'fc_clip_raises_on_lower_gt_upper', $${"function": "clip_to_range", "args": [50.0, 100.0, 0.0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (125, 'fc_round_half_up_05', $${"function": "round_half_up", "args": [0.5], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, false, 'function_call', 14),
  (125, 'fc_round_half_up_15', $${"function": "round_half_up", "args": [1.5], "kwargs": {}}$$, $${"result": 2.0, "tolerance": 1e-06}$$, true, 'function_call', 15),
  (125, 'fc_round_half_up_25', $${"function": "round_half_up", "args": [2.5], "kwargs": {}}$$, $${"result": 3.0, "tolerance": 1e-06}$$, true, 'function_call', 16),
  (125, 'fc_round_half_up_45', $${"function": "round_half_up", "args": [4.5], "kwargs": {}}$$, $${"result": 5.0, "tolerance": 1e-06}$$, true, 'function_call', 17),
  (125, 'fc_round_half_up_with_decimals_2', $${"function": "round_half_up", "args": [1.235, 2], "kwargs": {}}$$, $${"result": 1.24, "tolerance": 1e-06}$$, true, 'function_call', 18),
  (125, 'fc_round_half_up_055', $${"function": "round_half_up", "args": [0.55, 1], "kwargs": {}}$$, $${"result": 0.6, "tolerance": 1e-06}$$, true, 'function_call', 19),
  (125, 'fc_round_half_up_raises_on_negative_decimals', $${"function": "round_half_up", "args": [1.5, -1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 20),
  (125, 'fc_round_half_up_raises_on_non_numeric', $${"function": "round_half_up", "args": ["1.5"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 21),
  (125, 'fc_isn_dollar', $${"function": "is_numeric_string", "args": ["$1,234.56"], "kwargs": {}}$$, $${"result": true}$$, false, 'function_call', 22),
  (125, 'fc_isn_yen', $${"function": "is_numeric_string", "args": ["¥500"], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 23),
  (125, 'fc_isn_yuan_thousands', $${"function": "is_numeric_string", "args": ["￥1,000"], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 24),
  (125, 'fc_isn_negative', $${"function": "is_numeric_string", "args": ["-100.25"], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 25),
  (125, 'fc_isn_invalid_letters', $${"function": "is_numeric_string", "args": ["abc"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 26),
  (125, 'fc_isn_invalid_unit_suffix', $${"function": "is_numeric_string", "args": ["100.00 USD"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 27),
  (125, 'fc_isn_raises_on_non_string', $${"function": "is_numeric_string", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 28);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=125 GROUP BY task_id;

COMMIT;