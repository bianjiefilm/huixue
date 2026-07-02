"""
文本解释API端点
用于实现"帮我讲讲这段"功能
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import openai
import os

from app.core.dependencies import get_db
from app.schemas import schemas
from app.utils.logger import logger

router = APIRouter()

class ExplainTextRequest(BaseModel):
    """文本解释请求"""
    text: str
    context: Optional[str] = None  # 上下文信息
    level: str = "beginner"  # 解释难度：beginner, intermediate, advanced

class ExplainTextResponse(BaseModel):
    """文本解释响应"""
    original_text: str
    explanation: str
    key_points: list[str]
    examples: list[str]

@router.post("/explain", response_model=schemas.ApiResponse)
async def explain_text(
    request: ExplainTextRequest,
    db: Session = Depends(get_db)
):
    """
    解释选中的文本内容
    
    Args:
        request: 包含待解释文本的请求
        db: 数据库会话
        
    Returns:
        包含解释内容的响应
    """
    try:
        # 构建提示词
        level_prompts = {
            "beginner": "请用简单易懂的语言解释，就像对初学者讲解一样",
            "intermediate": "请用中等难度的语言解释，适合有一定基础的人理解", 
            "advanced": "请用专业术语和深入的分析来解释"
        }
        
        level_prompt = level_prompts.get(request.level, level_prompts["beginner"])
        
        system_prompt = f"""
你是一个专业的知识解释助手。{level_prompt}。

请按以下格式回答：
1. 核心解释：用通俗易懂的话解释这段内容的含义
2. 关键要点：列出3-5个关键点
3. 实例说明：给出1-2个具体例子帮助理解

要求：
- 语言生动有趣，避免枯燥
- 使用生活化的比喻和例子
- 突出重点，去除冗余信息
"""

        user_prompt = f"""
请帮我解释这段文本：

"{request.text}"

{f'上下文信息：{request.context}' if request.context else ''}
"""

        # 模拟AI响应（实际项目中需要集成真正的AI服务）
        explanation = generate_explanation(request.text, request.level, request.context)
        
        return schemas.ApiResponse(
            code="0000",
            message="文本解释生成成功",
            data={
                "original_text": request.text,
                "explanation": explanation["explanation"],
                "key_points": explanation["key_points"],
                "examples": explanation["examples"]
            }
        )
        
    except Exception as e:
        logger.error(f"生成文本解释失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"生成文本解释失败: {str(e)}"
        )

def generate_explanation(text: str, level: str, context: Optional[str] = None) -> dict:
    """
    生成文本解释
    
    这里是一个示例实现，实际项目中应该集成OpenAI、Claude等AI服务
    """
    # 示例解释逻辑
    explanations = {
        "数据库": {
            "explanation": "数据库就像一个超级整理柜，专门用来存储和管理大量信息。就像图书馆管理员整理书籍一样，数据库帮我们有序地保存数据，需要时能快速找到。",
            "key_points": [
                "用来存储大量结构化数据",
                "提供快速查询和检索功能", 
                "确保数据的安全性和完整性",
                "支持多用户同时访问",
                "可以建立数据之间的关系"
            ],
            "examples": [
                "银行用数据库存储客户账户信息和交易记录",
                "电商网站用数据库管理商品库存和订单信息"
            ]
        }
    }
    
    # 简单的关键词匹配（实际实现中应该使用AI）
    for keyword, explanation in explanations.items():
        if keyword in text:
            return explanation
    
    # 默认解释
    return {
        "explanation": f"这段文本讲述的是关于'{text[:50]}...'的内容。虽然可能比较复杂，但我们可以把它理解为一个特定领域的概念或操作步骤。",
        "key_points": [
            "这是一个专业术语或概念",
            "需要结合具体场景来理解",
            "可能涉及技术或业务流程"
        ],
        "examples": [
            "类似于我们日常生活中的相关场景",
            "在实际应用中的具体体现"
        ]
    }

@router.get("/explain/history")
async def get_explain_history(
    db: Session = Depends(get_db)
):
    """获取用户的解释历史记录"""
    # 实际实现中可以存储用户的解释历史
    return schemas.ApiResponse(
        code="0000", 
        message="获取解释历史成功",
        data={"history": []}
    )