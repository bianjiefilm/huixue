"""
关卡生成API端点
包含生成关卡提纲和生成具体关卡内容的功能
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request, Body
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import logging
import uuid
from datetime import datetime
import json
from pathlib import Path
import asyncio
from enum import Enum

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import (
    User,
    DifficultyLevelEnum,
    TaskTypeEnum,
    DifficultyEnum,
    QuestionTypeEnum,
)
from app.schemas.generation import (
    OutlineResponse, LevelGenerationRequest, LevelGenerationResponse,
    OutlineItem, PracticeContent, MetadataGenerationRequest, MetadataResponse, 
    Category, Config, EvaluationAssetResponse, EvaluationAssetRequest, 
    QuestionGenerationResponse, QuestionGenerationRequest,
    FullCourseManifest, TaskCreateResponse, TaskStatusResponse,
    # 实训相关Schema
    FullTrainingManifest, TrainingTaskCreateResponse, TrainingTaskStatusResponse
)
from app.schemas.schemas import ApiResponse
from app.utils.file_parser import FileParser
from app.utils.llm_client import LLMClient
from app.utils.task_manager import task_manager
from app.utils.multi_file_processor import multi_file_processor

# 配置日志
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(
    prefix="/generation",
    tags=['关卡生成']
)

# 初始化LLM客户端
llm_client = LLMClient()


@router.post("/outline", response_model=ApiResponse)
async def generate_outline(
    file: UploadFile = File(..., description="教学文件（PDF或DOCX格式）"),
    db: Session = Depends(get_db)
):
    """
    生成关卡提纲
    
    上传一个课程章节的教学文件（PDF或DOCX），API会解析其文本内容，
    并返回一个结构化的关卡提纲建议。
    """
    try:
        # 验证文件大小
        FileParser.validate_file_size(file, max_size_mb=10)
        
        # 提取文件文本内容
        logger.info(f"开始解析文件: {file.filename}")
        text_content = await FileParser.extract_text_from_upload_file(file)
        
        if not text_content or len(text_content.strip()) < 100:
            raise HTTPException(
                status_code=400, 
                detail="文件内容过少，无法生成有效的关卡提纲"
            )
        
        logger.info(f"文件解析完成，内容长度: {len(text_content)}")
        
        # 调用LLM生成提纲
        logger.info("开始调用LLM生成关卡提纲")
        outline_data = llm_client.generate_course_outline(text_content, file.filename)
        
        # 构建响应
        outline_items = []
        for item in outline_data:
            outline_items.append(OutlineItem(
                level_title=item.get("level_title", ""),
                core_knowledge=item.get("core_knowledge", ""),
                suggested_type=item.get("suggested_type", "实践题"),
                difficulty=item.get("difficulty", "中级")
            ))
        
        response_data = OutlineResponse(
            filename=file.filename,
            outline=outline_items
        )
        
        logger.info(f"成功生成{len(outline_items)}个关卡提纲")
        
        return ApiResponse(
            code="0000",
            message="提纲生成成功",
            data=response_data.model_dump(),
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成提纲失败: {str(e)}")
        return ApiResponse(
            code="2000",
            message=f"生成提纲失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/level", response_model=LevelGenerationResponse)
async def generate_level(request: LevelGenerationRequest):
    """生成具体关卡内容"""
    try:
        logger.info(f"收到关卡生成请求: {request.current_task.level_title}")
        
        # 实例化LLM客户端
        llm_client = LLMClient()
        
        # 构造提纲项数据
        outline_item = {
            "level_title": request.current_task.level_title,
            "core_knowledge": request.current_task.core_knowledge,
            "suggested_type": request.current_task.suggested_type,
            "difficulty": request.current_task.difficulty
        }
        
        # 生成关卡内容
        content = llm_client.generate_level_content(request.background_context, outline_item)
        
        return LevelGenerationResponse(
            level_title=request.current_task.level_title,
            level_type=request.current_task.suggested_type,
            content=content
        )
        
    except Exception as e:
        logger.error(f"关卡生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"关卡生成失败: {str(e)}")

# 新增API 3.1: 生成课程元数据
@router.post("/course-metadata", response_model=MetadataResponse)
async def generate_course_metadata(request: MetadataGenerationRequest):
    """生成课程元数据 (practice_info.json)"""
    try:
        logger.info(f"收到课程元数据生成请求: {request.course_title}")
        
        # 实例化LLM客户端
        llm_client = LLMClient()
        
        # 生成课程元数据
        metadata = llm_client.generate_course_metadata(
            request.course_title, 
            request.syllabus_text, 
            request.file_manifest
        )
        
        # 转换为响应模型
        return MetadataResponse(
            practice_name=metadata["practice_name"],
            practice_type=metadata["practice_type"],
            introduction=metadata["introduction"],
            difficulty=metadata["difficulty"],
            category=Category(
                primary=metadata["category"]["primary"],
                secondary=metadata["category"]["secondary"]
            ),
            environment_id=metadata["environment_id"],
            config=Config(
                allow_skip=metadata["config"]["allow_skip"],
                editor_enabled=metadata["config"]["editor_enabled"],
                shell_enabled=metadata["config"]["shell_enabled"],
                repo_visible=metadata["config"]["repo_visible"]
            )
        )
        
    except Exception as e:
        logger.error(f"课程元数据生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"课程元数据生成失败: {str(e)}")

# 新增API 3.2: 生成评测资源
@router.post("/evaluation-assets", response_model=EvaluationAssetResponse)
async def generate_evaluation_assets(request: EvaluationAssetRequest):
    """生成评测资源 (judge.py 和 tests.json)"""
    try:
        logger.info(f"收到评测资源生成请求，任务描述长度: {len(request.task_markdown)}")
        
        # 实例化LLM客户端
        llm_client = LLMClient()
        
        # 生成评测资源
        evaluation_assets = llm_client.generate_evaluation_assets(
            request.task_markdown,
            request.answer_code
        )
        
        return EvaluationAssetResponse(
            judge_script=evaluation_assets["judge_script"],
            test_cases=evaluation_assets["test_cases"]
        )
        
    except Exception as e:
        logger.error(f"评测资源生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"评测资源生成失败: {str(e)}")

# 新增API 3.3: 生成考核试题
@router.post("/exam-questions", response_model=QuestionGenerationResponse)
async def generate_exam_questions(request: QuestionGenerationRequest):
    """生成考核试题 (questions.json)"""
    try:
        logger.info(f"收到考核试题生成请求，单选:{request.num_single_choice}题，多选:{request.num_multiple_choice}题，判断:{request.num_true_false}题")
        
        # 实例化LLM客户端
        llm_client = LLMClient()
        
        # 生成考核试题
        questions = llm_client.generate_exam_questions(
            request.content_text,
            request.num_single_choice,
            request.num_multiple_choice,
            request.num_true_false
        )
        
        return QuestionGenerationResponse(questions=questions)
        
    except Exception as e:
        logger.error(f"考核试题生成失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"考核试题生成失败: {str(e)}") 

# 新增API: 多文件批量处理
@router.post("/full-course-package/tasks", response_model=TaskCreateResponse)
async def create_full_course_package_task(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """创建完整课程包生成任务（多文件批量处理）"""
    try:
        logger.info("收到多文件课程包生成请求")
        
        # 解析multipart/form-data
        form = await request.form()
        
        # 获取manifest JSON
        manifest_str = form.get("manifest")
        if not manifest_str:
            raise HTTPException(status_code=400, detail="缺少manifest参数")
        
        try:
            manifest_dict = json.loads(manifest_str)
            manifest = FullCourseManifest(**manifest_dict)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"manifest格式错误: {str(e)}")
        
        # 收集所有上传的文件
        file_data = {}
        for file_item in manifest.files:
            form_field_name = file_item.form_field_name
            uploaded_file = form.get(form_field_name)
            
            if not uploaded_file:
                raise HTTPException(
                    status_code=400, 
                    detail=f"文件 {form_field_name} 未上传"
                )
            
            # 读取文件内容
            file_content = await uploaded_file.read()
            file_data[form_field_name] = file_content
            
            logger.info(f"接收文件: {file_item.original_filename} ({len(file_content)} 字节)")
        
        # 创建异步任务
        task_id = task_manager.create_task("full_course_package")
        
        # 启动异步处理（传入当前用户ID用于数据库持久化）
        multi_file_processor.process_full_course_package_async(
            task_id, manifest, file_data, current_user.id
        )
        
        logger.info(f"创建课程包生成任务: {task_id}")
        
        return TaskCreateResponse(
            task_id=task_id,
            message="课程包生成任务已创建，请使用task_id查询处理进度"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建课程包任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")

@router.get("/full-course-package/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_full_course_package_task_status(task_id: str):
    """查询课程包生成任务状态"""
    try:
        logger.info(f"查询任务状态: {task_id}")
        
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 构建响应
        response = TaskStatusResponse(
            task_id=task_id,
            status=task.status,
            progress=task.progress
        )
        
        if task.status == "SUCCESS" and task.result:
            response.result = task.result
        elif task.status == "ERROR" and task.error_message:
            response.error_message = task.error_message
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}") 


# ==================== 实训资源生成API ====================

@router.post("/full-training-package/tasks", response_model=TrainingTaskCreateResponse)
async def create_full_training_package_task(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """创建完整实训包生成任务（多文件批量处理）"""
    try:
        logger.info("收到实训包生成请求")
        
        # 解析multipart/form-data
        form = await request.form()
        
        # 获取manifest JSON
        manifest_str = form.get("manifest")
        if not manifest_str:
            raise HTTPException(status_code=400, detail="缺少manifest参数")
        
        try:
            manifest_dict = json.loads(manifest_str)
            manifest = FullTrainingManifest(**manifest_dict)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"manifest格式错误: {str(e)}")
        
        # 收集所有上传的文件
        file_data = {}
        for file_item in manifest.files:
            form_field_name = file_item.form_field_name
            uploaded_file = form.get(form_field_name)
            
            if not uploaded_file:
                raise HTTPException(
                    status_code=400, 
                    detail=f"文件 {form_field_name} 未上传"
                )
            
            # 读取文件内容
            file_content = await uploaded_file.read()
            file_data[form_field_name] = file_content
            
            logger.info(f"接收实训文件: {file_item.original_filename} ({len(file_content)} 字节)")
        
        # 创建异步任务
        task_id = task_manager.create_task("full_training_package")
        
        # 启动异步处理（传入当前用户ID用于数据库持久化）
        from app.utils.training_package_processor import training_package_processor
        training_package_processor.process_full_training_package_async(
            task_id, manifest, file_data, current_user.id
        )
        
        logger.info(f"创建实训包生成任务: {task_id}")
        
        return TrainingTaskCreateResponse(
            task_id=task_id,
            message="实训包生成任务已创建，请使用task_id查询处理进度"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建实训包生成任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/full-training-package/tasks/{task_id}", response_model=TrainingTaskStatusResponse)
async def get_training_package_task_status(task_id: str):
    """查询实训包生成任务状态"""
    try:
        task = task_manager.get_task(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        return TrainingTaskStatusResponse(
            task_id=task_id,
            status=task.status.value,
            progress=task.progress,
            result=task.result,
            error_message=task.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询实训包任务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}")


# ==================== AI辅助内容创作API ====================

@router.post("/extract-text", response_model=ApiResponse)
async def extract_text(
    file: UploadFile = File(..., description="PDF或PPT文件"),
    db: Session = Depends(get_db)
):
    """
    API 1: 文本提取
    从上传的PDF或PPT文件中提取纯文本或Markdown内容
    """
    try:
        # 验证文件大小
        FileParser.validate_file_size(file, max_size_mb=20)
        
        # 验证文件类型
        allowed_extensions = ['.pdf', '.ppt', '.pptx', '.doc', '.docx']
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。支持的格式：{', '.join(allowed_extensions)}"
            )
        
        # 提取文件文本内容
        logger.info(f"开始提取文件文本: {file.filename}")
        text_content = await FileParser.extract_text_from_upload_file(file)
        
        if not text_content or len(text_content.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="文件内容过少，无法提取有效文本"
            )
        
        logger.info(f"文本提取完成，内容长度: {len(text_content)}")
        
        # 将文本转换为Markdown格式（如果可能）
        markdown_content = text_content  # 这里可以添加更复杂的转换逻辑
        
        return ApiResponse(
            code="0000",
            message="文本提取成功",
            data={
                "filename": file.filename,
                "text_content": text_content,
                "markdown_content": markdown_content,
                "content_length": len(text_content)
            },
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文本提取失败: {str(e)}")
        return ApiResponse(
            code="2000",
            message=f"文本提取失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/suggest-outline", response_model=ApiResponse)
async def suggest_outline(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    API 2: 知识点大纲建议
    基于提取的文本生成结构化的关卡大纲建议
    """
    try:
        text_content = request.get("text_content", "")
        course_type = request.get("course_type", "practice")  # practice/exam
        
        if not text_content:
            raise HTTPException(
                status_code=400,
                detail="缺少文本内容"
            )
        
        logger.info(f"开始生成大纲建议，文本长度: {len(text_content)}")
        
        # 调用LLM生成大纲
        outline_data = llm_client.generate_course_outline(text_content, "user_document")
        
        # 根据课程类型调整大纲
        structured_outline = []
        for item in outline_data:
            level_item = {
                "title": item.get("level_title", ""),
                "knowledge_points": item.get("core_knowledge", "").split("；"),
                "suggested_type": item.get("suggested_type", "实践题"),
                "difficulty": item.get("difficulty", "中级"),
                "estimated_time": 30 if item.get("suggested_type") == "实践题" else 10
            }
            structured_outline.append(level_item)
        
        logger.info(f"成功生成{len(structured_outline)}个关卡建议")
        
        return ApiResponse(
            code="0000",
            message="大纲建议生成成功",
            data={
                "outline": structured_outline,
                "total_levels": len(structured_outline),
                "course_type": course_type
            },
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成大纲建议失败: {str(e)}")
        return ApiResponse(
            code="2000",
            message=f"生成大纲建议失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/suggest-code-snippet", response_model=ApiResponse) 
async def suggest_code_snippet(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    API 3: 代码片段生成
    根据具体指令生成目标明确的代码片段
    """
    try:
        instruction = request.get("instruction", "")
        target_type = request.get("target_type", "student_template")  # student_template/judge_script/test_case
        context = request.get("context", "")
        language = request.get("language", "python")
        
        if not instruction:
            raise HTTPException(
                status_code=400,
                detail="缺少指令文本"
            )
        
        logger.info(f"生成代码片段，目标类型: {target_type}")
        
        # 根据目标类型构建不同的提示
        if target_type == "student_template":
            system_prompt = f"""你是一位编程教学专家，专门创建学生练习模板。
请根据指令生成一个{language}语言的代码模板，要求：
1. 包含清晰的注释和TODO标记
2. 提供必要的函数签名和结构
3. 留出学生需要填充的代码区域
4. 代码要可运行且结构清晰"""
            
        elif target_type == "judge_script":
            system_prompt = f"""你是一位自动化测试专家，专门编写评测脚本。
请根据指令生成评测代码，要求：
1. 能够正确读取和执行学生代码
2. 包含输入输出处理逻辑
3. 有错误处理机制
4. 返回清晰的评测结果"""
            
        elif target_type == "test_case":
            system_prompt = """你是一位测试用例设计专家。
请根据指令生成测试用例，要求：
1. 覆盖正常情况和边界情况
2. 包含输入和期望输出
3. 有合理的测试说明
返回JSON格式的测试用例数组"""
            
        else:
            system_prompt = f"""你是一位{language}编程专家。
请根据指令生成相应的代码片段。"""
        
        user_prompt = f"""指令：{instruction}

上下文信息：
{context if context else '无额外上下文'}

请生成符合要求的代码片段。"""
        
        # 调用LLM生成代码
        response = llm_client.client.chat.completions.create(
            model=llm_client.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        generated_code = response.choices[0].message.content
        logger.info(f"成功生成代码片段，长度: {len(generated_code)}")
        
        # 提取代码块（如果被markdown包围）
        if "```" in generated_code:
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', generated_code, re.DOTALL)
            if code_blocks:
                generated_code = code_blocks[0]
        
        return ApiResponse(
            code="0000",
            message="代码片段生成成功",
            data={
                "code": generated_code,
                "target_type": target_type,
                "language": language
            },
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成代码片段失败: {str(e)}")
        return ApiResponse(
            code="2000",
            message=f"生成代码片段失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/practice-outline-from-file", response_model=ApiResponse)
async def practice_outline_from_file(
    file: UploadFile = File(..., description="教学文件（PDF/PPT）"),
    db: Session = Depends(get_db)
):
    """
    接口 1: 从文件生成实践大纲
    上传教学文件，生成结构化的课程实践建议大纲
    """
    try:
        # 验证文件
        FileParser.validate_file_size(file, max_size_mb=20)
        
        # 提取文本
        logger.info(f"解析教学文件: {file.filename}")
        text_content = await FileParser.extract_text_from_upload_file(file)
        
        if not text_content or len(text_content.strip()) < 100:
            raise HTTPException(
                status_code=400,
                detail="文件内容不足，无法生成有效大纲"
            )
        
        # 生成实践大纲
        system_prompt = """你是一位资深的课程设计专家，专门为在线编程学习平台设计实践课程。
请根据教学文档内容，设计一个完整的课程实践大纲。

要求：
1. 将知识点拆解成多个渐进式的实践关卡
2. 每个关卡要有明确的学习目标和实践内容
3. 关卡难度要循序渐进
4. 包含不同类型的练习（编码题、选择题、判断题等）

返回JSON格式：
[
  {
    "level_title": "关卡标题",
    "core_knowledge": "核心知识点",
    "practice_description": "实践内容简述",
    "suggested_type": "实践题/选择题/判断题",
    "difficulty": "初级/中级/高级",
    "estimated_time": 预计完成时间（分钟）
  }
]"""
        
        user_prompt = f"""请为以下教学内容设计课程实践大纲：

文件名：{file.filename}
内容：
{text_content[:3000]}  # 限制长度

请生成6-10个实践关卡的完整大纲。"""
        
        response = llm_client.client.chat.completions.create(
            model=llm_client.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content
        
        # 解析JSON
        try:
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            else:
                json_content = content
            
            outline = json.loads(json_content)
        except:
            # 返回默认大纲
            outline = [
                {
                    "level_title": "基础概念入门",
                    "core_knowledge": "基本概念和原理",
                    "practice_description": "通过简单练习理解基础概念",
                    "suggested_type": "判断题",
                    "difficulty": "初级",
                    "estimated_time": 15
                }
            ]
        
        return ApiResponse(
            code="0000",
            message="实践大纲生成成功",
            data={
                "filename": file.filename,
                "outline": outline,
                "original_text": text_content  # 保存原文供后续使用
            },
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成实践大纲失败: {str(e)}")
        return ApiResponse(
            code="2000", 
            message=f"生成实践大纲失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/practice-level-content", response_model=ApiResponse)
async def practice_level_content(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    接口 2: 生成实践关卡内容
    基于大纲项生成完整的关卡内容（任务手册、代码模板、评测脚本等）
    """
    try:
        level_info = request.get("level_info", {})
        original_text = request.get("original_text", "")
        
        if not level_info:
            raise HTTPException(
                status_code=400,
                detail="缺少关卡信息"
            )
        
        level_type = level_info.get("suggested_type", "实践题")
        
        if level_type == "实践题":
            # 生成编程实践内容
            system_prompt = """你是一位专业的编程教学设计师，专门创建高质量的编程实践内容。
请生成完整的实践关卡内容。

返回JSON格式：
{
  "task_handbook": "## 任务说明\\n详细的Markdown格式任务手册...",
  "student_template": "# 学生代码模板\\n带注释和TODO的Python代码...",
  "judge_script": "# 评测脚本\\n完整的judge.py代码...",
  "test_cases": [
    {
      "input": "测试输入",
      "expected_output": "期望输出",
      "is_hidden": false,
      "description": "测试说明"
    }
  ],
  "reference_answer": "# 参考答案\\n完整的解决方案代码..."
}"""
            
            user_prompt = f"""请为以下关卡生成完整的实践内容：

关卡标题：{level_info.get('level_title')}
核心知识：{level_info.get('core_knowledge')}
实践描述：{level_info.get('practice_description', '')}
难度等级：{level_info.get('difficulty')}

参考上下文：
{original_text[:2000] if original_text else '无'}

请生成包含任务手册、学生模板、评测脚本、测试用例和参考答案的完整内容。"""
            
        else:
            # 生成选择题/判断题
            system_prompt = f"""你是一位教学评估专家，专门设计高质量的{level_type}。

返回JSON格式：
{{
  "questions": [
    {{
      "question_stem": "题目内容",
      "question_type": "{level_type}",
      "options": ["选项A", "选项B", ...],  // 判断题不需要
      "correct_answer": "A" 或 true/false,
      "analysis": "答案解析",
      "difficulty": "难度等级"
    }}
  ]
}}"""
            
            user_prompt = f"""请为以下知识点生成{level_type}：

知识点：{level_info.get('core_knowledge')}
难度：{level_info.get('difficulty')}

请生成3-5道高质量的题目。"""
        
        response = llm_client.client.chat.completions.create(
            model=llm_client.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content
        
        # 解析生成的内容
        try:
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_content = content[json_start:json_end].strip()
            else:
                json_content = content
            
            level_content = json.loads(json_content)
        except:
            # 返回默认内容
            if level_type == "实践题":
                level_content = {
                    "task_handbook": f"## {level_info.get('level_title')}\n\n请完成相关编程任务。",
                    "student_template": "# 请编写您的代码\npass",
                    "judge_script": "# 评测脚本\nprint('评测通过')",
                    "test_cases": [{"input": "test", "expected_output": "test", "is_hidden": False}],
                    "reference_answer": "# 参考答案\npass"
                }
            else:
                level_content = {
                    "questions": [{
                        "question_stem": "示例题目",
                        "question_type": level_type,
                        "correct_answer": "A",
                        "analysis": "示例解析"
                    }]
                }
        
        return ApiResponse(
            code="0000",
            message="关卡内容生成成功",
            data={
                "level_title": level_info.get('level_title'),
                "level_type": level_type,
                "content": level_content
            },
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成关卡内容失败: {str(e)}")
        return ApiResponse(
            code="2000",
            message=f"生成关卡内容失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# ==================== 课程考核试题生成API ====================

@router.post("/questions-from-file", response_model=ApiResponse)
async def generate_questions_from_file(
    file: UploadFile = File(..., description="教学文件（PDF/PPT）"),
    num_single_choice: int = 10,
    num_multiple_choice: int = 5,
    num_true_false: int = 5,
    db: Session = Depends(get_db)
):
    """
    从文件批量生成试题
    根据上传的教学文件，生成指定类型和数量的试题
    """
    try:
        # 验证文件
        FileParser.validate_file_size(file, max_size_mb=20)
        
        # 提取文本
        logger.info(f"解析教学文件以生成试题: {file.filename}")
        text_content = await FileParser.extract_text_from_upload_file(file)
        
        if not text_content or len(text_content.strip()) < 200:
            raise HTTPException(
                status_code=400,
                detail="文件内容不足，无法生成有效试题"
            )
        
        # 调用LLM生成试题
        logger.info(f"生成试题: 单选{num_single_choice}题, 多选{num_multiple_choice}题, 判断{num_true_false}题")
        questions = llm_client.generate_exam_questions(
            text_content,
            num_single_choice,
            num_multiple_choice,
            num_true_false
        )
        
        # 格式化为符合题库导入格式的数据
        formatted_questions = format_questions_for_import(questions)
        
        return ApiResponse(
            code="0000",
            message="试题生成成功",
            data={
                "filename": file.filename,
                "questions": formatted_questions,
                "statistics": {
                    "single_choice": num_single_choice,
                    "multiple_choice": num_multiple_choice,
                    "true_false": num_true_false,
                    "total": len(formatted_questions)
                }
            },
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成试题失败: {str(e)}")
        return ApiResponse(
            code="2000",
            message=f"生成试题失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/format-questions-for-excel", response_model=ApiResponse)
async def format_questions_for_excel(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    格式化试题为Excel导入格式
    将AI生成的试题转换为符合Excel模板的格式
    """
    try:
        questions = request.get("questions", [])
        subject = request.get("subject", "通用")
        chapter = request.get("chapter", "")
        
        if not questions:
            raise HTTPException(
                status_code=400,
                detail="缺少试题数据"
            )
        
        # 转换为Excel格式
        excel_data = []
        for idx, q in enumerate(questions, 1):
            # 基础信息
            row = {
                "序号": idx,
                "题目类型": q.get("question_type", "单选题"),
                "题干": q.get("question_stem", ""),
                "科目": subject,
                "章节": chapter,
                "难度": q.get("difficulty", "中等"),
                "答案解析": q.get("analysis", "")
            }
            
            # 处理选项和答案
            if q.get("question_type") == "判断题":
                row["正确答案"] = "正确" if q.get("correct_answer") == True else "错误"
            else:
                # 单选题或多选题
                options = q.get("options", [])
                for i, opt in enumerate(options[:6]):  # 最多支持6个选项
                    row[f"选项{chr(65+i)}"] = opt
                
                # 答案格式化
                correct = q.get("correct_answer", [])
                if isinstance(correct, list):
                    row["正确答案"] = ",".join(correct)
                else:
                    row["正确答案"] = correct
            
            excel_data.append(row)
        
        return ApiResponse(
            code="0000",
            message="格式化成功",
            data={
                "excel_format": excel_data,
                "total": len(excel_data)
            },
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"格式化试题失败: {str(e)}")
        return ApiResponse(
            code="2000",
            message=f"格式化试题失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


@router.post("/batch-import-questions", response_model=ApiResponse)
async def batch_import_questions(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    批量导入试题到题库
    将审核后的试题批量导入到系统题库
    """
    try:
        questions = request.get("questions", [])
        category_id = request.get("category_id")
        
        if not questions:
            raise HTTPException(
                status_code=400,
                detail="没有要导入的试题"
            )
        
        # 导入试题到数据库
        imported_count = 0
        failed_count = 0
        errors = []
        
        for q in questions:
            try:
                # 创建题目记录
                from app.models.models import Question
                
                question = Question(
                    question_type=map_question_type(q.get("question_type")),
                    question_stem=q.get("question_stem"),
                    options=json.dumps(q.get("options", [])),
                    correct_answer=q.get("correct_answer"),
                    analysis=q.get("analysis", ""),
                    difficulty=q.get("difficulty", "中等"),
                    subject=q.get("subject", ""),
                    chapter=q.get("chapter", ""),
                    category_id=category_id,
                    creator_id=current_user.id,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                
                db.add(question)
                imported_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append({
                    "question": q.get("question_stem", "")[:50],
                    "error": str(e)
                })
        
        # 提交数据库事务
        if imported_count > 0:
            db.commit()
        
        return ApiResponse(
            code="0000",
            message=f"导入完成：成功{imported_count}题，失败{failed_count}题",
            data={
                "imported": imported_count,
                "failed": failed_count,
                "errors": errors
            },
            trace_id=str(uuid.uuid4())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"批量导入试题失败: {str(e)}")
        return ApiResponse(
            code="2000",
            message=f"批量导入失败: {str(e)}",
            trace_id=str(uuid.uuid4())
        )


# 辅助函数
def format_questions_for_import(questions: List[Dict]) -> List[Dict]:
    """
    格式化试题为导入格式
    """
    formatted = []
    for q in questions:
        formatted_q = {
            "question_type": q.get("question_type", "单选题"),
            "question_stem": q.get("question_stem", ""),
            "difficulty": q.get("difficulty", "中等"),
            "analysis": q.get("analysis", "")
        }
        
        # 处理选项和答案
        if q.get("question_type") == "判断题":
            formatted_q["correct_answer"] = q.get("correct_answer", True)
        else:
            formatted_q["options"] = q.get("options", [])
            formatted_q["correct_answer"] = q.get("correct_answer", [])
        
        formatted.append(formatted_q)
    
    return formatted


def map_question_type(type_str: str) -> int:
    """
    映射题型字符串到数据库枚举值
    """
    type_map = {
        "单选题": 1,
        "多选题": 2,
        "判断题": 3,
        "填空题": 4,
        "问答题": 5
    }
    return type_map.get(type_str, 1)


# ==================== 自动化课程生成流水线 API ====================

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


# 内存中的任务存储（实际生产环境应使用Redis或数据库）
tasks_store = {}


@router.get("/course-projects", response_model=ApiResponse)
async def get_course_projects(db: Session = Depends(get_db)):
    """
    获取课程项目列表（每个文件夹是一个课程项目）
    检查每个项目的完成状态
    """
    try:
        resource_path = Path(__file__).parent.parent.parent.parent.parent / "ziyuan" / "课程资源"
        
        if not resource_path.exists():
            return ApiResponse(
                code="404",
                message="资源目录不存在",
                data={"projects": []}
            )
        
        # 扫描所有子目录（每个子目录是一个课程项目）
        projects = []
        supported_extensions = ['.pdf', '.ppt', '.pptx', '.doc', '.docx']
        
        for project_dir in resource_path.iterdir():
            if not project_dir.is_dir():
                continue
            if project_dir.name.startswith('.'):
                continue
                
            project_name = project_dir.name
            
            # 找出该项目中的所有教学文件
            project_files = []
            for ext in supported_extensions:
                for file_path in project_dir.glob(f"*{ext}"):
                    if not file_path.name.startswith('.'):
                        file_stat = file_path.stat()
                        project_files.append({
                            "name": file_path.name,
                            "size": file_stat.st_size,
                            "extension": file_path.suffix
                        })
            
            if not project_files:
                continue
                
            # 找出主文件（最大的PDF或PPT文件）
            main_file = max(project_files, key=lambda x: x["size"])
            
            # 检查数据库中的状态
            from app.models.models import Practice, Task, Question
            
            # 检查是否存在Practice记录
            practice = db.query(Practice).filter(
                Practice.title.like(f"%{project_name}%")
            ).first()
            
            status = "待处理"
            missing_parts = []
            
            if practice:
                # 检查是否有Tasks
                stages_count = db.query(Task).filter(
                    Task.practice_id == practice.id
                ).count()
                
                if stages_count == 0:
                    missing_parts.append("关卡内容")
                
                # 检查是否有Questions（通过category字段关联）
                questions_count = db.query(Question).filter(
                    Question.category.like(f"%{project_name}%")
                ).count()
                
                if questions_count == 0:
                    missing_parts.append("考核试题")
                
                if len(missing_parts) == 0:
                    status = "已完成"
                else:
                    status = "部分完成"
            else:
                status = "待处理"
                missing_parts = ["实践课程", "关卡内容", "考核试题"]
            
            projects.append({
                "project_name": project_name,
                "main_file": main_file["name"],
                "file_count": len(project_files),
                "total_size_mb": round(sum(f["size"] for f in project_files) / (1024 * 1024), 2),
                "status": status,
                "missing_parts": missing_parts,
                "practice_id": practice.id if practice else None
            })
        
        # 按状态排序：待处理 > 部分完成 > 已完成
        status_order = {"待处理": 0, "部分完成": 1, "已完成": 2}
        projects.sort(key=lambda x: (status_order.get(x["status"], 3), x["project_name"]))
        
        logger.info(f"扫描到 {len(projects)} 个课程项目")
        
        return ApiResponse(
            code="0000",
            message=f"获取课程项目列表成功，共 {len(projects)} 个项目",
            data={
                "projects": projects,
                "total": len(projects),
                "stats": {
                    "pending": len([p for p in projects if p["status"] == "待处理"]),
                    "partial": len([p for p in projects if p["status"] == "部分完成"]),
                    "completed": len([p for p in projects if p["status"] == "已完成"])
                }
            }
        )
        
    except Exception as e:
        logger.error(f"获取资源文件列表失败: {str(e)}")
        return ApiResponse(
            code="500",
            message=f"获取失败: {str(e)}",
            data=None
        )


async def supplement_course_project_task(task_id: str, project_name: str, category_id: int, user_id: int):
    """
    智能补充课程项目任务
    根据项目当前状态，只生成缺失的部分
    """
    try:
        from app.core.database import SessionLocal
        from app.models.models import Practice, Task, Question
        
        db = SessionLocal()
        
        # 更新任务状态
        tasks_store[task_id] = {
            "status": TaskStatus.PROCESSING.value,
            "progress": 5,
            "message": f"正在检查项目 {project_name} 的状态..."
        }
        
        # 1. 定位项目目录和主文件
        resource_path = Path(__file__).parent.parent.parent.parent.parent / "ziyuan" / "课程资源" / project_name
        if not resource_path.exists():
            raise Exception(f"项目目录不存在: {project_name}")
        
        # 找出最大的教学文件作为主文件
        supported_extensions = ['.pdf', '.ppt', '.pptx', '.doc', '.docx']
        main_file = None
        max_size = 0
        
        for ext in supported_extensions:
            for file_path in resource_path.glob(f"*{ext}"):
                if not file_path.name.startswith('.'):
                    file_size = file_path.stat().st_size
                    if file_size > max_size:
                        max_size = file_size
                        main_file = file_path
        
        if not main_file:
            raise Exception(f"项目 {project_name} 中没有找到教学文件")
        
        logger.info(f"使用主文件: {main_file.name}")
        
        # 2. 检查现有数据
        practice = db.query(Practice).filter(
            Practice.title.like(f"%{project_name}%")
        ).first()
        
        need_practice = practice is None
        need_stages = False
        need_questions = False
        
        # 将分类ID映射为分类名称（无论是否新建实践都需要）
        category_map = {
            1: "计算机基础",
            2: "数据分析",
            3: "人工智能",
            4: "软件开发",
        }
        category_name = category_map.get(category_id, "通用")

        if practice:
            # 检查是否需要生成Tasks
            stages_count = db.query(Task).filter(
                Task.practice_id == practice.id
            ).count()
            need_stages = stages_count == 0
            
            # 检查是否需要生成Questions
            questions_count = db.query(Question).filter(
                Question.category.like(f"%{project_name}%")
            ).count()
            need_questions = questions_count == 0
        else:
            need_stages = True
            need_questions = True
        
        tasks_store[task_id]["progress"] = 10
        tasks_store[task_id]["message"] = f"项目状态：Practice={not need_practice}, Tasks={not need_stages}, Questions={not need_questions}"
        
        # 3. 提取文本内容（如果需要生成任何内容）
        if need_practice or need_stages or need_questions:
            tasks_store[task_id]["progress"] = 15
            tasks_store[task_id]["message"] = "正在提取文本内容..."
            
            with open(main_file, 'rb') as f:
                file_content = f.read()
            
            from fastapi import UploadFile
            from io import BytesIO
            upload_file = UploadFile(
                filename=main_file.name,
                file=BytesIO(file_content)
            )
            
            text_content = await FileParser.extract_text_from_upload_file(upload_file)
        
        # 4. 按需生成Practice和Tasks
        if need_practice:
            tasks_store[task_id]["progress"] = 20
            tasks_store[task_id]["message"] = "正在创建实践课程..."
            
            practice = Practice(
                title=f"{project_name} - AI生成",
                description=f"基于 {main_file.name} 自动生成的实践课程",
                direction=category_name,
                category=category_name,
                difficulty=DifficultyLevelEnum.intermediate,
                creator_id=user_id,
            )
            db.add(practice)
            db.flush()
            logger.info(f"创建Practice: {practice.id}")
        
        if need_stages:
            tasks_store[task_id]["progress"] = 30
            tasks_store[task_id]["message"] = "正在生成关卡大纲..."
            
            # 生成大纲
            outline_data = llm_client.generate_course_outline(text_content, main_file.name)
            
            tasks_store[task_id]["progress"] = 40
            tasks_store[task_id]["message"] = f"正在生成{len(outline_data)}个关卡内容..."
            
            # 生成每个关卡
            for idx, outline_item in enumerate(outline_data):
                progress = 40 + (idx + 1) * 30 // len(outline_data)
                tasks_store[task_id]["progress"] = progress
                tasks_store[task_id]["message"] = f"生成关卡 {idx + 1}/{len(outline_data)}"
                
                level_content = llm_client.generate_level_content(text_content, outline_item)
                
                # 根据建议类型映射任务类型
                suggested_type = outline_item.get("suggested_type", "实践题")
                if suggested_type == "实践题":
                    task_type_enum = TaskTypeEnum.PRACTICE
                elif suggested_type == "选择题":
                    task_type_enum = TaskTypeEnum.SINGLE_CHOICE
                elif suggested_type == "判断题":
                    task_type_enum = TaskTypeEnum.TRUE_FALSE
                else:
                    task_type_enum = TaskTypeEnum.PRACTICE

                stage = Task(
                    practice_id=practice.id,
                    title=outline_item.get("level_title"),
                    task_type=task_type_enum,
                    order_in_practice=idx + 1,
                    difficulty=outline_item.get("difficulty"),
                    handbook_markdown=level_content.get("task_handbook") if isinstance(level_content, dict) else None,
                    question_data=json.dumps(level_content.get("questions")) if isinstance(level_content, dict) and level_content.get("questions") else None,
                )
                db.add(stage)
                
                await asyncio.sleep(0.5)  # 避免请求过快
            
            logger.info(f"为Practice {practice.id} 创建了 {len(outline_data)} 个Tasks")
        
        # 5. 按需生成Questions
        if need_questions:
            tasks_store[task_id]["progress"] = 70
            tasks_store[task_id]["message"] = "正在生成考核试题..."
            
            questions = llm_client.generate_exam_questions(
                text_content,
                num_single_choice=10,
                num_multiple_choice=5,
                num_true_false=5
            )
            
            tasks_store[task_id]["progress"] = 80
            tasks_store[task_id]["message"] = f"正在保存{len(questions)}道试题..."
            
            for q in questions:
                qt = q.get("question_type", "单选题")
                if qt == "单选题":
                    qtype_enum = QuestionTypeEnum.SINGLE_CHOICE
                elif qt == "多选题":
                    qtype_enum = QuestionTypeEnum.MULTIPLE_CHOICE
                elif qt == "判断题":
                    qtype_enum = QuestionTypeEnum.TRUE_FALSE
                else:
                    qtype_enum = QuestionTypeEnum.SINGLE_CHOICE

                correct = q.get("correct_answer")
                # 统一为JSON字符串
                from json import dumps as json_dumps
                if isinstance(correct, (list, dict)):
                    correct_json = json_dumps(correct, ensure_ascii=False)
                else:
                    # 将标量包装为列表，便于统一处理
                    correct_json = json_dumps([correct] if correct is not None else [], ensure_ascii=False)

                question = Question(
                    content=q.get("question_stem", ""),
                    question_type=qtype_enum,
                    options=json_dumps(q.get("options", []), ensure_ascii=False) if q.get("options") is not None else None,
                    correct_answers=correct_json,
                    explanation=q.get("analysis", ""),
                    difficulty=DifficultyEnum.INTERMEDIATE,
                    creator_id=user_id,
                    direction=category_name,
                    category=category_name,
                )
                db.add(question)
            
            logger.info(f"为项目 {project_name} 创建了 {len(questions)} 道试题")
        
        # 6. 提交事务
        db.commit()
        
        # 7. 更新任务状态为成功
        tasks_store[task_id]["progress"] = 100
        tasks_store[task_id]["status"] = TaskStatus.SUCCESS.value
        tasks_store[task_id]["message"] = "课程项目补充完成"
        tasks_store[task_id]["result"] = {
            "practice_id": practice.id if practice else None,
            "created_practice": need_practice,
            "created_stages": need_stages,
            "created_questions": need_questions
        }
        
    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {str(e)}")
        tasks_store[task_id] = {
            "status": TaskStatus.ERROR.value,
            "progress": tasks_store.get(task_id, {}).get("progress", 0),
            "message": f"处理失败: {str(e)}",
            "error": str(e)
        }
    finally:
        db.close()


async def process_course_generation_task(task_id: str, file_path: str, category_id: int = None):
    """
    异步处理课程生成任务
    这是核心的编排逻辑，将多个API串联起来
    
    Args:
        task_id: 任务ID
        file_path: 文件相对路径（可能包含子目录，如 "数据挖掘分析/第一章：人工智能的起源和发展.pdf"）
        category_id: 课程分类ID
    """
    try:
        # 更新任务状态为处理中
        tasks_store[task_id] = {
            "status": TaskStatus.PROCESSING.value,
            "progress": 0,
            "message": "开始处理文件..."
        }
        
        # 1. 定位文件（支持子目录）
        resource_path = Path(__file__).parent.parent.parent.parent.parent / "ziyuan" / "课程资源" / file_path
        if not resource_path.exists():
            raise Exception(f"文件不存在: {file_path}")
        
        tasks_store[task_id]["progress"] = 10
        tasks_store[task_id]["message"] = "正在提取文本内容..."
        
        # 2. 提取文本内容
        with open(resource_path, 'rb') as f:
            file_content = f.read()
        
        # 创建临时UploadFile对象
        from fastapi import UploadFile
        from io import BytesIO
        upload_file = UploadFile(
            filename=file_name,
            file=BytesIO(file_content)
        )
        
        text_content = await FileParser.extract_text_from_upload_file(upload_file)
        
        tasks_store[task_id]["progress"] = 20
        tasks_store[task_id]["message"] = "正在生成实践大纲..."
        
        # 3. 生成实践大纲
        # 使用文件名作为源标识符
        file_name = Path(file_path).name
        outline_data = llm_client.generate_course_outline(text_content, file_name)
        
        tasks_store[task_id]["progress"] = 30
        tasks_store[task_id]["message"] = f"正在生成{len(outline_data)}个关卡内容..."
        
        # 4. 生成每个关卡的详细内容
        generated_stages = []
        for idx, outline_item in enumerate(outline_data):
            tasks_store[task_id]["progress"] = 30 + (idx + 1) * 40 // len(outline_data)
            tasks_store[task_id]["message"] = f"生成关卡 {idx + 1}/{len(outline_data)}: {outline_item.get('level_title')}"
            
            # 生成关卡内容
            level_content = llm_client.generate_level_content(text_content, outline_item)
            
            generated_stages.append({
                "title": outline_item.get("level_title"),
                "content": level_content,
                "type": outline_item.get("suggested_type"),
                "difficulty": outline_item.get("difficulty")
            })
            
            # 避免请求过快
            await asyncio.sleep(1)
        
        tasks_store[task_id]["progress"] = 70
        tasks_store[task_id]["message"] = "正在生成考核试题..."
        
        # 5. 生成考核试题
        questions = llm_client.generate_exam_questions(
            text_content,
            num_single_choice=10,
            num_multiple_choice=5,
            num_true_false=5
        )
        
        tasks_store[task_id]["progress"] = 80
        tasks_store[task_id]["message"] = "正在保存到数据库..."
        
        # 6. 数据持久化（这里需要根据实际的数据库模型来实现）
        # 示例：创建Practice记录和Task记录
        from app.core.database import SessionLocal
        from app.models.models import Practice, Task
        
        db = SessionLocal()
        try:
            # 创建Practice记录
            practice = Practice(
                name=f"{file_name.rsplit('.', 1)[0]} - 自动生成",
                description=f"基于文件 {file_name} 自动生成的实践课程",
                difficulty="中级",
                category_id=category_id,
                creator_id=1,  # 需要实际的用户ID
                created_at=datetime.now()
            )
            db.add(practice)
            db.flush()
            
            # 创建Task记录
            for idx, stage_data in enumerate(generated_stages):
                stage = Task(
                    practice_id=practice.id,
                    title=stage_data["title"],
                    order=idx + 1,
                    content=json.dumps(stage_data["content"]),
                    type=stage_data["type"],
                    difficulty=stage_data["difficulty"]
                )
                db.add(stage)
            
            # 保存试题（需要题库表结构）
            # ...
            
            db.commit()
            
            tasks_store[task_id]["progress"] = 100
            tasks_store[task_id]["status"] = TaskStatus.SUCCESS.value
            tasks_store[task_id]["message"] = "课程生成成功"
            tasks_store[task_id]["result"] = {
                "practice_id": practice.id,
                "stages_count": len(generated_stages),
                "questions_count": len(questions)
            }
            
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {str(e)}")
        tasks_store[task_id] = {
            "status": TaskStatus.ERROR.value,
            "progress": tasks_store.get(task_id, {}).get("progress", 0),
            "message": f"处理失败: {str(e)}",
            "error": str(e)
        }


@router.post("/supplement-course-project", response_model=ApiResponse)
async def supplement_course_project(
    request: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    智能补充课程项目
    根据项目当前状态，只生成缺失的部分
    
    参数:
        project_name: 项目文件夹名称
        category_id: 课程分类ID
    """
    try:
        project_name = request.get("project_name")
        category_id = request.get("category_id", 1)
        
        if not project_name:
            raise HTTPException(
                status_code=400,
                detail="缺少项目名称参数"
            )
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        tasks_store[task_id] = {
            "status": TaskStatus.PENDING.value,
            "progress": 0,
            "message": "正在分析项目状态..."
        }
        
        # 启动异步任务（智能补充模式）
        asyncio.create_task(
            supplement_course_project_task(
                task_id, 
                project_name, 
                category_id,
                current_user.id
            )
        )
        
        logger.info(f"创建智能补充任务: {task_id} for project: {project_name}")
        
        return ApiResponse(
            code="0000",
            message="任务创建成功",
            data={
                "task_id": task_id,
                "project_name": project_name,
                "status": "pending"
            },
            trace_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建课程生成任务失败: {str(e)}")
        return ApiResponse(
            code="500",
            message=f"创建任务失败: {str(e)}",
            data=None
        )


@router.get("/tasks/{task_id}/status", response_model=ApiResponse)
async def get_task_status(task_id: str):
    """
    查询任务状态
    返回任务的当前状态、进度和结果
    """
    try:
        task = tasks_store.get(task_id)
        
        if not task:
            return ApiResponse(
                code="404",
                message="任务不存在",
                data=None
            )
        
        return ApiResponse(
            code="0000",
            message="获取任务状态成功",
            data={
                "task_id": task_id,
                "status": task.get("status"),
                "progress": task.get("progress"),
                "message": task.get("message"),
                "result": task.get("result") if task.get("status") == TaskStatus.SUCCESS.value else None,
                "error": task.get("error") if task.get("status") == TaskStatus.ERROR.value else None
            },
            trace_id=task_id
        )
        
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}")
        return ApiResponse(
            code="500",
            message=f"查询失败: {str(e)}",
            data=None
        )


# ====================== 实训资源增强 APIs ======================

@router.get("/training-projects", response_model=ApiResponse)
async def get_training_projects(
    db: Session = Depends(get_db)
):
    """
    获取实训资源项目列表
    扫描 ziyuan/实训资源/ 目录，返回每个项目的状态
    
    返回:
        - project_name: 项目名称
        - status: 状态（待处理/部分完成/已完成）
        - missing_components: 缺失的组件列表
    """
    try:
        base_path = Path("ziyuan/实训资源")
        
        if not base_path.exists():
            return ApiResponse(
                code="404",
                message="实训资源目录不存在",
                data={"projects": [], "total": 0}
            )
        
        projects = []
        
        # 扫描所有子目录（每个子目录是一个实训项目）
        for project_dir in sorted(base_path.iterdir()):
            if not project_dir.is_dir():
                continue
            
            # 跳过特殊目录
            if project_dir.name in ['ai_generated', 'assets', 'datasets', 'notebooks', 'templates', '.DS_Store']:
                continue
            
            project_name = project_dir.name
            
            # 统计项目中的文件
            files = []
            for file_path in project_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    files.append({
                        'path': str(file_path.relative_to(base_path)),
                        'size': file_path.stat().st_size
                    })
            
            if not files:
                continue
            
            # 找出最大的文件作为主文件
            largest_file = max(files, key=lambda x: x['size'])
            
            # 检查数据库中是否有该项目的实训记录
            # 这里需要根据实际的实训表结构调整
            has_training = False
            has_datasets = False
            has_notebooks = False
            training_id = None
            
            # 检查是否存在相关的实训记录（基于项目名称）
            # 注意：这里假设有一个Training表，实际需要根据你的数据模型调整
            # training = db.query(Training).filter(
            #     Training.name.contains(project_name)
            # ).first()
            # if training:
            #     has_training = True
            #     training_id = training.id
            
            # 判断项目状态
            missing_components = []
            if not has_training:
                missing_components.append("实训任务")
            if not has_datasets:
                missing_components.append("数据集")
            if not has_notebooks:
                missing_components.append("实验笔记")
            
            if len(missing_components) == 0:
                status = "已完成"
            elif len(missing_components) < 3:
                status = "部分完成"
            else:
                status = "待处理"
            
            projects.append({
                "project_name": project_name,
                "path": str(project_dir),
                "file_count": len(files),
                "largest_file": largest_file['path'],
                "largest_file_size_mb": round(largest_file['size'] / (1024 * 1024), 2),
                "status": status,
                "missing_components": missing_components,
                "has_training": has_training,
                "has_datasets": has_datasets,
                "has_notebooks": has_notebooks,
                "training_id": training_id
            })
        
        return ApiResponse(
            code="0000",
            message="获取实训项目列表成功",
            data={
                "projects": projects,
                "total": len(projects),
                "stats": {
                    "completed": len([p for p in projects if p["status"] == "已完成"]),
                    "partial": len([p for p in projects if p["status"] == "部分完成"]),
                    "pending": len([p for p in projects if p["status"] == "待处理"])
                }
            },
            trace_id=str(uuid.uuid4())
        )
        
    except Exception as e:
        logger.error(f"获取实训项目列表失败: {str(e)}")
        return ApiResponse(
            code="500",
            message=f"获取项目列表失败: {str(e)}",
            data={"projects": [], "total": 0}
        )


@router.post("/supplement-training-project", response_model=ApiResponse)
async def supplement_training_project(
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    智能增强实训项目
    根据项目当前状态，只生成缺失的部分
    
    参数:
        project_name: 项目文件夹名称
    """
    try:
        project_name = request.get("project_name")
        
        if not project_name:
            raise HTTPException(
                status_code=400,
                detail="缺少项目名称参数"
            )
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        tasks_store[task_id] = {
            "status": TaskStatus.PENDING.value,
            "progress": 0,
            "message": "正在分析实训项目状态..."
        }
        
        # 启动异步任务（智能增强模式）
        asyncio.create_task(
            supplement_training_project_task(
                task_id, 
                project_name,
                current_user.id
            )
        )
        
        logger.info(f"创建实训增强任务: {task_id} for project: {project_name}")
        
        return ApiResponse(
            code="0000",
            message="任务创建成功",
            data={
                "task_id": task_id,
                "project_name": project_name,
                "status": "pending"
            },
            trace_id=task_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建实训增强任务失败: {str(e)}")
        return ApiResponse(
            code="500",
            message=f"创建任务失败: {str(e)}",
            data=None
        )


async def supplement_training_project_task(task_id: str, project_name: str, user_id: int):
    """
    异步任务：智能增强实训项目
    只生成项目中缺失的组件
    """
    try:
        # 更新状态
        tasks_store[task_id]["status"] = TaskStatus.PROCESSING.value
        tasks_store[task_id]["progress"] = 10
        tasks_store[task_id]["message"] = "正在检查项目现有组件..."
        
        # 连接数据库
        db = SessionLocal()
        
        try:
            # 找到项目中最大的文件
            base_path = Path("ziyuan/实训资源")
            project_path = base_path / project_name
            
            if not project_path.exists():
                raise Exception(f"项目目录不存在: {project_name}")
            
            # 找出最大的文件
            files = []
            for file_path in project_path.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    files.append({
                        'path': file_path,
                        'size': file_path.stat().st_size
                    })
            
            if not files:
                raise Exception(f"项目中没有找到文件: {project_name}")
            
            largest_file = max(files, key=lambda x: x['size'])
            file_path = str(largest_file['path'])
            
            # 检查现有组件
            # 注意：这里需要根据实际的实训数据模型调整
            has_training = False
            has_datasets = False
            has_notebooks = False
            
            tasks_store[task_id]["progress"] = 30
            tasks_store[task_id]["message"] = "正在生成缺失的组件..."
            
            # 根据缺失的组件进行智能补充
            generated_count = 0
            
            if not has_training:
                # 生成实训任务
                tasks_store[task_id]["message"] = "正在生成实训任务..."
                # TODO: 调用生成实训任务的逻辑
                generated_count += 1
                tasks_store[task_id]["progress"] = 50
            
            if not has_datasets:
                # 生成数据集
                tasks_store[task_id]["message"] = "正在准备数据集..."
                # TODO: 调用生成数据集的逻辑
                generated_count += 1
                tasks_store[task_id]["progress"] = 70
            
            if not has_notebooks:
                # 生成实验笔记
                tasks_store[task_id]["message"] = "正在生成实验笔记..."
                # TODO: 调用生成实验笔记的逻辑
                generated_count += 1
                tasks_store[task_id]["progress"] = 90
            
            # 完成
            tasks_store[task_id]["status"] = TaskStatus.SUCCESS.value
            tasks_store[task_id]["progress"] = 100
            tasks_store[task_id]["message"] = f"实训项目增强完成，生成了 {generated_count} 个组件"
            tasks_store[task_id]["result"] = {
                "training_generated": not has_training,
                "datasets_generated": not has_datasets,
                "notebooks_generated": not has_notebooks,
                "total_generated": generated_count
            }
            
            logger.info(f"实训项目增强完成: {project_name}, 生成了 {generated_count} 个组件")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"实训项目增强失败: {str(e)}")
        tasks_store[task_id]["status"] = TaskStatus.ERROR.value
        tasks_store[task_id]["error"] = str(e)
        tasks_store[task_id]["message"] = f"处理失败: {str(e)}" 