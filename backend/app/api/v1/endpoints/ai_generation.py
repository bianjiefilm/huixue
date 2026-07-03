"""
AI 实践课生成器 API 端点

对齐《慧学AI升级方案-v2.md》第十六章「接口设计 - 教师端生成流程」。
Phase1 范围：创建任务 -> 解析资料+拆知识点 -> 老师确认知识点 -> 生成关卡草稿。
「保存为实践课程」(commit-to-practice) 需要对接现有 practices 相关表体系，
留作下一步，不在本文件内盲猜实现。

本地开发范围收窄：这些端点只操作 ai_local_db 里的 7 张 AI 专属表(SQLite)，
不接触主体 Postgres DATABASE_URL 下的 100+ 个既有模型。
"""

import os
import tempfile
import logging
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.ai_gate import require_ai_enabled
from app.core.ai_local_db import get_ai_db
from app.models.models import (
    AIGenerationJob,
    AISourceDocument,
    AIDocumentChunk,
    AIKnowledgePoint,
    AIChallengeDraft,
)
from app.services.doc_parser.parser import parse_document, DocParseError
from app.services.ai_orch.orchestrator import (
    extract_knowledge_points,
    generate_challenge_drafts,
    AIOrchestrationError,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai/generation-jobs",
    tags=["AI 实践课生成器"],
    dependencies=[Depends(require_ai_enabled)],
)


# ==================== 响应模型 ====================

class KnowledgePointOut(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    source_refs_json: Any = None
    suggested_difficulty: Optional[str] = None
    suggested_challenge_type: Optional[str] = None
    selected: bool

    class Config:
        from_attributes = True


class GenerationJobOut(BaseModel):
    id: str
    objective: Optional[str] = None
    student_level: Optional[str] = None
    status: str
    model_name: Optional[str] = None
    suggested_challenge_count: Optional[int] = None
    selected_challenge_count: Optional[int] = None

    class Config:
        from_attributes = True


class CreateJobResponse(BaseModel):
    job: GenerationJobOut
    knowledge_points: List[KnowledgePointOut]


class ConfirmKnowledgePointsRequest(BaseModel):
    selected_knowledge_point_ids: List[str]


class ChallengeDraftOut(BaseModel):
    id: str
    title: str
    difficulty: Optional[str] = None
    skill_tags_json: Any = None
    task_markdown: Optional[str] = None
    evaluation_mode: str
    student_files_json: Any = None
    test_cases_json: Any = None
    hidden_test_cases_json: Any = None
    reference_answer: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class GenerateDraftsRequest(BaseModel):
    challenge_count: int = 3


# ==================== ① 创建生成任务：上传资料 -> 解析 -> 拆知识点 ====================

@router.post("", response_model=CreateJobResponse)
async def create_generation_job(
    file: UploadFile = File(..., description="教学资料，PDF/DOCX/PPTX"),
    objective: str = Form(..., description="教学目标"),
    student_level: str = Form(..., description="学生水平"),
    teacher_id: int = Form(1, description="本地开发范围：暂不接入完整用户体系，默认1"),
    db: Session = Depends(get_ai_db),
):
    """
    对齐方案十六章 POST /api/ai/generation-jobs。

    Phase1 简化：同步完成 解析 -> 落库分块 -> 知识点拆解(真实调用LLM)，
    不做异步任务队列。资料量大时会阻塞请求，后续如需异步化再加队列。
    """
    suffix = os.path.splitext(file.filename or "")[1] or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        parsed = parse_document(tmp_path)
    except DocParseError as e:
        raise HTTPException(status_code=422, detail=f"文档解析失败: {e}")
    finally:
        os.unlink(tmp_path)

    source_doc = AISourceDocument(
        teacher_id=teacher_id,
        file_name=file.filename or "unknown",
        file_type=parsed["file_type"],
        file_size=len(content),
        parse_status="parsed",
        page_count=parsed.get("pages"),
    )
    db.add(source_doc)
    db.flush()

    for chunk in parsed["chunks"]:
        db.add(AIDocumentChunk(
            document_id=source_doc.id,
            page_no=chunk.get("page"),
            section_title=chunk.get("heading"),
            chunk_text=chunk.get("text", ""),
            chunk_order=int(chunk["chunk_id"].split("_")[-1]) if "_" in chunk.get("chunk_id", "") else 0,
        ))
    db.commit()

    job = AIGenerationJob(
        teacher_id=teacher_id,
        objective=objective,
        student_level=student_level,
        source_document_ids=[source_doc.id],
        status="parsed",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        knowledge_points = await extract_knowledge_points(
            parsed["chunks"], objective, student_level
        )
    except AIOrchestrationError as e:
        job.status = "failed"
        db.commit()
        raise HTTPException(status_code=502, detail=f"知识点拆解失败: {e}")

    kp_rows = []
    for kp in knowledge_points:
        row = AIKnowledgePoint(
            job_id=job.id,
            title=kp.name,
            summary=kp.summary,
            source_refs_json=[{"chunk_id": kp.source_chunk_id, "location": kp.source_location}],
            suggested_difficulty=kp.suggested_difficulty,
            suggested_challenge_type="auto" if kp.suggested_for_challenge else "manual",
            selected=True,
        )
        db.add(row)
        kp_rows.append(row)

    job.status = "knowledge_extracted"
    db.commit()
    for row in kp_rows:
        db.refresh(row)
    db.refresh(job)

    return CreateJobResponse(job=job, knowledge_points=kp_rows)


# ==================== ② 获取知识点拆解结果 ====================

@router.get("/{job_id}/knowledge-points", response_model=List[KnowledgePointOut])
async def get_knowledge_points(job_id: str, db: Session = Depends(get_ai_db)):
    job = db.query(AIGenerationJob).filter(AIGenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    return db.query(AIKnowledgePoint).filter(AIKnowledgePoint.job_id == job_id).all()


# ==================== ③ 确认/删除知识点 ====================

@router.patch("/{job_id}/knowledge-points", response_model=List[KnowledgePointOut])
async def confirm_knowledge_points(
    job_id: str,
    request: ConfirmKnowledgePointsRequest,
    db: Session = Depends(get_ai_db),
):
    job = db.query(AIGenerationJob).filter(AIGenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="生成任务不存在")

    kps = db.query(AIKnowledgePoint).filter(AIKnowledgePoint.job_id == job_id).all()
    selected_set = set(request.selected_knowledge_point_ids)
    for kp in kps:
        kp.selected = kp.id in selected_set
    job.status = "knowledge_confirmed"
    db.commit()
    return db.query(AIKnowledgePoint).filter(AIKnowledgePoint.job_id == job_id).all()


# ==================== ④ 生成关卡草稿 ====================

@router.post("/{job_id}/challenge-drafts", response_model=List[ChallengeDraftOut])
async def create_challenge_drafts(
    job_id: str,
    request: GenerateDraftsRequest,
    db: Session = Depends(get_ai_db),
):
    job = db.query(AIGenerationJob).filter(AIGenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="生成任务不存在")

    selected_kps = db.query(AIKnowledgePoint).filter(
        AIKnowledgePoint.job_id == job_id, AIKnowledgePoint.selected == True  # noqa: E712
    ).all()
    if not selected_kps:
        raise HTTPException(status_code=400, detail="没有已确认的知识点，无法生成关卡")

    kp_dicts = []
    for kp in selected_kps:
        refs = kp.source_refs_json or [{}]
        kp_dicts.append({
            "name": kp.title,
            "summary": kp.summary or "",
            "source_chunk_id": refs[0].get("chunk_id", ""),
            "source_location": refs[0].get("location", ""),
            "suggested_difficulty": kp.suggested_difficulty or "入门",
            "suggested_for_challenge": True,
            "is_practical_skill": True,
        })

    try:
        drafts = await generate_challenge_drafts(
            kp_dicts, job.student_level or "zero_basis", request.challenge_count
        )
    except AIOrchestrationError as e:
        raise HTTPException(status_code=502, detail=f"关卡生成失败: {e}")

    draft_rows = []
    for draft in drafts:
        row = AIChallengeDraft(
            job_id=job.id,
            knowledge_point_ids_json=draft.source_knowledge_point_ids,
            title=draft.challenge_name,
            difficulty=draft.difficulty,
            skill_tags_json=draft.skill_tags,
            task_markdown=draft.task_instructions,
            evaluation_mode="auto" if draft.evaluation_mode == "自动评测" else "manual",
            student_files_json={"task.py": draft.task_file_template} if draft.task_file_template else {},
            evaluator_files_json={draft.evaluation_script_file: "pending"} if draft.evaluation_script_file else {},
            test_cases_json=draft.visible_test_cases or [],
            hidden_test_cases_json=draft.hidden_test_cases or [],
            reference_answer=draft.reference_solution,
            rubric_json={"submission_requirements": draft.submission_requirements, "grading_rubric": draft.grading_rubric}
            if draft.submission_requirements or draft.grading_rubric else {},
            status="draft",
        )
        db.add(row)
        draft_rows.append(row)

    job.status = "draft_generated"
    job.suggested_challenge_count = len(draft_rows)
    job.selected_challenge_count = len(draft_rows)
    db.commit()
    for row in draft_rows:
        db.refresh(row)

    return draft_rows
