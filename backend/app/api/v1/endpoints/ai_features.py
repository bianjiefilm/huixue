"""
AI Features API Endpoints

Provides REST API endpoints for AI-powered features using PromptPilot integration.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import logging

from app.core.ai_gate import require_ai_enabled
from app.core.config import settings
from app.core.database import get_db
from app.services.ai_features import PromptPilotFeatureService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-features", tags=["AI Features"])


# ==================== Request/Response Models ====================

# Feature 1: Dashboard Recommendation
class RecommendationReasonRequest(BaseModel):
    """Request for generating recommendation reason."""
    user_name: str = Field(..., description="Student's full name")
    course_title: str = Field(..., description="Title of the recommended course")
    recommendation_reason: str = Field(..., description="Type: DEADLINE, SKILL_GAP, OPTIONAL_PATH, MANDATORY")
    context_data: str = Field(..., description="Additional context (e.g., '2 days')")
    user_id: Optional[int] = Field(default=1, description="User ID")
    user_role: Optional[str] = Field(default="student", description="User role")


class RecommendationReasonResponse(BaseModel):
    """Response for recommendation reason."""
    success: bool
    reason_text: str
    run_id: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


# Feature 2: AI Brainstorm
class BrainstormRequest(BaseModel):
    """Request for AI brainstorming."""
    user_prompt: str = Field(..., description="Brainstorming topic/question")
    project_context: Optional[List[str]] = Field(default=None, description="Existing project nodes")
    user_id: Optional[int] = Field(default=1, description="User ID")
    user_role: Optional[str] = Field(default="student", description="User role")


class BrainstormResponse(BaseModel):
    """Response for brainstorming."""
    success: bool
    content: Optional[str] = None
    ideas: List[Dict[str, Any]] = Field(default_factory=list)
    run_id: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


# Feature 3: Command Palette NLU
class CommandParseRequest(BaseModel):
    """Request for parsing natural language command."""
    user_raw_query: str = Field(..., description="Raw natural language query")
    user_id: Optional[int] = Field(default=1, description="User ID")
    user_role: Optional[str] = Field(default="teacher", description="User role")


class CommandParseResponse(BaseModel):
    """Response for command parsing."""
    success: bool
    command: Optional[Dict[str, Any]] = None
    raw_response: Optional[str] = None
    run_id: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


# Feature 4a: Code Suggestion
class CodeSuggestionRequest(BaseModel):
    """Request for proactive code suggestions."""
    current_code_snippet: str = Field(..., description="Student's current code")
    task_objective: str = Field(..., description="Task description from handbook")
    task_answer: Optional[str] = Field(default=None, description="Optional reference answer")
    language: Optional[str] = Field(default="Python", description="Programming language")
    user_id: Optional[int] = Field(default=1, description="User ID")
    user_role: Optional[str] = Field(default="student", description="User role")


class CodeSuggestionResponse(BaseModel):
    """Response for code suggestion."""
    success: bool
    suggestion: str = ""
    run_id: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


# Feature 4b: Code Explanation
class CodeExplanationRequest(BaseModel):
    """Request for code explanation."""
    selected_code_snippet: str = Field(..., description="Code to explain")
    explanation_style: Optional[str] = Field(default="detailed", description="Style: 简洁/详细/ELI5")
    user_id: Optional[int] = Field(default=1, description="User ID")
    user_role: Optional[str] = Field(default="student", description="User role")


class CodeExplanationResponse(BaseModel):
    """Response for code explanation."""
    success: bool
    explanation: str = ""
    run_id: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


# Feature 4c: Error Diagnosis
class ErrorDiagnosisRequest(BaseModel):
    """Request for error diagnosis."""
    failed_code_snippet: str = Field(..., description="Student's submitted code")
    error_log: str = Field(..., description="Error message or test results")
    failed_test_case_input: str = Field(..., description="Input that caused failure")
    failed_test_case_expected_output: str = Field(..., description="Expected output")
    task_objective: str = Field(..., description="Task description from handbook")
    user_id: Optional[int] = Field(default=1, description="User ID")
    user_role: Optional[str] = Field(default="student", description="User role")


class ErrorDiagnosisResponse(BaseModel):
    """Response for error diagnosis."""
    success: bool
    diagnosis: str = ""
    run_id: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


# Feature 5: General Chat
class GeneralChatRequest(BaseModel):
    """Request for general chat."""
    user_message: str = Field(..., description="User's message")
    context: Optional[str] = Field(default=None, description="Optional context information")
    user_id: Optional[int] = Field(default=1, description="User ID")
    user_role: Optional[str] = Field(default="student", description="User role")


class GeneralChatResponse(BaseModel):
    """Response for general chat."""
    success: bool
    reply: str = ""
    run_id: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


# Service Status
class ServiceStatusResponse(BaseModel):
    """Response for service status check."""
    available: bool
    message: str
    task_ids: Dict[str, str]


# ==================== API Endpoints ====================

@router.get("/status", response_model=ServiceStatusResponse)
async def get_service_status(db: Session = Depends(get_db)):
    """
    Check if the AI features service is available.
    """
    from app.services.agentpilot import PROMPTPILOT_TASKS

    if not settings.AI_FEATURES_ENABLED:
        return ServiceStatusResponse(
            available=False,
            message="AI 功能当前未开放",
            task_ids={},
        )

    service = PromptPilotFeatureService(db)
    return ServiceStatusResponse(
        available=service.is_available,
        message="PromptPilot service is available" if service.is_available else "PromptPilot not configured",
        task_ids=PROMPTPILOT_TASKS
    )


@router.post("/recommendation/explain", response_model=RecommendationReasonResponse, dependencies=[Depends(require_ai_enabled)])
async def generate_recommendation_reason(
    request: RecommendationReasonRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a human-friendly recommendation reason for a course.
    
    Used by the personalization engine to explain why a course
    is being recommended to a student.
    """
    try:
        service = PromptPilotFeatureService(db)
        result = await service.generate_recommendation_reason(
            user_id=request.user_id,
            user_name=request.user_name,
            course_title=request.course_title,
            recommendation_reason=request.recommendation_reason,
            context_data=request.context_data,
            user_role=request.user_role
        )
        return RecommendationReasonResponse(**result)
    except Exception as e:
        logger.error(f"Recommendation reason generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成推荐理由失败: {e}"
        )


@router.post("/brainstorm", response_model=BrainstormResponse, dependencies=[Depends(require_ai_enabled)])
async def ai_brainstorm(
    request: BrainstormRequest,
    db: Session = Depends(get_db)
):
    """
    AI-powered brainstorming for project canvas.
    
    Generates creative ideas based on user's topic and existing project context.
    """
    try:
        service = PromptPilotFeatureService(db)
        result = await service.brainstorm(
            user_id=request.user_id,
            user_prompt=request.user_prompt,
            project_context=request.project_context,
            user_role=request.user_role
        )
        return BrainstormResponse(**result)
    except Exception as e:
        logger.error(f"Brainstorm failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI头脑风暴失败: {e}"
        )


@router.post("/command/parse", response_model=CommandParseResponse, dependencies=[Depends(require_ai_enabled)])
async def parse_command(
    request: CommandParseRequest,
    db: Session = Depends(get_db)
):
    """
    Parse natural language command into structured API call.
    
    Used by the global command palette (Ctrl+K) to understand user intent.
    """
    try:
        service = PromptPilotFeatureService(db)
        result = await service.parse_natural_language_command(
            user_id=request.user_id,
            user_raw_query=request.user_raw_query,
            user_role=request.user_role
        )
        return CommandParseResponse(**result)
    except Exception as e:
        logger.error(f"Command parse failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"命令解析失败: {e}"
        )


@router.post("/code/suggest", response_model=CodeSuggestionResponse, dependencies=[Depends(require_ai_enabled)])
async def suggest_code_optimization(
    request: CodeSuggestionRequest,
    db: Session = Depends(get_db)
):
    """
    Generate proactive code optimization suggestions.
    
    Analyzes student's code and provides helpful suggestions
    based on the task objective and reference answer.
    """
    try:
        service = PromptPilotFeatureService(db)
        result = await service.suggest_code_optimization(
            user_id=request.user_id,
            current_code_snippet=request.current_code_snippet,
            task_objective=request.task_objective,
            task_answer=request.task_answer,
            language=request.language,
            user_role=request.user_role
        )
        return CodeSuggestionResponse(**result)
    except Exception as e:
        logger.error(f"Code suggestion failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码建议生成失败: {e}"
        )


@router.post("/code/explain", response_model=CodeExplanationResponse, dependencies=[Depends(require_ai_enabled)])
async def explain_code(
    request: CodeExplanationRequest,
    db: Session = Depends(get_db)
):
    """
    Explain selected code snippet.
    
    Provides detailed explanation of code functionality,
    logic, and potential issues.
    """
    try:
        service = PromptPilotFeatureService(db)
        result = await service.explain_code_snippet(
            user_id=request.user_id,
            selected_code_snippet=request.selected_code_snippet,
            explanation_style=request.explanation_style,
            user_role=request.user_role
        )
        return CodeExplanationResponse(**result)
    except Exception as e:
        logger.error(f"Code explanation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"代码解释失败: {e}"
        )


@router.post("/code/diagnose", response_model=ErrorDiagnosisResponse, dependencies=[Depends(require_ai_enabled)])
async def diagnose_error(
    request: ErrorDiagnosisRequest,
    db: Session = Depends(get_db)
):
    """
    Diagnose evaluation error and suggest fixes.
    
    Analyzes failed code submission along with error logs and test cases
    to provide detailed diagnosis and fix suggestions.
    """
    try:
        service = PromptPilotFeatureService(db)
        result = await service.diagnose_evaluation_error(
            user_id=request.user_id,
            failed_code_snippet=request.failed_code_snippet,
            error_log=request.error_log,
            failed_test_case_input=request.failed_test_case_input,
            failed_test_case_expected_output=request.failed_test_case_expected_output,
            task_objective=request.task_objective,
            user_role=request.user_role
        )
        return ErrorDiagnosisResponse(**result)
    except Exception as e:
        logger.error(f"Error diagnosis failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"错误诊断失败: {e}"
        )


@router.post("/chat", response_model=GeneralChatResponse, dependencies=[Depends(require_ai_enabled)])
async def general_chat(
    request: GeneralChatRequest,
    db: Session = Depends(get_db)
):
    """
    General AI conversation.
    
    Provides general-purpose AI chat functionality for learning assistance.
    """
    try:
        service = PromptPilotFeatureService(db)
        result = await service.general_chat(
            user_id=request.user_id,
            user_message=request.user_message,
            context=request.context,
            user_role=request.user_role
        )
        return GeneralChatResponse(**result)
    except Exception as e:
        logger.error(f"General chat failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI对话失败: {e}"
        )


# ==================== Batch Recommendation Endpoint ====================

class BatchRecommendationItem(BaseModel):
    """Single course recommendation item."""
    course_id: int
    course_title: str
    recommendation_reason: str
    context_data: str


class BatchRecommendationRequest(BaseModel):
    """Request for batch recommendation reasons."""
    user_id: int
    user_name: str
    courses: List[BatchRecommendationItem]
    user_role: Optional[str] = Field(default="student")


class BatchRecommendationResponseItem(BaseModel):
    """Single recommendation response item."""
    course_id: int
    priority: str
    reason_text: str


class BatchRecommendationResponse(BaseModel):
    """Response for batch recommendation."""
    success: bool
    recommendations: List[BatchRecommendationResponseItem]
    error: Optional[str] = None


@router.post("/recommendation/batch", response_model=BatchRecommendationResponse, dependencies=[Depends(require_ai_enabled)])
async def generate_batch_recommendations(
    request: BatchRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Generate recommendation reasons for multiple courses at once.
    
    This is the main endpoint for the personalization engine to get
    AI-generated recommendation reasons for the dashboard.
    """
    try:
        service = PromptPilotFeatureService(db)
        recommendations = []
        
        for course in request.courses:
            result = await service.generate_recommendation_reason(
                user_id=request.user_id,
                user_name=request.user_name,
                course_title=course.course_title,
                recommendation_reason=course.recommendation_reason,
                context_data=course.context_data,
                user_role=request.user_role
            )
            
            # Determine priority based on reason type
            priority_map = {
                "DEADLINE": "high",
                "SKILL_GAP": "high",
                "MANDATORY": "medium",
                "OPTIONAL_PATH": "low"
            }
            priority = priority_map.get(course.recommendation_reason, "medium")
            
            recommendations.append(BatchRecommendationResponseItem(
                course_id=course.course_id,
                priority=priority,
                reason_text=result.get("reason_text", "")
            ))
        
        return BatchRecommendationResponse(
            success=True,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Batch recommendation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量生成推荐理由失败: {e}"
        )

