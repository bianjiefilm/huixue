#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据挖掘分析课程监测系统 (MCP视角)

监测维度:
1. 资产维度 - 算法矩阵检查 (19个核心算法代码覆盖)
2. 技术维度 - 随机性钳制 (random_state参数检测)
3. 依赖维度 - 可视化地狱检查 (Graphviz、Matplotlib中文)

三大结束标志:
- 标志1: 19个算法节点全点亮
- 标志2: 随机种子已锁定 (>90%)
- 标志3: Graphviz软着陆

使用方法:
    python3 monitor_data_mining_course.py [--course-path PATH] [--output OUTPUT]
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# 算法定义 (基于19个核心知识点)
# ============================================================================

ALGORITHMS = {
    # 分类算法
    "Logistic": {
        "name": "逻辑回归",
        "keywords": ["LogisticRegression", "logistic"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "分类"
    },
    "LDA": {
        "name": "线性判别分析",
        "keywords": ["LinearDiscriminantAnalysis", "LDA"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "分类"
    },
    "MultiClass": {
        "name": "多分类策略",
        "keywords": ["OneVsRestClassifier", "OneVsOneClassifier", "multiclass"],
        "library": "sklearn",
        "has_random_state": False,
        "category": "分类"
    },
    "DecisionTree": {
        "name": "决策树",
        "keywords": ["DecisionTreeClassifier", "DecisionTreeRegressor"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "分类"
    },
    "kNN": {
        "name": "K近邻",
        "keywords": ["KNeighborsClassifier", "KNeighborsRegressor", "KNeighbors"],
        "library": "sklearn",
        "has_random_state": False,
        "category": "分类"
    },
    "NaiveBayes": {
        "name": "朴素贝叶斯",
        "keywords": ["GaussianNB", "MultinomialNB", "BernoulliNB", "NaiveBayes"],
        "library": "sklearn",
        "has_random_state": False,
        "category": "分类"
    },
    "NeuralNet": {
        "name": "神经网络(MLP)",
        "keywords": ["MLPClassifier", "MLPRegressor", "NeuralNetwork"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "分类"
    },
    "RandomForest": {
        "name": "随机森林",
        "keywords": ["RandomForestClassifier", "RandomForestRegressor"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "集成学习"
    },
    "Adaboost": {
        "name": "Adaboost",
        "keywords": ["AdaBoostClassifier", "AdaBoostRegressor", "AdaBoost"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "集成学习"
    },
    # 回归算法
    "LinearReg": {
        "name": "线性回归",
        "keywords": ["LinearRegression", "Ridge", "Lasso"],
        "library": "sklearn",
        "has_random_state": False,
        "category": "回归"
    },
    # 聚类算法
    "KMeans": {
        "name": "K-Means聚类",
        "keywords": ["KMeans", "K-means"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "聚类"
    },
    "DBSCAN": {
        "name": "DBSCAN聚类",
        "keywords": ["DBSCAN"],
        "library": "sklearn",
        "has_random_state": False,
        "category": "聚类"
    },
    "AGNES": {
        "name": "AGNES聚类",
        "keywords": ["AgglomerativeClustering", "AGNES"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "聚类"
    },
    "GMM": {
        "name": "高斯混合模型",
        "keywords": ["GaussianMixture", "GMM"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "聚类"
    },
    "ClusteringMetrics": {
        "name": "聚类评估指标",
        "keywords": ["silhouette_score", "calinski_harabasz_score", "davies_bouldin_score"],
        "library": "sklearn",
        "has_random_state": False,
        "category": "聚类"
    },
    # 降维算法
    "PCA": {
        "name": "PCA主成分分析",
        "keywords": ["PCA", "PrincipalComponentAnalysis"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "降维"
    },
    "MDS": {
        "name": "MDS多维缩放",
        "keywords": ["MDS", "MultidimensionalScaling"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "降维"
    },
    # 基础概念
    "Intro": {
        "name": "机器学习绪论",
        "keywords": ["train_test_split", "cross_val_score", "GridSearchCV"],
        "library": "sklearn",
        "has_random_state": True,
        "category": "基础"
    },
    "Evaluation": {
        "name": "模型评估",
        "keywords": ["accuracy_score", "precision_score", "recall_score", "f1_score",
                     "confusion_matrix", "roc_auc_score", "classification_report"],
        "library": "sklearn",
        "has_random_state": False,
        "category": "基础"
    }
}

# 需要random_state的算法函数
RANDOM_STATE_FUNCTIONS = {
    "train_test_split": True,
    "KMeans": True,
    "KNeighborsClassifier": False,  # n_neighbors不依赖random_state
    "KNeighborsRegressor": False,
    "DecisionTreeClassifier": True,
    "DecisionTreeRegressor": True,
    "RandomForestClassifier": True,
    "RandomForestRegressor": True,
    "LogisticRegression": True,
    "LinearDiscriminantAnalysis": True,
    "MLPClassifier": True,
    "MLPRegressor": True,
    "AdaBoostClassifier": True,
    "GaussianMixture": True,
    "AgglomerativeClustering": True,
    "PCA": True,
    "MDS": True,
}

# Graphviz相关
GRAPHVIZ_FUNCTIONS = ["export_graphviz", "export_to_graphviz", "graphviz"]

# 默认路径
DEFAULT_COURSE_PATH = "/Users/jimfu/Work/huixue/ziyuan_data/课程资源/数据挖掘分析"
DEFAULT_OUTPUT_PATH = "/Users/jimfu/Work/huixue/frontend/public/data-mining-monitoring-report.html"


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class AlgorithmCheckResult:
    """算法检查结果"""
    algo_id: str
    algo_name: str
    category: str
    detected: bool = False
    file_count: int = 0
    has_random_state: bool = True  # 如果需要，是否检测到random_state
    issues: List[str] = field(default_factory=list)


@dataclass
class RandomStateCheckResult:
    """随机种子检查结果"""
    file_path: str
    total_calls: int = 0
    calls_with_seed: int = 0
    coverage_rate: float = 0.0
    missing_seeds: List[str] = field(default_factory=list)


@dataclass
class GraphvizCheckResult:
    """Graphviz检查结果"""
    file_path: str
    has_graphviz_call: bool = False
    has_fallback: bool = False  # 是否有export_text降级
    has_install_guide: bool = False  # 是否有安装指引
    issues: List[str] = field(default_factory=list)


@dataclass
class DataMiningMonitorReport:
    """数据挖掘课程监测报告"""
    timestamp: str = ""
    course_name: str = "数据挖掘分析"

    # 维度1: 算法覆盖
    algorithms: Dict[str, AlgorithmCheckResult] = field(default_factory=dict)
    missing_algorithm_count: int = 0
    coverage_rate: float = 0.0

    # 维度2: 随机种子
    random_state_results: List[RandomStateCheckResult] = field(default_factory=list)
    random_seed_coverage: float = 0.0
    random_seed_passed: bool = True

    # 维度3: 可视化依赖
    graphviz_results: List[GraphvizCheckResult] = field(default_factory=list)
    graphviz_safe: bool = True
    graphviz_issues: List[str] = field(default_factory=list)

    # 文件统计
    total_py_files: int = 0
    total_ipynb_files: int = 0

    # 三大标志
    coverage_signal: bool = False  # 标志1: 19算法覆盖
    deterministic_signal: bool = False  # 标志2: 随机种子锁定
    visualization_signal: bool = False  # 标志3: Graphviz软着陆
    all_passed: bool = False

    # 综合状态
    @property
    def status(self) -> str:
        if self.all_passed:
            return "已封版"
        elif self.coverage_rate >= 80 and self.random_seed_coverage >= 0.8:
            return "待完善"
        else:
            return "需修复"


# ============================================================================
# 监测器类
# ============================================================================

class DataMiningCourseMonitor:
    """数据挖掘课程监测器"""

    def __init__(self, course_path: str):
        self.course_path = Path(course_path)
        self.report = DataMiningMonitorReport()
        self.report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 编译正则表达式
        self.random_state_pattern = re.compile(r'random_state\s*=\s*([A-Za-z_]\w*|\d+|None)')
        self.graphviz_pattern = re.compile(r'(?:export_graphviz|export_to_graphviz|graphviz)')
        self.graphviz_fallback_pattern = re.compile(r'export_text')
        self.chinese_font_patterns = [
            re.compile(r"rcParams\['font\.sans-serif'\].*SimHei"),
            re.compile(r"rcParams\['font\.sans-serif'\].*Microsoft"),
            re.compile(r"rcParams\['font\.sans-serif'\].*WenQuanYi"),
            re.compile(r"rcParams\['font\.sans-serif'\].*PingFang"),
        ]

    def run_full_scan(self) -> DataMiningMonitorReport:
        """执行完整扫描"""
        print("=" * 60)
        print(">>> 开始 数据挖掘分析课程监测")
        print("=" * 60)

        # 维度1: 算法矩阵检查
        print("\n[1/3] 检查19个算法代码覆盖...")
        self._check_algorithm_coverage()
        print(f"      覆盖统计: {self.report.coverage_rate:.1f}%, 空缺算法: {self.report.missing_algorithm_count}")

        # 维度2: 随机性钳制检查
        print("\n[2/3] 检测随机种子配置...")
        self._check_random_state()
        print(f"      随机种子覆盖率: {self.report.random_seed_coverage:.1%}")

        # 维度3: 可视化依赖检查
        print("\n[3/3] 检测可视化依赖 (Graphviz/中文字体)...")
        self._check_visualization()
        print(f"      Graphviz状态: {'安全' if self.report.graphviz_safe else '需修复'}")

        # 计算三大标志
        self._calculate_completion_signals()

        # 打印
        self._print_summary()

        return self.report

    def _check_algorithm_coverage(self):
        """检查算法覆盖"""
        # 初始化算法结果
        for algo_id, algo_info in ALGORITHMS.items():
            self.report.algorithms[algo_id] = AlgorithmCheckResult(
                algo_id=algo_id,
                algo_name=algo_info["name"],
                category=algo_info["category"]
            )

        # 扫描所有.py和.ipynb文件
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))

        self.report.total_py_files = len(py_files)
        self.report.total_ipynb_files = len(ipynb_files)

        all_files = py_files + ipynb_files

        for filepath in all_files:
            content = self._read_file_content(filepath)
            if not content:
                continue

            # 检测每个算法
            for algo_id, algo_info in ALGORITHMS.items():
                result = self.report.algorithms[algo_id]
                if result.detected:
                    continue

                for keyword in algo_info["keywords"]:
                    if keyword.lower() in content.lower():
                        result.detected = True
                        result.file_count += 1
                        break

        # 统计覆盖
        detected_count = sum(1 for a in self.report.algorithms.values() if a.detected)
        self.report.missing_algorithm_count = len(ALGORITHMS) - detected_count
        self.report.coverage_rate = round(detected_count / len(ALGORITHMS) * 100, 1)

    def _check_random_state(self):
        """检查random_state参数"""
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))

        all_files = py_files + ipynb_files

        for filepath in all_files:
            content = self._read_file_content(filepath)
            if not content:
                continue

            result = RandomStateCheckResult(file_path=str(filepath))

            # 检测需要random_state的函数调用
            for func_name in RANDOM_STATE_FUNCTIONS:
                pattern = rf'{func_name}\s*\('
                calls = list(re.finditer(pattern, content))
                if calls:
                    for call_match in calls:
                        result.total_calls += 1
                        # 检查调用后面是否有random_state参数
                        call_end = min(call_match.end() + 200, len(content))
                        call_context = content[call_match.end():call_end]
                        if not self.random_state_pattern.search(call_context):
                            result.missing_seeds.append(f"{func_name}()")
                        else:
                            result.calls_with_seed += 1

            if result.total_calls > 0:
                result.coverage_rate = result.calls_with_seed / result.total_calls
                self.report.random_state_results.append(result)

        # 计算总体覆盖率
        if self.report.random_state_results:
            total_calls = sum(r.total_calls for r in self.report.random_state_results)
            total_with_seed = sum(r.calls_with_seed for r in self.report.random_state_results)
            self.report.random_seed_coverage = total_with_seed / total_calls if total_calls > 0 else 1.0
            self.report.random_seed_passed = self.report.random_seed_coverage > 0.9
        else:
            self.report.random_seed_coverage = 1.0
            self.report.random_seed_passed = True

    def _check_visualization(self):
        """检查可视化依赖"""
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))

        all_files = py_files + ipynb_files

        for filepath in all_files:
            content = self._read_file_content(filepath)
            if not content:
                continue

            result = GraphvizCheckResult(file_path=str(filepath))

            # 检查Graphviz调用
            if self.graphviz_pattern.search(content):
                result.has_graphviz_call = True
                # 检查是否有降级方案
                if self.graphviz_fallback_pattern.search(content):
                    result.has_fallback = True
                else:
                    result.issues.append("缺少export_text降级方案")

            # 检查中文字体设置
            has_chinese_font = any(p.search(content) for p in self.chinese_font_patterns)
            if not has_chinese_font and ("plt." in content or "matplotlib" in content.lower()):
                result.issues.append("缺少中文字体设置")

            if result.has_graphviz_call or result.issues:
                self.report.graphviz_results.append(result)
                self.report.graphviz_issues.extend(result.issues)

        self.report.graphviz_safe = len(self.report.graphviz_issues) == 0

    def _calculate_completion_signals(self):
        """计算三大结束标志"""
        # 标志1: 19个算法节点全点亮
        self.report.coverage_signal = self.report.missing_algorithm_count == 0

        # 标志2: 随机种子已锁定 (>90%)
        self.report.deterministic_signal = self.report.random_seed_passed

        # 标志3: Graphviz软着陆
        self.report.visualization_signal = self.report.graphviz_safe

        # 综合判断
        self.report.all_passed = (
            self.report.coverage_signal and
            self.report.deterministic_signal and
            self.report.visualization_signal
        )

    def _print_summary(self):
        """打印结果摘要"""
        print("\n" + "=" * 60)
        print(">>> 监测完成! 三大标志状态:")
        print(f"    标志1 (算法覆盖): {'✅ 通过' if self.report.coverage_signal else '❌ 未通过'}")
        print(f"    标志2 (随机种子): {'✅ 通过' if self.report.deterministic_signal else '❌ 未通过'}")
        print(f"    标志3 (可视化): {'✅ 通过' if self.report.visualization_signal else '❌ 未通过'}")
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

        # 生成算法覆盖表格
        algo_rows = ""
        for algo_id, algo in r.algorithms.items():
            status = "✅" if algo.detected else "❌"
            category_tag = f"<span class='tag tag-pass'>{algo.category}</span>"
            algo_rows += f"""
                <tr>
                    <td style="padding: 8px; font-weight: 600;">{algo_id}</td>
                    <td style="padding: 8px;">{algo.algo_name}</td>
                    <td style="padding: 8px;">{category_tag}</td>
                    <td style="padding: 8px; text-align: center;">{status}</td>
                </tr>
            """

        # 生成随机种子问题表格
        random_issues_html = ""
        for result in r.random_state_results:
            if result.missing_seeds:
                coverage_pct = result.coverage_rate * 100
                color = "#dc3545" if coverage_pct < 90 else "#28a745"
                random_issues_html += f"""
                    <tr>
                        <td style="padding: 8px; word-break: break-all;">{result.file_path.split('/')[-1]}</td>
                        <td style="padding: 8px; text-align: center; color: {color};">{coverage_pct:.0f}%</td>
                        <td style="padding: 8px; color: #f57c00;">{', '.join(result.missing_seeds[:3])}</td>
                    </tr>
                """

        if not random_issues_html:
            random_issues_html = "<tr><td colspan='3' style='padding: 16px; color: #28a745;'>✅ 所有随机函数均已配置random_state</td></tr>"

        # 生成Graphviz问题表格
        graphviz_issues_html = ""
        for result in r.graphviz_results:
            if result.issues:
                graphviz_issues_html += f"""
                    <tr>
                        <td style="padding: 8px; word-break: break-all;">{result.file_path.split('/')[-1]}</td>
                        <td style="padding: 8px; color: #f57c00;">{'/'.join(result.issues)}</td>
                    </tr>
                """

        if not graphviz_issues_html:
            graphviz_issues_html = "<tr><td colspan='2' style='padding: 16px; color: #28a745;'>✅ Graphviz调用已配置降级方案</td></tr>"

        # 修复建议HTML
        if not r.all_passed:
            fix_suggestion_html = '''
        <div class="card" style="background: linear-gradient(135deg, #fff3cd, #ffeeba);">
            <h2><span class="card-icon">🔧</span>自动修复建议</h2>
            <div style="margin-top: 12px;">
                <p><strong>1. 随机种子自动注入:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;"># 遍历代码，在所有支持random_state的函数中插入random_state=42
from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier(random_state=42)  # 添加random_state</pre>
                <p><strong>2. Graphviz降级方案:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;">try:
    from sklearn.tree import export_graphviz
    dot_data = export_graphviz(model, out_file=None, ...)
    graph = graphviz.Source(dot_data)
except:
    from sklearn.tree import export_text
    print(export_text(model))</pre>
                <p><strong>3. Matplotlib中文字体:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;">import matplotlib.pyplot as plt
import platform
if platform.system() == 'Windows':
    plt.rcParams['font.sans-serif'] = ['SimHei']
elif platform.system() == 'Darwin':
    plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False</pre>
            </div>
        </div>'''
        else:
            fix_suggestion_html = ''

        # 构建完整HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>数据挖掘分析课程 - 质量监测报告</title>
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
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 数据挖掘分析课程 - 质量监测报告</h1>
        <p class="subtitle">基于 MCP 视角的自动化质量检测 | 检测时间: {r.timestamp}</p>

        <!-- 状态横幅 -->
        <div class="status-banner {'status-pass' if r.all_passed else 'status-fail'}">
            {'✅ 全部通过 - 可封版' if r.all_passed else '⚠️ 需修复问题'}
        </div>

        <!-- 三大标志 -->
        <div class="summary-grid">
            <div class="signal-card {'signal-pass' if r.coverage_signal else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.coverage_signal else '❌'}</div>
                <div class="signal-title">标志1: 19算法覆盖</div>
                <div class="signal-value">{'完整' if r.coverage_signal else f'{r.missing_algorithm_count}个缺失'}</div>
            </div>
            <div class="signal-card {'signal-pass' if r.deterministic_signal else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.deterministic_signal else '❌'}</div>
                <div class="signal-title">标志2: 随机种子锁定</div>
                <div class="signal-value">{'已锁定' if r.deterministic_signal else f'{r.random_seed_coverage:.0%}'}</div>
            </div>
            <div class="signal-card {'signal-pass' if r.visualization_signal else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.visualization_signal else '❌'}</div>
                <div class="signal-title">标志3: Graphviz软着陆</div>
                <div class="signal-value">{'安全' if r.visualization_signal else '需修复'}</div>
            </div>
        </div>

        <!-- 算法覆盖检查 -->
        <div class="card">
            <h2><span class="card-icon">📊</span>19个算法代码覆盖检查</h2>
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
                    <div class="stat-value" style="color: {'#28a745' if r.missing_algorithm_count == 0 else '#dc3545'};">{len(ALGORITHMS) - r.missing_algorithm_count}</div>
                    <div class="stat-label">已检测算法</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.coverage_rate}%</div>
                    <div class="stat-label">覆盖率</div>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {r.coverage_rate}%;"></div>
            </div>
            {'<div class="warning-box">⚠️ 存在算法代码缺失，请补充对应章节的Python代码</div>' if r.missing_algorithm_count > 0 else ''}
            <table>
                <thead>
                    <tr>
                        <th>算法ID</th>
                        <th>算法名称</th>
                        <th>类别</th>
                        <th style="text-align: center;">状态</th>
                    </tr>
                </thead>
                <tbody>
                    {algo_rows}
                </tbody>
            </table>
        </div>

        <!-- 随机种子检查 -->
        <div class="card">
            <h2><span class="card-icon">🎲</span>随机种子配置检查 (Deterministic Lock)</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.random_seed_coverage >= 0.9 else '#dc3545'};">{r.random_seed_coverage:.0%}</div>
                    <div class="stat-label">覆盖率</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{sum(r.total_calls for r in r.random_state_results)}</div>
                    <div class="stat-label">随机函数调用</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.random_seed_passed else '#f57c00'};">{'通过' if r.random_seed_passed else '需修复'}</div>
                    <div class="stat-label">检查结果</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len([r for r in r.random_state_results if r.missing_seeds])}</div>
                    <div class="stat-label">问题文件</div>
                </div>
            </div>
            {'<div class="warning-box">⚠️ 部分算法缺少random_state参数，建议注入random_state=42以确保结果可复现</div>' if not r.random_seed_passed else ''}
            <table>
                <thead>
                    <tr>
                        <th>文件</th>
                        <th style="text-align: center;">覆盖率</th>
                        <th>缺失random_state的函数</th>
                    </tr>
                </thead>
                <tbody>
                    {random_issues_html}
                </tbody>
            </table>
        </div>

        <!-- 可视化依赖检查 -->
        <div class="card">
            <h2><span class="card-icon">📈</span>可视化依赖检查 (Graphviz & 中文字体)</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.graphviz_safe else '#dc3545'};">{'安全' if r.graphviz_safe else '风险'}</div>
                    <div class="stat-label">Graphviz状态</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(r.graphviz_results)}</div>
                    <div class="stat-label">检测文件</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(r.graphviz_issues)}</div>
                    <div class="stat-label">问题数</div>
                </div>
            </div>
            {'<div class="warning-box">💡 Graphviz为系统级依赖，建议同时提供export_text降级方案</div>' if not r.graphviz_safe else ''}
            <table>
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>问题描述</th>
                    </tr>
                </thead>
                <tbody>
                    {graphviz_issues_html}
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
    parser = argparse.ArgumentParser(description='数据挖掘分析课程监测系统')
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
    monitor = DataMiningCourseMonitor(str(course_path))
    report = monitor.run_full_scan()
    monitor.export_html_report(args.output)

    # 返回退出码
    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
