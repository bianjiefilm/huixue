"""
Pure helper functions for the V3 resource sync diff engine.

Extracted from services/resource_sync_v3/diff_engine.py — no DB, no I/O.
"""
from typing import Dict, List, Any, Optional, Tuple


def infer_resource_type(db_record: Dict[str, Any]) -> str:
    """
    Infer resource type from a database record.

    Returns "training" if training_type field is present and truthy,
    otherwise "practice".
    """
    if db_record.get('training_type'):
        return "training"
    return "practice"


def is_version_newer(fs_version: str, db_version: str) -> bool:
    """
    Compare two semantic version strings (x.y.z).

    Returns True if fs_version is strictly newer than db_version.
    Falls back to string comparison on parse failure.
    """
    try:
        fs_parts = [int(x) for x in fs_version.split('.')]
        db_parts = [int(x) for x in db_version.split('.')]

        max_len = max(len(fs_parts), len(db_parts))
        fs_parts.extend([0] * (max_len - len(fs_parts)))
        db_parts.extend([0] * (max_len - len(db_parts)))

        return fs_parts > db_parts
    except (ValueError, AttributeError):
        return fs_version != db_version


def check_file_changes(
    fs_files: Dict[str, Dict[str, Any]],
    db_files: Dict[str, Dict[str, Any]],
) -> List[str]:
    """
    Detect file-level changes between filesystem manifest and DB record.

    Both arguments map file_path -> {exists, size, modified, ...}.

    Returns list of human-readable change descriptions.
    """
    changes: List[str] = []

    fs_paths = set(fs_files.keys())
    db_paths = set(db_files.keys())

    # New files
    for f in sorted(fs_paths - db_paths):
        changes.append(f"新增: {f}")

    # Deleted files
    for f in sorted(db_paths - fs_paths):
        changes.append(f"删除: {f}")

    # Common files — check size and mtime
    for file_path in sorted(fs_paths & db_paths):
        fs_info = fs_files[file_path]
        db_info = db_files.get(file_path, {})

        if not fs_info.get('exists', True):
            changes.append(f"文件不存在: {file_path}")
            continue
        if not db_info.get('exists', True):
            changes.append(f"数据库中文件不存在: {file_path}")
            continue

        fs_size = fs_info.get('size', 0)
        db_size = db_info.get('size', 0)
        if fs_size != db_size:
            changes.append(f"大小变化: {file_path} ({db_size} -> {fs_size})")

        fs_mtime = fs_info.get('modified')
        db_mtime = db_info.get('modified')
        if fs_mtime and db_mtime and fs_mtime > db_mtime:
            changes.append(f"修改时间更新: {file_path}")

    return changes


def validate_sync_plan_actions(
    actions: List[Dict[str, str]],
    max_actions: int = 1000,
) -> List[str]:
    """
    Validate a list of sync actions for conflicts and limits.

    Each action dict must have 'action_type' and 'resource_id'.

    Returns list of error strings.
    """
    errors: List[str] = []

    if len(actions) > max_actions:
        errors.append(f"同步动作过多 ({len(actions)})，可能存在配置问题")

    # Check for duplicate resource_id across different action types
    resource_actions: Dict[str, List[str]] = {}
    for action in actions:
        rid = action.get('resource_id', '')
        atype = action.get('action_type', '')
        if rid not in resource_actions:
            resource_actions[rid] = []
        resource_actions[rid].append(atype)

    for rid, atypes in resource_actions.items():
        if len(atypes) > 1:
            errors.append(f"资源 {rid} 存在冲突的同步动作: {atypes}")

    return errors
