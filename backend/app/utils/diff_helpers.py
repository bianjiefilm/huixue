"""
Pure helper functions for resource_sync v1 diff_engine.

Extracted from services/resource_sync/diff_engine.py — no DB, no I/O, no logging.
"""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple


# ==================== Set operations ====================

def find_new_keys(fs_keys: Set[str], db_keys: Set[str]) -> Set[str]:
    """Return resource IDs present in filesystem but not in database."""
    return fs_keys - db_keys


def find_deleted_keys(fs_keys: Set[str], db_keys: Set[str]) -> Set[str]:
    """Return resource IDs present in database but not in filesystem."""
    return db_keys - fs_keys


# ==================== Deletion action ====================

_HARD_DELETE_PATTERN = re.compile(
    r'(?:^|[\s_\-])(?:test|demo)(?:[\s_\-]|$)|临时',
    re.IGNORECASE,
)


def determine_deletion_action(title: str) -> str:
    """
    Decide soft_delete vs delete based on resource title keywords.

    Returns 'delete' for test/demo/临时 resources, 'soft_delete' otherwise.
    Uses word-boundary matching to avoid false positives (e.g. "contest").
    """
    if _HARD_DELETE_PATTERN.search(title):
        return 'delete'
    return 'soft_delete'


# ==================== Version comparison ====================

def should_mark_version_change(
    fs_modified: datetime,
    db_modified: datetime,
    fs_checksum: Optional[str],
    db_checksum: Optional[str],
) -> bool:
    """
    Determine whether a resource has a version-level change.

    A change is detected when:
    - filesystem is newer than database, OR
    - checksums differ (even if timestamps are equal)
    """
    if fs_modified > db_modified:
        return True
    return fs_checksum != db_checksum


# ==================== Metadata field comparison ====================

_COMPARABLE_FIELDS = [
    'title', 'intro', 'industry', 'difficulty', 'course_hours',
    'estimated_completion_time', 'max_students', 'is_active',
]

_ARRAY_FIELDS = ['prerequisites', 'learning_objectives', 'tags']

_TRAINING_FIELDS = ['training_type', 'require_design_files']


def compare_metadata_fields(
    fs_metadata: Any,
    db_metadata: Dict[str, Any],
) -> List[Tuple[str, Any, Any]]:
    """
    Compare metadata fields between a filesystem metadata object and a DB dict.

    fs_metadata: object with attributes (getattr)
    db_metadata: plain dict

    Returns list of (field_name, old_value, new_value) tuples for changed fields.
    """
    changes: List[Tuple[str, Any, Any]] = []

    # Scalar fields
    for field in _COMPARABLE_FIELDS:
        fs_value = getattr(fs_metadata, field, None)
        db_value = db_metadata.get(field)
        if fs_value != db_value:
            changes.append((field, db_value, fs_value))

    # Array fields — compared as sets
    for field in _ARRAY_FIELDS:
        fs_value = getattr(fs_metadata, field, [])
        db_value = db_metadata.get(field, [])
        if set(fs_value) != set(db_value):
            changes.append((field, db_value, fs_value))

    # Training-specific fields
    if hasattr(fs_metadata, 'training_type'):
        for field in _TRAINING_FIELDS:
            fs_value = getattr(fs_metadata, field, None)
            db_value = db_metadata.get(field)
            if fs_value != db_value:
                changes.append((field, db_value, fs_value))

        # Assignment nodes
        if hasattr(fs_metadata, 'assignment_nodes'):
            fs_nodes = fs_metadata.assignment_nodes
            db_nodes = db_metadata.get('assignment_nodes', [])
            if fs_nodes != db_nodes:
                changes.append(('assignment_nodes', db_nodes, fs_nodes))

    return changes


# ==================== File dependency comparison ====================

def compare_file_keys(
    fs_files: Dict[str, Any],
    db_files: Dict[str, Any],
) -> Tuple[List[str], List[str]]:
    """
    Compare file dependency dicts by their keys.

    Returns (added_files, removed_files).
    """
    added = [p for p in fs_files if p not in db_files]
    removed = [p for p in db_files if p not in fs_files]
    return added, removed
