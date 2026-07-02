"""模型评估与优化 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Dict, List, Tuple


def stratified_kfold_split(y: list, n_splits: int, random_state: int = 42) -> List[Tuple[List[int], List[int]]]:
    """
    分层 K 折划分: 把 y 的索引分成 n_splits 折, 每折保持原始类别比例。

    Args:
        y: list[int], 类别标签。
        n_splits: 折数 (>= 2)。
        random_state: 用于可复现性 (实现里可用 random.seed)。

    Returns:
        list[(train_idx, test_idx)] 长度 n_splits;
        所有折的 test_idx 并集 = {0..len(y)-1} 且互斥。

    Raises:
        ValueError: y 空 / n_splits 非正 / 某类样本数 < n_splits 无法分层。
        TypeError: 输入类型错误。
    """
    pass


def bootstrap_sample(values: list, n: int, random_state: int = 42) -> list:
    """
    对 values 做有放回采样 n 次, 用 random_state 保证确定性。

    Args:
        values: list, 待采样源。
        n: 采样后大小。
        random_state: 随机种子。

    Returns:
        list 长度 n; 含原 values 中元素 (允许重复)。

    Raises:
        ValueError: values 空 / n 非负。
        TypeError: 输入类型错误。
    """
    pass


def aggregate_cv_scores(scores: list) -> Dict[str, float]:
    """
    给定每折分数列表, 返回 mean/std/min/max。std 用 N (population)。

    Returns:
        dict 含 4 键: 'mean', 'std', 'min', 'max'。

    Raises:
        ValueError: scores 空。
        TypeError: 输入类型错误。
    """
    pass


def compute_learning_curve_means(train_scores: list, val_scores: list) -> Dict[str, list]:
    """
    给定形状 (n_sizes, n_repeats) 的训练/验证分数矩阵, 返回各数据量下的均值与标准差。

    Returns:
        dict 含 4 键: 'train_mean', 'train_std', 'val_mean', 'val_std';
        每个值是长度 n_sizes 的 list。

    Raises:
        ValueError: 矩阵空 / 行长度不一致 / 两矩阵形状不匹配。
        TypeError: 输入类型错误。
    """
    pass
