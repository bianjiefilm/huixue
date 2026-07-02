"""数据预处理与特征工程 - 学生作答文件"""
import pandas as pd
import numpy as np
from typing import List, Tuple


def encode_label(series: pd.Series) -> Tuple[pd.Series, dict]:
    """
    对分类型特征做标签编码。

    Returns:
        (编码后的 Series, 编码映射字典 {原始值: 编码})
    """
    pass


def one_hot_encode(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    对指定列做独热编码,返回新增列后的 DataFrame 副本。

    Returns:
        pd.DataFrame: 含独热编码列的 DataFrame
    """
    pass


def standardize(X_train: np.ndarray, X_test: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    对训练集 fit 并 transform, 对测试集只 transform。

    标准化公式: (X - mean) / std

    Returns:
        (X_train_scaled, X_test_scaled)
    """
    pass


def variance_threshold_selection(X: np.ndarray, threshold: float = 0.0) -> Tuple[np.ndarray, List[int]]:
    """
    方差过滤: 删除方差小于等于 threshold 的特征。

    Returns:
        (筛选后的特征矩阵, 被保留的特征索引列表)
    """
    pass
