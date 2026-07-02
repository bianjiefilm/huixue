"""循环神经网络基础 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Tuple


def rnn_single_step(x_t: list, h_prev: list, W_xh: list, W_hh: list, b_h: list) -> List[float]:
    """
    朴素 RNN 单步: h_t = tanh(W_xh @ x_t + W_hh @ h_prev + b_h)。

    Args:
        x_t: 当前输入 list[float] 长度 input_dim。
        h_prev: 上一步隐藏状态 list[float] 长度 hidden_dim。
        W_xh: list[list[float]] 形状 (input_dim, hidden_dim)。
        W_hh: list[list[float]] 形状 (hidden_dim, hidden_dim)。
        b_h: list[float] 长度 hidden_dim。

    Returns:
        list[float] 新隐藏状态 h_t, 长度 hidden_dim。

    Raises:
        ValueError: 维度不匹配。
        TypeError: 输入类型错误。
    """
    pass


def lstm_gates(x_t: list, h_prev: list, W_list: list, b_list: list) -> Tuple[List[float], List[float], List[float], List[float]]:
    """
    LSTM 4 门激活计算。

    把 [x_t; h_prev] 拼接为 concat 长度 input_dim+hidden_dim, 4 门分别:
      i_t = sigmoid(concat @ W_i + b_i)
      f_t = sigmoid(concat @ W_f + b_f)
      o_t = sigmoid(concat @ W_o + b_o)
      g_t = tanh(concat @ W_g + b_g)

    Args:
        x_t: list[float] 长度 input_dim。
        h_prev: list[float] 长度 hidden_dim。
        W_list: 4 个矩阵 [W_i, W_f, W_o, W_g], 每个形状 (input_dim+hidden_dim, hidden_dim)。
        b_list: 4 个向量 [b_i, b_f, b_o, b_g], 每个长度 hidden_dim。

    Returns:
        4-tuple (i, f, o, g), 每个长度 hidden_dim。

    Raises:
        ValueError: W_list 或 b_list 长度非 4 / 维度不匹配。
        TypeError: 输入类型错误。
    """
    pass


def gru_gates(x_t: list, h_prev: list, W_list: list, b_list: list) -> Tuple[List[float], List[float], List[float]]:
    """
    GRU 3 门激活计算。

    z_t = sigmoid(concat @ W_z + b_z)  其中 concat = [x_t; h_prev]
    r_t = sigmoid(concat @ W_r + b_r)
    h_tilde = tanh([x_t; r_t * h_prev] @ W_h + b_h)

    Args:
        x_t: list[float]。
        h_prev: list[float]。
        W_list: 3 个矩阵 [W_z, W_r, W_h], 每个形状 (input_dim+hidden_dim, hidden_dim)。
        b_list: 3 个向量 [b_z, b_r, b_h]。

    Returns:
        3-tuple (z, r, h_tilde)。

    Raises:
        ValueError: W_list 或 b_list 长度非 3 / 维度不匹配。
        TypeError: 输入类型错误。
    """
    pass


def compute_sequence_length_after_truncate(seq_len: int, max_len: int) -> int:
    """
    截断后的实际序列长度: min(seq_len, max_len)。

    Args:
        seq_len: 原始长度 (>=0)。
        max_len: 允许最大长度 (>=1)。

    Returns:
        int: 截断后长度。

    Raises:
        ValueError: seq_len 或 max_len 非法。
        TypeError: 输入类型错误。
    """
    pass
