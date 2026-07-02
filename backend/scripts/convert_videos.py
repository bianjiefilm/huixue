#!/usr/bin/env python3
"""
批量转换视频为Web兼容格式的脚本
使用 H.264 Main Profile Level 3.1，确保浏览器兼容性
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

# 禁用输出缓冲
sys.stdout.reconfigure(line_buffering=True)

RESOURCE_DIR = Path("/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/课程资源")
BACKUP_DIR = Path("/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/课程资源_原始备份")

def log(msg):
    print(msg, flush=True)

def get_video_profile(file_path):
    """获取视频的 profile"""
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=profile',
            '-of', 'csv=p=0', str(file_path)
        ], capture_output=True, text=True, timeout=30)
        return result.stdout.strip()
    except Exception as e:
        log(f"    ⚠ 无法读取 profile: {e}")
        return None

def convert_video(input_path, output_path):
    """转换视频为 Web 兼容格式"""
    try:
        result = subprocess.run([
            'ffmpeg', '-y', '-i', str(input_path),
            '-c:v', 'libx264', '-profile:v', 'main', '-level', '3.1',
            '-preset', 'medium', '-crf', '20',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            str(output_path)
        ], capture_output=True, text=True, timeout=1800)  # 30分钟超时
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        log("    ⚠ 转码超时")
        return False
    except Exception as e:
        log(f"    ⚠ 转码错误: {e}")
        return False

def main():
    log("=" * 50)
    log("视频批量转码脚本 - Web兼容格式 (Python版)")
    log("=" * 50)
    log("")

    # 创建备份目录
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # 统计
    total = 0
    skipped = 0
    converted = 0
    failed = 0

    # 收集所有视频文件
    video_files = list(RESOURCE_DIR.rglob("*.mp4"))
    log(f"找到 {len(video_files)} 个视频文件")
    log("")

    for video_path in sorted(video_files):
        total += 1
        relative_path = video_path.relative_to(RESOURCE_DIR)
        log(f"[{total}/{len(video_files)}] {relative_path}")

        # 检查是否已是兼容格式
        profile = get_video_profile(video_path)
        if profile in ['Main', 'Baseline']:
            log(f"    ✓ 已是兼容格式 ({profile})，跳过")
            skipped += 1
            continue

        # 创建备份
        backup_path = BACKUP_DIR / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)

        if not backup_path.exists():
            log("    → 备份原文件...")
            try:
                shutil.copy2(video_path, backup_path)
            except Exception as e:
                log(f"    ⚠ 备份失败: {e}")
                failed += 1
                continue

        # 转码到临时文件
        temp_path = video_path.with_suffix('.temp.mp4')
        log(f"    → 转码中 (profile={profile})...")

        if convert_video(video_path, temp_path):
            # 替换原文件
            try:
                temp_path.replace(video_path)
                log("    ✓ 转码完成")
                converted += 1
            except Exception as e:
                log(f"    ⚠ 替换文件失败: {e}")
                temp_path.unlink(missing_ok=True)
                failed += 1
        else:
            temp_path.unlink(missing_ok=True)
            log("    ✗ 转码失败")
            failed += 1

        log("")

    log("=" * 50)
    log("转码完成!")
    log(f"总计: {total} 个视频")
    log(f"跳过: {skipped} 个 (已是兼容格式)")
    log(f"转码: {converted} 个")
    log(f"失败: {failed} 个")
    log(f"原文件已备份到: {BACKUP_DIR}")
    log("=" * 50)

if __name__ == "__main__":
    main()
