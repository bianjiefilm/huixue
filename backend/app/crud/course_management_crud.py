"""
课程管理相关的CRUD操作
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple, Dict
import app.models.models as models
import app.schemas.schemas as schemas
from datetime import datetime, timezone
import json

def get_public_courses(
    db: Session,
    course_type: Optional[str] = None,
    category_node: Optional[str] = None,  # 分类树节点ID
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """获取公开发布的课程列表"""
    # 基础查询 - 只查询公开发布的课程
    query = db.query(models.Course)
    
    # 这里需要根据实际的数据库字段来筛选公开发布的课程
    # 由于现有数据库可能没有publish_status字段，我们先用visibility字段
    query = query.filter(models.Course.visibility == models.CourseVisibilityEnum.PUBLIC_PLATFORM)
    
    # 课程类型筛选
    if course_type:
        if course_type == "practice":
            query = query.filter(models.Course.course_type == models.CourseTypeEnum.PRACTICE)
        elif course_type == "training":
            query = query.filter(models.Course.course_type == models.CourseTypeEnum.TRAINING)
        elif course_type == "course_material":
            query = query.filter(models.Course.course_type == models.CourseTypeEnum.COURSE_MATERIAL)
    
    # 分类筛选（根据分类树节点）
    if category_node:
        # 解析分类节点，可能是方向或具体分类
        if category_node.startswith("direction_"):
            direction = category_node.replace("direction_", "")
            query = query.filter(models.Course.direction == direction)
        elif category_node.startswith("category_"):
            category = category_node.replace("category_", "")
            # 这里需要根据实际的categories字段结构来查询
            query = query.filter(models.Course.categories.ilike(f"%{category}%"))
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                models.Course.title.ilike(f"%{keyword}%"),
                models.Course.description.ilike(f"%{keyword}%")
            )
        )
    
    # 按更新时间倒序排列
    query = query.order_by(models.Course.updated_at.desc())
    
    total = query.count()
    courses = query.offset(skip).limit(limit).all()
    
    return courses, total

def get_course_category_tree(db: Session, course_type: Optional[str] = None):
    """获取课程分类树结构"""
    # 根据课程类型获取不同的分类树
    if course_type == "practice":
        # 实践课程：9大方向及分类
        directions = [
            "人工智能", "大数据", "云计算", "物联网", "区块链", 
            "网络安全", "软件工程", "移动开发", "前端开发"
        ]
        tree = []
        for i, direction in enumerate(directions):
            direction_node = {
                "id": f"direction_{direction}",
                "name": direction,
                "type": "direction",
                "children": [],
                "course_count": 0
            }
            tree.append(direction_node)
        
        return tree
    
    elif course_type == "training":
        # 实训课程：行业分类
        industries = [
            "互联网", "金融", "教育", "医疗", "制造业", 
            "零售", "物流", "政府", "其他"
        ]
        tree = []
        for industry in industries:
            tree.append({
                "id": f"industry_{industry}",
                "name": industry,
                "type": "industry",
                "children": [],
                "course_count": 0
            })
        
        return tree
    
    else:
        # 默认返回通用分类树
        return []

def unpublish_course(db: Session, course_id: int, admin_id: int, reason: Optional[str] = None):
    """下架课程"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return {"success": False, "message": "课程不存在"}

    # 检查课程是否已发布
    if course.visibility != models.CourseVisibilityEnum.PUBLIC_PLATFORM:
        return {"success": False, "message": "课程未公开发布"}

    # 检查课程来源，决定下架后的状态
    # 暂时通过判断是否有创建者来区分教师课程和管理员导入课程
    # 教师公开课程下架后转为个人发布，管理员导入课程下架后变为未发布
    course.visibility = models.CourseVisibilityEnum.PRIVATE

    # 记录下架时间
    course.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(course)
        return {"success": True, "message": "下架成功"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"下架失败: {str(e)}"}

def publish_course(db: Session, course_id: int, admin_id: int, reason: Optional[str] = None):
    """发布课程"""
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        return {"success": False, "message": "课程不存在"}

    # 检查课程是否可以发布
    if course.visibility == models.CourseVisibilityEnum.PUBLIC_PLATFORM:
        return {"success": False, "message": "课程已经公开发布"}

    # 发布课程
    course.visibility = models.CourseVisibilityEnum.PUBLIC_PLATFORM
    course.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(course)
        return {"success": True, "message": "发布成功"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"发布失败: {str(e)}"}

def publish_practice_course(db: Session, course_id: int, operator_id: int):
    """发布实践课程"""
    return publish_course(db, course_id, operator_id)

def unpublish_practice_course(db: Session, course_id: int, operator_id: int):
    """下架实践课程"""
    return unpublish_course(db, course_id, operator_id)

def publish_training_course(db: Session, course_id: int, operator_id: int):
    """发布实训课程"""
    return publish_course(db, course_id, operator_id)

def unpublish_training_course(db: Session, course_id: int, operator_id: int):
    """下架实训课程"""
    return unpublish_course(db, course_id, operator_id)

def get_course_management_detail(db: Session, course_id: int):
    """获取课程管理详情"""
    course = db.query(models.Course).options(
        joinedload(models.Course.chapters),
        joinedload(models.Course.resources),
        joinedload(models.Course.assessments)
    ).filter(models.Course.id == course_id).first()
    
    if not course:
        return None
    
    return course

def get_course_management_stats(db: Session):
    """获取课程管理统计信息"""
    # 总课程数
    total_courses = db.query(models.Course).count()
    
    # 各类型课程数
    practice_courses = db.query(models.Course).filter(
        models.Course.course_type == models.CourseTypeEnum.PRACTICE
    ).count()
    
    training_courses = db.query(models.Course).filter(
        models.Course.course_type == models.CourseTypeEnum.TRAINING
    ).count()
    
    course_materials = db.query(models.Course).filter(
        models.Course.course_type == models.CourseTypeEnum.COURSE_MATERIAL
    ).count()
    
    # 已发布课程数
    published_courses = db.query(models.Course).filter(
        models.Course.visibility == models.CourseVisibilityEnum.PUBLIC_PLATFORM
    ).count()
    
    # 待审批申请数
    pending_requests = db.query(models.CourseRequest).filter(
        models.CourseRequest.status == models.CourseRequestStatusEnum.PENDING
    ).count()
    
    # 总申请数
    total_requests = db.query(models.CourseRequest).count()

    return {
        "total_courses": total_courses,
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "published_courses": published_courses,
    }

def _course_type_to_chinese(course_type):
    """课程类型转中文"""
    type_map = {
        models.CourseTypeEnum.PRACTICE: "实践课程",
        models.CourseTypeEnum.TRAINING: "实训课程",
        models.CourseTypeEnum.COURSE_MATERIAL: "课程教材"
    }
    return type_map.get(course_type, "未知")

def _difficulty_to_chinese_mgmt(difficulty):
    """难度转中文"""
    if not difficulty:
        return None
    
    difficulty_map = {
        models.DifficultyEnum.BEGINNER: "初级",
        models.DifficultyEnum.INTERMEDIATE: "中级", 
        models.DifficultyEnum.ADVANCED: "高级"
    }
    return difficulty_map.get(difficulty, "未知")

def _get_course_source(course):
    """获取课程来源"""
    # 这里需要根据实际的数据库字段来判断
    # 暂时返回模拟数据
    return "教师创建"

def _get_course_publish_status(course):
    """获取课程发布状态"""
    if course.visibility == models.CourseVisibilityEnum.PUBLIC_PLATFORM:
        return "已发布"
    elif course.visibility == models.CourseVisibilityEnum.PUBLIC_SELF:
        return "个人发布"
    else:
        return "未发布"

def get_course_type_text(course_type):
    """获取课程类型中文名"""
    type_map = {
        models.CourseTypeEnum.PRACTICE: "实践课程",
        models.CourseTypeEnum.TRAINING: "实训课程",
        models.CourseTypeEnum.COURSE_MATERIAL: "课程教材"
    }
    return type_map.get(course_type, "未知")

def get_request_type_text(request_type):
    """获取申请类型中文名"""
    type_map = {
        models.CourseRequestTypeEnum.PUBLISH: "公开发布",
        models.CourseRequestTypeEnum.UNPUBLISH: "撤销发布"
    }
    return type_map.get(request_type, "未知")

def get_request_status_text(status):
    """获取申请状态中文名"""
    status_map = {
        models.CourseRequestStatusEnum.PENDING: "待审核",
        models.CourseRequestStatusEnum.APPROVED: "已通过",
        models.CourseRequestStatusEnum.REJECTED: "已驳回"
    }
    return status_map.get(status, "未知")

# ==================== 课程申请相关功能 ====================

def get_course_requests(
    db: Session,
    status: Optional[str] = None,
    course_type: Optional[str] = None,
    request_type: Optional[str] = None,
    course_name: Optional[str] = None,
    applicant_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    sort_field: str = "applied_at",
    sort_order: str = "desc"
):
    """获取课程申请列表"""
    query = db.query(models.CourseRequest).options(
        joinedload(models.CourseRequest.course),
        joinedload(models.CourseRequest.applicant),
        joinedload(models.CourseRequest.reviewer)
    )
    
    # 状态筛选
    if status:
        try:
            status_enum = models.CourseRequestStatusEnum(status)
            query = query.filter(models.CourseRequest.status == status_enum)
        except ValueError:
            pass
    
    # 课程类型筛选
    if course_type:
        try:
            course_type_enum = models.CourseTypeEnum(course_type.upper())
            query = query.filter(models.CourseRequest.course_type == course_type_enum)
        except ValueError:
            pass
    
    # 申请类型筛选
    if request_type:
        try:
            request_type_enum = models.CourseRequestTypeEnum(request_type.upper())
            query = query.filter(models.CourseRequest.request_type == request_type_enum)
        except ValueError:
            pass
    
    # 课程名称搜索
    if course_name:
        query = query.join(models.Course)
        query = query.filter(models.Course.title.ilike(f"%{course_name}%"))
    
    # 申请人姓名搜索
    if applicant_name:
        query = query.join(models.User, models.CourseRequest.applicant_id == models.User.id)
        query = query.filter(
            or_(
                models.User.full_name.ilike(f"%{applicant_name}%"),
                models.User.username.ilike(f"%{applicant_name}%")
            )
        )
    
    # 按申请时间倒序排列
    query = query.order_by(models.CourseRequest.applied_at.desc())
    
    total = query.count()
    requests = query.offset(skip).limit(limit).all()
    
    return requests, total

def get_course_request_detail(db: Session, request_id: int):
    """获取课程申请详情"""
    request = db.query(models.CourseRequest).options(
        joinedload(models.CourseRequest.course),
        joinedload(models.CourseRequest.applicant),
        joinedload(models.CourseRequest.reviewer)
    ).filter(models.CourseRequest.id == request_id).first()
    
    return request

def approve_course_request(db: Session, request_id: int, reviewer_id: int, review_comments: Optional[str] = None):
    """审批课程申请（同意）"""
    request = db.query(models.CourseRequest).filter(models.CourseRequest.id == request_id).first()
    if not request:
        return {"success": False, "message": "申请不存在"}
    
    if request.status != models.CourseRequestStatusEnum.PENDING:
        return {"success": False, "message": "申请已处理"}
    
    # 更新申请状态
    request.status = models.CourseRequestStatusEnum.APPROVED
    
    # 根据课程类型获取对应的课程记录
    course = None
    if request.course_type == models.CourseTypeEnum.PRACTICE:
        course = db.query(models.Practice).filter(models.Practice.id == request.course_id).first()
        if course:
            # 如果是发布申请，更新课程状态
            if request.request_type == models.CourseRequestTypeEnum.PUBLISH:
                course.visibility = models.PracticeVisibilityEnum.PUBLIC
                course.publish_status = models.PracticePublishStatusEnum.PUBLISHED
                course.published_at = datetime.now(timezone.utc)
            # 如果是撤销申请，更新课程状态
            elif request.request_type == models.CourseRequestTypeEnum.UNPUBLISH:
                course.visibility = models.PracticeVisibilityEnum.PRIVATE
                course.publish_status = models.PracticePublishStatusEnum.EDITING
            course.updated_at = datetime.now(timezone.utc)
    elif request.course_type == models.CourseTypeEnum.TRAINING:
        course = db.query(models.Training).filter(models.Training.id == request.course_id).first()
        if course:
            # 如果是发布申请，更新课程状态
            if request.request_type == models.CourseRequestTypeEnum.PUBLISH:
                course.visibility = models.TrainingVisibilityEnum.PUBLIC
                course.publish_status = models.TrainingPublishStatusEnum.PUBLISHED
                course.published_at = datetime.now(timezone.utc)
            # 如果是撤销申请，更新课程状态
            elif request.request_type == models.CourseRequestTypeEnum.UNPUBLISH:
                course.visibility = models.TrainingVisibilityEnum.PRIVATE
                course.publish_status = models.TrainingPublishStatusEnum.EDITING
            course.updated_at = datetime.now(timezone.utc)
    
    # 记录审批信息
    request.reviewer_id = reviewer_id
    request.review_comments = review_comments
    request.reviewed_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
        db.refresh(request)
        return {"success": True, "message": "申请已同意"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"审批失败: {str(e)}"}


def reject_course_request(db: Session, request_id: int, reviewer_id: int, review_comments: Optional[str] = None):
    """审批课程申请（驳回）"""
    request = db.query(models.CourseRequest).filter(models.CourseRequest.id == request_id).first()
    if not request:
        return {"success": False, "message": "申请不存在"}
    
    if request.status != models.CourseRequestStatusEnum.PENDING:
        return {"success": False, "message": "申请已处理"}
    
    # 更新申请状态
    request.status = models.CourseRequestStatusEnum.REJECTED
    
    # 记录审批信息
    request.reviewer_id = reviewer_id
    request.review_comments = review_comments
    request.reviewed_at = datetime.now(timezone.utc)
    
    try:
        db.commit()
        db.refresh(request)
        return {"success": True, "message": "申请已驳回"}
    except Exception as e:
        db.rollback()
        return {"success": False, "message": f"审批失败: {str(e)}"}

def _request_type_to_chinese(request_type):
    """申请类型转中文"""
    type_map = {
        models.CourseRequestTypeEnum.PUBLISH: "申请公开发布",
        models.CourseRequestTypeEnum.UNPUBLISH: "申请撤销公开"
    }
    return type_map.get(request_type, "未知")

def _request_status_to_chinese(status):
    """申请状态转中文"""
    status_map = {
        models.CourseRequestStatusEnum.PENDING: "待审批",
        models.CourseRequestStatusEnum.APPROVED: "已同意",
        models.CourseRequestStatusEnum.REJECTED: "已驳回",
        models.CourseRequestStatusEnum.CANCELLED: "已撤销"
    }
    return status_map.get(status, "未知")

# ==================== 实践课程管理相关功能 ====================

def get_practice_course_categories(db: Session):
    """获取实践课程分类列表"""
    # 获取所有实践课程的方向和分类
    practices = db.query(models.Practice).all()
    
    # 构建分类树
    category_tree = {}
    
    for practice in practices:
        direction = practice.direction or "其他"
        if direction not in category_tree:
            category_tree[direction] = {
                "direction": direction,
                "categories": set(),
                "count": 0
            }
        
        category_tree[direction]["count"] += 1
        
        # 解析分类（存储为JSON）
        if practice.categories:
            try:
                categories = json.loads(practice.categories) if isinstance(practice.categories, str) else practice.categories
                for cat in categories:
                    category_tree[direction]["categories"].add(cat)
            except:
                pass
    
    # 转换为CategoryNode格式
    result = []
    for direction, data in category_tree.items():
        # 创建子分类节点
        children = []
        for category in data["categories"]:
            children.append({
                "key": f"category_{category}",
                "title": category,
                "children": None
            })
        
        # 创建方向节点
        result.append({
            "key": f"direction_{direction}",
            "title": f"{direction} ({data['count']})",
            "children": children if children else None
        })
    
    return result

def get_practice_courses(
    db: Session,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    sort_field: str = "updated_at",
    sort_order: str = "desc"
):
    """获取实践课程列表 (admin 视角)

    Z3 P0-8 修: 删除 visibility==PUBLIC_PLATFORM 过滤. 老逻辑只返 1 行 (PUBLIC_PLATFORM
    课程), 把 14 个 PRIVATE 草稿/教师私有全过滤掉, 但 admin 的核心职责正是"管理 + 发布"
    未发布课程, 这条 filter 与 admin 角色定位相悖. 端点已加 require_role("admin") 限制
    调用方, 删除此 filter 不再造成越权.
    """
    # 从 courses 表查询全部 PRACTICE 课程 (含 PRIVATE 草稿, admin 可见)
    query = db.query(models.Course).filter(
        models.Course.course_type == models.CourseTypeEnum.PRACTICE,
    )

    # 分类筛选
    if category:
        # 可以是方向或具体分类
        query = query.filter(
            or_(
                models.Course.direction == category,
                models.Course.categories.ilike(f"%{category}%")
            )
        )

    # 排序
    if sort_field == "updated_at":
        if sort_order == "desc":
            query = query.order_by(models.Course.updated_at.desc())
        else:
            query = query.order_by(models.Course.updated_at.asc())
    elif sort_field == "title":
        if sort_order == "desc":
            query = query.order_by(models.Course.title.desc())
        else:
            query = query.order_by(models.Course.title.asc())

    total = query.count()
    courses = query.offset(skip).limit(limit).all()

    # 转换为practices格式的临时对象
    practices = []
    for course in courses:
        class TempPractice:
            def __init__(self, course):
                self.id = course.id
                self.title = course.title
                self.description = course.description
                self.cover_url = course.cover_url
                self.direction = course.direction
                self.category = course.categories  # 映射到category字段
                self.difficulty = None
                self.task_count = course.practice_task_count or 0
                self.coin = 0  # 默认值
                self.creator_id = None
                self.creator = None
                self.created_at = course.created_at
                self.updated_at = course.updated_at
                self.publish_status = None  # 发布状态
                self.visibility = course.visibility  # 可见性

        practices.append(TempPractice(course))

    return practices, total

def get_practice_course_detail(db: Session, course_id: int):
    """获取实践课程详情"""
    # 首先检查课程是否在courses表中且已发布
    course = db.query(models.Course).filter(
        models.Course.id == course_id,
        models.Course.course_type == models.CourseTypeEnum.PRACTICE,
        models.Course.visibility == models.CourseVisibilityEnum.PUBLIC_PLATFORM
    ).first()

    if not course:
        return None

    # 获取实践课程详情
    practice = db.query(models.Practice).filter(models.Practice.id == course_id).first()

    if practice:
        # 加载关联的创建者信息
        if practice.creator_id:
            practice.creator = db.query(models.User).filter(models.User.id == practice.creator_id).first()
        return practice

    # 如果practices表中没有数据，返回courses表的基本信息
    # 创建一个临时的practice对象
    class TempPractice:
        def __init__(self, course):
            self.id = course.id
            self.title = course.title
            self.description = course.description
            self.intro = course.description
            self.cover_url = course.cover_url
            self.direction = course.direction
            self.category = course.categories
            self.difficulty = None
            self.task_count = course.practice_task_count or 0
            self.coin = 0
            self.creator_id = None
            self.creator = None
            self.visibility = course.visibility
            self.created_at = course.created_at
            self.updated_at = course.updated_at
            self.publish_status = None
            # PracticeCourseDetail需要的额外属性
            self.summary = course.description  # 使用description作为summary
            self.practice_type = None
            self.environment_id = None
            self.storage_limit = None
            self.memory_limit = None
            self.cpu_limit = None

    return TempPractice(course)

def get_training_course_categories(db: Session):
    """获取实训课程分类树"""
    # 获取所有已发布的实训并提取其行业和类型
    trainings = db.query(models.Training).filter(
        models.Training.visibility == models.TrainingVisibilityEnum.PUBLIC,
        models.Training.publish_status == models.TrainingPublishStatusEnum.PUBLISHED
    ).all()

    # 构建分类树结构
    result = []
    industry_map = {}

    for training in trainings:
        industry = training.industry or "未分类"
        if industry not in industry_map:
            industry_map[industry] = {
                "key": industry,
                "title": industry,
                "children": []
            }

        # 添加实训类型作为子分类（如果有的话）
        if training.training_type:
            # 处理枚举或字符串类型
            type_value = training.training_type.value if hasattr(training.training_type, 'value') else str(training.training_type)
            type_exists = any(child["key"] == type_value for child in industry_map[industry]["children"])
            if not type_exists:
                industry_map[industry]["children"].append({
                    "key": type_value,
                    "title": type_value,
                    "children": None
                })

    # 转换为列表格式
    for industry, data in industry_map.items():
        result.append({
            "key": data["key"],
            "title": data["title"],
            "children": data["children"] if data["children"] else None
        })

    return result

def get_training_courses(
    db: Session,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    sort_field: str = "updated_at",
    sort_order: str = "desc"
):
    """获取实训课程列表"""
    from sqlalchemy.orm import joinedload

    # 直接从trainings表查询已发布的实训课程
    query = db.query(models.Training).options(
        joinedload(models.Training.creator)
    ).filter(
        models.Training.visibility == models.TrainingVisibilityEnum.PUBLIC,
        models.Training.publish_status == models.TrainingPublishStatusEnum.PUBLISHED
    )

    # 分类筛选
    if category:
        # 可以是行业或具体类型
        query = query.filter(
            or_(
                models.Training.industry == category,
                models.Training.training_type == category
            )
        )

    # 排序
    if sort_field == "updated_at":
        if sort_order == "desc":
            query = query.order_by(models.Training.updated_at.desc())
        else:
            query = query.order_by(models.Training.updated_at.asc())
    elif sort_field == "title":
        if sort_order == "desc":
            query = query.order_by(models.Training.title.desc())
        else:
            query = query.order_by(models.Training.title.asc())

    total = query.count()
    trainings = query.offset(skip).limit(limit).all()

    return trainings, total

def get_training_course_detail(db: Session, course_id: int):
    """获取实训课程详情"""
    from sqlalchemy.orm import joinedload

    # 直接从trainings表查询
    training = db.query(models.Training).options(
        joinedload(models.Training.creator)
    ).filter(
        models.Training.id == course_id,
        models.Training.visibility == models.TrainingVisibilityEnum.PUBLIC,
        models.Training.publish_status == models.TrainingPublishStatusEnum.PUBLISHED
    ).first()

    return training 