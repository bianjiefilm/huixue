"""MapReduce 编程实战 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Dict, Tuple


def word_count(documents: List[str]) -> Dict[str, int]:
    """
    统计文档列表中每个 word 出现次数 (按空白切分, 大小写敏感)。

    Args:
        documents: 文档字符串列表。

    Returns:
        dict[str, int]: word → count。

    Raises:
        TypeError: 输入不是 list 或元素不是 str。
    """
    pass


def inverted_index(documents: List[List[str]]) -> Dict[str, List[int]]:
    """
    构建倒排索引: word → 出现该 word 的文档索引列表 (升序, 不重复)。

    Args:
        documents: list[list[str]] 每个 doc 是 word list。

    Returns:
        dict[str, list[int]]: word → [doc_idx_list]。

    Raises:
        TypeError: 输入类型错误。
    """
    pass


def top_k_frequent(counts: Dict[str, int], k: int) -> List[str]:
    """
    返回 top k 频率词列表, 排序: 频率降序优先, 同频按字母升序。

    Args:
        counts: dict[word, count] (count >= 0)。
        k: 取前 k 个, k >= 0。

    Returns:
        list[str]: 长度 min(k, len(counts))。

    Raises:
        ValueError: k < 0 / count 含负数。
        TypeError: 输入类型错误。
    """
    pass


def compute_co_occurrence(documents: List[List[str]]) -> Dict[Tuple[str, str], int]:
    """
    计算每对**有序**词对 (a, b, a 不同位置) 在同一文档共现次数。
    跨文档累加。

    Args:
        documents: list[list[str]]。

    Returns:
        dict[(str, str), int]: (a, b) → count。

    Raises:
        TypeError: 输入类型错误。
    """
    pass
