"""
tutor 学生端 AI 闯关辅导助手

对齐《慧学AI升级方案-v2.md》第十二章「学生端 AI 闯关辅导助手」。

核心安全设计（不可违反）：
- 参考答案 / 隐藏测试集在服务端组装 prompt 时物理排除，不进学生端 context。
  见 context_builder.build_tutor_context 的函数签名 —— 没有 reference_answer /
  hidden_test_cases 参数，调用方物理传不进来，而不是"传了但不用"的软约束。
- AI 回复落地前经 output_filter 做相似度检测，与参考答案高度重合时截断降级。
"""

from .schemas import StudentHintRequest, StudentHintResponse

__all__ = ["StudentHintRequest", "StudentHintResponse"]
