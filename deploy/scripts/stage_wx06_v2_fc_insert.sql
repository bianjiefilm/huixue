-- WX06 (task_id=123) function_call task_tests — 22 条

BEGIN;

DELETE FROM task_tests WHERE task_id=123;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (123, 'fc_cna_one_in_4', $${"function": "count_non_ascii", "args": ["abc中"], "kwargs": {}}$$, $${"result": 1}$$, false, 'function_call', 1),
  (123, 'fc_cna_two_in_5', $${"function": "count_non_ascii", "args": ["abc中文"], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 2),
  (123, 'fc_cna_one_in_5', $${"function": "count_non_ascii", "args": ["中a b c"], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 3),
  (123, 'fc_cna_four_in_6', $${"function": "count_non_ascii", "args": ["ab中文测试"], "kwargs": {}}$$, $${"result": 4}$$, true, 'function_call', 4),
  (123, 'fc_cna_two_emojis', $${"function": "count_non_ascii", "args": ["ab😀c😀"], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 5),
  (123, 'fc_cna_raises_on_non_string', $${"function": "count_non_ascii", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (123, 'fc_rcc_remove_bell', $${"function": "remove_control_chars", "args": ["hi\u0007there"], "kwargs": {}}$$, $${"result": "hithere"}$$, false, 'function_call', 7),
  (123, 'fc_rcc_remove_null', $${"function": "remove_control_chars", "args": ["a\u0000b"], "kwargs": {}}$$, $${"result": "ab"}$$, true, 'function_call', 8),
  (123, 'fc_rcc_remove_vt', $${"function": "remove_control_chars", "args": ["a\u000bb"], "kwargs": {}}$$, $${"result": "ab"}$$, true, 'function_call', 9),
  (123, 'fc_rcc_mixed_keep_remove', $${"function": "remove_control_chars", "args": ["a\tb\nc\u0007d"], "kwargs": {}}$$, $${"result": "a\tb\ncd"}$$, true, 'function_call', 10),
  (123, 'fc_rcc_keep_only_visible', $${"function": "remove_control_chars", "args": ["hi\u0005world"], "kwargs": {}}$$, $${"result": "hiworld"}$$, true, 'function_call', 11),
  (123, 'fc_rcc_raises_on_non_string', $${"function": "remove_control_chars", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 12),
  (123, 'fc_ipa_only_chinese', $${"function": "is_pure_ascii", "args": ["中文"], "kwargs": {}}$$, $${"result": false}$$, false, 'function_call', 13),
  (123, 'fc_ipa_japanese', $${"function": "is_pure_ascii", "args": ["ひらがな"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 14),
  (123, 'fc_ipa_emoji_only', $${"function": "is_pure_ascii", "args": ["😀😀"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 15),
  (123, 'fc_ipa_korean', $${"function": "is_pure_ascii", "args": ["한글"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 16),
  (123, 'fc_ipa_raises_on_non_string', $${"function": "is_pure_ascii", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 17),
  (123, 'fc_bom_starts_with_bom', $${"function": "has_utf8_bom", "args": ["﻿hello"], "kwargs": {}}$$, $${"result": true}$$, false, 'function_call', 18),
  (123, 'fc_bom_in_middle', $${"function": "has_utf8_bom", "args": ["hi﻿lo"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 19),
  (123, 'fc_bom_at_end', $${"function": "has_utf8_bom", "args": ["hi﻿"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 20),
  (123, 'fc_bom_two_in_middle', $${"function": "has_utf8_bom", "args": ["h﻿i﻿"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 21),
  (123, 'fc_bom_raises_on_non_string', $${"function": "has_utf8_bom", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 22);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=123 GROUP BY task_id;

COMMIT;