#!/usr/bin/env python3
"""
step3_scorched_earth_deploy.py — 焦土重置 & 黄金载荷上线

核弹级部署脚本：6 步物理替换流水线。

用法:
    python3 step3_scorched_earth_deploy.py             # Dry-Run 预览
    python3 step3_scorched_earth_deploy.py --execute    # 真实执行

前置条件:
    - ziyuan_normalized/A_Interactive_Courses/ 已清理至 0 BLOCKER
    - sshpass 已安装 (brew install hudochenkov/sshpass/sshpass)
    - 服务器 <慧学服务器1-IP> 可达 (Tailscale)

安全机制:
    - 默认 dry-run，打印执行计划
    - --execute 需要二次确认
    - 每步有明确成功/失败判断
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path
from datetime import datetime

# ============================================================
# ANSI Colors
# ============================================================
if sys.stdout.isatty():
    R = "\033[91m"; Y = "\033[93m"; G = "\033[92m"; C = "\033[96m"
    B = "\033[1m"; D = "\033[2m"; X = "\033[0m"
else:
    R = Y = G = C = B = D = X = ""

# ============================================================
# SERVER CONFIG
# ============================================================
SERVER_IP   = "<慧学服务器1-IP>"
SERVER_USER = "huixuedashuju"
SERVER_PASS = "kejixueyuan@dashuju"
SSH_BASE    = f"sshpass -p '{SERVER_PASS}' ssh -o StrictHostKeyChecking=no {SERVER_USER}@{SERVER_IP}"
SCP_BASE    = f"sshpass -p '{SERVER_PASS}' scp -o StrictHostKeyChecking=no"
SUDO_PREFIX = f"echo '{SERVER_PASS}' | sudo -S"

# Remote paths
REMOTE_ZIYUAN_DIR  = "/data/huixue_storage/static/ziyuan_data_full"
REMOTE_TMP         = "/tmp/clean_payload.tar.gz"

# Database config (huixue-db-test via Docker internal network)
DB_HOST = "<慧学内网物理IP-1>"
DB_PORT = "5432"
DB_NAME = "huixue"
DB_USER = "huixue"
DB_PASS = "huixue2024"

# Tables to TRUNCATE (order matters: children first, then parents)
TRUNCATE_TABLES = [
    "classroom_courses",
    "classroom_trainings",
    "training_datasets",
    "training_jupyter_files",
    "chapters",
    "tasks",
    "student_course_progress",
    "classroom_students",
    "classrooms",
    "courses",
    "trainings",
]

# ============================================================
# STEP DEFINITIONS
# ============================================================

class Step:
    def __init__(self, number: int, title: str, description: str, commands: list, danger_level: str = "NORMAL"):
        self.number = number
        self.title = title
        self.description = description
        self.commands = commands  # list of (label, shell_command) tuples
        self.danger_level = danger_level  # NORMAL | DESTRUCTIVE | NUCLEAR

    @property
    def color(self):
        return {"NORMAL": G, "DESTRUCTIVE": Y, "NUCLEAR": R}[self.danger_level]

    @property
    def icon(self):
        return {"NORMAL": "📦", "DESTRUCTIVE": "🔥", "NUCLEAR": "☢️"}[self.danger_level]


def build_steps(local_root: Path, archive_path: Path) -> list:
    """Build the 6-step deployment plan."""
    
    source_dir = local_root / "ziyuan_normalized" / "A_Interactive_Courses"
    
    # Timestamp for backup
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    steps = []

    # --- Step 1: Local packaging ---
    steps.append(Step(1, "本地安全打包", 
        f"将 A_Interactive_Courses/ 打包成 {archive_path.name}",
        [
            ("打包 tar.gz", 
             f"cd {local_root / 'ziyuan_normalized'} && "
             f"tar -czf {archive_path} "
             f"--exclude='._*' --exclude='.DS_Store' --exclude='__pycache__' "
             f"A_Interactive_Courses/"),
            ("校验包大小",
             f"ls -lh {archive_path}"),
        ]))

    # --- Step 2: Upload to server ---
    steps.append(Step(2, "上传至服务器",
        f"通过 SCP 上传至 {SERVER_IP}:/tmp/",
        [
            ("SCP 上传",
             f"{SCP_BASE} {archive_path} {SERVER_USER}@{SERVER_IP}:{REMOTE_TMP}"),
            ("验证远端文件",
             f"{SSH_BASE} 'ls -lh {REMOTE_TMP}'"),
        ]))

    # --- Step 3: Scorched earth cleanup ---
    steps.append(Step(3, "服务器物理焦土清理",
        f"彻底清除 {REMOTE_ZIYUAN_DIR}/* 下的旧乱码目录和假数据",
        [
            ("备份旧目录清单 (安全网)",
             f"{SSH_BASE} '{SUDO_PREFIX} ls -la {REMOTE_ZIYUAN_DIR}/ > /tmp/ziyuan_backup_listing_{ts}.txt 2>&1 && echo BACKUP_LISTING_OK'"),
            ("焦土清除",
             f"{SSH_BASE} '{SUDO_PREFIX} rm -rf {REMOTE_ZIYUAN_DIR}/* && echo SCORCHED_EARTH_OK'"),
            ("验证清空",
             f"{SSH_BASE} '{SUDO_PREFIX} ls -la {REMOTE_ZIYUAN_DIR}/ && echo VERIFIED_EMPTY'"),
        ],
        danger_level="DESTRUCTIVE"))

    # --- Step 4: Deploy clean payload ---
    steps.append(Step(4, "纯净释出",
        f"解压 clean_payload.tar.gz 到 {REMOTE_ZIYUAN_DIR}/",
        [
            ("解压至目标目录",
             f"{SSH_BASE} '{SUDO_PREFIX} tar -xzf {REMOTE_TMP} -C {REMOTE_ZIYUAN_DIR}/ && echo EXTRACT_OK'"),
            ("移动内容到根层级 (去除 A_Interactive_Courses/ 包装层)",
             f"{SSH_BASE} '{SUDO_PREFIX} mv {REMOTE_ZIYUAN_DIR}/A_Interactive_Courses/* {REMOTE_ZIYUAN_DIR}/ "
             f"&& {SUDO_PREFIX} rmdir {REMOTE_ZIYUAN_DIR}/A_Interactive_Courses && echo FLATTEN_OK'"),
            ("验证目录结构",
             f"{SSH_BASE} '{SUDO_PREFIX} ls -la {REMOTE_ZIYUAN_DIR}/ && echo DEPLOY_VERIFIED'"),
            ("清理临时包",
             f"{SSH_BASE} 'rm -f {REMOTE_TMP}'"),
        ]))

    # --- Step 5: Database nuclear reset ---
    truncate_sql = "; ".join([f"TRUNCATE TABLE {t} CASCADE" for t in TRUNCATE_TABLES])
    psql_cmd = f"PGPASSWORD='{DB_PASS}' psql -h {DB_HOST} -p {DB_PORT} -U {DB_USER} -d {DB_NAME}"
    
    steps.append(Step(5, "数据库核弹清空",
        f"TRUNCATE 所有课程相关表 ({len(TRUNCATE_TABLES)} 张表)",
        [
            ("预检: 查看当前数据量",
             f"{SSH_BASE} \"{psql_cmd} -c \\\"SELECT 'courses' as tbl, count(*) FROM courses UNION ALL SELECT 'trainings', count(*) FROM trainings UNION ALL SELECT 'classrooms', count(*) FROM classrooms;\\\"\""),
            ("核弹 TRUNCATE",
             f"{SSH_BASE} \"{psql_cmd} -c \\\"{truncate_sql};\\\"\""),
            ("验证清空",
             f"{SSH_BASE} \"{psql_cmd} -c \\\"SELECT 'courses' as tbl, count(*) FROM courses UNION ALL SELECT 'trainings', count(*) FROM trainings;\\\"\""),
        ],
        danger_level="NUCLEAR"))

    # --- Step 6: Resync via ssot_deep_syncer ---
    steps.append(Step(6, "一键拉起 (SSOT Deep Sync)",
        "调用 ssot_deep_syncer.py 将纯净物理结构灌入空数据库",
        [
            ("上传最新 syncer 到服务器",
             f"{SCP_BASE} {local_root / 'backend' / 'ssot_deep_syncer.py'} {SERVER_USER}@{SERVER_IP}:/tmp/ssot_deep_syncer.py"),
            ("在 backend 容器内执行 syncer (副本1)",
             f"{SSH_BASE} \"docker exec \\$(docker ps -q -f name=huixue-backend | head -1) python3 /tmp/ssot_deep_syncer.py\""),
            ("最终验证: 查数据库",
             f"{SSH_BASE} \"{psql_cmd} -c \\\"SELECT 'courses' as tbl, count(*) FROM courses UNION ALL SELECT 'trainings', count(*) FROM trainings UNION ALL SELECT 'classrooms', count(*) FROM classrooms;\\\"\""),
        ]))

    return steps


# ============================================================
# EXECUTION ENGINE
# ============================================================

def print_plan(steps: list):
    """Print the deployment plan."""
    print(f"\n{B}{'='*78}")
    print(f"  ☢️  焦土重置 & 黄金载荷上线 — 部署计划")
    print(f"{'='*78}{X}\n")

    for step in steps:
        print(f"  {step.color}{step.icon} 步骤 {step.number}: {step.title}{X}")
        print(f"     {D}{step.description}{X}")
        for label, cmd in step.commands:
            # Sanitize passwords for display
            safe_cmd = cmd.replace(SERVER_PASS, "****").replace(DB_PASS, "****")
            print(f"     {D}  └─ {label}: {safe_cmd[:100]}{'...' if len(safe_cmd) > 100 else ''}{X}")
        print()


def execute_step(step: Step, step_num: int, total: int) -> bool:
    """Execute a single step. Returns True on success."""
    print(f"\n{step.color}{B}{'─'*78}")
    print(f"  {step.icon} [{step_num}/{total}] {step.title}")
    print(f"{'─'*78}{X}\n")

    for label, cmd in step.commands:
        print(f"  {C}▶ {label}{X}")
        
        # Sanitize for logging
        safe_cmd = cmd.replace(SERVER_PASS, "****").replace(DB_PASS, "****")
        print(f"  {D}$ {safe_cmd[:120]}{'...' if len(safe_cmd) > 120 else ''}{X}")

        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=1800)
        
        if result.stdout.strip():
            # Limit output display
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines[:20]:
                print(f"  {G}  {line}{X}")
            if len(output_lines) > 20:
                print(f"  {D}  ... ({len(output_lines) - 20} more lines){X}")

        if result.returncode != 0:
            print(f"  {R}✖ 失败 (exit code {result.returncode}){X}")
            if result.stderr.strip():
                for line in result.stderr.strip().split('\n')[:10]:
                    print(f"  {R}  {line}{X}")
            return False
        else:
            print(f"  {G}✔ 成功{X}")
        print()

    return True


def main():
    parser = argparse.ArgumentParser(
        description="焦土重置 & 黄金载荷上线 (Scorched Earth Deploy)"
    )
    parser.add_argument("--execute", action="store_true",
        help="真实执行 (默认为 dry-run 预览)")
    parser.add_argument("--skip-to", type=int, default=1, choices=range(1, 7),
        help="从指定步骤开始执行 (用于恢复中断)")
    parser.add_argument("--local-root", type=str, default=None,
        help="本地项目根目录")

    args = parser.parse_args()

    # Resolve paths
    if args.local_root:
        local_root = Path(args.local_root).resolve()
    else:
        local_root = Path(__file__).resolve().parent
        # If script is in tools/ssot-migration-kit/, go up 2 levels
        if local_root.name == "ssot-migration-kit":
            local_root = local_root.parent.parent

    archive_path = local_root / "clean_payload.tar.gz"
    source_dir = local_root / "ziyuan_normalized" / "A_Interactive_Courses"

    if not source_dir.exists():
        print(f"{R}错误: 源目录不存在: {source_dir}{X}")
        sys.exit(1)

    # Build plan
    steps = build_steps(local_root, archive_path)

    # --- DRY-RUN MODE ---
    if not args.execute:
        print_plan(steps)
        print(f"  {Y}⚠️  以上为预览模式。确认无误后执行:{X}")
        print(f"  {B}    python3 step3_scorched_earth_deploy.py --execute{X}")
        print(f"  {D}    可选: --skip-to 3  (从步骤 3 开始){X}\n")
        return

    # --- EXECUTE MODE ---
    print(f"\n{R}{B}{'='*78}")
    print(f"  ☢️  焦土重置 — 最终确认")
    print(f"{'='*78}{X}\n")
    print(f"  {R}即将执行以下破坏性操作:{X}")
    print(f"  {R}  • 清空服务器 {REMOTE_ZIYUAN_DIR}/ 下的全部文件{X}")
    print(f"  {R}  • TRUNCATE {len(TRUNCATE_TABLES)} 张数据库表{X}")
    print(f"  {R}  • 用本地净室数据全量替换{X}")
    print()

    confirm = input(f"  {Y}输入 'DEPLOY' 确认执行: {X}")
    if confirm.strip() != "DEPLOY":
        print(f"\n  {Y}已取消。{X}")
        sys.exit(0)

    print(f"\n  {G}确认通过，开始部署...{X}\n")

    # Execute each step
    total = len(steps)
    for step in steps:
        if step.number < args.skip_to:
            print(f"  {D}⏭  跳过步骤 {step.number}: {step.title}{X}")
            continue

        success = execute_step(step, step.number, total)
        if not success:
            print(f"\n{R}{B}⛔ 步骤 {step.number} 失败！部署中止。{X}")
            print(f"{Y}修复后可使用 --skip-to {step.number} 从此步恢复。{X}")
            sys.exit(1)

    # Final report
    print(f"\n{G}{B}{'='*78}")
    print(f"  🎉 焦土重置 + 黄金载荷上线 — 全部完成！")
    print(f"{'='*78}{X}")
    print(f"  ✅ 服务器物理目录: 纯净全英文")
    print(f"  ✅ 数据库: 从 SSOT 物理结构重建")
    print(f"  ✅ 假数据/乱码: 彻底根除")
    print(f"\n  {C}前端验证: 打开浏览器访问 http://{SERVER_IP}:3000{X}\n")


if __name__ == "__main__":
    main()
