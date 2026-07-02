"""模型训练实战 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Dict, List, Tuple


def train_step_linear(W: list, b: float, X: list, y: list, lr: float) -> Tuple[List[float], float, float]:
    """
    线性回归单 batch 训练: 前向 → MSE 损失 → 梯度 → SGD 更新。

    Args:
        W: 当前权重 list[float] 长度 d。
        b: 当前偏置 float。
        X: list[list[float]] 形状 (N, d)。
        y: list[float] 长度 N。
        lr: 学习率。

    Returns:
        (W_new, b_new, loss):
          W_new list[float] 长度 d
          b_new float
          loss float (MSE 在 batch 上)。

    Raises:
        ValueError: 输入空 / 维度不匹配。
        TypeError: 输入类型错误。
    """
    pass


def early_stopping_check(val_losses: list, patience: int, min_delta: float = 1e-4) -> bool:
    """
    判断是否应早停。

    规则: 当 best_before = min(val_losses[:-patience]) 且
        recent_best = min(val_losses[-patience:]),
        如果 best_before - recent_best < min_delta (即未改善 ≥ min_delta), 返回 True。
    序列长度 < patience+1 时返回 False (尚未到判断时机)。

    Args:
        val_losses: 历史验证损失。
        patience: 连续未改善的 epoch 数阈值。
        min_delta: 改善幅度阈值。

    Returns:
        bool: 是否应停止。

    Raises:
        ValueError: val_losses 空 / patience 非正。
        TypeError: 输入类型错误。
    """
    pass


def compute_validation_metrics(y_true: list, y_pred: list) -> Dict[str, float]:
    """
    二分类 5 指标: accuracy / precision / recall / f1 / specificity。

    Args:
        y_true: list[int 0/1]。
        y_pred: list[int 0/1] 与 y_true 等长。

    Returns:
        dict 含 5 键, 除零情况返回 0.0。

    Raises:
        ValueError: 输入空 / 长度不一致 / 含非 0/1 标签。
        TypeError: 输入类型错误。
    """
    pass


def format_training_log(epoch: int, train_loss: float, val_loss: float, val_metrics: dict) -> str:
    """
    格式化训练日志为单行字符串。

    格式: 'Epoch {epoch} | train_loss={tl:.4f} | val_loss={vl:.4f} | acc={a:.3f} | f1={f:.3f}'
    其中 acc, f1 来自 val_metrics。

    Args:
        epoch: int >= 0。
        train_loss, val_loss: float。
        val_metrics: 含 'accuracy' 与 'f1' 键的 dict。

    Returns:
        str: 单行格式化日志。

    Raises:
        ValueError: epoch 负 / val_metrics 缺关键字。
        TypeError: 输入类型错误。
    """
    pass
