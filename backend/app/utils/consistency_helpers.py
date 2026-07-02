"""
一致性监控纯函数

从 consistency_monitor.py 提取的无副作用函数。
"""

from typing import Any, Dict, List


def calculate_health_score(results: Dict[str, Any]) -> int:
    """
    根据一致性检查结果计算健康评分 (0-100)。

    算法:
    - consistency_score = 100 - (不一致数 / 检查总数 * 100)
    - error_penalty = 错误数 * 10
    - 最终 = max(0, consistency_score - error_penalty)
    - 无检查项时返回 100

    Args:
        results: 包含 cache_check 字典的检查结果

    Returns:
        0-100 的整数评分
    """
    cache_check = results.get("cache_check", {})
    total_checked = cache_check.get("total_checked", 0)
    inconsistencies = len(cache_check.get("inconsistencies", []))
    errors = len(cache_check.get("errors", []))

    if total_checked == 0:
        return 100

    consistency_score = max(0, 100 - (inconsistencies / total_checked * 100))
    error_penalty = errors * 10
    final_score = max(0, consistency_score - error_penalty)

    return int(final_score)
