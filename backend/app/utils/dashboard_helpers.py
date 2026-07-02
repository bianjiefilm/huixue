"""
仪表板/推荐系统纯函数

从 student_dashboard.py、excellent_work_recommendation.py 提取的无副作用计算逻辑。
"""

from typing import Any, Dict, List, Optional, Tuple


# ─── 截止日期紧急度 ───────────────────────────────────────────────

def deadline_urgency(days_left: Optional[int]) -> int:
    """
    根据剩余天数计算截止日期紧急度 (0-100)。

    规则:
    - None (无截止日期) → 0
    - <=0 天 → 100
    - 1-3 天 → 80
    - 4-7 天 → 50
    - >7 天 → max(0, 30 - days_left)
    """
    if days_left is None:
        return 0
    if days_left <= 0:
        return 100
    if days_left <= 3:
        return 80
    if days_left <= 7:
        return 50
    return max(0, 30 - days_left)


# ─── 进度百分比 ──────────────────────────────────────────────────

def progress_percent(completed: int, total: int) -> int:
    """
    计算完成百分比 (0-100)，total 为 0 时返回 0���
    """
    if total <= 0:
        return 0
    return min(100, int((completed / total) * 100))


# ─── 学习路径关注度评分 ─────────────────────────────────────────

def attention_score(
    urgency: int,
    progress_gap: int,
    is_mandatory: bool,
) -> float:
    """
    计算学习路径综合关注度得分。

    Score = urgency * 0.5 + progress_gap * 0.3 + (30 if mandatory else 0)
    """
    mandatory_weight = 30 if is_mandatory else 0
    return urgency * 0.5 + progress_gap * 0.3 + mandatory_weight


# ─── 优先级类型判定 ───────────────────────────────────��──────────

def priority_type(
    days_left: Optional[int],
    pct: int,
    total_tasks: int,
    is_mandatory: bool,
) -> str:
    """
    判定学习路径优先级类型。

    Returns: "deadline" | "skill_gap" | "mandatory" | "optional"
    """
    if days_left is not None and days_left <= 3:
        return "deadline"
    if pct < 30 and total_tasks > 0:
        return "skill_gap"
    if is_mandatory:
        return "mandatory"
    return "optional"


# ─── 技能分类 ────────────────────────────────────────────────────

_PROGRAMMING = ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'sql', 'html', 'css']
_DATA = ['数据分析', 'data analysis', 'pandas', 'numpy', '数据可视化', 'visualization', 'tableau', 'bi']
_ML = ['机器学习', 'machine learning', 'deep learning', '深度学习', 'tensorflow', 'pytorch', 'ai']
_STATS = ['统计', 'statistics', '概率', 'probability', '数学', 'math']


def categorize_skill(skill: str) -> str:
    """
    将技能名称分类为 "编程"/"数据分析"/"人工智能"/"数学统计"/"其他"。
    """
    lower = skill.lower()
    if any(p in lower for p in _PROGRAMMING):
        return "编程"
    if any(d in lower for d in _DATA):
        return "数据分析"
    if any(m in lower for m in _ML):
        return "人工智能"
    if any(s in lower for s in _STATS):
        return "数学统计"
    return "其他"


# ─── 推荐评分 ────────────────────────────────────────────────────

def recommendation_score(
    course_pref_count: int,
    liked_count: int,
    overall_score: Optional[float],
    view_count: int,
    like_count: int,
) -> float:
    """
    计算优秀作业推荐分数。

    - 课程偏好: course_pref_count * 0.5
    - 质量分 (仅 liked_count > 0): (overall_score/100 or 0.5) * 0.3
    - 流行度: min((view_count + like_count)/10, 1.0) * 0.2
    """
    score = course_pref_count * 0.5

    if liked_count > 0:
        quality = overall_score / 100.0 if overall_score else 0.5
        score += quality * 0.3

    popularity = min((view_count + like_count) / 10.0, 1.0)
    score += popularity * 0.2

    return score


# ─── 相似度计算 ──────────────────────────────────────────────────

def work_similarity_score(
    same_course: bool,
    same_difficulty: bool,
    heat_diff: int,
) -> float:
    """
    计算两个作业之间的相似度分数。

    - 课程相同: +0.4
    - 难度相同: +0.3
    - 热度差 < 10: +0.3
    """
    score = 0.0
    if same_course:
        score += 0.4
    if same_difficulty:
        score += 0.3
    if heat_diff < 10:
        score += 0.3
    return score


# ─── 实践状态判定 ───────────────────────────────────────���────────

def determine_practice_status(
    publish_status: str,
    visibility: Optional[str],
    is_published: bool,
) -> str:
    """
    根据发布状态和可见性确定前端显示状态。

    Args:
        publish_status: "EDITING" | "PUBLISHED" | "PENDING_REVIEW" | "REJECTED"
        visibility: "PRIVATE" | "PUBLIC" | None
        is_published: 是否曾经发布过

    Returns:
        "draft" | "editing" | "published_personal" | "published_public"
        | "pending" | "rejected"
    """
    ps = publish_status.upper() if publish_status else ""

    if ps == "EDITING":
        return "editing" if is_published else "draft"
    if ps == "PUBLISHED":
        if visibility and visibility.upper() == "PRIVATE":
            return "published_personal"
        return "published_public"
    if ps == "PENDING_REVIEW":
        return "pending"
    if ps == "REJECTED":
        return "rejected"
    return "draft"


# ─── 版本号递增 ──────────────────────────────────────────────────

def increment_version(current_version: str, version_type: str) -> str:
    """
    递增语义化版本号。

    Args:
        current_version: "major.minor.patch" 格式
        version_type: "major" | "minor"

    Returns:
        递增后的版本号字符串
    """
    try:
        parts = current_version.split(".")
        major, minor = int(parts[0]), int(parts[1])
        patch = int(parts[2]) if len(parts) > 2 else 0

        if version_type == "major":
            major += 1
            minor = 0
            patch = 0
        else:  # minor
            minor += 1
            patch = 0

        return f"{major}.{minor}.{patch}"
    except Exception:
        return "1.0.0"
