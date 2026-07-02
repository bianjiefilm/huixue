"""数据挖掘概述与流程 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import Dict


def map_activity_to_phase(activity: str) -> str:
    """
    将一个 CRISP-DM 活动描述映射到 6 阶段之一。

    Returns:
        6 阶段名 ('业务理解', '数据理解', '数据准备', '建模', '评估', '部署') 之一;
        无法识别返回 '未知'。

    Raises:
        TypeError: 当 activity 不是 str 时。
    """
    pass


def classify_learning_type(has_labels: bool, all_labeled: bool) -> str:
    """
    根据是否有标签、是否全部标注, 返回学习类型。

    Returns:
        'supervised' / 'unsupervised' / 'semi-supervised' 之一。

    Raises:
        TypeError: 当任一参数不是 bool 时。
    """
    pass


def compute_accuracy(y_true: list, y_pred: list) -> float:
    """
    给定真实标签与预测标签列表, 返回 accuracy (0.0 ~ 1.0)。

    Returns:
        accuracy 比例。

    Raises:
        ValueError: 当输入为空, 或两列表长度不一致时。
    """
    pass


def is_overfit(train_acc: float, test_acc: float, threshold: float = 0.1) -> Dict[str, object]:
    """
    根据训练/测试得分判断是否过拟合。

    Returns:
        含两个键的字典: 'is_overfitting' (bool), 'gap' (float)。

    Raises:
        TypeError: 当 train_acc / test_acc 不是数值时。
    """
    pass
