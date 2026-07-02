from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import AgentPilotClient, AgentPilotNotConfigured

router = APIRouter(prefix="/agentpilot", tags=["AgentPilot"])


class TaskRequest(BaseModel):
    name: str
    prompt: Any
    task_type: str = "DEFAULT"
    model_name: str = "doubao-seed-1.6-250615"
    criteria: Optional[str] = None
    variable_types: Optional[Dict[str, str]] = None


class TaskResponse(BaseModel):
    task_id: str
    version: str
    variable_names: List[str] = []
    model_name: str


class RenderRequest(BaseModel):
    task_id: str
    version: str
    variables: Dict[str, Any]


class RenderResponse(BaseModel):
    messages: List[Dict[str, Any]]


class FeedbackRequest(BaseModel):
    task_id: str
    version: str
    run_id: str
    feedback: Dict[str, Any]


class OptimizeRequest(BaseModel):
    task_id: str
    version: str


class OptimizeResponse(BaseModel):
    state: str
    optimized_version: Optional[str] = None
    opt_prompt: Optional[str] = None
    base_prompt: Optional[str] = None
    opt_metric: Optional[str] = None
    base_metric: Optional[str] = None
    opt_avg_score: Optional[float] = None
    base_avg_score: Optional[float] = None
    error: Optional[str] = None


class EvaluateRequest(BaseModel):
    example: Dict[str, Any]
    metric: Dict[str, Any]


class CriteriaRequest(BaseModel):
    examples: List[Dict[str, Any]]


def get_client() -> AgentPilotClient:
    try:
        return AgentPilotClient()
    except AgentPilotNotConfigured as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.get("/status")
def agentpilot_status():
    return {
        "enabled": settings.agentpilot_enabled,
        "workspace_id": settings.AGENTPILOT_WORKSPACE_ID,
        "has_ark": bool(settings.ARK_API_KEY),
    }


@router.post("/tasks", response_model=TaskResponse)
def create_task(payload: TaskRequest, client: AgentPilotClient = Depends(get_client)):
    version = client.create_task(
        name=payload.name,
        prompt=payload.prompt,
        task_type=payload.task_type,
        model_name=payload.model_name,
        criteria=payload.criteria,
        variable_types=payload.variable_types,
    )
    return TaskResponse(
        task_id=version.task_id,
        version=version.version,
        variable_names=version.variable_names,
        model_name=version.model_name,
    )


@router.post("/render", response_model=RenderResponse)
def render_inputs(payload: RenderRequest, client: AgentPilotClient = Depends(get_client)):
    data = client.render_input(payload.task_id, payload.version, payload.variables)
    return RenderResponse(messages=data.get("messages", []))


@router.post("/feedback")
def track_feedback(payload: FeedbackRequest, client: AgentPilotClient = Depends(get_client)):
    client.track_feedback(payload.task_id, payload.version, payload.run_id, payload.feedback)
    return {"status": "success"}


@router.post("/optimize", response_model=OptimizeResponse)
def optimize_prompt(payload: OptimizeRequest, client: AgentPilotClient = Depends(get_client)):
    result = client.optimize_prompt(payload.task_id, payload.version)
    return OptimizeResponse(**result)


@router.post("/evaluate")
def evaluate_example(payload: EvaluateRequest, client: AgentPilotClient = Depends(get_client)):
    result = client.evaluate_example(payload.example, payload.metric)
    return {
        "score": getattr(result, "score", None),
        "analysis": getattr(result, "analysis", None),
        "confidence": getattr(result, "confidence", None),
        "reference": getattr(result, "reference", None),
    }


@router.post("/criteria")
def generate_criteria(payload: CriteriaRequest, client: AgentPilotClient = Depends(get_client)):
    result = client.generate_criteria(payload.examples)
    return {"criteria": result}
