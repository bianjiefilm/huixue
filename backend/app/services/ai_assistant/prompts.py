"""
AI提示词模板管理
包含各种场景的提示词模板
"""


class PromptTemplates:
    """提示词模板类"""
    
    def get_markdown_summary_prompt(self, content: str, course_title: str = "") -> str:
        """获取 Markdown 摘要提示词"""
        title_line = f"课程标题：{course_title}\n" if course_title else ""
        return (
            "你是一位资深的教学教案编辑，请阅读下面的课程教学大纲，并生成一个结构化的摘要，帮助教师快速把握重点并设计课堂活动。\n\n"
            f"{title_line}" +
            "教学大纲内容：\n\n" +
            content +
            "\n\n请严格按照以下 JSON 结构返回（不要包含任何额外文字）：\n"
            "{\n"
            "  \"brief\": \"不超过120字的整体概述\",\n"
            "  \"highlights\": [\n"
            "    { \"title\": \"亮点名称\", \"description\": \"一句话说明亮点价值\", \"tag\": \"可选分类标签\" }\n"
            "  ],\n"
            "  \"suggested_activities\": [\n"
            "    { \"title\": \"课堂活动名称\", \"description\": \"活动目标与基本做法\" }\n"
            "  ]\n"
            "}\n\n"
            "请确保返回的是合法 JSON，中文输出。若发现内容过长，可以只保留 3 条亮点和 2 个课堂活动。"
        )

    def get_grading_prompt(self, question: str, reference_answer: str, 
                           student_answer: str) -> str:
        """
        获取批阅提示词
        """
        return f"""你是一位经验丰富的教师，请认真批阅以下学生作业。

题目：
{question}

参考答案要点：
{reference_answer}

学生答案：
{student_answer}

请按照以下要求进行批阅：
1. 根据学生答案与参考答案的匹配程度，给出0-100的分数
2. 写一句简短的评语（不超过50字）
3. 如果学生答案有不足，给出1-2条具体的改进建议

请严格按照以下JSON格式返回（不要包含其他内容）：
{{
    "score": 分数（0-100的整数）,
    "comment": "评语",
    "suggestions": ["建议1", "建议2"]
}}"""
    
    def get_content_generation_prompt(self, content_type: str, requirements: str) -> str:
        """
        获取内容生成提示词
        """
        templates = {
            "task_description": f"""你是一位资深的计算机教育专家，请根据以下要求创建一个编程任务。

要求：{requirements}

请生成一个完整的任务描述，包含：
1. 任务背景（用故事化的方式引入，让学生更有兴趣）
2. 具体要求（清晰列出需要完成的功能点）
3. 输入输出格式说明
4. 示例（至少包含一个输入输出示例）
5. 提示（给出解题思路提示，但不要直接给出答案）

请用Markdown格式输出，确保结构清晰、易于理解。""",
            
            "test_case": f"""你是一位严谨的测试工程师，请为以下编程任务生成测试用例。

任务描述：{requirements}

请生成5个测试用例，要求：
1. 覆盖正常情况（2个）
2. 覆盖边界情况（2个）
3. 覆盖异常情况（1个）

每个测试用例包含：
- 输入数据
- 预期输出
- 测试目的（简短说明）

请按以下格式输出：
测试用例1：
输入：xxx
输出：xxx
目的：xxx

测试用例2：
...""",
            
            "evaluation_criteria": f"""你是一位教学评估专家，请为以下任务制定评分标准。

任务：{requirements}

请制定详细的评分标准，包括：
1. 功能完成度（40分）
2. 代码质量（30分）
3. 算法效率（20分）
4. 代码规范（10分）

每个维度都要给出具体的评分细则。"""
        }
        
        return templates.get(content_type, f"请根据以下要求生成内容：{requirements}")
    
    def get_code_help_prompt(self, code: str, context: str = None, 
                             error_message: str = None) -> str:
        """
        获取代码辅导提示词
        """
        prompt = f"""你是一位耐心的编程助教，学生遇到了编程问题需要你的帮助。

学生的代码：
```python
{code}
```
"""
        
        if context:
            prompt += f"\n任务要求：{context}\n"
        
        if error_message:
            prompt += f"\n错误信息：{error_message}\n"
            prompt += """
请分析这个错误的原因，并提供调试建议。注意：
1. 用简单易懂的语言解释错误原因
2. 给出具体的调试步骤
3. 提供相关知识点的简要说明
4. 不要直接给出完整的正确代码，而是引导学生自己发现和解决问题
"""
        else:
            prompt += """
请解释这段代码的功能和执行流程。注意：
1. 逐行解释关键代码的作用
2. 说明整体的执行逻辑
3. 指出代码中的优点和可能的改进点
4. 如果发现潜在问题，给出提示但不要直接给出答案
"""
        
        return prompt
    
    def get_concept_explanation_prompt(self, concept: str, context: str = None) -> str:
        """
        获取概念解释提示词
        """
        prompt = f"""你是一位优秀的计算机科学教师，请用通俗易懂的方式解释以下概念。

概念：{concept}
"""
        
        if context:
            prompt += f"\n相关上下文：{context}\n"
        
        prompt += """
请按以下要求解释：
1. 用一个生活中的比喻来说明这个概念
2. 解释这个概念的核心思想（用初学者能理解的语言）
3. 给出一个简单的代码示例（如果适用）
4. 说明这个概念在实际编程中的应用场景

请确保解释简洁明了，适合初学者理解。"""
        
        return prompt
    
    def get_report_check_prompt(self, report_content: str) -> str:
        """
        获取报告检查提示词
        """
        return f"""你是一位严谨的学术写作指导老师，请检查以下实验报告。

报告内容：
{report_content}

请从以下几个方面进行检查：
1. 语言表达：是否通顺、有无错别字和语法错误
2. 结构完整性：是否包含背景介绍、实验过程、结果分析、总结等必要部分
3. 逻辑清晰度：论述是否有条理，结论是否有依据
4. 专业性：专业术语使用是否准确

请给出：
1. 总体评价（优秀/良好/合格/需改进）
2. 具体问题列表（如有）
3. 改进建议（2-3条）

按以下格式输出：
总体评价：xxx
问题：
1. xxx
2. xxx
建议：
1. xxx
2. xxx"""