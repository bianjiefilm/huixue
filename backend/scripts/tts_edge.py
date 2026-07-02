#!/usr/bin/env python3
"""
Edge TTS 语音合成工具 (免费替代方案)
使用微软Edge浏览器的TTS服务
"""
import asyncio
import edge_tts
from pathlib import Path


# 可用的中文发音人
EDGE_VOICES = {
    # 女声
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",      # 晓晓 - 活泼女声
    "xiaoyi": "zh-CN-XiaoyiNeural",          # 晓依 - 温柔女声
    "yunxi": "zh-CN-YunxiNeural",            # 云溪 - 知性女声
    # 男声
    "yunjian": "zh-CN-YunjianNeural",        # 云健 - 成熟男声
    "yunyang": "zh-CN-YunyangNeural",        # 云扬 - 新闻男声
    # 默认
    "default": "zh-CN-XiaoxiaoNeural"
}


async def synthesize_async(text: str, output_path: str, voice: str = "default") -> bool:
    """
    异步合成语音

    Args:
        text: 要合成的文本
        output_path: 输出文件路径
        voice: 发音人名称

    Returns:
        是否成功
    """
    try:
        voice_id = EDGE_VOICES.get(voice, EDGE_VOICES["default"])
        communicate = edge_tts.Communicate(text, voice_id)

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        await communicate.save(output_path)

        return True
    except Exception as e:
        print(f"合成失败: {e}")
        return False


def synthesize(text: str, output_path: str, voice: str = "default") -> bool:
    """
    同步合成语音

    Args:
        text: 要合成的文本
        output_path: 输出文件路径
        voice: 发音人名称

    Returns:
        是否成功
    """
    return asyncio.run(synthesize_async(text, output_path, voice))


def synthesize_batch(items: list, output_dir: str, voice: str = "default") -> list:
    """
    批量合成语音

    Args:
        items: 列表，每项包含 {"id": "xxx", "text": "xxx"}
        output_dir: 输出目录
        voice: 发音人名称

    Returns:
        成功的文件路径列表
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    results = []

    async def batch_synthesize():
        for item in items:
            item_id = item.get("id", "unknown")
            text = item.get("text", "")
            output_path = Path(output_dir) / f"{item_id}.mp3"

            print(f"  合成: {item_id}...")
            if await synthesize_async(text, str(output_path), voice):
                results.append(str(output_path))
                print(f"    ✅ 完成")
            else:
                print(f"    ❌ 失败")

    asyncio.run(batch_synthesize())
    return results


if __name__ == "__main__":
    # 测试
    test_text = "欢迎学习神经网络与深度学习课程。本课程将带你从零开始，掌握人工智能的核心技术。"
    output = "/tmp/test_edge_tts.mp3"

    print("测试Edge TTS...")
    if synthesize(test_text, output):
        print(f"✅ 成功: {output}")
    else:
        print("❌ 失败")
