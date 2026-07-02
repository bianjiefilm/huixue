from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, asc, func, case
from datetime import datetime, timezone
import json

from app.models import models
from app.schemas import course_management as schemas


class CourseManagementCRUD:
    """课程管理CRUD操作类"""
    
    # ==================== 实践课程管理 ====================
    
    def get_practice_course_categories(self, db: Session) -> List[Dict[str, Any]]:
        """获取实践课程分类树"""
        # 这里定义9大方向及其分类
        practice_categories = [
            {
                "key": "artificial_intelligence",
                "title": "人工智能",
                "children": [
                    {"key": "machine_learning", "title": "机器学习"},
                    {"key": "deep_learning", "title": "深度学习"},
                    {"key": "computer_vision", "title": "计算机视觉"},
                    {"key": "natural_language_processing", "title": "自然语言处理"}
                ]
            },
            {
                "key": "data_science",
                "title": "数据科学",
                "children": [
                    {"key": "data_analysis", "title": "数据分析"},
                    {"key": "data_mining", "title": "数据挖掘"},
                    {"key": "big_data", "title": "大数据"},
                    {"key": "statistics", "title": "统计学"}
                ]
            },
            {
                "key": "web_development",
                "title": "Web开发",
                "children": [
                    {"key": "frontend", "title": "前端开发"},
                    {"key": "backend", "title": "后端开发"},
                    {"key": "fullstack", "title": "全栈开发"},
                    {"key": "web_frameworks", "title": "Web框架"}
                ]
            },
            {
                "key": "mobile_development",
                "title": "移动开发",
                "children": [
                    {"key": "android", "title": "Android开发"},
                    {"key": "ios", "title": "iOS开发"},
                    {"key": "cross_platform", "title": "跨平台开发"},
                    {"key": "mobile_ui", "title": "移动端UI"}
                ]
            },
            {
                "key": "database",
                "title": "数据库",
                "children": [
                    {"key": "sql", "title": "关系型数据库"},
                    {"key": "nosql", "title": "非关系型数据库"},
                    {"key": "database_design", "title": "数据库设计"},
                    {"key": "database_optimization", "title": "数据库优化"}
                ]
            },
            {
                "key": "software_engineering",
                "title": "软件工程",
                "children": [
                    {"key": "software_design", "title": "软件设计"},
                    {"key": "testing", "title": "软件测试"},
                    {"key": "devops", "title": "DevOps"},
                    {"key": "project_management", "title": "项目管理"}
                ]
            },
            {
                "key": "cybersecurity",
                "title": "网络安全",
                "children": [
                    {"key": "network_security", "title": "网络安全"},
                    {"key": "web_security", "title": "Web安全"},
                    {"key": "penetration_testing", "title": "渗透测试"},
                    {"key": "security_analysis", "title": "安全分析"}
                ]
            },
            {
                "key": "cloud_computing",
                "title": "云计算",
                "children": [
                    {"key": "cloud_platforms", "title": "云平台"},
                    {"key": "containerization", "title": "容器化"},
                    {"key": "microservices", "title": "微服务"},
                    {"key": "serverless", "title": "无服务器"}
                ]
            },
            {
                "key": "algorithms",
                "title": "算法与数据结构",
                "children": [
                    {"key": "basic_algorithms", "title": "基础算法"},
                    {"key": "data_structures", "title": "数据结构"},
                    {"key": "advanced_algorithms", "title": "高级算法"},
                    {"key": "competitive_programming", "title": "竞赛编程"}
                ]
            }
        ]
        return practice_categories
    
    def get_practice_courses(
        self, 
        db: Session, 
        category: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100,
        sort_field: str = "updated_at",
        sort_order: str = "desc"
    ) -> Tuple[List[models.Practice], int]:
        """获取公开发布的实践课程列表"""
        query = db.query(models.Practice).options(
            joinedload(models.Practice.creator)
        ).filter(
            models.Practice.visibility == models.PracticeVisibilityEnum.PUBLIC,
            models.Practice.publish_status == models.PracticePublishStatusEnum.PUBLISHED
        )
        
        # 分类筛选
        if category and category != "root":
            query = query.filter(models.Practice.direction == category)
        
        # 排序
        if sort_field == "title":
            if sort_order == "asc":
                query = query.order_by(asc(models.Practice.title))
            else:
                query = query.order_by(desc(models.Practice.title))
        elif sort_field == "created_at":
            if sort_order == "asc":
                query = query.order_by(asc(models.Practice.created_at))
            else:
                query = query.order_by(desc(models.Practice.created_at))
        else:  # updated_at
            if sort_order == "asc":
                query = query.order_by(asc(models.Practice.updated_at))
            else:
                query = query.order_by(desc(models.Practice.updated_at))
        
        total = query.count()
        practices = query.offset(skip).limit(limit).all()
        
        return practices, total
    
    def get_practice_course_detail(self, db: Session, course_id: int) -> Optional[models.Practice]:
        """获取实践课程详情"""
        return db.query(models.Practice).options(
            joinedload(models.Practice.creator),
            joinedload(models.Practice.tasks)
        ).filter(
            models.Practice.id == course_id,
            models.Practice.visibility == models.PracticeVisibilityEnum.PUBLIC,
            models.Practice.publish_status == models.PracticePublishStatusEnum.PUBLISHED
        ).first()
    
    def unpublish_practice_course(
        self, 
        db: Session, 
        course_id: int, 
        operator_id: int
    ) -> Dict[str, Any]:
        """下架实践课程"""
        practice = db.query(models.Practice).filter(models.Practice.id == course_id).first()
        if not practice:
            return {"success": False, "message": "课程不存在"}
        
        if practice.visibility != models.PracticeVisibilityEnum.PUBLIC:
            return {"success": False, "message": "课程未公开发布"}
        
        # 检查课程来源
        if practice.creator_id:
            # 教师创建的课程，下架后转为个人发布
            practice.visibility = models.PracticeVisibilityEnum.PRIVATE
        else:
            # 管理员导入的课程，下架后状态变为未发布
            practice.publish_status = models.PracticePublishStatusEnum.EDITING
        
        practice.updated_at = datetime.now(timezone.utc)
        
        try:
            db.commit()
            return {"success": True, "message": "课程下架成功"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"下架失败: {str(e)}"}
    
    def publish_practice_course(
        self, 
        db: Session, 
        course_id: int, 
        operator_id: int
    ) -> Dict[str, Any]:
        """发布实践课程（仅限管理员导入的课程）"""
        practice = db.query(models.Practice).filter(models.Practice.id == course_id).first()
        if not practice:
            return {"success": False, "message": "课程不存在"}
        
        if practice.creator_id:
            return {"success": False, "message": "教师创建的课程需要通过审批流程发布"}
        
        practice.visibility = models.PracticeVisibilityEnum.PUBLIC
        practice.publish_status = models.PracticePublishStatusEnum.PUBLISHED
        practice.published_at = datetime.now(timezone.utc)
        practice.updated_at = datetime.now(timezone.utc)
        
        try:
            db.commit()
            return {"success": True, "message": "课程发布成功"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"发布失败: {str(e)}"}
    
    # ==================== 实训课程管理 ====================
    
    def get_training_course_categories(self, db: Session) -> List[Dict[str, Any]]:
        """获取实训课程行业分类树"""
        training_categories = [
            {
                "key": "finance",
                "title": "金融行业",
                "children": [
                    {"key": "fintech", "title": "金融科技"},
                    {"key": "risk_management", "title": "风险管理"},
                    {"key": "algorithmic_trading", "title": "算法交易"},
                    {"key": "blockchain", "title": "区块链金融"}
                ]
            },
            {
                "key": "healthcare",
                "title": "医疗健康",
                "children": [
                    {"key": "medical_ai", "title": "医疗AI"},
                    {"key": "health_informatics", "title": "健康信息学"},
                    {"key": "telemedicine", "title": "远程医疗"},
                    {"key": "drug_discovery", "title": "药物发现"}
                ]
            },
            {
                "key": "education",
                "title": "教育行业",
                "children": [
                    {"key": "edtech", "title": "教育科技"},
                    {"key": "online_learning", "title": "在线学习"},
                    {"key": "adaptive_learning", "title": "自适应学习"},
                    {"key": "knowledge_management", "title": "知识管理"}
                ]
            },
            {
                "key": "retail",
                "title": "零售电商",
                "children": [
                    {"key": "ecommerce", "title": "电子商务"},
                    {"key": "recommendation_systems", "title": "推荐系统"},
                    {"key": "supply_chain", "title": "供应链管理"},
                    {"key": "customer_analytics", "title": "客户分析"}
                ]
            },
            {
                "key": "manufacturing",
                "title": "制造业",
                "children": [
                    {"key": "industry_4_0", "title": "工业4.0"},
                    {"key": "predictive_maintenance", "title": "预测性维护"},
                    {"key": "quality_control", "title": "质量控制"},
                    {"key": "automation", "title": "自动化"}
                ]
            },
            {
                "key": "transportation",
                "title": "交通运输",
                "children": [
                    {"key": "smart_transportation", "title": "智能交通"},
                    {"key": "autonomous_vehicles", "title": "自动驾驶"},
                    {"key": "logistics_optimization", "title": "物流优化"},
                    {"key": "traffic_management", "title": "交通管理"}
                ]
            },
            {
                "key": "energy",
                "title": "能源行业",
                "children": [
                    {"key": "renewable_energy", "title": "可再生能源"},
                    {"key": "smart_grid", "title": "智能电网"},
                    {"key": "energy_optimization", "title": "能源优化"},
                    {"key": "carbon_management", "title": "碳管理"}
                ]
            },
            {
                "key": "media",
                "title": "媒体娱乐",
                "children": [
                    {"key": "content_creation", "title": "内容创作"},
                    {"key": "digital_marketing", "title": "数字营销"},
                    {"key": "streaming_platforms", "title": "流媒体平台"},
                    {"key": "game_development", "title": "游戏开发"}
                ]
            }
        ]
        return training_categories
    
    def get_training_courses(
        self, 
        db: Session, 
        category: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100,
        sort_field: str = "updated_at",
        sort_order: str = "desc"
    ) -> Tuple[List[models.Training], int]:
        """获取公开发布的实训课程列表"""
        query = db.query(models.Training).options(
            joinedload(models.Training.creator)
        ).filter(
            models.Training.visibility == models.TrainingVisibilityEnum.PUBLIC,
            models.Training.publish_status == models.TrainingPublishStatusEnum.PUBLISHED
        )
        
        # 分类筛选
        if category and category != "root":
            query = query.filter(models.Training.industry == category)
        
        # 排序
        if sort_field == "title":
            if sort_order == "asc":
                query = query.order_by(asc(models.Training.title))
            else:
                query = query.order_by(desc(models.Training.title))
        elif sort_field == "created_at":
            if sort_order == "asc":
                query = query.order_by(asc(models.Training.created_at))
            else:
                query = query.order_by(desc(models.Training.created_at))
        else:  # updated_at
            if sort_order == "asc":
                query = query.order_by(asc(models.Training.updated_at))
            else:
                query = query.order_by(desc(models.Training.updated_at))
        
        total = query.count()
        trainings = query.offset(skip).limit(limit).all()
        
        return trainings, total
    
    def get_training_course_detail(self, db: Session, course_id: int) -> Optional[models.Training]:
        """获取实训课程详情"""
        return db.query(models.Training).options(
            joinedload(models.Training.creator)
        ).filter(
            models.Training.id == course_id,
            models.Training.visibility == models.TrainingVisibilityEnum.PUBLIC,
            models.Training.publish_status == models.TrainingPublishStatusEnum.PUBLISHED
        ).first()
    
    def unpublish_training_course(
        self, 
        db: Session, 
        course_id: int, 
        operator_id: int
    ) -> Dict[str, Any]:
        """下架实训课程"""
        training = db.query(models.Training).filter(models.Training.id == course_id).first()
        if not training:
            return {"success": False, "message": "课程不存在"}
        
        if training.visibility != models.TrainingVisibilityEnum.PUBLIC:
            return {"success": False, "message": "课程未公开发布"}
        
        # 检查课程来源
        if training.creator_id:
            # 教师创建的课程，下架后转为个人发布
            training.visibility = models.TrainingVisibilityEnum.PRIVATE
        else:
            # 管理员导入的课程，下架后状态变为未发布
            training.publish_status = models.TrainingPublishStatusEnum.EDITING
        
        training.updated_at = datetime.now(timezone.utc)
        
        try:
            db.commit()
            return {"success": True, "message": "课程下架成功"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"下架失败: {str(e)}"}
    
    def publish_training_course(
        self, 
        db: Session, 
        course_id: int, 
        operator_id: int
    ) -> Dict[str, Any]:
        """发布实训课程（仅限管理员导入的课程）"""
        training = db.query(models.Training).filter(models.Training.id == course_id).first()
        if not training:
            return {"success": False, "message": "课程不存在"}
        
        if training.creator_id:
            return {"success": False, "message": "教师创建的课程需要通过审批流程发布"}
        
        training.visibility = models.TrainingVisibilityEnum.PUBLIC
        training.publish_status = models.TrainingPublishStatusEnum.PUBLISHED
        training.published_at = datetime.now(timezone.utc)
        training.updated_at = datetime.now(timezone.utc)
        
        try:
            db.commit()
            return {"success": True, "message": "课程发布成功"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"发布失败: {str(e)}"}
    
    # ==================== 课程审批管理 ====================
    
    def get_course_requests(
        self,
        db: Session,
        status: Optional[str] = None,
        course_type: Optional[str] = None,
        course_name: Optional[str] = None,
        applicant_name: Optional[str] = None,
        request_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
        sort_field: str = "applied_at",
        sort_order: str = "desc"
    ) -> Tuple[List[models.CourseRequest], int]:
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
                course_type_enum = models.CourseTypeEnum(course_type)
                query = query.filter(models.CourseRequest.course_type == course_type_enum)
            except ValueError:
                pass
        
        # 申请类型筛选
        if request_type:
            try:
                request_type_enum = models.CourseRequestTypeEnum(request_type)
                query = query.filter(models.CourseRequest.request_type == request_type_enum)
            except ValueError:
                pass
        
        # 课程名称和申请人姓名筛选
        if course_name or applicant_name:
            if course_name and applicant_name:
                # 联合查询课程和用户表
                query = query.join(models.Course).join(models.User, models.CourseRequest.applicant_id == models.User.id)
                query = query.filter(
                    and_(
                        models.Course.title.ilike(f"%{course_name}%"),
                        models.User.full_name.ilike(f"%{applicant_name}%")
                    )
                )
            elif course_name:
                query = query.join(models.Course).filter(models.Course.title.ilike(f"%{course_name}%"))
            elif applicant_name:
                query = query.join(models.User, models.CourseRequest.applicant_id == models.User.id)
                query = query.filter(models.User.full_name.ilike(f"%{applicant_name}%"))
        
        # 时间范围筛选
        if start_date:
            query = query.filter(models.CourseRequest.applied_at >= start_date)
        if end_date:
            query = query.filter(models.CourseRequest.applied_at <= end_date)
        
        # 排序
        if sort_field == "course_name":
            query = query.join(models.Course)
            if sort_order == "asc":
                query = query.order_by(asc(models.Course.title))
            else:
                query = query.order_by(desc(models.Course.title))
        elif sort_field == "applicant_name":
            query = query.join(models.User, models.CourseRequest.applicant_id == models.User.id)
            if sort_order == "asc":
                query = query.order_by(asc(models.User.full_name))
            else:
                query = query.order_by(desc(models.User.full_name))
        elif sort_field == "request_type":
            if sort_order == "asc":
                query = query.order_by(asc(models.CourseRequest.request_type))
            else:
                query = query.order_by(desc(models.CourseRequest.request_type))
        elif sort_field == "status":
            if sort_order == "asc":
                query = query.order_by(asc(models.CourseRequest.status))
            else:
                query = query.order_by(desc(models.CourseRequest.status))
        elif sort_field == "reviewed_at":
            if sort_order == "asc":
                query = query.order_by(asc(models.CourseRequest.reviewed_at))
            else:
                query = query.order_by(desc(models.CourseRequest.reviewed_at))
        else:  # applied_at
            if sort_order == "asc":
                query = query.order_by(asc(models.CourseRequest.applied_at))
            else:
                query = query.order_by(desc(models.CourseRequest.applied_at))
        
        total = query.count()
        requests = query.offset(skip).limit(limit).all()
        
        return requests, total
    
    def get_course_request_detail(self, db: Session, request_id: int) -> Optional[models.CourseRequest]:
        """获取课程申请详情"""
        return db.query(models.CourseRequest).options(
            joinedload(models.CourseRequest.course),
            joinedload(models.CourseRequest.applicant),
            joinedload(models.CourseRequest.reviewer)
        ).filter(models.CourseRequest.id == request_id).first()
    
    def approve_course_request(
        self, 
        db: Session, 
        request_id: int, 
        reviewer_id: int, 
        review_comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """同意课程申请"""
        request = db.query(models.CourseRequest).filter(models.CourseRequest.id == request_id).first()
        if not request:
            return {"success": False, "message": "申请不存在"}
        
        if request.status != models.CourseRequestStatusEnum.PENDING:
            return {"success": False, "message": "申请状态不允许审批"}
        
        # 更新申请状态
        request.status = models.CourseRequestStatusEnum.APPROVED
        request.reviewer_id = reviewer_id
        request.review_comments = review_comments
        request.reviewed_at = datetime.now(timezone.utc)
        
        # 根据申请类型更新课程状态
        try:
            if request.course_type == models.CourseTypeEnum.PRACTICE:
                # 实践课程
                practice = db.query(models.Practice).filter(models.Practice.id == request.course_id).first()
                if practice:
                    if request.request_type == models.CourseRequestTypeEnum.PUBLISH:
                        practice.visibility = models.PracticeVisibilityEnum.PUBLIC
                        practice.publish_status = models.PracticePublishStatusEnum.PUBLISHED
                        practice.published_at = datetime.now(timezone.utc)
                    elif request.request_type == models.CourseRequestTypeEnum.UNPUBLISH:
                        practice.visibility = models.PracticeVisibilityEnum.PRIVATE
            elif request.course_type == models.CourseTypeEnum.TRAINING:
                # 实训课程
                training = db.query(models.Training).filter(models.Training.id == request.course_id).first()
                if training:
                    if request.request_type == models.CourseRequestTypeEnum.PUBLISH:
                        training.visibility = models.TrainingVisibilityEnum.PUBLIC
                        training.publish_status = models.TrainingPublishStatusEnum.PUBLISHED
                        training.published_at = datetime.now(timezone.utc)
                    elif request.request_type == models.CourseRequestTypeEnum.UNPUBLISH:
                        training.visibility = models.TrainingVisibilityEnum.PRIVATE
            
            db.commit()
            return {"success": True, "message": "审批同意成功"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"审批失败: {str(e)}"}
    
    def reject_course_request(
        self, 
        db: Session, 
        request_id: int, 
        reviewer_id: int, 
        review_comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """驳回课程申请"""
        request = db.query(models.CourseRequest).filter(models.CourseRequest.id == request_id).first()
        if not request:
            return {"success": False, "message": "申请不存在"}
        
        if request.status != models.CourseRequestStatusEnum.PENDING:
            return {"success": False, "message": "申请状态不允许审批"}
        
        request.status = models.CourseRequestStatusEnum.REJECTED
        request.reviewer_id = reviewer_id
        request.review_comments = review_comments
        request.reviewed_at = datetime.now(timezone.utc)
        
        try:
            db.commit()
            return {"success": True, "message": "审批驳回成功"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"驳回失败: {str(e)}"}
    
    def cancel_course_request(
        self, 
        db: Session, 
        request_id: int, 
        applicant_id: int, 
        cancel_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """撤销课程申请"""
        request = db.query(models.CourseRequest).filter(
            models.CourseRequest.id == request_id,
            models.CourseRequest.applicant_id == applicant_id
        ).first()
        
        if not request:
            return {"success": False, "message": "申请不存在或无权限"}
        
        if request.status != models.CourseRequestStatusEnum.PENDING:
            return {"success": False, "message": "只能撤销待审批的申请"}
        
        request.status = models.CourseRequestStatusEnum.CANCELLED
        request.cancelled_reason = cancel_reason
        request.cancelled_at = datetime.now(timezone.utc)
        
        try:
            db.commit()
            return {"success": True, "message": "申请撤销成功"}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"撤销失败: {str(e)}"}
    
    def submit_course_request(
        self,
        db: Session,
        course_id: int,
        course_type: str,
        applicant_id: int,
        request_type: str,
        application_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """提交课程申请"""
        # 检查课程是否存在
        if course_type == "PRACTICE":
            course = db.query(models.Practice).filter(models.Practice.id == course_id).first()
        elif course_type == "TRAINING":
            course = db.query(models.Training).filter(models.Training.id == course_id).first()
        else:
            return {"success": False, "message": "不支持的课程类型"}
        
        if not course:
            return {"success": False, "message": "课程不存在"}
        
        # 检查是否有待审批的申请
        existing_request = db.query(models.CourseRequest).filter(
            models.CourseRequest.course_id == course_id,
            models.CourseRequest.course_type == models.CourseTypeEnum(course_type),
            models.CourseRequest.status == models.CourseRequestStatusEnum.PENDING
        ).first()
        
        if existing_request:
            return {"success": False, "message": "该课程已有待审批的申请"}
        
        # 创建新申请
        course_request = models.CourseRequest(
            course_id=course_id,
            course_type=models.CourseTypeEnum(course_type),
            applicant_id=applicant_id,
            request_type=models.CourseRequestTypeEnum(request_type),
            application_reason=application_reason,
            status=models.CourseRequestStatusEnum.PENDING
        )
        
        try:
            db.add(course_request)
            db.commit()
            return {"success": True, "message": "申请提交成功", "request_id": course_request.id}
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"提交失败: {str(e)}"}
    
    # ==================== 工具方法 ====================
    
    def get_request_type_text(self, request_type: models.CourseRequestTypeEnum) -> str:
        """获取申请类型中文"""
        type_map = {
            models.CourseRequestTypeEnum.PUBLISH: "申请公开发布",
            models.CourseRequestTypeEnum.UNPUBLISH: "申请撤销公开"
        }
        return type_map.get(request_type, "未知")
    
    def get_request_status_text(self, status: models.CourseRequestStatusEnum) -> str:
        """获取申请状态中文"""
        status_map = {
            models.CourseRequestStatusEnum.PENDING: "待审批",
            models.CourseRequestStatusEnum.APPROVED: "已同意",
            models.CourseRequestStatusEnum.REJECTED: "已驳回",
            models.CourseRequestStatusEnum.CANCELLED: "已撤销"
        }
        return status_map.get(status, "未知")
    
    def get_course_type_text(self, course_type: models.CourseTypeEnum) -> str:
        """获取课程类型中文"""
        type_map = {
            models.CourseTypeEnum.PRACTICE: "实践课程",
            models.CourseTypeEnum.TRAINING: "实训课程"
        }
        return type_map.get(course_type, "未知")


# 创建CRUD实例
course_management_crud = CourseManagementCRUD() 