#!/usr/bin/env python3
"""
《神经网络与深度学习》课程内容生成主脚本
生成PPT + 语音 + 视频
"""
import os
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.generate_course_ppt import CHAPTERS_DATA, generate_all_chapter_ppts, create_chapter_ppt
from scripts.tts_volcengine import VolcengineTTS, VOICE_TYPES


# 配置
COURSE_DIR = "/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/课程资源/神经网络与深度学习"
SLIDES_DIR = f"{COURSE_DIR}/assets/slides"
AUDIO_DIR = f"{COURSE_DIR}/assets/audio"
VIDEO_DIR = f"{COURSE_DIR}/assets/videos"


def step1_generate_ppts():
    """步骤1: 生成所有章节PPT"""
    print("\n" + "=" * 60)
    print("步骤1: 生成PPT课件")
    print("=" * 60)

    Path(SLIDES_DIR).mkdir(parents=True, exist_ok=True)

    for chapter in CHAPTERS_DATA:
        output_path = Path(SLIDES_DIR) / f"chapter_{chapter['id']}_{chapter['title']}.pptx"
        create_chapter_ppt(chapter, str(output_path))

    print(f"\n✅ 共生成 {len(CHAPTERS_DATA)} 个章节PPT")
    print(f"   保存位置: {SLIDES_DIR}")


def step2_generate_voice_scripts():
    """步骤2: 生成语音旁白文本"""
    print("\n" + "=" * 60)
    print("步骤2: 生成语音脚本")
    print("=" * 60)

    scripts_dir = Path(COURSE_DIR) / "assets/scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    all_scripts = []

    for chapter in CHAPTERS_DATA:
        chapter_script = {
            "id": chapter["id"],
            "title": chapter["title"],
            "slides": []
        }

        for i, slide in enumerate(chapter.get("slides", [])):
            if "note" in slide:
                chapter_script["slides"].append({
                    "slide_index": i + 1,  # 跳过标题页
                    "title": slide["title"],
                    "script": slide["note"]
                })

        all_scripts.append(chapter_script)

        # 保存单章节脚本
        script_path = scripts_dir / f"chapter_{chapter['id']}_script.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(f"# {chapter['title']}\n\n")
            for slide in chapter_script["slides"]:
                f.write(f"## {slide['title']}\n")
                f.write(f"{slide['script']}\n\n")

    # 保存完整脚本JSON
    import json
    with open(scripts_dir / "all_scripts.json", 'w', encoding='utf-8') as f:
        json.dump(all_scripts, f, ensure_ascii=False, indent=2)

    print(f"✅ 共生成 {len(all_scripts)} 个章节的语音脚本")
    print(f"   保存位置: {scripts_dir}")

    return all_scripts


def step3_synthesize_audio(scripts: list):
    """步骤3: 调用API合成语音"""
    print("\n" + "=" * 60)
    print("步骤3: 合成语音文件")
    print("=" * 60)

    Path(AUDIO_DIR).mkdir(parents=True, exist_ok=True)

    # 创建TTS客户端
    tts = VolcengineTTS(
        app_id="6026849500",
        access_token="6-HbFN7u0y_OHlwj0rCckrcjJ4iy3dtn"
    )

    total_slides = sum(len(ch["slides"]) for ch in scripts)
    current = 0

    for chapter in scripts:
        chapter_id = chapter["id"]
        chapter_title = chapter["title"]
        print(f"\n处理章节 {chapter_id}: {chapter_title}")

        for slide in chapter["slides"]:
            current += 1
            slide_idx = slide["slide_index"]
            script_text = slide["script"]

            output_path = f"{AUDIO_DIR}/chapter_{chapter_id}_slide_{slide_idx:02d}.mp3"

            print(f"  [{current}/{total_slides}] 合成: {slide['title'][:20]}...")

            success = tts.synthesize(
                text=script_text,
                output_path=output_path,
                voice_type=VOICE_TYPES["zhixing"],  # 知性女声
                speed_ratio=1.0,
                volume_ratio=1.0
            )

            if not success:
                print(f"    ❌ 合成失败")
            else:
                print(f"    ✅ 已保存")

    print(f"\n✅ 语音合成完成")
    print(f"   保存位置: {AUDIO_DIR}")


def step4_create_videos():
    """步骤4: 合成视频"""
    print("\n" + "=" * 60)
    print("步骤4: 生成教学视频")
    print("=" * 60)

    Path(VIDEO_DIR).mkdir(parents=True, exist_ok=True)

    from scripts.generate_course_videos import generate_chapter_video

    for chapter in CHAPTERS_DATA:
        chapter_id = chapter["id"]
        chapter_title = chapter["title"]

        ppt_path = f"{SLIDES_DIR}/chapter_{chapter_id}_{chapter_title}.pptx"
        output_path = f"{VIDEO_DIR}/chapter_{chapter_id}_{chapter_title}.mp4"

        if not Path(ppt_path).exists():
            print(f"跳过章节 {chapter_id}: PPT不存在")
            continue

        success = generate_chapter_video(
            chapter_id=chapter_id,
            chapter_title=chapter_title,
            ppt_path=ppt_path,
            audio_dir=AUDIO_DIR,
            output_path=output_path
        )

        if success:
            print(f"✅ 章节 {chapter_id} 视频已生成")
        else:
            print(f"❌ 章节 {chapter_id} 视频生成失败")

    print(f"\n✅ 视频生成完成")
    print(f"   保存位置: {VIDEO_DIR}")


def main():
    """主函数"""
    print("=" * 60)
    print("《神经网络与深度学习》课程内容生成")
    print("=" * 60)

    # 步骤1: 生成PPT
    step1_generate_ppts()

    # 步骤2: 生成语音脚本
    scripts = step2_generate_voice_scripts()

    # 步骤3: 合成语音
    step3_synthesize_audio(scripts)

    # 步骤4: 生成视频
    step4_create_videos()

    print("\n" + "=" * 60)
    print("全部完成!")
    print("=" * 60)
    print(f"PPT: {SLIDES_DIR}")
    print(f"音频: {AUDIO_DIR}")
    print(f"视频: {VIDEO_DIR}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="课程内容生成")
    parser.add_argument("--step", type=int, help="执行指定步骤(1-4)")
    args = parser.parse_args()

    if args.step == 1:
        step1_generate_ppts()
    elif args.step == 2:
        step2_generate_voice_scripts()
    elif args.step == 3:
        scripts = step2_generate_voice_scripts()
        step3_synthesize_audio(scripts)
    elif args.step == 4:
        step4_create_videos()
    else:
        main()
