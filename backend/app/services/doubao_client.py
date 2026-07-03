"""
豆包AI客户端
集成火山方舟豆包模型API
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List
import aiohttp
from app.core.cache import get_cache

logger = logging.getLogger(__name__)


class DoubaoClient:
    """豆包AI客户端"""

    def __init__(self):
        # 密钥只从环境变量读取；本模块顶层有全局实例,缺失时推迟到调用时报错
        self.api_key = os.getenv("ARK_API_KEY", "")
        # base_url/model 可通过环境变量覆盖，用于适配不同套餐(如 Agent Plan 走 /api/plan/v3
        # 且模型名为 doubao-seed-2.0-* 系列，与标准按量付费 /api/v3 + doubao-seed-1-6-* 不同)
        self.base_url = os.getenv("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        self.model = os.getenv("ARK_MODEL", "doubao-seed-1-6-flash-250828")
        self.cache = get_cache()

    def _generate_query_hash(self, messages: List[Dict], **kwargs) -> str:
        """生成查询的哈希值用于缓存"""
        # 将消息和参数序列化后哈希
        query_data = {
            "messages": messages,
            "model": self.model,
            **kwargs
        }
        query_str = json.dumps(query_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(query_str.encode()).hexdigest()

    async def chat_completion(self, messages: List[Dict],
                            max_tokens: int = 2000,
                            temperature: float = 0.7,
                            use_cache: bool = True,
                            timeout_seconds: int = 90) -> Dict[str, Any]:
        """
        调用豆包聊天完成API

        Args:
            messages: 消息列表
            max_tokens: 最大token数
            temperature: 温度参数
            use_cache: 是否使用缓存
            timeout_seconds: 请求超时秒数。真实压测发现(慧学AI升级Phase1 E2E UAT):
                思考型模型(如 doubao-seed-2.0-lite)在 reasoning_content 上会消耗
                大量时间,2个知识点的关卡生成实测约27秒,7个知识点必现超时。
                旧默认30秒对 max_tokens 较大的调用(如关卡生成用8000)完全不够,
                调用方按预期输出量级传入更长的值,不要依赖这里的默认值兜底。

        Returns:
            API响应结果
        """
        if not self.api_key:
            raise RuntimeError("AI 服务未配置: 缺少 ARK_API_KEY 环境变量")

        try:
            # 生成查询哈希用于缓存
            query_hash = self._generate_query_hash(messages, max_tokens=max_tokens, temperature=temperature)

            # 检查缓存
            if use_cache:
                cached_response = self.cache.get_ai_response(query_hash)
                if cached_response:
                    logger.info(f"使用缓存响应: {query_hash[:8]}...")
                    try:
                        return json.loads(cached_response)
                    except json.JSONDecodeError:
                        pass  # 缓存数据损坏，继续调用API

            # 准备请求数据
            request_data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            logger.info(f"调用豆包API: {query_hash[:8]}...")

            # 调用API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=request_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout_seconds)
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"豆包API调用失败: {response.status} - {error_text}")
                        raise Exception(f"API调用失败: {response.status}")

                    result = await response.json()

                    # 缓存成功响应
                    if use_cache and "choices" in result:
                        try:
                            self.cache.set_ai_response(query_hash, json.dumps(result, ensure_ascii=False))
                        except Exception as cache_error:
                            logger.warning(f"缓存AI响应失败: {cache_error}")

                    return result

        except Exception as e:
            # str(asyncio.TimeoutError()) 是空字符串,不带类型名会把超时异常打印成
            # "豆包API调用异常: "(冒号后空白),掩盖真实原因(真实压测中发现过这个坑)。
            logger.error(f"豆包API调用异常: {type(e).__name__}: {e}")
            raise

    async def simple_chat(self, user_message: str,
                         system_prompt: Optional[str] = None,
                         temperature: float = 0.7,
                         max_tokens: int = 1024,
                         use_cache: bool = True) -> str:
        """
        简化的聊天接口

        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数
            use_cache: 是否使用缓存

        Returns:
            AI回复内容
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        # 记录缓存查询信息
        query_hash = self._generate_query_hash(messages, temperature=temperature, max_tokens=max_tokens)
        logger.info(f"AI查询哈希: {query_hash[:8]}..., 使用缓存: {use_cache}")

        response = await self.chat_completion(messages, temperature=temperature, max_tokens=max_tokens, use_cache=use_cache)

        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]

        raise Exception("API响应格式错误")

    async def analyze_image(self, image_url: str, prompt: str) -> str:
        """
        分析图片内容

        Args:
            image_url: 图片URL
            prompt: 分析提示词

        Returns:
            分析结果
        """
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        response = await self.chat_completion(messages, use_cache=False)  # 图片分析不缓存

        if "choices" in response and len(response["choices"]) > 0:
            return response["choices"][0]["message"]["content"]

        raise Exception("图片分析响应格式错误")


# 全局豆包客户端实例
doubao_client = DoubaoClient()

def get_doubao_client() -> DoubaoClient:
    """获取豆包客户端实例"""
    return doubao_client
