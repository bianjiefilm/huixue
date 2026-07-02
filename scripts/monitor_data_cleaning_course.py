#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据清洗课程 - MCP自动化质量监测系统 (Kettle专项)

功能:
- 资产维度扫描: 18类任务三要素检测 (.ktr/.kjb + 数据 + 文档)
- 技术维度扫描: Kettle文件路径硬编码检测
- 逻辑维度验证: 数据脏度检测 + JDBC驱动完整性

使用方法:
    python scripts/monitor_data_cleaning_course.py
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from collections import Counter

# 18类实验任务定义
EXPERIMENT_TASKS = {
    "exp01": "CSV文件输入",
    "exp02": "Excel文件输入",
    "exp03": "文本文件输入",
    "exp04": "表输入",
    "exp05": "JSON输入",
    "exp06": "多文件合并输入",
    "exp07": "选择/重命名字段",
    "exp08": "过滤记录",
    "exp09": "去除重复行",
    "exp10": "空值处理",
    "exp11": "字符串操作",
    "exp12": "数据有效性校验",
    "exp13": "值映射",
    "exp14": "字符串拼接与拆分",
    "exp15": "表输出",
    "exp16": "文件输出",
    "exp17": "错误处理",
    "exp18": "完整数据清洗流水线"
}

@dataclass
class TaskCheckResult:
    """任务检查结果"""
    task_id: str
    task_name: str
    has_ktr: bool = False
    has_kjb: bool = False
    has_data: bool = False
    has_document: bool = False
    missing_items: List[str] = field(default_factory=list)
    status: str = "unknown"  # "complete", "incomplete", "empty"

@dataclass
class PathCheckResult:
    """路径硬编码检查结果"""
    file_path: str
    has_absolute_path: bool = False
    absolute_paths: List[str] = field(default_factory=list)
    has_relative_path: bool = False
    relative_paths: List[str] = field(default_factory=list)

@dataclass
class DataQualityResult:
    """数据质量检查结果"""
    file_path: str
    total_rows: int = 0
    null_count: int = 0
    null_rate: float = 0.0
    duplicate_rows: int = 0
    duplicate_rate: float = 0.0
    is_dirty: bool = False
    issues: List[str] = field(default_factory=list)

@dataclass
class DriverCheckResult:
    """JDBC驱动检查结果"""
    has_driver_dir: bool = False
    mysql_driver: bool = False
    oracle_driver: bool = False
    postgresql_driver: bool = False
    driver_files: List[str] = field(default_factory=list)
    missing_drivers: List[str] = field(default_factory=list)

@dataclass
class CourseMonitorReport:
    """完整监测报告"""
    timestamp: str = ""
    course_name: str = "数据清洗"

    # 资产维度
    tasks: Dict[str, TaskCheckResult] = field(default_factory=dict)
    task_coverage: float = 0.0
    complete_count: int = 0
    incomplete_count: int = 0
    empty_count: int = 0

    # 技术维度
    path_checks: List[PathCheckResult] = field(default_factory=dict)
    absolute_path_count: int = 0
    relative_path_count: int = 0

    # 逻辑维度
    data_quality: Dict[str, DataQualityResult] = field(default_factory=dict)
    driver_result: DriverCheckResult = None

    # 三大标志
    portability_signal: bool = False
    completeness_signal: bool = False
    dependency_signal: bool = False
    all_passed: bool = False


class DataCleaningCourseMonitor:
    """数据清洗课程监测器"""

    def __init__(self, course_path: str):
        self.course_path = Path(course_path)
        self.report = CourseMonitorReport()
        self.report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 路径硬编码检测模式
        self.absolute_path_patterns = [
            re.compile(r'[A-Za-z]:\\'),  # Windows: C:\, D:\
            re.compile(r'/home/[^/]+/'),  # Linux: /home/user/
            re.compile(r'/Users/[^/]+/'),  # macOS: /Users/user/
            re.compile(r'C:\\Program Files'),
            re.compile(r'D:\\'),
        ]

        # 相对路径模式
        self.relative_path_patterns = [
            re.compile(r'\$\{Internal\.Entry\.Current\.Directory\}'),
            re.compile(r'\$\{PROJECT\.Directory\}'),
            re.compile(r'\.\./'),
            re.compile(r'\./'),
        ]

    def run_full_scan(self) -> CourseMonitorReport:
        """执行完整扫描"""
        print("=" * 60)
        print(">>> 开始数据清洗课程监测 (Kettle专项)")
        print("=" * 60)

        # 1. 资产维度 - 18类任务三要素检测
        print("\n[1/4] 扫描18类任务三要素...")
        self._check_experiment_tasks()

        # 2. 技术维度 - Kettle路径硬编码检测
        print("\n[2/4] 检测Kettle文件路径硬编码...")
        self._check_path_hardcoding()

        # 3. 逻辑维度 - 数据脏度检测
        print("\n[3/4] 检测数据质量 (脏数据)...")
        self._check_data_quality()

        # 4. 逻辑维度 - JDBC驱动检测
        print("\n[4/4] 检测JDBC驱动完整性...")
        self._check_jdbc_drivers()

        # 计算三大标志
        self._calculate_completion_signals()

        print("\n" + "=" * 60)
        print(f">>> 监测完成! 三大标志状态:")
        print(f"    标志1 (可移植性): {'✅ 通过' if self.report.portability_signal else '❌ 未通过'}")
        print(f"    标志2 (完整性): {'✅ 通过' if self.report.completeness_signal else '❌ 未通过'}")
        print(f"    标志3 (依赖性): {'✅ 通过' if self.report.dependency_signal else '❌ 未通过'}")
        print(f"    综合状态: {'✅ 可封版' if self.report.all_passed else '❌ 需修复'}")
        print("=" * 60)

        return self.report

    def _check_experiment_tasks(self):
        """检查18类任务三要素 (.ktr/.kjb + 数据 + 文档)"""
        kettle_dir = self.course_path / "kettle"
        datasets_dir = self.course_path / "datasets"
        docs_dir = self.course_path / "docs"

        for task_id, task_name in EXPERIMENT_TASKS.items():
            result = TaskCheckResult(task_id=task_id, task_name=task_name)

            # 检查KTR文件
            ktr_files = list(kettle_dir.rglob(f"{task_id}*.ktr"))
            kjb_files = list(kettle_dir.rglob(f"{task_id}*.kjb"))

            result.has_ktr = len(ktr_files) > 0
            result.has_kjb = len(kjb_files) > 0

            # 检查数据文件 (CSV/TXT/Excel)
            data_files = list(datasets_dir.glob("*.csv")) + \
                        list(datasets_dir.glob("*.txt")) + \
                        list(datasets_dir.glob("*.xlsx"))
            result.has_data = len(data_files) > 0

            # 检查文档 (PDF/MD)
            doc_files = list(docs_dir.glob("*.pdf")) + list(docs_dir.glob("*.md"))
            result.has_document = len(doc_files) > 0

            # 记录缺失项
            if not result.has_ktr and not result.has_kjb:
                result.missing_items.append("KTR/KJB文件")
            if not result.has_data:
                result.missing_items.append("数据文件")
            if not result.has_document:
                result.missing_items.append("指导文档")

            # 确定状态
            if not result.has_ktr and not result.has_kjb and not result.has_data and not result.has_document:
                result.status = "empty"
            elif result.has_ktr or result.has_kjb:
                if result.has_data and result.has_document:
                    result.status = "complete"
                else:
                    result.status = "incomplete"
            else:
                result.status = "incomplete"

            self.report.tasks[task_id] = result

        # 统计
        complete = sum(1 for t in self.report.tasks.values() if t.status == "complete")
        incomplete = sum(1 for t in self.report.tasks.values() if t.status == "incomplete")
        empty = sum(1 for t in self.report.tasks.values() if t.status == "empty")

        self.report.complete_count = complete
        self.report.incomplete_count = incomplete
        self.report.empty_count = empty
        self.report.task_coverage = round(complete / len(EXPERIMENT_TASKS) * 100, 1)

        print(f"      任务统计: 完整={complete}, 不完整={incomplete}, 空缺={empty}")
        print(f"      完整率: {self.report.task_coverage}%")

    def _check_path_hardcoding(self):
        """检测Kettle文件中的路径硬编码"""
        kettle_dir = self.course_path / "kettle"
        ktr_files = list(kettle_dir.rglob("*.ktr"))
        kjb_files = list(kettle_dir.rglob("*.kjb"))

        total_absolute = 0
        total_relative = 0

        for ktr_file in ktr_files + kjb_files:
            result = PathCheckResult(file_path=str(ktr_file))
            content = self._read_file_content(ktr_file)

            if content:
                # 检测绝对路径
                for pattern in self.absolute_path_patterns:
                    matches = pattern.findall(content)
                    if matches:
                        result.has_absolute_path = True
                        # 提取路径示例
                        for match in matches[:3]:
                            context_start = max(0, content.find(match) - 20)
                            context_end = min(len(content), content.find(match) + len(match) + 20)
                            result.absolute_paths.append(f"...{content[context_start:context_end]}...")

                # 检测相对路径
                for pattern in self.relative_path_patterns:
                    matches = pattern.findall(content)
                    if matches:
                        result.has_relative_path = True

            if result.has_absolute_path:
                total_absolute += len(result.absolute_paths)
                print(f"      🔴 {ktr_file.name}: 发现 {len(result.absolute_paths)} 处绝对路径")

            if result.has_relative_path:
                total_relative += 1

            self.report.path_checks[result.file_path] = result

        self.report.absolute_path_count = total_absolute
        self.report.relative_path_count = total_relative

        print(f"      绝对路径: {total_absolute} 处")
        print(f"      使用相对路径: {total_relative} 个文件")

    def _check_data_quality(self):
        """检测数据脏度"""
        datasets_dir = self.course_path / "datasets"
        csv_files = list(datasets_dir.glob("*.csv"))

        dirty_count = 0
        for csv_file in csv_files:
            result = DataQualityResult(file_path=str(csv_file))
            content = self._read_file_content(csv_file)

            if content:
                lines = content.strip().split('\n')
                result.total_rows = len(lines) - 1  # 减去表头

                if result.total_rows > 0:
                    # 检查空值和脏数据
                    headers = lines[0].split(',')
                    null_count = 0
                    row_values = []

                    for line in lines[1:]:
                        values = line.split(',')
                        row_values.append(values)
                        # 检查空值（连续逗号或只有一个逗号后为空）
                        for val in values:
                            if val.strip() == '':
                                null_count += 1

                    result.null_count = null_count
                    result.null_rate = round(null_count / (result.total_rows * len(headers)) * 100, 2) if result.total_rows > 0 else 0

                    # 检查重复行
                    seen = set()
                    duplicate_count = 0
                    for values in row_values:
                        row_tuple = tuple(v.strip() for v in values)
                        if row_tuple in seen:
                            duplicate_count += 1
                        else:
                            seen.add(row_tuple)

                    result.duplicate_rows = duplicate_count
                    result.duplicate_rate = round(duplicate_count / result.total_rows * 100, 2) if result.total_rows > 0 else 0

                    # 判断是否足够"脏"
                    is_dirty = (
                        result.null_rate > 1 or  # 超过1%空值
                        result.duplicate_rate > 1 or  # 超过1%重复
                        result.total_rows > 100  # 数据量足够大
                    )
                    result.is_dirty = is_dirty

                    if is_dirty:
                        dirty_count += 1

                    # 记录问题
                    if result.null_rate > 5:
                        result.issues.append(f"空值率过高: {result.null_rate}%")
                    if result.duplicate_rate > 3:
                        result.issues.append(f"重复率过高: {result.duplicate_rate}%")

            self.report.data_quality[csv_file.name] = result

        print(f"      数据文件: {len(csv_files)} 个")
        print(f"      脏数据文件: {dirty_count} 个")

    def _check_jdbc_drivers(self):
        """检查JDBC驱动完整性"""
        result = DriverCheckResult()

        # 检查lib目录
        lib_dir = self.course_path / "lib"
        result.has_driver_dir = lib_dir.exists()

        if lib_dir.exists():
            jar_files = list(lib_dir.glob("*.jar"))
            for jar in jar_files:
                result.driver_files.append(jar.name)
                if "mysql" in jar.name.lower() and "connector" in jar.name.lower():
                    result.mysql_driver = True
                if "ojdbc" in jar.name.lower() or "oracle" in jar.name.lower():
                    result.oracle_driver = True
                if "postgresql" in jar.name.lower():
                    result.postgresql_driver = True

        # 检查是否有SQL相关任务需要驱动
        sql_dir = self.course_path / "sql"
        has_sql_tasks = sql_dir.exists() and any(sql_dir.glob("*.sql"))

        # 记录缺失的驱动
        if has_sql_tasks and not result.mysql_driver:
            result.missing_drivers.append("mysql-connector-java-*.jar")
        if has_sql_tasks and not result.oracle_driver:
            result.missing_drivers.append("ojdbc*.jar")

        # 检查是否有配套SQL脚本
        sql_files = list(sql_dir.glob("*.sql"))
        has_sql_scripts = len(sql_files) > 0

        result.has_sql_scripts = has_sql_scripts
        result.has_sql_tasks = has_sql_tasks

        self.report.driver_result = result

        status = "✅" if result.has_driver_dir and result.mysql_driver else "⚠️"
        print(f"      lib目录: {'存在' if result.has_driver_dir else '不存在'}")
        print(f"      MySQL驱动: {'有' if result.mysql_driver else '无'}")
        print(f"      Oracle驱动: {'有' if result.oracle_driver else '无'}")
        print(f"      SQL脚本: {'有' if has_sql_scripts else '无'}")

    def _calculate_completion_signals(self):
        """计算三大完成标志"""
        # 标志1: 可移植性 (无绝对路径)
        self.report.portability_signal = self.report.absolute_path_count == 0

        # 标志2: 完整性 (18类任务三要素齐备)
        self.report.completeness_signal = (
            self.report.complete_count == len(EXPERIMENT_TASKS) and
            self.report.empty_count == 0
        )

        # 标志3: 依赖性 (有SQL脚本和驱动)
        has_sql = self.report.driver_result and self.report.driver_result.has_sql_scripts
        has_drivers = self.report.driver_result and (
            self.report.driver_result.mysql_driver or
            not self.report.driver_result.has_sql_tasks  # 如果没有SQL任务，则不需要驱动
        )
        self.report.dependency_signal = has_sql and has_drivers

        # 综合状态
        self.report.all_passed = (
            self.report.portability_signal and
            self.report.completeness_signal and
            self.report.dependency_signal
        )

    def _read_file_content(self, filepath: Path) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            try:
                with open(filepath, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return None

    def export_html_report(self, output_path: str):
        """导出HTML报告"""
        r = self.report

        # 生成任务状态表格
        task_rows = ""
        for task_id, task in r.tasks.items():
            status_class = "tag-pass" if task.status == "complete" else "tag-fail" if task.status == "empty" else "tag-warning"
            status_text = "完整" if task.status == "complete" else "空缺" if task.status == "empty" else "不完整"
            missing = ", ".join(task.missing_items) if task.missing_items else "-"

            task_rows += f"""
            <tr>
                <td style="font-family: monospace;">{task_id}</td>
                <td>{task.task_name}</td>
                <td style="text-align: center;">{'✅' if task.has_ktr or task.has_kjb else '❌'}</td>
                <td style="text-align: center;">{'✅' if task.has_data else '❌'}</td>
                <td style="text-align: center;">{'✅' if task.has_document else '❌'}</td>
                <td><span class="tag {status_class}">{status_text}</span></td>
                <td style="font-size: 12px; color: #666;">{missing}</td>
            </tr>
            """

        # 生成数据质量卡片
        data_quality_cards = ""
        for filename, data in r.data_quality.items():
            tag_class = "tag-pass" if data.is_dirty else "tag-warning"
            tag_text = "脏数据" if data.is_dirty else "过于干净"
            data_quality_cards += f"""
                <div style="padding: 16px; background: #f8f9fa; border-radius: 8px;">
                    <div style="font-weight: 600; margin-bottom: 8px;">{filename}</div>
                    <div style="font-size: 12px; color: #666;">
                        <div>行数: {data.total_rows}</div>
                        <div>空值率: {data.null_rate}%</div>
                        <div>重复率: {data.duplicate_rate}%</div>
                        <div style="margin-top: 8px;">
                            <span class="tag {tag_class}">
                                {tag_text}
                            </span>
                        </div>
                    </div>
                </div>
            """

        # 生成缺失驱动警告
        missing_drivers_html = ""
        if r.driver_result and r.driver_result.missing_drivers:
            for d in r.driver_result.missing_drivers:
                missing_drivers_html += f'<div class="warning-box">⚠️ 缺失驱动: {d}</div>'

        # 生成路径警告
        path_warning_html = ""
        if r.absolute_path_count > 0:
            path_warning_html = '<div class="warning-box">⚠️ 建议: 将所有绝对路径替换为 $${{Internal.Entry.Current.Directory}}/filename</div>'

        # 驱动状态图标
        lib_dir_status = "✅" if r.driver_result and r.driver_result.has_driver_dir else "⚠️"
        lib_dir_text = "存在" if r.driver_result and r.driver_result.has_driver_dir else "不存在"

        mysql_driver_status = "✅" if r.driver_result and r.driver_result.mysql_driver else "❌"
        mysql_driver_text = "mysql-connector-java.jar 已包含" if r.driver_result and r.driver_result.mysql_driver else "缺失 - 连接MySQL将报错"

        sql_script_status = "✅" if r.driver_result and r.driver_result.has_sql_scripts else "❌"
        sql_script_text = "已提供" if r.driver_result and r.driver_result.has_sql_scripts else "缺失"

        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据清洗课程 - Kettle资源监测报告</title>
    <script src="/js/platform-config.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: white; border-radius: 16px; padding: 30px; margin-bottom: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
        .header h1 {{ color: #1a1a2e; font-size: 28px; margin-bottom: 10px; }}
        .header p {{ color: #666; font-size: 14px; }}
        .status-badge {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 16px; border-radius: 20px; font-weight: 600; }}
        .status-pass {{ background: #d4edda; color: #155724; }}
        .status-fail {{ background: #f8d7da; color: #721c24; }}
        .status-warning {{ background: #fff3cd; color: #856404; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 16px; padding: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }}
        .card h2 {{ color: #1a1a2e; font-size: 18px; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 2px solid #f0f0f0; display: flex; align-items: center; gap: 10px; }}
        .checklist {{ list-style: none; }}
        .checklist li {{ display: flex; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid #f5f5f5; }}
        .check-icon {{ width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; flex-shrink: 0; }}
        .check-pass {{ background: #28a745; color: white; }}
        .check-fail {{ background: #dc3545; color: white; }}
        .check-warn {{ background: #ffc107; color: #333; }}
        .summary {{ background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; border-radius: 16px; padding: 30px; text-align: center; }}
        .summary h2 {{ font-size: 24px; margin-bottom: 16px; }}
        .summary p {{ font-size: 16px; opacity: 0.9; }}
        .tag {{ display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 500; margin: 4px; }}
        .tag-pass {{ background: #d4edda; color: #155724; }}
        .tag-fail {{ background: #f8d7da; color: #721c24; }}
        .tag-warning {{ background: #fff3cd; color: #856404; }}
        .progress-bar {{ height: 8px; background: #e9ecef; border-radius: 4px; overflow: hidden; margin: 8px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #28a745, #20c997); border-radius: 4px; transition: width 0.3s; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #f0f0f0; }}
        th {{ background: #f8f9fa; font-weight: 600; font-size: 12px; color: #666; }}
        .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); gap: 12px; text-align: center; }}
        .stat-item {{ padding: 16px; border-radius: 8px; }}
        .stat-complete {{ background: #e8f5e9; }}
        .stat-incomplete {{ background: #fff3e0; }}
        .stat-empty {{ background: #ffebee; }}
        .stat-path {{ background: #e3f2fd; }}
        .url-item {{ display: flex; align-items: center; gap: 8px; padding: 8px; background: #f8f9fa; border-radius: 6px; margin: 4px 0; font-size: 12px; font-family: monospace; word-break: break-all; }}
        .warning-box {{ background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px; padding: 12px; margin: 8px 0; }}
        @media (max-width: 768px) {{ .grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;">
                <div>
                    <h1>📊 数据清洗课程 - Kettle资源监测报告</h1>
                    <p>基于 MCP 视角的自动化质量检测 | 检测时间: {r.timestamp}</p>
                </div>
                <div class="status-badge {'status-pass' if r.all_passed else 'status-fail'}">
                    <span style="font-size: 20px;">{'✓' if r.all_passed else '✗'}</span>
                    <span>{'全部通过 - 可封版' if r.all_passed else '需修复问题'}</span>
                </div>
            </div>
        </div>

        <!-- 三大标志 -->
        <div class="summary" style="margin-bottom: 20px;">
            <h2 style="font-size: 24px; margin-bottom: 16px;">🎯 任务闭环结束标志</h2>
            <p>当且仅当以下 3 个信号全部亮起绿灯，循环结束，触发"封版"</p>
            <div style="display: flex; justify-content: center; gap: 40px; margin: 24px 0; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <div style="font-size: 36px; font-weight: 700;">{'✅' if r.portability_signal else '❌'}</div>
                    <div>标志1: 可移植性</div>
                    <div style="font-size: 12px; opacity: 0.8;">无绝对路径</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 36px; font-weight: 700;">{'✅' if r.completeness_signal else '❌'}</div>
                    <div>标志2: 完整性</div>
                    <div style="font-size: 12px; opacity: 0.8;">18任务三要素</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 36px; font-weight: 700;">{'✅' if r.dependency_signal else '❌'}</div>
                    <div>标志3: 依赖性</div>
                    <div style="font-size: 12px; opacity: 0.8;">JDBC驱动+SQL</div>
                </div>
            </div>
        </div>

        <div class="grid">
            <!-- 标志1: 可移植性 -->
            <div class="card">
                <h2><div class="card-icon" style="background: #e3f2fd;">🔧</div>标志1: Kettle文件"去本地化" (Portability)</h2>
                <ul class="checklist">
                    <li>
                        <div class="check-icon {'check-pass' if r.portability_signal else 'check-fail'}">{'✓' if r.portability_signal else '✗'}</div>
                        <div>
                            <strong>绝对路径检测</strong>
                            <div style="font-size: 12px; color: #666; margin-top: 4px;">
                                发现 {r.absolute_path_count} 处硬编码路径
                            </div>
                        </div>
                    </li>
                    <li>
                        <div class="check-icon {'check-pass' if r.relative_path_count > 0 else 'check-warn'}">{'✓' if r.relative_path_count > 0 else '!'}</div>
                        <div>
                            <strong>相对路径使用</strong>
                            <div style="font-size: 12px; color: #666; margin-top: 4px;">
                                {r.relative_path_count} 个文件使用 $${{Internal.Entry.Current.Directory}}
                            </div>
                        </div>
                    </li>
                </ul>
                {'<div class="warning-box">⚠️ 建议: 将所有绝对路径替换为 $${{Internal.Entry.Current.Directory}}/filename</div>' if r.absolute_path_count > 0 else ''}
            </div>

            <!-- 标志2: 完整性 -->
            <div class="card">
                <h2><div class="card-icon" style="background: #fff3e0;">📁</div>标志2: 18类任务三要素齐备 (Completeness)</h2>
                <div class="stat-grid" style="margin-bottom: 16px;">
                    <div class="stat-item stat-complete">
                        <div style="font-size: 24px; font-weight: 700; color: #28a745;">{r.complete_count}</div>
                        <div style="font-size: 12px; color: #666;">完整</div>
                    </div>
                    <div class="stat-item stat-incomplete">
                        <div style="font-size: 24px; font-weight: 700; color: #f57c00;">{r.incomplete_count}</div>
                        <div style="font-size: 12px; color: #666;">不完整</div>
                    </div>
                    <div class="stat-item stat-empty">
                        <div style="font-size: 24px; font-weight: 700; color: #dc3545;">{r.empty_count}</div>
                        <div style="font-size: 12px; color: #666;">空缺</div>
                    </div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {r.task_coverage}%;"></div>
                </div>
                <div style="text-align: center; font-size: 14px; color: #28a745; font-weight: 600;">
                    完整率: {r.task_coverage}%
                </div>
            </div>

            <!-- 标志3: 依赖性 -->
            <div class="card">
                <h2><div class="card-icon" style="background: #e8f5e9;">🗄️</div>标志3: 数据库依赖自洽 (Dependency)</h2>
                <ul class="checklist">
                    <li>
                        <div class="check-icon {'check-pass' if r.driver_result and r.driver_result.has_driver_dir else 'check-warn'}">{'✓' if r.driver_result and r.driver_result.has_driver_dir else '!'}</div>
                        <div>
                            <strong>lib目录存在</strong>
                            <div style="font-size: 12px; color: #666; margin-top: 4px;">
                                {'存在' if r.driver_result and r.driver_result.has_driver_dir else '不存在'}
                            </div>
                        </div>
                    </li>
                    <li>
                        <div class="check-icon {'check-pass' if r.driver_result and r.driver_result.mysql_driver else 'check-fail'}">{'✓' if r.driver_result and r.driver_result.mysql_driver else '✗'}</div>
                        <div>
                            <strong>MySQL JDBC驱动</strong>
                            <div style="font-size: 12px; color: #666; margin-top: 4px;">
                                {'mysql-connector-java.jar 已包含' if r.driver_result and r.driver_result.mysql_driver else '缺失 - 连接MySQL将报错'}
                            </div>
                        </div>
                    </li>
                    <li>
                        <div class="check-icon {'check-pass' if r.driver_result and r.driver_result.has_sql_scripts else 'check-fail'}">{'✓' if r.driver_result and r.driver_result.has_sql_scripts else '✗'}</div>
                        <div>
                            <strong>SQL建表脚本</strong>
                            <div style="font-size: 12px; color: #666; margin-top: 4px;">
                                {'已提供' if r.driver_result and r.driver_result.has_sql_scripts else '缺失'}
                            </div>
                        </div>
                    </li>
                </ul>
                {''.join(f'<div class="warning-box">⚠️ 缺失驱动: {d}</div>' for d in (r.driver_result.missing_drivers if r.driver_result else []))}
            </div>
        </div>

        <!-- 任务三要素详细表 -->
        <div class="card" style="margin-bottom: 20px;">
            <h2><div class="card-icon" style="background: #fce4ec;">📋</div>18类实验任务完整度检查表</h2>
            <table>
                <thead>
                    <tr>
                        <th>任务ID</th>
                        <th>实验名称</th>
                        <th>KTR/KJB</th>
                        <th>数据</th>
                        <th>文档</th>
                        <th>状态</th>
                        <th>缺失项</th>
                    </tr>
                </thead>
                <tbody>
                    {task_rows}
                </tbody>
            </table>
        </div>

        <!-- 数据质量检测 -->
        <div class="card" style="margin-bottom: 20px;">
            <h2><div class="card-icon" style="background: #f3e5f5;">📊</div>数据质量"脏度"检测</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 16px;">
                {data_quality_cards}
            </div>
            <div class="warning-box" style="margin-top: 16px;">
                💡 提示: 清洗课程必须有"脏数据"。空值率应>1%，重复率应>1%，否则请使用劣化脚本生成测试数据。
            </div>
        </div>

        <!-- 路径检测结果 -->
        <div class="card" style="margin-bottom: 20px;">
            <h2><div class="card-icon" style="background: #fff8e1;">🔍</div>Kettle文件路径检测详情</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-top: 16px;">
                <div style="padding: 16px; background: #e3f2fd; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #1976d2;">{len(r.path_checks)}</div>
                    <div style="font-size: 12px; color: #666;">KTR/KJB文件</div>
                </div>
                <div style="padding: 16px; background: #ffebee; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #dc3545;">{r.absolute_path_count}</div>
                    <div style="font-size: 12px; color: #666;">绝对路径</div>
                </div>
                <div style="padding: 16px; background: #e8f5e9; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: 700; color: #28a745;">{r.relative_path_count}</div>
                    <div style="font-size: 12px; color: #666;">使用相对路径</div>
                </div>
            </div>
        </div>

        <!-- 最终封版状态 -->
        <div class="summary" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
            <h2 style="font-size: 32px; margin-bottom: 20px;">{'🎉 监测完成 - 资源已锁定' if r.all_passed else '⚠️ 监测完成 - 需修复问题'}</h2>
            <div style="display: flex; justify-content: center; gap: 40px; margin: 30px 0; flex-wrap: wrap;">
                <div style="text-align: center;">
                    <div style="font-size: 48px;">{'✅' if r.portability_signal else '❌'}</div>
                    <div>路径去本地化</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 48px;">{'✅' if r.completeness_signal else '❌'}</div>
                    <div>18任务齐备</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 48px;">{'✅' if r.dependency_signal else '❌'}</div>
                    <div>驱动+SQL完整</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 12px; display: inline-block;">
                <span style="font-size: 24px; font-weight: 700;">{'✅ 数据清洗 - Kettle资源已校验' if r.all_passed else '❌ 数据清洗 - 存在阻断问题'}</span>
            </div>
            <p style="margin-top: 20px; font-size: 14px;">课程资源状态: <strong>{'已封版' if r.all_passed else '待修复'}</strong> | 监测日期: {r.timestamp.split()[0]}</p>
        </div>

        <div style="text-align: center; margin-top: 20px; color: white; font-size: 12px;">
            <script>document.write(window.PlatformConfig.fullName + ' | ' + window.PlatformConfig.monitoringSystem);</script>
            <script>document.write('<br>' + window.PlatformConfig.copyright);</script>
        </div>
    </div>

    <script>
        // 模拟进度条动画
        document.querySelectorAll('.progress-fill').forEach(bar => {{
            const width = bar.style.width;
            bar.style.width = '0%';
            setTimeout(() => {{
                bar.style.width = width;
            }}, 100);
        }});
    </script>
</body>
</html>'''

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"\n✅ HTML报告已生成: {output_path}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='数据清洗课程监测 (Kettle专项)')
    parser.add_argument('--course-path', '-p',
                       default='/Users/jimfu/Work/huixue/ziyuan_data/课程资源/数据清洗',
                       help='课程资源路径')
    parser.add_argument('--output', '-o',
                       default='/Users/jimfu/Work/huixue/frontend/public/data-cleaning-monitoring-report.html',
                       help='HTML报告输出路径')

    args = parser.parse_args()

    # 执行监测
    monitor = DataCleaningCourseMonitor(args.course_path)
    report = monitor.run_full_scan()

    # 生成报告
    monitor.export_html_report(args.output)

    # 返回退出码
    exit_code = 0 if report.all_passed else 1
    return exit_code


if __name__ == "__main__":
    exit(main())
