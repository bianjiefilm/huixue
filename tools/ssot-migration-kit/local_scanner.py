#!/usr/bin/env python3
"""
local_scanner.py — SSOT V3.0 本地资源盘点探针 (100% Read-Only)

基于《Practice-Training-Directory-Whitepaper-SSOT-V3.0》规范设计。
本脚本绝不写入任何文件、绝不修改任何数据、绝不发起任何网络请求。
它只做一件事：扫描本地物理目录，输出红黄绿灯统计报告。

用法:
    python3 local_scanner.py [scan_root]
    python3 local_scanner.py [scan_root] --json      # JSON 机器可读输出
    默认 scan_root 为脚本同目录下的 ziyuan_data/

退出码:
    0 = 全绿 或 仅有 WARNING (CI 不阻断)
    1 = 存在 BLOCKER 级别问题 (CI 必须阻断)
"""

import os
import sys
import json
import csv
import re
import io
import argparse
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple

# ============================================================
# ANSI Colors (graceful fallback for non-TTY)
# ============================================================
if sys.stdout.isatty():
    C_RED     = "\033[91m"
    C_YELLOW  = "\033[93m"
    C_GREEN   = "\033[92m"
    C_CYAN    = "\033[96m"
    C_BOLD    = "\033[1m"
    C_DIM     = "\033[2m"
    C_RESET   = "\033[0m"
else:
    C_RED = C_YELLOW = C_GREEN = C_CYAN = C_BOLD = C_DIM = C_RESET = ""

# ============================================================
# Constants from Whitepaper
# ============================================================
SLUG_RE       = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
TASK_DIR_RE   = re.compile(r'^\d{2}-[a-z0-9]+(-[a-z0-9]+)*$')
NON_ASCII_RE  = re.compile(r'[^\x00-\x7F]')

# Minimum thresholds
MIN_CSV_ROWS_PRACTICE  = 10   # Whitepaper 3.1: ≥ 10 data rows
MIN_CSV_ROWS_TRAINING  = 50   # Whitepaper 3.2.1: ≥ 50 data rows
MIN_HANDBOOK_BYTES     = 100  # Whitepaper CI check #10
FAKE_CSV_MAX_ROWS      = 5    # If CSV ≤ 5 rows in a training, flag as suspicious fake data
FAKE_FILE_MAX_BYTES    = 50   # Files under 50 bytes are suspicious placeholders

# Named check IDs beyond whitepaper CI 1-14 range
CHECK_B_CLASS_DETECTION = 99  # B-class document course detection (§Action Item #4)

# Minimum consecutive garbled characters for positive mojibake detection
MIN_GARBLED_CONSECUTIVE = 2

# Legacy -> SSOT mapping (for detection)
LEGACY_TRAINING_DIR = "实训资源"
LEGACY_COURSE_DIR   = "课程资源"
LEGACY_PRACTICE_DIR = "课程实践"

@dataclass
class Issue:
    severity: str       # "BLOCKER" | "WARNING"
    resource_path: str  # relative path from scan root
    check_id: int       # CI checklist number
    message: str

@dataclass
class ResourceReport:
    path: str
    resource_type: str  # "training" | "practice" | "course_legacy" | "unknown"
    display_name: str
    issues: List[Issue] = field(default_factory=list)
    info: dict = field(default_factory=dict)

    @property
    def status(self) -> str:
        if any(i.severity == "BLOCKER" for i in self.issues):
            return "RED"
        elif any(i.severity == "WARNING" for i in self.issues):
            return "YELLOW"
        return "GREEN"

    @property
    def status_icon(self) -> str:
        return {"RED": f"{C_RED}❌", "YELLOW": f"{C_YELLOW}⚠️", "GREEN": f"{C_GREEN}✅"}[self.status]


# ============================================================
# Utility Functions (ALL READ-ONLY)
# ============================================================

def has_non_ascii(name: str) -> bool:
    """Check if a directory/file name contains non-ASCII (Chinese, garbled, etc.)."""
    return bool(NON_ASCII_RE.search(name))

def is_garbled(name: str) -> bool:
    """Heuristic: detect mojibake via consecutive garbled character patterns.
    
    Upgraded from single-char detection to consecutive-2+ pattern matching
    to eliminate false positives on rare but legitimate CJK characters.
    CP936→UTF-8 double-decode produces characteristic sequences where
    garbled chars cluster together; legitimate Chinese never does.
    
    The char set below (81 chars) was extracted from actual garbled filenames
    observed in this codebase's ziyuan_data/ directory.
    """
    # All 81 mojibake codepoints observed in CP936→UTF-8 double-decode artifacts
    garbled_chars = set(
        'ュ傝勬叓叚呭呮唽嗗嗘嗛垚垬堪姒娓娲婕嬪寮崲嵁嶇彇忔戠撳敤斂旂暟杞杩洓浇浠浣涜'
        '澶濇瀹炴炶版犺狅瑙疆礂秷竴竷竻笁簩簱簲粌粶織绔绗缃藉跨鍐鍒鍔鎬鎭鎵鎶鎹'
        '鏁鏃鐜鐨閰閲闆ф'
    )
    consecutive = 0
    for ch in name:
        if ch in garbled_chars:
            consecutive += 1
            if consecutive >= MIN_GARBLED_CONSECUTIVE:
                return True
        else:
            consecutive = 0
    return False

def safe_json_load(filepath: Path) -> Tuple[Optional[dict], Optional[str]]:
    """Attempt to load a JSON file. Returns (data, error_msg).
    
    Design note: Unlike CSV reading (which uses errors='replace' to gracefully
    degrade on encoding issues), JSON is read in strict mode. This is intentional:
    JSON encoding corruption = structural integrity failure = must be a BLOCKER.
    CSV encoding corruption = content-level issue = can degrade and warn.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"JSONDecodeError at line {e.lineno} col {e.colno}: {e.msg}"
    except UnicodeDecodeError as e:
        return None, f"UnicodeDecodeError: {e}"
    except Exception as e:
        return None, str(e)

def count_csv_rows(filepath: Path) -> Tuple[int, Optional[str]]:
    """Count data rows in a CSV (excluding header). Returns (row_count, error_msg).
    
    Uses errors='replace' intentionally: CSV encoding damage is a content-level
    issue that should degrade gracefully rather than crash the scanner.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                return 0, "CSV is completely empty (no header)"
            count = sum(1 for _ in reader)
            return count, None
    except Exception as e:
        return 0, str(e)

def check_csv_headers_english(filepath: Path) -> Tuple[bool, Optional[str]]:
    """Check if CSV headers are English (no Chinese characters)."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                return False, "No header row"
            for col in header:
                if has_non_ascii(col.strip()):
                    return False, f"Non-ASCII header found: '{col.strip()}'"
            return True, None
    except Exception as e:
        return False, str(e)

def file_has_content(filepath: Path, min_bytes: int = 1) -> bool:
    """Check if a file exists and has at least min_bytes."""
    return filepath.exists() and filepath.stat().st_size >= min_bytes

def human_size(size_bytes: int) -> str:
    """Pretty-print file size with appropriate precision."""
    value = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if value < 1024:
            return f"{value:.0f} {unit}" if unit == 'B' else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"

def check_evaluation_has_assert(filepath: Path) -> Tuple[bool, Optional[str]]:
    """Check if evaluation.py contains assert statements."""
    try:
        content = filepath.read_text(encoding='utf-8', errors='replace')
        # Count assert statements (not inside comments or strings — simple heuristic)
        lines = content.split('\n')
        assert_count = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            if re.search(r'\bassert\b', stripped):
                assert_count += 1
        return assert_count > 0, f"Found {assert_count} assert statement(s)"
    except Exception as e:
        return False, str(e)

def safe_iterdir(directory: Path) -> list:
    """Safely list directory contents, catching PermissionError."""
    try:
        return list(directory.iterdir())
    except PermissionError:
        return []
    except OSError:
        return []

def safe_rglob(directory: Path, pattern: str = "*") -> list:
    """Safely recursive-glob, catching PermissionError."""
    results = []
    try:
        for item in directory.rglob(pattern):
            try:
                results.append(item)
            except PermissionError:
                continue
    except PermissionError:
        pass
    except OSError:
        pass
    return results

# ============================================================
# Scanners
# ============================================================

def scan_training(train_dir: Path, scan_root: Path) -> ResourceReport:
    """Scan a single Training directory per SSOT-T-v3.0."""
    rel = train_dir.relative_to(scan_root)
    report = ResourceReport(
        path=str(rel),
        resource_type="training",
        display_name=train_dir.name
    )

    # --- Check #1: Directory name (kebab-case validation)
    if has_non_ascii(train_dir.name):
        sev = "WARNING"
        msg = f"目录名包含非ASCII字符 (违反SSOT V3.0 §1.3 kebab-case规范): '{train_dir.name}'"
        if is_garbled(train_dir.name):
            sev = "BLOCKER"
            msg = f"目录名包含乱码 (Mojibake): '{train_dir.name}'"
        report.issues.append(Issue(sev, str(rel), 1, msg))
    elif not SLUG_RE.match(train_dir.name.split('-', 1)[-1] if '-' in train_dir.name else train_dir.name):
        # Allow NN- prefix (e.g. "01-retail"), validate the slug portion
        report.issues.append(Issue("WARNING", str(rel), 1,
            f"目录名不完全符合 kebab-case: '{train_dir.name}'"))

    # --- Check #2: metadata.json exists
    meta_path = train_dir / "metadata.json"
    if not meta_path.exists():
        report.issues.append(Issue("BLOCKER", str(rel), 2,
            "缺少 metadata.json (SOUL 灵魂文件不存在，同步引擎将拒绝导入)"))
    else:
        meta, err = safe_json_load(meta_path)
        if err:
            report.issues.append(Issue("BLOCKER", str(rel), 2,
                f"metadata.json 解析失败: {err}"))
        else:
            report.info['metadata'] = meta
            # Check #3: ssotVersion
            ver = meta.get('ssotVersion', '')
            if ver != 'SSOT-T-v3.0':
                report.issues.append(Issue("BLOCKER", str(rel), 3,
                    f"metadata.json ssotVersion 不匹配 (期望 'SSOT-T-v3.0', 实际 '{ver}')"))

            # Required fields check
            for key in ['title', 'envType']:
                if not meta.get(key):
                    report.issues.append(Issue("BLOCKER", str(rel), 3,
                        f"metadata.json 缺少必要字段: '{key}'"))

            report.info['envType'] = meta.get('envType', 'UNKNOWN')

    # --- Check #4: cover image
    has_cover = any((train_dir / f"cover.{ext}").exists() for ext in ['png', 'jpg', 'jpeg', 'webp'])
    if not has_cover:
        report.issues.append(Issue("WARNING", str(rel), 4,
            "缺少封面图片 cover.[png|jpg]"))

    # --- Check #10: handbook.md
    hb = train_dir / "handbook.md"
    if not hb.exists():
        report.issues.append(Issue("BLOCKER", str(rel), 10,
            "缺少 handbook.md (SOUL 灵魂文件不存在，同步引擎将拒绝导入)"))
    elif hb.stat().st_size < MIN_HANDBOOK_BYTES:
        report.issues.append(Issue("WARNING", str(rel), 10,
            f"handbook.md 内容过少 ({human_size(hb.stat().st_size)})，可能为占位符"))

    # --- Check #11 & #12: Visceral files by envType
    env_type = report.info.get('envType', 'UNKNOWN')
    datasets_dir = train_dir / "datasets"

    if env_type in ('gwalk_bi', 'coding_jupyter', 'UNKNOWN'):
        # Check #11: datasets/ not empty
        if not datasets_dir.exists() or not safe_iterdir(datasets_dir):
            report.issues.append(Issue("BLOCKER", str(rel), 11,
                f"datasets/ 目录为空或不存在 (envType={env_type}, 需要真实数据集)"))
        else:
            csv_files = list(datasets_dir.glob("*.csv"))
            if not csv_files:
                report.issues.append(Issue("BLOCKER", str(rel), 11,
                    f"datasets/ 中没有 .csv 文件 (envType={env_type})"))
            for cf in csv_files:
                sz = cf.stat().st_size
                row_count, csv_err = count_csv_rows(cf)
                if csv_err:
                    report.issues.append(Issue("WARNING", str(rel), 11,
                        f"CSV读取错误 {cf.name}: {csv_err}"))
                elif sz <= FAKE_FILE_MAX_BYTES:
                    report.issues.append(Issue("BLOCKER", str(rel), 11,
                        f"🚨 疑似假数据! {cf.name} 仅 {human_size(sz)}，严重低于真实数据集标准"))
                elif row_count <= FAKE_CSV_MAX_ROWS:
                    report.issues.append(Issue("BLOCKER", str(rel), 11,
                        f"🚨 疑似假数据! {cf.name} 仅 {row_count} 数据行 (标准≥{MIN_CSV_ROWS_TRAINING})"))
                elif row_count < MIN_CSV_ROWS_TRAINING:
                    report.issues.append(Issue("WARNING", str(rel), 11,
                        f"{cf.name} 数据行不足 ({row_count}/{MIN_CSV_ROWS_TRAINING})"))

                # Header quality
                eng_ok, eng_err = check_csv_headers_english(cf)
                if not eng_ok and eng_err:
                    report.issues.append(Issue("WARNING", str(rel), 13,
                        f"{cf.name} 表头问题: {eng_err}"))

    if env_type == 'coding_jupyter':
        # Check #12: jupyter/ has .ipynb
        jupyter_dir = train_dir / "jupyter"
        if not jupyter_dir.exists() or not list(jupyter_dir.glob("*.ipynb")):
            report.issues.append(Issue("BLOCKER", str(rel), 12,
                "jupyter/ 中没有 .ipynb 文件 (envType=coding_jupyter需要Jupyter模板)"))
        else:
            for nb in jupyter_dir.glob("*.ipynb"):
                nb_data, nb_err = safe_json_load(nb)
                if nb_err:
                    report.issues.append(Issue("BLOCKER", str(rel), 12,
                        f"Jupyter文件损坏 {nb.name}: {nb_err}"))
                elif nb_data:
                    cells = nb_data.get('cells', [])
                    if len(cells) == 0:
                        report.issues.append(Issue("WARNING", str(rel), 12,
                            f"{nb.name} 为空Notebook (0 cells)"))
                    elif len(cells) == 1:
                        src = ''.join(cells[0].get('source', []))
                        if 'Hello' in src and len(src) < 50:
                            report.issues.append(Issue("BLOCKER", str(rel), 12,
                                f"🚨 疑似假数据! {nb.name} 仅含1个Hello World cell，非真实教学内容"))

    if env_type == 'vdi_ai':
        workflow_dir = train_dir / "workflow"
        if not workflow_dir.exists() or not list(workflow_dir.glob("*.knwf")):
            report.issues.append(Issue("BLOCKER", str(rel), 12,
                "workflow/ 中没有 .knwf 文件 (envType=vdi_ai需要工作流文件)"))

    # --- Check #14: Path length + garbled deep path dedup
    garbled_deep_count = 0
    first_garbled_deep = None
    for fp in safe_rglob(train_dir):
        if len(str(fp)) > 200:
            report.issues.append(Issue("WARNING", str(rel), 14,
                f"文件路径过长 ({len(str(fp))} chars): ...{str(fp)[-60:]}"))
        if is_garbled(fp.name):
            garbled_deep_count += 1
            if first_garbled_deep is None:
                first_garbled_deep = fp.name
    if garbled_deep_count > 0:
        suffix = f" (及其他 {garbled_deep_count - 1} 个乱码路径)" if garbled_deep_count > 1 else ""
        report.issues.append(Issue("BLOCKER", str(rel), 1,
            f"发现深层乱码路径: .../{first_garbled_deep}{suffix}"))

    return report


def scan_practice(prac_dir: Path, scan_root: Path) -> ResourceReport:
    """Scan a single Practice directory per SSOT-P-v3.0."""
    rel = prac_dir.relative_to(scan_root)
    report = ResourceReport(
        path=str(rel),
        resource_type="practice",
        display_name=prac_dir.name
    )

    # --- Check #1: Directory naming
    if has_non_ascii(prac_dir.name):
        sev = "BLOCKER" if is_garbled(prac_dir.name) else "WARNING"
        report.issues.append(Issue(sev, str(rel), 1,
            f"目录名包含非ASCII字符: '{prac_dir.name}'"))

    # --- Check #2: metadata.json
    meta_path = prac_dir / "metadata.json"
    if not meta_path.exists():
        report.issues.append(Issue("BLOCKER", str(rel), 2,
            "缺少 metadata.json (SOUL文件不存在)"))
    else:
        meta, err = safe_json_load(meta_path)
        if err:
            report.issues.append(Issue("BLOCKER", str(rel), 2,
                f"metadata.json 解析失败: {err}"))
        else:
            report.info['metadata'] = meta
            ver = meta.get('ssotVersion', '')
            if ver != 'SSOT-P-v3.0':
                report.issues.append(Issue("BLOCKER", str(rel), 3,
                    f"ssotVersion 不匹配 (期望 'SSOT-P-v3.0', 实际 '{ver}')"))

    # --- Check #4: cover image
    has_cover = any((prac_dir / f"cover.{ext}").exists() for ext in ['png', 'jpg', 'jpeg', 'webp'])
    if not has_cover:
        report.issues.append(Issue("WARNING", str(rel), 4, "缺少封面图片"))

    # --- Check #5: tasks/ directory
    tasks_dir = prac_dir / "tasks"
    if not tasks_dir.exists():
        report.issues.append(Issue("BLOCKER", str(rel), 5,
            "缺少 tasks/ 目录 (Practice必须至少包含1个关卡)"))
    else:
        task_subdirs = [d for d in sorted(safe_iterdir(tasks_dir)) if d.is_dir()]
        if len(task_subdirs) == 0:
            report.issues.append(Issue("BLOCKER", str(rel), 5,
                "tasks/ 目录为空 (至少需要1个关卡子目录)"))
        for td in task_subdirs:
            # Check #1.5: Task directory naming regex
            if not TASK_DIR_RE.match(td.name):
                report.issues.append(Issue("BLOCKER", str(rel), 1,
                    f"关卡目录命名不合规: '{td.name}' (应为 NN-kebab-case, 如 01-hello-world)"))
            # Check #6: task.json + handbook.md in each task dir
            if not (td / "task.json").exists():
                report.issues.append(Issue("BLOCKER", str(rel), 6,
                    f"关卡 {td.name}/ 缺少 task.json"))
            else:
                tj_data, tj_err = safe_json_load(td / "task.json")
                if tj_err:
                    report.issues.append(Issue("BLOCKER", str(rel), 6,
                        f"关卡 {td.name}/task.json 解析失败: {tj_err}"))
            if not (td / "handbook.md").exists():
                report.issues.append(Issue("BLOCKER", str(rel), 6,
                    f"关卡 {td.name}/ 缺少 handbook.md"))

    # --- Check #7: repo/evaluation.py
    eval_py = prac_dir / "repo" / "evaluation.py"
    if not eval_py.exists():
        report.issues.append(Issue("BLOCKER", str(rel), 7,
            "缺少 repo/evaluation.py (自动评测心脏)"))
    else:
        # Check #8: assert statements
        has_assert, assert_msg = check_evaluation_has_assert(eval_py)
        if not has_assert:
            report.issues.append(Issue("BLOCKER", str(rel), 8,
                f"evaluation.py 中找不到 assert 语句 — 自动评测无效！({assert_msg})"))

    # --- Check #9: datasets/*.csv
    datasets_dir = prac_dir / "datasets"
    if datasets_dir.exists():
        for cf in datasets_dir.glob("*.csv"):
            row_count, csv_err = count_csv_rows(cf)
            sz = cf.stat().st_size
            if sz <= FAKE_FILE_MAX_BYTES:
                report.issues.append(Issue("BLOCKER", str(rel), 9,
                    f"🚨 疑似假数据! {cf.name} 仅 {human_size(sz)}"))
            elif row_count < MIN_CSV_ROWS_PRACTICE:
                report.issues.append(Issue("WARNING", str(rel), 9,
                    f"{cf.name} 数据行不足 ({row_count}/{MIN_CSV_ROWS_PRACTICE})"))
    else:
        # INFO-level: not all practices require datasets, but worth noting
        report.info['no_datasets'] = True

    return report


def scan_legacy_course(course_dir: Path, scan_root: Path) -> ResourceReport:
    """Scan a legacy Course directory (B-class detection)."""
    rel = course_dir.relative_to(scan_root)
    report = ResourceReport(
        path=str(rel),
        resource_type="course_legacy",
        display_name=course_dir.name
    )

    # B-class detection: does this look like a traditional document course?
    has_pdf  = bool(safe_rglob(course_dir, "*.pdf"))
    has_mp4  = bool(safe_rglob(course_dir, "*.mp4"))
    has_docx = bool(safe_rglob(course_dir, "*.docx") + safe_rglob(course_dir, "*.doc"))
    has_pptx = bool(safe_rglob(course_dir, "*.pptx") + safe_rglob(course_dir, "*.ppt"))
    has_eval = bool(safe_rglob(course_dir, "evaluation.py"))
    has_ipynb = bool(safe_rglob(course_dir, "*.ipynb"))

    b_class_indicators = sum([has_pdf, has_mp4, has_docx, has_pptx])
    a_class_indicators = sum([has_eval, has_ipynb])

    if b_class_indicators > 0 and a_class_indicators == 0:
        report.info['classification'] = 'B-CLASS (传统文档课件)'
        report.issues.append(Issue("BLOCKER", str(rel), CHECK_B_CLASS_DETECTION,
            f"B类课件检测! 包含 PDF/MP4/Office 文档但无沙箱可执行内容。"
            f"严禁作为A类实训入库 (白皮书 §Action Item #4)"))
    elif a_class_indicators > 0:
        report.info['classification'] = 'A-CLASS (沙箱实训)'
    else:
        report.info['classification'] = 'UNCLASSIFIED'

    # Garbled path detection (deduplicated: max 1 BLOCKER per resource)
    garbled_count = 0
    first_garbled = None
    for fp in safe_rglob(course_dir):
        if is_garbled(fp.name):
            garbled_count += 1
            if first_garbled is None:
                first_garbled = fp.name
    if garbled_count > 0:
        suffix = f" (及其他 {garbled_count - 1} 个乱码路径)" if garbled_count > 1 else ""
        report.issues.append(Issue("BLOCKER", str(rel), 1,
            f"发现乱码路径: .../{first_garbled}{suffix}"))

    # metadata.json check
    meta_path = course_dir / "metadata.json"
    if not meta_path.exists():
        report.issues.append(Issue("WARNING", str(rel), 2,
            "缺少 metadata.json"))
    else:
        meta, err = safe_json_load(meta_path)
        if err:
            report.issues.append(Issue("BLOCKER", str(rel), 2,
                f"metadata.json 解析失败: {err}"))

    return report


# ============================================================
# Main Scanner
# ============================================================

def discover_resources(scan_root: Path) -> List[ResourceReport]:
    """Walk the scan root and discover all resources."""
    reports = []

    # Scan trainings
    for tdir_name in [LEGACY_TRAINING_DIR, "trainings", "content/trainings"]:
        tdir = scan_root / tdir_name
        if tdir.exists():
            for sub in sorted(tdir.iterdir()):
                if sub.is_dir() and not sub.name.startswith('.') and not sub.name.startswith('_'):
                    reports.append(scan_training(sub, scan_root))

    # Scan practices
    for pdir_name in [LEGACY_PRACTICE_DIR, "practices", "content/practices"]:
        pdir = scan_root / pdir_name
        if pdir.exists():
            for sub in sorted(pdir.iterdir()):
                if sub.is_dir() and not sub.name.startswith('.') and not sub.name.startswith('_'):
                    reports.append(scan_practice(sub, scan_root))

    # Scan legacy courses
    for cdir_name in [LEGACY_COURSE_DIR, "courses", "content/courses"]:
        cdir = scan_root / cdir_name
        if cdir.exists():
            for sub in sorted(cdir.iterdir()):
                if sub.is_dir() and not sub.name.startswith('.') and not sub.name.startswith('_'):
                    reports.append(scan_legacy_course(sub, scan_root))

    return reports


def print_report(reports: List[ResourceReport], scan_root: Path):
    """Print the final colored terminal report."""
    
    print(f"\n{C_BOLD}{'='*70}")
    print(f"  📡 SSOT V3.0 本地资源盘点探针报告")
    print(f"  扫描路径: {scan_root}")
    print(f"{'='*70}{C_RESET}\n")

    # Summary counters
    total = len(reports)
    greens = sum(1 for r in reports if r.status == "GREEN")
    yellows = sum(1 for r in reports if r.status == "YELLOW")
    reds = sum(1 for r in reports if r.status == "RED")
    total_blockers = sum(1 for r in reports for i in r.issues if i.severity == "BLOCKER")
    total_warnings = sum(1 for r in reports for i in r.issues if i.severity == "WARNING")

    # Group by type
    type_labels = {
        "training": "🏋️  实训 (Training)",
        "practice": "🧪 实践 (Practice)",
        "course_legacy": "📚 课程包 (Course/Legacy)"
    }

    for rtype, label in type_labels.items():
        typed = [r for r in reports if r.resource_type == rtype]
        if not typed:
            continue
        print(f"{C_BOLD}{C_CYAN}{label} ({len(typed)} 个){C_RESET}")
        print(f"{C_DIM}{'─'*68}{C_RESET}")

        for r in typed:
            icon = r.status_icon
            env = r.info.get('envType', '')
            cls = r.info.get('classification', '')
            extra = f" [{env}]" if env else (f" [{cls}]" if cls else "")
            print(f"  {icon} {C_BOLD}{r.display_name}{C_RESET}{C_DIM}{extra}{C_RESET}")

            blockers = [i for i in r.issues if i.severity == "BLOCKER"]
            warnings = [i for i in r.issues if i.severity == "WARNING"]

            for issue in blockers:
                print(f"      {C_RED}✖ [BLOCKER #{issue.check_id}] {issue.message}{C_RESET}")
            for issue in warnings:
                print(f"      {C_YELLOW}△ [WARNING #{issue.check_id}] {issue.message}{C_RESET}")

            if not r.issues:
                print(f"      {C_GREEN}所有检查通过{C_RESET}")

        print()

    # Final summary
    print(f"{C_BOLD}{'='*70}")
    print(f"  📊 最终统计")
    print(f"{'='*70}{C_RESET}")
    print(f"  扫描资源总数: {C_BOLD}{total}{C_RESET}")
    print(f"  {C_GREEN}✅ 通过 (GREEN): {greens}{C_RESET}")
    print(f"  {C_YELLOW}⚠️  警告 (YELLOW): {yellows}{C_RESET}")
    print(f"  {C_RED}❌ 阻断 (RED):    {reds}{C_RESET}")
    print()
    print(f"  BLOCKER 总数: {C_RED if total_blockers else C_GREEN}{total_blockers}{C_RESET}")
    print(f"  WARNING 总数: {C_YELLOW if total_warnings else C_GREEN}{total_warnings}{C_RESET}")
    print()

    if reds > 0:
        print(f"  {C_RED}{C_BOLD}⛔ 判定结果: 不可部署 (存在 {reds} 个阻断级问题){C_RESET}")
        print(f"  {C_RED}请先在本地修复所有 BLOCKER 后再向服务器同步！{C_RESET}")
    elif yellows > 0:
        print(f"  {C_YELLOW}{C_BOLD}⚠️  判定结果: 有条件部署 (存在 {yellows} 个警告){C_RESET}")
        print(f"  {C_YELLOW}建议修复所有 WARNING 以达到完美合规。{C_RESET}")
    else:
        print(f"  {C_GREEN}{C_BOLD}🎉 判定结果: 全绿通过！可以安全同步到服务器！{C_RESET}")

    print(f"\n{C_DIM}本脚本为 100% 只读操作，未修改任何文件。{C_RESET}\n")

    return reds, yellows


def reports_to_json(reports: List[ResourceReport]) -> str:
    """Serialize all reports to JSON for CI/CD pipeline consumption."""
    output = []
    for r in reports:
        entry = {
            "path": r.path,
            "resource_type": r.resource_type,
            "display_name": r.display_name,
            "status": r.status,
            "issues": [
                {
                    "severity": i.severity,
                    "check_id": i.check_id,
                    "message": i.message
                }
                for i in r.issues
            ],
            "info": {k: v for k, v in r.info.items() if k != 'metadata'}  # exclude large metadata blob
        }
        output.append(entry)
    return json.dumps(output, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="SSOT V3.0 本地资源盘点探针 (100% Read-Only)"
    )
    parser.add_argument("scan_root", nargs="?", default=None,
        help="扫描根目录 (默认: 脚本同目录的 ziyuan_data/)")
    parser.add_argument("--json", action="store_true", dest="json_output",
        help="输出 JSON 格式 (机器可读, 适用于 CI/CD 流水线)")

    args = parser.parse_args()

    # Determine scan root
    if args.scan_root:
        scan_root = Path(args.scan_root).resolve()
    else:
        script_dir = Path(__file__).resolve().parent
        scan_root = script_dir / "ziyuan_data"
        if not scan_root.exists():
            scan_root = script_dir  # fallback to script dir itself

    if not scan_root.exists():
        print(f"{C_RED}错误: 扫描路径不存在: {scan_root}{C_RESET}", file=sys.stderr)
        sys.exit(1)

    if not args.json_output:
        print(f"{C_DIM}正在扫描 {scan_root} ...{C_RESET}")

    reports = discover_resources(scan_root)

    if not reports:
        if args.json_output:
            print("[]")
        else:
            print(f"{C_YELLOW}未发现任何可识别的资源目录。")
            print(f"请确认目录结构包含: 实训资源/ | 课程资源/ | content/trainings/ | content/practices/{C_RESET}")
        sys.exit(0)

    if args.json_output:
        print(reports_to_json(reports))
    else:
        print_report(reports, scan_root)

    # Exit code: 1 = has BLOCKERs (CI must block), 0 = safe (GREEN or WARNING-only)
    has_blockers = any(i.severity == "BLOCKER" for r in reports for i in r.issues)
    sys.exit(1 if has_blockers else 0)


if __name__ == "__main__":
    main()
