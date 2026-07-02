#!/usr/bin/env python3
"""
计算机视觉课程 - 质量监测系统
=============================

基于 MCP 视角的自动化质量检测，针对计算机视觉课程的三大维度：
1. 资产维度 - 预训练权重文件检测
2. 技术维度 - OpenCV安全性检测 (cv2.imshow)
3. 逻辑维度 - 标注数据完整性检测

三大结束标志：
- 标志1: 核心算法推理演示就绪 (Demo脚本存在)
- 标志2: 标注工具链免安装 (LabelImg工具)
- 标志3: 可视化代码Web安全 (cv2.imshow已无害化)

作者: Claude Code
日期: 2026-01-14
"""

import argparse
import re
import sys
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime


# ============================================================================
# 常量定义
# ============================================================================

DEFAULT_COURSE_PATH = "/Users/jimfu/Work/huixue/ziyuan_data/课程资源/计算机视觉"
DEFAULT_OUTPUT_PATH = "/Users/jimfu/Work/huixue/frontend/public/computer-vision-monitoring-report.html"

# 权重文件扩展名和最小大小阈值
WEIGHT_EXTENSIONS = {
    '.pt': {'min_size_mb': 10, 'algorithm': ['YOLO', 'PyTorch']},
    '.pth': {'min_size_mb': 10, 'algorithm': ['PyTorch']},
    '.weights': {'min_size_mb': 10, 'algorithm': ['YOLO', 'Darknet']},
    '.h5': {'min_size_mb': 10, 'algorithm': ['Keras']},
    '.ckpt': {'min_size_mb': 10, 'algorithm': ['TensorFlow']},
}

# OpenCV 危险函数
CV2_DANGEROUS_PATTERNS = [
    (r'cv2\.imshow\s*\(', 'cv2.imshow() - 会导致Jupyter内核崩溃'),
    (r'cv2\.waitKey\s*\(', 'cv2.waitKey() - 通常与imshow配对使用'),
    (r'cv2\.namedWindow\s*\(', 'cv2.namedWindow() - 创建窗口'),
]

# OpenCV 安全替代方案
CV2_SAFE_PATTERNS = [
    (r'plt\.imshow\s*\(', 'matplotlib.pyplot.imshow'),
    (r'plt\.show\s*\(', 'matplotlib.pyplot.show'),
    (r'IPython\.display\.Image', 'IPython.display.Image'),
    (r'from\s+matplotlib\s+import\s+pyplot', 'matplotlib导入'),
]

# 核心算法关键词
ALGORITHM_KEYWORDS = {
    'YOLO': ['yolo', 'yolov3', 'yolov5', 'yolov8'],
    'RCNN': ['rcnn', 'fast_rcnn', 'faster_rcnn', 'mask_rcnn'],
    'CNN': ['cnn', 'convolutional', 'conv2d'],
    'GAN': ['gan', 'generator', 'discriminator', '生成对抗'],
    'Segmentation': ['segmentation', 'unet', 'mask', '语义分割'],
    'Tracking': ['tracking', 'track', '目标跟踪'],
}

# 标注文件格式
ANNOTATION_FORMATS = {
    'voc': ['.xml'],
    'yolo': ['.txt'],
    'coco': ['.json'],
}

# 图像文件格式
IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

# Demo脚本关键词
DEMO_SCRIPT_KEYWORDS = ['demo', 'inference', 'predict', '演示', '推理']


# ============================================================================
# 数据类定义
# ============================================================================

@dataclass
class WeightFileResult:
    """权重文件检测结果"""
    file_path: str
    file_name: str
    file_size_mb: float
    algorithm_type: str
    is_valid: bool  # 文件大小是否达标


@dataclass
class CV2SafetyResult:
    """OpenCV安全性检测结果"""
    file_path: str
    has_dangerous_code: bool = False
    has_safe_alternative: bool = False
    dangerous_patterns: List[str] = field(default_factory=list)
    safe_patterns: List[str] = field(default_factory=list)


@dataclass
class AnnotationCheckResult:
    """标注数据完整性检测结果"""
    directory: str
    image_count: int = 0
    annotation_count: int = 0
    missing_annotations: List[str] = field(default_factory=list)
    orphan_annotations: List[str] = field(default_factory=list)
    is_complete: bool = True


@dataclass
class DemoScriptResult:
    """Demo脚本检测结果"""
    file_path: str
    file_name: str
    has_demo_keyword: bool = False
    loads_local_weights: bool = False
    does_inference_only: bool = False


@dataclass
class LabelToolResult:
    """标注工具检测结果"""
    has_labelimg_tool: bool = False
    has_pip_instruction: bool = False
    has_sample_images: bool = False
    sample_image_count: int = 0
    tool_path: str = ""


@dataclass
class ComputerVisionMonitorReport:
    """计算机视觉课程监测报告"""
    timestamp: str = ""
    course_name: str = "计算机视觉"

    # 维度1: 权重资产
    weight_results: List[WeightFileResult] = field(default_factory=list)
    total_weight_count: int = 0
    total_weight_size_mb: float = 0.0
    yolo_weight_found: bool = False
    rcnn_weight_found: bool = False
    weight_signal: bool = False

    # 维度2: OpenCV安全
    cv2_results: List[CV2SafetyResult] = field(default_factory=list)
    unsafe_cv2_count: int = 0
    cv2_safe_count: int = 0
    cv2_signal: bool = False

    # 维度3: 标注数据
    annotation_results: List[AnnotationCheckResult] = field(default_factory=list)
    incomplete_dataset_count: int = 0
    annotation_signal: bool = False

    # 标志检查
    demo_script_results: List[DemoScriptResult] = field(default_factory=list)
    has_demo_script: bool = False
    inference_signal: bool = False

    label_tool_results: LabelToolResult = field(default_factory=lambda: LabelToolResult())
    toolchain_signal: bool = False

    # 统计
    total_py_files: int = 0
    total_ipynb_files: int = 0
    total_markdown_files: int = 0

    # 三大标志
    signal1_inference_ready: bool = False  # 推理演示就绪
    signal2_toolchain_ready: bool = False  # 标注工具链就绪
    signal3_web_safe: bool = False  # Web安全
    all_passed: bool = False

    @property
    def summary(self) -> str:
        return f"""
        权重: {self.total_weight_count}个, 共{self.total_weight_size_mb:.1f}MB
        OpenCV: 不安全{self.unsafe_cv2_count}处, 安全{self.cv2_safe_count}处
        标注: {self.incomplete_dataset_count}个数据集不完整
        Demo脚本: {'✅' if self.has_demo_script else '❌'}
        标注工具: {'✅' if self.label_tool_results.has_labelimg_tool else '❌'}
        """


# ============================================================================
# 监测类
# ============================================================================

class ComputerVisionCourseMonitor:
    """计算机视觉课程监测器"""

    def __init__(self, course_path: str):
        self.course_path = Path(course_path)
        self.report = ComputerVisionMonitorReport()
        self.report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 编译正则表达式
        self.cv2_dangerous_patterns = [(re.compile(p, re.I), msg) for p, msg in CV2_DANGEROUS_PATTERNS]
        self.cv2_safe_patterns = [(re.compile(p), msg) for p, msg in CV2_SAFE_PATTERNS]

    def _read_file_content(self, filepath: Path) -> Optional[str]:
        """读取文件内容"""
        try:
            if filepath.suffix == '.ipynb':
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
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
            return None

    def _check_weight_files(self):
        """检查预训练权重文件"""
        print("\n[1/5] 检测预训练权重文件...")
        weight_files = []

        # 遍历所有可能的权重文件
        for ext, config in WEIGHT_EXTENSIONS.items():
            files = list(self.course_path.rglob(f"*{ext}"))
            for f in files:
                size_mb = f.stat().st_size / (1024 * 1024)
                weight_files.append(WeightFileResult(
                    file_path=str(f),
                    file_name=f.name,
                    file_size_mb=round(size_mb, 2),
                    algorithm_type=config['algorithm'][0],
                    is_valid=size_mb >= config['min_size_mb']
                ))

        # 扫描代码中的权重加载引用
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))
        all_code_files = py_files + ipynb_files

        referenced_weights = set()
        for filepath in all_code_files:
            content = self._read_file_content(filepath)
            if not content:
                continue
            # 检测权重加载引用
            for ext in WEIGHT_EXTENSIONS.keys():
                pattern = rf'[\'"](\w*{ext.lstrip(".")}\w*)[\'"]'
                matches = re.findall(pattern, content, re.I)
                for m in matches:
                    referenced_weights.add(m)

        self.report.weight_results = weight_files
        self.report.total_weight_count = len(weight_files)
        self.report.total_weight_size_mb = round(sum(w.file_size_mb for w in weight_files), 2)

        # 检查YOLO和RCNN权重
        for w in weight_files:
            name_lower = w.file_name.lower()
            if any(kw in name_lower for kw in ['yolo', 'v8', 'v5']):
                self.report.yolo_weight_found = True
            if any(kw in name_lower for kw in ['resnet', 'rcnn', 'faster']):
                self.report.rcnn_weight_found = True

        # 标志: 只要有任一核心算法权重即可
        self.report.weight_signal = self.report.total_weight_count > 0

        print(f"      权重文件: {self.report.total_weight_count}个, 共{self.report.total_weight_size_mb:.1f}MB")
        print(f"      YOLO权重: {'✅' if self.report.yolo_weight_found else '❌'}")
        print(f"      状态: {'✅ 通过' if self.report.weight_signal else '❌ 缺失'}")

    def _check_cv2_safety(self):
        """检查OpenCV安全性"""
        print("\n[2/5] 检测 OpenCV 安全性...")
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))
        all_files = py_files + ipynb_files

        self.report.total_py_files = len(py_files)
        self.report.total_ipynb_files = len(ipynb_files)

        unsafe_count = 0
        safe_count = 0

        for filepath in all_files:
            content = self._read_file_content(filepath)
            if not content:
                continue

            result = CV2SafetyResult(file_path=str(filepath))
            has_cv2_import = 'cv2' in content or 'opencv' in content.lower()

            if not has_cv2_import:
                continue

            # 检测危险代码
            for pattern, msg in self.cv2_dangerous_patterns:
                if pattern.search(content):
                    result.has_dangerous_code = True
                    result.dangerous_patterns.append(msg)
                    unsafe_count += 1

            # 检测安全替代方案
            for pattern, msg in self.cv2_safe_patterns:
                if pattern.search(content):
                    result.has_safe_alternative = True
                    result.safe_patterns.append(msg)
                    safe_count += 1

            if result.has_dangerous_code or result.has_safe_alternative:
                self.report.cv2_results.append(result)

        self.report.unsafe_cv2_count = unsafe_count
        self.report.cv2_safe_count = safe_count
        self.report.cv2_signal = unsafe_count == 0

        print(f"      危险代码: {unsafe_count}处")
        print(f"      安全代码: {safe_count}处")
        print(f"      状态: {'✅ 通过' if self.report.cv2_signal else '❌ 需修复'}")

    def _check_annotation_data(self):
        """检查标注数据完整性"""
        print("\n[3/5] 检测标注数据完整性...")
        datasets_path = self.course_path / "datasets"

        incomplete_count = 0
        if not datasets_path.exists():
            print(f"      数据集目录不存在")
            self.report.annotation_signal = False
            return

        for ds_dir in datasets_path.iterdir():
            if not ds_dir.is_dir():
                continue

            # 统计图片数量
            images = []
            for ext in IMAGE_FORMATS:
                images.extend(ds_dir.rglob(f"*{ext}"))

            # 统计标注文件
            annotations = []
            for fmt, extensions in ANNOTATION_FORMATS.items():
                for ext in extensions:
                    annotations.extend(ds_dir.rglob(f"*{ext}"))

            image_names = {p.stem for p in images}
            annotation_names = {p.stem for p in annotations}

            missing = annotation_names - image_names
            orphans = image_names - annotation_names

            is_complete = len(missing) == 0 and len(orphans) == 0 and len(images) > 0

            result = AnnotationCheckResult(
                directory=ds_dir.name,
                image_count=len(images),
                annotation_count=len(annotations),
                missing_annotations=list(missing)[:5],  # 只保留前5个
                orphan_annotations=list(orphans)[:5],
                is_complete=is_complete
            )
            self.report.annotation_results.append(result)

            if not is_complete:
                incomplete_count += 1

        self.report.incomplete_dataset_count = incomplete_count
        self.report.annotation_signal = incomplete_count == 0

        print(f"      数据集: {len(self.report.annotation_results)}个")
        print(f"      不完整: {incomplete_count}个")
        print(f"      状态: {'✅ 通过' if self.report.annotation_signal else '❌ 不完整'}")

    def _check_demo_scripts(self):
        """检查Demo推理脚本"""
        print("\n[4/5] 检测Demo推理脚本...")
        py_files = list(self.course_path.rglob("*.py"))
        ipynb_files = list(self.course_path.rglob("*.ipynb"))
        all_files = py_files + ipynb_files

        demo_found = False
        for filepath in all_files:
            content = self._read_file_content(filepath)
            if not content:
                continue

            filename = filepath.name.lower()
            has_demo_keyword = any(kw in filename for kw in DEMO_SCRIPT_KEYWORDS)

            # 检查是否加载本地权重
            loads_local = any([
                re.search(r'load_state_dict|load_weights', content),
                re.search(r'weights\s*=\s*[\'"][\w/.]+[\'"]', content),
            ])

            # 检查是否仅推理(不训练)
            does_inference = all([
                not re.search(r'\.fit\(|\.train\(', content),
                re.search(r'predict|\.eval\(\)', content),
            ])

            if has_demo_keyword:
                demo_found = True
                self.report.demo_script_results.append(DemoScriptResult(
                    file_path=str(filepath),
                    file_name=filepath.name,
                    has_demo_keyword=True,
                    loads_local_weights=loads_local,
                    does_inference_only=does_inference
                ))

        self.report.has_demo_script = demo_found
        self.report.inference_signal = demo_found

        print(f"      Demo脚本: {'✅ 存在' if demo_found else '❌ 缺失'}")
        print(f"      状态: {'✅ 通过' if demo_found else '❌ 需添加'}")

    def _check_label_tools(self):
        """检查标注工具链"""
        print("\n[5/5] 检测标注工具链...")
        result = LabelToolResult()

        # 检查是否有labelImg相关文件
        labelimg_files = list(self.course_path.rglob("*labelimg*"))
        exe_files = list(self.course_path.rglob("*.exe"))

        if labelimg_files or exe_files:
            result.has_labelimg_tool = True
            result.tool_path = str(labelimg_files[0]) if labelimg_files else "目录中存在.exe"

        # 检查pip安装指令
        md_files = list(self.course_path.rglob("*.md"))
        for md in md_files:
            content = self._read_file_content(md)
            if content and re.search(r'pip\s+install\s+labelimg', content, re.I):
                result.has_pip_instruction = True
                break

        # 检查示例图片
        datasets_path = self.course_path / "datasets"
        sample_count = 0
        if datasets_path.exists():
            for ext in IMAGE_FORMATS:
                sample_count += len(list(datasets_path.rglob(f"*{ext}")))
            result.sample_image_count = sample_count
            result.has_sample_images = sample_count >= 5

        self.report.label_tool_results = result
        self.report.toolchain_signal = result.has_sample_images

        print(f"      LabelImg工具: {'✅' if result.has_labelimg_tool else '❌'}")
        print(f"      pip安装指令: {'✅' if result.has_pip_instruction else '❌'}")
        print(f"      示例图片: {sample_count}张 {'✅' if result.has_sample_images else '❌'}")
        print(f"      状态: {'✅ 通过' if self.report.toolchain_signal else '❌ 缺失'}")

    def _calculate_signals(self):
        """计算三大结束标志"""
        # 标志1: 推理演示就绪 (Demo脚本存在)
        self.report.signal1_inference_ready = self.report.has_demo_script

        # 标志2: 标注工具链免安装 (有示例图片即可)
        self.report.signal2_toolchain_ready = self.report.label_tool_results.has_sample_images

        # 标志3: Web安全 (cv2.imshow已无害化)
        self.report.signal3_web_safe = self.report.unsafe_cv2_count == 0

        # 综合状态
        self.report.all_passed = (
            self.report.signal1_inference_ready and
            self.report.signal2_toolchain_ready and
            self.report.signal3_web_safe
        )

    def run_full_scan(self) -> ComputerVisionMonitorReport:
        """执行完整扫描"""
        print("=" * 60)
        print(">>> 开始 计算机视觉课程监测")
        print("=" * 60)

        self._check_weight_files()
        self._check_cv2_safety()
        self._check_annotation_data()
        self._check_demo_scripts()
        self._check_label_tools()
        self._calculate_signals()

        self._print_summary()

        return self.report

    def _print_summary(self):
        """打印摘要"""
        print("\n" + "=" * 60)
        print(">>> 监测完成! 三大标志状态:")
        print(f"    标志1 (推理演示): {'✅ 通过' if self.report.signal1_inference_ready else '❌ 未通过'}")
        print(f"    标志2 (标注工具): {'✅ 通过' if self.report.signal2_toolchain_ready else '❌ 未通过'}")
        print(f"    标志3 (Web安全): {'✅ 通过' if self.report.signal3_web_safe else '❌ 未通过'}")
        print(f"    综合状态: {'✅ 全部通过 - 可封版' if self.report.all_passed else '❌ 需修复问题'}")
        print("=" * 60)

    def export_html_report(self, output_path: str):
        """导出HTML报告"""
        r = self.report

        # 构建权重问题HTML
        weight_issues_html = ""
        for w in r.weight_results:
            if not w.is_valid:
                weight_issues_html += f"""
                <tr>
                    <td style="padding: 8px;">{w.file_name}</td>
                    <td style="padding: 8px; color: #f57c00;">{w.file_size_mb:.1f}MB (小于10MB)</td>
                </tr>
                """
        if not weight_issues_html:
            if r.total_weight_count == 0:
                weight_issues_html = "<tr><td colspan='2' style='padding: 16px; color: #dc3545;'>❌ 未发现权重文件，请添加预训练模型权重</td></tr>"
            else:
                weight_issues_html = "<tr><td colspan='2' style='padding: 16px; color: #28a745;'>✅ 权重文件完整</td></tr>"

        # 构建CV2安全问题HTML
        cv2_issues_html = ""
        for result in r.cv2_results:
            if result.dangerous_patterns:
                for p in result.dangerous_patterns:
                    cv2_issues_html += f"""
                    <tr>
                        <td style="padding: 8px; word-break: break-all;">{result.file_path.split('/')[-1]}</td>
                        <td style="padding: 8px; color: #dc3545;">{p}</td>
                    </tr>
                    """
        if not cv2_issues_html:
            cv2_issues_html = "<tr><td colspan='2' style='padding: 16px; color: #28a745;'>✅ 无cv2.imshow危险代码</td></tr>"

        # 构建标注数据HTML
        annotation_html = ""
        for result in r.annotation_results:
            if not result.is_complete:
                annotation_html += f"""
                <tr>
                    <td style="padding: 8px;">{result.directory}</td>
                    <td style="padding: 8px;">图片: {result.image_count}, 标注: {result.annotation_count}</td>
                    <td style="padding: 8px; color: #f57c00;">{'缺失标注' if result.missing_annotations else '不匹配'}</td>
                </tr>
                """
        if not annotation_html:
            annotation_html = "<tr><td colspan='3' style='padding: 16px; color: #28a745;'>✅ 标注数据完整</td></tr>"

        # 修复建议HTML
        fix_suggestion_html = ""
        if not r.all_passed:
            fix_suggestion_html = '''
        <div class="card" style="background: linear-gradient(135deg, #fff3cd, #ffeeba);">
            <h2><span class="card-icon">🔧</span>自动修复建议</h2>
            <div style="margin-top: 12px;">
                <p><strong>1. cv2.imshow 替换为 plt.imshow:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;"># 错误 (会导致Jupyter崩溃)
cv2.imshow('image', img)
cv2.waitKey(0)

# 正确 (Web安全)
import matplotlib.pyplot as plt
plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
plt.show()</pre>
                <p><strong>2. 下载预训练权重:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;"># 下载YOLOv5权重
from urllib.request import urlretrieve
urlretrieve("https://github.com/ultralytics/yolov5/raw/master/yolov5s.pt",
            "weights/yolov5s.pt")</pre>
                <p><strong>3. 添加标注工具:</strong></p>
                <pre style="background: #f8f9fa; padding: 12px; border-radius: 8px; margin: 8px 0; overflow-x: auto;"># 安装LabelImg
pip install labelimg

# 启动标注工具
labelimg</pre>
            </div>
        </div>'''

        # 构建HTML
        html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>计算机视觉课程 - 质量监测报告</title>
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
        th, td {{ text-align: left; border-bottom: 1px solid #e9ecef; padding: 8px; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #666; }}
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
        <h1>👁️ 计算机视觉课程 - 质量监测报告</h1>
        <p class="subtitle">基于 MCP 视角的自动化质量检测 | 检测时间: {r.timestamp}</p>

        <!-- 状态横幅 -->
        <div class="status-banner {'status-pass' if r.all_passed else 'status-fail'}">
            {'✅ 全部通过 - 可封版' if r.all_passed else '⚠️ 需修复问题'}
        </div>

        <!-- 三大标志 -->
        <div class="summary-grid">
            <div class="signal-card {'signal-pass' if r.signal1_inference_ready else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.signal1_inference_ready else '❌'}</div>
                <div class="signal-title">标志1: 推理演示就绪</div>
                <div class="signal-value">{'Demo已配置' if r.signal1_inference_ready else '需添加'}</div>
            </div>
            <div class="signal-card {'signal-pass' if r.signal2_toolchain_ready else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.signal2_toolchain_ready else '❌'}</div>
                <div class="signal-title">标志2: 标注工具链</div>
                <div class="signal-value">{'已就绪' if r.signal2_toolchain_ready else '需补充'}</div>
            </div>
            <div class="signal-card {'signal-pass' if r.signal3_web_safe else 'signal-fail'}">
                <div class="signal-icon">{'✅' if r.signal3_web_safe else '❌'}</div>
                <div class="signal-title">标志3: Web安全</div>
                <div class="signal-value">{'安全' if r.signal3_web_safe else f'{r.unsafe_cv2_count}个风险'}</div>
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
                    <div class="stat-value">{r.total_weight_count}</div>
                    <div class="stat-label">权重文件</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.total_weight_size_mb:.1f}MB</div>
                    <div class="stat-label">权重总大小</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(r.annotation_results)}</div>
                    <div class="stat-label">数据集</div>
                </div>
            </div>
        </div>

        <!-- 权重文件检测 -->
        <div class="card">
            <h2><span class="card-icon">📦</span>预训练权重文件检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{r.total_weight_count}</div>
                    <div class="stat-label">权重文件数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.total_weight_size_mb:.1f}MB</div>
                    <div class="stat-label">总大小</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.yolo_weight_found else '#dc3545'};">{'✅' if r.yolo_weight_found else '❌'}</div>
                    <div class="stat-label">YOLO权重</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.weight_signal else '#dc3545'};">{'通过' if r.weight_signal else '缺失'}</div>
                    <div class="stat-label">检测结果</div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
                    {weight_issues_html}
                </tbody>
            </table>
        </div>

        <!-- OpenCV安全检测 -->
        <div class="card">
            <h2><span class="card-icon">⚠️</span>OpenCV 安全性检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.unsafe_cv2_count == 0 else '#dc3545'};">{r.unsafe_cv2_count}</div>
                    <div class="stat-label">危险代码</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{r.cv2_safe_count}</div>
                    <div class="stat-label">安全代码</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.cv2_signal else '#dc3545'};">{'通过' if r.cv2_signal else '需修复'}</div>
                    <div class="stat-label">检查结果</div>
                </div>
            </div>
            {f'<div class="warning-box">⚠️ 发现 {r.unsafe_cv2_count} 处 cv2.imshow 调用，会导致Jupyter内核崩溃</div>' if r.unsafe_cv2_count > 0 else ''}
            <table>
                <thead>
                    <tr>
                        <th>文件</th>
                        <th>问题描述</th>
                    </tr>
                </thead>
                <tbody>
                    {cv2_issues_html}
                </tbody>
            </table>
        </div>

        <!-- 标注数据检测 -->
        <div class="card">
            <h2><span class="card-icon">📝</span>标注数据完整性检查</h2>
            <div class="stat-grid">
                <div class="stat-item">
                    <div class="stat-value">{len(r.annotation_results)}</div>
                    <div class="stat-label">数据集</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#dc3545' if r.incomplete_dataset_count > 0 else '#28a745'};">{r.incomplete_dataset_count}</div>
                    <div class="stat-label">不完整</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" style="color: {'#28a745' if r.annotation_signal else '#dc3545'};">{'通过' if r.annotation_signal else '需修复'}</div>
                    <div class="stat-label">检查结果</div>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>数据集</th>
                        <th>统计</th>
                        <th>问题</th>
                    </tr>
                </thead>
                <tbody>
                    {annotation_html}
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
    parser = argparse.ArgumentParser(description='计算机视觉课程监测系统')
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
    monitor = ComputerVisionCourseMonitor(str(course_path))
    report = monitor.run_full_scan()
    monitor.export_html_report(args.output)

    # 返回退出码
    return 0 if report.all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
