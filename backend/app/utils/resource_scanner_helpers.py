"""
资源扫描器纯函数

从 resource_scanner.py 提取的无副作用函数，
覆盖资源类型检测、数据标准化、BI关卡提取、智能字段提取等逻辑。
"""

import re
from typing import Any, Dict, List, Optional, Tuple


# ─── 默认资源模式 ──────────────────────────────────────────────────
DEFAULT_RESOURCE_PATTERNS: Dict[str, List[str]] = {
    "course": ["课程资源", "课程资料"],
    "practice": ["实践资源", "微型实验", "实训资源"],
    "training": ["实训", "训练"],
    "material": ["教材", "教学材料"],
    "question": ["题库", "习题", "考试"],
}


# ─── 资源类型检测 ──────────────────────────────────────────────────

def detect_resource_type(
    path_str: str,
    resource_patterns: Optional[Dict[str, List[str]]] = None,
) -> Optional[str]:
    """
    根据路径字符串检测资源类型。

    Args:
        path_str: 路径字符串（会被转小写后匹配）
        resource_patterns: 自定义匹配规则，默认使用 DEFAULT_RESOURCE_PATTERNS

    Returns:
        匹配到的资源类型字符串，未匹配则 None
    """
    if resource_patterns is None:
        resource_patterns = DEFAULT_RESOURCE_PATTERNS

    lower_path = path_str.lower()
    for res_type, patterns in resource_patterns.items():
        for pattern in patterns:
            if pattern.lower() in lower_path:
                return res_type
    return None


# ─── 数据标准化 ────────────────────────────────────────────────────

def standardize_course_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将原始课程 JSON 标准化为统一结构。

    Args:
        data: 原始 JSON 数据（含 title/name 等字段）

    Returns:
        标准化后的课程字典
    """
    return {
        "title": data.get("title") or data.get("name") or "未命名课程",
        "description": data.get("description", ""),
        "type": data.get("type", "course"),
        "difficulty": data.get("difficulty", "beginner"),
        "duration": data.get("duration", 0),
        "topics": data.get("topics", []),
        "stages": data.get("stages", []),
        "resources": data.get("resources", []),
        "metadata": data,
    }


# ─── BI 关卡提取 ──────────────────────────────────────────────────

def extract_bi_stages(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    从 BI 项目 JSON 中提取关卡列表。

    规则:
    - dataSources → "数据源配置" 关卡
    - datasets   → "数据集创建" 关卡
    - dashboards → 每个 dashboard 一个关卡
    """
    stages: List[Dict[str, Any]] = []

    if "dataSources" in data:
        stages.append({
            "title": "数据源配置",
            "description": "配置并连接数据源",
            "tasks": ["配置数据库连接", "验证数据源访问"],
        })

    if "datasets" in data:
        stages.append({
            "title": "数据集创建",
            "description": "创建和配置数据集",
            "tasks": ["创建数据集", "配置数据关系"],
        })

    if "dashboards" in data:
        for i, dashboard in enumerate(data["dashboards"], 1):
            stages.append({
                "title": f"仪表板设计-{dashboard.get('name', i)}",
                "description": f"设计和实现{dashboard.get('name', '')}仪表板",
                "tasks": ["设计布局", "配置图表", "添加交互"],
            })

    return stages


# ─── 列表项 → 关卡 ───────────────────────────────────────────────

def item_to_stage(item: Dict[str, Any]) -> Dict[str, Any]:
    """将列表项字典转换为关卡字典。"""
    return {
        "title": item.get("title") or item.get("name", "未命名关卡"),
        "description": item.get("description", ""),
        "tasks": item.get("tasks", []),
    }


# ─── 智能字段提取 ─────────────────────────────────────────────────

_TITLE_FIELDS = ["title", "name", "courseName", "projectTitle", "项目名称", "课程名称"]
_DESC_FIELDS = ["description", "desc", "intro", "introduction", "简介", "描述"]


def intelligent_extraction(
    data: Dict[str, Any],
    fallback_title: str = "未命名",
    fallback_type: str = "course",
) -> Dict[str, Any]:
    """
    从任意结构的 JSON 中智能提取课程信息。

    Args:
        data: 原始 JSON
        fallback_title: 找不到标题时使用的备选名称
        fallback_type: 找不到类型时使用的备选类型

    Returns:
        标准化课程字典
    """
    title = None
    for field in _TITLE_FIELDS:
        if field in data:
            title = data[field]
            break

    description = ""
    for field in _DESC_FIELDS:
        if field in data:
            description = data[field]
            break

    return {
        "title": title or fallback_title,
        "description": description,
        "type": fallback_type,
        "difficulty": "beginner",
        "duration": 60,
        "topics": [],
        "stages": [],
        "resources": [],
        "metadata": data,
    }


# ─── BI项目数据标准化 ────────────────────────────────────────────

def parse_bi_project_data(
    data: Dict[str, Any],
    parent_name: str = "",
) -> Dict[str, Any]:
    """
    将 BI 项目 JSON 标准化。

    Args:
        data: 原始 JSON（含 projectTitle 等）
        parent_name: 父目录名，用于 fallback 和编号提取

    Returns:
        标准化课程字典
    """
    title = data.get("projectTitle", "")

    match = re.match(r"(\d+)-(.+)", parent_name)
    if match:
        _number, name = match.groups()
        if not title:
            title = name

    return {
        "title": title or parent_name,
        "description": data.get("projectDescription", ""),
        "type": "practice",
        "difficulty": "intermediate",
        "duration": 120,
        "topics": ["数据分析", "BI", "商业智能"],
        "stages": extract_bi_stages(data),
        "resources": [],
        "metadata": data,
    }


# ─── 目录名解析 ──────────────────────────────────────────────────

def parse_directory_name(name: str) -> Tuple[Optional[str], str]:
    """
    解析 "编号-名称" 格式的目录名。

    Returns:
        (number_or_none, title)
    """
    match = re.match(r"(\d+)-(.+)", name)
    if match:
        return match.group(1), match.group(2)
    return None, name


# ─── 结果集路由 ──────────────────────────────────────────────────

TYPE_TO_KEY = {
    "course": "courses",
    "practice": "practices",
    "training": "trainings",
    "material": "materials",
    "question": "questions",
}


def result_key_for_type(resource_type: str) -> str:
    """将资源类型映射到结果集键名。"""
    return TYPE_TO_KEY.get(resource_type, "courses")
