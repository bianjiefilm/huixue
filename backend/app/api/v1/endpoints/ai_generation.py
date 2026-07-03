"""
AI 实践课生成器 API 端点

对齐《慧学AI升级方案-v2.md》第十六章「接口设计 - 教师端生成流程」。
Phase1 范围：创建任务 -> 解析资料+拆知识点 -> 老师确认知识点 -> 生成关卡草稿。
「保存为实践课程」(commit-to-practice) 对齐方案第十一章，见本文件末尾
`commit_job_to_practice` 端点：把 AI 专属 SQLite 里的 job/draft 转成
主体 Postgres 里的 Practice + Task(+ TaskTest) 行。

本地开发范围收窄：前 4 个端点只操作 ai_local_db 里的 7 张 AI 专属表(SQLite)，
不接触主体 Postgres DATABASE_URL 下的 100+ 个既有模型；commit-to-practice
端点是唯一同时接触两个数据库的端点（读 SQLite，写 Postgres）。
"""

import json
import os
import tempfile
import logging
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.ai_gate import require_ai_enabled
from app.core.ai_local_db import get_ai_db
from app.core.database import get_db
from app.core.security import get_current_user
from app.services.ai_quota import get_quota_manager
from app.models.models import (
    AIUsageLog,
    AIGenerationJob,
    AISourceDocument,
    AIDocumentChunk,
    AIKnowledgePoint,
    AIChallengeDraft,
    Task,
)
from app.models import models as db_models
from app.services.doc_parser.parser import parse_document, DocParseError
from app.services.ai_orch.orchestrator import (
    extract_knowledge_points,
    generate_challenge_drafts,
    AIOrchestrationError,
)
from app.services.tutor.schemas import StudentHintRequest, StudentHintResponse
from app.services.tutor.tutor_service import get_hint, TutorServiceError

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


# ==================== ⑤ 获取草稿列表(供审核页刷新/直接访问) ====================

@router.get("/{job_id}/challenge-drafts", response_model=List[ChallengeDraftOut])
async def get_challenge_drafts(job_id: str, db: Session = Depends(get_ai_db)):
    job = db.query(AIGenerationJob).filter(AIGenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="生成任务不存在")
    return db.query(AIChallengeDraft).filter(AIChallengeDraft.job_id == job_id).all()


# ==================== ⑥ 保存为实践课程：POST /{job_id}/commit-to-practice ====================
#
# 对齐《慧学AI升级方案-v2.md》第十一章「保存为实践课程」。
#
# 调研结论摘要（详见任务书，本函数内的关键决策都直接对应调研结论的编号）：
#   - MJ/BD/CV 系列真实评测（v2 fc 协议）只依赖 task_tests 三列
#     (input_data / expected_output / match_rule='function_call')，
#     tasks.evaluation_script_path / evaluation_command / student_task_file_paths
#     三列在全部 141 个已知部署 SQL 里从未被写入，是死列 —— 本函数遵循这个
#     结论，new Task 的这三列全部保持 NULL，不发明本地文件系统路径去填它们。
#   - 唯一的结构性缺口：AIChallengeDraft.test_cases_json / hidden_test_cases_json
#     当前由 LLM 按 {"input":..., "output":...} 自由文本格式生成（见
#     app/services/ai_orch/prompts.py 里 visible_test_cases 的 JSON 示例），
#     不是 task_tests.function_call 协议要求的 {"function","args","kwargs"} /
#     {"result"|"raises"} 结构化键值对。两者之间没有可靠的自动转换规则
#     （字符串 "output": "..." 无法安全反解成 Python 对象）。
#     本函数的处理方式，如实简化，不假装能自动转换：
#       1) 仍然把 test_cases_json / hidden_test_cases_json 原样写入
#          task_tests.input_data/expected_output 两列，但 match_rule 设为
#          'manual_review_pending'（不是 'function_call'），这样 crud.py 的
#          fc/pytest_module/io_based 三路由判定（first_rule == 'function_call'）
#          不会被误触发去跑一个格式不对的自动评测。
#       2) 这类 Task 的 evaluation_mode 在 skills 附带字段里标注，前端/教师
#          需要人工把草稿测试用例改写成 fc 协议格式后，再手动把 match_rule
#          改成 'function_call' 才能启用自动评测（本次任务不做这一层 UI）。
#     这是"简化实现，不是完整方案"，见函数 docstring 与返回体
#     simplifications 字段的明确标注。


class CommitToPracticeRequest(BaseModel):
    practice_name: str
    visibility: str = "private_draft"  # "private_draft" | "published"


class CommitToPracticeResponse(BaseModel):
    job_id: str
    practice_id: int
    task_ids: List[int]
    status: str
    visibility: str
    simplifications: List[str]


_DIFFICULTY_MAP = {
    "零基础": db_models.DifficultyLevelEnum.beginner,
    "入门": db_models.DifficultyLevelEnum.beginner,
    "中等": db_models.DifficultyLevelEnum.intermediate,
    "综合": db_models.DifficultyLevelEnum.advanced,
}

_TASK_DIFFICULTY_MAP = {
    "零基础": "BEGINNER",
    "入门": "BEGINNER",
    "中等": "INTERMEDIATE",
    "综合": "ADVANCED",
}


@router.post("/{job_id}/commit-to-practice", response_model=CommitToPracticeResponse)
async def commit_job_to_practice(
    job_id: str,
    request: CommitToPracticeRequest,
    teacher_id: int = 1,
    ai_db: Session = Depends(get_ai_db),
    db: Session = Depends(get_db),
):
    """
    「保存为实践课程」：把一个 AI 生成任务(job)下已生成的关卡草稿，
    真实落库成主体 Postgres 里的 Practice + Task(+ TaskTest) 行。

    对齐方案第十一章。teacher_id 对齐 practices.py 现有 custom-practices
    端点用 query 参数传创建者 id 的方式（本地开发范围收窄：暂不接入完整
    鉴权体系，默认 1，与 create_generation_job 的 teacher_id 参数风格一致）。

    简化实现声明（如实说明，不是完整方案）：
      1) Task.evaluation_script_path / evaluation_command /
         student_task_file_paths 三列保持 NULL —— 调研结论确认这是
         MJ/BD/CV 真实评测链路里的死列，不发明本地磁盘路径。
      2) task_tests 的 match_rule 写 'manual_review_pending'，不是
         'function_call' —— 因为 AIChallengeDraft.test_cases_json /
         hidden_test_cases_json 目前是 LLM 自由文本 {"input","output"} 格式，
         不是 fc 协议要求的 {"function","args","kwargs"} 结构化格式，
         没有可靠的自动转换规则，强行按 function_call 写入会让学生提交
         100% 走 fc runner 却因格式不对而报错，比明确标注"待人工复核"更差。
      3) student_files_json 里 "task.py" 这个 key 与 fc runner 硬编码的
         student.py 文件名不一致（已知命名地雷，见调研结论残余风险1），
         本函数不做隐式改名，只原样存证，避免制造一个看起来能跑、实际
         跑不通的假自动评测。
    """
    job = ai_db.query(AIGenerationJob).filter(AIGenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="生成任务不存在")

    drafts = ai_db.query(AIChallengeDraft).filter(AIChallengeDraft.job_id == job_id).all()
    if not drafts:
        raise HTTPException(status_code=400, detail="该任务下没有已生成的关卡草稿，无法保存为实践课程")

    if request.visibility not in ("private_draft", "published"):
        raise HTTPException(status_code=422, detail="visibility 只能是 private_draft 或 published")

    creator = db.query(db_models.User).filter(db_models.User.id == teacher_id).first()
    if not creator:
        raise HTTPException(status_code=404, detail=f"创建者 teacher_id={teacher_id} 不存在")

    simplifications = [
        "evaluation_script_path/evaluation_command/student_task_file_paths 保持 NULL"
        "（调研确认这是 v2 fc 协议评测链路的死列，不发明本地磁盘路径）",
        "task_tests.match_rule 写 'manual_review_pending' 而非 'function_call'"
        "（草稿测试用例是 LLM 自由文本 {input,output} 格式，与 fc 协议要求的"
        " {function,args,kwargs}/{result|raises} 结构化格式不兼容，无可靠自动转换规则，"
        "需教师/开发者人工改写后再手动切换 match_rule 才能开启自动评测）",
        "student_files_json 里的文件名（如 task.py）未按 fc runner 硬编码的 student.py 改名，"
        "直接开启自动评测会因模块名不匹配而导入失败，需人工介入改名",
    ]

    # 取任务目标难度：优先第一个 draft 的难度，映射失败退回 beginner。
    first_difficulty = drafts[0].difficulty or "入门"
    practice_difficulty_enum = _DIFFICULTY_MAP.get(first_difficulty, db_models.DifficultyLevelEnum.beginner)

    # 汇总所有 draft 的技能标签，去重后作为 Practice 级别的技能标签落 PracticeSkill。
    all_skill_tags: List[str] = []
    for d in drafts:
        for tag in (d.skill_tags_json or []):
            if tag not in all_skill_tags:
                all_skill_tags.append(tag)

    now = datetime.now(timezone.utc)
    new_practice = db_models.Practice(
        title=request.practice_name,
        description=job.objective or "",
        difficulty=practice_difficulty_enum,
        direction="AI生成",
        category="AI生成实践",
        coin=0,
        task_count=len(drafts),
        practice_type="online_coding",
        creator_id=teacher_id,
        created_at=now,
        updated_at=now,
        visibility=db_models.PracticeVisibilityEnum.PRIVATE,
        publish_status=db_models.PracticePublishStatusEnum.EDITING,
    )
    db.add(new_practice)
    db.flush()  # 拿到 new_practice.id，尚未 commit

    for tag in all_skill_tags:
        db.add(db_models.PracticeSkill(practice_id=new_practice.id, skill_name=tag))

    task_ids: List[int] = []
    for order, draft in enumerate(drafts, start=1):
        task_difficulty = _TASK_DIFFICULTY_MAP.get(draft.difficulty or "入门", "BEGINNER")

        new_task = db_models.Task(
            practice_id=new_practice.id,
            title=draft.title,
            task_type=db_models.TaskTypeEnum.PRACTICE,
            order_in_practice=order,
            coin=10,
            difficulty=task_difficulty,
            skills=json.dumps(draft.skill_tags_json or []),
            handbook_markdown=draft.task_markdown or "",
            answer_content_markdown=draft.reference_answer or "",
            # 简化声明 1）：以下三列刻意保持 NULL，理由见函数 docstring。
            evaluation_script_path=None,
            evaluation_command=None,
            student_task_file_paths=json.dumps(draft.student_files_json) if draft.student_files_json else None,
            env_type="JUPYTER",
            question_data=json.dumps({
                "source": "ai_generation",
                "job_id": job.id,
                "draft_id": draft.id,
                "evaluation_mode": draft.evaluation_mode,
                "student_files_json": draft.student_files_json or {},
                "evaluator_files_json": draft.evaluator_files_json or {},
                "rubric_json": draft.rubric_json or {},
            }, ensure_ascii=False),
        )
        db.add(new_task)
        db.flush()  # 拿到 new_task.id
        task_ids.append(new_task.id)

        # 简化声明 2）：match_rule 写 'manual_review_pending'，不是 'function_call'。
        test_order = 0
        for case in (draft.test_cases_json or []):
            test_order += 1
            db.add(db_models.TaskTest(
                task_id=new_task.id,
                case_id=f"visible_{test_order}",
                input_data=json.dumps(case, ensure_ascii=False),
                expected_output=json.dumps(case.get("output", case), ensure_ascii=False)
                if isinstance(case, dict) else json.dumps(case, ensure_ascii=False),
                is_hidden=False,
                match_rule="manual_review_pending",
                test_order=test_order,
            ))
        for case in (draft.hidden_test_cases_json or []):
            test_order += 1
            db.add(db_models.TaskTest(
                task_id=new_task.id,
                case_id=f"hidden_{test_order}",
                input_data=json.dumps(case, ensure_ascii=False),
                expected_output=json.dumps(case.get("output", case), ensure_ascii=False)
                if isinstance(case, dict) else json.dumps(case, ensure_ascii=False),
                is_hidden=True,
                match_rule="manual_review_pending",
                test_order=test_order,
            ))

        draft.status = "committed"

    final_status = "committed"
    final_visibility = "PRIVATE"

    if request.visibility == "published":
        # 复用 practices.py::publish_practice 的私有可见发布分支字段设置逻辑
        # （不发起真实 HTTP 自调用，直接在同一 session 内设置同样的字段）。
        new_practice.visibility = db_models.PracticeVisibilityEnum.PRIVATE
        new_practice.publish_status = db_models.PracticePublishStatusEnum.PUBLISHED
        new_practice.is_published = True
        new_practice.published_at = now
        final_visibility = "PRIVATE"
    else:
        # private_draft：保持 EDITING + 未发布，只是把草稿真实落成 Practice/Task 行。
        new_practice.visibility = db_models.PracticeVisibilityEnum.PRIVATE
        new_practice.publish_status = db_models.PracticePublishStatusEnum.EDITING
        new_practice.is_published = False

    new_practice.updated_at = now

    job.status = "committed"
    job.practice_id = new_practice.id

    db.commit()
    ai_db.commit()

    return CommitToPracticeResponse(
        job_id=job.id,
        practice_id=new_practice.id,
        task_ids=task_ids,
        status=final_status,
        visibility=final_visibility if request.visibility == "published" else "private_draft",
        simplifications=simplifications,
    )


# ==================== 学生端 AI 闯关辅导助手：POST /api/v1/ai/student-hints ====================
#
# 对齐《慧学AI升级方案-v2.md》第十六章「学生端 AI 辅导」接口设计。
# 独立挂载一个新 APIRouter（前缀 /ai/student-hints），与上面 generation-jobs
# 的 router 分开注册，避免互相影响路径匹配。
#
# 上下文查询策略（对齐调研结论 + 任务书第2条）：
#   1) 优先查 Postgres `tasks` 表（真实已提交关卡）——
#      handbook_markdown -> task_instructions
#      answer_content_markdown -> reference_answer_for_filter_only（只进 output_filter 这一路）
#   2) 查不到（tasks 表为空或该 challenge_id 不存在）则退回 AI 专属 SQLite 的
#      ai_challenge_drafts 表（本地测试闭环用，草稿态数据）——
#      task_markdown -> task_instructions
#      reference_answer -> reference_answer_for_filter_only
#   3) 两边都查不到则 404。
#
# 硬约束（不可破坏，context_builder.py 函数签名本身已强制）：
#   reference_answer 只能流向 tutor_service.get_hint 的
#   reference_answer_for_filter_only 参数（进而只喂给 output_filter），
#   绝不能塞进 challenge_context dict 传给 build_tutor_context。

student_hints_router = APIRouter(
    prefix="/ai/student-hints",
    tags=["AI 闯关辅导助手"],
    dependencies=[Depends(require_ai_enabled)],
)


def _load_task_context_from_postgres(challenge_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """从 Postgres tasks 表按主键查真实已提交关卡。challenge_id 非纯数字直接判未命中。"""
    if not challenge_id.isdigit():
        return None
    task = db.query(Task).filter(Task.id == int(challenge_id), Task.deleted_at.is_(None)).first()
    if not task:
        return None

    skill_tags: List[str] = []
    if task.skills:
        try:
            parsed_skills = task.skills
            import json as _json
            loaded = _json.loads(parsed_skills) if isinstance(parsed_skills, str) else parsed_skills
            if isinstance(loaded, list):
                skill_tags = [str(s) for s in loaded]
        except (ValueError, TypeError):
            skill_tags = []

    return {
        "task_instructions": task.handbook_markdown or "",
        "reference_answer_for_filter_only": task.answer_content_markdown,
        "skill_tags": skill_tags,
    }


def _load_task_context_from_ai_draft(challenge_id: str, ai_db: Session) -> Optional[Dict[str, Any]]:
    """从 AI 专属 SQLite ai_challenge_drafts 表按主键(UUID字符串)查草稿态关卡。"""
    draft = ai_db.query(AIChallengeDraft).filter(AIChallengeDraft.id == challenge_id).first()
    if not draft:
        return None

    return {
        "task_instructions": draft.task_markdown or "",
        "reference_answer_for_filter_only": draft.reference_answer,
        "skill_tags": list(draft.skill_tags_json) if draft.skill_tags_json else [],
    }


@student_hints_router.post("", response_model=StudentHintResponse)
async def create_student_hint(
    request: StudentHintRequest,
    db: Session = Depends(get_db),
    ai_db: Session = Depends(get_ai_db),
    current_user: dict = Depends(get_current_user),
):
    """
    学生端 AI 闯关辅导助手：生成一次提示。

    真实 E2E UAT 发现的 P1 安全缺口修复：本端点之前不要求用户鉴权（理由是
    "与 ai_generation.py 现有端点风格一致"），但这是学生可触达的公开接口，
    实测确认任何人凭 challenge_id 就能无限次触发真实 LLM 调用，无身份约束、
    无服务端配额——教师端生成端点尚可容忍这个风险（本地开发/内部工具属性
    更强），学生端公开接口不行。现在挂真实 get_current_user 鉴权 + 复用
    已有的 AIQuotaManager（backend/app/services/ai_quota.py，student 角色
    月度20次额度）做服务端强制配额，不再只靠前端本地计数（前端"剩余提示
    次数"UI显示的是客户端状态，用户随时可以清空localStorage绕过，必须有
    服务端兜底）。
    """
    user_id = current_user["id"]

    quota_manager = get_quota_manager(db)
    quota_info = quota_manager.check_quota(user_id, "explain")
    if not quota_info.get("allowed"):
        raise HTTPException(
            status_code=429,
            detail=f"本月 AI 辅导次数已用完(已用 {quota_info.get('used_this_month')}/"
                   f"{quota_info.get('monthly_quota')})，将于 "
                   f"{quota_info.get('reset_date')} 重置",
        )

    task_context = _load_task_context_from_postgres(request.challenge_id, db)
    if task_context is None:
        task_context = _load_task_context_from_ai_draft(request.challenge_id, ai_db)
    if task_context is None:
        raise HTTPException(status_code=404, detail="关卡不存在，无法提供 AI 辅导")

    reference_answer_for_filter_only = task_context.pop("reference_answer_for_filter_only", None)

    # challenge_context 只放 build_tutor_context 认识的字段；student_submission /
    # visible_test_cases / failure_count 目前没有真实数据源接入（评测提交记录表
    # 不在本任务写集内），先传空值，不影响 hint_level 1/2 场景（eval_error 由
    # 请求体传入，走的是前端 evaluationState.error_message 真实报错文本）。
    challenge_context: Dict[str, Any] = {
        "task_instructions": task_context["task_instructions"],
        "student_submission": None,
        "visible_test_cases": None,
        "failure_count": 0,
        "skill_tags": task_context["skill_tags"],
    }

    try:
        response = await get_hint(
            request=request,
            challenge_context=challenge_context,
            reference_answer_for_filter_only=reference_answer_for_filter_only,
        )
    except TutorServiceError as e:
        logger.error("student-hints 调用 tutor_service 失败: %s", e)
        db.add(AIUsageLog(
            user_id=user_id,
            user_role=current_user.get("roles", ["student"])[0],
            feature_type="explain",
            error_message=str(e),
        ))
        db.commit()
        raise HTTPException(status_code=502, detail=f"AI 辅导服务调用失败: {e}")

    # 只在真实成功后才写用量记录，让 check_quota 的月度计数真实增长
    # （check_quota 只统计 error_message IS NULL 的行）。
    db.add(AIUsageLog(
        user_id=user_id,
        user_role=current_user.get("roles", ["student"])[0],
        feature_type="explain",
    ))
    db.commit()

    return response
