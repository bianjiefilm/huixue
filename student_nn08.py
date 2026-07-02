"""正则化与 Dropout - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Dict, List


def l1_regularization(weights: list, alpha: float) -> float:
    """
    L1 正则化项: alpha * sum(|w_i|)。

    Args:
        weights: 权重列表 (扁平化)。
        alpha: 强度系数, 非负。

    Returns:
        float: L1 正则化损失项。

    Raises:
        ValueError: 输入空 / alpha 负。
        TypeError: 输入类型错误。
    """
    pass


def l2_regularization(weights: list, alpha: float) -> float:
    """
    L2 正则化项: alpha * sum(w_i^2)。

    Args:
        weights: 权重列表。
        alpha: 强度系数, 非负。

    Returns:
        float: L2 正则化损失项。

    Raises:
        ValueError: 输入空 / alpha 负。
        TypeError: 输入类型错误。
    """
    pass


def apply_dropout(activation: list, drop_rate: float, seed: int = 42) -> List[float]:
    """
    单次 Dropout: 按 drop_rate 概率把元素置零, 留下的元素乘 1/(1-drop_rate)。

    使用 numpy.random.RandomState(seed).rand 生成 mask 保证确定性。

    Args:
        activation: 激活列表 (扁平化)。
        drop_rate: 置零概率, 范围 [0, 1)。
        seed: 随机种子。

    Returns:
        list[float] 与输入等长。

    Raises:
        ValueError: 输入空 / drop_rate 越界。
        TypeError: 输入类型错误。
    """
    pass


def check_overfit_signal(train_history: list, val_history: list, patience: int = 5) -> Dict[str, object]:
    """
    诊断训练/验证损失序列的过拟合信号。

    判断规则:
      - has_overfit: val 最近 patience 步内最佳 < 之前最佳 → False (还在改善); 否则 True
      - gap: train_history[-1] - val_history[-1] (负数表示 val > train, 即过拟合)
      - best_val_epoch: val_history 最低值的 epoch 索引 (0-indexed)
      - is_diverging: val_history 末尾值比最佳高 ≥ 10%

    Args:
        train_history: list[float] 每 epoch 训练损失。
        val_history: list[float] 每 epoch 验证损失。
        patience: 容忍未改善的 epoch 数。

    Returns:
        dict 含 4 键 (has_overfit / gap / best_val_epoch / is_diverging)。

    Raises:
        ValueError: 输入空 / 长度不一致 / patience 非正。
        TypeError: 输入类型错误。
    """
    pass
