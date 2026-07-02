#!/usr/bin/env python3
"""
火山引擎语音合成工具
基于 https://www.volcengine.com/docs/6561/79820
"""
import os
import json
import uuid
import base64
import requests
from pathlib import Path


class VolcengineTTS:
    """火山引擎语音合成客户端"""

    def __init__(self, app_id: str, access_token: str, cluster: str = "volcano_tts"):
        self.app_id = app_id
        self.access_token = access_token
        self.cluster = cluster
        self.api_url = "https://openspeech.bytedance.com/api/v1/tts"

    def synthesize(
        self,
        text: str,
        output_path: str,
        voice_type: str = "zh_female_shuangkuaisisi_mars_bigtts",
        speed_ratio: float = 1.0,
        volume_ratio: float = 1.0,
        pitch_ratio: float = 1.0,
        encoding: str = "mp3",
        sample_rate: int = 24000
    ) -> bool:
        """
        合成语音

        Args:
            text: 要合成的文本
            output_path: 输出音频文件路径
            voice_type: 发音人类型
            speed_ratio: 语速 (0.5-2.0)
            volume_ratio: 音量 (0.5-2.0)
            pitch_ratio: 音调 (0.5-2.0)
            encoding: 音频格式 (mp3, wav, ogg, pcm)
            sample_rate: 采样率

        Returns:
            是否成功
        """
        # 生成唯一请求ID
        req_id = str(uuid.uuid4())

        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer;{self.access_token}"
        }

        # 构建请求体
        payload = {
            "app": {
                "appid": self.app_id,
                "token": "access_token",
                "cluster": self.cluster
            },
            "user": {
                "uid": "huixue_user"
            },
            "audio": {
                "voice_type": voice_type,
                "encoding": encoding,
                "speed_ratio": speed_ratio,
                "volume_ratio": volume_ratio,
                "pitch_ratio": pitch_ratio,
                "sample_rate": sample_rate
            },
            "request": {
                "reqid": req_id,
                "text": text,
                "text_type": "plain",
                "operation": "query",
                "with_frontend": 1,
                "frontend_type": "unitTson"
            }
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )

            if response.status_code != 200:
                print(f"HTTP错误: {response.status_code}")
                print(response.text)
                return False

            result = response.json()

            if result.get("code") != 3000:
                print(f"API错误: {result.get('code')} - {result.get('message')}")
                return False

            # 解码音频数据
            audio_data = result.get("data", "")
            if not audio_data:
                print("未返回音频数据")
                return False

            audio_bytes = base64.b64decode(audio_data)

            # 保存文件
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_bytes(audio_bytes)

            print(f"语音已保存: {output_path}")
            return True

        except Exception as e:
            print(f"合成失败: {e}")
            return False

    def synthesize_long_text(
        self,
        text: str,
        output_path: str,
        max_chars: int = 500,
        **kwargs
    ) -> bool:
        """
        合成长文本（自动分段）

        Args:
            text: 长文本
            output_path: 输出路径
            max_chars: 每段最大字符数
            **kwargs: 传递给synthesize的其他参数

        Returns:
            是否成功
        """
        # 分段
        segments = self._split_text(text, max_chars)

        if len(segments) == 1:
            return self.synthesize(text, output_path, **kwargs)

        # 合成各段
        temp_files = []
        output_dir = Path(output_path).parent
        base_name = Path(output_path).stem

        for i, segment in enumerate(segments):
            temp_path = output_dir / f"{base_name}_part{i:03d}.mp3"
            if not self.synthesize(segment, str(temp_path), **kwargs):
                # 清理临时文件
                for f in temp_files:
                    Path(f).unlink(missing_ok=True)
                return False
            temp_files.append(str(temp_path))

        # 合并音频（需要ffmpeg）
        if len(temp_files) > 1:
            list_file = output_dir / f"{base_name}_list.txt"
            with open(list_file, 'w') as f:
                for tf in temp_files:
                    f.write(f"file '{tf}'\n")

            import subprocess
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(list_file), "-c", "copy", output_path
            ]
            result = subprocess.run(cmd, capture_output=True)

            # 清理
            list_file.unlink(missing_ok=True)
            for f in temp_files:
                Path(f).unlink(missing_ok=True)

            return result.returncode == 0

        return True

    def _split_text(self, text: str, max_chars: int) -> list:
        """按句子分割长文本"""
        if len(text) <= max_chars:
            return [text]

        # 按句子分割
        import re
        sentences = re.split(r'([。！？；\n])', text)

        segments = []
        current = ""

        for i in range(0, len(sentences), 2):
            sentence = sentences[i]
            punct = sentences[i + 1] if i + 1 < len(sentences) else ""
            full_sentence = sentence + punct

            if len(current) + len(full_sentence) <= max_chars:
                current += full_sentence
            else:
                if current:
                    segments.append(current)
                current = full_sentence

        if current:
            segments.append(current)

        return segments


# 可用的发音人列表
VOICE_TYPES = {
    # 中文女声 (Mars大模型音色)
    "shuangkuai": "zh_female_shuangkuaisisi_mars_bigtts",  # 爽快思思
    "tianmei": "zh_female_tianmeixiaoyuan_mars_bigtts",    # 甜美小源
    "zhixing": "zh_female_zhixingnvsheng_mars_bigtts",     # 知性女声
    # 中文男声 (Mars大模型音色)
    "yangguang": "zh_male_yangguangqingnian_mars_bigtts",  # 阳光青年
    "chengshu": "zh_male_chengshunanshen_mars_bigtts",     # 成熟男声
    # 通用
    "default": "zh_female_shuangkuaisisi_mars_bigtts"
}


def create_tts_client():
    """创建TTS客户端（使用预配置的凭证）"""
    return VolcengineTTS(
        app_id="6026849500",
        access_token="6-HbFN7u0y_OHlwj0rCckrcjJ4iy3dtn"
    )


if __name__ == "__main__":
    # 测试
    client = create_tts_client()
    test_text = "欢迎学习神经网络与深度学习课程。本课程将带你从零开始，掌握人工智能的核心技术。"
    client.synthesize(test_text, "/tmp/test_tts.mp3")
