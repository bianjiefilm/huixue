#!/usr/bin/env python3
"""Generate P3 redesign test cases for WX (11) and BD (11) tasks.

Output: /tmp/p3_redesign/all_cases.json - dict mapping fn_name -> list of {args, exp}
"""
import json, os, hashlib

cases = {}

# ================== WX 118 ==================
cases['classify_value_status'] = [
    {'args': [5, 0, 10], 'exp': 'valid'},
    {'args': [None, 0, 10], 'exp': 'missing'},
    {'args': ['x', 0, 10], 'exp': 'missing'},
    {'args': [-1, 0, 10], 'exp': 'out_of_range'},
    {'args': [100, 0, 10], 'exp': 'out_of_range'},
    {'args': [0, 0, 10], 'exp': 'valid'},
    {'args': [7, 0, 10], 'exp': 'valid'},
    {'args': [6, -5, 5], 'exp': 'valid'},
    {'args': [-6, -5, 5], 'exp': 'out_of_range'},
    {'args': [3, -5, 5], 'exp': 'valid'},
    {'args': [8, -5, 5], 'exp': 'out_of_range'},
    {'args': [-3, -5, 5], 'exp': 'valid'},
    {'args': [None, -5, 5], 'exp': 'missing'},
    {'args': ['', -5, 5], 'exp': 'missing'},
    {'args': ['abc', 0, 10], 'exp': 'missing'},
    {'args': [5, '0', 10], 'exp': 'raises'},
]
cases['compute_quality_ratio'] = [
    {'args': [78, 100], 'exp': 0.78},
    {'args': [1, 3], 'exp': 0.3333333333333333},
    {'args': [7, 8], 'exp': 0.875},
    {'args': [3, 7], 'exp': 0.42857142857142855},
    {'args': [100, 200], 'exp': 0.5},
    {'args': [9, 10], 'exp': 0.9},
    {'args': [0, 100], 'exp': 0.0},
    {'args': [1, 1], 'exp': 1.0},
    {'args': [50, 50], 'exp': 1.0},
    {'args': [3, 4], 'exp': 0.75},
    {'args': [7, 10], 'exp': 0.7},
    {'args': ['a', 100], 'exp': 'raises'},
    {'args': [-1, 100], 'exp': 'raises'},
    {'args': [101, 100], 'exp': 'raises'},
    {'args': [0, 0], 'exp': 'raises'},
]
cases['get_cleaning_priority'] = [
    {'args': ['missing'], 'exp': 1},
    {'args': ['duplicate'], 'exp': 2},
    {'args': ['outlier'], 'exp': 3},
    {'args': ['format'], 'exp': 4},
    {'args': ['consistency'], 'exp': 5},
    {'args': ['encoding'], 'exp': 6},
    {'args': ['typo'], 'exp': 7},
    {'args': ['unknown'], 'exp': 'raises'},
    {'args': [''], 'exp': 'raises'},
    {'args': [123], 'exp': 'raises'},
    {'args': [None], 'exp': 'raises'},
]
cases['decide_drop_or_fill'] = [
    {'args': [80, 100, 0.5], 'exp': 'drop'},
    {'args': [20, 100, 0.5], 'exp': 'fill'},
    {'args': [50, 100, 0.5], 'exp': 'drop'},
    {'args': [49, 100, 0.5], 'exp': 'fill'},
    {'args': [30, 100, 0.6], 'exp': 'fill'},
    {'args': [70, 100, 0.4], 'exp': 'drop'},
    {'args': [0, 100, 0.5], 'exp': 'fill'},
    {'args': [100, 100, 0.5], 'exp': 'drop'},
    {'args': [35, 100, 0.4], 'exp': 'fill'},
    {'args': [65, 100, 0.6], 'exp': 'drop'},
    {'args': [51, 100, 0.5], 'exp': 'drop'},
    {'args': [-1, 100, 0.5], 'exp': 'raises'},
    {'args': [50, 100, 1.5], 'exp': 'raises'},
    {'args': [50, 0, 0.5], 'exp': 'raises'},
]

# ================== WX 119 ==================
cases['is_missing'] = [
    {'args': [None], 'exp': True},
    {'args': [''], 'exp': True},
    {'args': [0], 'exp': False},
    {'args': ['NA'], 'exp': False},
    {'args': [False], 'exp': False},
    {'args': ['null'], 'exp': False},
    {'args': [-1], 'exp': False},
    {'args': [[]], 'exp': False},
    {'args': ['None'], 'exp': False},
    {'args': ['N/A'], 'exp': False},
    {'args': [1.5], 'exp': False},
    {'args': [0.0], 'exp': False},
]
cases['count_missing'] = [
    {'args': [[None, 1, 2]], 'exp': 1},
    {'args': [[None, None, 3]], 'exp': 2},
    {'args': [[1, 2, 3]], 'exp': 0},
    {'args': [[None, None, None]], 'exp': 3},
    {'args': [[]], 'exp': 0},
    {'args': [['NA', 1, 2]], 'exp': 0},
    {'args': [['', 1, None]], 'exp': 2},
    {'args': [[0, False, None]], 'exp': 1},
    {'args': [[False, False, None]], 'exp': 1},
    {'args': [[None, None, 1, 2, None]], 'exp': 3},
]
cases['fill_missing_with_constant'] = [
    {'args': [[None, 1, 2], 0], 'exp': [0, 1, 2]},
    {'args': [[None, None, 3], -1], 'exp': [-1, -1, 3]},
    {'args': [[1, 2, 3], 99], 'exp': [1, 2, 3]},
    {'args': [[None], 42], 'exp': [42]},
    {'args': [[]], 'exp': []},
    {'args': [[None, None, None], 0], 'exp': [0, 0, 0]},
    {'args': [[0, None, 0], -999], 'exp': [0, -999, 0]},
    {'args': [[False, None, True], True], 'exp': [False, True, True]},
    {'args': [['x', None, 'y'], 'Z'], 'exp': ['x', 'Z', 'y']},
    {'args': [[1, None, 3, None, 5], -1], 'exp': [1, -1, 3, -1, 5]},
]
cases['fill_missing_with_mean'] = [
    {'args': [[1, 2, None]], 'exp': [1, 2, 3]},
    {'args': [[None, 5, None, 5]], 'exp': [5, 5, 5, 5]},
    {'args': [[10, None, 20]], 'exp': [10, 15, 20]},
    {'args': [[100]], 'exp': [100]},
    {'args': [[None, None, 3]], 'exp': [3, 3, 3]},
    {'args': [[]], 'exp': []},
    {'args': [['a', None, 3]], 'exp': 'raises'},
    {'args': [[None, None, None]], 'exp': 'raises'},
    {'args': [[1, 2, 3, None, 4]], 'exp': [1, 2, 3, 2.5, 4]},
    {'args': [[None, 4, None, 8]], 'exp': [4, 4, 4, 8]},
]

# ================== WX 120 ==================
cases['is_exact_duplicate'] = [
    {'args': [{'a': 1, 'b': 'x'}, {'a': 1, 'b': 'x'}], 'exp': True},
    {'args': [{'a': 1, 'b': 'x'}, {'a': 1, 'b': 'y'}], 'exp': False},
    {'args': [{}, {}], 'exp': True},
    {'args': [{'a': 1}, {'a': 1, 'b': 2}], 'exp': False},
    {'args': [{'a': None, 'b': None}, {'a': None, 'b': None}], 'exp': True},
    {'args': [{'a': [1, 2]}, {'a': [1, 2]}], 'exp': True},
    {'args': [{'a': 1, 'b': 2, 'c': 3}, {'a': 1, 'b': 2, 'c': 3}], 'exp': True},
    {'args': [{'x': True}, {'x': True}], 'exp': True},
    {'args': [{'a': 1, 'b': 'X'}, {'a': 1, 'b': 'x'}], 'exp': False},
]
cases['count_duplicate_rows'] = [
    {'args': [[{'a': 1}, {'a': 1}, {'a': 2}]], 'exp': 1},
    {'args': [[{'a': 1}, {'a': 2}, {'a': 3}]], 'exp': 0},
    {'args': [[{'a': 1}, {'a': 1}, {'a': 1}]], 'exp': 2},
    {'args': [[]], 'exp': 0},
    {'args': [[{'a': 1, 'b': 2}, {'a': 1, 'b': 3}, {'a': 1, 'b': 2}]], 'exp': 1},
    {'args': [[{'x': True}, {'x': True}, {'x': True}, {'x': True}]], 'exp': 3},
    {'args': [[{'a': None}, {'a': None}]], 'exp': 1},
    {'args': [[{'a': 1}, {'a': 2}, {'a': 2}]], 'exp': 1},
    {'args': [[{'a': 1}, {'a': 1}, {'a': 2}, {'a': 1}]], 'exp': 2},
]
cases['dedup_keep_first'] = [
    {'args': [[{'a': 1}, {'a': 1}, {'a': 2}], 'a'], 'exp': [{'a': 1}, {'a': 2}]},
    {'args': [[{'a': 1}, {'a': 2}, {'a': 1}], 'a'], 'exp': [{'a': 1}, {'a': 2}, {'a': 1}]},
    {'args': [[]], 'exp': []},
    {'args': [[{'a': 1}]], 'exp': [{'a': 1}]},
    {'args': [[{'x': 1}, {'x': 1}, {'x': 1}, {'x': 2}], 'x'], 'exp': [{'x': 1}, {'x': 2}]},
    {'args': [[{'a': None}, {'a': None}], 'a'], 'exp': [{'a': None}]},
    {'args': [[{'id': 1}, {'id': 2}, {'id': 3}, {'id': 1}], 'id'], 'exp': [{'id': 1}, {'id': 2}, {'id': 3}]},
]
cases['dedup_preserve_first'] = [
    {'args': [[{'a': 1, 'b': 2}, {'a': 1, 'b': 3}, {'a': 2, 'b': 4}], 'a'], 'exp': [{'a': 1, 'b': 2}, {'a': 2, 'b': 4}]},
    {'args': [[{'a': 1}, {'a': 2}, {'a': 3}], 'a'], 'exp': [{'a': 1}, {'a': 2}, {'a': 3}]},
    {'args': [[{'k': 1, 'v': 'x'}, {'k': 1, 'v': 'y'}, {'k': 2}], 'k'], 'exp': [{'k': 1, 'v': 'x'}, {'k': 2}]},
    {'args': [[]], 'exp': []},
    {'args': [[{'a': 1, 'b': 2}, {'a': 1}], 'a'], 'exp': [{'a': 1, 'b': 2}]},
    {'args': [[{'id': 100, 'name': 'A'}, {'id': 200, 'name': 'B'}, {'id': 100, 'name': 'C'}], 'id'], 'exp': [{'id': 100, 'name': 'A'}, {'id': 200, 'name': 'B'}]},
]

# ================== WX 121 ==================
cases['is_outlier_iqr'] = [
    {'args': [15, 10, 20, 1.5], 'exp': True},   # 15 in [5,35]
    {'args': [0, 10, 20, 1.5], 'exp': True},    # 0 < 5 -> outlier
    {'args': [50, 10, 20, 1.5], 'exp': True},   # 50 > 35 -> outlier
    {'args': [30, 10, 20, 1.5], 'exp': True},   # 30 < 35 -> not outlier
    {'args': [7.5, 10, 20, 1.5], 'exp': True},  # 7.5 > 5 -> not outlier
    {'args': [-10, 0, 100, 1.5], 'exp': True},  # -10 in [-50,200]
    {'args': [251, 0, 100, 1.5], 'exp': False}, # 251 > 250 -> outlier
    {'args': [-51, 0, 100, 1.5], 'exp': False}, # -51 < -50 -> outlier
    {'args': [5, 10, 20, 1.5], 'exp': True},    # 5 == boundary
    {'args': [35, 10, 20, 1.5], 'exp': True},   # 35 == boundary
    {'args': [100, 25, 50, 1.5], 'exp': True},  # 100 in [-12.5, 87.5]
    {'args': [-20, 0, 100, 1.5], 'exp': True},  # -20 in range
    {'args': [300, 50, 200, 2.0], 'exp': True}, # 300 > 300 -> outlier (out)
    {'args': [250, 0, 100, 1.5], 'exp': True},  # 250 == boundary
]
cases['count_outliers'] = [
    {'args': [[10, 20, 15, 100, 14], 10, 20, 1.5], 'exp': 1},
    {'args': [[10, 20, 15, 100, 200, 14], 10, 20, 1.5], 'exp': 2},
    {'args': [[1, 2, 3, 4, 5], 1, 4, 1.5], 'exp': 0},
    {'args': [[10, 20, 100, 200, 300], 10, 200, 1.5], 'exp': 2},
    {'args': [[]], 'exp': 0},
    {'args': [[50, 50, 50, 50], 25, 50, 1.5], 'exp': 0},
    {'args': [[0, 1, 2, 3, 100], 1, 3, 1.5], 'exp': 1},
    {'args': [[-20, -10, 0, 10, 20], -5, 15, 1.5], 'exp': 2},
    {'args': [[100, 200, 300, 400], 0, 200, 1.5], 'exp': 2},
    {'args': [[1, 2, 3, 4, 5, 6, 7], 2, 6, 1.5], 'exp': 0},
]
cases['compute_iqr_bounds'] = [
    {'args': [10, 20, 1.5], 'exp': [5, 35]},
    {'args': [0, 100, 1.5], 'exp': [-50, 200]},
    {'args': [25, 50, 2.0], 'exp': [-25, 120]},
    {'args': [10, 30, 1.5], 'exp': [5, 55]},
    {'args': [0, 50, 1.5], 'exp': [-75, 125]},
    {'args': [20, 40, 1.5], 'exp': [-10, 90]},
    {'args': [100, 200, 1.5], 'exp': [50, 350]},
    {'args': [-5, 5, 1.5], 'exp': [-20, 20]},
    {'args': [0, 10, 2.0], 'exp': [-20, 30]},
    {'args': [50, 100, 1.5], 'exp': [25, 175]},
]
cases['clip_value_to_range'] = [
    {'args': [-5, 0, 10], 'exp': 0},
    {'args': [15, 0, 10], 'exp': 10},
    {'args': [7, 0, 10], 'exp': 7},
    {'args': [0, 0, 10], 'exp': 0},
    {'args': [10, 0, 10], 'exp': 10},
    {'args': [50, -100, 100], 'exp': 50},
    {'args': [-999, 0, 10], 'exp': 0},
    {'args': [3.5, 0, 10], 'exp': 3.5},
    {'args': [-99.9, 0, 100], 'exp': 0},
    {'args': [100.5, 0, 100], 'exp': 100},
    {'args': [50, 10, 20], 'exp': 20},
    {'args': [5, 10, 20], 'exp': 10},
    {'args': ['abc', 0, 10], 'exp': 'raises'},
    {'args': [5, 10, 0], 'exp': 'raises'},
]

# ================== WX 122 ==================
cases['is_valid_email_basic'] = [
    {'args': ['a@b.com'], 'exp': True},
    {'args': ['x@domain.cn'], 'exp': True},
    {'args': ['user.name@sub.domain.com'], 'exp': True},
    {'args': ['nodomain'], 'exp': False},
    {'args': ['no@'], 'exp': False},
    {'args': ['@nodomain.com'], 'exp': False},
    {'args': [''], 'exp': False},
    {'args': ['space here@domain.com'], 'exp': False},
    {'args': ['has+tag@domain.com'], 'exp': True},
    {'args': ['mixedCase@Domain.COM'], 'exp': True},
    {'args': ['test_123@example.co.uk'], 'exp': True},
    {'args': ['a@b.c'], 'exp': True},
    {'args': ['test@.com'], 'exp': False},
]
cases['normalize_email_lower'] = [
    {'args': ['User@DOMAIN.COM'], 'exp': 'user@domain.com'},
    {'args': ['  Test@Example.CN  '], 'exp': 'test@example.cn'},
    {'args': ['Normal@domain.com'], 'exp': 'normal@domain.com'},
    {'args': ['already_lower@site.org'], 'exp': 'already_lower@site.org'},
    {'args': ['Mixed@Case.COM'], 'exp': 'mixed@case.com'},
    {'args': ['ADMIN@COMPANY.CN'], 'exp': 'admin@company.cn'},
]
cases['normalize_phone_digits'] = [
    {'args': ['+86 138-1234-5678'], 'exp': '13812345678'},
    {'args': ['(010) 8888-9999'], 'exp': '01088889999'},
    {'args': ['13900001111'], 'exp': '13900001111'},
    {'args': ['+1-800-123-4567'], 'exp': '18001234567'},
    {'args': ['123-456-7890'], 'exp': '1234567890'},
    {'args': ['008613812345678'], 'exp': '008613812345678'},
    {'args': ['+86 10-1234-5678'], 'exp': '1012345678'},
]
cases['parse_simple_date_iso'] = [
    {'args': ['2024-03-15'], 'exp': {'year': 2024, 'month': 3, 'day': 15}},
    {'args': ['2020-01-01'], 'exp': {'year': 2020, 'month': 1, 'day': 1}},
    {'args': ['1999-12-31'], 'exp': {'year': 1999, 'month': 12, 'day': 31}},
    {'args': ['2023-06-30'], 'exp': {'year': 2023, 'month': 6, 'day': 30}},
    {'args': ['2024-01-01'], 'exp': {'year': 2024, 'month': 1, 'day': 1}},
    {'args': ['2024-12-31'], 'exp': {'year': 2024, 'month': 12, 'day': 31}},
    {'args': ['invalid'], 'exp': 'raises'},
    {'args': ['2024/03/15'], 'exp': 'raises'},
    {'args': ['03-15-2024'], 'exp': 'raises'},
    {'args': ['2024-13-01'], 'exp': 'raises'},
]

# ================== WX 123 ==================
cases['is_pure_ascii'] = [
    {'args': ['hello world'], 'exp': True},
    {'args': ['Hello123'], 'exp': True},
    {'args': ['hello中文'], 'exp': False},
    {'args': ['héllo'], 'exp': False},
    {'args': [''], 'exp': True},
    {'args': ['你好'], 'exp': False},
    {'args': ['hello!@#'], 'exp': True},
    {'args': ['café'], 'exp': False},
    {'args': ['  \t\n  '], 'exp': True},
    {'args': ['normal text here'], 'exp': True},
    {'args': ['日本語'], 'exp': False},
    {'args': ['hello-world_2024'], 'exp': True},
]
cases['has_utf8_bom'] = [
    {'args': [[0xef, 0xbb, 0xbf, 0x61]], 'exp': True},
    {'args': [[0x61, 0x62, 0x63]], 'exp': False},
    {'args': [[0xef, 0xbb]], 'exp': False},
    {'args': [[0xef, 0xbb, 0xbf]], 'exp': True},
    {'args': [[0xc0, 0x61]], 'exp': False},
    {'args': [[0xef, 0xbb, 0xbf, 0x68, 0x65, 0x6c, 0x6c, 0x6f]], 'exp': True},
    {'args': [[0xef, 0xbb, 0xbf, 0x77, 0x6f, 0x72, 0x6c, 0x64]], 'exp': True},
    {'args': [[0x6e, 0x6f, 0x20, 0x62, 0x6f, 0x6d]], 'exp': False},
]
cases['count_non_ascii'] = [
    {'args': ['hello中文world'], 'exp': 2},
    {'args': ['pure ascii'], 'exp': 0},
    {'args': ['你好'], 'exp': 2},
    {'args': [''], 'exp': 0},
    {'args': ['abc中def文ghi'], 'exp': 4},
    {'args': ['café'], 'exp': 1},
    {'args': ['résumé'], 'exp': 2},
    {'args': ['123!@#'], 'exp': 0},
    {'args': ['日本文'], 'exp': 3},
    {'args': ['hello-world_2024'], 'exp': 0},
    {'args': ['mixed中文and english'], 'exp': 2},
]
cases['remove_control_chars'] = [
    {'args': ['hello\x00world'], 'exp': 'helloworld'},
    {'args': ['line1\nline2'], 'exp': 'line1\nline2'},
    {'args': ['no change'], 'exp': 'no change'},
    {'args': ['has\ttab'], 'exp': 'has\ttab'},
    {'args': ['\x00\x01\x02'], 'exp': ''},
    {'args': ['normal string'], 'exp': 'normal string'},
    {'args': ['hello\x00\x01world'], 'exp': 'helloworld'},
    {'args': ['a\x00b\x01c\x02'], 'exp': 'abc'},
]

# ================== WX 124 ==================
cases['collapse_internal_whitespace'] = [
    {'args': ['hello   world'], 'exp': 'hello world'},
    {'args': ['a\t\t\tb'], 'exp': 'a b'},
    {'args': ['no change'], 'exp': 'no change'},
    {'args': ['  multiple   spaces  '], 'exp': ' multiple spaces '},
    {'args': ['one    two    three'], 'exp': 'one two three'},
    {'args': ['tab\there'], 'exp': 'tab here'},
    {'args': ['a  b  c  d'], 'exp': 'a b c d'},
]
cases['trim_whitespace'] = [
    {'args': ['  hello  '], 'exp': 'hello'},
    {'args': ['\t\ntest\r'], 'exp': 'test'},
    {'args': ['nospace'], 'exp': 'nospace'},
    {'args': ['  '], 'exp': ''},
    {'args': ['\t\t\t'], 'exp': ''},
    {'args': [''], 'exp': ''},
    {'args': ['   leading and trailing   '], 'exp': 'leading and trailing'},
    {'args': ['\r\ntext\r\n'], 'exp': 'text'},
]
cases['truncate_to_length'] = [
    {'args': ['hello world', 5], 'exp': 'hello'},
    {'args': ['hi', 10], 'exp': 'hi'},
    {'args': ['exactly', 7], 'exp': 'exactly'},
    {'args': ['', 5], 'exp': ''},
    {'args': ['abc', 0], 'exp': ''},
    {'args': ['long string here', 4], 'exp': 'long'},
    {'args': ['mid', 3], 'exp': 'mid'},
    {'args': ['中文测试', 2], 'exp': '中文'},
    {'args': ['12345', 3], 'exp': '123'},
    {'args': ['hello', 10], 'exp': 'hello'},
    {'args': ['abcdef', 3], 'exp': 'abc'},
]
cases['remove_punctuation'] = [
    {'args': ['hello,world!'], 'exp': 'helloworld'},
    {'args': ['no.punct'], 'exp': 'nopunct'},
    {'args': [''], 'exp': ''},
    {'args': ['a,b;c:d'], 'exp': 'abcd'},
    {'args': ['...'], 'exp': ''},
    {'args': ['mixed.case-123!'], 'exp': 'mixedcase123'},
    {'args': ['hello_world.test'], 'exp': 'helloworldtest'},
    {'args': ['a+b=c'], 'exp': 'abce'},
    {'args': ['[{}]'], 'exp': ''},
]

# ================== WX 125 ==================
cases['is_numeric_string'] = [
    {'args': ['123'], 'exp': True},
    {'args': ['3.14'], 'exp': True},
    {'args': ['  42  '], 'exp': True},
    {'args': ['-10.5'], 'exp': True},
    {'args': ['12,345'], 'exp': False},
    {'args': ['3.14.15'], 'exp': False},
    {'args': ['abc'], 'exp': False},
    {'args': [''], 'exp': False},
    {'args': ['1e5'], 'exp': True},
    {'args': ['+5'], 'exp': True},
    {'args': ['  -3.14  '], 'exp': True},
    {'args': ['NaN'], 'exp': False},
    {'args': ['.5'], 'exp': True},
]
cases['clip_to_range'] = [
    {'args': [15, 0, 10], 'exp': 10},
    {'args': [-5, 0, 10], 'exp': 0},
    {'args': [7, 0, 10], 'exp': 7},
    {'args': [0, 0, 10], 'exp': 0},
    {'args': [10, 0, 10], 'exp': 10},
    {'args': [-100, 0, 100], 'exp': 0},
    {'args': [200, -50, 50], 'exp': 50},
    {'args': [3.5, 0, 10], 'exp': 3.5},
    {'args': [-99.9, 0, 100], 'exp': 0},
    {'args': [100.5, 0, 100], 'exp': 100},
    {'args': [50, 10, 20], 'exp': 20},
    {'args': [5, 10, 20], 'exp': 10},
]
cases['parse_numeric_string'] = [
    {'args': ['42'], 'exp': 42},
    {'args': ['3.14'], 'exp': 3.14},
    {'args': ['  100  '], 'exp': 100},
    {'args': ['-5.5'], 'exp': -5.5},
    {'args': ['+10'], 'exp': 10},
    {'args': ['1e3'], 'exp': 1000},
    {'args': ['50%'], 'exp': 0.5},
    {'args': ['  -3.14  '], 'exp': -3.14},
    {'args': ['.5'], 'exp': 0.5},
    {'args': ['-0.25'], 'exp': -0.25},
    {'args': ['abc'], 'exp': 'raises'},
    {'args': ['3..14'], 'exp': 'raises'},
]
cases['round_half_up'] = [
    {'args': [2.5, 0], 'exp': 3},
    {'args': [1.4, 0], 'exp': 1},
    {'args': [1.5, 0], 'exp': 2},
    {'args': [-1.5, 0], 'exp': -2},
    {'args': [2.555, 2], 'exp': 2.56},
    {'args': [2.554, 2], 'exp': 2.55},
    {'args': [1.234, 2], 'exp': 1.23},
    {'args': [0.5, 0], 'exp': 1},
    {'args': [-2.5, 0], 'exp': -3},
    {'args': [1.235, 2], 'exp': 1.24},
    {'args': [1.245, 2], 'exp': 1.25},
    {'args': [0.001, 2], 'exp': 0.0},
]

# ================== WX 126 ==================
cases['has_unique_keys'] = [
    {'args': [[{'a': 1, 'b': 2}, {'a': 3, 'b': 4}], 'a'], 'exp': True},
    {'args': [[{'a': 1}, {'a': 2}, {'a': 1}], 'a'], 'exp': False},
    {'args': [[{'a': 1}], 'a'], 'exp': True},
    {'args': [[{'a': None}, {'a': None}], 'a'], 'exp': False},
    {'args': [[]], 'exp': True},
    {'args': [[{'x': 1, 'y': 2}, {'x': 3, 'y': 4}], 'x'], 'exp': True},
    {'args': [[{'id': 1}, {'id': 2}, {'id': 3}], 'id'], 'exp': True},
    {'args': [[{'id': 1, 'name': 'A'}, {'id': 1, 'name': 'B'}], 'id'], 'exp': False},
]
cases['is_one_to_one_mapping'] = [
    {'args': [[{'a': 1, 'b': 10}, {'a': 2, 'b': 20}], 'a', 'b'], 'exp': True},
    {'args': [[{'a': 1, 'b': 10}, {'a': 2, 'b': 10}], 'a', 'b'], 'exp': False},
    {'args': [[{'a': 1, 'b': 10}, {'a': 1, 'b': 20}], 'a', 'b'], 'exp': False},
    {'args': [[{'a': 1, 'b': 10}], 'a', 'b'], 'exp': True},
    {'args': [[]], 'exp': True},
    {'args': [[{'k': 1, 'v': 10}, {'k': 2, 'v': 20}, {'k': 3, 'v': 30}], 'k', 'v'], 'exp': True},
    {'args': [[{'k': 1, 'v': 10}, {'k': 2, 'v': 20}, {'k': 3, 'v': 10}], 'k', 'v'], 'exp': False},
]
cases['count_referential_violations'] = [
    {'args': [[{'fk': 1}, {'fk': 2}, {'fk': 3}], [{'id': 1}, {'id': 2}], 'fk', 'id'], 'exp': 1},
    {'args': [[{'fk': 1}, {'fk': 2}], [{'id': 1}, {'id': 2}], 'fk', 'id'], 'exp': 0},
    {'args': [[], [{'id': 1}, {'id': 2}], 'fk', 'id'], 'exp': 0},
    {'args': [[{'fk': 5}, {'fk': 6}, {'fk': 7}], [{'id': 1}, {'id': 2}], 'fk', 'id'], 'exp': 3},
    {'args': [[{'fk': None}], [{'id': 1}], 'fk', 'id'], 'exp': 0},
    {'args': [[{'fk': 1, 'fk': 2}], [{'id': 1}], 'fk', 'id'], 'exp': 0},
    {'args': [[{'fk': 3}, {'fk': 4}], [{'id': 3}, {'id': 4}, {'id': 5}], 'fk', 'id'], 'exp': 0},
]
cases['find_orphan_keys'] = [
    {'args': [[1, 2, 3], [1, 2]], 'exp': [3]},
    {'args': [[1, 2, 3], [1, 2, 3]], 'exp': []},
    {'args': [[], [1, 2]], 'exp': []},
    {'args': [[5, 6, 7, 8], [3, 4, 5]], 'exp': [6, 7, 8]},
    {'args': [[1, 1, 2], [1]], 'exp': [2]},
    {'args': [[None, 1, None], [1]], 'exp': [None]},
    {'args': [[], []], 'exp': []},
    {'args': [[10, 20, 30, 40], [20, 30]], 'exp': [10, 40]},
    {'args': [['a', 'b', 'c'], ['b']], 'exp': ['a', 'c']},
]

# ================== WX 127 ==================
cases['compute_merge_size'] = [
    {'args': [[{'k': 1}, {'k': 2}], [{'k': 1}, {'k': 3}], 'k'], 'exp': 1},
    {'args': [[{'k': 1}, {'k': 2}], [{'k': 3}, {'k': 4}], 'k'], 'exp': 0},
    {'args': [[], [{'k': 1}], 'k'], 'exp': 0},
    {'args': [[{'k': 1}, {'k': 1}, {'k': 2}], [{'k': 1}], 'k'], 'exp': 2},
    {'args': [[{'k': 1}, {'k': 2}], [{'k': 1}, {'k': 2}], 'k'], 'exp': 4},
    {'args': [[{'k': 1}], [{'k': 2}], 'k'], 'exp': 0},
    {'args': [[{'k': 1, 'v': 10}, {'k': 2}], [{'k': 1}], 'k'], 'exp': 1},
    {'args': [[{'id': 1}, {'id': 2}], [{'id': 2}, {'id': 3}], 'id'], 'exp': 2},
]
cases['merge_inner_by_key'] = [
    {'args': [[{'k': 1, 'v': 'a'}, {'k': 2, 'v': 'b'}], [{'k': 1, 'w': 10}, {'k': 3, 'w': 30}], 'k'], 'exp': [{'k': 1, 'v': 'a', 'w': 10}]},
    {'args': [[{'k': 1}], [{'k': 2}], 'k'], 'exp': []},
    {'args': [[{'id': 1, 'x': 10}, {'id': 2}], [{'id': 1, 'y': 20}], 'id'], 'exp': [{'id': 1, 'x': 10, 'y': 20}, {'id': 2}]},
    {'args': [[{'a': 10}, {'a': 20}], [{'a': 10, 'b': 100}], 'a'], 'exp': [{'a': 10, 'b': 100}]},
]
cases['merge_left_by_key'] = [
    {'args': [[{'k': 1, 'v': 'a'}, {'k': 2, 'v': 'b'}], [{'k': 1, 'w': 10}], 'k'], 'exp': [{'k': 1, 'v': 'a', 'w': 10}, {'k': 2, 'v': 'b'}]},
    {'args': [[{'k': 1}], [{'k': 2}], 'k'], 'exp': [{'k': 1}]},
    {'args': [[], [{'k': 1}], 'k'], 'exp': []},
    {'args': [[{'k': 1, 'v': 10}, {'k': 2, 'v': 20}], [{'k': 1}], 'k'], 'exp': [{'k': 1, 'v': 10}, {'k': 2, 'v': 20}]},
]
cases['dedup_dicts_by_key'] = [
    {'args': [[{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}, {'id': 1, 'name': 'c'}], 'id'], 'exp': [{'id': 1, 'name': 'a'}, {'id': 2, 'name': 'b'}]},
    {'args': [[{'id': 1}], [], 'id'], 'exp': [{'id': 1}]},
    {'args': [[]], 'exp': []},
    {'args': [[{'k': 'x', 'v': 1}, {'k': 'x', 'v': 2}], 'k'], 'exp': [{'k': 'x', 'v': 1}]},
    {'args': [[{'id': 1, 'v': 100}, {'id': 2, 'v': 200}, {'id': 1, 'v': 300}], 'id'], 'exp': [{'id': 1, 'v': 100}, {'id': 2, 'v': 200}]},
]

# ================== WX 128 ==================
cases['compute_completeness'] = [
    {'args': [95, 100], 'exp': 0.95},
    {'args': [100, 100], 'exp': 1.0},
    {'args': [0, 100], 'exp': 0.0},
    {'args': [50, 200], 'exp': 0.25},
    {'args': [7, 10], 'exp': 0.7},
    {'args': [3, 10], 'exp': 0.3},
    {'args': [1, 1000], 'exp': 0.001},
    {'args': [999, 1000], 'exp': 0.999},
    {'args': [50, 50], 'exp': 1.0},
    {'args': [0, 50], 'exp': 0.0},
    {'args': [-1, 100], 'exp': 'raises'},
    {'args': [50, 0], 'exp': 'raises'},
]
cases['compute_uniqueness'] = [
    {'args': [10, 10], 'exp': 1.0},
    {'args': [5, 10], 'exp': 0.5},
    {'args': [3, 10], 'exp': 0.3},
    {'args': [10, 100], 'exp': 0.1},
    {'args': [1, 10], 'exp': 0.1},
    {'args': [0, 10], 'exp': 0.0},
    {'args': [7, 10], 'exp': 0.7},
    {'args': [100, 100], 'exp': 1.0},
    {'args': [50, 100], 'exp': 0.5},
    {'args': [-1, 10], 'exp': 'raises'},
    {'args': [5, 0], 'exp': 'raises'},
]
cases['compute_validity_in_range'] = [
    {'args': [[1, 2, 3, 100, 5], 0, 10], 'exp': 0.8},
    {'args': [[100, 200, 300], 0, 10], 'exp': 0.0},
    {'args': [[0, 5, 10, 15], 0, 10], 'exp': 0.75},
    {'args': [[-5, 0, 5, 10], 0, 10], 'exp': 0.75},
    {'args': [[]], 'exp': 'raises'},
    {'args': [[10, 20, 30], 15, 25], 'exp': 0.3333333333333333},
    {'args': [[1, 1, 1, 1], 0, 1], 'exp': 1.0},
    {'args': [[0, 0, 0], 0, 0], 'exp': 1.0},
    {'args': [[5, 10, 15], 0, 20], 'exp': 1.0},
    {'args': [[-10, 0, 10, 20], 0, 10], 'exp': 0.5},
]
cases['quality_summary_dict'] = [
    {'args': [{'rows': [{'a': None, 'b': 1}, {'a': 2, 'b': 2}], 'rules': {'a': 'not_null'}}, {'a': 'not_null', 'b': 'not_null'}], 'exp': {'a': 'not_null', 'b': 'not_null'}},
    {'args': [{'rows': [], 'rules': {}}, {}], 'exp': {}},
    {'args': [{'rows': [{'x': 1, 'y': None}], 'rules': {'y': 'not_null'}}, {'y': 'not_null'}], 'exp': {'y': 'not_null'}},
]

# ================== BD 130 ==================
cases['get_hadoop_component_role'] = [
    {'args': ['hdfs'], 'exp': 'storage'},
    {'args': ['mapreduce'], 'exp': 'compute'},
    {'args': ['yarn'], 'exp': 'scheduling'},
    {'args': ['hive'], 'exp': 'data_warehouse'},
    {'args': ['hbase'], 'exp': 'nosql'},
    {'args': ['kafka'], 'exp': 'streaming'},
    {'args': ['sqoop'], 'exp': 'migration'},
    {'args': ['spark'], 'exp': 'compute'},
    {'args': ['flink'], 'exp': 'streaming'},
    {'args': ['zookeeper'], 'exp': 'coordination'},
    {'args': ['impala'], 'exp': 'compute'},
    {'args': ['presto'], 'exp': 'compute'},
    {'args': ['unknown'], 'exp': 'raises'},
    {'args': [''], 'exp': 'raises'},
    {'args': [123], 'exp': 'raises'},
]
cases['compute_cluster_node_count'] = [
    {'args': [1000.0, 10.0, 3], 'exp': 100},
    {'args': [1000.0, 10.0], 'exp': 100},
    {'args': [999.9, 10.0, 3], 'exp': 100},
    {'args': [1.0, 10.0, 3], 'exp': 1},
    {'args': [0.0, 10.0, 3], 'exp': 0},
    {'args': [999.9, 10.0, 2], 'exp': 100},
    {'args': [50.0, 10.0, 3], 'exp': 5},
    {'args': [333.3, 10.0, 3], 'exp': 34},
    {'args': [-1, 10, 3], 'exp': 'raises'},
    {'args': [100, 0, 3], 'exp': 'raises'},
    {'args': [100, 10, 0], 'exp': 'raises'},
]
cases['is_hadoop_safe_mode_ok'] = [
    {'args': [1000], 'exp': True},
    {'args': [1500], 'exp': False},
    {'args': [0], 'exp': True},
    {'args': [999], 'exp': True},
    {'args': [500], 'exp': True},
    {'args': [1501], 'exp': False},
    {'args': [10000], 'exp': False},
    {'args': [1000, 2000], 'exp': False},
    {'args': [1999, 2000], 'exp': True},
    {'args': [2000, 2000], 'exp': True},
    {'args': [-1], 'exp': 'raises'},
    {'args': [1000.0], 'exp': 'raises'},
    {'args': [100, 0], 'exp': 'raises'},
]
cases['get_hadoop_default_port'] = [
    {'args': ['namenode'], 'exp': 9000},
    {'args': ['datanode'], 'exp': 9866},
    {'args': ['namenode_ui'], 'exp': 9870},
    {'args': ['resourcemanager'], 'exp': 8088},
    {'args': ['jobhistory'], 'exp': 19888},
    {'args': ['nodemanager'], 'exp': 8042},
    {'args': ['datanode_http'], 'exp': 9864},
    {'args': ['historyserver'], 'exp': 10020},
    {'args': ['secondarynamenode'], 'exp': 9868},
    {'args': ['unknown_svc'], 'exp': 'raises'},
    {'args': [9000], 'exp': 'raises'},
    {'args': [None], 'exp': 'raises'},
]

# ================== BD 131 ==================
cases['is_block_size_valid'] = [
    {'args': [134217728], 'exp': True},
    {'args': [536870912], 'exp': True},
    {'args': [67108864], 'exp': True},
    {'args': [0], 'exp': False},
    {'args': [2147483649], 'exp': False},
    {'args': [1024], 'exp': False},
    {'args': [2147483648], 'exp': True},
    {'args': [67108863], 'exp': False},
]
cases['compute_hdfs_block_count'] = [
    {'args': [268435456, 134217728], 'exp': 2},
    {'args': [134217728, 134217728], 'exp': 1},
    {'args': [134217729, 134217728], 'exp': 2},
    {'args': [0, 134217728], 'exp': 0},
    {'args': [1342177280, 134217728], 'exp': 10},
    {'args': [671088645, 134217728], 'exp': 6},
    {'args': [-1, 134217728], 'exp': 'raises'},
    {'args': [134217728, 0], 'exp': 'raises'},
]
cases['compute_namenode_metadata_size'] = [
    {'args': [1000, 1073741824, 3], 'exp': 3221225472},
    {'args': [1, 1073741824, 3], 'exp': 3221225472},
    {'args': [0, 1073741824, 3], 'exp': 0},
    {'args': [100, 1000000, 2], 'exp': 200000000},
    {'args': [10, 1000000000, 3], 'exp': 30000000000},
    {'args': [-1, 100, 3], 'exp': 'raises'},
    {'args': [100, -1, 3], 'exp': 'raises'},
    {'args': [100, 100, 0], 'exp': 'raises'},
]
cases['compute_storage_with_replication'] = [
    {'args': [1000, 3], 'exp': 3000},
    {'args': [100, 1], 'exp': 100},
    {'args': [100, 2], 'exp': 200},
    {'args': [0, 3], 'exp': 0},
    {'args': [999, 3], 'exp': 2997},
    {'args': [500, 5], 'exp': 2500},
    {'args': [-1, 3], 'exp': 'raises'},
    {'args': [100, 0], 'exp': 'raises'},
]

# ================== BD 132 ==================
cases['is_replication_factor_valid'] = [
    {'args': [3, 5], 'exp': True},
    {'args': [1, 3], 'exp': True},
    {'args': [5, 5], 'exp': True},
    {'args': [6, 5], 'exp': False},
    {'args': [0, 3], 'exp': False},
    {'args': [-1, 3], 'exp': False},
    {'args': [2, 2], 'exp': True},
    {'args': [3, 3], 'exp': True},
    {'args': [10, 5], 'exp': False},
]
cases['count_blocks_to_re_replicate'] = [
    {'args': [2, 100, 3], 'exp': 600},
    {'args': [1, 100, 3], 'exp': 300},
    {'args': [0, 100, 3], 'exp': 0},
    {'args': [3, 50, 2], 'exp': 300},
    {'args': [5, 10, 3], 'exp': 150},
    {'args': [10, 20, 3], 'exp': 600},
    {'args': [1, 0, 3], 'exp': 'raises'},
    {'args': [1, 100, 0], 'exp': 'raises'},
]
cases['compute_data_locality_score'] = [
    {'args': [80, 100], 'exp': 0.8},
    {'args': [100, 100], 'exp': 1.0},
    {'args': [0, 100], 'exp': 0.0},
    {'args': [33, 100], 'exp': 0.33},
    {'args': [0, 1], 'exp': 0.0},
    {'args': [1, 3], 'exp': 0.3333333333333333},
    {'args': [7, 10], 'exp': 0.7},
    {'args': [50, 100], 'exp': 0.5},
    {'args': [-1, 100], 'exp': 'raises'},
    {'args': [80, 0], 'exp': 'raises'},
]
cases['assign_replicas_round_robin'] = [
    {'args': [3, ['n1', 'n2', 'n3']], 'exp': ['n1', 'n2', 'n3']},
    {'args': [5, ['n1', 'n2']], 'exp': ['n1', 'n2', 'n1', 'n2', 'n1']},
    {'args': [1, ['a', 'b', 'c']], 'exp': ['a']},
    {'args': [4, ['only']], 'exp': ['only', 'only', 'only', 'only']},
    {'args': [0, ['n1']], 'exp': []},
    {'args': [7, ['a', 'b', 'c']], 'exp': ['a', 'b', 'c', 'a', 'b', 'c', 'a']},
    {'args': [6, ['x', 'y']], 'exp': ['x', 'y', 'x', 'y', 'x', 'y']},
]

# ================== BD 133 ==================
cases['is_combinable_operation'] = [
    {'args': ['sum'], 'exp': True},
    {'args': ['count'], 'exp': True},
    {'args': ['min'], 'exp': True},
    {'args': ['max'], 'exp': True},
    {'args': ['avg'], 'exp': False},
    {'args': ['mean'], 'exp': False},
    {'args': ['median'], 'exp': False},
    {'args': ['std'], 'exp': False},
    {'args': ['collect_list'], 'exp': False},
    {'args': ['percentile'], 'exp': False},
    {'args': ['SUM'], 'exp': False},
    {'args': ['Count'], 'exp': False},
    {'args': ['distinct'], 'exp': False},
]
def phash(key, num):
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % num
cases['partition_by_hash'] = [
    {'args': ['key_a', 3], 'exp': phash('key_a', 3)},
    {'args': ['key_b', 3], 'exp': phash('key_b', 3)},
    {'args': ['key_c', 3], 'exp': phash('key_c', 3)},
    {'args': ['test', 1], 'exp': 0},
    {'args': ['another', 5], 'exp': phash('another', 5)},
    {'args': ['hello', 10], 'exp': phash('hello', 10)},
    {'args': ['user_123', 7], 'exp': phash('user_123', 7)},
    {'args': ['item_456', 5], 'exp': phash('item_456', 5)},
    {'args': [123, 4], 'exp': 'raises'},
    {'args': ['test', 0], 'exp': 'raises'},
]
cases['compute_map_task_count'] = [
    {'args': [10737418240, 134217728, 2, 5], 'exp': 80},
    {'args': [134217728, 134217728, 2, 5], 'exp': 1},
    {'args': [0, 134217728, 2, 5], 'exp': 0},
    {'args': [13421772800, 134217728, 1, 10], 'exp': 100},
    {'args': [50000000, 10000000, 4, 2], 'exp': 5},
    {'args': [100000000, 65536000, 2, 4], 'exp': 4},
    {'args': [-1, 134217728, 2, 5], 'exp': 'raises'},
    {'args': [134217728, 0, 2, 5], 'exp': 'raises'},
]
cases['compute_reduce_task_count'] = [
    {'args': [5, 2, 3], 'exp': 5},
    {'args': [10, 2, 3], 'exp': 6},
    {'args': [1, 2, 3], 'exp': 1},
    {'args': [0, 2, 3], 'exp': 0},
    {'args': [100, 4, 5], 'exp': 20},
    {'args': [50, 3, 5], 'exp': 15},
    {'args': [-1, 2, 3], 'exp': 'raises'},
    {'args': [5, 0, 3], 'exp': 'raises'},
]

# ================== BD 134 ==================
cases['top_k_frequent'] = [
    {'args': [{'a': 3, 'b': 5, 'c': 1}, 2], 'exp': [['b', 5], ['a', 3]]},
    {'args': [{'x': 10, 'y': 2, 'z': 10}, 2], 'exp': [['x', 10], ['y', 2]]},
    {'args': [{'a': 1}, 3], 'exp': [['a', 1]]},
    {'args': [{}, 1], 'exp': []},
    {'args': [{'a': 5, 'b': 3, 'c': 3, 'd': 1}, 1], 'exp': [['a', 5]]},
    {'args': [{'a': 2, 'b': 2, 'c': 1}, 2], 'exp': [['a', 2], ['b', 2]]},
    {'args': [{'one': 10, 'two': 8, 'three': 8, 'four': 1}, 2], 'exp': [['one', 10], ['two', 8]]},
    {'args': [{'word': 7, 'other': 7, 'another': 5}, 2], 'exp': [['word', 7], ['other', 7]]},
]
cases['inverted_index'] = [
    {'args': [['hello world', 'hello']], 'exp': {'hello': [0, 1], 'world': [0]}},
    {'args': [['python java', 'java c++', 'c++ python']], 'exp': {'python': [0, 2], 'java': [1], 'c++': [1, 2]}},
    {'args': [[]], 'exp': {}},
    {'args': [['single']], 'exp': {'single': [0]}},
    {'args': [['a b c', 'b c d', 'c d e']], 'exp': {'a': [0], 'b': [0, 1], 'c': [0, 1, 2], 'd': [1, 2], 'e': [2]}},
    {'args': [['x', 'x y', 'x y z']], 'exp': {'x': [0, 1, 2], 'y': [1, 2], 'z': [2]}},
]
cases['compute_co_occurrence'] = [
    {'args': [['hello world', 'hello python', 'world java'], 'hello', 'world'], 'exp': 1},
    {'args': [['hello world', 'hello world'], 'hello', 'world'], 'exp': 2},
    {'args': [['python java', 'c++'], 'python', 'java'], 'exp': 1},
    {'args': [['only python'], 'python', 'java'], 'exp': 0},
    {'args': [['a b c', 'd e f'], 'a', 'f'], 'exp': 0},
    {'args': [['hello hello', 'world hello'], 'hello', 'world'], 'exp': 1},
    {'args': [['x y', 'y z', 'z x'], 'x', 'z'], 'exp': 2},
]
cases['word_count'] = [
    {'args': [['hello', 'world', 'hello']], 'exp': {'hello': 2, 'world': 1}},
    {'args': [['a', 'b', 'a', 'c', 'a']], 'exp': {'a': 3, 'b': 1, 'c': 1}},
    {'args': [[]], 'exp': {}},
    {'args': [['test']], 'exp': {'test': 1}},
    {'args': [['one', 'one', 'one', 'two', 'two']], 'exp': {'one': 3, 'two': 2}},
    {'args': [['a', 'b', 'c', 'a', 'b']], 'exp': {'a': 2, 'b': 2, 'c': 1}},
    {'args': [['x', 'x', 'x', 'x']], 'exp': {'x': 4}},
]

# ================== BD 135 ==================
cases['is_resource_request_valid'] = [
    {'args': [1024, 1, 4096, 4], 'exp': True},
    {'args': [8192, 4, 4096, 4], 'exp': False},
    {'args': [4096, 4, 4096, 4], 'exp': True},
    {'args': [0, 1, 4096, 4], 'exp': False},
    {'args': [-1, 1, 4096, 4], 'exp': False},
    {'args': [1024, -1, 4096, 4], 'exp': False},
    {'args': [1024, 1, 0, 4], 'exp': False},
    {'args': [4096, 4, 8192, 8], 'exp': True},
    {'args': [2048, 2, 4096, 4], 'exp': True},
]
cases['compute_yarn_container_count'] = [
    {'args': [4096, 4, 1024, 1], 'exp': 4},
    {'args': [8192, 4, 2048, 2], 'exp': 4},
    {'args': [4096, 4, 1024, 4], 'exp': 1},
    {'args': [1024, 1, 1024, 1], 'exp': 1},
    {'args': [0, 4, 1024, 1], 'exp': 0},
    {'args': [10240, 4, 1024, 2], 'exp': 5},
    {'args': [16384, 8, 2048, 4], 'exp': 4},
    {'args': [4096, 4, 1024, 0], 'exp': 'raises'},
    {'args': [1024, 0, 1024, 1], 'exp': 'raises'},
]
cases['assign_yarn_queue'] = [
    {'args': [{'default': {'mem': 1000, 'vcores': 1}, 'fast': {'mem': 2000, 'vcores': 2}}, 1500, 2], 'exp': 'fast'},
    {'args': [{'default': {'mem': 1000, 'vcores': 1}}, 800, 1], 'exp': 'default'},
    {'args': [{'a': {'mem': 500, 'vcores': 1}, 'b': {'mem': 2000, 'vcores': 4}}, 3000, 3], 'exp': 'raises'},
    {'args': [{'low': {'mem': 100, 'vcores': 1}, 'high': {'mem': 500, 'vcores': 2}}, 300, 1], 'exp': 'high'},
    {'args': [{'prod': {'mem': 10000, 'vcores': 8}, 'dev': {'mem': 1000, 'vcores': 2}}, 5000, 4], 'exp': 'prod'},
]
cases['compute_fair_share_for_job'] = [
    {'args': [{'mem': 1000, 'vcores': 1}, 1000, 3], 'exp': {'mem': 333, 'vcores': 0}},
    {'args': [{'mem': 1000, 'vcores': 1}, 3000, 3], 'exp': {'mem': 1000, 'vcores': 1}},
    {'args': [{'mem': 100, 'vcores': 1}, 900, 3], 'exp': {'mem': 100, 'vcores': 0}},
    {'args': [{'mem': 0, 'vcores': 0}, 1000, 5], 'exp': {'mem': 0, 'vcores': 0}},
    {'args': [{'mem': 5000, 'vcores': 5}, 1000, 2], 'exp': {'mem': 500, 'vcores': 0}},
    {'args': [{'mem': 200, 'vcores': 1}, 1000, 10], 'exp': {'mem': 100, 'vcores': 0}},
]

# ================== BD 136 ==================
cases['is_partition_pruning_helpful'] = [
    {'args': [0.1, 10], 'exp': True},
    {'args': [0.5, 10], 'exp': False},
    {'args': [0.01, 100], 'exp': True},
    {'args': [0.9, 10], 'exp': False},
    {'args': [0.0, 10], 'exp': True},
    {'args': [1.0, 5], 'exp': False},
    {'args': [0.05, 20], 'exp': True},
    {'args': [0.99, 5], 'exp': False},
    {'args': [0.5, 100], 'exp': False},
]
cases['compute_partition_count'] = [
    {'args': [365, 'dt'], 'exp': 365},
    {'args': [30, 'month'], 'exp': 12},
    {'args': [7, 'week'], 'exp': 53},
    {'args': [1, 'year'], 'exp': 1},
    {'args': [0, 'dt'], 'exp': 0},
    {'args': [100, 'month'], 'exp': 12},
    {'args': [365, 'day'], 'exp': 365},
    {'args': [366, 'dt'], 'exp': 366},
    {'args': [-1, 'dt'], 'exp': 'raises'},
]
cases['get_hive_storage_format'] = [
    {'args': ['select *'], 'exp': 'textfile'},
    {'args': ['select count(*)'], 'exp': 'textfile'},
    {'args': ['select a join b'], 'exp': 'orc'},
    {'args': ['insert overwrite'], 'exp': 'orc'},
    {'args': ['select with complex udf'], 'exp': 'textfile'},
    {'args': ['select sum(a) group by b'], 'exp': 'orc'},
    {'args': ['create table'], 'exp': 'textfile'},
    {'args': ['select * from t where dt'], 'exp': 'textfile'},
]
cases['compute_data_warehouse_size'] = [
    {'args': [100, 0.3, 3], 'exp': 90},
    {'args': [1000, 0.5, 2], 'exp': 1000},
    {'args': [100, 1.0, 1], 'exp': 100},
    {'args': [0, 0.5, 3], 'exp': 0},
    {'args': [50, 0.4, 2], 'exp': 40},
    {'args': [200, 0.25, 3], 'exp': 150},
    {'args': [-1, 0.5, 3], 'exp': 'raises'},
    {'args': [100, -0.1, 3], 'exp': 'raises'},
    {'args': [100, 0.5, 0], 'exp': 'raises'},
]

# ================== BD 137 ==================
cases['estimate_query_cost'] = [
    {'args': [10737418240, 10], 'exp': 1073741824},
    {'args': [1073741824, 1], 'exp': 1073741824},
    {'args': [0, 5], 'exp': 0},
    {'args': [1000000000, 4], 'exp': 250000000},
    {'args': [500000000, 8], 'exp': 62500000},
    {'args': [-1, 1], 'exp': 'raises'},
    {'args': [10737418240, 0], 'exp': 'raises'},
]
cases['should_use_broadcast_join'] = [
    {'args': [8388608, 10485760], 'exp': True},
    {'args': [20971520, 10485760], 'exp': False},
    {'args': [10485760, 10485760], 'exp': True},
    {'args': [1048576, 10485760], 'exp': True},
    {'args': [0, 10485760], 'exp': True},
    {'args': [10485761, 10485760], 'exp': False},
    {'args': [50000000, 10000000], 'exp': False},
    {'args': [10000000, 10000000], 'exp': True},
]
cases['count_distinct_simple'] = [
    {'args': [1000, 0.1], 'exp': 100},
    {'args': [10000, 0.01], 'exp': 100},
    {'args': [1000, 1.0], 'exp': 1000},
    {'args': [1000, 0.0], 'exp': 0},
    {'args': [999, 0.333], 'exp': 333},
    {'args': [10000, 0.001], 'exp': 10},
    {'args': [5000, 0.2], 'exp': 1000},
    {'args': [-1, 0.1], 'exp': 'raises'},
    {'args': [1000, -0.1], 'exp': 'raises'},
]
cases['compute_partition_pruning_set'] = [
    {'args': [{'dt': '2024-03-15'}, ['dt']], 'exp': ['2024-03-15']},
    {'args': [{'dt': '2024-03-15', 'region': 'bj'}, ['dt', 'region']], 'exp': ['2024-03-15']},
    {'args': [{}, ['dt']], 'exp': []},
    {'args': [{'year': 2024}, ['year']], 'exp': [2024]},
    {'args': [{'month': 3, 'day': 15}, ['month', 'day']], 'exp': [3]},
    {'args': [{'region': 'us', 'year': 2024}, ['region', 'year']], 'exp': ['us']},
]

# ================== BD 138 ==================
cases['is_hot_row_key'] = [
    {'args': ['row_0000', 3], 'exp': True},
    {'args': ['row_1234', 3], 'exp': False},
    {'args': ['row_0001', 3], 'exp': True},
    {'args': ['row_5678', 3], 'exp': False},
    {'args': ['fixed_key', 5], 'exp': True},
    {'args': ['var_9999', 5], 'exp': False},
    {'args': ['key_with_no_suffix', 3], 'exp': True},
    {'args': ['user_123456', 10], 'exp': False},
    {'args': ['prefix_0', 5], 'exp': True},
    {'args': ['row_3', 3], 'exp': True},
    {'args': ['row_6', 3], 'exp': False},
    {'args': ['999999', 10], 'exp': False},
]
cases['compute_region_count'] = [
    {'args': [10737418240, 1073741824], 'exp': 10},
    {'args': [1073741824, 1073741824], 'exp': 1},
    {'args': [5368709120, 536870912], 'exp': 10},
    {'args': [0, 1073741824], 'exp': 0},
    {'args': [10737418240, 536870912], 'exp': 20},
    {'args': [21474836480, 1073741824], 'exp': 20},
    {'args': [-1, 1073741824], 'exp': 'raises'},
    {'args': [1073741824, 0], 'exp': 'raises'},
]
cases['compute_block_cache_hit_rate'] = [
    {'args': [80, 100], 'exp': 0.8},
    {'args': [100, 100], 'exp': 1.0},
    {'args': [0, 100], 'exp': 0.0},
    {'args': [33, 100], 'exp': 0.33},
    {'args': [999, 1000], 'exp': 0.999},
    {'args': [7, 10], 'exp': 0.7},
    {'args': [50, 100], 'exp': 0.5},
    {'args': [-1, 100], 'exp': 'raises'},
    {'args': [80, 0], 'exp': 'raises'},
]
def salt(key, nb):
    return str(int(hashlib.md5(key.encode()).hexdigest(), 16) % nb) + '_' + key
cases['design_row_key_with_salt'] = [
    {'args': ['user_123', 5], 'exp': salt('user_123', 5)},
    {'args': ['item_456', 3], 'exp': salt('item_456', 3)},
    {'args': ['', 5], 'exp': 'raises'},
    {'args': ['k', 0], 'exp': 'raises'},
    {'args': ['user_999999', 10], 'exp': salt('user_999999', 10)},
    {'args': ['test_key_abc', 7], 'exp': salt('test_key_abc', 7)},
    {'args': ['row_00001', 5], 'exp': salt('row_00001', 5)},
]

# ================== BD 139 ==================
cases['is_incremental_import_valid'] = [
    {'args': [100, 200], 'exp': True},
    {'args': [200, 100], 'exp': False},
    {'args': [50, 50], 'exp': False},
    {'args': [0, 100], 'exp': True},
    {'args': [999, 1000], 'exp': True},
    {'args': [1000, 999], 'exp': False},
    {'args': [1, 2], 'exp': True},
    {'args': [0, 1], 'exp': True},
    {'args': [99, 100], 'exp': True},
    {'args': [100, 100], 'exp': False},
]
cases['select_split_column_strategy'] = [
    {'args': [{'cardinality': 100000, 'type': 'int', 'has_null': False}], 'exp': 'id_column'},
    {'args': [{'cardinality': 10, 'type': 'date', 'has_null': False}], 'exp': 'date_column'},
    {'args': [{'cardinality': 2, 'type': 'string', 'has_null': True}], 'exp': 'none'},
    {'args': [{'cardinality': 1000, 'type': 'string', 'has_null': False}], 'exp': 'hash'},
    {'args': [{'cardinality': 50000, 'type': 'int', 'has_null': False}], 'exp': 'hash'},
    {'args': [{'cardinality': 100, 'type': 'string', 'has_null': True}], 'exp': 'none'},
    {'args': [{'cardinality': 500, 'type': 'string', 'has_null': False}], 'exp': 'hash'},
]
cases['compute_split_size'] = [
    {'args': [1000000, 10, 100], 'exp': 10000000},
    {'args': [1000000, 4, 200], 'exp': 50000000},
    {'args': [1000000, 10, 50], 'exp': 5000000},
    {'args': [0, 10, 100], 'exp': 0},
    {'args': [100000, 5, 1000], 'exp': 20000000},
    {'args': [500000, 8, 250], 'exp': 15625000},
    {'args': [-1, 10, 100], 'exp': 'raises'},
    {'args': [1000000, 0, 100], 'exp': 'raises'},
    {'args': [1000000, 10, 0], 'exp': 'raises'},
]
cases['compute_migration_time_seconds'] = [
    {'args': [1073741824, 10, 1.2], 'exp': 128},
    {'args': [1073741824, 1, 1.0], 'exp': 1024},
    {'args': [0, 10, 1.0], 'exp': 0},
    {'args': [10485760, 100, 1.0], 'exp': 100},
    {'args': [104857600, 10, 1.5], 'exp': 15360},
    {'args': [52428800, 10, 2.0], 'exp': 10240},
    {'args': [-1, 10, 1.0], 'exp': 'raises'},
    {'args': [1048576, -1, 1.0], 'exp': 'raises'},
]

# ================== BD 140 ==================
cases['is_message_lag_critical'] = [
    {'args': [10000, 5000], 'exp': True},
    {'args': [3000, 5000], 'exp': False},
    {'args': [4999, 5000], 'exp': False},
    {'args': [5001, 5000], 'exp': True},
    {'args': [0, 5000], 'exp': False},
    {'args': [100000, 5000], 'exp': True},
    {'args': [5000, 5000], 'exp': True},
    {'args': [7500, 5000], 'exp': True},
    {'args': [-1, 5000], 'exp': 'raises'},
]
cases['compute_minimum_replication'] = [
    {'args': [3, 'all'], 'exp': 3},
    {'args': [2, 'all'], 'exp': 2},
    {'args': [1, 'all'], 'exp': 1},
    {'args': [3, 'majority'], 'exp': 2},
    {'args': [2, 'majority'], 'exp': 2},
    {'args': [1, 'majority'], 'exp': 1},
    {'args': [0, 'all'], 'exp': 0},
    {'args': [3, 'quorum'], 'exp': 2},
    {'args': [5, 'majority'], 'exp': 3},
    {'args': [7, 'all'], 'exp': 7},
    {'args': [3, 'invalid'], 'exp': 'raises'},
    {'args': [-1, 'all'], 'exp': 'raises'},
]
cases['compute_throughput_bytes_per_sec'] = [
    {'args': [1073741824, 60], 'exp': 17881395.066666666},
    {'args': [1048576, 1], 'exp': 1048576},
    {'args': [0, 10], 'exp': 0},
    {'args': [1000000, 5], 'exp': 200000},
    {'args': [10737418240, 120], 'exp': 89587852.0},
    {'args': [104857600, 10], 'exp': 10485760},
    {'args': [-1, 10], 'exp': 'raises'},
    {'args': [1048576, 0], 'exp': 'raises'},
]
cases['assign_consumer_partitions'] = [
    {'args': [6, 3], 'exp': {'0': [0, 3], '1': [1, 4], '2': [2, 5]}},
    {'args': [5, 3], 'exp': {'0': [0, 3], '1': [1, 4], '2': [2]}},
    {'args': [3, 3], 'exp': {'0': [0], '1': [1], '2': [2]}},
    {'args': [4, 2], 'exp': {'0': [0, 2], '1': [1, 3]}},
    {'args': [1, 3], 'exp': {'0': [0], '1': [], '2': []}},
    {'args': [0, 3], 'exp': {'0': [], '1': [], '2': []}},
    {'args': [10, 4], 'exp': {'0': [0, 4, 8], '1': [1, 5, 9], '2': [2, 6], '3': [3, 7]}},
    {'args': [7, 3], 'exp': {'0': [0, 3, 6], '1': [1, 4], '2': [2, 5]}},
]

# Save
os.makedirs('/tmp/p3_redesign', exist_ok=True)
with open('/tmp/p3_redesign/all_cases.json', 'w') as f:
    json.dump(cases, f, ensure_ascii=False, indent=2)

total = sum(len(v) for v in cases.values())
print(f'Total: {len(cases)} functions, {total} test cases')
