"""
PromptPilot Feature Service

Provides high-level AI feature methods for the platform. Previously backed by
AgentPilot/PromptPilot (removed: the actual prompt templates lived in an
external SaaS this repo has no access to, so they could not be faithfully
migrated). Every method below now always takes its existing "AI 不可用"
fallback branch — response shape is unchanged, callers do not need to change.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict

from app.models.models import (
    AIUsageLog, User, Task, TaskEvaluationResult,
    StudentCourseProgress, ClassroomCourse, Course, Practice,
    StudentPracticeProgress, CourseVisibilityEnum
)

logger = logging.getLogger(__name__)


class PromptPilotFeatureService:
    """
    High-level service for AI features. AgentPilot/PromptPilot backing has
    been removed; every feature method takes its existing unavailable-fallback
    branch until a Phase1 doubao_client-backed replacement lands.
    """

    def __init__(self, db: Session):
        self.db = db
        self._client = None
        self._init_error: Optional[str] = "AgentPilot 已下线，功能待迁移到方舟直连"

    @property
    def is_available(self) -> bool:
        """Check if the underlying LLM client is available."""
        return self._client is not None
    
    def _log_usage(
        self,
        user_id: int,
        user_role: str,
        feature_type: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        response_time: float = 0.0,
        error_message: Optional[str] = None
    ):
        """Log AI usage to the database."""
        try:
            log_entry = AIUsageLog(
                user_id=user_id,
                user_role=user_role,
                feature_type=feature_type,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                response_time=response_time,
                error_message=error_message,
                cost_estimate=(prompt_tokens + completion_tokens) * 0.000002  # Rough estimate
            )
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to log AI usage: {e}")
    
    # ==================== Feature 1: Dashboard Recommendation ====================
    
    async def generate_recommendation_reason(
        self,
        user_id: int,
        user_name: str,
        course_title: str,
        recommendation_reason: str,
        context_data: str,
        user_role: str = "student"
    ) -> Dict[str, Any]:
        """
        Generate a human-friendly recommendation reason for a course.
        
        This is used by the personalization engine to explain why a course
        is being recommended to a student.
        
        Args:
            user_id: Student's user ID
            user_name: Student's full name
            course_title: Title of the recommended course
            recommendation_reason: Type of recommendation (DEADLINE, SKILL_GAP, OPTIONAL_PATH)
            context_data: Additional context (e.g., '2 days', 'related to Quantum AI project')
            user_role: User's role (student/teacher)
            
        Returns:
            Dict with 'reason_text' (human-friendly explanation) and metadata
        """
        if not self.is_available:
            return {
                "success": False,
                "error": self._init_error or "PromptPilot not available",
                "reason_text": self._fallback_recommendation_reason(recommendation_reason, context_data)
            }
        
        task_id = PROMPTPILOT_TASKS["recommendation"]
        # 使用PromptPilot模板中定义的变量名 {{$user_name}} 等，变量名带$前缀
        variables = {
            "$user_name": user_name,
            "$course_title": course_title,
            "$recommendation_reason": recommendation_reason,
            "$context_data": context_data
        }
        
        result = await self._client.call_task(task_id, variables)
        
        self._log_usage(
            user_id=user_id,
            user_role=user_role,
            feature_type="dashboard_recommendation",
            prompt_tokens=result.get("prompt_tokens", 0),
            completion_tokens=result.get("completion_tokens", 0),
            error_message=result.get("error")
        )
        
        if result.get("success"):
            return {
                "success": True,
                "reason_text": result["content"],
                "run_id": result.get("run_id"),
                "tokens_used": result.get("total_tokens", 0)
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "reason_text": self._fallback_recommendation_reason(recommendation_reason, context_data)
            }
    
    def _fallback_recommendation_reason(self, reason_type: str, context: str) -> str:
        """Generate a fallback recommendation reason when AI is unavailable."""
        reasons = {
            "DEADLINE": f"该课程截止日期临近（{context}），建议优先完成。",
            "SKILL_GAP": f"根据您的学习记录，该课程可以帮助您提升薄弱技能点（{context}）。",
            "OPTIONAL_PATH": f"这是一门拓展课程（{context}），可以帮助您拓宽知识面。",
            "MANDATORY": f"这是一门必修课程（{context}），请按时完成。"
        }
        return reasons.get(reason_type, f"推荐学习该课程：{context}")
    
    # ==================== Feature 2: AI Brainstorm ====================
    
    async def brainstorm(
        self,
        user_id: int,
        user_prompt: str,
        project_context: Optional[List[str]] = None,
        user_role: str = "student"
    ) -> Dict[str, Any]:
        """
        AI-powered brainstorming for project canvas.
        
        Args:
            user_id: User's ID
            user_prompt: User's brainstorming topic/question
            project_context: Optional list of existing project nodes
            user_role: User's role
            
        Returns:
            Dict with 'ideas' list and metadata
        """
        if not self.is_available:
            return {
                "success": False,
                "error": self._init_error or "PromptPilot not available",
                "ideas": []
            }
        
        task_id = PROMPTPILOT_TASKS["brainstorm"]
        # 使用PromptPilot模板中定义的变量名 {{$project_context}}, {{$user_prompt}}
        variables = {
            "$project_context": json.dumps(project_context or [], ensure_ascii=False),
            "$user_prompt": user_prompt
        }
        
        result = await self._client.call_task(task_id, variables, temperature=0.8)
        
        self._log_usage(
            user_id=user_id,
            user_role=user_role,
            feature_type="brainstorm",
            prompt_tokens=result.get("prompt_tokens", 0),
            completion_tokens=result.get("completion_tokens", 0),
            error_message=result.get("error")
        )
        
        if result.get("success"):
            # Try to parse ideas from the response
            content = result["content"]
            ideas = self._parse_brainstorm_response(content)
            return {
                "success": True,
                "content": content,
                "ideas": ideas,
                "run_id": result.get("run_id"),
                "tokens_used": result.get("total_tokens", 0)
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "ideas": []
            }
    
    def _parse_brainstorm_response(self, content: str) -> List[Dict[str, str]]:
        """Parse brainstorm response into structured ideas."""
        ideas = []
        try:
            # Try parsing as JSON first
            data = json.loads(content)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "ideas" in data:
                return data["ideas"]
        except json.JSONDecodeError:
            pass
        
        # Parse numbered list format
        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-") or line.startswith("•")):
                # Remove numbering/bullet
                text = line.lstrip("0123456789.-•) ").strip()
                if text:
                    ideas.append({"idea": text})
        
        return ideas if ideas else [{"idea": content[:500]}]
    
    # ==================== Feature 3: Command Palette NLU ====================
    
    async def parse_natural_language_command(
        self,
        user_id: int,
        user_raw_query: str,
        user_role: str = "teacher"
    ) -> Dict[str, Any]:
        """
        Parse natural language command into structured API call.
        
        Args:
            user_id: User's ID
            user_raw_query: Raw natural language query (e.g., "搜索张老师的数据结构课")
            user_role: User's role
            
        Returns:
            Dict with parsed 'command' structure
        """
        if not self.is_available:
            return {
                "success": False,
                "error": self._init_error or "PromptPilot not available",
                "command": None
            }
        
        task_id = PROMPTPILOT_TASKS["command_nlu"]
        
        # Few-shot examples for NLU
        few_shot_examples = """
示例1:
输入: "搜索张老师的数据结构课"
输出: {"action": "search", "entity": "classroom_course", "filters": {"teacher_name": "张老师", "keyword": "数据结构"}}

示例2:
输入: "创建一个新课堂"
输出: {"action": "create", "entity": "classroom", "params": {}}

示例3:
输入: "查看我的学生列表"
输出: {"action": "list", "entity": "students", "filters": {}}

示例4:
输入: "打开Python课程"
输出: {"action": "navigate", "entity": "course", "filters": {"keyword": "Python"}}
"""
        
        # 使用PromptPilot模板中定义的变量名（不带$前缀）
        variables = {
            "few_shot_examples": few_shot_examples,
            "user_raw_query": user_raw_query
        }
        
        result = await self._client.call_task(task_id, variables, temperature=0.3)
        
        self._log_usage(
            user_id=user_id,
            user_role=user_role,
            feature_type="command_nlu",
            prompt_tokens=result.get("prompt_tokens", 0),
            completion_tokens=result.get("completion_tokens", 0),
            error_message=result.get("error")
        )
        
        if result.get("success"):
            command = self._parse_command_response(result["content"])
            return {
                "success": True,
                "command": command,
                "raw_response": result["content"],
                "run_id": result.get("run_id"),
                "tokens_used": result.get("total_tokens", 0)
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "command": None
            }
    
    def _parse_command_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Parse NLU response into command structure."""
        import re
        
        # Try to extract JSON from <output> tag first
        output_match = re.search(r'<output>\s*(\{.*?\})\s*</output>', content, re.DOTALL)
        if output_match:
            try:
                return json.loads(output_match.group(1))
            except json.JSONDecodeError:
                pass
        
        try:
            # Try direct JSON parse
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try to extract nested JSON (with filters object)
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)?\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback: return as search command
        return {
            "action": "search",
            "entity": "all",
            "filters": {"keyword": content[:100]}
        }
    
    # ==================== Feature 4a: Proactive Code Suggestion ====================
    
    async def suggest_code_optimization(
        self,
        user_id: int,
        current_code_snippet: str,
        task_objective: str,
        task_answer: Optional[str] = None,
        language: str = "Python",
        user_role: str = "student"
    ) -> Dict[str, Any]:
        """
        Generate proactive code optimization suggestions.
        
        Args:
            user_id: Student's user ID
            current_code_snippet: Student's current code
            task_objective: Task description from handbook
            task_answer: Optional reference answer
            language: Programming language
            user_role: User's role
            
        Returns:
            Dict with 'suggestion' text
        """
        if not self.is_available:
            return {
                "success": False,
                "error": self._init_error or "PromptPilot not available",
                "suggestion": ""
            }
        
        task_id = PROMPTPILOT_TASKS["code_suggestion"]
        # 使用PromptPilot模板中定义的变量名，尝试带$前缀
        variables = {
            "$task_objective": task_objective[:1000],
            "$current_code_snippet": current_code_snippet[:3000],
            "$language": language,
            "$task_answer": (task_answer or "")[:2000]
        }
        
        result = await self._client.call_task(task_id, variables, temperature=0.5)
        
        self._log_usage(
            user_id=user_id,
            user_role=user_role,
            feature_type="coding_assistant_suggestion",
            prompt_tokens=result.get("prompt_tokens", 0),
            completion_tokens=result.get("completion_tokens", 0),
            error_message=result.get("error")
        )
        
        if result.get("success"):
            return {
                "success": True,
                "suggestion": result["content"],
                "run_id": result.get("run_id"),
                "tokens_used": result.get("total_tokens", 0)
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "suggestion": ""
            }
    
    # ==================== Feature 4b: Code Explanation ====================
    
    async def explain_code_snippet(
        self,
        user_id: int,
        selected_code_snippet: str,
        explanation_style: str = "detailed",
        user_role: str = "student"
    ) -> Dict[str, Any]:
        """
        Explain selected code snippet.
        
        Args:
            user_id: User's ID
            selected_code_snippet: Code to explain
            explanation_style: Style of explanation (简洁/详细/ELI5)
            user_role: User's role
            
        Returns:
            Dict with 'explanation' text
        """
        if not self.is_available:
            return {
                "success": False,
                "error": self._init_error or "PromptPilot not available",
                "explanation": ""
            }
        
        task_id = PROMPTPILOT_TASKS["code_explanation"]
        # 尝试多种变量名格式
        variables = {
            "selected_code": selected_code_snippet[:3000],
            "explanation_style": explanation_style,
            "SELECTED_CODE": selected_code_snippet[:3000],
            "EXPLANATION_STYLE": explanation_style
        }
        
        result = await self._client.call_task(task_id, variables, temperature=0.5)
        
        self._log_usage(
            user_id=user_id,
            user_role=user_role,
            feature_type="coding_assistant_explanation",
            prompt_tokens=result.get("prompt_tokens", 0),
            completion_tokens=result.get("completion_tokens", 0),
            error_message=result.get("error")
        )
        
        if result.get("success"):
            return {
                "success": True,
                "explanation": result["content"],
                "run_id": result.get("run_id"),
                "tokens_used": result.get("total_tokens", 0)
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "explanation": ""
            }
    
    # ==================== Feature 4c: Error Diagnosis ====================
    
    async def diagnose_evaluation_error(
        self,
        user_id: int,
        failed_code_snippet: str,
        error_log: str,
        failed_test_case_input: str,
        failed_test_case_expected_output: str,
        task_objective: str,
        user_role: str = "student"
    ) -> Dict[str, Any]:
        """
        Diagnose evaluation error and suggest fixes.
        
        Args:
            user_id: Student's user ID
            failed_code_snippet: Student's submitted code
            error_log: Error message or test results
            failed_test_case_input: Input that caused failure
            failed_test_case_expected_output: Expected output
            task_objective: Task description from handbook
            user_role: User's role
            
        Returns:
            Dict with 'diagnosis' text explaining the error and suggested fix
        """
        if not self.is_available:
            return {
                "success": False,
                "error": self._init_error or "PromptPilot not available",
                "diagnosis": ""
            }
        
        task_id = PROMPTPILOT_TASKS["error_diagnosis"]
        # 使用PromptPilot模板中定义的变量名 {{$task_objective}}, {{$failed_code_snippet}}, {{$failed_test_case_input}}, {{$failed_test_case_expected_output}}, {{$error_log}}
        variables = {
            "$task_objective": task_objective[:1000],
            "$failed_code_snippet": failed_code_snippet[:3000],
            "$failed_test_case_input": failed_test_case_input[:500],
            "$failed_test_case_expected_output": failed_test_case_expected_output[:500],
            "$error_log": error_log[:1500]
        }
        
        result = await self._client.call_task(task_id, variables, temperature=0.4)
        
        self._log_usage(
            user_id=user_id,
            user_role=user_role,
            feature_type="coding_assistant_diagnosis",
            prompt_tokens=result.get("prompt_tokens", 0),
            completion_tokens=result.get("completion_tokens", 0),
            error_message=result.get("error")
        )
        
        if result.get("success"):
            return {
                "success": True,
                "diagnosis": result["content"],
                "run_id": result.get("run_id"),
                "tokens_used": result.get("total_tokens", 0)
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "diagnosis": ""
            }
    
    # ==================== Feature 5: General Chat ====================
    
    def _build_student_context(self, user_id: int) -> str:
        """
        构建学生学习上下文，用于AI助手对话。
        
        包含：
        - 学生已掌握的技能
        - 学习进度
        - 可选拓展课程
        """
        context_parts = []
        
        try:
            # 1. 获取学生基本信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                context_parts.append(f"【学生信息】\n用户名：{user.username}\n姓名：{user.full_name or '未设置'}")
            
            # 2. 获取学生已掌握的技能（从通过的任务中聚合）
            skill_counts = defaultdict(int)
            passed_tasks = self.db.query(Task.skills)\
                .join(TaskEvaluationResult, Task.id == TaskEvaluationResult.task_id)\
                .filter(TaskEvaluationResult.user_id == user_id)\
                .filter(TaskEvaluationResult.status == 'pass')\
                .all()
            
            for task_row in passed_tasks:
                if task_row.skills:
                    try:
                        skills_list = json.loads(task_row.skills) if task_row.skills.startswith('[') else [s.strip() for s in task_row.skills.split(',') if s.strip()]
                        for skill in skills_list:
                            skill_counts[skill] += 1
                    except:
                        pass
            
            if skill_counts:
                top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                skills_text = "、".join([f"{skill}({count}次)" for skill, count in top_skills])
                context_parts.append(f"\n【已掌握技能】\n{skills_text}")
            else:
                context_parts.append("\n【已掌握技能】\n暂无（请完成更多任务来积累技能）")
            
            # 3. 获取学习进度
            progress_records = self.db.query(
                StudentCourseProgress,
                ClassroomCourse,
                Course
            ).join(
                ClassroomCourse, StudentCourseProgress.classroom_course_id == ClassroomCourse.id
            ).join(
                Course, ClassroomCourse.course_id == Course.id
            ).filter(
                StudentCourseProgress.student_id == user_id
            ).all()
            
            in_progress = []
            completed = []
            for progress, cc, course in progress_records:
                status_str = progress.student_status.value if progress.student_status else 'NOT_STARTED'
                course_info = f"{course.title}"
                if status_str in ['COMPLETED', 'PASSED']:
                    completed.append(course_info)
                elif status_str in ['ONGOING', 'IN_PROGRESS']:
                    in_progress.append(f"{course_info}（进度：{progress.completed_task_count}个任务完成）")
            
            context_parts.append(f"\n【学习进度】")
            if in_progress:
                context_parts.append(f"进行中课程：{'; '.join(in_progress)}")
            else:
                context_parts.append("进行中课程：暂无")
            if completed:
                context_parts.append(f"已完成课程：{'; '.join(completed)}")
            else:
                context_parts.append("已完成课程：暂无")
            
            # 4. 获取可选拓展课程（推荐）
            try:
                available_courses = self.db.query(Course)\
                    .filter(Course.visibility.in_([
                        CourseVisibilityEnum.PUBLIC_SELF, 
                        CourseVisibilityEnum.PUBLIC_PLATFORM
                    ]))\
                    .limit(5).all()
                
                # 如果没有公开课程，获取所有课程
                if not available_courses:
                    available_courses = self.db.query(Course).limit(5).all()
                
                if available_courses:
                    courses_text = []
                    for i, course in enumerate(available_courses, 1):
                        difficulty = course.difficulty.value if course.difficulty else "未设置"
                        direction = course.direction or "通用"
                        courses_text.append(f"{i}. {course.title} - 难度：{difficulty}，方向：{direction}")
                    context_parts.append(f"\n【平台可选课程】\n" + "\n".join(courses_text))
            except Exception as e:
                logger.warning(f"获取可选课程失败: {e}")
            
            # 5. 获取实践进度
            practice_progress = self.db.query(
                StudentPracticeProgress,
                Practice
            ).join(
                Practice, StudentPracticeProgress.practice_id == Practice.id
            ).filter(
                StudentPracticeProgress.student_id == user_id
            ).limit(5).all()
            
            if practice_progress:
                practice_text = []
                for pp, practice in practice_progress:
                    status = "已完成" if pp.is_completed else f"进行中（{pp.completed_task_count}个关卡）"
                    practice_text.append(f"- {practice.title}：{status}")
                context_parts.append(f"\n【实践进度】\n" + "\n".join(practice_text))
            
            # 6. 添加推荐规则提示
            context_parts.append("""
【推荐规则】
- 优先推荐与学生已掌握技能相关的进阶课程
- 考虑课程难度是否适合学生当前水平
- 如果学生有进行中的课程，鼓励先完成
- 给出具体的学习建议和理由""")
            
        except Exception as e:
            logger.error(f"构建学生上下文失败: {e}")
            context_parts.append(f"\n[上下文构建异常: {str(e)[:100]}]")
        
        return "\n".join(context_parts)
    
    async def general_chat(
        self,
        user_id: int,
        user_message: str,
        context: Optional[str] = None,
        user_role: str = "student",
        auto_enrich_context: bool = True
    ) -> Dict[str, Any]:
        """
        General AI conversation with automatic context enrichment.
        
        Args:
            user_id: User's ID
            user_message: User's message
            context: Optional context information
            user_role: User's role
            auto_enrich_context: Whether to automatically enrich context with student data
            
        Returns:
            Dict with 'reply' text
        """
        if not self.is_available:
            return {
                "success": False,
                "error": self._init_error or "PromptPilot not available",
                "reply": "AI助手暂时不可用，请稍后再试。"
            }
        
        # 自动丰富上下文（针对学生）
        full_context = context or ""
        if auto_enrich_context and user_id and user_role == "student":
            try:
                student_context = self._build_student_context(user_id)
                full_context = f"{student_context}\n\n{context or ''}"
                logger.info(f"[general_chat] 已构建学生上下文，长度: {len(student_context)}")
            except Exception as e:
                logger.error(f"[general_chat] 构建学生上下文失败: {e}")
        
        task_id = PROMPTPILOT_TASKS["general_chat"]
        # 使用丰富后的上下文
        variables = {
            "context": full_context[:3000],
            "user_message": user_message[:2000],
            "RETRIEVED_CONTEXT": full_context[:3000],
            "USER_QUERY": user_message[:2000]
        }
        
        logger.info(f"[general_chat] 调用PromptPilot，上下文长度: {len(full_context)}, 问题: {user_message[:100]}")
        
        result = await self._client.call_task(task_id, variables, temperature=0.7)
        
        self._log_usage(
            user_id=user_id,
            user_role=user_role,
            feature_type="general_chat",
            prompt_tokens=result.get("prompt_tokens", 0),
            completion_tokens=result.get("completion_tokens", 0),
            error_message=result.get("error")
        )
        
        if result.get("success"):
            return {
                "success": True,
                "reply": result["content"],
                "run_id": result.get("run_id"),
                "tokens_used": result.get("total_tokens", 0)
            }
        else:
            return {
                "success": False,
                "error": result.get("error"),
                "reply": "AI助手暂时无法回复，请稍后再试。"
            }

