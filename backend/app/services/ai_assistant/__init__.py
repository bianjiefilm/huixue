"""
AI助教服务模块
提供AI辅助教学功能，包括批阅助手、内容生成、代码辅导等
"""

from .ai_service import AIService
from .prompts import PromptTemplates

__all__ = ['AIService', 'PromptTemplates']