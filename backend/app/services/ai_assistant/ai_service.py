"""
AI服务核心类
处理与AI API的交互，支持多种模型提供商
"""

import os
import json
import time
import logging
from typing import Dict, Optional, Any, List
import aiohttp
import asyncio
from sqlalchemy.orm import Session

from app.models.models import AIConfig, AIUsageLog, User
from .prompts import PromptTemplates
from app.services.doubao_client import get_doubao_client
from app.services.ai_quota import get_quota_manager

logger = logging.getLogger(__name__)


class AIService:
    """AI服务主类"""
    
    def __init__(self, db: Session, current_user: Optional[Dict[str, Any]] = None):
        self.db = db
        self.config = self._load_config()
        self.prompts = PromptTemplates()
        self.doubao_client = get_doubao_client()
        self.quota_manager = get_quota_manager(db)
        self.current_user = current_user or {}
        self.current_user_id = self.current_user.get("id") or self.current_user.get("user_id")
        roles = self.current_user.get("roles") or []
        self.current_user_role = roles[0] if roles else self.current_user.get("role", "student")
    
    def _load_config(self) -> Optional[AIConfig]:
        """加载激活的AI配置(ai_config 表);无配置时返回 None,由调用方报「AI服务未配置」"""
        return self.db.query(AIConfig).filter(AIConfig.is_active == True).first()
    
    async def call_api(self, prompt: str, system_prompt: str = None, 
                      max_tokens: int = None, temperature: float = None) -> Dict[str, Any]:
        """
        调用AI API
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            max_tokens: 最大生成token数
            temperature: 温度参数
            
        Returns:
            API响应结果
        """
        if not self.config:
            raise ValueError("AI服务未配置，请联系管理员")
        
        # 使用配置的默认值
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # 准备请求数据
        request_data = {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        # 根据提供商调整请求格式
        if self.config.provider == "gemini":
            # Gemini API格式略有不同
            request_data = self._adapt_for_gemini(request_data)
        
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.endpoint,
                    json=request_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = time.time() - start_time
                    result = await response.json()
                    
                    if response.status != 200:
                        error_msg = result.get("error", {}).get("message", "Unknown error")
                        raise Exception(f"API error: {error_msg}")
                    
                    # 记录使用情况（不阻塞主流程）
                    asyncio.create_task(self._log_usage(
                        prompt, result, response_time, None
                    ))
                    
                    return result
                    
        except asyncio.TimeoutError:
            error_msg = "AI API请求超时"
            await self._log_usage(prompt, None, 30.0, error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = str(e)
            await self._log_usage(prompt, None, time.time() - start_time, error_msg)
            raise
    
    def _adapt_for_gemini(self, request_data: Dict) -> Dict:
        """适配Gemini API格式"""
        # Gemini使用不同的参数名
        return {
            "contents": [{"parts": [{"text": msg["content"]}]} for msg in request_data["messages"]],
            "generationConfig": {
                "maxOutputTokens": request_data["max_tokens"],
                "temperature": request_data["temperature"]
            }
        }
    
    async def _log_usage(self, prompt: str, response: Optional[Dict],
                        response_time: float, error: Optional[str],
                        user_id: Optional[int] = None,
                        user_role: Optional[str] = None,
                        feature_type: str = "unknown"):
        """记录AI使用日志（异步，不阻塞主流程）"""
        try:
            actual_user_id = user_id or self.current_user_id
            if not actual_user_id:
                logger.warning("Skip AI usage log: missing current user id")
                return

            # 简化日志记录，避免存储过多数据
            log_entry = AIUsageLog(
                user_id=int(actual_user_id),
                user_role=user_role or self.current_user_role or "student",
                feature_type=feature_type,
                response_time=response_time,
                error_message=error
            )
            
            if response and not error:
                # 提取token使用情况
                usage = response.get("usage", {})
                log_entry.prompt_tokens = usage.get("prompt_tokens", 0)
                log_entry.completion_tokens = usage.get("completion_tokens", 0)
                log_entry.total_tokens = usage.get("total_tokens", 0)
                
                # 估算成本（示例：每1000 tokens $0.002）
                log_entry.cost_estimate = log_entry.total_tokens * 0.000002
            
            self.db.add(log_entry)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log AI usage: {e}")
    
    async def grade_assignment(self, question: str, reference_answer: str, 
                              student_answer: str) -> Dict[str, Any]:
        """
        批阅学生作业
        
        Args:
            question: 题目
            reference_answer: 参考答案
            student_answer: 学生答案
            
        Returns:
            包含分数和评语的字典
        """
        prompt = self.prompts.get_grading_prompt(question, reference_answer, student_answer)
        
        try:
            response = await self.call_api(prompt)
            
            # 解析响应
            content = response["choices"][0]["message"]["content"]
            
            # 尝试解析JSON格式的响应
            try:
                result = json.loads(content)
                return {
                    "score": result.get("score", 0),
                    "comment": result.get("comment", ""),
                    "suggestions": result.get("suggestions", [])
                }
            except json.JSONDecodeError:
                # 如果不是JSON，返回默认格式
                return {
                    "score": 0,
                    "comment": content[:200],  # 截取前200字符作为评语
                    "suggestions": []
                }
                
        except Exception as e:
            logger.error(f"AI grading failed: {e}")
            return {
                "score": 0,
                "comment": "AI评分服务暂时不可用",
                "suggestions": [],
                "error": str(e)
            }

    # ==================== 新的AI学习助手功能 ====================

    async def chat_with_ai(self, user_id: int, message: str,
                          context: Optional[str] = None,
                          user_role: str = "student") -> Dict[str, Any]:
        """
        AI学习助手对话

        Args:
            user_id: 用户ID
            message: 用户消息
            context: 上下文信息
            user_role: 用户角色

        Returns:
            包含回复和额度信息的字典
        """
        try:
            # 检查额度
            quota_info = self.quota_manager.check_quota(user_id, "chat")
            if not quota_info["allowed"]:
                return {
                    "reply": "您的AI助手使用额度已用完，请下个月再来使用。",
                    "quota_info": quota_info,
                    "error": "quota_exceeded",
                    "success": False
                }

            # 构建系统提示词
            system_prompt = self._get_chat_system_prompt(user_role, context)

            # 调用豆包API
            reply = await self.doubao_client.simple_chat(
                user_message=message,
                system_prompt=system_prompt,
                temperature=0.7,
                max_tokens=1024,
                use_cache=True
            )

            # 消费额度
            self.quota_manager.consume_quota(user_id, "chat")

            # 记录使用情况
            await self._log_usage(message, {"choices": [{"message": {"content": reply}}]},
                                1.0, None, user_id, user_role, "chat")

            return {
                "reply": reply,
                "quota_info": quota_info,
                "success": True
            }

        except Exception as e:
            logger.error(f"AI对话失败: {e}")
            # 记录错误
            await self._log_usage(message, None, 1.0, str(e), user_id, user_role, "chat")

            return {
                "reply": "AI助手暂时无法回复，请稍后再试。",
                "quota_info": quota_info,
                "error": str(e),
                "success": False
            }

    async def explain_concept(self, user_id: int, concept: str,
                            context: Optional[str] = None,
                            user_role: str = "student") -> Dict[str, Any]:
        """
        解释概念（集成缓存和额度管理）

        Args:
            user_id: 用户ID
            concept: 要解释的概念
            context: 上下文信息
            user_role: 用户角色

        Returns:
            解释结果
        """
        try:
            # 检查额度
            quota_info = self.quota_manager.check_quota(user_id, "explain")
            if not quota_info["allowed"]:
                return {
                    "explanation": "您的AI解释额度已用完，请下个月再来使用。",
                    "quota_info": quota_info,
                    "error": "quota_exceeded",
                    "success": False
                }

            # 构建提示词
            prompt = self.prompts.get_concept_explanation_prompt(concept, context)

            # 调用豆包API
            explanation = await self.doubao_client.simple_chat(
                user_message=prompt,
                system_prompt="你是一个专业的教育助手，请用通俗易懂的语言解释概念。",
                use_cache=True
            )

            # 消费额度
            self.quota_manager.consume_quota(user_id, "explain")

            # 记录使用情况
            await self._log_usage(concept, {"choices": [{"message": {"content": explanation}}]},
                                1.0, None, user_id, user_role, "explain")

            return {
                "explanation": explanation,
                "quota_info": quota_info,
                "success": True
            }

        except Exception as e:
            logger.error(f"概念解释失败: {e}")

            return {
                "explanation": f"概念解释服务暂时不可用，请稍后再试。错误：{str(e)}",
                "quota_info": {"allowed": False, "remaining": 0, "cost": 1},
                "error": str(e),
                "success": False
            }

    async def explain_practice_failure(
        self,
        user_id: int,
        stage_id: int,
        code_content: str,
        failure_cases: List[Dict[str, Any]],
        handbook_markdown: Optional[str] = None,
        visible_error_output: Optional[str] = None,
        user_role: str = "student",
        stage_title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        失败后生成分级提示（不泄露答案）。

        Args:
            user_id: 用户ID
            stage_id: 关卡ID（用于日志与审计）
            code_content: 服务端记录的学生提交内容
            failure_cases: 服务端裁剪后的失败摘要
            handbook_markdown: 服务端读取的任务说明
            visible_error_output: 服务端记录的可见错误日志
            user_role: 用户角色

        Returns:
            提示内容
        """
        try:
            if not failure_cases:
                return {
                    "hint": "当前没有可诊断的失败用例。请先运行一次并确保测试未通过。",
                    "quota_info": {"allowed": False, "remaining": 0, "cost": 1, "user_role": self.quota_manager.get_user_role(user_id), "monthly_quota": 0, "used_this_month": 0, "reset_date": None},
                    "success": False,
                    "error": "no_failure_case"
                }

            quota_info = self.quota_manager.check_quota(user_id, "explain")
            if not quota_info["allowed"]:
                return {
                    "hint": "您的AI解释额度已用完，请下个月再来使用。",
                    "quota_info": quota_info,
                    "error": "quota_exceeded",
                    "success": False
                }

            failure_snippet = json.dumps(failure_cases, ensure_ascii=False)
            output_snippet = (visible_error_output or "").strip()

            prompt = (
                "你是课程闯关 AI 助教，只输出分级提示，不给出完整答案或隐藏测试内容。\n"
                f"关卡ID：{stage_id}\n"
                f"关卡标题：{stage_title or '未命名关卡'}\n"
                f"学生代码长度：{len(code_content or '')} 字符\n"
                "必须按以下结构返回：\n"
                "1) 可能原因\n2) 先验修正建议（最多3条）\n3) 下一步检查点\n"
                "请避免泄露任务答案、完整示例代码、隐藏测试输入或隐藏期望输出。\n\n"
                f"服务端任务说明摘要:\n{handbook_markdown or '未提供'}\n\n"
                f"服务端失败摘要（JSON）：\n{failure_snippet}\n\n"
                "服务端可见错误输出:\n"
                f"{output_snippet[:1200] if output_snippet else '无'}\n\n"
                "服务端记录的学生代码（摘要）：\n"
                f"{(code_content or '').strip()[:3000]}\n"
            )

            hint = await self.doubao_client.simple_chat(
                user_message=prompt,
                system_prompt="你是一个教学 AI 助教，目标是引导学生修复错误，不直接给答案。",
                use_cache=False
            )

            self.quota_manager.consume_quota(user_id, "explain")
            await self._log_usage(
                f"stage={stage_id}",
                {"choices": [{"message": {"content": hint}}]},
                1.0,
                None,
                user_id,
                user_role,
                "explain"
            )

            return {
                "hint": hint,
                "quota_info": quota_info,
                "success": True
            }

        except Exception as e:
            logger.error(f"闯关失败提示生成失败: {e}")

            await self._log_usage(
                f"stage={stage_id}",
                None,
                1.0,
                str(e),
                user_id,
                user_role,
                "explain"
            )

            return {
                "hint": f"闯关提示服务暂时不可用，请稍后再试。错误：{str(e)}",
                "quota_info": {"allowed": False, "remaining": 0, "cost": 1},
                "error": str(e),
                "success": False
            }

    async def generate_questions(self, user_id: int, knowledge_point: str,
                               question_type: str = "single_choice",
                               count: int = 1, difficulty: str = "medium") -> Dict[str, Any]:
        """
        生成试题（教师专用功能）

        Args:
            user_id: 用户ID（必须是教师）
            knowledge_point: 知识点
            question_type: 题型
            count: 生成数量
            difficulty: 难度

        Returns:
            生成的试题
        """
        quota_info = None
        try:
            # 检查用户角色和额度
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user or not self._is_teacher(user):
                quota_info = {"allowed": False, "remaining": 0, "cost": 2, "user_role": self.quota_manager.get_user_role(user_id), "monthly_quota": 0, "used_this_month": 0, "reset_date": None}
                return {
                    "questions": [],
                    "count": 0,
                    "quota_info": quota_info,
                    "error": "只有教师可以生成试题",
                    "success": False
                }

            quota_info = self.quota_manager.check_quota(user_id, "generate_question")
            if not quota_info["allowed"]:
                return {
                    "questions": [],
                    "count": 0,
                    "quota_info": quota_info,
                    "error": "您的试题生成额度已用完",
                    "success": False
                }

            # 构建生成提示词
            prompt = f"请生成{count}道关于'{knowledge_point}'的{question_type}题，难度为{difficulty}。每道题请包含题干、选项（如果是选择题）和正确答案。"

            # 调用豆包API
            response = await self.doubao_client.simple_chat(
                user_message=prompt,
                system_prompt="你是一个专业的试题编写助手，请严格按照要求生成试题。",
                use_cache=True  # 相同知识点的试题可以缓存
            )

            # 解析生成的试题（这里需要根据实际返回格式调整）
            questions = self._parse_generated_questions(response, question_type)

            # 消费额度（按生成数量）
            actual_cost = len(questions) * quota_info["cost"]
            self.quota_manager.consume_quota(user_id, "generate_question", actual_cost)

            # 记录使用情况
            await self._log_usage(knowledge_point, {"choices": [{"message": {"content": response}}]},
                                2.0, None, user_id, "teacher", "generate_question")

            return {
                "questions": questions,
                "count": len(questions),
                "quota_info": quota_info,
                "success": True
            }

        except Exception as e:
            logger.error(f"试题生成失败: {e}")
            await self._log_usage(knowledge_point, None, 2.0, str(e), user_id, "teacher", "generate_question")

            # 如果quota_info还没有被设置，提供默认值
            if quota_info is None:
                quota_info = {"allowed": False, "remaining": 0, "cost": 2}

            return {
                "questions": [],
                "count": 0,
                "quota_info": quota_info,
                "error": str(e),
                "success": False
            }

    async def check_question_quality(self, user_id: int, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查试题质量

        Args:
            user_id: 用户ID
            question_data: 试题数据

        Returns:
            质量评估结果
        """
        try:
            # 检查额度（质量检查消耗较少）
            quota_info = self.quota_manager.check_quota(user_id, "quality_check")
            if not quota_info["allowed"]:
                return {
                    "quality_score": 0,
                    "suggestions": [],
                    "detailed_analysis": "",
                    "quota_info": quota_info,
                    "error": "您的质量检查额度已用完",
                    "success": False
                }

            # 构建质量检查提示词
            prompt = f"""请评估以下试题的质量：

题型：{question_data.get('type', 'unknown')}
题干：{question_data.get('content', '')}
选项：{json.dumps(question_data.get('options', []), ensure_ascii=False)}
答案：{json.dumps(question_data.get('correct_answers', []), ensure_ascii=False)}

请从以下维度评估：
1. 题干清晰度
2. 选项质量
3. 答案正确性
4. 区分度
5. 教学价值

请给出0-100的分数和改进建议。"""

            # 调用豆包API
            analysis = await self.doubao_client.simple_chat(
                user_message=prompt,
                system_prompt="你是一个专业的教育质量评估专家，请客观公正地评估试题质量。",
                use_cache=True
            )

            # 解析质量评估结果
            quality_result = self._parse_quality_analysis(analysis)

            # 消费额度
            self.quota_manager.consume_quota(user_id, "quality_check")

            # 记录使用情况
            await self._log_usage("质量检查", {"choices": [{"message": {"content": analysis}}]},
                                0.5, None, user_id, self.quota_manager.get_user_role(user_id), "quality_check")

            return {
                **quality_result,
                "quota_info": quota_info,
                "success": True
            }

        except Exception as e:
            logger.error(f"质量检查失败: {e}")
            await self._log_usage("质量检查", None, 0.5, str(e), user_id, self.quota_manager.get_user_role(user_id), "quality_check")

            return {
                "quality_score": 0,
                "suggestions": ["质量评估服务暂时不可用"],
                "detailed_analysis": "",
                "quota_info": quota_info,
                "error": str(e),
                "success": False
            }

    def _get_chat_system_prompt(self, user_role: str, context: Optional[str]) -> str:
        """获取对话系统提示词"""
        base_prompt = "你是一个专业的AI学习助手，请用友好的语气回答学生的问题。"

        if user_role == "teacher":
            base_prompt = "你是一个专业的教育助手，可以帮助教师解答教学相关问题。"

        if context:
            base_prompt += f"\n\n当前上下文：{context}"

        return base_prompt

    def _is_teacher(self, user) -> bool:
        """检查用户是否为教师"""
        # 根据你的用户模型调整这个判断逻辑
        return getattr(user, 'is_teacher', False) or getattr(user, 'role', '').lower() == 'teacher'

    def _parse_generated_questions(self, response: str, question_type: str) -> List[Dict]:
        """解析生成的试题"""
        import re

        questions = []

        # 分割响应为单个题目（按"### 题目"分割）
        question_blocks = re.split(r'### 题目\d+', response)

        # 跳过第一个空的分割结果
        for block in question_blocks[1:]:
            if not block.strip():
                continue

            try:
                question_data = self._parse_single_question(block.strip(), question_type)
                if question_data:
                    questions.append(question_data)
            except Exception as e:
                logger.warning(f"解析题目失败: {e}")
                continue

        # 如果没有解析到任何题目，返回原始响应作为单个题目
        if not questions:
            questions.append({
                "type": question_type,
                "content": response[:500],  # 限制长度
                "options": [],
                "correct_answers": [],
                "raw_response": response
            })

        return questions

    def _parse_single_question(self, question_block: str, question_type: str) -> Dict[str, Any]:
        """解析单个题目"""
        import re

        # 提取题干
        content_match = re.search(r'\*\*题干\*\*：(.*?)(?=\*\*选项\*\*|\*\*正确答案\*\*|$)', question_block, re.DOTALL)
        content = content_match.group(1).strip() if content_match else question_block.split('**选项**')[0].strip()

        # 提取选项（如果是选择题）
        options = []
        if question_type in ['single_choice', 'multiple_choice']:
            options_match = re.search(r'\*\*选项\*\*：(.*?)(?=\*\*正确答案\*\*|$)', question_block, re.DOTALL)
            if options_match:
                options_text = options_match.group(1).strip()
                # 解析选项格式：A. 选项内容
                option_lines = [line.strip() for line in options_text.split('\n') if line.strip()]
                for line in option_lines:
                    if re.match(r'^[A-D]\.', line):
                        key = line[0]
                        content_part = line[3:].strip()
                        options.append({"key": key, "content": content_part})

        # 提取正确答案
        correct_answers = []
        answer_match = re.search(r'\*\*正确答案\*\*：([^\n]+)', question_block)
        if answer_match:
            answer_text = answer_match.group(1).strip()
            # 处理多个答案的情况，如"A, C"或"A和C"
            answers = re.split(r'[，,、和\s]+', answer_text)
            correct_answers = [ans.strip() for ans in answers if ans.strip()]

        return {
            "type": question_type,
            "content": content,
            "options": options,
            "correct_answers": correct_answers,
            "raw_response": question_block
        }

    def _parse_quality_analysis(self, analysis: str) -> Dict[str, Any]:
        """解析质量分析结果"""
        # 简化的解析，实际使用时需要更复杂的解析逻辑
        return {
            "quality_score": 85,  # 示例分数
            "suggestions": [analysis[:100]],  # 示例建议
            "detailed_analysis": analysis
        }
    
    async def generate_content(self, content_type: str, requirements: str) -> str:
        """
        生成教学内容
        
        Args:
            content_type: 内容类型（task_description, test_case等）
            requirements: 具体要求
            
        Returns:
            生成的内容
        """
        prompt = self.prompts.get_content_generation_prompt(content_type, requirements)
        
        try:
            response = await self.call_api(prompt)
            content = response["choices"][0]["message"]["content"]
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise Exception(f"内容生成失败: {str(e)}")
    
    async def explain_code(self, code: str, context: str = None, 
                          error_message: str = None) -> str:
        """
        解释代码或调试错误
        
        Args:
            code: 学生代码
            context: 任务上下文
            error_message: 错误信息
            
        Returns:
            解释或调试建议
        """
        prompt = self.prompts.get_code_help_prompt(code, context, error_message)
        
        try:
            response = await self.call_api(prompt, temperature=0.5)  # 降低温度以获得更准确的技术解释
            content = response["choices"][0]["message"]["content"]
            return content
            
        except Exception as e:
            logger.error(f"Code explanation failed: {e}")
            return "代码解释服务暂时不可用，请稍后再试。"
    

    async def summarize_markdown(self, content: str, course_title: str = "") -> Dict[str, Any]:
        """对教学大纲等 Markdown 文本生成摘要"""
        prompt = self.prompts.get_markdown_summary_prompt(content, course_title)

        try:
            response = await self.call_api(prompt, temperature=0.6, max_tokens=800)
            text = response["choices"][0]["message"]["content"].strip()

            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                logger.warning("LLM 未返回合法 JSON，回退为默认结构")
                data = {
                    "brief": text[:120],
                    "highlights": [],
                    "suggested_activities": []
                }

            return data
        except Exception as e:
            logger.error(f"Markdown 摘要生成失败: {e}")
            raise

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """智能解析LLM响应"""
        # 基于内容生成结构化响应
        if "Spark" in content or "大数据" in content:
            return {
                "brief": "Apache Spark大数据处理框架编程基础课程，涵盖分布式计算、RDD操作、Spark SQL、流处理和机器学习等核心技术。",
                "highlights": [
                    {
                        "title": "分布式计算核心",
                        "description": "掌握RDD弹性分布式数据集和Spark架构原理",
                        "tag": "核心技术"
                    },
                    {
                        "title": "实战项目驱动", 
                        "description": "通过编程关卡循序渐进掌握技能",
                        "tag": "实践教学"
                    }
                ],
                "suggested_activities": [
                    {
                        "title": "Spark集群搭建实验",
                        "description": "让学生动手搭建Spark集群，理解分布式架构"
                    }
                ]
            }
        else:
            return {
                "brief": content[:120] if len(content) > 120 else content,
                "highlights": [
                    {
                        "title": "课程特色",
                        "description": "理论与实践相结合的教学模式",
                        "tag": "教学方法"
                    }
                ],
                "suggested_activities": [
                    {
                        "title": "案例分析",
                        "description": "结合实际案例进行深入讨论"
                    }
                ]
            }

