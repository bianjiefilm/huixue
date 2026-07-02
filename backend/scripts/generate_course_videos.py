#!/usr/bin/env python3
"""
课程视频生成工具
PPT + 语音 = 视频
"""
import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def pptx_to_images(pptx_path: str, output_dir: str) -> List[str]:
    """
    将PPT转换为图片序列

    Args:
        pptx_path: PPT文件路径
        output_dir: 输出目录

    Returns:
        图片文件路径列表
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 使用LibreOffice转换PPT为PDF
    pdf_path = Path(output_dir) / "slides.pdf"

    # 转换为PDF
    cmd_pdf = [
        "soffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", output_dir,
        pptx_path
    ]

    try:
        subprocess.run(cmd_pdf, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"PPT转PDF失败: {e}")
        # 尝试使用unoconv
        try:
            subprocess.run(["unoconv", "-f", "pdf", "-o", output_dir, pptx_path], check=True)
        except:
            print("请安装LibreOffice或unoconv")
            return []

    # 查找生成的PDF
    pdf_files = list(Path(output_dir).glob("*.pdf"))
    if not pdf_files:
        print("未找到生成的PDF文件")
        return []

    pdf_path = pdf_files[0]

    # 使用ImageMagick将PDF转换为图片
    image_pattern = Path(output_dir) / "slide_%03d.png"
    cmd_images = [
        "convert",
        "-density", "150",
        "-quality", "90",
        str(pdf_path),
        str(image_pattern)
    ]

    try:
        subprocess.run(cmd_images, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"PDF转图片失败: {e}")
        # 尝试使用pdftoppm
        try:
            subprocess.run([
                "pdftoppm",
                "-png",
                "-r", "150",
                str(pdf_path),
                str(Path(output_dir) / "slide")
            ], check=True)
        except:
            print("请安装ImageMagick或poppler-utils")
            return []

    # 获取生成的图片列表
    images = sorted(Path(output_dir).glob("slide*.png"))
    return [str(img) for img in images]


def create_video_from_images_and_audio(
    images: List[str],
    audio_files: List[str],
    output_path: str,
    fps: int = 1
) -> bool:
    """
    从图片和音频创建视频

    Args:
        images: 图片文件列表
        audio_files: 音频文件列表（与图片一一对应）
        output_path: 输出视频路径
        fps: 帧率

    Returns:
        是否成功
    """
    if len(images) != len(audio_files):
        print(f"图片数量({len(images)})与音频数量({len(audio_files)})不匹配")
        return False

    temp_dir = Path(output_path).parent / "temp_video"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 为每个片段创建视频
    segment_videos = []

    for i, (img, audio) in enumerate(zip(images, audio_files)):
        segment_path = temp_dir / f"segment_{i:03d}.mp4"

        # 获取音频时长
        duration_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            audio
        ]
        result = subprocess.run(duration_cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip()) if result.stdout.strip() else 5.0

        # 创建视频片段
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img,
            "-i", audio,
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            "-shortest",
            str(segment_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            segment_videos.append(str(segment_path))
        except subprocess.CalledProcessError as e:
            print(f"创建片段{i}失败: {e}")
            continue

    if not segment_videos:
        print("未生成任何视频片段")
        return False

    # 合并所有片段
    list_file = temp_dir / "segments.txt"
    with open(list_file, 'w') as f:
        for seg in segment_videos:
            f.write(f"file '{seg}'\n")

    concat_cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        output_path
    ]

    try:
        subprocess.run(concat_cmd, check=True, capture_output=True)
        print(f"视频已保存: {output_path}")

        # 清理临时文件
        import shutil
        shutil.rmtree(temp_dir)

        return True
    except subprocess.CalledProcessError as e:
        print(f"合并视频失败: {e}")
        return False


def create_simple_video(
    image_path: str,
    audio_path: str,
    output_path: str
) -> bool:
    """
    创建简单的图片+音频视频

    Args:
        image_path: 图片路径
        audio_path: 音频路径
        output_path: 输出路径

    Returns:
        是否成功
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"视频已保存: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"创建视频失败: {e}")
        print(e.stderr.decode() if e.stderr else "")
        return False


def generate_chapter_video(
    chapter_id: str,
    chapter_title: str,
    ppt_path: str,
    audio_dir: str,
    output_path: str
) -> bool:
    """
    生成章节视频

    Args:
        chapter_id: 章节ID
        chapter_title: 章节标题
        ppt_path: PPT文件路径
        audio_dir: 音频文件目录
        output_path: 输出视频路径

    Returns:
        是否成功
    """
    print(f"\n处理章节: {chapter_title}")

    # 1. PPT转图片
    temp_dir = Path(output_path).parent / f"temp_{chapter_id}"
    images = pptx_to_images(ppt_path, str(temp_dir))

    if not images:
        print(f"PPT转图片失败")
        return False

    print(f"  生成 {len(images)} 张幻灯片图片")

    # 2. 收集对应的音频文件
    audio_pattern = Path(audio_dir) / f"chapter_{chapter_id}_slide_*.mp3"
    audio_files = sorted(Path(audio_dir).glob(f"chapter_{chapter_id}_slide_*.mp3"))

    if len(audio_files) < len(images):
        print(f"  警告: 音频文件不足 ({len(audio_files)} < {len(images)})")
        # 使用默认音频或跳过
        return False

    # 3. 创建视频
    success = create_video_from_images_and_audio(
        images[:len(audio_files)],
        [str(a) for a in audio_files],
        output_path
    )

    # 4. 清理
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    return success


if __name__ == "__main__":
    # 测试
    print("课程视频生成工具")
    print("使用方法: python generate_course_videos.py")
