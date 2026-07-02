#!/usr/bin/env python3
"""
公募基金精准营销课程监测脚本
============================

基于 MCP 视角的自动化质量监测系统

监测维度:
1. 资产维度 - 金融合规与脱敏（PII扫描）
2. 技术维度 - 不均衡样本处理（SMOTE/class_weight）
3. 逻辑维度 - 双模型与业务输出（KMeans + 分类 + 外呼名单）

三大结束标志:
- 标志1: 隐私脱敏率100%
- 标志2: 不均衡处理逻辑存在
- 标志3: 营销提升度可视化（ROC/Lift）
"""

import os
import re
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


@dataclass
class PIICheckResult:
    """PII检测结果"""
    column_name: str
    pii_type: str  # phone, id_card, name, bank_card
    leaked_count: int = 0
    sample_values: List[str] = field(default_factory=list)
    is_masked: bool = False


@dataclass
class ImbalanceCheckResult:
    """不均衡检测结果"""
    total_samples: int = 0
    positive_samples: int = 0
    negative_samples: int = 0
    positive_rate: float = 0.0
    is_balanced: bool = False
    has_handling_code: bool = False
    handling_method: str = ""  # SMOTE, class_weight, etc.
    is_valid: bool = True
    issues: List[str] = field(default_factory=list)


@dataclass
class ModelCheckResult:
    """模型检测结果"""
    has_clustering_model: bool = False
    clustering_algorithm: str = ""
    has_predictive_model: bool = False
    predictive_algorithm: str = ""
    has_business_output: bool = False
    output_file: str = ""
    has_evaluation_plot: bool = False
    evaluation_type: str = ""  # ROC, Lift, etc.
    issues: List[str] = field(default_factory=list)


@dataclass
class FundMarketingMonitorReport:
    """公募基金营销课程监测报告"""
    timestamp: str = ""
    course_name: str = "公募基金精准营销"

    # 维度1: PII合规
    pii_results: List[PIICheckResult] = field(default_factory=list)
    pii_leak_count: int = 0
    privacy_signal: bool = False

    # 维度2: 不均衡处理
    imbalance_result: ImbalanceCheckResult = field(default_factory=lambda: ImbalanceCheckResult())
    imbalance_signal: bool = False

    # 维度3: 双模型与业务
    model_result: ModelCheckResult = field(default_factory=lambda: ModelCheckResult())
    model_signal: bool = False

    # 统计
    total_datasets: int = 0
    total_code_files: int = 0

    # 三大标志
    signal1_privacy_protected: bool = False  # 隐私脱敏
    signal2_imbalance_handled: bool = False  # 不均衡处理
    signal3_lift_visualized: bool = False    # 提升度可视化
    all_passed: bool = False

    # 修复建议
    fix_suggestions: List[str] = field(default_factory=list)


class FundMarketingCourseMonitor:
    """公募基金精准营销课程监测器"""

    def __init__(self, course_path: str):
        self.course_path = Path(course_path)
        self.report = FundMarketingMonitorReport()
        self.report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def run(self):
        """执行完整监测"""
        print("=" * 70)
        print(">>> 开始 公募基金精准营销课程监测")
        print("=" * 70)

        # 步骤1: 检测PII合规
        self._check_pii_compliance()

        # 步骤2: 检测不均衡处理
        self._check_imbalance_handling()

        # 步骤3: 检测双模型与业务输出
        self._check_dual_model_business()

        # 计算结束标志
        self._calculate_completion_signals()

        # 生成报告
        self._print_results()
        self._export_html_report()

        return self.report

    def _check_pii_compliance(self):
        """检查PII合规性"""
        print("\n[1/3] 检测金融数据PII合规性...")

        # PII正则表达式
        PII_PATTERNS = {
            'phone': (r'1[3-9]\d{9}', '手机号'),
            'id_card': (r'\d{17}[\dXx]', '身份证号'),
            'bank_card': (r'\d{16,19}', '银行卡号'),
            'name': (r'^[\u4e00-\u9fa5]{2,4}$', '中文姓名')
        }

        # 数据文件
        excel_files = list(self.course_path.rglob("*.xlsx")) + list(self.course_path.rglob("*.csv"))
        self.report.total_datasets = len(excel_files)

        total_leaks = 0

        for f in excel_files:
            try:
                if f.suffix == '.xlsx':
                    xl = pd.ExcelFile(f)
                    for sheet in xl.sheet_names:
                        df = pd.read_excel(f, sheet_name=sheet, nrows=100)
                        self._scan_pii_in_df(df, f.name, total_leaks)
                else:
                    df = pd.read_csv(f, nrows=100)
                    self._scan_pii_in_df(df, f.name, total_leaks)
            except Exception as e:
                print(f"      读取失败: {f.name} - {e}")

        # 统计泄漏
        for result in self.report.pii_results:
            if not result.is_masked and result.leaked_count > 0:
                total_leaks += result.leaked_count

        self.report.pii_leak_count = total_leaks
        self.report.privacy_signal = total_leaks == 0

        status = "✅" if self.report.privacy_signal else "❌"
        print(f"      {status} PII泄漏检测: {total_leaks} 处")

    def _scan_pii_in_df(self, df: pd.DataFrame, filename: str, total_leaks: int):
        """扫描DataFrame中的PII"""
        PII_PATTERNS = {
            'phone': (r'1[3-9]\d{9}', '手机号'),
            'id_card': (r'\d{17}[\dXx]', '身份证号'),
            'bank_card': (r'\d{16,19}', '银行卡号'),
        }

        for col in df.columns:
            col_str = str(col).lower()
            sample_value = str(df[col].iloc[0]) if len(df) > 0 else ""

            # 检查是否掩码列（如手机号列包含***）
            is_masked = any(marker in sample_value for marker in ['*', '***', 'XXX', 'xxxx'])

            # 检测手机号
            if '手机' in col_str or 'phone' in col_str or 'tel' in col_str:
                if is_masked:
                    result = PIICheckResult(column_name=col, pii_type='phone', is_masked=True)
                    self.report.pii_results.append(result)
                else:
                    # 检查是否有明文手机号
                    for _, val in df[col].astype(str).items():
                        if re.match(r'1[3-9]\d{9}', val):
                            result = PIICheckResult(
                                column_name=col, pii_type='phone',
                                leaked_count=df[col].astype(str).str.match(r'1[3-9]\d{9}').sum(),
                                sample_values=list(df[col].head(3).astype(str)),
                                is_masked=False
                            )
                            self.report.pii_results.append(result)
                            break

            # 检测身份证号
            if '身份证' in col_str or 'id_card' in col_str or 'idno' in col_str:
                if is_masked:
                    result = PIICheckResult(column_name=col, pii_type='id_card', is_masked=True)
                    self.report.pii_results.append(result)
                else:
                    result = PIICheckResult(
                        column_name=col, pii_type='id_card',
                        leaked_count=df[col].astype(str).str.match(r'\d{17}[\dXx]').sum(),
                        sample_values=list(df[col].head(3).astype(str)),
                        is_masked=False
                    )
                    self.report.pii_results.append(result)

            # 检测银行卡号
            if '银行卡' in col_str or 'bank_card' in col_str or 'card_no' in col_str:
                if is_masked:
                    result = PIICheckResult(column_name=col, pii_type='bank_card', is_masked=True)
                    self.report.pii_results.append(result)

    def _check_imbalance_handling(self):
        """检查不均衡处理"""
        print("\n[2/3] 检测不均衡样本处理...")

        # 数据文件
        excel_files = list(self.course_path.rglob("*.xlsx")) + list(self.course_path.rglob("*.csv"))

        # 查找可能的目标列
        target_columns = ['subscribe', 'y', 'label', 'target', 'buy', 'is_buy', '购买', '是否购买']

        positive_count = 0
        total_count = 0
        target_col_found = None

        for f in excel_files:
            try:
                if f.suffix == '.xlsx':
                    xl = pd.ExcelFile(f)
                    for sheet in xl.sheet_names:
                        df = pd.read_excel(f, sheet_name=sheet, nrows=10000)
                        for col in df.columns:
                            if any(col.lower() == t.lower() for t in target_columns):
                                target_col_found = col
                                total_count = len(df)
                                positive_count = df[col].sum()
                                break
                else:
                    df = pd.read_csv(f, nrows=10000)
                    for col in df.columns:
                        if any(col.lower() == t.lower() for t in target_columns):
                            target_col_found = col
                            total_count = len(df)
                            positive_count = df[col].sum()
                            break
            except:
                pass

        # 计算正样本比例
        positive_rate = positive_count / total_count if total_count > 0 else 0

        print(f"      正样本比例: {positive_rate*100:.2f}%")

        # 检查代码中的不均衡处理
        code_files = list(self.course_path.rglob("*.py"))
        self.report.total_code_files = len(code_files)

        has_smote = False
        has_class_weight = False
        has_resample = False

        for cf in code_files:
            try:
                content = cf.read_text(encoding='utf-8')
                content_lower = content.lower()

                if 'smote' in content_lower:
                    has_smote = True
                if 'class_weight' in content_lower:
                    has_class_weight = True
                if 'resample' in content_lower:
                    has_resample = True
            except:
                pass

        has_handling = has_smote or has_class_weight or has_resample
        handling_method = []
        if has_smote:
            handling_method.append('SMOTE')
        if has_class_weight:
            handling_method.append('class_weight')
        if has_resample:
            handling_method.append('resample')

        # 判定
        is_balanced = 0.3 <= positive_rate <= 0.7  # 30%-70%认为是平衡的
        is_valid = is_balanced or has_handling

        issues = []
        if not is_balanced and not has_handling:
            issues.append("正样本比例过低且无SMOTE/class_weight处理")

        self.report.imbalance_result = ImbalanceCheckResult(
            total_samples=total_count,
            positive_samples=int(positive_count),
            negative_samples=int(total_count - positive_count),
            positive_rate=positive_rate,
            is_balanced=is_balanced,
            has_handling_code=has_handling,
            handling_method=', '.join(handling_method),
            is_valid=is_valid,
            issues=issues
        )

        self.report.imbalance_signal = is_valid

        status = "✅" if self.report.imbalance_signal else "⚠️"
        print(f"      {status} 不均衡处理: {'已处理' if has_handling else '未处理'}")
        print(f"      {status} 正样本比例: {positive_rate*100:.2f}%")

    def _check_dual_model_business(self):
        """检查双模型与业务输出"""
        print("\n[3/3] 检测双模型与业务输出...")

        # 算法正则
        CLUSTERING_ALGOS = {
            'kmeans': r'\bKMeans\b',
            'dbscan': r'\bDBSCAN\b',
            'hierarchical': r'\bHierarchical\b|AgglomerativeClustering'
        }

        PREDICTIVE_ALGOS = {
            'logistic': r'\bLogisticRegression\b',
            'random_forest': r'\bRandomForest\b',
            'xgboost': r'\bXGBoost\b|梯度提升',
            'lightgbm': r'\bLightGBM\b',
            'lr': r'\blinear_model\.LogisticRegression\b'
        }

        EVALUATION_PLOTS = {
            'roc': r'\bROC\b|roc_curve|plot_roc',
            'lift': r'\bLift\b|lift_chart|plot_lift',
            'pr': r'\bPR\b|precision_recall'
        }

        # 扫描代码
        code_files = list(self.course_path.rglob("*.py")) + list(self.course_path.rglob("*.ipynb"))
        self.report.total_code_files = len(code_files)

        has_clustering = False
        clustering_name = ""
        has_predictive = False
        predictive_name = ""
        has_business_output = False
        output_file = ""
        has_evaluation_plot = False
        evaluation_type = ""

        for cf in code_files:
            try:
                content = cf.read_text(encoding='utf-8')
                content_lower = content.lower()

                # 检查聚类模型
                for algo, pattern in CLUSTERING_ALGOS.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        has_clustering = True
                        clustering_name = algo.upper()
                        break

                # 检查预测模型
                for algo, pattern in PREDICTIVE_ALGOS.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        has_predictive = True
                        predictive_name = algo.upper()
                        break

                # 检查业务输出
                if re.search(r'call_list|外呼名单|高意向|top.*customer', content_lower):
                    has_business_output = True
                    output_match = re.search(r'to_csv\([\'"]?([^\'")]+)', content)
                    output_file = output_match.group(1) if output_match else "外呼名单.csv"

                # 检查评估图表
                for plot_type, pattern in EVALUATION_PLOTS.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        has_evaluation_plot = True
                        evaluation_type = plot_type.upper()
                        break
            except:
                pass

        issues = []
        if not has_clustering:
            issues.append("缺少聚类模型（KMeans/DBSCAN）")
        if not has_predictive:
            issues.append("缺少预测模型（LogisticRegression/RandomForest/XGBoost）")
        if not has_business_output:
            issues.append("缺少外呼名单导出")
        if not has_evaluation_plot:
            issues.append("缺少ROC/Lift曲线可视化")

        self.report.model_result = ModelCheckResult(
            has_clustering_model=has_clustering,
            clustering_algorithm=clustering_name,
            has_predictive_model=has_predictive,
            predictive_algorithm=predictive_name,
            has_business_output=has_business_output,
            output_file=output_file,
            has_evaluation_plot=has_evaluation_plot,
            evaluation_type=evaluation_type,
            issues=issues
        )

        self.report.model_signal = has_clustering and has_predictive and has_business_output

        status = "✅" if self.report.model_signal else "⚠️"
        print(f"      {status} 聚类模型: {clustering_name if has_clustering else '未检测到'}")
        print(f"      {status} 预测模型: {predictive_name if has_predictive else '未检测到'}")
        print(f"      {status} 业务输出: {output_file if has_business_output else '未检测到'}")
        print(f"      {status} 评估图表: {evaluation_type if has_evaluation_plot else '未检测到'}")

    def _calculate_completion_signals(self):
        """计算三大结束标志"""
        # 标志1: 隐私脱敏
        self.report.signal1_privacy_protected = self.report.privacy_signal

        # 标志2: 不均衡处理
        self.report.signal2_imbalance_handled = self.report.imbalance_signal

        # 标志3: 提升度可视化
        self.report.signal3_lift_visualized = self.report.model_result.has_evaluation_plot

        # 综合状态
        self.report.all_passed = (
            self.report.signal1_privacy_protected and
            self.report.signal2_imbalance_handled and
            self.report.signal3_lift_visualized
        )

        # 生成修复建议
        if not self.report.signal1_privacy_protected:
            self.report.fix_suggestions.append("发现明文PII数据，请进行脱敏处理")

        if not self.report.signal2_imbalance_handled:
            self.report.fix_suggestions.append("正样本比例过低，需添加SMOTE或class_weight处理")

        if not self.report.signal3_lift_visualized:
            self.report.fix_suggestions.append("缺少ROC或Lift曲线可视化代码")

    def _print_results(self):
        """打印结果"""
        print("\n" + "=" * 70)
        print(">>> 监测完成! 三大标志状态:")
        print("=" * 70)
        print(f"    标志1 (隐私脱敏): {'✅ 通过' if self.report.signal1_privacy_protected else '❌ 未通过'}")
        print(f"    标志2 (不均衡处理): {'✅ 通过' if self.report.signal2_imbalance_handled else '❌ 未通过'}")
        print(f"    标志3 (提升可视化): {'✅ 通过' if self.report.signal3_lift_visualized else '❌ 未通过'}")
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
    <title>公募基金精准营销课程 - 质量监测报告</title>
    <script src="/js/platform-config.js"></script>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
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
        .stat-value {{ font-size: 28px; font-weight: 700; color: #11998e; }}
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
        <h1>💰 公募基金精准营销课程 - 质量监测报告</h1>
        <p class="subtitle">基于 MCP 视角的自动化质量检测 | 检测时间: {self.report.timestamp}</p>

        <!-- 状态横幅 -->
        <div class="status-banner {'status-pass' if self.report.all_passed else 'status-fail'}">
            {'✅ 全部通过 - 可封版' if self.report.all_passed else '❌ 部分未通过 - 需修复'}
        </div>

        <!-- 三大标志 -->
        <div class="summary-grid">
            <div class="signal-card {'signal-pass' if self.report.signal1_privacy_protected else 'signal-fail'}">
                <div class="signal-icon">{'✅' if self.report.signal1_privacy_protected else '❌'}</div>
                <div class="signal-title">标志1: 隐私脱敏</div>
                <div class="signal-value">{'已脱敏' if self.report.signal1_privacy_protected else '存在PII泄漏'}</div>
            </div>
            <div class="signal-card {'signal-pass' if self.report.signal2_imbalance_handled else 'signal-fail'}">
                <div class="signal-icon">{'✅' if self.report.signal2_imbalance_handled else '⚠️'}</div>
                <div class="signal-title">标志2: 不均衡处理</div>
                <div class="signal-value">{'已处理' if self.report.signal2_imbalance_handled else '需处理'}</div>
            </div>
            <div class="signal-card {'signal-pass' if self.report.signal3_lift_visualized else 'signal-fail'}">
                <div class="signal-icon">{'✅' if self.report.signal3_lift_visualized else '❌'}</div>
                <div class="signal-title">标志3: 提升可视化</div>
                <div class="signal-value">{'已展示' if self.report.signal3_lift_visualized else '缺失'}</div>
            </div>
        </div>

        <!-- 统计概览 -->
        <div class="card">
            <h2>📊 资源概览</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{self.report.total_datasets}</div>
                    <div class="stat-label">数据集</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.total_code_files}</div>
                    <div class="stat-label">代码文件</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.imbalance_result.positive_rate*100:.1f}%</div>
                    <div class="stat-label">正样本比例</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.pii_leak_count}</div>
                    <div class="stat-label">PII泄漏</div>
                </div>
            </div>
        </div>

        <!-- PII合规检测 -->
        <div class="card">
            <h2>🔒 PII合规检测</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{self.report.pii_leak_count}</div>
                    <div class="stat-label">泄漏数量</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{'✅' if self.report.privacy_signal else '❌'}</div>
                    <div class="stat-label">合规状态</div>
                </div>
            </div>
            {'<div class="warning-box">发现PII数据泄漏，请立即脱敏处理</div>' if self.report.pii_leak_count > 0 else ''}
        </div>

        <!-- 不均衡处理检测 -->
        <div class="card">
            <h2>⚖️ 不均衡样本处理</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{self.report.imbalance_result.total_samples}</div>
                    <div class="stat-label">总样本数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.imbalance_result.positive_rate*100:.1f}%</div>
                    <div class="stat-label">正样本比例</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.imbalance_result.handling_method if self.report.imbalance_result.handling_method else '无'}</div>
                    <div class="stat-label">处理方法</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{'✅' if self.report.imbalance_result.is_valid else '⚠️'}</div>
                    <div class="stat-label">有效性</div>
                </div>
            </div>
        </div>

        <!-- 双模型检测 -->
        <div class="card">
            <h2>🤖 双模型与业务输出</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{self.report.model_result.clustering_algorithm if self.report.model_result.has_clustering_model else '❌'}</div>
                    <div class="stat-label">聚类模型</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.model_result.predictive_algorithm if self.report.model_result.has_predictive_model else '❌'}</div>
                    <div class="stat-label">预测模型</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{'✅' if self.report.model_result.has_business_output else '❌'}</div>
                    <div class="stat-label">外呼名单</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{self.report.model_result.evaluation_type if self.report.model_result.has_evaluation_plot else '❌'}</div>
                    <div class="stat-label">评估图表</div>
                </div>
            </div>
        </div>

        <!-- 问题清单 -->
        {''.join([f'<div class="warning-box">问题: {issue}</div>' for issue in self.report.model_result.issues]) if self.report.model_result.issues else ''}

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
        report_path = html_path / "fund-marketing-monitoring-report.html"
        report_path.write_text(html_content, encoding='utf-8')
        print(f"\n✅ HTML报告已生成: {report_path}")


def main():
    """主函数"""
    import sys
    course_path = "/Users/jimfu/Work/huixue/ziyuan_data/课程资源/公募基金精准营销"

    if len(sys.argv) > 1:
        course_path = sys.argv[1]

    monitor = FundMarketingCourseMonitor(course_path)
    monitor.run()

    return monitor.report


if __name__ == "__main__":
    main()
