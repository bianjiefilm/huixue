#!/usr/bin/env python3
"""
使用Edge TTS生成《神经网络与深度学习》课程语音
"""
import asyncio
import json
from pathlib import Path
import edge_tts


COURSE_DIR = "/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/课程资源/神经网络与深度学习"
SCRIPTS_DIR = f"{COURSE_DIR}/assets/scripts"
AUDIO_DIR = f"{COURSE_DIR}/assets/audio"

# 使用晓晓(活泼女声)
VOICE = "zh-CN-XiaoxiaoNeural"


async def generate_all_audio():
    """生成所有章节的语音"""
    # 读取脚本文件
    scripts_file = Path(SCRIPTS_DIR) / "all_scripts.json"
    with open(scripts_file, 'r', encoding='utf-8') as f:
        all_scripts = json.load(f)

    Path(AUDIO_DIR).mkdir(parents=True, exist_ok=True)

    total_slides = sum(len(ch["slides"]) for ch in all_scripts)
    current = 0

    for chapter in all_scripts:
        chapter_id = chapter["id"]
        chapter_title = chapter["title"]
        print(f"\n处理章节 {chapter_id}: {chapter_title}")

        for slide in chapter["slides"]:
            current += 1
            slide_idx = slide["slide_index"]
            script_text = slide["script"]
            slide_title = slide["title"]

            output_path = f"{AUDIO_DIR}/chapter_{chapter_id}_slide_{slide_idx:02d}.mp3"

            print(f"  [{current}/{total_slides}] {slide_title[:20]}...")

            try:
                communicate = edge_tts.Communicate(script_text, VOICE)
                await communicate.save(output_path)
                print(f"    ✅ 已保存")
            except Exception as e:
                print(f"    ❌ 失败: {e}")

    print(f"\n✅ 语音生成完成")
    print(f"   保存位置: {AUDIO_DIR}")

    # 列出生成的文件
    audio_files = list(Path(AUDIO_DIR).glob("*.mp3"))
    print(f"   共生成 {len(audio_files)} 个音频文件")


if __name__ == "__main__":
    print("=" * 60)
    print("使用Edge TTS生成课程语音")
    print("=" * 60)
    asyncio.run(generate_all_audio())
