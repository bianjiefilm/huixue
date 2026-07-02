"""
大语言模型调用工具
基于豆包大模型API进行关卡内容生成
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    """大语言模型客户端"""
    
    def __init__(self, api_key: str = None):
        # 密钥只从参数或环境变量读取；模块顶层会实例化本类,
        # 因此缺少密钥时不能在这里抛错,推迟到真正调用 AI 时
        self.api_key = api_key or os.getenv("ARK_API_KEY") or ""
        self._client: Optional[OpenAI] = None
        self.model = "deepseek-v3-250324"

    @property
    def client(self) -> OpenAI:
        if self._client is None:
            if not self.api_key:
                raise RuntimeError("AI 服务未配置: 缺少 ARK_API_KEY 环境变量")
            self._client = OpenAI(
                base_url="https://ark.cn-beijing.volces.com/api/v3",
                api_key=self.api_key,
            )
        return self._client
    
    def generate_course_outline(self, course_content: str, filename: str) -> List[Dict[str, str]]:
        """
        生成课程关卡提纲
        
        Args:
            course_content: 课程文本内容
            filename: 文件名
            
        Returns:
            关卡提纲列表
        """
        
        system_prompt = """你是一位经验丰富的教学设计专家，专门为在线学习平台设计实践关卡。
请根据提供的教学内容，设计一套循序渐进的关卡提纲。

要求：
1. 关卡应该符合学习者的认知规律，从简单到复杂
2. 每个关卡都有明确的学习目标和核心知识点
3. 关卡类型要多样化：实践题、判断题、选择题
4. 难度分布要合理：初级、中级、高级

请返回JSON格式的关卡提纲，每个关卡包含：
- level_title: 关卡标题
- core_knowledge: 核心知识点
- suggested_type: 建议关卡类型（实践题/判断题/选择题）
- difficulty: 难度级别（初级/中级/高级）"""
        
        user_prompt = f"""请为以下教学内容设计关卡提纲：

文件名：{filename}

教学内容：
{course_content}

请生成5-8个关卡的提纲，确保覆盖所有重要知识点。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            logger.info(f"LLM返回的提纲内容: {content}")
            
            # 尝试解析JSON
            try:
                # 提取JSON部分
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "[" in content and "]" in content:
                    json_start = content.find("[")
                    json_end = content.rfind("]") + 1
                    json_content = content[json_start:json_end]
                else:
                    # 如果没有找到JSON格式，尝试解析整个内容
                    json_content = content
                
                outline_data = json.loads(json_content)
                
                # 检查是否是嵌套格式（如 {"关卡提纲": [...]} 或 {"outline": [...]}）
                if isinstance(outline_data, dict):
                    # 尝试常见的嵌套键名
                    for key in ['关卡提纲', 'outline', 'data', 'levels', '提纲']:
                        if key in outline_data and isinstance(outline_data[key], list):
                            return outline_data[key]
                    
                    # 如果没有找到嵌套结构，但是字典包含正确的字段，可能是单个关卡
                    if 'level_title' in outline_data:
                        return [outline_data]
                
                return outline_data
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}, 原始内容: {content}")
                # 返回默认的提纲结构
                return [
                    {
                        "level_title": "基础概念理解",
                        "core_knowledge": "核心概念和基本原理",
                        "suggested_type": "判断题",
                        "difficulty": "初级"
                    },
                    {
                        "level_title": "实际应用练习",
                        "core_knowledge": "知识点的实际应用",
                        "suggested_type": "实践题",
                        "difficulty": "中级"
                    }
                ]
                
        except Exception as e:
            logger.error(f"生成提纲失败: {str(e)}")
            raise Exception(f"生成提纲失败: {str(e)}")
    
    def generate_level_content(self, text_content: str, outline_item: dict) -> Union[dict, List[dict]]:
        """
        基于教学内容和提纲项生成具体的关卡内容
        
        Args:
            text_content: 教学文档的文本内容
            outline_item: 关卡提纲项，包含level_title, core_knowledge, suggested_type, difficulty
            
        Returns:
            实践题返回dict（包含task_markdown和answer_markdown），
            其他题型返回List[dict]（题目列表）
        """
        try:
            level_type = outline_item.get('suggested_type', '实践题')
            
            if level_type == "实践题":
                system_prompt = """你是一位专业的编程教学专家，专门设计实践编程任务。
请根据教学内容和关卡要求，生成一个完整的编程实践任务。

要求：
1. 任务描述要清晰具体，包含明确的输入输出要求
2. 提供完整可运行的参考答案代码
3. 任务难度要符合指定的难度等级
4. 代码注释要详细，便于学习者理解

返回JSON格式：
{
  "task_markdown": "## 任务描述\\n(详细的任务说明...)",
  "answer_markdown": "```python\\n# 参考答案\\n(完整的Python代码)\\n```"
}"""
                
                user_prompt = f"""请为以下关卡设计编程实践任务：

关卡标题：{outline_item.get('level_title', '未知标题')}
核心知识点：{outline_item.get('core_knowledge', '未知知识点')}
难度等级：{outline_item.get('difficulty', '中级')}

教学内容参考：
{text_content}

请生成包含任务描述和参考答案的完整实践任务。"""
                
            else:
                # 选择题、判断题等
                system_prompt = f"""你是一位资深的教学评估专家，专门设计高质量的{level_type}。
请根据教学内容生成3-5道{level_type}，要求：

1. 题目要有层次，覆盖知识点的不同角度
2. 选项设计要有干扰性，但不能误导
3. 答案解析要详细，帮助学习者理解
4. 题目难度要符合指定等级

返回JSON格式数组：
[
  {{
    "question_stem": "题干内容",
    "question_type": "{level_type}",
    "options": ["A. 选项1", "B. 选项2", ...] // 判断题不需要此字段
    "correct_answer": "B" // 或 true/false 对于判断题,
    "analysis": "详细的答案解析"
  }}
]"""
                
                user_prompt = f"""请为以下关卡生成{level_type}：

关卡标题：{outline_item.get('level_title', '未知标题')}
核心知识点：{outline_item.get('core_knowledge', '未知知识点')}
难度等级：{outline_item.get('difficulty', '中级')}

教学内容参考：
{text_content}

请生成3-5道质量高的{level_type}。"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            logger.info(f"LLM返回的关卡内容: {content[:200]}...")
            
            # 解析JSON响应
            try:
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "[" in content and "]" in content:
                    json_start = content.find("[")
                    json_end = content.rfind("]") + 1
                    json_content = content[json_start:json_end]
                elif "{" in content and "}" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_content = content[json_start:json_end]
                else:
                    json_content = content
                
                level_content = json.loads(json_content)
                return level_content
                
            except json.JSONDecodeError as e:
                logger.error(f"关卡内容JSON解析失败: {e}")
                # 返回默认内容
                if level_type == "实践题":
                    return {
                        "task_markdown": f"## {outline_item.get('level_title', '编程练习')}\n\n请完成与{outline_item.get('core_knowledge', '相关知识点')}相关的编程任务。",
                        "answer_markdown": "```python\n# 请编写您的代码\npass\n```"
                    }
                else:
                    return [
                        {
                            "question_stem": f"关于{outline_item.get('core_knowledge', '相关知识点')}，以下说法正确的是？",
                            "question_type": level_type,
                            "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"] if level_type == "选择题" else None,
                            "correct_answer": "A" if level_type == "选择题" else True,
                            "analysis": "这是一个示例题目，请根据具体内容进行学习。"
                        }
                    ]
                
        except Exception as e:
            logger.error(f"生成关卡内容失败: {str(e)}")
            raise Exception(f"生成关卡内容时发生错误: {str(e)}")

    def generate_course_metadata(self, course_title: str, syllabus_text: str, file_manifest: str) -> dict:
        """
        生成课程元数据 (practice_info.json)
        
        Args:
            course_title: 课程标题
            syllabus_text: 教学大纲文本
            file_manifest: 文件清单
            
        Returns:
            dict: 包含课程元数据的字典
        """
        try:
            system_prompt = """你是一位经验丰富的课程设计师，专门为在线学习平台配置课程元数据。
请根据我提供的文件清单和课程概述，生成一个符合平台规范的practice_info.json元数据文件。

要求：
1. 严格按照指定的JSON结构和键名输出
2. "introduction"字段需要根据课程概述内容，撰写一段约100字的、吸引人的课程介绍
3. "category"的二级分类请从教学方案中推断
4. "config"部分使用默认值
5. 根据课程内容判断合适的难度等级

输出格式严格按照以下JSON结构：
{
  "practice_name": "(课程名称)",
  "practice_type": "在线编码实践",
  "introduction": "(由你生成的课程介绍)",
  "difficulty": "(初级/中级/高级)",
  "category": {
    "primary": "计算机基础",
    "secondary": ["(从教学方案推断)", "(技术栈相关)"]
  },
  "environment_id": "python-3.9-standard",
  "config": {
    "allow_skip": true,
    "editor_enabled": true,
    "shell_enabled": true,
    "repo_visible": true
  }
}"""
            
            user_prompt = f"""请为以下课程生成元数据：

课程名称：{course_title}

教学大纲/方案内容：
{syllabus_text}

文件清单：
{file_manifest}

请生成完整的practice_info.json内容。"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            logger.info(f"LLM返回的元数据内容: {content}")
            
            # 解析JSON响应
            try:
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "{" in content and "}" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_content = content[json_start:json_end]
                else:
                    json_content = content
                
                metadata = json.loads(json_content)
                return metadata
                
            except json.JSONDecodeError as e:
                logger.error(f"元数据JSON解析失败: {e}")
                # 返回默认元数据
                return {
                    "practice_name": course_title,
                    "practice_type": "在线编码实践",
                    "introduction": f"本课程《{course_title}》旨在帮助学习者掌握相关技能，通过理论学习与实践相结合的方式，培养实际问题解决能力。",
                    "difficulty": "初级",
                    "category": {
                        "primary": "计算机基础",
                        "secondary": ["程序设计", "Python语言"]
                    },
                    "environment_id": "python-3.9-standard",
                    "config": {
                        "allow_skip": True,
                        "editor_enabled": True,
                        "shell_enabled": True,
                        "repo_visible": True
                    }
                }
                
        except Exception as e:
            logger.error(f"生成课程元数据失败: {str(e)}")
            raise Exception(f"生成课程元数据时发生错误: {str(e)}")

    def generate_evaluation_assets(self, task_markdown: str, answer_code: str) -> dict:
        """
        生成评测资源 (judge.py 和 tests.json)
        
        Args:
            task_markdown: 任务描述的Markdown内容
            answer_code: 参考答案代码
            
        Returns:
            dict: 包含judge_script和test_cases的字典
        """
        try:
            system_prompt = """你是一位自动化测试专家，专门为编程实践任务生成评测脚本和测试用例。

请根据任务描述和参考答案，生成以下两部分内容：
1. judge.py - 自动评测脚本
2. tests.json - 测试用例集合

要求：
1. judge.py要能够正确评测学生代码的输出
2. 测试用例要覆盖正常情况、边界情况和异常情况
3. 至少生成5-8个测试用例
4. 测试用例要有可见和隐藏两种类型

返回JSON格式：
{
  "judge_script": "完整的judge.py代码内容",
  "test_cases": [
    {
      "input": "输入数据",
      "expected_output": "期望输出",
      "is_hidden": false,
      "match_rule": "完全匹配"
    }
  ]
}"""
            
            user_prompt = f"""请为以下编程任务生成评测资源：

任务描述：
{task_markdown}

参考答案代码：
{answer_code}

请生成完整的judge.py脚本和测试用例集合。"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            content = response.choices[0].message.content
            logger.info(f"LLM返回的评测资源: {content[:200]}...")
            
            # 解析JSON响应
            try:
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "{" in content and "}" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_content = content[json_start:json_end]
                else:
                    json_content = content
                
                evaluation_assets = json.loads(json_content)
                return evaluation_assets
                
            except json.JSONDecodeError as e:
                logger.error(f"评测资源JSON解析失败: {e}")
                # 返回默认评测资源
                return {
                    "judge_script": """import sys
import json

def judge_solution(student_code, test_case):
    \"\"\"评测学生代码\"\"\"
    try:
        # 执行学生代码
        exec_globals = {}
        exec(student_code, exec_globals)
        
        # 这里需要根据具体任务调整评测逻辑
        # 示例：假设学生需要实现一个函数
        if 'main' in exec_globals:
            result = exec_globals['main'](test_case['input'])
            return str(result) == test_case['expected_output']
        return False
    except Exception as e:
        return False

if __name__ == "__main__":
    # 读取学生代码和测试用例
    student_code = sys.stdin.read()
    # 这里应该加载具体的测试逻辑
    print("评测完成")""",
                    "test_cases": [
                        {
                            "input": "测试输入",
                            "expected_output": "期望输出",
                            "is_hidden": False,
                            "match_rule": "完全匹配"
                        }
                    ]
                }
                
        except Exception as e:
            logger.error(f"生成评测资源失败: {str(e)}")
            raise Exception(f"生成评测资源时发生错误: {str(e)}")

    def generate_exam_questions(self, content_text: str, num_single: int, num_multiple: int, num_true_false: int) -> list:
        """
        生成考核试题 (questions.json)
        
        Args:
            content_text: 教学章节的文本内容
            num_single: 单选题数量
            num_multiple: 多选题数量
            num_true_false: 判断题数量
            
        Returns:
            list: 包含所有试题的列表
        """
        try:
            system_prompt = f"""你是一位专业的教学评估专家，专门设计高质量的考核试题。
请根据教学内容生成以下数量的试题：
- 单选题：{num_single}道
- 多选题：{num_multiple}道  
- 判断题：{num_true_false}道

要求：
1. 题目要有层次，覆盖知识点的不同角度和难度
2. 选项设计要有合理的干扰性，但不能误导
3. 多选题的正确答案可以是2-4个选项
4. 答案解析要详细，帮助学习者理解
5. 题目要基于提供的教学内容

返回JSON格式数组：
[
  {{
    "question_stem": "题干内容",
    "question_type": "单选题", // 或 "多选题", "判断题"
    "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"], // 判断题不需要此字段
    "correct_answer": ["B"], // 单选题用单个元素数组，多选题用多个元素，判断题直接用true/false
    "analysis": "详细的答案解析"
  }}
]"""
            
            user_prompt = f"""请基于以下教学内容生成考核试题：

教学内容：
{content_text}

请严格按照要求生成指定数量的各类题型，确保题目质量高且覆盖面广。"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            logger.info(f"LLM返回的考核试题: {content[:200]}...")
            
            # 解析JSON响应
            try:
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "[" in content and "]" in content:
                    json_start = content.find("[")
                    json_end = content.rfind("]") + 1
                    json_content = content[json_start:json_end]
                else:
                    json_content = content
                
                questions = json.loads(json_content)
                return questions
                
            except json.JSONDecodeError as e:
                logger.error(f"考核试题JSON解析失败: {e}")
                # 返回默认试题
                default_questions = []
                
                # 添加单选题
                for i in range(num_single):
                    default_questions.append({
                        "question_stem": f"关于教学内容的单选题 {i+1}",
                        "question_type": "单选题",
                        "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                        "correct_answer": ["A"],
                        "analysis": "这是一道示例单选题，请根据具体教学内容学习。"
                    })
                
                # 添加多选题
                for i in range(num_multiple):
                    default_questions.append({
                        "question_stem": f"关于教学内容的多选题 {i+1}",
                        "question_type": "多选题",
                        "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
                        "correct_answer": ["A", "B"],
                        "analysis": "这是一道示例多选题，请根据具体教学内容学习。"
                    })
                
                # 添加判断题
                for i in range(num_true_false):
                    default_questions.append({
                        "question_stem": f"关于教学内容的判断题 {i+1}",
                        "question_type": "判断题",
                        "correct_answer": True,
                        "analysis": "这是一道示例判断题，请根据具体教学内容学习。"
                    })
                
                return default_questions
                
        except Exception as e:
            logger.error(f"生成考核试题失败: {str(e)}")
            raise Exception(f"生成考核试题时发生错误: {str(e)}")

    def generate_training_metadata(self, training_title: str, analysis_goals: List[str], training_type: str, sql_content: str) -> Dict[str, Any]:
        """
        生成实训元数据
        
        Args:
            training_title: 实训标题
            analysis_goals: 分析目标列表
            training_type: 实训类型（拖拽式/编码式）
            sql_content: SQL文件内容
            
        Returns:
            实训元数据字典
        """
        
        system_prompt = """你是一位资深的实训项目设计专家，专门为企业级数据分析实训项目设计元数据。
请根据提供的实训信息和SQL数据结构，生成完整的实训元数据。

要求：
1. introduction应该详细描述实训背景、目标和预期收获
2. industry要准确反映业务领域
3. difficulty要根据数据复杂度和分析要求合理评估
4. duration_hours要考虑实际操作时间
5. homework_nodes要设计合理的作业节点
6. require_report根据实训性质决定是否需要报告

请返回JSON格式的元数据，包含：
- training_name: 实训名称
- introduction: 详细介绍（200-300字）
- industry: 所属行业
- difficulty: 难度等级（初级/中级/高级）
- duration_hours: 预计学时（整数）
- training_type: 实训类型
- homework_nodes: 作业节点配置数组
- require_report: 是否需要实验报告（布尔值）"""
        
        user_prompt = f"""请为以下实训项目生成元数据：

实训标题：{training_title}
分析目标：{'; '.join(analysis_goals)}
实训类型：{training_type}

SQL数据结构：
{sql_content[:2000]}  # 限制长度避免token超限

请根据这些信息生成完整的实训元数据。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            logger.info(f"LLM返回的实训元数据: {content}")
            
            # 解析JSON
            try:
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_content = content[json_start:json_end].strip()
                elif "{" in content and "}" in content:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    json_content = content[json_start:json_end]
                else:
                    json_content = content
                
                metadata = json.loads(json_content)
                return metadata
                
            except json.JSONDecodeError as e:
                logger.error(f"实训元数据JSON解析失败: {e}")
                # 返回默认元数据
                return {
                    "training_name": training_title,
                    "introduction": f"本实训项目基于真实业务场景，通过数据分析实践，培养学员的数据洞察能力。主要分析目标包括：{'; '.join(analysis_goals)}。",
                    "industry": "综合",
                    "difficulty": "中级",
                    "duration_hours": 8,
                    "training_type": training_type,
                    "homework_nodes": [
                        {
                            "name": f"{training_title}作战室",
                            "tool": "BI" if training_type == "拖拽式" else "Jupyter",
                            "require_design_file": training_type == "拖拽式"
                        }
                    ],
                    "require_report": True
                }
                
        except Exception as e:
            logger.error(f"生成实训元数据失败: {str(e)}")
            raise Exception(f"生成实训元数据时发生错误: {str(e)}")

    def generate_training_handbook(self, training_title: str, analysis_goals: List[str], sql_content: str, metadata_intro: str) -> str:
        """
        生成实训手册
        
        Args:
            training_title: 实训标题
            analysis_goals: 分析目标列表
            sql_content: SQL文件内容
            metadata_intro: 元数据中的介绍
            
        Returns:
            Markdown格式的实训手册
        """
        
        system_prompt = """你是一位专业的实训手册编写专家，擅长将复杂的数据分析项目转化为清晰易懂的操作指南。
请根据提供的实训信息和数据结构，编写完整的实训手册。

手册结构要求：
1. 项目背景与目标（结合metadata介绍）
2. 数据源说明（基于SQL结构分析）
3. 操作步骤（详细的分析流程）
4. 作业提交要求
5. 评分标准

写作要求：
- 使用Markdown格式
- 语言专业但易懂
- 步骤清晰，逻辑性强
- 包含具体的操作指导
- 字数控制在1500-2500字"""
        
        user_prompt = f"""请为以下实训项目编写手册：

实训标题：{training_title}
分析目标：{'; '.join(analysis_goals)}
项目介绍：{metadata_intro}

数据结构（SQL）：
{sql_content[:3000]}  # 限制长度

请编写一份完整的实训手册，包含背景介绍、数据说明、操作步骤、提交要求和评分标准。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            logger.info(f"LLM返回的实训手册长度: {len(content)}")
            
            # 如果内容被Markdown代码块包围，提取出来
            if "```markdown" in content:
                markdown_start = content.find("```markdown") + 11
                markdown_end = content.find("```", markdown_start)
                return content[markdown_start:markdown_end].strip()
            elif content.startswith("```") and content.endswith("```"):
                # 去除首尾的代码块标记
                lines = content.split('\n')
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].strip() == "```":
                    lines = lines[:-1]
                return '\n'.join(lines)
            else:
                return content
                
        except Exception as e:
            logger.error(f"生成实训手册失败: {str(e)}")
            # 返回默认手册模板
            return f"""# 实训手册：{training_title}

## 1. 项目背景与目标

{metadata_intro}

主要分析目标：
{chr(10).join([f"- {goal}" for goal in analysis_goals])}

## 2. 数据源说明

本实训使用真实业务数据，包含多个数据表，涵盖了企业运营的各个方面。

## 3. 操作步骤

### 步骤1：数据探索
- 了解数据表结构
- 分析数据质量和完整性

### 步骤2：数据分析
- 根据分析目标制定分析方案
- 使用相应工具进行数据可视化

### 步骤3：结果总结
- 生成分析报告
- 提出业务建议

## 4. 作业提交要求

请按照实训要求完成所有分析任务，并提交相应的成果文件。

## 5. 评分标准

- 分析思路清晰（30%）
- 操作规范准确（40%）
- 结果解读合理（30%）
""" 