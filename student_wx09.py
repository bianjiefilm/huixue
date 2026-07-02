"""关系一致性校验 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List


def find_orphan_keys(child_keys: List, parent_keys: List) -> List:
    """
    返回 child_keys 中出现但 parent_keys 中没有的 key 列表 (按 child_keys 顺序)。
    若同一 orphan 在 child_keys 中出现多次, 全部保留 (含重复)。

    Args:
        child_keys: 子表 keys。
        parent_keys: 父表 keys。

    Returns:
        list: 孤儿 keys 列表。

    Raises:
        TypeError: 输入不是 list。
    """
    pass


def has_unique_keys(keys: List) -> bool:
    """
    判断 list 中所有元素是否互不相同。

    Args:
        keys: 任意 list。

    Returns:
        bool: 无重复 → True; 否则 False。空 list → True (vacuously)。

    Raises:
        TypeError: keys 不是 list。
    """
    pass


def count_referential_violations(child_keys: List, parent_keys: List) -> int:
    """
    计数 child_keys 中不在 parent_keys 的元素个数 (含重复)。

    Args:
        child_keys, parent_keys: list。

    Returns:
        int: 违反外键约束的子记录数。

    Raises:
        TypeError: 输入不是 list。
    """
    pass


def is_one_to_one_mapping(left: List, right: List) -> bool:
    """
    判断两个等长 list 是否构成 1-1 映射:
      - len(left) == len(right)
      - left 内部无重复
      - right 内部无重复

    Args:
        left, right: 两个 list。

    Returns:
        bool: 满足全部条件 → True; 否则 False。

    Raises:
        TypeError: 输入不是 list。
    """
    pass
