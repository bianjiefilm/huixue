#!/usr/bin/env python3
"""
step1_clean_workspace.py — 物理骨架重塑 & A/B 类隔离清洗脚本

核心原则：
    1. 绝不修改原始 ziyuan_data/ 目录，所有操作基于 shutil.copytree() 复制
    2. 默认 --dry-run 模式，仅打印行动计划表
    3. 加 --force 参数才执行真实复制
    4. 乱码目录与正常目录的「影分身」自动合并到同一英文目标

用法：
    python3 step1_clean_workspace.py                  # Dry-Run 模式
    python3 step1_clean_workspace.py --force           # 执行真实复制
    python3 step1_clean_workspace.py --source /path    # 指定源目录
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================
# ANSI Colors
# ============================================================
if sys.stdout.isatty():
    R = "\033[91m"; Y = "\033[93m"; G = "\033[92m"; C = "\033[96m"
    B = "\033[1m"; D = "\033[2m"; X = "\033[0m"
else:
    R = Y = G = C = B = D = X = ""

# ============================================================
# 1. MASTER MAPPING DICTIONARY
#    Key   = 原始中文/乱码目录名 (basename)
#    Value = (英文kebab-case目标名, A/B分类)
#    分类: "A" = 交互式沙箱课程, "B" = 传统图文课件
# ============================================================

# --- 实训资源 (Trainings) — 均为 A 类 ---
TRAINING_MAP: Dict[str, Tuple[str, str]] = {
    "01-某零售企业经营分析":         ("01-retail-business-analysis",        "A"),
    "02-公募基金精准营销案例":       ("02-fund-precision-marketing",        "A"),
    "03-A股上市公司销售额分析":      ("03-a-share-sales-analysis",          "A"),
    "04-公募基金精准营销案例":       ("04-fund-marketing-advanced",         "A"),  # 第二个同名
    "04-客户流失模型预测":           ("04-customer-churn-prediction",       "A"),
    "05-电商销售BI分析":             ("05-ecommerce-sales-bi",             "A"),
    "06-企业用能环保监测分析":       ("06-energy-monitoring",               "A"),
}

# --- 课程资源 (Courses) — 逐个判定 A/B ---
COURSE_MAP: Dict[str, Tuple[str, str]] = {
    # B 类: 含大量 PDF/MP4/Office, 纯传统图文课件
    "数据清洗":                     ("data-cleaning",                     "B"),  # 54 PDF/docx
    "数据采集与预处理":             ("data-collection-preprocessing",     "B"),  # 94 PDF/MP4
    "大数据技术基础与应用实践":     ("bigdata-fundamentals-practice",     "B"),  # 102 PDF/MP4
    "Python程序设计":               ("python-programming",                "B"),  # 220 PDF/MP4
    "Spark编程基础":                ("spark-basics",                      "B"),  # 189 PDF/MP4
    "数据挖掘分析":                 ("data-mining-analysis",              "B"),  # 94 PDF/MP4 (虽含6个ipynb但以PDF/MP4为主)
    "神经网络与深度学习":           ("neural-network-deep-learning",      "B"),  # 48 PDF/MP4

    # A 类: 含真实数据集/metadata/cover, 符合沙箱规范
    "零售经营分析":                 ("retail-analysis",                   "A"),  # 有 metadata + datasets + cover
    "公募基金精准营销":             ("fund-marketing-practice",           "A"),  # 有 metadata + datasets + code
    "应收账款管理":                 ("accounts-receivable",               "A"),  # 有 CSV 数据集
}


# ============================================================
# 2. ACTION PLAN BUILDER
# ============================================================

class ActionItem:
    """Represents a single copy/merge action."""
    def __init__(self, source: Path, target: Path, action: str, classification: str, note: str = ""):
        self.source = source
        self.target = target
        self.action = action           # "COPY" | "MERGE"
        self.classification = classification  # "A" | "B"
        self.note = note

    def __repr__(self):
        return f"{self.action} [{self.classification}] {self.source.name} -> {self.target.name}"


def build_action_plan(source_root: Path, target_root: Path) -> List[ActionItem]:
    """Scan source_root and build the complete action plan."""
    actions = []
    seen_targets: Dict[str, ActionItem] = {}  # target_name -> first ActionItem (for merge detection)

    # --- Scan 实训资源 ---
    train_dir = source_root / "实训资源"
    if train_dir.exists():
        for sub in sorted(train_dir.iterdir()):
            if not sub.is_dir() or sub.name.startswith('.'):
                continue
            mapping = TRAINING_MAP.get(sub.name)
            if mapping:
                eng_name, cls = mapping
            else:
                # Unknown training — default to A with sanitized name
                eng_name = sanitize_dirname(sub.name)
                cls = "A"

            bucket = "A_Interactive_Courses" if cls == "A" else "B_Legacy_Materials"
            # Trainings go under trainings/ sub-path
            target_path = target_root / bucket / "trainings" / eng_name

            if eng_name in seen_targets:
                # Shadow clone detected — merge!
                action = ActionItem(sub, target_path, "MERGE", cls,
                    f"影分身合并: 与 '{seen_targets[eng_name].source.name}' 合并")
            else:
                action = ActionItem(sub, target_path, "COPY", cls)
                seen_targets[eng_name] = action

            actions.append(action)

    # --- Scan 课程资源 ---
    course_dir = source_root / "课程资源"
    if course_dir.exists():
        for sub in sorted(course_dir.iterdir()):
            if not sub.is_dir() or sub.name.startswith('.'):
                continue
            mapping = COURSE_MAP.get(sub.name)
            if mapping:
                eng_name, cls = mapping
            else:
                eng_name = sanitize_dirname(sub.name)
                cls = "B"  # Unknown courses default to B-class (safety)

            bucket = "A_Interactive_Courses" if cls == "A" else "B_Legacy_Materials"
            sub_path = "courses" if cls == "A" else "courses"
            target_path = target_root / bucket / sub_path / eng_name

            if eng_name in seen_targets:
                action = ActionItem(sub, target_path, "MERGE", cls,
                    f"影分身合并: 与 '{seen_targets[eng_name].source.name}' 合并")
            else:
                action = ActionItem(sub, target_path, "COPY", cls)
                seen_targets[eng_name] = action

            actions.append(action)

    return actions


def sanitize_dirname(name: str) -> str:
    """Best-effort conversion of Chinese/garbled directory names to kebab-case ASCII."""
    import re
    # Strip numeric prefix like "01-" and reattach after conversion
    prefix_match = re.match(r'^(\d{2})-(.+)$', name)
    if prefix_match:
        prefix = prefix_match.group(1)
        rest = prefix_match.group(2)
    else:
        prefix = ""
        rest = name

    # Attempt known translations
    known = {
        "某零售企业经营分析": "retail-business-analysis",
        "公募基金精准营销案例": "fund-precision-marketing",
        "A股上市公司销售额分析": "a-share-sales-analysis",
        "客户流失模型预测": "customer-churn-prediction",
        "电商销售BI分析": "ecommerce-sales-bi",
        "企业用能环保监测分析": "energy-monitoring",
    }

    if rest in known:
        slug = known[rest]
    else:
        # Fallback: strip non-ASCII, lowercase, replace spaces
        slug = re.sub(r'[^\x00-\x7F]+', '', rest).strip()
        slug = slug.lower().replace(' ', '-').replace('_', '-')
        slug = re.sub(r'-+', '-', slug).strip('-')
        if not slug:
            slug = "unknown-resource"

    if prefix:
        return f"{prefix}-{slug}"
    return slug


# ============================================================
# 3. EXECUTION ENGINE
# ============================================================

def copy_tree_merge(src: Path, dst: Path):
    """Copy a directory tree, merging into existing dst if it already exists."""
    if not dst.exists():
        shutil.copytree(str(src), str(dst))
    else:
        # Merge: walk src and copy missing files into dst
        for item in src.rglob("*"):
            rel = item.relative_to(src)
            target = dst / rel
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            elif item.is_file():
                if not target.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(item), str(target))
                # If target already exists, skip (first-copy wins)


def execute_plan(actions: List[ActionItem], target_root: Path, dry_run: bool = True):
    """Execute or preview the action plan."""

    # --- Print the action table ---
    a_count = sum(1 for a in actions if a.classification == "A")
    b_count = sum(1 for a in actions if a.classification == "B")
    merge_count = sum(1 for a in actions if a.action == "MERGE")

    print(f"\n{B}{'='*78}")
    print(f"  🏗️  物理骨架重塑 行动计划表")
    print(f"  目标根目录: {target_root}")
    print(f"  模式: {G}--dry-run (预览){X}" if dry_run else f"  模式: {R}--force (执行){X}")
    print(f"{'='*78}{X}\n")

    print(f"  {C}A 类 (沙箱实训):{X} {a_count} 个   {Y}B 类 (传统课件):{X} {b_count} 个   "
          f"{R}影分身合并:{X} {merge_count} 个\n")

    print(f"  {B}{'─'*76}{X}")
    print(f"  {B}{'原始目录名':<30s} {'动作':<8s} {'分类':^4s} {'目标英文路径'}{X}")
    print(f"  {B}{'─'*76}{X}")

    for a in actions:
        cls_color = G if a.classification == "A" else Y
        act_color = R if a.action == "MERGE" else G
        src_display = a.source.name[:28]
        tgt_display = str(a.target.relative_to(a.target.parent.parent.parent))
        note = f"  ← {a.note}" if a.note else ""
        print(f"  {src_display:<30s} {act_color}{a.action:<8s}{X} "
              f"{cls_color}{a.classification:^4s}{X} {tgt_display}{D}{note}{X}")

    print(f"\n  {B}{'─'*76}{X}")

    if dry_run:
        print(f"\n  {Y}⚠️  以上为预览模式。确认无误后请运行:{X}")
        print(f"  {B}    python3 step1_clean_workspace.py --force{X}\n")
        return

    # --- Execute ---
    print(f"\n  {G}▶ 开始执行复制...{X}\n")

    # Create top-level structure
    (target_root / "A_Interactive_Courses" / "trainings").mkdir(parents=True, exist_ok=True)
    (target_root / "A_Interactive_Courses" / "courses").mkdir(parents=True, exist_ok=True)
    (target_root / "B_Legacy_Materials" / "courses").mkdir(parents=True, exist_ok=True)

    for i, a in enumerate(actions, 1):
        label = f"[{i}/{len(actions)}]"
        if a.action == "MERGE":
            print(f"  {label} {R}MERGE{X} {a.source.name} -> {a.target.name}")
            copy_tree_merge(a.source, a.target)
        else:
            print(f"  {label} {G}COPY{X}  {a.source.name} -> {a.target.name}")
            copy_tree_merge(a.source, a.target)

    # Final stats
    a_dir = target_root / "A_Interactive_Courses"
    b_dir = target_root / "B_Legacy_Materials"
    a_total = sum(1 for _ in a_dir.rglob("*") if _.is_file()) if a_dir.exists() else 0
    b_total = sum(1 for _ in b_dir.rglob("*") if _.is_file()) if b_dir.exists() else 0

    print(f"\n{B}{'='*78}")
    print(f"  ✅ 复制完成！")
    print(f"{'='*78}{X}")
    print(f"  A_Interactive_Courses/ : {G}{a_total}{X} 个文件")
    print(f"  B_Legacy_Materials/   : {Y}{b_total}{X} 个文件")
    print(f"\n  {C}下一步: 对 A 目录运行盘点探针:{X}")
    print(f"  {B}    python3 local_scanner.py {target_root / 'A_Interactive_Courses'}{X}\n")


# ============================================================
# 4. MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="物理骨架重塑 & A/B类隔离清洗 (Clean Room Builder)"
    )
    parser.add_argument("--force", action="store_true",
        help="执行真实复制 (默认为 dry-run 预览模式)")
    parser.add_argument("--source", type=str, default=None,
        help="源目录路径 (默认: 脚本同目录的 ziyuan_data/)")
    parser.add_argument("--target", type=str, default=None,
        help="目标净室路径 (默认: 源目录同级的 ziyuan_normalized/)")

    args = parser.parse_args()

    # Resolve source
    if args.source:
        source_root = Path(args.source).resolve()
    else:
        script_dir = Path(__file__).resolve().parent
        source_root = script_dir / "ziyuan_data"

    if not source_root.exists():
        print(f"{R}错误: 源目录不存在: {source_root}{X}")
        sys.exit(1)

    # Resolve target
    if args.target:
        target_root = Path(args.target).resolve()
    else:
        target_root = source_root.parent / "ziyuan_normalized"

    if target_root.exists() and args.force:
        print(f"{Y}⚠️  目标目录已存在: {target_root}{X}")
        print(f"{Y}   将增量合并到已有目录中。{X}")

    # Build plan
    actions = build_action_plan(source_root, target_root)

    if not actions:
        print(f"{Y}未发现任何可处理的资源目录。{X}")
        sys.exit(0)

    # Execute
    execute_plan(actions, target_root, dry_run=not args.force)


if __name__ == "__main__":
    main()
