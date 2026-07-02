import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj09 import support, confidence, lift, find_frequent_itemsets
import pandas as pd

def test_support():
    df = pd.DataFrame({'item1': [True, True, False, True], 'item2': [True, True, True, False]})
    result = support(df, ['item1'])
    assert result is not None, "pass-only 不得分"
    assert 0 <= result <= 1

def test_confidence():
    df = pd.DataFrame({'A': [True, True, False], 'B': [True, False, True]})
    result = confidence(df, ['A'], ['B'])
    assert result is not None, "pass-only 不得分"
    assert 0 <= result <= 1

def test_lift():
    df = pd.DataFrame({'A': [True]*5 + [False]*5, 'B': [True]*5 + [True]*5})
    result = lift(df, ['A'], ['B'])
    assert result is not None, "pass-only 不得分"
    assert result > 0

def test_find_frequent_itemsets():
    transactions = [['牛奶', '面包'], ['牛奶', '鸡蛋'], ['面包', '鸡蛋'], ['牛奶', '面包', '鸡蛋']]
    result = find_frequent_itemsets(transactions, min_support=0.5)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, list)
