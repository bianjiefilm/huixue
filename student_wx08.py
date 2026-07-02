"""数值清洗 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""


def parse_numeric_string(s: str) -> float:
    """
    解析数值字符串为 float, 支持 $ ¥ ￥ 货币符号与千分位逗号。
    简化规则:
      1. strip 前后空白
      2. 移除 $ ¥ ￥
      3. 移除千分位逗号
      4. float()

    Args:
        s: 数值字符串。

    Returns:
        float: 解析结果。

    Raises:
        ValueError: 不能解析为 float。
        TypeError: 输入不是字符串。
    """
    pass


def clip_to_range(value: float, lower: float, upper: float) -> float:
    """
    截断 value 到 [lower, upper]: max(min(value, upper), lower)。

    Args:
        value: 待截断值。
        lower, upper: 上下界, lower <= upper。

    Returns:
        float: 截断结果。

    Raises:
        ValueError: lower > upper。
        TypeError: 输入不是数值。
    """
    pass


def round_half_up(value: float, decimals: int = 0) -> float:
    """
    四舍五入 (half-up, 不是银行家舍入)。
    0.5 总是向上 (toward +infinity): 0.5 → 1, 2.5 → 3, -1.5 → -1。

    Args:
        value: 待舍入值。
        decimals: 小数位数 (>= 0)。

    Returns:
        float: 舍入结果。

    Raises:
        ValueError: decimals < 0。
        TypeError: 输入类型错误。
    """
    pass


def is_numeric_string(s: str) -> bool:
    """
    判断字符串能否解析为合法数值 (parse_numeric_string 不抛异常 → True)。

    Args:
        s: 任意字符串。

    Returns:
        bool: 可解析 → True; 否则 False。

    Raises:
        TypeError: 输入不是字符串。
    """
    pass
