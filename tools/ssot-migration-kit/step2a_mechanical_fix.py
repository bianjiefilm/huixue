#!/usr/bin/env python3
"""
step2a_mechanical_fix.py — 纯机械扫雷：乱码重命名 + BOM 清洗

作用于 ziyuan_normalized/ 目录。
1. 将残留乱码子目录重命名为标准英文名
2. 清洗 CSV/JSON 文件的 UTF-8 BOM 头
3. 完成后自动调用 local_scanner.py 验证
"""

import os
import sys
import subprocess
from pathlib import Path

# ============================================================
# ANSI Colors
# ============================================================
if sys.stdout.isatty():
    R = "\033[91m"; Y = "\033[93m"; G = "\033[92m"; C = "\033[96m"
    B = "\033[1m"; D = "\033[2m"; X = "\033[0m"
else:
    R = Y = G = C = B = D = X = ""

# ============================================================
# 1. GARBLED -> ENGLISH RENAME MAP (deep sub-directories)
# ============================================================
GARBLED_RENAME_MAP = {
    "瀹炶鎵嬪唽":     "handbook_assets",    # 实训手册 (garbled)
    "浠ｇ爜":         "repo",               # 代码 (garbled)
}

# ============================================================
# 2. RENAME ENGINE
# ============================================================

def rename_garbled_dirs(root: Path) -> int:
    """Recursively find and rename garbled directories."""
    count = 0
    # We need to collect first then rename to avoid iterator invalidation
    to_rename = []
    
    for dirpath, dirnames, filenames in os.walk(str(root), topdown=False):
        for dname in dirnames:
            if dname in GARBLED_RENAME_MAP:
                old_path = Path(dirpath) / dname
                new_name = GARBLED_RENAME_MAP[dname]
                new_path = Path(dirpath) / new_name
                to_rename.append((old_path, new_path))
    
    for old_path, new_path in to_rename:
        if new_path.exists():
            # Merge: move contents from old into existing new
            print(f"  {Y}MERGE{X} {old_path.name} -> {new_path.name} (目标已存在,合并内容)")
            for item in old_path.iterdir():
                target = new_path / item.name
                if not target.exists():
                    item.rename(target)
            # Remove old empty dir
            try:
                old_path.rmdir()
            except OSError:
                pass
        else:
            print(f"  {G}RENAME{X} {old_path.name} -> {new_path.name}")
            old_path.rename(new_path)
        count += 1
    
    return count


# ============================================================
# 3. BOM CLEANER
# ============================================================

BOM = b'\xef\xbb\xbf'

def strip_bom_from_file(filepath: Path) -> bool:
    """Remove UTF-8 BOM from a file. Returns True if BOM was found and stripped."""
    try:
        raw = filepath.read_bytes()
        if raw.startswith(BOM):
            filepath.write_bytes(raw[3:])
            return True
        return False
    except (PermissionError, OSError):
        return False


def clean_bom(root: Path) -> int:
    """Scan all .csv and .json files and strip BOM headers."""
    count = 0
    for ext in ['*.csv', '*.json']:
        for fp in root.rglob(ext):
            if strip_bom_from_file(fp):
                print(f"  {G}BOM清除{X} {fp.relative_to(root)}")
                count += 1
    return count


# ============================================================
# 4. MAIN
# ============================================================

def main():
    script_dir = Path(__file__).resolve().parent
    target_root = script_dir / "ziyuan_normalized"
    
    if not target_root.exists():
        print(f"{R}错误: 目标目录不存在: {target_root}{X}")
        sys.exit(1)

    print(f"\n{B}{'='*70}")
    print(f"  🧹 Step 2A: 纯机械扫雷")
    print(f"  作用路径: {target_root}")
    print(f"{'='*70}{X}\n")

    # --- Phase 1: Rename garbled directories ---
    print(f"{C}▶ 阶段1: 乱码目录重命名{X}")
    rename_count = rename_garbled_dirs(target_root)
    print(f"  完成: {rename_count} 个目录已重命名\n")

    # --- Phase 2: BOM cleaning ---
    print(f"{C}▶ 阶段2: UTF-8 BOM 头清洗{X}")
    bom_count = clean_bom(target_root)
    print(f"  完成: {bom_count} 个文件已清除 BOM\n")

    # --- Phase 3: Auto-verify ---
    print(f"{C}▶ 阶段3: 自动调用盘点探针验证{X}")
    print(f"{'─'*70}\n")
    
    scanner_path = script_dir / "local_scanner.py"
    scan_target = target_root / "A_Interactive_Courses"
    
    result = subprocess.run(
        [sys.executable, str(scanner_path), str(scan_target)],
        cwd=str(script_dir)
    )
    
    print(f"\n{B}{'='*70}")
    print(f"  📊 Step 2A 汇总")
    print(f"{'='*70}{X}")
    print(f"  乱码目录重命名: {G}{rename_count}{X} 个")
    print(f"  BOM 头清洗:     {G}{bom_count}{X} 个")
    print(f"  探针退出码:     {result.returncode}")
    print()


if __name__ == "__main__":
    main()
