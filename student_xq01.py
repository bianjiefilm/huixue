"""学生学业表现基础统计 - 学生作答文件 (校情数据分析 第 1 关)

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Dict


def compute_pass_rate(grades: List[Dict], threshold: float = 60) -> Dict:
    """
    给定一组学生成绩, 计算通过率统计。

    Args:
        grades: list[dict], 每条形如 {"student_id": "S001", "score": 75}。
        threshold: 通过分数阈值 (默认 60)。

    Returns:
        dict 含 3 keys: "pass_count" (int), "fail_count" (int), "pass_rate" (float)。

    Raises:
        ValueError: 输入数据不合法。
        TypeError: 输入类型错误。
    """
    pass


def item_difficulty(scores: List[float], max_score: float = 100) -> float:
    """
    计算单道题目的难度系数。

    Args:
        scores: list[float], 单道题所有学生得分。
        max_score: 该题满分 (默认 100)。

    Returns:
        float ∈ [0.0, 1.0], 越高越简单。

    Raises:
        ValueError: 输入数据不合法。
        TypeError: 输入类型错误。
    """
    pass


def enrollment_concentration(courses: List[Dict]) -> float:
    """
    计算选课集中度 (赫芬达尔指数 HHI)。

    Args:
        courses: list[dict], 每条形如 {"course_id": "C001", "enroll_count": 40}。

    Returns:
        float ∈ (0.0, 1.0]。

    Raises:
        ValueError: 输入数据不合法。
        TypeError: 输入类型错误。
    """
    pass


def gpa_distribution_buckets(gpas: List[float], buckets: List[float]) -> Dict:
    """
    按 buckets 分桶统计 gpa 人数。

    Args:
        gpas: list[float], GPA 值 (典型范围 0.0-4.0)。
        buckets: list[float] 严格递增, 长度 >= 2。

    Returns:
        dict, key 形如 "0.00-1.00", value 为该段人数 (int)。

    Raises:
        ValueError: 输入数据不合法。
        TypeError: 输入类型错误。
    """
    pass
