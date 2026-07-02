-- WX07 (task_id=124) function_call task_tests — 32 条

BEGIN;

DELETE FROM task_tests WHERE task_id=124;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (124, 'fc_trim_spaces', $${"function": "trim_whitespace", "args": ["  hello  "], "kwargs": {}}$$, $${"result": "hello"}$$, false, 'function_call', 1),
  (124, 'fc_trim_tabs', $${"function": "trim_whitespace", "args": ["\thello\t"], "kwargs": {}}$$, $${"result": "hello"}$$, true, 'function_call', 2),
  (124, 'fc_trim_newlines', $${"function": "trim_whitespace", "args": ["\n\nhello\n"], "kwargs": {}}$$, $${"result": "hello"}$$, true, 'function_call', 3),
  (124, 'fc_trim_mixed', $${"function": "trim_whitespace", "args": [" \t\nhello\n\t "], "kwargs": {}}$$, $${"result": "hello"}$$, true, 'function_call', 4),
  (124, 'fc_trim_full_width_space', $${"function": "trim_whitespace", "args": ["　hello　"], "kwargs": {}}$$, $${"result": "hello"}$$, true, 'function_call', 5),
  (124, 'fc_trim_internal_preserved', $${"function": "trim_whitespace", "args": ["  a b c  "], "kwargs": {}}$$, $${"result": "a b c"}$$, true, 'function_call', 6),
  (124, 'fc_trim_raises_on_non_string', $${"function": "trim_whitespace", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (124, 'fc_collapse_double_space', $${"function": "collapse_internal_whitespace", "args": ["a  b"], "kwargs": {}}$$, $${"result": "a b"}$$, false, 'function_call', 8),
  (124, 'fc_collapse_triple_space', $${"function": "collapse_internal_whitespace", "args": ["a   b"], "kwargs": {}}$$, $${"result": "a b"}$$, true, 'function_call', 9),
  (124, 'fc_collapse_tab', $${"function": "collapse_internal_whitespace", "args": ["a\tb"], "kwargs": {}}$$, $${"result": "a b"}$$, true, 'function_call', 10),
  (124, 'fc_collapse_newline', $${"function": "collapse_internal_whitespace", "args": ["a\nb"], "kwargs": {}}$$, $${"result": "a b"}$$, true, 'function_call', 11),
  (124, 'fc_collapse_mixed', $${"function": "collapse_internal_whitespace", "args": ["a \t \n b"], "kwargs": {}}$$, $${"result": "a b"}$$, true, 'function_call', 12),
  (124, 'fc_collapse_with_trim', $${"function": "collapse_internal_whitespace", "args": ["  a  b  "], "kwargs": {}}$$, $${"result": "a b"}$$, true, 'function_call', 13),
  (124, 'fc_collapse_three_words', $${"function": "collapse_internal_whitespace", "args": ["hello   world   wide"], "kwargs": {}}$$, $${"result": "hello world wide"}$$, true, 'function_call', 14),
  (124, 'fc_collapse_raises_on_non_string', $${"function": "collapse_internal_whitespace", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (124, 'fc_truncate_short_unchanged', $${"function": "truncate_to_length", "args": ["hello", 10], "kwargs": {}}$$, $${"result": "hello"}$$, false, 'function_call', 16),
  (124, 'fc_truncate_long', $${"function": "truncate_to_length", "args": ["hello world", 5], "kwargs": {}}$$, $${"result": "hello"}$$, true, 'function_call', 17),
  (124, 'fc_truncate_exact_length', $${"function": "truncate_to_length", "args": ["hello", 5], "kwargs": {}}$$, $${"result": "hello"}$$, true, 'function_call', 18),
  (124, 'fc_truncate_to_3', $${"function": "truncate_to_length", "args": ["hello", 3], "kwargs": {}}$$, $${"result": "hel"}$$, true, 'function_call', 19),
  (124, 'fc_truncate_to_1', $${"function": "truncate_to_length", "args": ["hello", 1], "kwargs": {}}$$, $${"result": "h"}$$, true, 'function_call', 20),
  (124, 'fc_truncate_chinese', $${"function": "truncate_to_length", "args": ["中文测试", 2], "kwargs": {}}$$, $${"result": "中文"}$$, true, 'function_call', 21),
  (124, 'fc_truncate_to_zero', $${"function": "truncate_to_length", "args": ["hello", 0], "kwargs": {}}$$, $${"result": ""}$$, true, 'function_call', 22),
  (124, 'fc_truncate_raises_on_negative', $${"function": "truncate_to_length", "args": ["hello", -1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (124, 'fc_truncate_raises_on_non_string', $${"function": "truncate_to_length", "args": [123, 5], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24),
  (124, 'fc_punc_english', $${"function": "remove_punctuation", "args": ["Hello, World!"], "kwargs": {}}$$, $${"result": "Hello World"}$$, false, 'function_call', 25),
  (124, 'fc_punc_question', $${"function": "remove_punctuation", "args": ["What?"], "kwargs": {}}$$, $${"result": "What"}$$, true, 'function_call', 26),
  (124, 'fc_punc_chinese', $${"function": "remove_punctuation", "args": ["你好，世界！"], "kwargs": {}}$$, $${"result": "你好世界"}$$, true, 'function_call', 27),
  (124, 'fc_punc_mixed', $${"function": "remove_punctuation", "args": ["Hi! 你好。"], "kwargs": {}}$$, $${"result": "Hi 你好"}$$, true, 'function_call', 28),
  (124, 'fc_punc_quotes', $${"function": "remove_punctuation", "args": ["\"Quote\" 'tick'"], "kwargs": {}}$$, $${"result": "Quote tick"}$$, true, 'function_call', 29),
  (124, 'fc_punc_brackets', $${"function": "remove_punctuation", "args": ["[a] (b) {c}"], "kwargs": {}}$$, $${"result": "a b c"}$$, true, 'function_call', 30),
  (124, 'fc_punc_no_punctuation', $${"function": "remove_punctuation", "args": ["hello world"], "kwargs": {}}$$, $${"result": "hello world"}$$, true, 'function_call', 31),
  (124, 'fc_punc_raises_on_non_string', $${"function": "remove_punctuation", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 32);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=124 GROUP BY task_id;

COMMIT;