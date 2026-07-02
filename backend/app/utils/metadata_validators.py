"""
Pure validation functions for resource metadata (metadata.json).

Extracted from services/resource_sync_v3/parser.py — no DB, no I/O.
"""
import re
from pathlib import PurePosixPath
from typing import Dict, List, Any, Optional


def clean_empty_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively remove None and empty-string values from a dict."""
    cleaned = {}
    for key, value in data.items():
        if value is not None and value != "":
            if isinstance(value, dict):
                cleaned[key] = clean_empty_values(value)
            elif isinstance(value, list):
                cleaned[key] = [item for item in value if item is not None]
            else:
                cleaned[key] = value
    return cleaned


def migrate_legacy_format(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate legacy enum values to current format.

    training_type: DRAG_DROP → drag_and_drop, CODING → coding
    difficulty: easy → beginner, medium → intermediate, hard → advanced
    """
    result = dict(data)

    if 'training_type' in result:
        type_mapping = {
            'DRAG_DROP': 'drag_and_drop',
            'CODING': 'coding',
        }
        if result['training_type'] in type_mapping:
            result['training_type'] = type_mapping[result['training_type']]

    if 'difficulty' in result:
        difficulty_mapping = {
            'easy': 'beginner',
            'medium': 'intermediate',
            'hard': 'advanced',
        }
        if result['difficulty'] in difficulty_mapping:
            result['difficulty'] = difficulty_mapping[result['difficulty']]

    return result


def validate_required_fields(
    data: Dict[str, Any],
    is_training: bool = False,
) -> List[str]:
    """
    Check that all mandatory fields are present and non-empty.

    Args:
        data: metadata dict
        is_training: True for training resources (extra required fields)

    Returns:
        list of error strings (empty == valid)
    """
    errors: List[str] = []

    required_fields = [
        'id', 'title', 'intro', 'difficulty',
        'course_hours', 'handbook_content_path',
    ]

    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            errors.append(f"缺少必需字段: {field}")

    if is_training:
        if 'training_type' not in data:
            errors.append("实训资源缺少必需字段: training_type")
        if 'industry' not in data:
            errors.append("实训资源缺少必需字段: industry")

    # environment_config
    if 'environment_config' not in data:
        errors.append("缺少环境配置: environment_config")
    else:
        env_config = data['environment_config']
        if not isinstance(env_config, dict):
            errors.append("environment_config必须是对象")
        else:
            if 'env_type' not in env_config:
                errors.append("environment_config缺少字段: env_type")
            if 'docker_image_name' not in env_config:
                errors.append("environment_config缺少字段: docker_image_name")

    return errors


def validate_data_formats(data: Dict[str, Any]) -> List[str]:
    """
    Validate data types and formats (ID pattern, version, hours, file extensions).

    Returns list of error strings.
    """
    errors: List[str] = []

    # ID format
    if 'id' in data:
        if not re.match(r'^[a-zA-Z0-9_-]+$', str(data['id'])):
            errors.append("id只能包含字母、数字、下划线和连字符")

    # Version format
    if 'version' in data:
        if not re.match(r'^\d+\.\d+\.\d+$', str(data['version'])):
            errors.append("version必须是x.y.z格式的版本号")

    # course_hours
    if 'course_hours' in data:
        try:
            hours = int(data['course_hours'])
            if not (1 <= hours <= 100):
                errors.append("course_hours必须在1-100之间")
        except (ValueError, TypeError):
            errors.append("course_hours必须是整数")

    # File path extensions
    file_rules = {
        'handbook_content_path': (['.md', '.markdown'], "markdown文件"),
        'cover_url_path': (['.png', '.jpg', '.jpeg', '.gif'], "图片文件"),
    }
    for field, (allowed_exts, label) in file_rules.items():
        if field in data and data[field]:
            suffix = PurePosixPath(str(data[field])).suffix.lower()
            if suffix not in allowed_exts:
                errors.append(f"{field}必须指向{label}")

    # Content resources
    if 'content_resources' in data:
        errors.extend(validate_content_resources(data['content_resources']))

    return errors


def validate_content_resources(content_resources: Any) -> List[str]:
    """Validate content_resources structure and file extensions."""
    errors: List[str] = []

    if not isinstance(content_resources, dict):
        return ["content_resources必须是对象"]

    expected_keys = ['datasets', 'sql_scripts', 'bi_templates', 'ai_models']

    for key in expected_keys:
        if key not in content_resources:
            content_resources[key] = []

        resource_list = content_resources[key]
        if not isinstance(resource_list, list):
            errors.append(f"content_resources.{key}必须是数组")
            continue

        for i, resource in enumerate(resource_list):
            if not isinstance(resource, dict):
                errors.append(f"content_resources.{key}[{i}]必须是对象")
                continue

            if 'path' not in resource:
                errors.append(f"content_resources.{key}[{i}]缺少path字段")

            if key == 'sql_scripts' and 'path' in resource:
                if not PurePosixPath(resource['path']).suffix.lower() == '.sql':
                    errors.append(
                        f"content_resources.sql_scripts[{i}].path必须指向.sql文件"
                    )

            if key == 'bi_templates' and 'path' in resource:
                suffix = PurePosixPath(resource['path']).suffix.lower()
                if suffix not in ['.zip', '.json']:
                    errors.append(
                        f"content_resources.bi_templates[{i}].path必须指向.zip或.json文件"
                    )

    return errors


def validate_business_rules(
    data: Dict[str, Any],
    is_training: bool = False,
) -> List[str]:
    """
    Enforce domain-specific constraints.

    Returns list of error strings.
    """
    errors: List[str] = []

    if is_training:
        training_type = data.get('training_type')
        industry = data.get('industry', '').lower()

        if training_type == 'drag_and_drop':
            if not industry or industry in ['computer science', '计算机科学']:
                errors.append(
                    "拖拽式实训的industry不应该是一般性行业，请指定具体的业务领域"
                )

    # assignment_nodes
    if 'assignment_nodes' in data:
        nodes = data['assignment_nodes']
        if not isinstance(nodes, list):
            errors.append("assignment_nodes必须是数组")
        else:
            for i, node in enumerate(nodes):
                if not isinstance(node, dict):
                    errors.append(f"assignment_nodes[{i}]必须是对象")
                    continue
                if 'tool_type' in node:
                    if node['tool_type'] not in ['BI', 'AI']:
                        errors.append(
                            f"assignment_nodes[{i}].tool_type必须是'BI'或'AI'"
                        )

    return errors


def suggest_fixes(errors: List[str]) -> Dict[str, Any]:
    """
    Generate remediation suggestions from an error list.

    Returns dict with 'fixes' and 'warnings' lists.
    """
    suggestions: Dict[str, Any] = {
        'fixes': [],
        'warnings': [],
    }

    for error in errors:
        if '缺少必需字段' in error:
            parts = error.split(': ', 1)
            field = parts[1] if len(parts) > 1 else ''
            suggestions['fixes'].append({
                'type': 'add_required_field',
                'field': field,
                'suggestion': f"为字段 '{field}' 提供合适的值",
            })

        elif '必须指向' in error and '文件' in error:
            if 'handbook' in error:
                suggestions['fixes'].append({
                    'type': 'fix_file_path',
                    'field': 'handbook_content_path',
                    'suggestion': "确保handbook_content_path指向一个存在的.md文件",
                })
            elif 'cover' in error:
                suggestions['fixes'].append({
                    'type': 'fix_file_path',
                    'field': 'cover_url_path',
                    'suggestion': "确保cover_url_path指向一个存在的图片文件",
                })

    return suggestions
