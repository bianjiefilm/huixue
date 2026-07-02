"""综合项目: 电商订单数据清洗流水线 - 学生作答文件

仅写函数体, 不在 docstring 中泄漏算法步骤或公式。
请阅读 handbook 后实现以下 4 个函数。
"""
from typing import List, Dict, Optional


def validate_pipeline_input(rows: List[Dict], required_keys: List[str]) -> bool:
    """
    校验输入 rows 是否合法:
      - 每条 dict 必须包含 required_keys 中所有 key
      - 允许额外 key

    Args:
        rows: list[dict]。
        required_keys: 必需 key list。

    Returns:
        bool: 全部满足 → True; 任一缺 key → False。空 rows 或空 required_keys → True。

    Raises:
        TypeError: rows 不是 list / required_keys 不是 list / row 不是 dict。
    """
    pass


def get_cleaning_step_for_issue(issue: str) -> str:
    """
    问题类型到清洗步骤名的映射:
      'missing'     → 'fillna'
      'duplicate'   → 'drop_dup'
      'outlier'     → 'clip'
      'format'      → 'normalize'
      'consistency' → 'validate_fk'

    Args:
        issue: 5 个之一。

    Returns:
        str: 对应步骤名。

    Raises:
        ValueError: 未知 issue。
        TypeError: 输入不是字符串。
    """
    pass


def compute_pipeline_health_score(quality_dict: Dict[str, float],
                                  weights: Optional[Dict[str, float]] = None) -> float:
    """
    加权平均: sum(w_i * q_i) / sum(w_i), 三 key (completeness, uniqueness, validity)。

    Args:
        quality_dict: 必含 3 key, 各 ∈ [0, 1]。
        weights: 同 3 key 的正权重 dict (None 默认全 1)。

    Returns:
        float ∈ [0.0, 1.0]。

    Raises:
        ValueError: quality 越界 / weights 含非正 / 缺 key。
        TypeError: 输入不是 dict。
    """
    pass


def combine_cleaning_report(rows_in: int, rows_out: int,
                            issues_fixed: Dict[str, int]) -> Dict:
    """
    组装清洗报告 dict:
      {
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rows_dropped': rows_in - rows_out,
        'issues_fixed': issues_fixed,
        'total_issues': sum(issues_fixed.values()),
      }

    Args:
        rows_in, rows_out: 非负整数, rows_out <= rows_in。
        issues_fixed: dict[str, int], 值都 >= 0。

    Returns:
        dict: 5 key。

    Raises:
        ValueError: rows_in/out 非法 / issues_fixed 含负数。
        TypeError: 输入类型错误。
    """
    pass
