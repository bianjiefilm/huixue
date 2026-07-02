"""
试题库API端点
"""

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import logging
import tempfile
import os
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.identity import resolve_scoped_id
from app.schemas import schemas
from app.crud import crud_question_library

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health", response_model=schemas.ApiResponse)
def health_check():
    """试题库服务健康检查"""
    return schemas.ApiResponse(
        code="0000",
        message="试题库服务正常",
        data={"service": "question_library", "status": "healthy"}
    )


@router.get("/questions/filter-tags", response_model=schemas.ApiResponse)
def get_question_filter_tags(db: Session = Depends(get_db)):
    """
    获取试题筛选标签
    
    返回可用的筛选维度：题型、方向、分类、难度、来源
    """
    try:
        filter_tags = crud_question_library.get_question_filter_tags(db)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取筛选标签成功",
            data=filter_tags
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取筛选标签失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取筛选标签失败: {str(e)}")


@router.get("/questions/template")
def download_template():
    """
    下载试题导入模板
    
    返回Excel格式的试题模板文件，包含4个sheet：单选题、多选题、判断题、简答题
    """
    try:
        template_result = crud_question_library.download_question_template()
        
        if template_result.get("success"):
            # 返回文件下载
            from fastapi.responses import FileResponse
            
            # 判断文件类型
            if template_result["filepath"].endswith('.xlsx'):
                media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            else:
                media_type = "application/json"
            
            return FileResponse(
                path=template_result["filepath"],
                filename=template_result["filename"],
                media_type=media_type
            )
        else:
            # 如果生成Excel失败，返回JSON格式
            template_data = [
                {
                    "content": "Python是一种什么类型的编程语言？",
                    "question_type": "SINGLE_CHOICE",
                    "options": [
                        {"key": "A", "content": "编译型"},
                        {"key": "B", "content": "解释型"},
                        {"key": "C", "content": "汇编型"},
                        {"key": "D", "content": "机器型"}
                    ],
                    "correct_answers": ["B"],
                    "explanation": "Python是一种解释型编程语言。",
                    "difficulty": "BEGINNER",
                    "direction": "Python基础",
                    "category": "编程语言"
                }
            ]
            
            # 保存为临时JSON文件
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
            json.dump(template_data, temp_file, ensure_ascii=False, indent=2)
            temp_file.close()
            
            return FileResponse(
                path=temp_file.name,
                filename="试题导入模板.json",
                media_type="application/json"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载模板失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"下载模板失败: {str(e)}")


@router.get("/questions", response_model=schemas.ApiResponse)
def get_question_library(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    question_type: Optional[str] = Query(None, description="题目类型"),
    direction: Optional[str] = Query(None, description="方向筛选"),
    category: Optional[str] = Query(None, description="分类筛选"),
    difficulty: Optional[str] = Query(None, description="难度筛选"),
    source: Optional[str] = Query(None, description="来源筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取试题库列表

    支持多维度筛选：
    - keyword: 关键词搜索（搜索题干内容）
    - question_type: 题目类型（SINGLE_CHOICE/MULTIPLE_CHOICE/TRUE_FALSE/SHORT_ANSWER）
    - direction: 方向筛选
    - category: 分类筛选
    - difficulty: 难度筛选（BEGINNER/INTERMEDIATE/ADVANCED）
    - source: 来源筛选（个人/平台）
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 处理关键词参数，确保中文字符正确处理
        if keyword:
            try:
                # 尝试解码可能被URL编码的中文字符
                from urllib.parse import unquote
                # 多次解码以处理可能的重复编码
                decoded = keyword
                for _ in range(2):
                    new_decoded = unquote(decoded)
                    if new_decoded == decoded:
                        break
                    decoded = new_decoded
                keyword = decoded
            except HTTPException:
                raise
            except Exception as decode_error:
                # 如果解码失败，使用原始值
                logger.warning(f"关键词参数处理失败: {decode_error}")

        skip = (page - 1) * page_size
        
        questions, total = crud_question_library.get_question_library_list(
            db=db,
            teacher_id=teacher_id,
            keyword=keyword,
            question_type=question_type,
            direction=direction,
            category=category,
            difficulty=difficulty,
            source=source,
            skip=skip,
            limit=page_size
        )
        
        # 获取筛选标签
        filter_tags = crud_question_library.get_question_filter_tags(db)
        
        return schemas.ApiResponse(
            code="0000",
            message="获取试题库列表成功",
            data={
                "list": questions,
                "meta": {
                    "total": total,
                    "page": page,
                    "page_size": page_size
                },
                "filter_tags": filter_tags
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取试题库列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取试题库列表失败: {str(e)}")


@router.post("/questions", response_model=schemas.ApiResponse)
def create_question(
    request: schemas.QuestionCreateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    新建试题

    支持的题目类型：
    - SINGLE_CHOICE: 单选题
    - MULTIPLE_CHOICE: 多选题
    - TRUE_FALSE: 判断题
    - SHORT_ANSWER: 简答题
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        question_data = request.model_dump()
        
        new_question = crud_question_library.create_question(
            db=db,
            question_data=question_data,
            creator_id=teacher_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message="试题创建成功",
            data={
                "question_id": new_question.id,
                "question_type": new_question.question_type.value if new_question.question_type else None
            }
        )
        
    except ValueError as e:
        logger.error(f"试题创建失败，参数错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"试题创建失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"试题创建失败: {str(e)}")


@router.get("/questions/{question_id}", response_model=schemas.ApiResponse)
def get_question_detail(
    question_id: str,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取试题详情"""
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        question_detail = crud_question_library.get_question_detail(
            db=db,
            question_id=question_id,
            teacher_id=teacher_id
        )
        
        if not question_detail:
            raise HTTPException(status_code=404, detail="试题不存在或无权限访问")
        
        return schemas.ApiResponse(
            code="0000",
            message="获取试题详情成功",
            data=question_detail
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取试题详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取试题详情失败: {str(e)}")


@router.put("/questions/{question_id}", response_model=schemas.ApiResponse)
def update_question(
    question_id: str,
    request: schemas.QuestionUpdateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新试题

    注意：
    - 只能编辑个人创建的试题
    - 题目类型不可修改
    - 编辑完成后将修改试卷库中所有用到该题目的试卷
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        update_data = request.model_dump(exclude_unset=True)
        
        updated_question = crud_question_library.update_question(
            db=db,
            question_id=question_id,
            teacher_id=teacher_id,
            update_data=update_data
        )
        
        if not updated_question:
            raise HTTPException(status_code=404, detail="试题不存在或无权限编辑")
        
        return schemas.ApiResponse(
            code="0000",
            message="试题更新成功",
            data={
                "question_id": updated_question.id,
                "updated_at": updated_question.updated_at
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"试题更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"试题更新失败: {str(e)}")


@router.delete("/questions/{question_id}", response_model=schemas.ApiResponse)
def delete_question(
    question_id: str,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    删除试题

    注意：
    - 仅个人试题可删除
    - 试题删除时，不影响已使用该试题的试卷、考试
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        success = crud_question_library.delete_question(
            db=db,
            question_id=question_id,
            teacher_id=teacher_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="试题不存在、无权限删除或已被试卷使用")
        
        return schemas.ApiResponse(
            code="0000",
            message="试题删除成功",
            data={"question_id": question_id}
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"试题删除失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"试题删除失败: {str(e)}")


@router.post("/questions/{question_id}/copy", response_model=schemas.ApiResponse)
def copy_question(
    question_id: str,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    复制试题

    复制后，创建一个新个人试题，内容与原试题内容一致
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        new_question = crud_question_library.copy_question(
            db=db,
            question_id=question_id,
            teacher_id=teacher_id
        )
        
        if not new_question:
            raise HTTPException(status_code=404, detail="原试题不存在")
        
        return schemas.ApiResponse(
            code="0000",
            message="试题复制成功",
            data={
                "original_question_id": question_id,
                "new_question_id": new_question.id
            }
        )
        
    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"试题复制失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"试题复制失败: {str(e)}")


@router.put("/questions/{question_id}", response_model=schemas.ApiResponse)
def update_question_v2(
    question_id: str,
    request: schemas.QuestionUpdateRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    更新试题

    注意：
    - 仅个人试题可编辑
    - 编辑内置试题时，会自动复制为个人试题
    - 编辑试题会同步更新所有使用该试题的试卷（但不影响已发布考试）
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 验证试题是否存在
        question = crud_question_library.get_question_detail(db, question_id, teacher_id)
        if not question:
            raise HTTPException(status_code=404, detail="试题不存在")

        # 检查编辑权限
        if not question.get('can_edit', False):
            raise HTTPException(status_code=403, detail="无权限编辑此试题")

        updated_question = crud_question_library.update_question(
            db=db,
            question_id=question_id,
            question_data=request,
            teacher_id=teacher_id
        )

        if not updated_question:
            raise HTTPException(status_code=400, detail="试题更新失败")

        return schemas.ApiResponse(
            code="0000",
            message="试题更新成功",
            data={
                "question_id": updated_question.id,
                "updated_at": updated_question.updated_at.isoformat() if updated_question.updated_at else None
            }
        )

    except HTTPException:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"试题更新失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"试题更新失败: {str(e)}")


@router.post("/questions/batch-delete", response_model=schemas.ApiResponse)
def batch_delete_questions(
    request: schemas.QuestionBatchDeleteRequest,
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    批量删除试题

    仅个人试题有多选框，选择个人试题后，点击"删除试题"执行批量删除
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        deleted_count, failed_questions = crud_question_library.batch_delete_questions(
            db=db,
            question_ids=request.question_ids,
            teacher_id=teacher_id
        )
        
        return schemas.ApiResponse(
            code="0000",
            message=f"批量删除完成，成功删除{deleted_count}道试题",
            data={
                "deleted_count": deleted_count,
                "failed_count": len(failed_questions),
                "failed_questions": failed_questions
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量删除试题失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量删除试题失败: {str(e)}")


@router.post("/questions/import", response_model=schemas.ApiResponse)
def import_questions(
    file: UploadFile = File(..., description="试题文件"),
    teacher_id: Optional[int] = Query(None, description="教师ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    导入试题

    支持上传模板文件导入试题，文件格式要求：
    - 支持JSON格式
    - 文件内容必须符合系统字段，否则整文件拒绝
    """
    try:
        teacher_id = resolve_scoped_id(current_user, teacher_id, allowed_roles=("teacher",))
        # 根据文件扩展名保存上传的文件
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ['.json', '.xlsx', '.xls']:
            raise HTTPException(status_code=400, detail="只支持JSON或Excel文件格式")
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_ext)
        content = file.file.read()
        temp_file.write(content)
        temp_file.close()
        
        # 导入试题
        import_result = crud_question_library.import_questions_from_file(
            db=db,
            file_path=temp_file.name,
            teacher_id=teacher_id
        )
        
        # 清理临时文件
        os.unlink(temp_file.name)
        
        return schemas.ApiResponse(
            code="0000",
            message=import_result["message"],
            data=import_result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导入试题失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入试题失败: {str(e)}")





 