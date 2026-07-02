#!/usr/bin/env python3
"""
为计算机视觉课程生成PPT和视频资源
使用 Pillow 生成幻灯片图片
使用 Edge TTS 生成语音
使用 FFmpeg 合成视频
"""
import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 配置
COURSE_NAME = "计算机视觉"
COURSE_DIR = Path("/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/课程资源/计算机视觉")
ASSETS_DIR = COURSE_DIR / "assets"
SLIDES_DIR = ASSETS_DIR / "slides"
VIDEOS_DIR = ASSETS_DIR / "videos"
AUDIO_DIR = ASSETS_DIR / "audio"

# 章节配置
CHAPTERS = [
    {"id": "01", "title": "计算机视觉概述", "folder": "01-计算机视觉概述"},
    {"id": "02", "title": "图像标注", "folder": "02-图像标注"},
    {"id": "03", "title": "神经网络基础", "folder": "03-神经网络基础"},
    {"id": "04", "title": "卷积神经网络CNN", "folder": "04-卷积神经网络CNN"},
    {"id": "05", "title": "经典CNN模型", "folder": "05-经典CNN模型"},
    {"id": "06", "title": "目标检测基础", "folder": "06-目标检测基础"},
    {"id": "07", "title": "RCNN系列算法", "folder": "07-RCNN系列算法"},
    {"id": "08", "title": "YOLO系列算法", "folder": "08-YOLO系列算法"},
    {"id": "09", "title": "语义分割", "folder": "09-语义分割"},
    {"id": "10", "title": "目标跟踪", "folder": "10-目标跟踪"},
    {"id": "11", "title": "图像生成", "folder": "11-图像生成"},
]

# 颜色配置
COLORS = {
    "bg_gradient_start": (0, 100, 180),  # 蓝色渐变
    "bg_gradient_end": (0, 150, 220),
    "title": (255, 255, 255),
    "subtitle": (200, 230, 255),
    "text": (240, 240, 240),
}


def create_gradient_background(width, height, color1, color2):
    """创建渐变背景"""
    img = Image.new('RGB', (width, height))
    for y in range(height):
        r = int(color1[0] + (color2[0] - color1[0]) * y / height)
        g = int(color1[1] + (color2[1] - color1[1]) * y / height)
        b = int(color1[2] + (color2[2] - color1[2]) * y / height)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    return img


def get_font(size, bold=False):
    """获取字体"""
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except:
                continue
    return ImageFont.load_default()


def generate_slide(chapter_id, chapter_title, output_path):
    """生成章节幻灯片"""
    width, height = 1920, 1080

    # 创建渐变背景
    img = create_gradient_background(
        width, height,
        COLORS["bg_gradient_start"],
        COLORS["bg_gradient_end"]
    )
    draw = ImageDraw.Draw(img)

    # 课程名称
    font_course = get_font(48)
    course_text = f"《{COURSE_NAME}》"
    bbox = draw.textbbox((0, 0), course_text, font=font_course)
    x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((x, 120), course_text, font=font_course, fill=COLORS["subtitle"])

    # 章节标题
    font_title = get_font(72, bold=True)
    title_text = f"第{chapter_id}章 {chapter_title}"
    bbox = draw.textbbox((0, 0), title_text, font=font_title)
    x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((x, height // 2 - 80), title_text, font=font_title, fill=COLORS["title"])

    # 装饰线
    line_width = 400
    line_y = height // 2 + 40
    draw.rectangle(
        [(width // 2 - line_width // 2, line_y),
         (width // 2 + line_width // 2, line_y + 4)],
        fill=COLORS["subtitle"]
    )

    # 底部信息
    font_footer = get_font(32)
    footer_text = "慧学 平台"
    bbox = draw.textbbox((0, 0), footer_text, font=font_footer)
    x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((x, height - 100), footer_text, font=font_footer, fill=COLORS["text"])

    # 保存
    img.save(output_path)
    print(f"  生成幻灯片: {output_path.name}")


async def generate_audio(text, output_path):
    """使用 Edge TTS 生成语音"""
    try:
        import edge_tts
        voice = "zh-CN-YunxiNeural"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
        print(f"  生成音频: {output_path.name}")
        return True
    except Exception as e:
        print(f"  音频生成失败: {e}")
        return False


def generate_video(slide_path, audio_path, output_path):
    """使用 FFmpeg 合成视频"""
    try:
        # 获取音频时长
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', str(audio_path)],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip())

        # 生成视频
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', str(slide_path),
            '-i', str(audio_path),
            '-c:v', 'libx264', '-tune', 'stillimage',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-t', str(duration),
            '-shortest',
            str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, check=True)
        print(f"  生成视频: {output_path.name}")
        return True
    except Exception as e:
        print(f"  视频生成失败: {e}")
        return False


async def process_chapter(chapter):
    """处理单个章节"""
    chapter_id = chapter["id"]
    chapter_title = chapter["title"]
    chapter_folder = chapter["folder"]

    print(f"\n处理章节: {chapter_id}. {chapter_title}")

    # 生成幻灯片
    slide_filename = f"chapter_{chapter_id}_{chapter_title}.png"
    slide_path = SLIDES_DIR / slide_filename
    generate_slide(chapter_id, chapter_title, slide_path)

    # 读取脚本内容
    script_path = COURSE_DIR / "chapters" / chapter_folder / "sections" / "01-核心原理" / "script.txt"
    if script_path.exists():
        script_text = script_path.read_text(encoding='utf-8')
    else:
        script_text = f"欢迎学习{COURSE_NAME}课程第{chapter_id}章，{chapter_title}。"

    # 限制文本长度 (Edge TTS 限制)
    if len(script_text) > 3000:
        script_text = script_text[:3000] + "..."

    # 生成音频
    audio_filename = f"chapter_{chapter_id}_{chapter_title}.mp3"
    audio_path = AUDIO_DIR / audio_filename
    await generate_audio(script_text, audio_path)

    # 生成视频
    video_filename = f"chapter_{chapter_id}_{chapter_title}.mp4"
    video_path = VIDEOS_DIR / video_filename
    if audio_path.exists():
        generate_video(slide_path, audio_path, video_path)


async def main():
    print("=" * 60)
    print(f"为《{COURSE_NAME}》课程生成PPT和视频资源")
    print("=" * 60)

    # 创建目录
    SLIDES_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    # 处理每个章节
    for chapter in CHAPTERS:
        await process_chapter(chapter)

    print("\n" + "=" * 60)
    print("资源生成完成!")
    print(f"  幻灯片: {SLIDES_DIR}")
    print(f"  视频: {VIDEOS_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
