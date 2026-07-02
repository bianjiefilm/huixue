#!/usr/bin/env python3
"""
神经网络与深度学习课程 - 质量监测系统
=====================================

基于 MCP 视角的自动化质量检测，针对深度学习课程的三大维度：
1. 资产维度 - 重资产清单（预训练权重文件）
2. 技术维度 - TF 2.0 纯度检测
3. 逻辑维度 - 算力熔断检测

三大结束标志：
- 标志1: TF 2.0 语法纯度 100%
- 标志2: 目标检测"开箱即用" (预训练权重)
- 标志3: 环境依赖"本地化"

作者: Claude Code
日期: 2026-01-14
"""

import argparse
import re
import sys
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# ============================================================================
# 常量定义
# ============================================================================

DEFAULT_COURSE_PATH = "/Users/jimfu/Work/huixue/ziyuan_data/课程资源/神经网络与深度学习"
DEFAULT_OUTPUT_PATH = "/Users/jimfu/Work/huixue/frontend/public/neural-network-monitoring-report.html"

# TF 1.x 红线特征 (必须清洗)
TF1_LEGACY_PATTERNS = [
    (r'tf\.Session\(\)', "tf.Session() - TF 1.x 会话 API"),
    (r'tf\.placeholder\(', "tf.placeholder() - TF 1.x 占位符"),
    (r'tf\.global_variables_initializer\(\)', "tf.global_variables_initializer() - TF 1.x 变量初始化"),
    (r'tf\.local_variables_initializer\(\)', "tf.local_variables_initializer()"),
    (r'tf\.get_default_session\(\)', "tf.get_default_session()"),
    (r'sess\.run\(', "sess.run() - TF 1.x 会话执行"),
    (r'tf\.assign\(', "tf.assign() 需要配合 tf.Variable 使用"),
    (r'tf\.initialize_all_variables\(\)', "tf.initialize_all_variables() - 已废弃"),
    (r'tf\.reset_default_graph\(\)', "tf.reset_default_graph() - TF 1.x 图重置"),
    (r'with tf\.Session\(\)', "with tf.Session() - TF 1.x 会话上下文"),
    (r'tf\.disable_eager_execution\(\)', "tf.disable_eager_execution() - 禁用 TF 2.0"),
]

# TF 2.0 绿线特征
TF2_GREEN_PATTERNS = [
    (r'tf\.keras', "TF.Keras API"),
    (r'model\.fit\(', "model.fit() - Keras 训练"),
    (r'tf\.GradientTape', "tf.GradientTape - 自动微分"),
    (r'tf\.function\(', "tf.function - 图函数"),
    (r'model\.predict\(', "model.predict() - Keras 预测"),
    (r'tf\.data\.Dataset', "tf.data.Dataset - 数据管道"),
    (r'tf\. distribute', "tf.distribute - 分布式训练"),
    (r'tf\.config\.list_physical_devices', "GPU 配置"),
]

# 权重文件扩展名
WEIGHT_EXTENSIONS = ['.h5', '.pb', '.pth', '.pt', '.ckpt', '.weights', '.model', '.bin']

# 在线下载模式
ONLINE_DOWNLOAD_PATTERNS = [
    (r'mnist\.load_data\(\)', "Keras MNIST自动下载"),
    (r'fashion_mnist\.load_data\(\)', "Keras Fashion-MNIST自动下载"),
    (r'cifar\d*\.load_data\(\)', "Keras CIFAR自动下载"),
    (r'\.load_data\(\)', "通用load_data()可能在线下载"),
    (r'kears\.datasets', "Keras Datasets自动下载"),
    (r'tf\.keras\.datasets', "TF Keras Datasets"),
    (r'keras\.utils\.get_file\(.*url=', "使用get_file从URL下载"),
    (r'urllib\.request\.urlretrieve', "使用urllib下载"),
    (r'wget\.', "使用wget下载"),
    (r'curl.*-O', "使用curl下载"),
]

# 目标检测关键词
OBJECT_DETECTION_KEYWORDS = ['yolo', 'ssd', 'faster-rcnn', 'faster_r_cnn', 'rcnn', 'coco', 'detect']

# 超参数风险模式
HYPERPARAMETER_PATTERNS = [
    (r'epochs\s*=\s*(\d+)', "epochs"),
    (r'batch_size\s*=\s*(\d+)', "batch_size"),
    (r'learning_rate\s*=\s*([\d.]+)', "learning_rate"),
]


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class TFVersionCheckResult:
    """TF版本检测结果"""
    file_path: str
    tf1_legacy_count: int = 0
    tf2_green_count: int = 0
    is_valid: bool = True
    tf1_issues: List[str] = field(default_factory=list)
    tf2_features: List[str] = field(default_factory=list)


@dataclass
class WeightFileCheckResult:
    """权重文件检测结果"""
    chapter_id: str
    chapter_name: str
    required_weights: List[str] = field(default_factory=list)
    found_weights: List[str] = field(default_factory=list)
    missing_weights: List[str] = field(default_factory=list)
    weight_size_mb: float = 0.0
    is_complete: bool = True


@dataclass
class DatasetCheckResult:
    """数据集检测结果"""
    dataset_name: str
    has_local_files: bool = False
    local_path: str = ""
    online_download_calls: int = 0
    is_offline_ready: bool = False


@dataclass
class HyperparameterCheckResult:
    """超参数检测结果"""
    file_path: str
    epochs: Optional[int] = None
    batch_size: Optional[int] = None
    has_risk: bool = False
    risk_level: str = "safe"  # safe, warning, danger
    risk_reasons: List[str] = field(default_factory=list)


@dataclass
class NeuralNetworkMonitorReport:
    """神经网络课程监测报告"""
    timestamp: str = ""
    course_name: str = "神经网络与深度学习"

    # 维度1: TF版本纯度
    tf_version_results: List[TFVersionCheckResult] = field(default_factory=list)
    tf1_legacy_count: int = 0
    tf2_purity_rate: float = 0.0
    tf_version_passed: bool = False

    # 维度2: 权重资产
    weight_results: List[WeightFileCheckResult] = field(default_factory=list)
    object_detection_weight_found: bool = False
    weight_file_count: int = 0
    total_weight_size_mb: float = 0.0
    weight_signal: bool = False

    # 维度3: 数据集本地化
    dataset_results: List[DatasetCheckResult] = field(default_factory=list)
    online_download_count: int = 0
    dataset_offline_ready: bool = False
    dataset_signal: bool = False

    # 维度4: 算力熔断
    hyperparam_results: List[HyperparameterCheckResult] = field(default_factory=list)
    risk_file_count: int = 0
    compute_risk_count: int = 0
    compute_signal: bool = True  # 默认通过

    # 统计
    total_py_files: int = 0
    total_ipynb_files: int = 0

    # 三大标志
    signal1_tf_purity: bool = False  # TF 2.0 纯度
    signal2_inference_ready: bool = False  # 目标检测开箱即用
    signal3_offline_ready: bool = False  # 环境本地化
    all_passed: bool = False

    @property
    def summary(self) -> str:
        """生成摘要"""
        return f"""
        TF版本: 遗留代码={self.tf1_legacy_count}, 纯度={self.tf2_purity_rate:.0%}
        权重文件: {self.weight_file_count}个, 共{self.total_weight_size_mb:.1f}MB
        在线下载: {self.online_download_count}次
        算力风险: {self.compute_risk_count}个文件
        """


# ============================================================================
# 监测类
# ============================================================================

class NeuralNetworkCourseMonitor:
    """神经网络与深度学习课程监测器"""

    def __init__(self, course_path: str):
        self.course_path = Path(course_path)
        self.report = NeuralNetworkMonitorReport()
        self.report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 编译正则表达式
        self.tf1_patterns = [(re.compile(p, re.I), msg) for p, msg in TF1_LEGACY_PATTERNS]
        self.tf2_patterns = [(re.compile(p), msg) for p, msg in TF2_GREEN_PATTERNS]
        self.online_patterns = [(re.compile(p, re.I), msg) for p, msg in ONLINE_DOWNLOAD_PATTERNS]

    def _read_file_content(self, filepath: Path) -> Optional[str]:
        """读取文件内容"""
        try:
            if filepath.suffix == '.ipynb':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 从notebook提取代码
                    code_cells = []
                    for cell in data.get('cells', []):
                        if cell.get('cell_type') == 'code':
                            source = cell.get('source', [])
                            if isinstance(source, list):
                                code_cells.append(''.join(source))
                            else:
                                code_cells.append(source)
                    return '\n'.join(code_cells)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            print(f"  警告: 无法读取文件 {filepath}: {e}")
            return None

    def _check_tf_version(self):
        """检查TF版本纯度"""
        print("\n[1/4] 检测 TF 2.0 语法纯度...")
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))
        all_files = py_files + ipynb_files

        self.report.total_py_files = len(py_files)
        self.report.total_ipynb_files = len(ipynb_files)

        tf1_total = 0
        valid_files = 0

        for filepath in all_files:
            content = self._read_file_content(filepath)
            if not content:
                continue

            result = TFVersionCheckResult(file_path=str(filepath))
            is_valid = True

            # 检测 TF 1.x 遗留代码
            for pattern, msg in self.tf1_patterns:
                matches = list(pattern.finditer(content))
                if matches:
                    result.tf1_legacy_count += len(matches)
                    tf1_total += len(matches)
                    result.tf1_issues.append(f"{msg} (x{len(matches)})")
                    is_valid = False

            # 检测 TF 2.0 特征
            for pattern, msg in self.tf2_patterns:
                matches = list(pattern.finditer(content))
                if matches:
                    result.tf2_green_count += len(matches)
                    result.tf2_features.append(f"{msg} (x{len(matches)})")

            result.is_valid = is_valid
            if result.tf1_legacy_count > 0 or result.tf2_green_count > 0:
                self.report.tf_version_results.append(result)

            if is_valid and result.tf2_green_count > 0:
                valid_files += 1

        self.report.tf1_legacy_count = tf1_total
        total_with_tf = len([r for r in self.report.tf_version_results
                            if r.tf2_green_count > 0 or r.tf1_legacy_count > 0])
        self.report.tf2_purity_rate = (1 - tf1_total / max(total_with_tf, 1)) * 100 if total_with_tf > 0 else 100
        self.report.tf_version_passed = tf1_total == 0
        self.report.signal1_tf_purity = tf1_total == 0

        print(f"      TF 1.x 遗留代码: {tf1_total}处")
        print(f"      TF 2.0 纯度: {self.report.tf2_purity_rate:.0f}%")
        print(f"      状态: {'✅ 通过' if self.report.tf_version_passed else '❌ 需修复'}")

    def _check_weight_files(self):
        """检查预训练权重文件"""
        print("\n[2/4] 检测预训练权重文件...")
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))
        all_files = py_files + ipynb_files

        # 扫描目标检测相关代码
        object_detection_files = []
        required_weights = []

        for filepath in all_files:
            content = self._read_file_content(filepath)
            if not content:
                continue

            # 检测目标检测关键词
            has_obj_detection = any(kw in content.lower() for kw in OBJECT_DETECTION_KEYWORDS)
            if has_obj_detection:
                object_detection_files.append(filepath)

            # 检测权重加载代码
            for ext in WEIGHT_EXTENSIONS:
                pattern = rf'[\'"](\w*{ext.lstrip(".")}\w*)[\'"]'
                matches = re.findall(pattern, content, re.I)
                for match in matches:
                    if match not in required_weights:
                        required_weights.append(match)

        # 查找实际的权重文件
        weight_files = []
        for ext in WEIGHT_EXTENSIONS:
            weight_files.extend(list(self.course_path.rglob(f"*{ext}")))

        self.report.weight_file_count = len(weight_files)

        # 计算权重文件大小
        total_size = 0
        for wf in weight_files:
            try:
                size_mb = wf.stat().st_size / (1024 * 1024)
                total_size += size_mb
            except:
                pass
        self.report.total_weight_size_mb = round(total_size, 2)

        # 检查目标检测权重
        object_detection_weights = []
        for wf in weight_files:
            wf_name = wf.name.lower()
            if any(kw in wf_name for kw in ['yolo', 'ssd', 'faster', 'rcnn', 'mobilenet', 'efficientdet']):
                object_detection_weights.append(wf)

        self.report.object_detection_weight_found = len(object_detection_weights) > 0
        missing = [w for w in required_weights if not any(w in str(f).lower() for f in weight_files)]

        # 创建检测结果
        result = WeightFileCheckResult(
            chapter_id="target_detection",
            chapter_name="目标检测",
            required_weights=required_weights,
            found_weights=[str(f.name) for f in weight_files],
            missing_weights=missing,
            weight_size_mb=total_size,
            is_complete=len(missing) == 0 and total_size > 0
        )
        self.report.weight_results.append(result)
        self.report.signal2_inference_ready = total_size > 0

        print(f"      发现权重文件: {len(weight_files)}个, 共{total_size:.1f}MB")
        print(f"      目标检测权重: {'✅ 存在' if self.report.object_detection_weight_found else '❌ 缺失'}")
        print(f"      状态: {'✅ 通过' if self.report.signal2_inference_ready else '❌ 需修复'}")

    def _check_dataset_localization(self):
        """检查数据集本地化"""
        print("\n[3/4] 检测环境依赖本地化...")
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))
        all_files = py_files + ipynb_files

        total_download_calls = 0
        has_local_mnist = False
        has_local_fashion_mnist = False

        # 检查本地数据集
        datasets_path = self.course_path / "datasets"
        if datasets_path.exists():
            for ds in datasets_path.iterdir():
                if ds.is_dir():
                    files = list(ds.rglob("*"))
                    if files:
                        if ds.name == "mnist":
                            has_local_mnist = True
                        elif ds.name == "fashion-mnist":
                            has_local_fashion_mnist = True

        # 检测在线下载调用
        for filepath in all_files:
            content = self._read_file_content(filepath)
            if not content:
                continue

            for pattern, msg in self.online_patterns:
                matches = list(pattern.finditer(content))
                if matches:
                    total_download_calls += len(matches)

        self.report.online_download_count = total_download_calls
        self.report.dataset_offline_ready = total_download_calls == 0 or has_local_mnist
        self.report.signal3_offline_ready = total_download_calls == 0 or has_local_mnist

        print(f"      在线下载调用: {total_download_calls}次")
        print(f"      本地MNIST: {'✅ 存在' if has_local_mnist else '❌ 缺失'}")
        print(f"      状态: {'✅ 通过' if self.report.signal3_offline_ready else '❌ 需修复'}")

    def _check_compute_risk(self):
        """检查算力熔断风险"""
        print("\n[4/4] 检测算力熔断风险...")
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))
        all_files = py_files + ipynb_files

        risk_count = 0

        for filepath in all_files:
            content = self._read_file_content(filepath)
            if not content:
                continue

            result = HyperparameterCheckResult(file_path=str(filepath))
            has_risk = False
            risk_reasons = []

            # 提取超参数
            epochs_match = re.search(r'epochs\s*=\s*(\d+)', content, re.I)
            batch_match = re.search(r'batch_size\s*=\s*(\d+)', content, re.I)

            if epochs_match:
                result.epochs = int(epochs_match.group(1))
                if result.epochs > 20:
                    has_risk = True
                    risk_reasons.append(f"epochs={result.epochs} 可能过长 (>20)")

            if batch_match:
                result.batch_size = int(batch_match.group(1))
                if result.batch_size > 64:
                    has_risk = True
                    risk_reasons.append(f"batch_size={result.batch_size} 可能导致OOM (>64)")

            # 检测是否有深层网络
            deep_nets = re.findall(r'(ResNet|VGG|Inception|EfficientNet|BERT|GPT|Transformer)', content, re.I)
            if deep_nets and result.epochs and result.epochs > 5:
                has_risk = True
                risk_reasons.append(f"深层网络({', '.join(deep_nets[:3])})建议epochs<=5")

            result.has_risk = has_risk
            result.risk_reasons = risk_reasons
            result.risk_level = "danger" if has_risk else "safe"

            if has_risk:
                risk_count += 1
                self.report.hyperparam_results.append(result)

        self.report.compute_risk_count = risk_count
        self.report.compute_signal = risk_count == 0

        print(f"      风险文件: {risk_count}个")
        print(f"      状态: {'✅ 通过' if self.report.compute_signal else '⚠️ 需关注'}")

    def _calculate_signals(self):
        """计算三大结束标志"""
        # 标志1: TF 2.0 纯度
        self.report.signal1_tf_purity = self.report.tf1_legacy_count == 0

        # 标志2: 目标检测开箱即用 (存在权重文件 或 有降级方案)
        # 阈值: 权重文件>0说明已配置权重目录
        self.report.signal2_inference_ready = self.report.weight_file_count > 0

        # 标志3: 环境本地化 (无在线下载 或已有本地数据)
        self.report.signal3_offline_ready = (
            self.report.online_download_count == 0 or
            self.report.dataset_offline_ready
        )

        self.report.all_passed = (
            self.report.signal1_tf_purity and
            self.report.signal2_inference_ready and
            self.report.signal3_offline_ready
        )

    def run_full_scan(self) -> NeuralNetworkMonitorReport:
        """执行完整扫描"""
        print("=" * 60)
        print(">>> 开始 神经网络与深度学习课程监测")
        print("=" * 60)

        self._check_tf_version()
        self._check_weight_files()
        self._check_dataset_localization()
        self._check_compute_risk()
        self._calculate_signals()

        self._print_summary()

        return self.report

    def _print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 60)
        print(">>> 监测完成! 三大标志状态:")
        print(f"    标志1 (TF 2.0 纯度): {'✅ 通过' if self.report.signal1_tf_purity else '❌ 未通过'}")
        print(f"    标志2 (目标检测开箱): {'✅ 通过' if self.report.signal2_inference_ready else '❌ 未通过'}")
        print(f"    标志3 (环境本地化): {'✅ 通过' if self.report.signal3_offline_ready else '❌ 未通过'}")
        print(f"    综合状态: {'✅ 全部通过 - 可封版' if self.report.all_passed else '❌ 需修复问题'}")
        print("=" * 60)

    def export_html_report(self, output_path: str):
        """导出HTML报告"""
        r = self.report

        # 构建问题详情HTML
        tf_issues_html = ""
        if r.tf_version_results:
            for result in r.tf_version_results[:5]:  # 最多显示5个
                if result.tf1_issues:
                    tf_issues_html += f"""
                    <tr>
                        <td style="padding: 8px; word-break: break-all;">{result.file_path.split('/')[-1]}</td>
                        <td style="padding: 8px; color: #dc3545;">{', '.join(result.tf1_issues[:2])}</td>
                    </tr>
                    """
        if not tf_issues_html:
            tf_issues_html = "<tr><td colspan='2' style='padding: 16px; color: #28a745;'>✅ 无TF 1.x遗留代码</td></tr>"

        # 权重问题HTML
        weight_issues_html = ""
        for result in r.weight_results:
            if result.missing_weights:
                for w in result.missing_weights[:3]:
                    weight_issues_html += f"<li style='margin: 4px 0;'>缺失: <code>{w}</code></li>"

        if not weight_issues_html:
            weight_issues_html = "<li style='color: #28a745;'>✅ 权重文件完整</li>"
        else:
            weight_issues_html = f"<ul style='margin: 8px 0; padding-left: 20px;'>{weight_issues_html}</ul>"

        # 在线下载HTML
        download_issues_html = ""
        if r.online_download_count > 0:
            download_issues_html = f"""
            <div class="warning-box">
                ⚠️ 检测到 {r.online_download_count} 处在线下载调用，建议使用本地数据集
            </div>
            """

        # 算力风险HTML
        compute_issues_html = ""
        if r.hyperparam_results:
            for result in r.hyperparam_results[:5]:
                compute_issues_html += f"""
                <tr>
                    <td style="padding: 8px; word-break: break-all;">{result.file_path.split('/')[-1]}</td>
                    <td style="padding: 8px; color: #f57c00;">{', '.join(result.risk_reasons)}</td>
                </tr>
                """
        if not compute_issues_html:
            compute_issues_html = "<tr><td colspan='2' style='padding: 16px; color: #28a745;'>✅ 无算力风险</td></tr>"

        # 修复建议HTML
        fix_suggestion_html = ""
        if not r.all_passed:
            fix_suggestion_html = '''
        <div class="card" style="background: linear-gradient(135deg, #fff3cd, #ffeeba);">
            <h2><span class="card-icon">🔧</span>自动修复建议</h2>
            <div style="margin-top: 12px;">
                <p><strong>1. TF 1.x 升级到 TF 2.0:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;"># TF 1.x 风格 (错误)
sess = tf.Session()
sess.run(tf.global_variables_initializer())

# TF 2.0 风格 (正确)
# 直接使用 Eager Execution 或 Keras API
model = tf.keras.Sequential([...])
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy')
model.fit(x_train, y_train)</pre>
                <p><strong>2. 下载预训练权重:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;"># 从HuggingFace下载YOLOv5权重
from urllib.request import urlretrieve
urlretrieve("https://huggingface.co/ultralytics/yolov5s/resolve/main/yolov5s.pt",
            "models/yolov5s.pt")</pre>
                <p><strong>3. 本地数据集配置:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;"># 使用本地MNIST数据
from utils.data_loader import load_mnist
(x_train, y_train), (x_test, y_test) = load_mnist()

# 或指定本地路径
(x_train, y_train), (x_test, y_test) = mnist.load_data(path='datasets/mnist.npz')</pre>
            </div>
        </div>'''

        # 构建HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>神经网络与深度学习课程 - 质量监测报告</title>
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 神经网络与深度学习课程 - 质量监测报告</h1>
        <p class="subtitle">基于 MCP 视角的自动化质量检测 | 检测时间: {r.timestamp}</p>

        <!-- 状态横幅 -->
        <div class="status-banner {'status-pass' if r.all_passed else 'status-fail'}">
            {'✅ 全部通过 - 可封版' if r.all_passed else '⚠️ 需修复问题'}
        </div>

        <!-- 三大标志 -->
        <div class="summary-grid">
            <div class="signal-card {'signal-pass' if r.signal1_tf_purity else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.signal1_tf_purity else '❌'}</div>
                <div class="signal-title">标志1: TF 2.0 纯度</div>
                <div class="signal-value">{'100%' if r.signal1_tf_purity else f'{r.tf2_purity_rate:.0f}%'}</div>
            </div>
            <div class="signal-card {'signal-pass' if r.signal2_inference_ready else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.signal2_inference_ready else '❌'}</div>
                <div class="signal-title">标志2: 目标检测开箱</div>
                <div class="signal-value">{'已配置' if r.signal2_inference_ready else '需注入权重'}</div>
            </div>
            <div class="signal-card {'signal-pass' if r.signal3_offline_ready else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.signal3_offline_ready else '❌'}</div>
                <div class="signal-title">标志3: 环境本地化</div>
                <div class="signal-value">{'已就绪' if r.signal3_offline_ready else f'{r.online_download_count}次下载'}</div>
            </div>
        </div>

        <!-- 统计概览 -->
        <div class="card">
            <h2><span class="card-icon">📊</span>资源概览</h2>
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
                    <div class="stat-value">{r.weight_file_count}</div>
                    <div class="stat-label">权重文件</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.total_weight_size_mb:.1f}MB</div>
                    <div class="stat-label">权重总大小</div>
                </div>
            </div>
        </div>

        <!-- TF版本检测 -->
        <div class="card">
            <h2><span class="card-icon">🔄</span>TF 2.0 语法纯度检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#dc3545' if r.tf1_legacy_count > 0 else '#28a745'};">{r.tf1_legacy_count}</div>
                    <div class="stat-label">TF 1.x 遗留</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.tf2_purity_rate:.0f}%</div>
                    <div class="stat-label">TF 2.0 纯度</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.signal1_tf_purity else '#dc3545'};">{'通过' if r.signal1_tf_purity else '需修复'}</div>
                    <div class="stat-label">检查结果</div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>问题描述</th>
                    </tr>
                </thead>
                <tbody>
                    {tf_issues_html}
                </tbody>
            </table>
        </div>

        <!-- 权重文件检测 -->
        <div class="card">
            <h2><span class="card-icon">📦</span>预训练权重文件检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{r.weight_file_count}</div>
                    <div class="stat-label">权重文件数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.total_weight_size_mb:.1f}MB</div>
                    <div class="stat-label">总大小</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.signal2_inference_ready else '#dc3545'};">{'已配置' if r.signal2_inference_ready else '缺失'}</div>
                    <div class="stat-label">目标检测</div>
                </div>
            </div>
            {f'<div class="warning-box">⚠️ 权重文件不足50MB，目标检测无法开箱即用</div>' if not r.signal2_inference_ready and r.weight_file_count > 0 else ''}
            <div style="margin-top: 12px;">
                {weight_issues_html}
            </div>
        </div>

        <!-- 数据集本地化 -->
        <div class="card">
            <h2><span class="card-icon">💾</span>数据集本地化检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#dc3545' if r.online_download_count > 0 else '#28a745'};">{r.online_download_count}</div>
                    <div class="stat-label">在线下载调用</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.dataset_offline_ready else '#dc3545'};">{'已就绪' if r.dataset_offline_ready else '需配置'}</div>
                    <div class="stat-label">本地数据</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.signal3_offline_ready else '#dc3545'};">{'通过' if r.signal3_offline_ready else '需修复'}</div>
                    <div class="stat-label">检查结果</div>
                </div>
            </div>
            {download_issues_html}
        </div>

        <!-- 算力熔断检测 -->
        <div class="card">
            <h2><span class="card-icon">⚡</span>算力熔断检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#dc3545' if r.compute_risk_count > 0 else '#28a745'};">{r.compute_risk_count}</div>
                    <div class="stat-label">风险文件</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.compute_signal else '#f57c00'};">{'安全' if r.compute_signal else '需关注'}</div>
                    <div class="stat-label">算力状态</div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>风险描述</th>
                    </tr>
                </thead>
                <tbody>
                    {compute_issues_html}
                </tbody>
            </table>
        </div>

        <!-- 修复建议 -->
        {fix_suggestion_html}

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
    parser = argparse.ArgumentParser(description='神经网络与深度学习课程监测系统')
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
    monitor = NeuralNetworkCourseMonitor(str(course_path))
    report = monitor.run_full_scan()
    monitor.export_html_report(args.output)

    # 返回退出码
    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
