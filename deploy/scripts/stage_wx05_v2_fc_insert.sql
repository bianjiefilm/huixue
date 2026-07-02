-- WX05 (task_id=122) function_call task_tests — 25 条

BEGIN;

DELETE FROM task_tests WHERE task_id=122;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (122, 'fc_phone_dashes_138', $${"function": "normalize_phone_digits", "args": ["138-0000-0000"], "kwargs": {}}$$, $${"result": "13800000000"}$$, false, 'function_call', 1),
  (122, 'fc_phone_spaces_186', $${"function": "normalize_phone_digits", "args": ["186 5555 1234"], "kwargs": {}}$$, $${"result": "18655551234"}$$, true, 'function_call', 2),
  (122, 'fc_phone_parens_199', $${"function": "normalize_phone_digits", "args": ["(199) 8888-2222"], "kwargs": {}}$$, $${"result": "19988882222"}$$, true, 'function_call', 3),
  (122, 'fc_phone_intl_prefix_852', $${"function": "normalize_phone_digits", "args": ["+852 9123-4567"], "kwargs": {}}$$, $${"result": "85291234567"}$$, true, 'function_call', 4),
  (122, 'fc_phone_alphanumeric_mix', $${"function": "normalize_phone_digits", "args": ["1abc3xyz8"], "kwargs": {}}$$, $${"result": "138"}$$, true, 'function_call', 5),
  (122, 'fc_phone_no_digits', $${"function": "normalize_phone_digits", "args": ["abc"], "kwargs": {}}$$, $${"result": ""}$$, true, 'function_call', 6),
  (122, 'fc_phone_raises_on_non_string', $${"function": "normalize_phone_digits", "args": [13800000000], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (122, 'fc_email_bob_163', $${"function": "normalize_email_lower", "args": ["  Bob@163.COM  "], "kwargs": {}}$$, $${"result": "bob@163.com"}$$, false, 'function_call', 8),
  (122, 'fc_email_carol_qq', $${"function": "normalize_email_lower", "args": [" Carol.X@qq.com  "], "kwargs": {}}$$, $${"result": "carol.x@qq.com"}$$, true, 'function_call', 9),
  (122, 'fc_email_alice_uppercase_with_spaces', $${"function": "normalize_email_lower", "args": [" Alice@Gmail.com "], "kwargs": {}}$$, $${"result": "alice@gmail.com"}$$, true, 'function_call', 10),
  (122, 'fc_email_dave_with_tabs', $${"function": "normalize_email_lower", "args": ["\tDAVE@Hotmail.CO.UK\t"], "kwargs": {}}$$, $${"result": "dave@hotmail.co.uk"}$$, true, 'function_call', 11),
  (122, 'fc_email_empty_after_strip', $${"function": "normalize_email_lower", "args": ["   "], "kwargs": {}}$$, $${"result": ""}$$, true, 'function_call', 12),
  (122, 'fc_email_raises_on_non_string', $${"function": "normalize_email_lower", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 13),
  (122, 'fc_invalid_no_at', $${"function": "is_valid_email_basic", "args": ["alice.gmail.com"], "kwargs": {}}$$, $${"result": false}$$, false, 'function_call', 14),
  (122, 'fc_invalid_just_text', $${"function": "is_valid_email_basic", "args": ["notanemail"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 15),
  (122, 'fc_invalid_only_dot', $${"function": "is_valid_email_basic", "args": ["alice.com"], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 16),
  (122, 'fc_valid_typical', $${"function": "is_valid_email_basic", "args": ["alice@gmail.com"], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 17),
  (122, 'fc_valid_raises_on_non_string', $${"function": "is_valid_email_basic", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 18),
  (122, 'fc_date_2026_04_25', $${"function": "parse_simple_date_iso", "args": ["2026-04-25"], "kwargs": {}}$$, $${"result": [2026, 4, 25]}$$, false, 'function_call', 19),
  (122, 'fc_date_2000_01_01', $${"function": "parse_simple_date_iso", "args": ["2000-01-01"], "kwargs": {}}$$, $${"result": [2000, 1, 1]}$$, true, 'function_call', 20),
  (122, 'fc_date_2024_12_31', $${"function": "parse_simple_date_iso", "args": ["2024-12-31"], "kwargs": {}}$$, $${"result": [2024, 12, 31]}$$, true, 'function_call', 21),
  (122, 'fc_date_leap_day_2024_02_29', $${"function": "parse_simple_date_iso", "args": ["2024-02-29"], "kwargs": {}}$$, $${"result": [2024, 2, 29]}$$, true, 'function_call', 22),
  (122, 'fc_date_1999_09_09', $${"function": "parse_simple_date_iso", "args": ["1999-09-09"], "kwargs": {}}$$, $${"result": [1999, 9, 9]}$$, true, 'function_call', 23),
  (122, 'fc_date_raises_on_non_numeric', $${"function": "parse_simple_date_iso", "args": ["year-mm-dd"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 24),
  (122, 'fc_date_raises_on_non_string', $${"function": "parse_simple_date_iso", "args": [20260425], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 25);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=122 GROUP BY task_id;

COMMIT;