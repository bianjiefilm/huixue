"""WX07 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_wx07 import (
    trim_whitespace,
    collapse_internal_whitespace,
    truncate_to_length,
    remove_punctuation,
)


# F1: trim_whitespace — input != output
def test_trim_spaces():
    assert trim_whitespace("  hello  ") == "hello"

def test_trim_tabs():
    assert trim_whitespace("\thello\t") == "hello"

def test_trim_newlines():
    assert trim_whitespace("\n\nhello\n") == "hello"

def test_trim_mixed():
    assert trim_whitespace(" \t\nhello\n\t ") == "hello"

def test_trim_full_width_space():
    """全角空格也去"""
    assert trim_whitespace("　hello　") == "hello"

def test_trim_internal_preserved():
    """内部空白保留: 'a b c' → 'a b c'"""
    assert trim_whitespace("  a b c  ") == "a b c"

def test_trim_raises_on_non_string():
    with pytest.raises(TypeError):
        trim_whitespace(123)


# F2: collapse_internal_whitespace — input != output for all
def test_collapse_double_space():
    assert collapse_internal_whitespace("a  b") == "a b"

def test_collapse_triple_space():
    assert collapse_internal_whitespace("a   b") == "a b"

def test_collapse_tab():
    assert collapse_internal_whitespace("a\tb") == "a b"

def test_collapse_newline():
    assert collapse_internal_whitespace("a\nb") == "a b"

def test_collapse_mixed():
    """混合空白 'a \\t \\n b' → 'a b'"""
    assert collapse_internal_whitespace("a \t \n b") == "a b"

def test_collapse_with_trim():
    """前后空白也清: '  a  b  ' → 'a b'"""
    assert collapse_internal_whitespace("  a  b  ") == "a b"

def test_collapse_three_words():
    assert collapse_internal_whitespace("hello   world   wide") == "hello world wide"

def test_collapse_raises_on_non_string():
    with pytest.raises(TypeError):
        collapse_internal_whitespace(123)


# F3: truncate_to_length
def test_truncate_short_unchanged():
    """短的不截"""
    assert truncate_to_length("hello", 10) == "hello"

def test_truncate_long():
    """长的截到 max_len"""
    assert truncate_to_length("hello world", 5) == "hello"

def test_truncate_exact_length():
    """长度等于 max_len 不变"""
    assert truncate_to_length("hello", 5) == "hello"

def test_truncate_to_3():
    assert truncate_to_length("hello", 3) == "hel"

def test_truncate_to_1():
    assert truncate_to_length("hello", 1) == "h"

def test_truncate_chinese():
    """中文 3 字符 max=2 → 取前 2 字符"""
    assert truncate_to_length("中文测试", 2) == "中文"

def test_truncate_to_zero():
    """boundary: max_len=0 → ''"""
    assert truncate_to_length("hello", 0) == ""

def test_truncate_raises_on_negative():
    with pytest.raises(ValueError):
        truncate_to_length("hello", -1)

def test_truncate_raises_on_non_string():
    with pytest.raises(TypeError):
        truncate_to_length(123, 5)


# F4: remove_punctuation
def test_punc_english():
    assert remove_punctuation("Hello, World!") == "Hello World"

def test_punc_question():
    assert remove_punctuation("What?") == "What"

def test_punc_chinese():
    assert remove_punctuation("你好，世界！") == "你好世界"

def test_punc_mixed():
    """混合英中标点"""
    assert remove_punctuation("Hi! 你好。") == "Hi 你好"

def test_punc_quotes():
    """引号也去"""
    assert remove_punctuation('"Quote" \'tick\'') == "Quote tick"

def test_punc_brackets():
    assert remove_punctuation("[a] (b) {c}") == "a b c"

def test_punc_no_punctuation():
    """无标点不变"""
    assert remove_punctuation("hello world") == "hello world"

def test_punc_raises_on_non_string():
    with pytest.raises(TypeError):
        remove_punctuation(123)
