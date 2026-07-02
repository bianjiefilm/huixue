#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python程序设计课程监测系统 (MCP视角)

监测维度:
1. 资产维度 - 大纲映射检查 (9个核心知识点代码覆盖)
2. 技术维度 - Python 3纯度检查 (Py2遗留代码检测)
3. 逻辑维度 - 在线执行友好性检查 (GUI依赖、死循环风险)

三大结束标志:
- 标志1: Python 3语法合规率100%
- 标志2: UTF-8编码统一
- 标志3: 9大模块代码全覆盖

使用方法:
    python3 monitor_python_course.py [--course-path PATH] [--output OUTPUT]
"""

import argparse
import ast
import chardet
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# 章节定义 (基于metadata.json中的practices)
# ============================================================================

CHAPTERS = {
    "ch01": {"name": "Python概述", "dirs": ["01-Python语言概述", "01-Python概述"]},
    "ch02": {"name": "基础语法", "dirs": ["02-基础语法"]},
    "ch03": {"name": "控制结构", "dirs": ["03-程序控制结构", "03-Python流程控制"]},
    "ch04": {"name": "序列", "dirs": ["04-列表与元组", "04-Python数据结构"]},
    "ch05": {"name": "字符串", "dirs": ["05-字典与集合", "05-Python字符串"]},
    "ch06": {"name": "函数", "dirs": ["06-字符串处理", "06-Python函数"]},
    "ch07": {"name": "面向对象", "dirs": ["07-函数定义与使用", "07-Python面向对象"]},
    "ch08": {"name": "模块", "dirs": ["08-面向对象编程", "08-Python模块与包"]},
    "ch09": {"name": "异常处理", "dirs": ["09-模块与包", "09-Python异常处理"]},
}

# Python 2 红线特征 (语法特征扫描)
PY2_PATTERNS = [
    (r'print\s+[^(]', "print无括号 (Python 2)"),
    (r'raw_input\s*\(', "raw_input (Python 2)"),
    (r'except\s+\w+\s*,\s*\w+\s*:', "旧式异常捕获 except Exception, e:"),
    (r'#.*coding:\s*gbk', "GBK编码声明"),
    (r'#.*coding:\s*gb2312', "GB2312编码声明"),
    (r'#.*coding:\s*gb18030', "GB18030编码声明"),
    (r'\bfile\s*\(', "file()函数 (Python 2)"),
    (r'^\s*unicode\s*\(', "unicode()函数 (Python 2)"),
    (r'\{\%\s*(?:for|if)', "Django模板语法 (Py2倾向)"),
    (r'\{0\[', "旧式格式化字符串"),
    (r'print\s+"[^"]*"\s*%', "print % 格式化 (Py2)"),
]

# GUI阻断检测
GUI_LIBRARIES = ['turtle', 'tkinter', 'pygame', 'PyQt', 'PySide', 'wx', ' PyQt4', 'PyQt5']

# 默认课程路径
DEFAULT_COURSE_PATH = "/Users/jimfu/Work/huixue/ziyuan_data/课程资源/Python程序设计"
DEFAULT_OUTPUT_PATH = "/Users/jimfu/Work/huixue/frontend/public/python-monitoring-report.html"


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class ChapterCheckResult:
    """章节检查结果"""
    chapter_id: str
    chapter_name: str
    has_code: bool = False
    code_type: Optional[str] = None  # "py", "ipynb", or None
    py_file_count: int = 0
    ipynb_file_count: int = 0
    empty: bool = True


@dataclass
class SyntaxCheckResult:
    """语法检查结果"""
    file_path: str
    is_valid: bool = True
    py2_legacy_count: int = 0
    issues: List[str] = field(default_factory=list)


@dataclass
class EncodingCheckResult:
    """编码检查结果"""
    file_path: str
    detected_encoding: str
    is_utf8: bool = True
    has_bom: bool = False


@dataclass
class ExecutionRiskResult:
    """执行风险检查结果"""
    file_path: str
    has_gui_import: bool = False
    gui_libs: List[str] = field(default_factory=list)
    has_infinite_loop_risk: bool = False
    loop_count: int = 0


@dataclass
class PythonCourseMonitorReport:
    """Python课程监测报告"""
    timestamp: str = ""
    course_name: str = "Python程序设计"

    # 维度1: 资产覆盖
    chapters: Dict[str, ChapterCheckResult] = field(default_factory=dict)
    empty_chapter_count: int = 0
    coverage_rate: float = 0.0

    # 维度2: 语法纯度
    syntax_results: List[SyntaxCheckResult] = field(default_factory=list)
    py2_legacy_count: int = 0
    syntax_passed: bool = True

    # 维度3: 执行友好性
    execution_risks: List[ExecutionRiskResult] = field(default_factory=list)
    gui_risk_count: int = 0
    infinite_loop_count: int = 0

    # 编码检查
    encoding_results: List[EncodingCheckResult] = field(default_factory=list)
    encoding_issues: List[str] = field(default_factory=list)
    encoding_passed: bool = True

    # 文件统计
    total_py_files: int = 0
    total_ipynb_files: int = 0
    total_md_files: int = 0

    # 三大标志
    syntax_signal: bool = False  # 标志1: Python 3语法合规
    encoding_signal: bool = False  # 标志2: UTF-8编码
    coverage_signal: bool = False  # 标志3: 9模块覆盖
    all_passed: bool = False

    # 综合状态
    @property
    def status(self) -> str:
        if self.all_passed:
            return "已封版"
        elif self.syntax_passed and self.coverage_rate >= 80:
            return "待完善"
        else:
            return "需修复"


# ============================================================================
# 监测器类
# ============================================================================

class PythonCourseMonitor:
    """Python程序设计课程监测器"""

    def __init__(self, course_path: str):
        self.course_path = Path(course_path)
        self.report = PythonCourseMonitorReport()
        self.report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 编译正则表达式
        self.py2_patterns = [(re.compile(p), msg) for p, msg in PY2_PATTERNS]
        self.loop_pattern = re.compile(r'while\s+(True|1)\s*:')
        self.break_pattern = re.compile(r'while\s+(True|1)\s*:.*?break', re.DOTALL)
        self.gbk_pattern = re.compile(r'#.*coding:\s*gbk', re.IGNORECASE)

    def run_full_scan(self) -> PythonCourseMonitorReport:
        """执行完整扫描"""
        print("=" * 60)
        print(">>> 开始 Python程序设计课程监测")
        print("=" * 60)

        # 维度1: 资产覆盖检查
        print("\n[1/4] 检查9大模块代码覆盖...")
        self._check_chapter_coverage()
        print(f"      覆盖统计: {self.report.coverage_rate:.1f}%, 空缺章节: {self.report.empty_chapter_count}")

        # 维度2: Python 3纯度检查
        print("\n[2/4] 检测Python 2遗留代码...")
        self._check_python2_legacy()
        print(f"      Py2遗留: {self.report.py2_legacy_count} 处")

        # 维度3: 编码检查
        print("\n[3/4] 检查文件编码...")
        self._check_encoding()
        print(f"      编码问题: {len(self.report.encoding_issues)} 个")

        # 维度4: 执行友好性检查
        print("\n[4/4] 检测在线执行友好性...")
        self._check_execution_friendliness()
        print(f"      GUI风险: {self.report.gui_risk_count}, 死循环风险: {self.report.infinite_loop_count}")

        # 计算三大标志
        self._calculate_completion_signals()

        # 打印结果摘要
        self._print_summary()

        return self.report

    def _check_chapter_coverage(self):
        """检查章节代码覆盖"""
        notebooks_dir = self.course_path / "notebooks"
        chapters_dir = self.course_path / "chapters"

        # 初始化章节结果
        for ch_id, ch_info in CHAPTERS.items():
            self.report.chapters[ch_id] = ChapterCheckResult(
                chapter_id=ch_id,
                chapter_name=ch_info["name"]
            )

        # 检查notebooks目录
        if notebooks_dir.exists():
            for notebook in notebooks_dir.glob("*.ipynb"):
                # 从文件名推断章节
                content = self._read_file_content(notebook)
                if content:
                    result = self._analyze_notebook_content(content, notebook.name)
                    for ch_id, chapter in self.report.chapters.items():
                        if result.get(ch_id) and not chapter.has_code:
                            chapter.has_code = True
                            chapter.ipynb_file_count += 1
                            chapter.code_type = "ipynb"

        # 检查chapters目录中的.py文件
        if chapters_dir.exists():
            for chapter_dir in chapters_dir.iterdir():
                if chapter_dir.is_dir():
                    # 匹配章节
                    matched_ch_id = None
                    for ch_id, ch_info in CHAPTERS.items():
                        for dir_name in ch_info["dirs"]:
                            if dir_name in chapter_dir.name:
                                matched_ch_id = ch_id
                                break
                        if matched_ch_id:
                            break

                    if matched_ch_id:
                        py_files = list(chapter_dir.rglob("*.py"))
                        if py_files:
                            self.report.chapters[matched_ch_id].has_code = True
                            self.report.chapters[matched_ch_id].code_type = "py"
                            self.report.chapters[matched_ch_id].py_file_count = len(py_files)

        # 统计文件
        self.report.total_py_files = len(list(self.course_path.rglob("*.py")))
        self.report.total_ipynb_files = len(list(self.course_path.rglob("*.ipynb")))
        self.report.total_md_files = len(list(self.course_path.rglob("*.md")))

        # 计算覆盖率
        complete_count = sum(1 for ch in self.report.chapters.values() if ch.has_code)
        self.report.empty_chapter_count = len(CHAPTERS) - complete_count
        self.report.coverage_rate = round(complete_count / len(CHAPTERS) * 100, 1)

    def _analyze_notebook_content(self, content: str, filename: str) -> Dict[str, bool]:
        """分析notebook内容确定章节对应关系"""
        result = {}

        # 从notebook单元格中提取关键词
        keywords_by_chapter = {
            "ch01": ["Python概述", "Python简介", "Python语言", "# 第1章"],
            "ch02": ["变量", "数据类型", "运算符", "# 第2章", "# 第3章"],
            "ch03": ["控制结构", "if", "elif", "else", "for", "while", "# 第3章"],
            "ch04": ["列表", "list", "元组", "tuple", "# 第4章"],
            "ch05": ["字典", "dict", "集合", "set", "# 第5章"],
            "ch06": ["字符串", "str", "string", "# 第6章"],
            "ch07": ["函数", "def", "return", "# 第7章"],
            "ch08": ["面向对象", "class", "对象", "OOP", "# 第8章"],
            "ch09": ["异常", "try", "except", "# 第9章"],
        }

        for ch_id, keywords in keywords_by_chapter.items():
            for keyword in keywords:
                if keyword in content:
                    result[ch_id] = True
                    break

        return result

    def _check_python2_legacy(self):
        """检测Python 2遗留代码"""
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))

        # 检查.py文件
        for py_file in py_files:
            result = self._check_file_python2_legacy(py_file)
            if result:
                self.report.syntax_results.append(result)
                if result.py2_legacy_count > 0:
                    self.report.py2_legacy_count += result.py2_legacy_count

        # 检查.ipynb文件中的代码
        for ipynb_file in ipynb_files:
            result = self._check_notebook_python2_legacy(ipynb_file)
            if result and result.py2_legacy_count > 0:
                self.report.syntax_results.append(result)
                self.report.py2_legacy_count += result.py2_legacy_count

        self.report.syntax_passed = self.report.py2_legacy_count == 0

    def _check_file_python2_legacy(self, filepath: Path) -> Optional[SyntaxCheckResult]:
        """检查单个.py文件的Python 2遗留"""
        try:
            content = self._read_file_content(filepath)
            if not content:
                return None

            result = SyntaxCheckResult(file_path=str(filepath))
            issues = []

            # 检测Py2模式
            for pattern, msg in self.py2_patterns:
                matches = pattern.findall(content)
                if matches:
                    result.py2_legacy_count += len(matches)
                    issues.append(f"{msg}: {len(matches)}处")

            # 尝试ast解析
            try:
                ast.parse(content)
            except SyntaxError as e:
                result.is_valid = False
                issues.append(f"SyntaxError: {e}")

            result.issues = issues
            return result

        except Exception as e:
            return SyntaxCheckResult(
                file_path=str(filepath),
                is_valid=False,
                issues=[f"读取错误: {e}"]
            )

    def _check_notebook_python2_legacy(self, filepath: Path) -> Optional[SyntaxCheckResult]:
        """检查.ipynb文件的Python 2遗留"""
        try:
            content = self._read_file_content(filepath)
            if not content:
                return None

            notebook = json.loads(content)
            result = SyntaxCheckResult(file_path=str(filepath))
            issues = []

            # 遍历所有单元格
            for cell in notebook.get("cells", []):
                if cell.get("cell_type") == "code":
                    code = cell.get("source", "")
                    if isinstance(code, list):
                        code = "\n".join(code)

                    for pattern, msg in self.py2_patterns:
                        matches = pattern.findall(code)
                        if matches:
                            result.py2_legacy_count += len(matches)
                            issues.append(f"{msg}: {len(matches)}处")

            result.issues = issues
            return result

        except Exception as e:
            return None

    def _check_encoding(self):
        """检查文件编码"""
        py_files = list(self.course_path.rglob("*.py"))
        md_files = list(self.course_path.rglob("*.md"))

        for py_file in py_files:
            result = self._check_file_encoding(py_file)
            if result:
                self.report.encoding_results.append(result)
                if not result.is_utf8:
                    self.report.encoding_issues.append(f"{py_file}: {result.detected_encoding}")

        for md_file in md_files:
            result = self._check_file_encoding(md_file)
            if result and not result.is_utf8:
                self.report.encoding_results.append(result)
                self.report.encoding_issues.append(f"{md_file}: {result.detected_encoding}")

        self.report.encoding_passed = len(self.report.encoding_issues) == 0

    def _check_file_encoding(self, filepath: Path) -> Optional[EncodingCheckResult]:
        """检查单个文件的编码"""
        try:
            # 读取二进制内容进行检测
            with open(filepath, 'rb') as f:
                raw_data = f.read(10240)  # 读取前10KB

            # 使用chardet检测编码
            detection = chardet.detect(raw_data)
            encoding = detection.get('encoding', 'utf-8')
            confidence = detection.get('confidence', 0)

            # 检查BOM
            has_bom = raw_data.startswith(b'\xef\xbb\xbf')

            # 检查是否是UTF-8
            is_utf8 = encoding == 'utf-8' and confidence > 0.7

            # 检查是否包含GBK编码声明
            try:
                text = raw_data.decode('utf-8', errors='ignore')
                if self.gbk_pattern.search(text):
                    is_utf8 = False
                    encoding = 'gbk'
            except:
                pass

            return EncodingCheckResult(
                file_path=str(filepath),
                detected_encoding=encoding if encoding else 'unknown',
                is_utf8=is_utf8,
                has_bom=has_bom
            )

        except Exception:
            return None

    def _check_execution_friendliness(self):
        """检查在线执行友好性"""
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))

        # 检查.py文件
        for py_file in py_files:
            result = self._check_file_execution_risk(py_file)
            if result:
                self.report.execution_risks.append(result)
                if result.has_gui_import:
                    self.report.gui_risk_count += 1
                if result.has_infinite_loop_risk:
                    self.report.infinite_loop_count += 1

        # 检查.ipynb文件
        for ipynb_file in ipynb_files:
            result = self._check_notebook_execution_risk(ipynb_file)
            if result:
                self.report.execution_risks.append(result)
                if result.has_gui_import:
                    self.report.gui_risk_count += 1
                if result.has_infinite_loop_risk:
                    self.report.infinite_loop_count += 1

    def _check_file_execution_risk(self, filepath: Path) -> Optional[ExecutionRiskResult]:
        """检查单个.py文件的执行风险"""
        try:
            content = self._read_file_content(filepath)
            if not content:
                return None

            result = ExecutionRiskResult(file_path=str(filepath))

            # 检查GUI导入
            for lib in GUI_LIBRARIES:
                pattern = rf'(?:import\s+|from\s+){lib}'
                if re.search(pattern, content, re.IGNORECASE):
                    result.has_gui_import = True
                    result.gui_libs.append(lib)

            # 检查死循环风险
            # 只检测真正无退出条件的循环，如 while True: 后只有 pass 或无操作
            for match in self.loop_pattern.finditer(content):
                loop_body = content[match.start():]
                # 如果循环体只有 pass 或空，则为真正的死循环
                # 排除有 return/break/raise 的正常循环（如输入验证）
                has_exit = (
                    self.break_pattern.search(loop_body) or
                    re.search(r'\breturn\b', loop_body) or
                    re.search(r'\braise\b', loop_body)
                )
                # 跳过以 # 开头或 # 注释的 while True（如演示代码）
                stripped = loop_body.lstrip()
                if stripped.startswith('#'):
                    continue
                if not has_exit and re.match(r'^\s*while\s+True\s*:[\s\n]*$', loop_body.split('\n')[0] + ':'):
                    # 检查循环体是否只有 pass 或空
                    loop_lines = loop_body.split('\n')[1:]
                    for line in loop_lines[:3]:  # 只检查前几行
                        if line.strip() and not line.strip().startswith('#'):
                            if line.strip() in ('pass',):
                                result.has_infinite_loop_risk = True
                                result.loop_count += 1
                                break

            return result

        except Exception:
            return None

    def _check_notebook_execution_risk(self, filepath: Path) -> Optional[ExecutionRiskResult]:
        """检查.ipynb文件的执行风险"""
        try:
            content = self._read_file_content(filepath)
            if not content:
                return None

            notebook = json.loads(content)
            result = ExecutionRiskResult(file_path=str(filepath))

            # 遍历所有代码单元格
            for cell in notebook.get("cells", []):
                if cell.get("cell_type") == "code":
                    code = cell.get("source", "")
                    if isinstance(code, list):
                        code = "\n".join(code)

                    # 检查GUI导入
                    for lib in GUI_LIBRARIES:
                        pattern = rf'(?:import\s+|from\s+){lib}'
                        if re.search(pattern, code, re.IGNORECASE):
                            result.has_gui_import = True
                            if lib not in result.gui_libs:
                                result.gui_libs.append(lib)

                    # 检查死循环
                    # 只检测真正无退出条件的循环，如 while True: 后只有 pass
                    # 排除有 return/break/raise 的正常循环（如输入验证）
                    for match in self.loop_pattern.finditer(code):
                        loop_body = code[match.start():]
                        has_exit = (
                            self.break_pattern.search(loop_body) or
                            re.search(r'\breturn\b', loop_body) or
                            re.search(r'\braise\b', loop_body)
                        )
                        # 跳过注释中的 while True
                        stripped = loop_body.lstrip()
                        if stripped.startswith('#'):
                            continue
                        if not has_exit:
                            # 检查循环体是否只有 pass 或空
                            loop_lines = loop_body.split('\n')[1:]
                            for line in loop_lines[:3]:
                                if line.strip() and not line.strip().startswith('#'):
                                    if line.strip() in ('pass',):
                                        result.has_infinite_loop_risk = True
                                        result.loop_count += 1
                                        break

            return result

        except Exception:
            return None

    def _calculate_completion_signals(self):
        """计算三大结束标志"""
        # 标志1: Python 3语法合规率100%
        self.report.syntax_signal = self.report.syntax_passed

        # 标志2: UTF-8编码统一
        self.report.encoding_signal = self.report.encoding_passed

        # 标志3: 9大模块代码全覆盖
        self.report.coverage_signal = self.report.empty_chapter_count == 0

        # 综合判断
        self.report.all_passed = (
            self.report.syntax_signal and
            self.report.encoding_signal and
            self.report.coverage_signal
        )

    def _print_summary(self):
        """打印结果摘要"""
        print("\n" + "=" * 60)
        print(">>> 监测完成! 三大标志状态:")
        print(f"    标志1 (Python3纯度): {'✅ 通过' if self.report.syntax_signal else '❌ 未通过'}")
        print(f"    标志2 (UTF-8编码): {'✅ 通过' if self.report.encoding_signal else '❌ 未通过'}")
        print(f"    标志3 (9模块覆盖): {'✅ 通过' if self.report.coverage_signal else '❌ 未通过'}")
        print(f"    综合状态: {'✅ 可封版' if self.report.all_passed else '❌ 需修复'}")
        print("=" * 60)

    def _read_file_content(self, filepath: Path) -> Optional[str]:
        """读取文件内容 (支持多编码)"""
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue
        return None

    def export_html_report(self, output_path: str):
        """导出HTML报告"""
        r = self.report

        # 生成问题详情表格
        syntax_issues_html = ""
        for result in r.syntax_results:
            if result.issues:
                status = "⚠️" if result.is_valid else "❌"
                syntax_issues_html += f"""
                    <tr>
                        <td style="padding: 8px; word-break: break-all;">{result.file_path.split('/')[-1]}</td>
                        <td style="padding: 8px;">{status}</td>
                        <td style="padding: 8px; color: #f57c00;">{', '.join(result.issues[:3])}</td>
                    </tr>
                """

        if not syntax_issues_html:
            syntax_issues_html = "<tr><td colspan='3' style='padding: 16px; color: #28a745;'>✅ 无Python 2遗留问题</td></tr>"

        # 生成编码问题表格
        encoding_issues_html = ""
        for issue in r.encoding_issues[:10]:
            encoding_issues_html += f"""
                <tr>
                    <td style="padding: 8px; color: #dc3545;">{issue.split(':')[0]}</td>
                    <td style="padding: 8px; color: #dc3545;">{issue.split(':')[-1].strip() if ':' in issue else '未知'}</td>
                </tr>
            """

        if not encoding_issues_html:
            encoding_issues_html = "<tr><td colspan='2' style='padding: 16px; color: #28a745;'>✅ 所有文件均为UTF-8编码</td></tr>"

        # 生成章节覆盖表格
        chapter_rows = ""
        for ch_id, chapter in r.chapters.items():
            status = "✅" if chapter.has_code else "❌"
            code_info = f"{chapter.code_type.upper()}" if chapter.has_code else "-"
            chapter_rows += f"""
                <tr>
                    <td style="padding: 8px; font-weight: 600;">{chapter.chapter_id}</td>
                    <td style="padding: 8px;">{chapter.chapter_name}</td>
                    <td style="padding: 8px; text-align: center;">{status}</td>
                    <td style="padding: 8px; text-align: center;">{code_info}</td>
                </tr>
            """

        # 生成执行风险详情
        risk_rows = ""
        for risk in r.execution_risks:
            if risk.has_gui_import or risk.has_infinite_loop_risk:
                risk_type = []
                if risk.has_gui_import:
                    risk_type.append(f"GUI({', '.join(risk.gui_libs)})")
                if risk.has_infinite_loop_risk:
                    risk_type.append("死循环风险")
                risk_rows += f"""
                    <tr>
                        <td style="padding: 8px; word-break: break-all;">{risk.file_path.split('/')[-1]}</td>
                        <td style="padding: 8px; color: #f57c00;">{'/'.join(risk_type)}</td>
                    </tr>
                """

        if not risk_rows:
            risk_rows = "<tr><td colspan='2' style='padding: 16px; color: #28a745;'>✅ 无执行风险</td></tr>"

        # 预构建修复建议HTML
        fix_suggestion_html = ""
        if not r.all_passed:
            fix_suggestion_html = """
        <div class="card" style="background: linear-gradient(135deg, #fff3cd, #ffeeba);">
            <h2><span class="card-icon">🔧</span>自动修复建议</h2>
            <div style="margin-top: 12px;">
                <p><strong>1. Python 2 → 3 升级:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;">2to3 -w your_file.py</pre>
                <p><strong>2. 编码转换:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;">iconv -f GBK -t UTF-8 your_file.py > new_file.py</pre>
                <p><strong>3. GUI代码降级:</strong></p>
                <p style="margin-top: 8px;">将GUI相关代码注释掉，替换为控制台输出提示</p>
            </div>
        </div>
            """

        # 构建完整HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Python程序设计课程 - 质量监测报告</title>
    <script src="/js/platform-config.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{ color: white; text-align: center; margin-bottom: 8px; font-size: 28px; }}
        .subtitle {{ color: rgba(255,255,255,0.9); text-align: center; margin-bottom: 30px; }}
        .card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .card h2 {{ font-size: 18px; margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }}
        .card-icon {{ font-size: 20px; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .signal-card {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .signal-icon {{ font-size: 48px; margin-bottom: 12px; }}
        .signal-title {{ font-size: 14px; color: #666; margin-bottom: 4px; }}
        .signal-value {{ font-size: 18px; font-weight: 600; color: #333; }}
        .signal-pass {{ background: linear-gradient(135deg, #28a745, #20c997); color: white; }}
        .signal-fail {{ background: linear-gradient(135deg, #dc3545, #c82333); color: white; }}
        .signal-warn {{ background: linear-gradient(135deg, #ffc107, #e0a800); color: #333; }}
        .status-banner {{
            text-align: center;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            font-size: 24px;
            font-weight: 600;
        }}
        .status-pass {{ background: linear-gradient(135deg, #28a745, #20c997); color: white; }}
        .status-fail {{ background: linear-gradient(135deg, #dc3545, #c82333); color: white; }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }}
        .stat-item {{
            background: #f8f9fa;
            padding: 16px;
            border-radius: 12px;
            text-align: center;
        }}
        .stat-value {{ font-size: 28px; font-weight: 700; color: #667eea; }}
        .stat-label {{ font-size: 12px; color: #666; margin-top: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
        th, td {{ text-align: left; border-bottom: 1px solid #e9ecef; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #666; }}
        .tag {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .tag-pass {{ background: #d4edda; color: #155724; }}
        .tag-warn {{ background: #fff3cd; color: #856404; }}
        .tag-fail {{ background: #f8d7da; color: #721c24; }}
        .warning-box {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
            color: #856404;
        }}
        .progress-bar {{
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin: 12px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
        }}
        .risk-table td {{ font-size: 13px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Python程序设计课程 - 质量监测报告</h1>
        <p class="subtitle">基于 MCP 视角的自动化质量检测 | 检测时间: {r.timestamp}</p>

        <!-- 状态横幅 -->
        <div class="status-banner {'status-pass' if r.all_passed else 'status-fail'}">
            {'✅ 全部通过 - 可封版' if r.all_passed else '⚠️ 需修复问题'}
        </div>

        <!-- 三大标志 -->
        <div class="summary-grid">
            <div class="signal-card {'signal-pass' if r.syntax_signal else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.syntax_signal else '❌'}</div>
                <div class="signal-title">标志1: Python 3 纯度</div>
                <div class="signal-value">{'合规' if r.syntax_signal else f'{r.py2_legacy_count}处问题'}</div>
            </div>
            <div class="signal-card {'signal-pass' if r.encoding_signal else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.encoding_signal else '❌'}</div>
                <div class="signal-title">标志2: UTF-8 编码</div>
                <div class="signal-value">{'统一' if r.encoding_signal else f'{len(r.encoding_issues)}个问题'}</div>
            </div>
            <div class="signal-card {'signal-pass' if r.coverage_signal else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.coverage_signal else '❌'}</div>
                <div class="signal-title">标志3: 9模块覆盖</div>
                <div class="signal-value">{'完整' if r.coverage_signal else f'{r.empty_chapter_count}个空缺'}</div>
            </div>
        </div>

        <!-- 章节覆盖检查 -->
        <div class="card">
            <h2><span class="card-icon">📁</span>9大模块代码覆盖检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{r.total_py_files}</div>
                    <div class="stat-label">Python文件</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.total_ipynb_files}</div>
                    <div class="stat-label">Notebooks</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.total_md_files}</div>
                    <div class="stat-label">Markdown</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.coverage_rate}%</div>
                    <div class="stat-label">覆盖率</div>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {r.coverage_rate}%;"></div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>章节ID</th>
                        <th>章节名称</th>
                        <th style="text-align: center;">状态</th>
                        <th style="text-align: center;">代码类型</th>
                    </tr>
                </thead>
                <tbody>
                    {chapter_rows}
                </tbody>
            </table>
        </div>

        <!-- Python 3 纯度检查 -->
        <div class="card">
            <h2><span class="card-icon">🐍</span>Python 3 纯度检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.py2_legacy_count == 0 else '#dc3545'};">{r.py2_legacy_count}</div>
                    <div class="stat-label">Py2遗留问题</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(r.syntax_results)}</div>
                    <div class="stat-label">检查文件数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.syntax_passed else '#dc3545'};">{'通过' if r.syntax_passed else '失败'}</div>
                    <div class="stat-label">语法检查</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.gui_risk_count}</div>
                    <div class="stat-label">GUI风险</div>
                </div>
            </div>
            {'<div class="warning-box">⚠️ 发现Python 2遗留代码，建议使用2to3工具自动升级</div>' if r.py2_legacy_count > 0 else ''}
            <table>
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>状态</th>
                        <th>问题详情</th>
                    </tr>
                </thead>
                <tbody>
                    {syntax_issues_html}
                </tbody>
            </table>
        </div>

        <!-- 编码检查 -->
        <div class="card">
            <h2><span class="card-icon">📝</span>文件编码检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if len(r.encoding_issues) == 0 else '#dc3545'};">{len(r.encoding_issues)}</div>
                    <div class="stat-label">编码问题</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(r.encoding_results)}</div>
                    <div class="stat-label">检查文件</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.encoding_passed else '#dc3545'};">{'UTF-8' if r.encoding_passed else '异常'}</div>
                    <div class="stat-label">编码状态</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.infinite_loop_count}</div>
                    <div class="stat-label">死循环风险</div>
                </div>
            </div>
            {'<div class="warning-box">⚠️ 发现非UTF-8编码文件，建议使用iconv或Python脚本转换</div>' if len(r.encoding_issues) > 0 else ''}
            <table>
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>检测编码</th>
                    </tr>
                </thead>
                <tbody>
                    {encoding_issues_html}
                </tbody>
            </table>
        </div>

        <!-- 执行风险详情 -->
        <div class="card">
            <h2><span class="card-icon">⚡</span>在线执行友好性检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.gui_risk_count == 0 else '#f57c00'};">{r.gui_risk_count}</div>
                    <div class="stat-label">GUI阻断风险</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.infinite_loop_count == 0 else '#f57c00'};">{r.infinite_loop_count}</div>
                    <div class="stat-label">死循环风险</div>
                </div>
            </div>
            {'<div class="warning-box">💡 GUI库(turtle/tkinter/pygame等)在线环境不支持，建议替换为控制台版本</div>' if r.gui_risk_count > 0 else ''}
            <table class="risk-table">
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>风险类型</th>
                    </tr>
                </thead>
                <tbody>
                    {risk_rows}
                </tbody>
            </table>
        </div>

        <!-- 修复建议 -->
        {fix_suggestion_html if not r.all_passed else ''}

        <!-- 结束状态 -->
        <div class="card" style="text-align: center; padding: 30px;">
            <h2 style="justify-content: center;">{'🎉 资源已锁定 - 可封版' if r.all_passed else '⚠️ 需修复问题'}</h2>
            <p style="margin-top: 12px; color: #666;">
                课程资源状态: <strong>{'已封版' if r.all_passed else '待修复'}</strong>
                | 监测日期: {datetime.now().strftime("%Y-%m-%d")}
            </p>
        </div>

        <p style="text-align: center; color: rgba(255,255,255,0.7); margin-top: 20px; font-size: 12px;">
            慧学 平台 | 基于 MCP 视角的自动化质量检测系统
        </p>
    </div>
</body>
</html>'''

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✅ HTML报告已生成: {output_path}")


# ============================================================================
# 主函数
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Python程序设计课程监测系统')
    parser.add_argument('--course-path', '-p',
                       default=DEFAULT_COURSE_PATH,
                       help='课程资源路径')
    parser.add_argument('--output', '-o',
                       default=DEFAULT_OUTPUT_PATH,
                       help='HTML报告输出路径')

    args = parser.parse_args()

    # 检查路径是否存在
    course_path = Path(args.course_path)
    if not course_path.exists():
        print(f"❌ 错误: 课程路径不存在: {course_path}")
        return 1

    # 执行监测
    monitor = PythonCourseMonitor(str(course_path))
    report = monitor.run_full_scan()
    monitor.export_html_report(args.output)

    # 返回退出码
    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
