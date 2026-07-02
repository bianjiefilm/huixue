#!/usr/bin/env python3
"""
零售经营分析课程监测脚本
========================

基于 MCP 视角的自动化质量监测系统

监测维度:
1. 资产维度 - 三表合一校验（经营/人员/运营）
2. 可视化维度 - 气泡图可行性（3+数值字段）
3. 逻辑维度 - 商业常识验证

三大结束标志:
- 标志1: 三大管理维度字段覆盖
- 标志2: 气泡图三维支撑
- 手册与数据一致
"""

import os
import re
import json
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 中文显示配置
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


@dataclass
class FieldCheckResult:
    """字段检测结果"""
    field_name: str
    found: bool
    match_type: str  # "exact", "fuzzy", "none"
    suggestion: str = ""


@dataclass
class DimensionCheckResult:
    """维度检测结果"""
    dimension_name: str  # 经营/人员/运营
    required_fields: List[str]
    found_fields: List[str]
    missing_fields: List[str]
    coverage_rate: float = 0.0
    is_complete: bool = False


@dataclass
class VisualizationCheckResult:
    """可视化检测结果"""
    numeric_columns: int = 0
    categorical_columns: int = 0
    can_draw_bubble_chart: bool = False
    bubble_requirements: Dict[str, bool] = field(default_factory=dict)
    non_null_rates: Dict[str, float] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)


@dataclass
class BusinessLogicResult:
    """商业逻辑检测结果"""
    data_rows: int = 0
    time_span_months: int = 0
    logic_errors: List[str] = field(default_factory=list)
    has_negative_sales: bool = False
    has_profit_exceeding_sales: bool = False
    is_logically_valid: bool = True


@dataclass
class ConsistencyCheckResult:
    """一致性检测结果"""
    manual_fields: List[str] = field(default_factory=list)
    excel_headers: List[str] = field(default_factory=list)
    matched_fields: List[str] = field(default_factory=list)
    mismatched_fields: List[str] = field(default_factory=list)
    match_rate: float = 0.0
    is_consistent: bool = True


@dataclass
class RetailAnalysisMonitorReport:
    """零售经营分析课程监测报告"""
    timestamp: str = ""
    course_name: str = "零售经营分析"

    # 维度1: 字段覆盖
    dimension_results: List[DimensionCheckResult] = field(default_factory=list)
    missing_dimension_count: int = 0
    dimension_signal: bool = False

    # 维度2: 可视化可行性
    visualization_result: VisualizationCheckResult = field(default_factory=lambda: VisualizationCheckResult())
    visualization_signal: bool = False

    # 维度3: 商业逻辑
    business_logic_result: BusinessLogicResult = field(default_factory=lambda: BusinessLogicResult())
    logic_signal: bool = False

    # 维度4: 数据一致性
    consistency_result: ConsistencyCheckResult = field(default_factory=lambda: ConsistencyCheckResult())
    consistency_signal: bool = False

    # 统计
    total_datasets: int = 0
    total_files: int = 0

    # 三大标志
    signal1_dimension_covered: bool = False  # 维度覆盖
    signal2_bubble_supported: bool = False   # 气泡图支撑
    signal3_consistent: bool = False         # 数据一致
    all_passed: bool = False

    # 修复建议
    fix_suggestions: List[str] = field(default_factory=list)


class RetailAnalysisCourseMonitor:
    """零售经营分析课程监测器"""

    def __init__(self, course_path: str):
        self.course_path = Path(course_path)
        self.report = RetailAnalysisMonitorReport()
        self.report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def run(self):
        """执行完整监测"""
        print("=" * 70)
        print(">>> 开始 零售经营分析课程监测")
        print("=" * 70)

        # 步骤1: 检测三大管理维度字段覆盖
        self._check_dimension_coverage()

        # 步骤2: 检测气泡图可行性
        self._check_visualization_feasibility()

        # 步骤3: 检测商业逻辑
        self._check_business_logic()

        # 步骤4: 检测手册与数据一致性
        self._check_consistency()

        # 计算结束标志
        self._calculate_completion_signals()

        # 生成报告
        self._print_results()
        self._export_html_report()

        return self.report

    def _check_dimension_coverage(self):
        """检查三大管理维度字段覆盖"""
        print("\n[1/4] 检测三大管理维度字段覆盖...")

        # 定义各维度必需字段（支持中英文模糊匹配）
        DIMENSION_REQUIREMENTS = {
            '经营': {
                'keywords': ['销售额', 'sales', 'revenue', '利润', 'profit', '日期', 'date', '时间', 'time', '月份', 'month'],
                'core_fields': ['销售额', 'sales', '利润', 'profit', '日期', 'date'],
                'description': '经营分析需包含销售和利润数据'
            },
            '人员': {
                'keywords': ['员工', 'employee', 'staff', '人效', 'labor', '店长', 'manager', '薪资', 'salary', '工资'],
                'core_fields': ['员工人数', 'employee_count', '店长', 'manager', '薪资', 'salary', '人效', 'labor'],
                'description': '人员管理需包含员工或店长相关字段'
            },
            '运营': {
                'keywords': ['门店', 'store', '面积', 'area', '坪效', 'pingsheng', '库存', 'inventory', '客流量', 'traffic'],
                'core_fields': ['门店面积', 'store_area', '门店', 'store', '坪效', 'pingsheng', '库存', 'inventory'],
                'description': '运营分析需包含门店或坪效相关字段'
            }
        }

        # 收集所有数据文件
        excel_files = list(self.course_path.rglob("*.xlsx")) + list(self.course_path.rglob("*.csv"))
        self.report.total_datasets = len(excel_files)
        self.report.total_files = len(list(self.course_path.rglob("*")))

        if not excel_files:
            print(f"      ⚠️ 未找到数据文件!")
            self.report.missing_dimension_count = 3
            self.report.dimension_signal = False
            return

        # 提取所有字段（保留原始大小写和中文）
        all_headers = set()
        for f in excel_files:
            try:
                if f.suffix == '.xlsx':
                    # 读取所有sheet
                    xl = pd.ExcelFile(f)
                    for sheet in xl.sheet_names:
                        df = pd.read_excel(f, sheet_name=sheet)
                        all_headers.update(df.columns.tolist())
                else:
                    df = pd.read_csv(f)
                    all_headers.update(df.columns.tolist())
            except Exception as e:
                print(f"      读取失败: {f.name} - {e}")

        print(f"      发现字段: {list(all_headers)}")

        # 简化维度检查逻辑：直接检查字段是否存在
        dimension_checks = {
            '经营': {
                'required': ['销售额', '利润', '日期'],
                'aliases': {'日期': ['日期', '时间', '月份', 'month', 'date']},  # 别名映射
                'found': []
            },
            '人员': {
                'required': ['员工', '店长'],
                'aliases': {'员工': ['员工', '人数'], '店长': ['店长', 'manager']},
                'found': []
            },
            '运营': {
                'required': ['门店', '面积', '客流量'],
                'aliases': {'门店': ['门店', 'store'], '面积': ['面积', 'area'], '客流量': ['客流量', 'traffic', '客流']},
                'found': []
            }
        }

        # 简化匹配：检查关键词是否存在
        for dim_name, dim_data in dimension_checks.items():
            aliases = dim_data.get('aliases', {})
            for req in dim_data['required']:
                # 检查主字段或其别名
                patterns = [req] + aliases.get(req, [])
                if any(any(p.lower() in h.lower() or h.lower() in p.lower() for p in patterns) for h in all_headers):
                    dim_data['found'].append(req)

        # 生成结果
        for dim_name, dim_data in dimension_checks.items():
            coverage = len(dim_data['found']) / len(dim_data['required'])
            missing = [r for r in dim_data['required'] if r not in dim_data['found']]
            result = DimensionCheckResult(
                dimension_name=dim_name,
                required_fields=dim_data['required'],
                found_fields=dim_data['found'],
                missing_fields=missing,
                coverage_rate=coverage,
                is_complete=coverage >= 0.67  # 至少2/3字段覆盖
            )
            self.report.dimension_results.append(result)

        missing_count = sum(1 for r in self.report.dimension_results if not r.is_complete)
        self.report.missing_dimension_count = missing_count
        self.report.dimension_signal = missing_count == 0

        # 打印各维度状态
        for r in self.report.dimension_results:
            status = "✅" if r.is_complete else "❌"
            print(f"      {status} {r.dimension_name}: 覆盖率 {r.coverage_rate*100:.0f}% ({len(r.found_fields)}/{len(r.required_fields)})")

    def _check_visualization_feasibility(self):
        """检查可视化可行性（气泡图）"""
        print("\n[2/4] 检测气泡图可行性...")

        # 收集所有数据文件
        excel_files = list(self.course_path.rglob("*.xlsx")) + list(self.course_path.rglob("*.csv"))

        if not excel_files:
            print(f"      ⚠️ 未找到数据文件!")
            self.report.visualization_signal = False
            return

        # 合并所有数值字段
        all_numeric_cols = []
        all_categorical_cols = []
        non_null_rates = {}

        for f in excel_files:
            try:
                if f.suffix == '.xlsx':
                    xl = pd.ExcelFile(f)
                    for sheet in xl.sheet_names:
                        df = pd.read_excel(f, sheet_name=sheet)
                        for col in df.columns:
                            if pd.api.types.is_numeric_dtype(df[col]):
                                all_numeric_cols.append(col)
                                non_null_rates[col] = df[col].notna().mean()
                            else:
                                all_categorical_cols.append(col)
                else:
                    df = pd.read_csv(f)
                    for col in df.columns:
                        if pd.api.types.is_numeric_dtype(df[col]):
                            all_numeric_cols.append(col)
                            non_null_rates[col] = df[col].notna().mean()
                        else:
                            all_categorical_cols.append(col)
            except Exception as e:
                print(f"      读取失败: {f.name}")

        # 去重
        numeric_unique = list(dict.fromkeys(all_numeric_cols))
        categorical_unique = list(dict.fromkeys(all_categorical_cols))

        print(f"      数值字段: {len(numeric_unique)} 个")
        print(f"      分类字段: {len(categorical_unique)} 个")

        # 气泡图需要: X轴(数值) + Y轴(数值) + 气泡大小(数值) + 颜色(分类)
        bubble_ready = len(numeric_unique) >= 3
        high_quality_data = all(rate > 0.9 for rate in non_null_rates.values()) if non_null_rates else False

        self.report.visualization_result = VisualizationCheckResult(
            numeric_columns=len(numeric_unique),
            categorical_columns=len(categorical_unique),
            can_draw_bubble_chart=bubble_ready,
            bubble_requirements={
                'X_axis_numeric': len(numeric_unique) >= 1,
                'Y_axis_numeric': len(numeric_unique) >= 2,
                'bubble_size_numeric': len(numeric_unique) >= 3,
                'color_category': len(categorical_unique) >= 1,
                'high_quality_data': high_quality_data
            },
            non_null_rates=non_null_rates,
            issues=["数值字段不足3个，无法绘制气泡图"] if not bubble_ready else []
        )

        self.report.visualization_signal = bubble_ready and high_quality_data

        status = "✅" if self.report.visualization_signal else "❌"
        print(f"      {status} 气泡图支持: {'是' if bubble_ready else '否'} ({len(numeric_unique)}个数值字段)")

    def _check_business_logic(self):
        """检查商业逻辑"""
        print("\n[3/4] 检测商业逻辑...")

        excel_files = list(self.course_path.rglob("*.xlsx")) + list(self.course_path.rglob("*.csv"))

        if not excel_files:
            print(f"      ⚠️ 未找到数据文件!")
            self.report.logic_signal = False
            return

        total_rows = 0
        months_covered = set()
        logic_errors = []

        for f in excel_files:
            try:
                if f.suffix == '.xlsx':
                    xl = pd.ExcelFile(f)
                    for sheet in xl.sheet_names:
                        df = pd.read_excel(f, sheet_name=sheet)
                        total_rows += len(df)

                        # 检查日期字段
                        for col in df.columns:
                            col_lower = col.lower()
                            if 'date' in col_lower or '日期' in col or '时间' in col or '月份' in col:
                                try:
                                    # 尝试多种日期格式
                                    dates = pd.to_datetime(df[col], errors='coerce', format='%Y-%m')
                                    if dates.isna().all():
                                        dates = pd.to_datetime(df[col], errors='coerce')
                                    if len(dates.dropna()) > 0:
                                        months_covered.update(dates.dt.month.tolist())
                                except Exception as e:
                                    pass

                        # 检查销售和利润逻辑
                        for col in df.columns:
                            col_lower = col.lower()
                            if 'sales' in col_lower or '销售额' in col:
                                if (df[col] < 0).any():
                                    logic_errors.append(f"{f.name}: 存在负销售额")
                            elif 'profit' in col_lower or '利润' in col:
                                # 假设存在销售额字段，检查利润是否合理
                                pass

                else:
                    df = pd.read_csv(f)
                    total_rows += len(df)
            except Exception as e:
                print(f"      读取失败: {f.name}")

        time_span = len(months_covered)
        is_valid = len(logic_errors) == 0 and time_span >= 1

        self.report.business_logic_result = BusinessLogicResult(
            data_rows=total_rows,
            time_span_months=time_span,
            logic_errors=logic_errors,
            is_logically_valid=is_valid
        )

        self.report.logic_signal = is_valid

        status = "✅" if is_valid else "⚠️"
        print(f"      {status} 数据行数: {total_rows}")
        print(f"      {status} 时间跨度: {time_span} 个月")

    def _check_consistency(self):
        """检查手册与数据一致性"""
        print("\n[4/4] 检测手册与数据一致性...")

        # 查找实训手册
        manual_files = list(self.course_path.rglob("*.md")) + list(self.course_path.rglob("*.pdf"))

        # 收集所有数据字段
        excel_files = list(self.course_path.rglob("*.xlsx")) + list(self.course_path.rglob("*.csv"))
        all_headers = set()

        for f in excel_files:
            try:
                if f.suffix == '.xlsx':
                    xl = pd.ExcelFile(f)
                    for sheet in xl.sheet_names:
                        df = pd.read_excel(f, sheet_name=sheet)
                        all_headers.update(df.columns.tolist())
                else:
                    df = pd.read_csv(f)
                    all_headers.update(df.columns.tolist())
            except:
                pass

        # 提取手册中的关键字段（从markdown中）
        manual_fields = set()
        for mf in manual_files:
            if mf.suffix == '.md':
                try:
                    content = mf.read_text(encoding='utf-8')

                    # 方法1: 提取Markdown表格第一列（字段名）
                    lines = content.split('\n')
                    in_table = False
                    table_header = []
                    for i, line in enumerate(lines):
                        line = line.strip()
                        if line.startswith('|') and not line.startswith('|-'):
                            if not in_table:
                                # 表头行
                                in_table = True
                                parts = re.findall(r'\|([^\|]+)', line)
                                table_header = [p.strip() for p in parts]
                            else:
                                # 数据行，提取第一列（字段名）
                                parts = re.findall(r'\|([^\|]+)', line)
                                if parts and len(parts) > 0:
                                    first_col = parts[0].strip()
                                    # 过滤：长度合适，不是数字，不是分隔符
                                    if first_col and 1 < len(first_col) < 20:
                                        if not all(c in '- :|' for c in first_col):
                                            if not first_col.replace('.', '').replace('%', '').isdigit():
                                                # 排除常见非字段名
                                                if first_col not in ['字段名', '说明', '示例', '数据类型', '格式', '指标', '公式']:
                                                    manual_fields.add(first_col)
                        elif line.startswith('|-'):
                            continue
                        else:
                            in_table = False

                    # 方法2: 从代码块中提取
                    code_fields = re.findall(r'`([\w\u4e00-\u9fa5]+)`', content)
                    for f in code_fields:
                        if len(f) > 1 and len(f) < 20:
                            manual_fields.add(f)

                except Exception as e:
                    pass

        print(f"      手册提取字段: {list(manual_fields)}")

        # 计算匹配率
        headers_lower = {h.lower(): h for h in all_headers}
        manual_lower = {f.lower(): f for f in manual_fields}

        matched = []
        mismatched = []

        for m_field_lower, m_field in manual_lower.items():
            found = any(m_field_lower in h.lower() or h.lower() in m_field_lower for h in all_headers)
            if found:
                matched.append(m_field)
            else:
                mismatched.append(m_field)

        match_rate = len(matched) / len(manual_fields) if manual_fields else 1.0
        is_consistent = match_rate >= 0.95

        self.report.consistency_result = ConsistencyCheckResult(
            manual_fields=list(manual_fields),
            excel_headers=list(all_headers),
            matched_fields=matched,
            mismatched_fields=mismatched,
            match_rate=match_rate,
            is_consistent=is_consistent
        )

        self.report.consistency_signal = is_consistent

        status = "✅" if is_consistent else "⚠️"
        print(f"      {status} 手册字段匹配率: {match_rate*100:.1f}%")

    def _calculate_completion_signals(self):
        """计算三大结束标志"""
        # 标志1: 三大管理维度字段覆盖
        self.report.signal1_dimension_covered = self.report.dimension_signal

        # 标志2: 气泡图三维支撑
        self.report.signal2_bubble_supported = self.report.visualization_signal

        # 标志3: 手册与数据一致
        self.report.signal3_consistent = self.report.consistency_signal

        # 综合状态
        self.report.all_passed = (
            self.report.signal1_dimension_covered and
            self.report.signal2_bubble_supported and
            self.report.signal3_consistent
        )

        # 生成修复建议
        if not self.report.signal1_dimension_covered:
            missing = [r.dimension_name for r in self.report.dimension_results if not r.is_complete]
            self.report.fix_suggestions.append(f"缺失管理维度: {', '.join(missing)}")

        if not self.report.signal2_bubble_supported:
            self.report.fix_suggestions.append("数值字段不足3个，无法绘制气泡图")

        if not self.report.signal3_consistent:
            self.report.fix_suggestions.append("手册字段与Excel表头不一致")

    def _print_results(self):
        """打印结果"""
        print("\n" + "=" * 70)
        print(">>> 监测完成! 三大标志状态:")
        print("=" * 70)
        print(f"    标志1 (维度覆盖): {'✅ 通过' if self.report.signal1_dimension_covered else '❌ 未通过'}")
        print(f"    标志2 (气泡图支撑): {'✅ 通过' if self.report.signal2_bubble_supported else '❌ 未通过'}")
        print(f"    标志3 (数据一致): {'✅ 通过' if self.report.signal3_consistent else '❌ 未通过'}")
        print()
        if self.report.all_passed:
            print("    🎉 综合状态: ✅ 全部通过 - 可封版")
        else:
            print("    ⚠️ 综合状态: ❌ 部分未通过 - 需修复")
            print("\n    修复建议:")
            for suggestion in self.report.fix_suggestions:
                print(f"      - {suggestion}")
        print("=" * 70)

    def _export_html_report(self):
        """导出HTML报告"""
        html_path = Path("/Users/jimfu/Work/huixue/frontend/public")
        html_path.mkdir(parents=True, exist_ok=True)

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>零售经营分析课程 - 质量监测报告</title>
    <script src="/js/platform-config.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
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
        .stat-value {{ font-size: 28px; font-weight: 700; color: #f5576c; }}
        .stat-label {{ font-size: 12px; color: #666; margin-top: 4px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
        th, td {{ text-align: left; border-bottom: 1px solid #e9ecef; padding: 8px; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #666; }}
        .pass {{ color: #28a745; }}
        .fail {{ color: #dc3545; }}
        .warning-box {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏪 零售经营分析课程 - 质量监测报告</h1>
        <p class="subtitle">基于 MCP 视角的自动化质量检测 | 检测时间: {self.report.timestamp}</p>

        <!-- 状态横幅 -->
        <div class="status-banner {'status-pass' if self.report.all_passed else 'status-fail'}">
            {'✅ 全部通过 - 可封版' if self.report.all_passed else '❌ 部分未通过 - 需修复'}
        </div>

        <!-- 三大标志 -->
        <div class="summary-grid">
            <div class="signal-card {'signal-pass' if self.report.signal1_dimension_covered else 'signal-fail'}">
                <div class="signal-icon">{'✅' if self.report.signal1_dimension_covered else '❌'}</div>
                <div class="signal-title">标志1: 维度覆盖</div>
                <div class="signal-value">{'通过' if self.report.signal1_dimension_covered else '缺失维度'}</div>
            </div>
            <div class="signal-card {'signal-pass' if self.report.signal2_bubble_supported else 'signal-fail'}">
                <div class="signal-icon">{'✅' if self.report.signal2_bubble_supported else '❌'}</div>
                <div class="signal-title">标志2: 气泡图支撑</div>
                <div class="signal-value">{'支持' if self.report.signal2_bubble_supported else '数值不足'}</div>
            </div>
            <div class="signal-card {'signal-pass' if self.report.signal3_consistent else 'signal-fail'}">
                <div class="signal-icon">{'✅' if self.report.signal3_consistent else '⚠️'}</div>
                <div class="signal-title">标志3: 数据一致</div>
                <div class="signal-value">{'一致' if self.report.signal3_consistent else '需核对'}</div>
            </div>
        </div>

        <!-- 统计概览 -->
        <div class="card">
            <h2>📊 资源概览</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{self.report.total_files}</div>
                    <div class="stat-label">文件总数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.total_datasets}</div>
                    <div class="stat-label">数据集</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.business_logic_result.data_rows}</div>
                    <div class="stat-label">数据行数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.business_logic_result.time_span_months}</div>
                    <div class="stat-label">时间跨度(月)</div>
                </div>
            </div>
        </div>

        <!-- 维度覆盖检测 -->
        <div class="card">
            <h2>📋 三大管理维度覆盖</h2>
            <table>
                <thead>
                    <tr>
                        <th>维度</th>
                        <th>必需字段</th>
                        <th>已发现</th>
                        <th>覆盖率</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
"""
        for r in self.report.dimension_results:
            status = "✅" if r.is_complete else "❌"
            html_content += f"""
                    <tr>
                        <td>{r.dimension_name}</td>
                        <td>{', '.join(r.required_fields[:3])}...</td>
                        <td>{len(r.found_fields)} 个</td>
                        <td>{r.coverage_rate*100:.0f}%</td>
                        <td class="{'pass' if r.is_complete else 'fail'}">{status}</td>
                    </tr>
"""

        html_content += f"""
                </tbody>
            </table>
        </div>

        <!-- 可视化可行性 -->
        <div class="card">
            <h2>📈 气泡图可行性</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{self.report.visualization_result.numeric_columns}</div>
                    <div class="stat-label">数值字段</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.visualization_result.categorical_columns}</div>
                    <div class="stat-label">分类字段</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{'✅' if self.report.visualization_result.can_draw_bubble_chart else '❌'}</div>
                    <div class="stat-label">气泡图</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{'✅' if all(self.report.visualization_result.non_null_rates.values()) else '⚠️'}</div>
                    <div class="stat-label">数据质量</div>
                </div>
            </div>
        </div>

        <!-- 商业逻辑 -->
        <div class="card">
            <h2>🧮 商业逻辑检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{self.report.business_logic_result.data_rows}</div>
                    <div class="stat-label">数据行数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.business_logic_result.time_span_months}</div>
                    <div class="stat-label">月份数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{'✅' if self.report.business_logic_result.is_logically_valid else '⚠️'}</div>
                    <div class="stat-label">逻辑有效</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(self.report.business_logic_result.logic_errors)}</div>
                    <div class="stat-label">逻辑错误</div>
                </div>
            </div>
            {'<div class="warning-box">发现问题: ' + '; '.join(self.report.business_logic_result.logic_errors) + '</div>' if self.report.business_logic_result.logic_errors else ''}
        </div>

        <!-- 数据一致性 -->
        <div class="card">
            <h2>📝 手册-数据一致性</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{len(self.report.consistency_result.manual_fields)}</div>
                    <div class="stat-label">手册字段</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(self.report.consistency_result.excel_headers)}</div>
                    <div class="stat-label">Excel表头</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.consistency_result.match_rate*100:.0f}%</div>
                    <div class="stat-label">匹配率</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{'✅' if self.report.consistency_result.is_consistent else '⚠️'}</div>
                    <div class="stat-label">一致</div>
                </div>
            </div>
        </div>

        <!-- 修复建议 -->
        {''.join([f'<div class="warning-box">修复建议: {s}</div>' for s in self.report.fix_suggestions]) if self.report.fix_suggestions else ''}

        <!-- 结束状态 -->
        <div class="card" style="text-align: center; padding: 30px;">
            <h2 style="justify-content: center;">{'🎉 资源已锁定 - 可封版' if self.report.all_passed else '⚠️ 需要修复后封版'}</h2>
            <p style="margin-top: 12px; color: #666;">
                课程资源状态: <strong>{'已封版' if self.report.all_passed else '待修复'}</strong>
                | 监测日期: {self.report.timestamp.split()[0]}
            </p>
        </div>

        <p style="text-align: center; color: rgba(255,255,255,0.7); margin-top: 20px; font-size: 12px;">
            慧学 平台 | 基于 MCP 视角的自动化质量检测系统
        </p>
    </div>
</body>
</html>
"""
        report_path = html_path / "retail-analysis-monitoring-report.html"
        report_path.write_text(html_content, encoding='utf-8')
        print(f"\n✅ HTML报告已生成: {report_path}")


def main():
    """主函数"""
    import sys
    # 默认路径
    course_path = "/Users/jimfu/Work/huixue/ziyuan_data/课程资源/零售经营分析"

    if len(sys.argv) > 1:
        course_path = sys.argv[1]

    monitor = RetailAnalysisCourseMonitor(course_path)
    monitor.run()

    return monitor.report


if __name__ == "__main__":
    main()
