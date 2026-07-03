# doc_parser

对应《慧学AI升级方案-v2.md》第五章"资料解析"。将老师上传的 PDF / DOCX / PPTX
解析为统一的 chunk 结构，供后续知识点拆解 / AI 生成关卡使用。

## 接口

```python
from app.services.doc_parser import parse_document, parse_pdf, parse_docx, parse_pptx, DocParseError

result = parse_document("/path/to/file.pdf")  # 按扩展名自动分发
# 或直接调用具体格式的解析函数
result = parse_pdf("/path/to/file.pdf")
result = parse_docx("/path/to/file.docx")
result = parse_pptx("/path/to/file.pptx")
```

返回结构（与方案第五章示例对齐）：

```json
{
  "document_id": "doc_xxx",
  "title": "文档标题",
  "file_type": "pdf | docx | pptx",
  "pages": 18,
  "chunks": [
    {"chunk_id": "chunk_001", "page": 3, "heading": "数据导入", "text": "..."}
  ]
}
```

失败时抛出 `DocParseError`（带清楚的 message 和 file_path），不会静默返回空结构。

## 依赖

- PDF: `pypdf`（已在 requirements.txt）
- DOCX: `python-docx`（已在 requirements.txt）
- PPTX: 优先用 `python-pptx`（若已安装）；否则用标准库 `zipfile` + `xml.etree`
  直接解析 `ppt/slides/slideN.xml`，不引入新依赖。

## 已知局限

- **扫描版 PDF**：无文字层的 PDF 无法提取文字，`parse_pdf` 会在全文档零文字时
  抛 `DocParseError` 提示疑似扫描版。多模态 OCR 识别是方案第十九章的后续能力，
  本模块不实现。
- **DOCX 页码**：Word 的分页是渲染时动态计算的，`python-docx` 无法在不渲染的
  情况下拿到真实页码，因此 DOCX 解析结果的 `page` 字段固定为 `1`，`heading`
  按标题样式（Heading 1/2/3 或"标题 1/2/3"）切分 chunk。
- **PPTX zipfile 兜底**：未安装 `python-pptx` 时，走 XML 解析只能提取标准
  占位符（title/body）文字与 speaker notes，无法处理 SmartArt、嵌入图表内部
  文字、艺术字特效等复杂对象。
- **图片中的文字**（图表截图等）不会被提取，需依赖方案中提到的视觉模型描述
  能力（后续阶段）。
