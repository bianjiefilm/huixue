"""
文件解析工具
支持PDF和DOCX文件的文本提取
"""

import io
import os
from typing import Optional
from fastapi import UploadFile, HTTPException
import logging

logger = logging.getLogger(__name__)

# 可选依赖，用于文档解析
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class FileParser:
    """文件解析器"""
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """从PDF文件中提取文本"""
        if not PDF_AVAILABLE:
            raise HTTPException(
                status_code=500, 
                detail="PDF解析功能不可用，请安装PyPDF2库: pip install PyPDF2"
            )
        
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"PDF解析失败: {str(e)}")
            raise HTTPException(status_code=400, detail=f"PDF文件解析失败: {str(e)}")
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """从DOCX文件中提取文本"""
        if not DOCX_AVAILABLE:
            raise HTTPException(
                status_code=500, 
                detail="DOCX解析功能不可用，请安装python-docx库: pip install python-docx"
            )
        
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"DOCX解析失败: {str(e)}")
            raise HTTPException(status_code=400, detail=f"DOCX文件解析失败: {str(e)}")
    
    @staticmethod
    async def extract_text_from_upload_file(file: UploadFile) -> str:
        """从上传的文件中提取文本"""
        # 兼容性：优先根据 content_type 判断，其次根据文件后缀名判断
        allowed_types = {
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
        }
        file_ext = os.path.splitext(file.filename or "")[1].lower()
        content_type = getattr(file, "content_type", None)
        is_pdf = (content_type == "application/pdf") or (content_type is None and file_ext == ".pdf")
        is_docx = (
            content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            or (content_type is None and file_ext == ".docx")
        )
        if not (is_pdf or is_docx):
            # 如果content_type不匹配但扩展名能识别，继续处理；否则报错
            if file_ext in [".pdf", ".docx"]:
                # 允许继续
                pass
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="不支持的文件类型，仅支持PDF和DOCX文件"
                )
        
        # 读取文件内容
        try:
            file_content = await file.read()
            if len(file_content) == 0:
                raise HTTPException(status_code=400, detail="文件内容为空")
        except Exception as e:
            logger.error(f"文件读取失败: {str(e)}")
            raise HTTPException(status_code=400, detail=f"文件读取失败: {str(e)}")
        
        # 根据文件类型提取文本（根据content_type或扩展名）
        if is_pdf or file_ext == ".pdf":
            return FileParser.extract_text_from_pdf(file_content)
        if is_docx or file_ext == ".docx":
            return FileParser.extract_text_from_docx(file_content)
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    
    @staticmethod
    def validate_file_size(file: UploadFile, max_size_mb: int = 10) -> None:
        """验证文件大小"""
        if hasattr(file, 'size') and file.size:
            max_size_bytes = max_size_mb * 1024 * 1024
            if file.size > max_size_bytes:
                raise HTTPException(
                    status_code=400, 
                    detail=f"文件大小超过限制，最大支持{max_size_mb}MB"
                ) 