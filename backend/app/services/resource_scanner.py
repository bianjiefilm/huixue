"""
智能资源扫描器 - 动态发现和解析教学资源
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

from app.utils.resource_scanner_helpers import (
    detect_resource_type as _detect_resource_type,
    standardize_course_data as _standardize_course_data,
    extract_bi_stages as _extract_bi_stages,
    item_to_stage as _item_to_stage,
    intelligent_extraction as _intelligent_extraction,
    parse_bi_project_data as _parse_bi_project_data,
    parse_directory_name as _parse_directory_name,
    result_key_for_type as _result_key_for_type,
)

logger = logging.getLogger(__name__)


class IntelligentResourceScanner:
    """智能资源扫描器 - 自适应解析各种格式的资源文件"""

    def __init__(self, base_path: str = "ziyuan"):
        self.base_path = Path(base_path)
        self.resource_patterns = {
            "course": ["课程资源", "课程资料"],
            "practice": ["实践资源", "微型实验", "实训资源"],
            "training": ["实训", "训练"],
            "material": ["教材", "教学材料"],
            "question": ["题库", "习题", "考试"]
        }

    def scan_all_resources(self) -> Dict[str, List[Dict]]:
        """扫描所有资源"""
        results = {
            "courses": [],
            "practices": [],
            "trainings": [],
            "materials": [],
            "questions": []
        }

        # 递归扫描目录
        for root, dirs, files in os.walk(self.base_path):
            root_path = Path(root)

            # 检测资源类型
            resource_type = self._detect_resource_type(root_path)
            if not resource_type:
                continue

            # 扫描course_data.json
            if "course_data.json" in files:
                resource_data = self._parse_course_data(root_path / "course_data.json")
                if resource_data:
                    resource_data["path"] = str(root_path)
                    resource_data["type"] = resource_type
                    self._add_to_results(results, resource_type, resource_data)

            # 扫描Python实践文件
            elif "student.py" in files or "test_evaluator.py" in files:
                practice_data = self._parse_practice_files(root_path)
                if practice_data:
                    results["practices"].append(practice_data)

            # 扫描README.md
            elif "README.md" in files:
                readme_data = self._parse_readme(root_path / "README.md")
                if readme_data:
                    readme_data["path"] = str(root_path)
                    readme_data["type"] = resource_type
                    self._add_to_results(results, resource_type, readme_data)

        return results

    def _detect_resource_type(self, path: Path) -> Optional[str]:
        """检测资源类型"""
        return _detect_resource_type(str(path), self.resource_patterns)

    def _parse_course_data(self, file_path: Path) -> Optional[Dict]:
        """智能解析course_data.json - 支持多种格式"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 标准格式
            if "title" in data or "name" in data:
                return self._standardize_course_data(data)

            # BI项目格式 (如某零售企业经营分析)
            elif "projectTitle" in data:
                return self._parse_bi_project(data, file_path)

            # 数组格式
            elif isinstance(data, list) and len(data) > 0:
                return self._parse_array_format(data, file_path)

            # 其他格式 - 尝试智能提取
            else:
                return self._intelligent_extraction(data, file_path)

        except Exception as e:
            logger.warning(f"解析文件失败 {file_path}: {e}")
            # 从目录名推断信息
            return self._infer_from_directory(file_path.parent)

    def _standardize_course_data(self, data: Dict) -> Dict:
        """标准化课程数据"""
        return _standardize_course_data(data)

    def _parse_bi_project(self, data: Dict, file_path: Path) -> Dict:
        """解析BI项目格式"""
        return _parse_bi_project_data(data, file_path.parent.name)

    def _extract_bi_stages(self, data: Dict) -> List[Dict]:
        """从BI项目数据中提取关卡"""
        return _extract_bi_stages(data)

    def _parse_array_format(self, data: List, file_path: Path) -> Dict:
        """解析数组格式的数据"""
        # 假设第一个元素包含课程信息
        first_item = data[0] if data else {}

        return {
            "title": first_item.get("name", file_path.parent.name),
            "description": first_item.get("description", ""),
            "type": "course",
            "difficulty": "beginner",
            "duration": 60,
            "topics": [],
            "stages": [self._item_to_stage(item) for item in data],
            "resources": [],
            "metadata": {"items": data}
        }

    def _item_to_stage(self, item: Dict) -> Dict:
        """将列表项转换为关卡"""
        return _item_to_stage(item)

    def _intelligent_extraction(self, data: Dict, file_path: Path) -> Dict:
        """智能提取课程信息"""
        fallback_type = self._detect_resource_type(file_path.parent) or "course"
        return _intelligent_extraction(data, file_path.parent.name, fallback_type)

    def _infer_from_directory(self, directory: Path) -> Dict:
        """从目录结构推断课程信息"""
        name = directory.name

        # 尝试解析编号和名称
        _number, title = _parse_directory_name(name)

        # 扫描子目录作为关卡
        stages = []
        for subdir in directory.iterdir():
            if subdir.is_dir():
                stage_match = re.match(r"关卡(\d+)-(.+)", subdir.name)
                if stage_match:
                    stages.append({
                        "order": int(stage_match.group(1)),
                        "title": stage_match.group(2),
                        "path": str(subdir)
                    })

        return {
            "title": title,
            "description": f"从目录 {name} 推断的课程",
            "type": self._detect_resource_type(directory) or "course",
            "difficulty": "beginner",
            "duration": 60,
            "topics": [],
            "stages": sorted(stages, key=lambda x: x.get("order", 999)),
            "resources": [],
            "inferred": True
        }

    def _parse_practice_files(self, directory: Path) -> Optional[Dict]:
        """解析实践文件（student.py, test_evaluator.py）"""
        practice_data = {
            "title": directory.name,
            "type": "practice",
            "path": str(directory),
            "files": {}
        }

        # 读取student.py
        student_file = directory / "student.py"
        if student_file.exists():
            with open(student_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 提取函数定义
                functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', content)
                practice_data["student_functions"] = functions
                practice_data["files"]["student"] = str(student_file)

        # 读取test_evaluator.py
        test_file = directory / "test_evaluator.py"
        if test_file.exists():
            practice_data["files"]["test"] = str(test_file)

        # 读取README.md
        readme_file = directory / "README.md"
        if readme_file.exists():
            readme_data = self._parse_readme(readme_file)
            practice_data.update(readme_data)

        return practice_data if practice_data["files"] else None

    def _parse_readme(self, file_path: Path) -> Dict:
        """解析README文件提取课程信息"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取标题
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            title = title_match.group(1) if title_match else file_path.parent.name

            # 提取描述（第一段非标题文本）
            desc_match = re.search(r'^[^#\n]+', content, re.MULTILINE)
            description = desc_match.group(0) if desc_match else ""

            # 提取任务列表
            tasks = re.findall(r'[-*]\s+(.+)', content)

            return {
                "title": title,
                "description": description.strip(),
                "tasks": tasks,
                "has_readme": True
            }
        except Exception as e:
            logger.warning(f"解析README失败 {file_path}: {e}")
            return {}

    def _add_to_results(self, results: Dict, resource_type: str, data: Dict):
        """添加到结果集"""
        key = _result_key_for_type(resource_type)
        results[key].append(data)

    def generate_standard_course_data(self, resource_info: Dict, output_path: Path):
        """生成标准格式的course_data.json"""
        standard_data = {
            "title": resource_info.get("title", "未命名课程"),
            "description": resource_info.get("description", ""),
            "type": resource_info.get("type", "course"),
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "difficulty": resource_info.get("difficulty", "beginner"),
            "duration": resource_info.get("duration", 60),
            "topics": resource_info.get("topics", []),
            "prerequisites": [],
            "objectives": [],
            "stages": resource_info.get("stages", []),
            "resources": resource_info.get("resources", []),
            "evaluation": {
                "type": "auto",
                "passing_score": 60
            }
        }

        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(standard_data, f, ensure_ascii=False, indent=2)

        return standard_data