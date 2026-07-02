"""数据探索与特征理解 - 学生作答文件"""
import pandas as pd
import numpy as np
from typing import Dict, List


def get_data_overview(df: pd.DataFrame) -> Dict[str, any]:
    """
    返回 DataFrame 的基本概况: 行数、列数、缺失率、类型分布。

    Returns:
        dict: {n_rows, n_columns, missing_rate: dict{col: rate}, dtypes: dict{col: str}}
    """
    pass


def calculate_correlation(df: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """
    计算特征间的相关系数矩阵。

    Args:
        df: DataFrame
        method: 'pearson'|'spearman'

    Returns:
        pd.DataFrame: 相关系数矩阵
    """
    pass


def find_high_correlation_pairs(df: pd.DataFrame, threshold: float = 0.8) -> List[tuple]:
    """
    找出相关系数绝对值大于 threshold 的特征对。

    Returns:
        List[tuple]: [(feature1, feature2, corr), ...]
    """
    pass


def detect_outliers_iqr(df: pd.DataFrame, column: str) -> List[int]:
    """
    基于 IQR 检测指定列的异常值索引。

    Returns:
        List[int]: 异常值行索引列表
    """
    pass
