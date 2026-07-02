from __future__ import annotations

import logging
import uuid
import asyncio
import os
import ssl
from functools import lru_cache
from typing import Any, Dict, List, Optional

import aiohttp
import certifi

# 配置SSL证书路径（修复Docker容器中的SSL问题）
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

try:
    import agent_pilot as ap
    from agent_pilot import OptimizeState
    AGENT_PILOT_AVAILABLE = True
except ImportError:
    ap = None
    OptimizeState = None
    AGENT_PILOT_AVAILABLE = False

from app.core.config import settings

logger = logging.getLogger(__name__)

# PromptPilot Task IDs
PROMPTPILOT_TASKS = {
    "recommendation": "ta-20251202120239-Vedo3",  # 个性化推荐引擎
    "brainstorm": "ta-20251202120916-pt62j",      # 画布级协作套件
    "command_nlu": "ta-20251202121057-rKUFm",     # 全局命令面板
    "code_suggestion": "ta-20251202121212-8wXMB", # 主动式代码建议
    "code_explanation": "ta-20251202121145-x7YxP", # 按需代码解释
    "error_diagnosis": "ta-20251202121147-cGf5p", # 评测错误诊断
    "general_chat": "ta-20251202130446-8WmTn",    # 通用对话
}


class AgentPilotNotConfigured(Exception):
    """Raised when AgentPilot configuration is missing."""


class AgentPilotClient:
    """Wrapper for PromptPilot Agent SDK usage."""

    def __init__(self):
        if not AGENT_PILOT_AVAILABLE:
            raise AgentPilotNotConfigured("AgentPilot SDK 未安装")
        
        if not settings.agentpilot_enabled:
            raise AgentPilotNotConfigured("AgentPilot SDK 未配置，缺少 API Key 或 Workspace ID")

        self.api_key = settings.AGENTPILOT_API_KEY
        self.api_url = settings.AGENTPILOT_API_URL
        self.workspace_id = settings.AGENTPILOT_WORKSPACE_ID
        self.sample_rate = settings.AGENTPILOT_SAMPLE_RATE
        self.ark_api_key = settings.ARK_API_KEY

        self._configure_sdk()

    def _configure_sdk(self) -> None:
        """Set default configuration for agent_pilot SDK."""
        if not AGENT_PILOT_AVAILABLE:
            return
        # 设置基础配置
        ap.config.set_config(
            api_key=self.api_key,
            api_url=self.api_url,
        )
        logger.info("AgentPilot SDK 配置完成: api_url=%s, workspace_id=%s", self.api_url, self.workspace_id)

    @lru_cache
    def get_ark_client(self) -> Any:
        if not AGENT_PILOT_AVAILABLE:
            return None
        if not self.ark_api_key:
            raise AgentPilotNotConfigured("未配置 ARK_API_KEY，无法创建 Ark 客户端")
        try:
            # 尝试导入 volcengine ark 客户端
            from volcengine.ark import Ark
            client = Ark(api_key=self.ark_api_key)
            if ap:
                ap.probing(object=client, sample_rate=self.sample_rate)
            return client
        except ImportError:
            logger.warning("volcengine.ark 模块未找到，跳过 Ark 客户端创建")
            return None

    def create_task(
        self,
        name: str,
        prompt: Any,
        task_type: str = "DEFAULT",
        model_name: str = "doubao-seed-1.6-250615",
        criteria: Optional[str] = None,
        variable_types: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a new PromptPilot task and return the created version."""
        logger.info("Creating AgentPilot task: %s", name)
        kwargs: Dict[str, Any] = {
            "name": name,
            "task_type": task_type,
            "prompt": prompt,
            "model_name": model_name,
            "api_key": self.api_key,
            "api_url": self.api_url,
            "workspace_id": self.workspace_id,
        }
        if criteria:
            kwargs["criteria"] = criteria
        if variable_types:
            kwargs["variable_types"] = variable_types
        return ap.create_task(**kwargs)

    def get_prompt(self, task_id: str, version: str) -> Dict[str, Any]:
        return ap.get_prompt(
            task_id=task_id, 
            version=version,
            api_key=self.api_key,
            api_url=self.api_url,
            workspace_id=self.workspace_id
        )

    def list_prompts(self, task_id: str) -> List[Dict[str, Any]]:
        return ap.list_prompts(
            task_id=task_id,
            api_key=self.api_key,
            api_url=self.api_url,
            workspace_id=self.workspace_id
        )

    def render_input(self, task_id: str, version: str, variables: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
        """渲染PromptPilot模板，带重试机制"""
        logger.info(f"Rendering task {task_id} with variables: {list(variables.keys())}")
        last_error = None
        for attempt in range(max_retries):
            try:
                result = ap.render(
                    task_id=task_id,
                    version=version,
                    variables=variables,
                    api_key=self.api_key,
                    api_url=self.api_url,
                    workspace_id=self.workspace_id,
                )
                # 调试日志：显示渲染结果的前500字符
                if result and "messages" in result:
                    for msg in result["messages"]:
                        content = msg.get("content", [])
                        if isinstance(content, list) and content:
                            text = content[0].get("text", "") if isinstance(content[0], dict) else str(content[0])
                            logger.info(f"Rendered message preview: {text[:300]}...")
                return result
            except Exception as e:
                last_error = e
                logger.warning(f"PromptPilot render attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1 * (attempt + 1))  # 递增等待时间
        
        raise Exception(f"Error rendering template: {last_error}")

    def track_event(
        self,
        run_id: str,
        task_id: str,
        version: str,
        variables: Dict[str, Any],
        input_messages: List[Dict[str, Any]],
        output_message: Dict[str, Any],
        reference: Optional[str] = None,
    ) -> None:
        ap.track_event(
            run_type="llm",
            event_name="reference",
            run_id=run_id,
            task_id=task_id,
            version=version,
            variables=variables,
            input_messages=input_messages,
            output_message=output_message,
            reference=reference,
            api_key=self.api_key,
            api_url=self.api_url,
        )
        ap.flush()

    def track_feedback(
        self,
        task_id: str,
        version: str,
        run_id: str,
        feedback: Dict[str, Any],
    ) -> None:
        ap.track_feedback(
            task_id=task_id,
            version=version,
            run_id=run_id,
            feedback=feedback,
            api_key=self.api_key,
            api_url=self.api_url,
        )
        ap.flush()

    def evaluate_example(self, example: Dict[str, Any], metric: Dict[str, Any]) -> Any:
        return ap.eval.evaluate(
            example=example,
            metric=metric,
            api_key=self.api_key,
            api_url=self.api_url,
        )

    def generate_criteria(self, examples: List[Dict[str, Any]]) -> str:
        return ap.eval.generate_criteria(
            examples=examples,
            api_key=self.api_key,
            api_url=self.api_url,
        )

    def optimize_prompt(self, task_id: str, base_version: str) -> Dict[str, Any]:
        """Run prompt optimization and return report when finished."""
        job = ap.optimize.create(
            task_id=task_id,
            base_version=base_version,
            api_key=self.api_key,
            api_url=self.api_url,
        )
        info = job.get_job_info()
        while info.state not in {"SUCCESS", "FAILED"}:
            logger.debug("AgentPilot 优化进度: state=%s percent=%.2f", info.state, getattr(info.progress, "percent", 0))
            info = job.get_job_info()
        if info.state == "SUCCESS":
            report = job.get_report()
            return {
                "state": "success",
                "optimized_version": report.opt.optimized_version,
                "opt_prompt": report.opt.prompt,
                "base_prompt": report.base.prompt,
                "opt_metric": report.opt.metric,
                "base_metric": report.base.metric,
                "opt_avg_score": report.opt.avg_score,
                "base_avg_score": report.base.avg_score,
            }
        return {"state": "failed", "error": getattr(info, "error_message", "优化失败")}

    async def call_task(
        self,
        task_id: str,
        variables: Dict[str, Any],
        version: str = "v1",
        model_name: str = "doubao-seed-1.6-250615",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """
        Unified method to call a PromptPilot task with variables.
        
        Args:
            task_id: PromptPilot task ID (e.g., ta-20251202120239-Vedo3)
            variables: Dictionary of variables to render the prompt template
            version: Prompt version (default: v1)
            model_name: LLM model to use
            temperature: Generation temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict containing:
                - content: The LLM response text
                - run_id: Unique ID for this run (for tracking)
                - prompt_tokens: Input tokens used
                - completion_tokens: Output tokens generated
                - success: Boolean indicating success
        """
        run_id = str(uuid.uuid4())
        
        try:
            # Step 1: Render the prompt template with variables
            render_result = self.render_input(task_id, version, variables)
            
            if not render_result or "messages" not in render_result:
                raise ValueError(f"Failed to render prompt for task {task_id}")
            
            # Extract rendered messages
            messages = render_result.get("messages", [])
            if not messages:
                raise ValueError(f"No messages returned from render for task {task_id}")
            
            # Step 2: Call LLM with rendered prompt
            # Use direct HTTP call to Volcengine Ark API
            ark_endpoint = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
            
            headers = {
                "Authorization": f"Bearer {self.ark_api_key}",
                "Content-Type": "application/json"
            }
            
            # Build request messages from rendered result
            request_messages = []
            for msg in messages:
                role = msg.get("role", "user")
                content_parts = msg.get("content", [])
                if isinstance(content_parts, list):
                    # Extract text from content parts
                    text_content = ""
                    for part in content_parts:
                        if isinstance(part, dict) and "text" in part:
                            text_content += part["text"]
                        elif isinstance(part, str):
                            text_content += part
                    content = text_content
                else:
                    content = str(content_parts)
                request_messages.append({"role": role, "content": content})
            
            request_data = {
                "model": model_name,
                "messages": request_messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            # 创建SSL上下文，使用certifi证书
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.post(
                    ark_endpoint,
                    json=request_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ark API error: {response.status} - {error_text}")
                        raise Exception(f"Ark API error: {response.status}")
                    
                    result = await response.json()
            
            # Extract response
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            
            # Step 3: Track event for logging (async, non-blocking)
            try:
                output_message = {"role": "assistant", "content": content}
                self.track_event(
                    run_id=run_id,
                    task_id=task_id,
                    version=version,
                    variables=variables,
                    input_messages=request_messages,
                    output_message=output_message,
                )
            except Exception as track_error:
                logger.warning(f"Failed to track event: {track_error}")
            
            return {
                "content": content,
                "run_id": run_id,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error calling task {task_id}: {e}")
            return {
                "content": "",
                "run_id": run_id,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "success": False,
                "error": str(e)
            }

    def get_task_id(self, feature_name: str) -> str:
        """Get the task ID for a named feature."""
        task_id = PROMPTPILOT_TASKS.get(feature_name)
        if not task_id:
            raise ValueError(f"Unknown feature: {feature_name}. Available: {list(PROMPTPILOT_TASKS.keys())}")
        return task_id
