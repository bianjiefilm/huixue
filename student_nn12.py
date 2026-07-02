"""综合项目: 手写数字识别 - 学生作答文件

不嵌完整数据 (与 v1 灾难形成对照)。
学生需自己构造满足 schema 的 100 样本 10 类不平衡数据。
仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
"""
from typing import Dict, List, Tuple


def load_mnist_subset() -> Dict[str, list]:
    """
    构造或加载手写数字数据 (100 样本 10 类不平衡)。

    Returns:
        dict 含 2 个键:
          - 'images': list[list[list[float]]] 形状 (100, 8, 8), 像素值 [0, 16]
          - 'labels': list[int] 长度 100, 类别比例 [5,8,10,12,15,8,10,12,10,10]

    可用方法: 1) 合成数据 (随机像素 + 类别相关偏置); 2) sklearn.datasets.load_digits 子采样。
    """
    pass


def preprocess_and_split(data: dict, test_size: float = 0.2,
                         random_state: int = 42) -> Tuple[list, list, list, list]:
    """
    扁平化 8×8 图像到 64 维向量 + z-score 标准化 + 分层划分。

    步骤约定:
      1. images 扁平化: (100, 8, 8) → (100, 64)
      2. 分层 train_test_split, 保持 10 类比例
      3. 数值特征 z-score 标准化 (用 train 统计量, test 只 transform)

    Returns:
        (X_train, X_test, y_train, y_test):
          X_train / X_test: list[list[float]] 行=样本 列=64 标准化特征
          y_train / y_test: list[int] 0-9 标签

    Raises:
        ValueError: data 缺关键字段。
        TypeError: data 不是 dict。
    """
    pass


def train_simple_classifier(X_train: list, y_train: list,
                             n_epochs: int = 20, lr: float = 0.1) -> Dict[str, list]:
    """
    训练简单线性 softmax 分类器 (64 → 10 logits)。

    使用 SGD 单步更新 (复用 NN07), 多元交叉熵损失 (复用 NN03)。

    Args:
        X_train: list[list[float]] 形状 (N, 64)。
        y_train: list[int] 0-9 长度 N。
        n_epochs: 训练轮数。
        lr: 学习率。

    Returns:
        dict 含 2 键:
          - 'W': list[list[float]] 形状 (64, 10) 训练后权重
          - 'b': list[float] 长度 10 偏置

    Raises:
        ValueError: 输入空 / 长度不一致。
        TypeError: 输入类型错误。
    """
    pass


def evaluate_classifier(state: dict, X_test: list, y_test: list) -> Dict[str, object]:
    """
    多分类 5 指标评估。

    Args:
        state: dict 含 'W' 与 'b' 的训练后状态。
        X_test: list[list[float]] 形状 (M, 64)。
        y_test: list[int] 长度 M。

    Returns:
        dict 含 5 键:
          - 'accuracy': float, 整体正确率
          - 'macro_precision': float, 各类 precision 平均
          - 'macro_recall': float, 各类 recall 平均
          - 'macro_f1': float, 各类 F1 平均
          - 'per_class_accuracy': list[float] 长度 10, 各类准确率

    Raises:
        ValueError: 输入空 / state 缺字段。
        TypeError: 输入类型错误。
    """
    pass
