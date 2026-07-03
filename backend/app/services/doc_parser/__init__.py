"""文档解析服务 (慧学 AI 升级方案 v2 - 第五章 资料解析)。

对齐方案第五章示例结构:
{
  "document_id": "doc_123",
  "title": "数据分析基础课件",
  "file_type": "pptx",
  "pages": 18,
  "chunks": [
    {"chunk_id": "chunk_001", "page": 3, "heading": "数据导入", "text": "..."}
  ]
}
"""

from .parser import (
    DocParseError,
    parse_document,
    parse_docx,
    parse_pdf,
    parse_pptx,
)

__all__ = [
    "DocParseError",
    "parse_document",
    "parse_docx",
    "parse_pdf",
    "parse_pptx",
]
