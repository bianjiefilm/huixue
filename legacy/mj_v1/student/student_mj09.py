"""关联规则挖掘 - 学生作答文件"""
import pandas as pd
import numpy as np
from typing import Dict, List


def support(df: pd.DataFrame, itemset: List[str]) -> float:
    """
    计算项集的支持度: 包含 itemset 中所有项的记录数 / 总记录数

    Returns:
        float: 支持度 (0~1)
    """
    pass


def confidence(df: pd.DataFrame, antecedent: List[str], consequent: List[str]) -> float:
    """
    计算关联规则的置信度: sup(antecedent ∪ consequent) / sup(antecedent)

    Returns:
        float: 置信度 (0~1)
    """
    pass


def lift(df: pd.DataFrame, antecedent: List[str], consequent: List[str]) -> float:
    """
    计算提升度: P(A∩B) / (P(A) * P(B))

    Returns:
        float: 提升度 (>1 表示正相关)
    """
    pass


def find_frequent_itemsets(transactions: List[List[str]], min_support: float) -> List[frozenset]:
    """
    Apriori 算法找频繁项集。

    Args:
        transactions: 事务列表,每个事务是商品列表
        min_support: 最小支持度阈值

    Returns:
        List[frozenset]: 满足最小支持度的项集列表
    """
    pass
