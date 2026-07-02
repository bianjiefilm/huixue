"""
兼容性路由 - 为前端提供简化的API路径
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.core.database import get_db
from app.core.security import get_current_user
from app.models import models
from app.models.organization import College, Major, Grade, Class, Student
import app.schemas.schemas as schemas
import app.crud.organization_crud as organization_crud
from fastapi.responses import JSONResponse

router = APIRouter()

# 组织架构树 - 简化路径
@router.get("/organizations/tree")
async def get_organization_tree_compat(
    school_id: int = Query(1, description="学校ID，默认为1"),
    db: Session = Depends(get_db)
):
    """获取组织架构树（兼容路径）"""
    try:
        tree = organization_crud.get_organization_tree(db, school_id)
        return tree
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 部门树列表 - 兼容前端API
@router.get("/classes/departlists")
async def get_department_tree_compat(
    db: Session = Depends(get_db)
):
    """获取部门树列表（兼容前端API路径）"""
    try:
        # 使用Organization表构建组织架构树
        tree = []
        
        # 获取所有顶级组织（parent_id为空的）
        top_orgs = db.query(models.Organization).filter(
            models.Organization.parent_id == None
        ).all()
        
        # 如果没有组织数据，返回默认结构
        if not top_orgs:
            # 返回一个默认的学院结构便于测试
            return [
                {
                    "id": "dept-default",
                    "name": "计算机学院",
                    "code": "CS",
                    "org_type": "college",
                    "level": 1,
                    "children": [
                        {
                            "id": "class-default",
                            "name": "计算机2024级1班",
                            "code": "CS2024-1",
                            "org_type": "class",
                            "level": 2,
                            "children": []
                        }
                    ]
                }
            ]
        
        def build_tree(parent_id=None, level=1):
            """递归构建组织树"""
            if parent_id is None:
                orgs = db.query(models.Organization).filter(
                    models.Organization.parent_id == None
                ).all()
            else:
                orgs = db.query(models.Organization).filter(
                    models.Organization.parent_id == parent_id
                ).all()
            
            result = []
            for org in orgs:
                node = {
                    "id": f"org-{org.id}",
                    "name": org.name,
                    "code": org.code or "",
                    "org_type": org.org_type.value if org.org_type else "department",
                    "level": level,
                    "children": build_tree(org.id, level + 1)
                }
                result.append(node)
            return result
        
        tree = build_tree()
        print(f"[departlists] 返回 {len(tree)} 个组织数据")
        return tree
        
    except Exception as e:
        import traceback
        error_msg = f"获取部门树失败: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return JSONResponse(content={"code": "500", "message": str(e)}, status_code=500)

# 班级学生列表 - 兼容前端API
@router.get("/classes/classtulists")
async def get_class_students_compat(
    class_id: str = Query(..., description="班级ID，支持格式: 数字ID或class-xxx格式"),
    db: Session = Depends(get_db)
):
    """获取班级学生列表（兼容前端API路径）"""
    try:
        print(f"[classtulists] 原始class_id: {class_id}")
        
        # 处理class_id：可能是字符串格式如 "class-default", "class-15", "org-4" 或纯数字
        actual_class_id = None
        if class_id == "class-default":
            # 默认班级，返回所有学生（用于测试）
            students = db.query(Student).filter(Student.school_id == 1).limit(50).all()
        elif isinstance(class_id, str) and class_id.startswith("class-"):
            # 提取数字ID
            try:
                actual_class_id = int(class_id.replace("class-", ""))
            except ValueError:
                actual_class_id = None
        elif isinstance(class_id, str) and class_id.startswith("org-"):
            # 处理org-前缀格式（组织树节点ID）
            try:
                actual_class_id = int(class_id.replace("org-", ""))
            except ValueError:
                actual_class_id = None
        else:
            try:
                actual_class_id = int(class_id)
            except ValueError:
                actual_class_id = None
        
        if actual_class_id is not None:
            students = db.query(Student).filter(Student.class_id == actual_class_id).all()
        elif class_id != "class-default":
            students = []
        
        print(f"[classtulists] 查询到 {len(students)} 个学生")

        # 格式化返回数据
        student_list = []
        for student in students:
            student_data = {
                "id": student.id,
                "realname": student.name,
                "xuehao": student.student_number,
                "class_name": "",  # Student模型没有class_name字段
                "student_id": str(student.id)  # 添加student_id字段，前端需要
            }
            student_list.append(student_data)

        return JSONResponse(content=student_list, status_code=200)
    except Exception as e:
        import traceback
        error_msg = f"获取班级学生失败: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return JSONResponse(content={"code": "500", "message": str(e)}, status_code=500)

# 学生列表 - 简化路径
@router.get("/students")
async def get_students_compat(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    school_id: int = Query(1, description="学校ID，默认为1"),
    db: Session = Depends(get_db)
):
    """获取学生列表（兼容路径）"""
    try:
        # 直接使用 organization.py 中的 search_students 逻辑
        query = db.query(Student).filter(Student.school_id == school_id)
        
        if keyword and keyword.strip():
            query = query.filter(
                db.or_(
                    Student.name.ilike(f"%{keyword}%"),
                    Student.student_number.ilike(f"%{keyword}%")
                )
            )
        
        # 分页
        total = query.count()
        students = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 构建响应
        items = []
        for student in students:
            items.append({
                "id": student.id,
                "student_number": student.student_number,
                "name": student.name,
                "gender": student.gender,
                "phone": student.phone,
                "email": student.email,
                "is_active": student.is_active,
                "created_at": student.created_at.isoformat() if student.created_at else None
            })
        
        return {
            "data": {
                "list": items,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 创建学生 - 简化路径
@router.post("/students")
async def create_student_compat(
    data: dict = Body(...),
    school_id: int = Query(1, description="学校ID，默认为1"),
    db: Session = Depends(get_db)
):
    """创建学生（兼容路径）"""
    try:
        print(f"[创建学生] 接收到的数据: {data}")
        
        # 支持前端发送的不同字段名称
        # studentId -> student_number, organizationId/department_id/department -> class_id
        student_number = data.get("student_number") or data.get("studentId") or data.get("student_id")
        class_id = data.get("class_id") or data.get("organizationId") or data.get("department_id") or data.get("department")
        
        # 处理class_id：可能是字符串或数字，需要提取数字部分
        if class_id:
            if isinstance(class_id, str) and '-' in class_id:
                # 格式如 "class-15"，提取数字部分
                class_id = int(class_id.split('-')[-1])
            elif isinstance(class_id, str):
                class_id = int(class_id)
        
        # 创建学生对象
        student = Student(
            school_id=school_id,
            student_number=student_number,
            name=data.get("name"),
            gender=data.get("gender"),
            phone=data.get("phone"),
            email=data.get("email"),
            class_id=class_id,
            is_active=data.get("is_active", True)
        )
        
        # 添加到数据库
        db.add(student)
        db.commit()
        db.refresh(student)
        
        print(f"[创建学生] 成功创建学生: ID={student.id}, Name={student.name}")
        
        # 返回响应
        return schemas.ApiResponse(
            code="0000",
            message="学生创建成功",
            data={
                "id": student.id,
                "student_number": student.student_number,
                "name": student.name,
                "gender": student.gender,
                "phone": student.phone,
                "email": student.email,
                "class_id": student.class_id,
                "is_active": student.is_active,
                "created_at": student.created_at.isoformat() if student.created_at else None
            }
        )
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"创建学生失败: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=400, detail=str(e))

# 批量获取教师信息 - 简化路径
@router.post("/teachers/batch")
async def batch_get_teachers_compat(
    request: dict = Body(...),
    db: Session = Depends(get_db)
):
    """批量获取教师信息（兼容路径）"""
    ids = request.get("ids", [])
    teachers = db.query(models.User).filter(
        models.User.id.in_(ids)
    ).all()
    
    result = []
    for teacher in teachers:
        result.append({
            "id": str(teacher.id),
            "job_number": teacher.username,
            "name": teacher.full_name or teacher.username,
            "gender": "male",
            "phone": "",
            "email": teacher.email,
            "title": "教师",
            "department": "计算机学院",
            "is_active": teacher.is_active
        })
    
    return {"data": {"list": result}}

# 获取组织列表 - 简化路径
@router.get("/organizations")
async def get_organizations_compat(
    parent_id: Optional[str] = Query(None, description="父级ID"),
    type: Optional[str] = Query(None, description="组织类型"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query("", description="搜索关键词"),
    school_id: int = Query(1, description="学校ID，默认为1"),
    db: Session = Depends(get_db)
):
    """获取组织列表（兼容路径）"""
    # 处理NaN值和字符串转换
    if parent_id is not None and (parent_id == "NaN" or parent_id == "null"):
        parent_id = None
    elif parent_id is not None:
        try:
            parent_id = int(parent_id)
        except ValueError:
            parent_id = None
    
    # 构建查询
    query = db.query(models.Organization).filter(models.Organization.school_id == school_id)
    
    if parent_id is not None:
        query = query.filter(models.Organization.parent_id == parent_id)
    
    if type:
        # 将小写的type转换为大写的枚举值
        type_upper = type.upper()
        query = query.filter(models.Organization.org_type == type_upper)
    
    if keyword:
        query = query.filter(models.Organization.name.ilike(f"%{keyword}%"))
    
    # 分页
    total = query.count()
    organizations = query.offset((page - 1) * page_size).limit(page_size).all()
    
    # 构建响应
    items = []
    for org in organizations:
        items.append({
            "id": org.id,
            "name": org.name,
            "code": org.code,
            "type": org.org_type.value if org.org_type else None,
            "parent_id": org.parent_id,
            "is_active": org.is_active,
            "created_at": org.created_at.isoformat() if org.created_at else None,
            "updated_at": org.updated_at.isoformat() if org.updated_at else None
        })
    
    return {
        "list": items,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }

# 创建组织 - 简化路径
@router.post("/organizations")
async def create_organization_compat(
    data: dict = Body(...),
    school_id: int = Query(1, description="学校ID，默认为1"),
    db: Session = Depends(get_db)
):
    """创建组织（兼容路径）"""
    try:
        # 打印接收到的数据用于调试
        print(f"创建组织接收到的数据: {data}")
        print(f"数据中的键: {list(data.keys())}")
        print(f"type字段的值: '{data.get('type')}'")
        print(f"type字段是否存在: {'type' in data}")
        print(f"data类型: {type(data)}")
        
        # 处理parent_id - 前端可能发送类似 "school-1" 的格式
        # 支持 parentId 和 parent_id 两种字段名
        parent_id = data.get("parent_id") or data.get("parentId")
        if parent_id and isinstance(parent_id, str):
            # 如果是字符串格式如 "school-1", "college-2" 等，提取数字部分
            if "-" in parent_id:
                parent_id = int(parent_id.split("-")[-1])
            elif parent_id.isdigit():
                parent_id = int(parent_id)
            else:
                parent_id = None
        
        # 处理组织类型
        org_type_str = data.get("type", "").upper() if data.get("type") else None
        print(f"原始类型字段: {data.get('type')}, 转换后: {org_type_str}")
        
        if org_type_str:
            try:
                org_type = models.OrganizationTypeEnum[org_type_str]
            except KeyError:
                raise ValueError(f"无效的组织类型: {data.get('type')}, 可用类型: {[e.value for e in models.OrganizationTypeEnum]}")
        else:
            raise ValueError(f"组织类型不能为空，接收到的数据: {data}")
        
        # 创建组织对象
        organization = models.Organization(
            school_id=school_id,
            name=data.get("name"),
            code=data.get("code"),
            org_type=org_type,
            parent_id=parent_id,
            description=data.get("description"),
            is_active=True
        )
        
        # 添加到数据库
        db.add(organization)
        db.commit()
        db.refresh(organization)
        
        # 返回响应
        return {
            "code": "0000",
            "message": "创建成功",
            "data": {
                "id": organization.id,
                "name": organization.name,
                "code": organization.code,
                "type": organization.org_type.value if organization.org_type else None,
                "parent_id": organization.parent_id,
                "description": organization.description,
                "status": organization.is_active,
                "created_at": organization.created_at.isoformat() if organization.created_at else None,
                "updated_at": organization.updated_at.isoformat() if organization.updated_at else None
            }
        }
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"创建组织失败: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # 打印到控制台以便调试
        raise HTTPException(status_code=400, detail=str(e))

# 更新组织 - 简化路径
@router.put("/organizations/{org_id}")
async def update_organization_compat(
    org_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db)
):
    """更新组织（兼容路径）"""
    try:
        # 查找组织
        organization = db.query(models.Organization).filter(
            models.Organization.id == org_id
        ).first()
        
        if not organization:
            raise HTTPException(status_code=404, detail="组织不存在")
        
        # 更新字段
        if "name" in data:
            organization.name = data["name"]
        if "code" in data:
            organization.code = data["code"]
        if "description" in data:
            organization.description = data["description"]
        
        db.commit()
        db.refresh(organization)
        
        # 返回响应
        return {
            "code": "0000",
            "message": "更新成功",
            "data": {
                "id": organization.id,
                "name": organization.name,
                "code": organization.code,
                "type": organization.org_type.value if organization.org_type else None,
                "parent_id": organization.parent_id,
                "description": organization.description,
                "status": organization.is_active,
                "created_at": organization.created_at.isoformat() if organization.created_at else None,
                "updated_at": organization.updated_at.isoformat() if organization.updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"更新组织失败: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=400, detail=str(e))


# 删除组织 - 兼容路径
@router.delete("/organizations/{org_id}")
async def delete_organization_compat(
    org_id: int,
    db: Session = Depends(get_db)
):
    """删除组织（兼容路径）"""
    try:
        # 查找组织
        organization = db.query(models.Organization).filter(
            models.Organization.id == org_id
        ).first()

        if not organization:
            raise HTTPException(status_code=404, detail="组织不存在")

        # 检查是否有子组织
        children = db.query(models.Organization).filter(
            models.Organization.parent_id == org_id
        ).count()

        if children > 0:
            raise HTTPException(
                status_code=400,
                detail=f"无法删除：该组织下有 {children} 个子组织，请先删除子组织"
            )

        # 检查是否有用户关联（简单检查）
        # 可以根据需要添加更多检查

        # 执行删除
        db.delete(organization)
        db.commit()

        return {
            "code": "0000",
            "message": "删除成功",
            "data": None
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_detail = f"删除组织失败: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=400, detail=str(e))


# ========== 实训项目数据集端点 ==========

@router.get("/projects/{project_id}/datasets")
async def get_project_datasets_compat(
    project_id: int,
    db: Session = Depends(get_db)
):
    """
    获取实训项目的数据集列表（旧版兼容接口）

    为了兼容旧前端代码，使用 /projects/{id}/datasets 路径
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # 获取实训信息
        training = db.query(models.Training).filter(models.Training.id == project_id).first()
        if not training:
            return {
                "code": "0000",
                "message": "暂无数据集",
                "data": {"datasets": [], "total": 0}
            }

        # 获取实训关联的数据集
        datasets_from_db = db.query(models.TrainingDataset).filter(
            models.TrainingDataset.training_id == project_id
        ).all()

        if not datasets_from_db:
            return {
                "code": "0000",
                "message": "暂无数据集",
                "data": {"datasets": [], "total": 0}
            }

        # 构建数据集列表
        result_datasets = []
        for ds in datasets_from_db:
            file_path = ds.access_path_in_env or ds.access_path or f"/datasets/{ds.name}"
            result_datasets.append({
                "id": ds.id,
                "name": ds.name,
                "path": file_path,
                "size": ds.file_size or 0,
                "description": ds.description or "",
            })

        return {
            "code": "0000",
            "message": "获取数据集列表成功",
            "data": {
                "training_id": project_id,
                "datasets": result_datasets,
                "total": len(result_datasets)
            }
        }

    except Exception as e:
        logger.error(f"获取数据集列表失败: {str(e)}")
        return {
            "code": "500",
            "message": f"获取数据集列表失败: {str(e)}",
            "data": {"datasets": [], "total": 0}
        }