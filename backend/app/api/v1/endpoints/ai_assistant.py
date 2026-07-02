"""
AI助教API端点
提供AI辅助教学相关的接口
"""

import os
import ast
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.ai_assistant import AIService
from app.models import models as db_models
from app.models.models import AIConfig, AIUsageLog, Training
from app.crud import stage_crud

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


# ==================== 请求/响应模型 ====================

class GradingRequest(BaseModel):
    """批阅请求"""
    training_id: int
    student_answer: str
    user_id: Optional[int] = None

class GradingResponse(BaseModel):
    """批阅响应"""
    score: int
    comment: str
    suggestions: list[str]
    error: Optional[str] = None

class ContentGenerationRequest(BaseModel):
    """内容生成请求"""
    content_type: str  # task_description, test_case, evaluation_criteria
    requirements: str
    user_id: Optional[int] = None

class CodeHelpRequest(BaseModel):
    """代码辅导请求"""
    code: str
    context: Optional[str] = None
    error_message: Optional[str] = None
    user_id: Optional[int] = None

class ConceptExplainRequest(BaseModel):
    """概念解释请求"""
    concept: str
    context: Optional[str] = None
    user_id: Optional[int] = None


class MarkdownSummaryRequest(BaseModel):
    """Markdown 摘要请求"""
    content: str
    course_title: Optional[str] = ""


class AIConfigRequest(BaseModel):
    """AI配置请求"""
    provider: str = "deepseek"
    endpoint: str
    api_key: str
    model_name: str
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7
    features: Optional[Dict[str, bool]] = None

class MarkdownSummaryResponse(BaseModel):
    """Markdown 摘要响应"""
    brief: str = ""
    highlights: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_activities: List[Dict[str, Any]] = Field(default_factory=list)

# ==================== 新的AI学习助手请求/响应模型 ====================

class AIChatRequest(BaseModel):
    """AI对话请求"""
    message: str
    context: Optional[str] = None
    user_id: Optional[int] = None

class AIChatResponse(BaseModel):
    """AI对话响应"""
    reply: str
    quota_info: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class ExplainConceptRequest(BaseModel):
    """概念解释请求"""
    concept: str
    context: Optional[str] = None
    user_id: Optional[int] = None

class ExplainConceptResponse(BaseModel):
    """概念解释响应"""
    explanation: str
    quota_info: Dict[str, Any]
    success: bool
    error: Optional[str] = None


class PracticeFailureHintRequest(BaseModel):
    """闯关失败解释请求"""

    stage_id: int
    code_content: str
    failure_cases: List[Dict[str, Any]] = Field(default_factory=list)
    handbook_markdown: Optional[str] = None
    visible_error_output: Optional[str] = None
    user_id: Optional[int] = None


class PracticeFailureHintResponse(BaseModel):
    """闯关失败解释响应"""

    hint: str
    quota_info: Dict[str, Any]
    success: bool
    error: Optional[str] = None


def _load_test_results(raw_value: Optional[str]) -> List[Dict[str, Any]]:
    if not raw_value:
        return []

    for loader in (json.loads, ast.literal_eval):
        try:
            loaded = loader(raw_value)
            if isinstance(loaded, list):
                return [item for item in loaded if isinstance(item, dict)]
        except Exception:
            continue
    return []


def _build_public_failure_context(
    db: Session,
    stage_id: int,
    user_id: int,
    user_role: str,
) -> Dict[str, Any]:
    if user_role == "student":
        result = stage_crud.get_stage_detail_for_student(db, stage_id=stage_id, user_id=user_id)
    elif user_role == "teacher":
        result = stage_crud.get_practice_stage_detail(db, stage_id=stage_id, creator_id=user_id)
    elif user_role == "admin":
        stage = db.query(db_models.Task).filter(
            db_models.Task.id == stage_id,
            db_models.Task.deleted_at.is_(None),
        ).first()
        result = (stage, []) if stage else None
    else:
        result = None

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问该关卡"
        )

    stage, _ = result
    latest_failure = db.query(db_models.TaskEvaluationResult).filter(
        db_models.TaskEvaluationResult.task_id == stage_id,
        db_models.TaskEvaluationResult.user_id == user_id,
        db_models.TaskEvaluationResult.status.in_(["fail", "error", "timeout"]),
    ).order_by(db_models.TaskEvaluationResult.created_at.desc()).first()

    if latest_failure is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有可用于诊断的真实失败评测记录"
        )

    public_case_ids = {
        test.case_id
        for test in db.query(db_models.TaskTest).filter(
            db_models.TaskTest.task_id == stage_id,
            db_models.TaskTest.is_hidden == False,
        ).all()
        if test.case_id
    }
    raw_test_results = _load_test_results(latest_failure.test_results)
    public_failures = []
    for item in raw_test_results:
        case_id = item.get("case_id") or item.get("caseId") or item.get("name")
        status_value = str(item.get("status") or item.get("result") or "").lower()
        if case_id in public_case_ids and status_value not in ("pass", "passed", "success"):
            public_failures.append({
                "case_id": case_id,
                "status": item.get("status") or item.get("result"),
                "message": str(item.get("message") or item.get("error") or "")[:500],
            })

    return {
        "stage_id": stage_id,
        "stage_title": stage.title,
        "handbook_markdown": (stage.handbook_markdown or "")[:4000],
        "submission_code": latest_failure.submission_code or "",
        "failure_summary": {
            "status": latest_failure.status,
            "score": latest_failure.score,
            "total_tests": latest_failure.total_tests,
            "passed_tests": latest_failure.passed_tests,
            "error_message": (latest_failure.error_message or "")[:1200],
            "public_failures": public_failures[:5],
        },
    }

class GenerateQuestionsRequest(BaseModel):
    """试题生成请求"""
    knowledge_point: str
    question_type: str = "single_choice"
    count: int = Field(default=1, ge=1, le=5)  # 最多一次生成5道题
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")
    user_id: Optional[int] = None

class QuestionData(BaseModel):
    """试题数据"""
    type: str
    content: str
    options: List[Dict[str, Any]] = Field(default_factory=list)
    correct_answers: List[Any] = Field(default_factory=list)
    raw_response: Optional[str] = None

class GenerateQuestionsResponse(BaseModel):
    """试题生成响应"""
    questions: List[QuestionData]
    count: int
    quota_info: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class CheckQualityRequest(BaseModel):
    """质量检查请求"""
    question_data: Dict[str, Any]
    user_id: Optional[int] = None

class CheckQualityResponse(BaseModel):
    """质量检查响应"""
    quality_score: int
    suggestions: List[str]
    detailed_analysis: str
    quota_info: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class QuotaInfoResponse(BaseModel):
    """额度信息响应"""
    user_role: str
    monthly_quota: int
    used_this_month: int
    remaining: int
    reset_date: Optional[str] = None
    usage_by_type: Dict[str, int] = Field(default_factory=dict)
    estimated_cost: float = 0.0


@router.post("/summary", response_model=MarkdownSummaryResponse)
async def get_markdown_summary(
    request: MarkdownSummaryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取Markdown内容的智能摘要"""
    # 检查是否有激活的AI配置
    active_config = db.query(AIConfig).filter(AIConfig.is_active == True).first()
    if not active_config and not os.getenv("AI_API_KEY"):
        return MarkdownSummaryResponse(
            brief="",
            highlights=[],
            suggested_activities=[]
        )
    try:
        ai_service = AIService(db, current_user=current_user)
        summary_data = await ai_service.summarize_markdown(
            content=request.content,
            course_title=request.course_title or ""
        )
        return MarkdownSummaryResponse(**summary_data)
    except ValueError as exc:
        # AI未配置时返回空结果，不报500错误
        if "AI服务未配置" in str(exc):
            logger.warning("AI summary skipped: no active AI config")
            return MarkdownSummaryResponse(brief="", highlights=[], suggested_activities=[])
        raise
    except Exception as exc:
        logger.error("Markdown summary failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成摘要失败: {exc}"
        )

# ==================== 新的AI学习助手API端点 ====================

@router.post("/chat", response_model=AIChatResponse)
async def chat_with_ai(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """AI学习助手对话"""
    try:
        user_id = int(current_user["id"])

        ai_service = AIService(db, current_user=current_user)
        result = await ai_service.chat_with_ai(
            user_id=user_id,
            message=request.message,
            context=request.context
        )

        return AIChatResponse(**result)
    except Exception as exc:
        logger.error("AI chat failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI对话失败: {exc}"
        )

@router.post("/explain-concept", response_model=ExplainConceptResponse)
async def explain_concept(
    request: ExplainConceptRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """AI概念解释"""
    try:
        user_id = int(current_user["id"])

        ai_service = AIService(db, current_user=current_user)
        result = await ai_service.explain_concept(
            user_id=user_id,
            concept=request.concept,
            context=request.context
        )

        return ExplainConceptResponse(**result)
    except Exception as exc:
        logger.error("Concept explanation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"概念解释失败: {exc}"
        )


@router.post("/explain-practice-failure", response_model=PracticeFailureHintResponse)
async def explain_practice_failure(
    request: PracticeFailureHintRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """闯关失败后的 AI 分级提示"""
    try:
        user_id = int(current_user["id"])
        user_role = (current_user.get("roles") or ["student"])[0]
        failure_context = _build_public_failure_context(
            db=db,
            stage_id=request.stage_id,
            user_id=user_id,
            user_role=user_role,
        )

        ai_service = AIService(db, current_user=current_user)
        result = await ai_service.explain_practice_failure(
            user_id=user_id,
            stage_id=request.stage_id,
            code_content=failure_context["submission_code"],
            failure_cases=[failure_context["failure_summary"]],
            handbook_markdown=failure_context["handbook_markdown"],
            visible_error_output=failure_context["failure_summary"].get("error_message"),
            user_role=user_role,
            stage_title=failure_context["stage_title"],
        )

        return PracticeFailureHintResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Practice failure hint failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"闯关失败提示失败: {exc}"
        )

@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(
    request: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """AI试题生成（教师专用）"""
    try:
        user_id = int(current_user["id"])

        ai_service = AIService(db, current_user=current_user)
        result = await ai_service.generate_questions(
            user_id=user_id,
            knowledge_point=request.knowledge_point,
            question_type=request.question_type,
            count=request.count,
            difficulty=request.difficulty
        )

        return GenerateQuestionsResponse(**result)
    except Exception as exc:
        logger.error("Question generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"试题生成失败: {exc}"
        )

@router.post("/check-quality", response_model=CheckQualityResponse)
async def check_question_quality(
    request: CheckQualityRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """试题质量检查"""
    try:
        user_id = int(current_user["id"])

        ai_service = AIService(db, current_user=current_user)
        result = await ai_service.check_question_quality(
            user_id=user_id,
            question_data=request.question_data
        )

        return CheckQualityResponse(**result)
    except Exception as exc:
        logger.error("Quality check failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"质量检查失败: {exc}"
        )

@router.get("/quota/{user_id}", response_model=QuotaInfoResponse)
async def get_user_quota(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取用户AI使用额度信息"""
    try:
        from app.services.ai_quota import get_quota_manager
        quota_manager = get_quota_manager(db)
        quota_info = quota_manager.get_quota_stats(user_id)

        # 转换日期格式
        if quota_info.get("reset_date"):
            quota_info["reset_date"] = quota_info["reset_date"].isoformat()

        return QuotaInfoResponse(**quota_info)
    except Exception as exc:
        logger.error("Get quota info failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取额度信息失败: {exc}"
        )
