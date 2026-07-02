"""模型评估与优化 - 学生作答文件"""
import numpy as np
from typing import List, Dict, Tuple


def stratified_kfold_split(y: np.ndarray, n_splits: int, random_state: int = None) -> List[Tuple[np.ndarray, np.ndarray]]:
    """
    分层 K 折划分: 保持各类别比例一致地划分 K 个 (train_idx, test_idx) 对。

    Args:
        y: 标签向量
        n_splits: 折数
        random_state: 随机种子

    Returns:
        List[(train_indices, test_indices), ...]
    """
    pass


def cross_val_score(estimator, X: np.ndarray, y: np.ndarray, cv_splits: list, scoring: str) -> np.ndarray:
    """
    简化版交叉验证: 对每个 split 用 estimator.fit/predict/score, 返回得分数组。

    scoring: 'accuracy'|'f1'|'roc_auc'

    Returns:
        np.ndarray: 各折得分
    """
    pass


def bootstrap_sample(X: np.ndarray, y: np.ndarray, n_samples: int = None) -> Tuple[np.ndarray, np.ndarray]:
    """
    有放回抽样,生成与原数据集等大的 Bootstrap 样本。

    Returns:
        (X_boot, y_boot)
    """
    pass


def compute_learning_curve(train_sizes: np.ndarray, train_scores: np.ndarray, test_scores: np.ndarray) -> Dict:
    """
    从 learning_curve 原始输出计算均值和标准差。

    Returns:
        dict: {train_mean, train_std, test_mean, test_std} (各为 np.ndarray)
    """
    pass
