#!/usr/bin/env python3
"""
教学大纲解析器 - 基于Markdown格式的教学大纲提取章节结构
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class ChapterResource:
    """章节配套资源"""
    theory_materials: List[str]  # 理论资料PDF文件
    practice_modules: List[str]  # 微型实验模块
    question_count: int         # 题库题目数量
    
@dataclass
class ChapterInfo:
    """章节信息"""
    number: int
    title: str
    full_title: str  # 完整标题，如"第一章 Python基础入门"
    theory_hours: int
    practice_hours: int
    total_hours: int
    content: List[str]
    objectives: List[str]
    resources: ChapterResource

class SyllabusParser:
    """教学大纲解析器"""
    
    def __init__(self, syllabus_path: Path):
        self.syllabus_path = syllabus_path
        self.content = ""
        if syllabus_path.exists():
            self.content = syllabus_path.read_text(encoding='utf-8')
    
    def parse_chapters(self) -> List[ChapterInfo]:
        """解析所有章节信息"""
        chapters = []
        
        # 匹配章节标题的正则表达式
        chapter_pattern = r'### (第[一二三四五六七八九十]+章)\s+([^（]+)（(\d+)学时）'
        
        # 查找所有章节
        chapter_matches = list(re.finditer(chapter_pattern, self.content))
        
        for i, match in enumerate(chapter_matches):
            chapter_num = self._chinese_to_number(match.group(1))
            chapter_name = match.group(2).strip()
            total_hours = int(match.group(3))
            full_title = f"{match.group(1)} {chapter_name}"
            
            # 提取章节内容（从当前章节到下一章节）
            start_pos = match.start()
            if i + 1 < len(chapter_matches):
                end_pos = chapter_matches[i + 1].start()
                chapter_content = self.content[start_pos:end_pos]
            else:
                chapter_content = self.content[start_pos:]
            
            # 解析章节详细信息
            theory_hours, practice_hours = self._parse_hours(chapter_content)
            teaching_content = self._parse_teaching_content(chapter_content)
            objectives = self._parse_objectives(chapter_content)
            resources = self._parse_resources(chapter_content, chapter_name)
            
            chapter = ChapterInfo(
                number=chapter_num,
                title=chapter_name,
                full_title=full_title,
                theory_hours=theory_hours,
                practice_hours=practice_hours,
                total_hours=total_hours,
                content=teaching_content,
                objectives=objectives,
                resources=resources
            )
            
            chapters.append(chapter)
        
        return chapters
    
    def _chinese_to_number(self, chinese_chapter: str) -> int:
        """将中文章节号转换为数字"""
        chinese_nums = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
        }
        
        # 提取中文数字
        match = re.search(r'第([一二三四五六七八九十]+)章', chinese_chapter)
        if match:
            chinese_num = match.group(1)
            return chinese_nums.get(chinese_num, 1)
        return 1
    
    def _parse_hours(self, chapter_content: str) -> tuple[int, int]:
        """解析理论和实践学时"""
        hours_match = re.search(r'\*\*理论学时：(\d+)\s+实践学时：(\d+)\*\*', chapter_content)
        if hours_match:
            return int(hours_match.group(1)), int(hours_match.group(2))
        return 0, 0
    
    def _parse_teaching_content(self, chapter_content: str) -> List[str]:
        """解析教学内容"""
        content_section = re.search(r'#### 教学内容\n(.*?)(?=####|$)', chapter_content, re.DOTALL)
        if content_section:
            content_text = content_section.group(1).strip()
            # 提取列表项
            items = re.findall(r'^-\s+(.+)$', content_text, re.MULTILINE)
            return items
        return []
    
    def _parse_objectives(self, chapter_content: str) -> List[str]:
        """解析学习要求"""
        objectives_section = re.search(r'#### 学习要求\n(.*?)(?=####|$)', chapter_content, re.DOTALL)
        if objectives_section:
            objectives_text = objectives_section.group(1).strip()
            # 提取列表项
            items = re.findall(r'^-\s+(.+)$', objectives_text, re.MULTILINE)
            return items
        return []
    
    def _parse_resources(self, chapter_content: str, chapter_name: str) -> ChapterResource:
        """解析配套资源"""
        theory_materials = []
        practice_modules = []
        question_count = 0
        
        # 查找配套资源部分
        resources_section = re.search(r'#### 配套资源\n(.*?)(?=---|####|$)', chapter_content, re.DOTALL)
        if resources_section:
            resources_text = resources_section.group(1).strip()
            
            # 解析理论资料
            theory_matches = re.findall(r'\[([^]]+\.pdf)\]', resources_text)
            theory_materials.extend(theory_matches)
            
            # 解析微型实验
            practice_matches = re.findall(r'🎮 \*\*微型实验\*\*:\s*(.+)', resources_text)
            for match in practice_matches:
                if '实践' in match:
                    practice_modules.append(match.strip())
                else:
                    # 处理关卡列表
                    stage_matches = re.findall(r'关卡\d+[：:]\s*([^-\n]+)', resources_text)
                    practice_modules.extend([stage.strip() for stage in stage_matches])
            
            # 解析题库数量
            question_matches = re.findall(r'(\d+)道[选择题判断题]+', resources_text)
            if question_matches:
                question_count = sum(int(num) for num in question_matches)
        
        return ChapterResource(
            theory_materials=theory_materials,
            practice_modules=practice_modules,
            question_count=question_count
        )
    
    def export_structure(self, output_path: Path = None) -> Dict[str, Any]:
        """导出章节结构为JSON格式"""
        chapters = self.parse_chapters()
        
        structure = {
            "course_name": "Python程序设计",
            "total_chapters": len(chapters),
            "total_hours": sum(ch.total_hours for ch in chapters),
            "chapters": []
        }
        
        for chapter in chapters:
            chapter_data = {
                "number": chapter.number,
                "title": chapter.title,
                "full_title": chapter.full_title,
                "hours": {
                    "theory": chapter.theory_hours,
                    "practice": chapter.practice_hours,
                    "total": chapter.total_hours
                },
                "content": chapter.content,
                "objectives": chapter.objectives,
                "resources": {
                    "theory_materials": chapter.resources.theory_materials,
                    "practice_modules": chapter.resources.practice_modules,
                    "question_count": chapter.resources.question_count
                }
            }
            structure["chapters"].append(chapter_data)
        
        if output_path:
            output_path.write_text(json.dumps(structure, ensure_ascii=False, indent=2), encoding='utf-8')
        
        return structure

def main():
    """测试解析器"""
    syllabus_path = Path("/Users/jimfu/Desktop/huixue/backend/ziyuan/课程资源/Python程序设计/01-课程文档/教学大纲.md")
    
    parser = SyllabusParser(syllabus_path)
    chapters = parser.parse_chapters()
    
    print(f"解析到 {len(chapters)} 个章节:")
    for chapter in chapters:
        print(f"\n{chapter.full_title}")
        print(f"  学时: 理论{chapter.theory_hours} + 实践{chapter.practice_hours} = {chapter.total_hours}")
        print(f"  理论资料: {len(chapter.resources.theory_materials)}个")
        print(f"  实践模块: {len(chapter.resources.practice_modules)}个")
        print(f"  题库: {chapter.resources.question_count}道题")
    
    # 导出结构
    output_path = Path("/Users/jimfu/Desktop/huixue/backend/course_structure.json")
    structure = parser.export_structure(output_path)
    print(f"\n结构已导出到: {output_path}")

if __name__ == "__main__":
    main()


