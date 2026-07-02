"""
Student Dashboard API Endpoints
学生仪表板 API 端点
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.api.deps import get_db
from app.core.security import get_current_user
from app.services.student_dashboard import StudentDashboardService
from app.services.ai_features.feature_service import PromptPilotFeatureService

router = APIRouter()


# ==================== Response Models ====================

class LearningPath(BaseModel):
    id: str
    courseId: str
    classroomCourseId: int
    title: str
    code: str
    coverImage: Optional[str] = None
    progress: int
    priority: str
    daysRemaining: Optional[int] = None
    dueDate: Optional[str] = None
    classroomId: str
    classroomName: str
    isMandatory: bool
    totalTasks: int
    completedTasks: int
    attentionScore: float
    priorityReason: Optional[str] = None

class SkillNode(BaseModel):
    id: str
    name: str
    category: str
    mastery: int
    connections: List[str] = []

class SkillLink(BaseModel):
    source: str
    target: str
    weight: int

class SkillConstellationResponse(BaseModel):
    nodes: List[SkillNode]
    links: List[SkillLink]
    totalSkills: int
    topSkills: List[str]
    aiSummary: Optional[str] = None

class Deadline(BaseModel):
    id: str
    title: str
    dueDate: Optional[str] = None
    daysRemaining: int
    type: str
    courseId: str
    classroomId: str
    isCritical: bool

class Recommendation(BaseModel):
    courseId: str
    title: str
    reason: str
    matchScore: int
    tags: List[str] = []

class PriorityIntelResponse(BaseModel):
    deadlines: List[Deadline]
    recommendations: List[Recommendation]
    criticalCount: int

class DashboardResponse(BaseModel):
    success: bool
    activePaths: List[LearningPath]
    skillConstellation: SkillConstellationResponse
    priorityIntel: PriorityIntelResponse


# ==================== Endpoints ====================

@router.get("/dashboard", response_model=DashboardResponse)
async def get_student_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    获取学生仪表板完整数据
    
    返回：
    - 活跃学习路径（按优先级排序的前3个课程）
    - 技能星座（基于已通过任务的技能聚合）
    - 优先情报（即将到期任务和推荐课程）
    """
    try:
        # current_user 是一个字典: {"user_id": id, "username": name, ...}
        student_id = current_user.get("user_id") or current_user.get("id")
        username = current_user.get("username", "同学")
        service = StudentDashboardService(db)
        
        # 获取活跃学习路径
        active_paths = service.get_active_learning_paths(student_id)
        
        # 获取技能星座
        skill_data = service.get_skill_constellation(student_id)
        
        # 获取优先情报
        priority_intel = service.get_priority_intel(student_id)
        
        # 尝试使用 AI 生成推荐理由
        try:
            ai_service = PromptPilotFeatureService(db)
            
            # 为高优先级课程生成 AI 推荐理由
            for path in active_paths[:2]:
                if path["priority"] in ["deadline", "skill_gap"]:
                    reason_type = "DEADLINE" if path["priority"] == "deadline" else "SKILL_GAP"
                    context = f"还剩{path['daysRemaining']}天" if path.get("daysRemaining") else ""
                    
                    ai_result = await ai_service.generate_recommendation_reason(
                        user_name=username,
                        course_title=path["title"],
                        recommendation_reason=reason_type,
                        context_data=context,
                        user_id=student_id
                    )
                    
                    if ai_result.get("success"):
                        path["priorityReason"] = ai_result.get("reason_text", "")
        except Exception as e:
            # AI 服务不可用时继续使用默认理由
            pass
        
        return {
            "success": True,
            "activePaths": active_paths,
            "skillConstellation": {
                **skill_data,
                "aiSummary": None
            },
            "priorityIntel": priority_intel
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取仪表板数据失败: {str(e)}")


@router.get("/dashboard/learning-paths")
async def get_learning_paths(
    limit: int = 3,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取活跃学习路径"""
    user_id = current_user.get("user_id") or current_user.get("id")
    service = StudentDashboardService(db)
    paths = service.get_active_learning_paths(user_id, limit)
    return {"success": True, "data": paths}


@router.get("/dashboard/skill-constellation")
async def get_skill_constellation(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取技能星座数据"""
    user_id = current_user.get("user_id") or current_user.get("id")
    service = StudentDashboardService(db)
    data = service.get_skill_constellation(user_id)
    return {"success": True, "data": data}


@router.get("/dashboard/priority-intel")
async def get_priority_intel(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取优先情报"""
    user_id = current_user.get("user_id") or current_user.get("id")
    service = StudentDashboardService(db)
    data = service.get_priority_intel(user_id)
    return {"success": True, "data": data}


@router.post("/dashboard/ai-skill-summary")
async def get_ai_skill_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    使用 AI 生成技能图谱评语
    """
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        service = StudentDashboardService(db)
        skill_data = service.get_skill_constellation(user_id)
        
        top_skills = skill_data.get("topSkills", [])
        if not top_skills:
            return {
                "success": True,
                "summary": "开始学习并完成任务，解锁您的技能星座！"
            }
        
        # 使用 AI 生成评语
        ai_service = PromptPilotFeatureService(db)
        
        skills_text = "、".join(top_skills[:5])
        context = f"学生掌握的主要技能：{skills_text}"
        
        result = await ai_service.general_chat(
            user_message=f"请根据学生的技能掌握情况给出一句简短的学习建议（不超过50字）：{context}",
            context="您是慧学的AI学习助手Tempo，帮助学生解答学习问题。请基于提供的文件内容回答问题。如果不知道，请明确说不知道，不要编造信息。",
            user_id=user_id
        )
        
        if result.get("success"):
            return {
                "success": True,
                "summary": result.get("reply", "您的学习进展良好，继续加油！")
            }
        else:
            return {
                "success": True,
                "summary": f"您在{skills_text}方面表现出色，继续保持！"
            }
            
    except Exception as e:
        return {
            "success": False,
            "summary": "暂时无法生成AI评语",
            "error": str(e)
        }


@router.post("/dashboard/ai-recommendation")
async def get_ai_recommendation(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    使用 AI 生成课程推荐
    """
    try:
        user_id = current_user.get("user_id") or current_user.get("id")
        service = StudentDashboardService(db)
        skill_data = service.get_skill_constellation(user_id)
        
        top_skills = skill_data.get("topSkills", [])
        skills_text = "、".join(top_skills) if top_skills else "Python、数据分析"
        
        # 使用 AI 生成推荐
        ai_service = PromptPilotFeatureService(db)
        
        prompt = f"""学生当前已掌握技能：{skills_text}

现有可选拓展课程列表：
1. 人工智能伦理入门 (标签: AI, 伦理)
2. 高级数据可视化 (标签: D3.js, BI)
3. 深度学习实践 (标签: PyTorch, 神经网络)

请从列表中推荐1门最适合该学生的课程，用副驾的口吻给出一句简短的推荐理由。"""
        
        result = await ai_service.general_chat(
            user_message=prompt,
            context="您是慧学的AI学习助手Tempo，帮助学生规划学习路径。",
            user_id=user_id
        )
        
        if result.get("success"):
            return {
                "success": True,
                "recommendation": {
                    "courseId": "rec-ai-1",
                    "title": "人工智能伦理入门",
                    "reason": result.get("reply", "基于您的技能图谱，这门课程是很好的拓展选择"),
                    "matchScore": 85
                }
            }
        else:
            return {
                "success": True,
                "recommendation": {
                    "courseId": "rec-1",
                    "title": "人工智能伦理入门",
                    "reason": "基于您的技能图谱，这门拓展课程与您的学习路径高度匹配",
                    "matchScore": 85
                }
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

