"""
文件服务端点 - 提供从本地ziyuan文件夹访问文件的功能
"""

from pathlib import Path
import mimetypes
import os

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_db, get_current_user
from app.models import models
from app.utils.logger import logger

router = APIRouter()


def ranged_file_response(file_path: Path, request: Request, media_type: str):
    """
    支持 HTTP Range 请求的文件响应（用于视频流式播放）
    """
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")
    
    if range_header:
        # 解析 Range 头
        range_match = range_header.replace("bytes=", "").split("-")
        start = int(range_match[0]) if range_match[0] else 0
        end = int(range_match[1]) if range_match[1] else file_size - 1
        
        # 确保范围有效
        if start >= file_size:
            return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})
        
        end = min(end, file_size - 1)
        content_length = end - start + 1
        
        def iter_file():
            with open(file_path, "rb") as f:
                f.seek(start)
                remaining = content_length
                chunk_size = 1024 * 1024  # 1MB chunks
                while remaining > 0:
                    read_size = min(chunk_size, remaining)
                    data = f.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data
        
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": media_type,
        }
        
        return StreamingResponse(
            iter_file(),
            status_code=206,
            headers=headers,
            media_type=media_type
        )
    else:
        # 没有 Range 请求，返回完整文件
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        }
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            headers=headers
        )

# 基础资源目录
BASE_RESOURCE_DIR = settings.resource_base_path

# MIME类型映射
MIME_TYPES = {
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.csv': 'text/csv',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.mp4': 'video/mp4',
    '.avi': 'video/x-msvideo',
    '.mov': 'video/quicktime',
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.zip': 'application/zip',
    '.rar': 'application/x-rar-compressed',
    '.7z': 'application/x-7z-compressed',
    '.txt': 'text/plain',
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.html': 'text/html',
    '.py': 'text/x-python',
    '.js': 'application/javascript',
    '.java': 'text/x-java-source',
    '.cpp': 'text/x-c++src',
    '.c': 'text/x-csrc',
}

def get_mime_type(file_path: Path) -> str:
    """获取文件的MIME类型"""
    ext = file_path.suffix.lower()
    mime_type = MIME_TYPES.get(ext)
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(str(file_path))
    return mime_type or 'application/octet-stream'

@router.get("/classroom-disk/{classroom_id}/{filename}")
async def serve_classroom_disk_file(
    classroom_id: int,
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提供课堂云盘文件访问"""
    try:
        # 验证用户是否有权限访问该课堂
        # TODO: 添加权限验证逻辑
        
        # 构建文件路径
        file_path = BASE_RESOURCE_DIR / "课堂云盘" / f"classroom_{classroom_id}" / filename
        
        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 安全检查：确保文件路径在允许的目录内
        try:
            file_path.resolve().relative_to(BASE_RESOURCE_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="非法文件访问")
        
        # 返回文件
        return FileResponse(
            path=str(file_path),
            media_type=get_mime_type(file_path),
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"文件访问失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件访问失败: {str(e)}")

@router.get("/training-dataset/{training_id}/{filename}")
async def serve_training_dataset_file(
    training_id: int,
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提供实训数据集文件访问"""
    try:
        # 构建文件路径
        file_path = BASE_RESOURCE_DIR / "实训资源" / f"training_{training_id}" / filename
        
        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 安全检查：确保文件路径在允许的目录内
        try:
            file_path.resolve().relative_to(BASE_RESOURCE_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="非法文件访问")
        
        # 返回文件
        return FileResponse(
            path=str(file_path),
            media_type=get_mime_type(file_path),
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"数据集文件访问失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件访问失败: {str(e)}")

@router.get("/homework/{homework_id}/{student_id}/{filename}")
async def serve_homework_submission_file(
    homework_id: int,
    student_id: int,
    filename: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提供作业提交文件访问"""
    try:
        # 验证用户权限：学生只能访问自己的文件，教师可以访问所有学生的文件
        # TODO: 添加教师权限验证
        if current_user.id != student_id:
            raise HTTPException(status_code=403, detail="无权限访问该文件")
        
        # 构建文件路径
        file_path = BASE_RESOURCE_DIR / "作业提交" / f"homework_{homework_id}" / f"student_{student_id}" / filename
        
        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 安全检查：确保文件路径在允许的目录内
        try:
            file_path.resolve().relative_to(BASE_RESOURCE_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="非法文件访问")
        
        # 返回文件
        return FileResponse(
            path=str(file_path),
            media_type=get_mime_type(file_path),
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"作业文件访问失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件访问失败: {str(e)}")


@router.get("/preview/image/{path:path}")
async def preview_image(
    path: str,
    width: int = 800,
    height: int = 600
):
    """预览图片文件"""
    try:
        # 构建文件路径
        file_path = BASE_RESOURCE_DIR / path
        
        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 安全检查
        try:
            file_path.resolve().relative_to(BASE_RESOURCE_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="非法文件访问")
        
        # 检查是否为图片文件
        if file_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            raise HTTPException(status_code=400, detail="不是有效的图片文件")
        
        # 返回图片
        return FileResponse(
            path=str(file_path),
            media_type=get_mime_type(file_path)
        )
        
    except Exception as e:
        logger.error(f"图片预览失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"图片预览失败: {str(e)}")

@router.get("/teaching-resource/{module_id}/{filename}")
async def serve_teaching_resource_by_module(
    module_id: int,
    filename: str,
    preview: bool = False,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提供教学资源文件访问（基于模块ID）"""
    import urllib.parse
    
    try:
        # 验证用户权限
        # 如果是预览模式，任何用户都可以预览
        # 如果是下载模式，只有教师可以下载
        if not preview:
            # 验证是否为教师
            user_id = current_user.get('id', 1) if isinstance(current_user, dict) else current_user.id
            # TODO: 这里应该检查用户是否为教师
            
            # 构建文件路径
            file_path = BASE_RESOURCE_DIR / "教学资源" / f"module_{module_id}" / filename
            
            # 检查文件是否存在
            if not file_path.exists() or not file_path.is_file():
                raise HTTPException(status_code=404, detail="文件不存在")
            
            # 安全检查：确保文件路径在允许的目录内
            try:
                file_path.resolve().relative_to(BASE_RESOURCE_DIR.resolve())
            except ValueError:
                raise HTTPException(status_code=403, detail="非法文件访问")
            
            # 对文件名进行URL编码以支持中文
            encoded_filename = urllib.parse.quote(filename)
            
            # 返回文件用于下载
            return FileResponse(
                path=str(file_path),
                media_type=get_mime_type(file_path),
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
            )
        
        else:
            # 预览模式 - 返回文件内容但设置为inline显示
            file_path = BASE_RESOURCE_DIR / "教学资源" / f"module_{module_id}" / filename
            
            # 检查文件是否存在
            if not file_path.exists() or not file_path.is_file():
                raise HTTPException(status_code=404, detail="文件不存在")
            
            # 安全检查：确保文件路径在允许的目录内
            try:
                file_path.resolve().relative_to(BASE_RESOURCE_DIR.resolve())
            except ValueError:
                raise HTTPException(status_code=403, detail="非法文件访问")
            
            # 对文件名进行URL编码以支持中文
            encoded_filename = urllib.parse.quote(filename)
            
            # 返回文件用于预览
            return FileResponse(
                path=str(file_path),
                media_type=get_mime_type(file_path),
                headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"}
            )
        
    except Exception as e:
        logger.error(f"教学资源文件访问失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件访问失败: {str(e)}")

@router.get("/test-file-access")
async def test_file_access():
    """测试文件访问"""
    try:
        test_path = BASE_RESOURCE_DIR / "课程资源" / "机器学习实战" / "机器学习导论.pdf"
        return {
            "base_dir": str(BASE_RESOURCE_DIR),
            "test_path": str(test_path),
            "exists": test_path.exists(),
            "is_file": test_path.is_file() if test_path.exists() else False
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/course-files/{path:path}")
@router.head("/course-files/{path:path}")
async def serve_course_files(path: str, preview: bool = False):
    """简化的课程文件服务端点"""
    from urllib.parse import unquote
    from fastapi.responses import FileResponse
    
    # URL解码
    decoded_path = unquote(path)
    file_path = BASE_RESOURCE_DIR / decoded_path
    
    # 检查文件存在
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 返回文件
    import urllib.parse
    encoded_filename = urllib.parse.quote(file_path.name)
    return FileResponse(
        path=str(file_path),
        media_type=get_mime_type(file_path),
        headers={"Content-Disposition": f"{'inline' if preview else 'attachment'}; filename*=UTF-8''{encoded_filename}"}
    )

@router.get("/syllabus/{filename}")
@router.head("/syllabus/{filename}")
async def serve_syllabus_file(filename: str):
    """提供教学大纲Markdown文件访问"""
    try:
        # 构建教学大纲文件路径
        syllabus_dir = Path("static/resources/syllabus")
        file_path = syllabus_dir / filename

        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            logger.error(f"教学大纲文件不存在: {filename}, 完整路径: {file_path}")
            raise HTTPException(status_code=404, detail=f"教学大纲文件不存在: {filename}")

        # 安全检查：确保文件在syllabus目录内
        try:
            file_path.resolve().relative_to(syllabus_dir.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="非法文件访问")

        # 获取文件MIME类型（Markdown文件使用text/plain或text/markdown）
        mime_type = get_mime_type(file_path)
        if not mime_type or mime_type == 'application/octet-stream':
            mime_type = 'text/markdown'  # 默认Markdown MIME类型

        # 对文件名进行URL编码以支持中文
        import urllib.parse
        encoded_filename = urllib.parse.quote(file_path.name)

        # 返回文件内容（教学大纲使用inline显示）
        return FileResponse(
            path=str(file_path),
            media_type=mime_type,
            headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"教学大纲文件访问失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件访问失败: {str(e)}")


@router.get("/teaching-resources/{path:path}")
@router.head("/teaching-resources/{path:path}")
async def serve_teaching_resources(
    path: str,
    request: Request,
    preview: bool = False
):
    """提供课程资源文件访问（支持预览模式和视频流式播放）"""
    from urllib.parse import unquote
    import urllib.parse

    try:
        # URL解码路径参数（处理中文字符）
        decoded_path = unquote(path)

        # 构建文件路径
        file_path = BASE_RESOURCE_DIR / decoded_path

        # 检查文件是否存在
        if not file_path.exists() or not file_path.is_file():
            logger.error(f"文件不存在: {decoded_path}, 完整路径: {file_path}")
            raise HTTPException(status_code=404, detail=f"文件不存在: {decoded_path}")

        # 安全检查：确保文件路径在允许的目录内
        try:
            file_path.resolve().relative_to(BASE_RESOURCE_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=403, detail="非法文件访问")

        # 获取文件MIME类型
        mime_type = get_mime_type(file_path)

        # 对文件名进行URL编码以支持中文
        encoded_filename = urllib.parse.quote(file_path.name)

        # 视频文件使用支持 Range 请求的流式响应
        if mime_type and mime_type.startswith('video/'):
            return ranged_file_response(file_path, request, mime_type)

        # 根据预览模式设置响应头
        if preview:
            # 预览模式 - 设置为inline显示
            return FileResponse(
                path=str(file_path),
                media_type=mime_type,
                headers={"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}"}
            )
        else:
            # 下载模式
            return FileResponse(
                path=str(file_path),
                media_type=mime_type,
                headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"课程资源文件访问失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件访问失败: {str(e)}")
