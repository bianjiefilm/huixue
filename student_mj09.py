"""关联规则挖掘 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Set


def compute_support(transactions: list, itemset: set) -> float:
    """
    计算项集 itemset 在 transactions 中的支持度。

    Args:
        transactions: list[set], 每个事务是一个项的集合。
        itemset: set, 待查项集。

    Returns:
        float: 支持度 [0, 1]。

    Raises:
        ValueError: transactions 空 / itemset 空。
        TypeError: 输入类型错误。
    """
    pass


def compute_confidence(transactions: list, antecedent: set, consequent: set) -> float:
    """
    计算规则 antecedent → consequent 的置信度。

    Returns:
        float: 置信度 [0, 1]。

    Raises:
        ValueError: transactions 空 / antecedent 空 / antecedent 支持度为 0。
        TypeError: 输入类型错误。
    """
    pass


def compute_lift(transactions: list, antecedent: set, consequent: set) -> float:
    """
    计算规则 antecedent → consequent 的提升度。

    Returns:
        float: lift, 大于 1 表示正相关, 等于 1 独立, 小于 1 负相关。

    Raises:
        ValueError: transactions 空 / antecedent 或 consequent 支持度为 0。
        TypeError: 输入类型错误。
    """
    pass


def find_frequent_itemsets(transactions: list, min_support: float) -> Set[frozenset]:
    """
    挖掘所有支持度 ≥ min_support 的频繁项集 (单项及多项)。

    Returns:
        set[frozenset]: 包含所有频繁项集 (注意是 set 容器, 不是 list);
                        空集不在结果中。

    Raises:
        ValueError: transactions 空 / min_support 越界 [0, 1]。
        TypeError: 输入类型错误。
    """
    pass
