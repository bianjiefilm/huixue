#!/usr/bin/env python3
"""
生成《神经网络与深度学习》课程视频
使用Pillow生成幻灯片图片，ffmpeg合成视频
"""
import os
import subprocess
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


COURSE_DIR = "/Users/jimfu/Work/huixue(yuanban)/ziyuan_data/课程资源/神经网络与深度学习"
AUDIO_DIR = f"{COURSE_DIR}/assets/audio"
VIDEO_DIR = f"{COURSE_DIR}/assets/videos"
TEMP_DIR = f"{COURSE_DIR}/assets/temp_slides"

# 幻灯片尺寸 (1920x1080)
SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080

# 颜色
COLOR_PRIMARY = (24, 144, 255)
COLOR_WHITE = (255, 255, 255)
COLOR_DARK = (38, 38, 38)
COLOR_LIGHT_BG = (248, 250, 252)


def get_font(size: int, bold: bool = False):
    """获取字体"""
    # macOS系统字体
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue

    return ImageFont.load_default()


def create_slide_image(title: str, bullets: list, slide_num: int, total: int) -> Image:
    """
    创建幻灯片图片

    Args:
        title: 幻灯片标题
        bullets: 要点列表
        slide_num: 当前幻灯片序号
        total: 总幻灯片数

    Returns:
        PIL Image对象
    """
    # 创建背景
    img = Image.new('RGB', (SLIDE_WIDTH, SLIDE_HEIGHT), COLOR_LIGHT_BG)
    draw = ImageDraw.Draw(img)

    # 顶部色块
    draw.rectangle([(0, 0), (SLIDE_WIDTH, 120)], fill=COLOR_PRIMARY)

    # 标题
    title_font = get_font(48, bold=True)
    draw.text((60, 35), title, font=title_font, fill=COLOR_WHITE)

    # 页码
    page_font = get_font(24)
    page_text = f"{slide_num}/{total}"
    draw.text((SLIDE_WIDTH - 100, 45), page_text, font=page_font, fill=COLOR_WHITE)

    # 内容区域
    content_font = get_font(36)
    y_pos = 180

    for bullet in bullets:
        # 绘制项目符号
        draw.ellipse([(60, y_pos + 12), (72, y_pos + 24)], fill=COLOR_PRIMARY)

        # 绘制文本（自动换行）
        text = bullet
        max_width = SLIDE_WIDTH - 160

        # 简单的文本换行
        words = list(text)
        lines = []
        current_line = ""

        for char in words:
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=content_font)
            if bbox[2] - bbox[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = char

        if current_line:
            lines.append(current_line)

        for i, line in enumerate(lines):
            x_offset = 90 if i == 0 else 90
            draw.text((x_offset, y_pos), line, font=content_font, fill=COLOR_DARK)
            y_pos += 50

        y_pos += 20

    # 底部装饰线
    draw.rectangle([(0, SLIDE_HEIGHT - 10), (SLIDE_WIDTH, SLIDE_HEIGHT)], fill=COLOR_PRIMARY)

    return img


def create_title_slide(chapter_title: str, subtitle: str = "神经网络与深度学习") -> Image:
    """创建标题页"""
    img = Image.new('RGB', (SLIDE_WIDTH, SLIDE_HEIGHT), COLOR_PRIMARY)
    draw = ImageDraw.Draw(img)

    # 主标题
    title_font = get_font(72, bold=True)
    bbox = draw.textbbox((0, 0), chapter_title, font=title_font)
    title_width = bbox[2] - bbox[0]
    x = (SLIDE_WIDTH - title_width) // 2
    draw.text((x, 380), chapter_title, font=title_font, fill=COLOR_WHITE)

    # 副标题
    sub_font = get_font(36)
    bbox = draw.textbbox((0, 0), subtitle, font=sub_font)
    sub_width = bbox[2] - bbox[0]
    x = (SLIDE_WIDTH - sub_width) // 2
    draw.text((x, 500), subtitle, font=sub_font, fill=(200, 220, 255))

    return img


def create_video_from_slides(chapter_id: str, chapter_data: dict) -> bool:
    """
    为单个章节创建视频

    Args:
        chapter_id: 章节ID
        chapter_data: 章节数据

    Returns:
        是否成功
    """
    chapter_title = chapter_data["title"]
    slides_data = chapter_data.get("slides", [])

    print(f"\n处理章节 {chapter_id}: {chapter_title}")

    # 创建临时目录
    temp_dir = Path(TEMP_DIR) / f"chapter_{chapter_id}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 生成幻灯片图片
    slide_images = []
    audio_files = []
    total_slides = len(slides_data) + 1  # +1 for title slide

    # 1. 标题页（无音频，持续3秒）
    title_img = create_title_slide(chapter_title)
    title_path = temp_dir / "slide_00.png"
    title_img.save(title_path)
    slide_images.append((str(title_path), 3.0))  # 3秒

    # 2. 内容页
    for i, slide in enumerate(slides_data):
        slide_idx = slide["slide_index"]
        slide_title = slide["title"]
        bullets = chapter_data["bullets"][i] if i < len(chapter_data.get("bullets", [])) else []

        # 创建幻灯片图片
        img = create_slide_image(slide_title, bullets, i + 1, len(slides_data))
        img_path = temp_dir / f"slide_{slide_idx:02d}.png"
        img.save(img_path)

        # 查找对应音频
        audio_path = Path(AUDIO_DIR) / f"chapter_{chapter_id}_slide_{slide_idx:02d}.mp3"
        if audio_path.exists():
            # 获取音频时长
            duration = get_audio_duration(str(audio_path))
            slide_images.append((str(img_path), duration))
            audio_files.append(str(audio_path))
        else:
            print(f"  警告: 音频不存在 {audio_path}")
            slide_images.append((str(img_path), 5.0))  # 默认5秒

    # 合成视频
    output_path = Path(VIDEO_DIR) / f"chapter_{chapter_id}_{chapter_title}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    success = concat_slides_to_video(slide_images, audio_files, str(output_path))

    # 清理临时文件
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    return success


def get_audio_duration(audio_path: str) -> float:
    """获取音频时长"""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True
        )
        return float(result.stdout.strip())
    except:
        return 5.0


def concat_slides_to_video(slides: list, audios: list, output_path: str) -> bool:
    """
    合并幻灯片和音频生成视频

    Args:
        slides: [(图片路径, 时长), ...]
        audios: [音频路径, ...]
        output_path: 输出路径

    Returns:
        是否成功
    """
    temp_dir = Path(output_path).parent / "temp_concat"
    temp_dir.mkdir(parents=True, exist_ok=True)

    segments = []

    # 标题页（无音频）
    if slides:
        title_img, title_duration = slides[0]
        title_video = temp_dir / "segment_000.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", title_img,
            "-c:v", "libx264",
            "-t", str(title_duration),
            "-pix_fmt", "yuv420p",
            "-r", "30",
            str(title_video)
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            segments.append(str(title_video))

    # 内容页（带音频）
    for i, ((img_path, duration), audio_path) in enumerate(zip(slides[1:], audios), start=1):
        segment_path = temp_dir / f"segment_{i:03d}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", img_path,
            "-i", audio_path,
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            "-r", "30",
            str(segment_path)
        ]

        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            segments.append(str(segment_path))
            print(f"  片段 {i} 已生成")
        else:
            print(f"  片段 {i} 生成失败")

    if not segments:
        return False

    # 合并所有片段
    list_file = temp_dir / "segments.txt"
    with open(list_file, 'w') as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True)

    # 清理
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)

    if result.returncode == 0:
        print(f"  ✅ 视频已保存: {output_path}")
        return True
    else:
        print(f"  ❌ 视频合成失败")
        return False


# 章节内容数据（从PPT生成脚本获取）
CHAPTERS_CONTENT = [
    {
        "id": "01",
        "title": "人工智能起源与发展",
        "slides": [
            {"slide_index": 1, "title": "什么是人工智能？"},
            {"slide_index": 2, "title": "人工智能发展历程"},
            {"slide_index": 3, "title": "人工智能的三个层次"}
        ],
        "bullets": [
            ["人工智能(AI)是让机器模拟人类智能的技术", "包括学习、推理、感知、理解语言等能力", "目标是创造能够自主思考和决策的智能系统", "应用领域：图像识别、语音处理、自然语言处理等"],
            ["1956年：达特茅斯会议，AI概念首次提出", "1960-1970年代：专家系统兴起", "1980-1990年代：机器学习方法发展", "2006年至今：深度学习革命，GPU加速训练"],
            ["弱人工智能：专注于特定任务（如下棋、图像识别）", "强人工智能：具有人类级别的通用智能", "超级人工智能：超越人类智能的假设阶段", "目前我们主要处于弱人工智能阶段"]
        ]
    },
    {
        "id": "02",
        "title": "TensorFlow环境安装",
        "slides": [
            {"slide_index": 1, "title": "TensorFlow简介"},
            {"slide_index": 2, "title": "环境准备"},
            {"slide_index": 3, "title": "安装步骤"},
            {"slide_index": 4, "title": "验证与测试"}
        ],
        "bullets": [
            ["Google开发的开源深度学习框架", "支持CPU、GPU、TPU等多种硬件加速", "TensorFlow 2.0采用即时执行模式，更易上手", "广泛应用于学术研究和工业生产"],
            ["Python 3.8或更高版本", "推荐使用Anaconda管理环境", "GPU版本需要CUDA和cuDNN支持", "建议使用虚拟环境隔离项目依赖"],
            ["创建虚拟环境：conda create -n tf python=3.9", "激活环境：conda activate tf", "安装TensorFlow：pip install tensorflow", "验证安装：import tensorflow as tf"],
            ["检查版本：tf.__version__", "检查GPU支持：tf.config.list_physical_devices('GPU')", "运行简单计算：tf.constant([1, 2, 3])", "完成第一个TensorFlow程序"]
        ]
    },
    {
        "id": "03",
        "title": "Python语言基础",
        "slides": [
            {"slide_index": 1, "title": "Python基础语法"},
            {"slide_index": 2, "title": "列表与字典操作"},
            {"slide_index": 3, "title": "面向对象编程"}
        ],
        "bullets": [
            ["变量定义与数据类型（int、float、str、list、dict）", "条件语句：if-elif-else结构", "循环语句：for和while循环", "函数定义：def关键字与参数传递"],
            ["列表切片：list[start:end:step]", "列表推导式：[x**2 for x in range(10)]", "字典的键值对操作", "常用方法：append、extend、pop、get等"],
            ["类的定义：class关键字", "构造方法：__init__", "实例属性与类属性", "继承与多态"]
        ]
    },
    {
        "id": "04",
        "title": "科学计算与可视化",
        "slides": [
            {"slide_index": 1, "title": "NumPy数组操作"},
            {"slide_index": 2, "title": "NumPy核心操作"},
            {"slide_index": 3, "title": "Matplotlib可视化"}
        ],
        "bullets": [
            ["NumPy是Python科学计算的核心库", "ndarray：高效的多维数组对象", "数组创建：array、zeros、ones、arange", "数组运算：支持广播机制的向量化操作"],
            ["数组形状变换：reshape、transpose、flatten", "数组索引与切片：支持多维索引", "数学运算：dot、matmul、sum、mean", "线性代数：矩阵乘法、求逆、特征值分解"],
            ["plt.plot()：绑制折线图", "plt.scatter()：绘制散点图", "plt.imshow()：显示图像数据", "子图与布局：subplot、figure"]
        ]
    },
    {
        "id": "05",
        "title": "TensorFlow基础",
        "slides": [
            {"slide_index": 1, "title": "张量（Tensor）概念"},
            {"slide_index": 2, "title": "张量操作"},
            {"slide_index": 3, "title": "自动微分（AutoGrad）"}
        ],
        "bullets": [
            ["张量是TensorFlow的核心数据结构", "标量（0维）、向量（1维）、矩阵（2维）、高维张量", "创建张量：tf.constant、tf.Variable", "张量属性：shape、dtype、device"],
            ["数学运算：tf.add、tf.multiply、tf.matmul", "形状操作：tf.reshape、tf.transpose", "聚合操作：tf.reduce_sum、tf.reduce_mean", "索引切片：与NumPy语法兼容"],
            ["GradientTape：记录计算过程", "自动计算梯度：tape.gradient()", "支持高阶导数计算", "是反向传播算法的核心实现"]
        ]
    },
    {
        "id": "06",
        "title": "监督学习基础",
        "slides": [
            {"slide_index": 1, "title": "监督学习概述"},
            {"slide_index": 2, "title": "线性回归模型"},
            {"slide_index": 3, "title": "梯度下降优化"}
        ],
        "bullets": [
            ["监督学习：从标注数据中学习映射关系", "训练数据：输入特征X和目标标签Y", "回归问题：预测连续值（如房价预测）", "分类问题：预测离散类别（如图像分类）"],
            ["模型形式：y = wx + b", "损失函数：均方误差MSE", "优化目标：最小化损失函数", "梯度下降：迭代更新参数"],
            ["梯度：损失函数对参数的偏导数", "学习率：控制参数更新步长", "批量梯度下降、随机梯度下降、小批量梯度下降", "收敛条件：损失不再显著下降"]
        ]
    },
    {
        "id": "07",
        "title": "人工神经网络",
        "slides": [
            {"slide_index": 1, "title": "神经元模型"},
            {"slide_index": 2, "title": "多层感知机（MLP）"},
            {"slide_index": 3, "title": "使用Keras构建MLP"}
        ],
        "bullets": [
            ["生物神经元的数学抽象", "输入加权求和：z = Σ(wi·xi) + b", "激活函数：引入非线性变换", "常用激活函数：Sigmoid、ReLU、Tanh"],
            ["输入层：接收原始特征", "隐藏层：进行特征变换和提取", "输出层：产生最终预测结果", "全连接结构：每层神经元与下一层全部连接"],
            ["Sequential模型：层的线性堆叠", "Dense层：全连接层", "compile()：配置优化器和损失函数", "fit()：训练模型"]
        ]
    },
    {
        "id": "08",
        "title": "深度学习基础",
        "slides": [
            {"slide_index": 1, "title": "深度学习的优势"},
            {"slide_index": 2, "title": "反向传播算法"},
            {"slide_index": 3, "title": "常用优化器"},
            {"slide_index": 4, "title": "防止过拟合"}
        ],
        "bullets": [
            ["自动特征学习：无需手工设计特征", "层次化表示：从低级到高级特征", "端到端学习：直接从原始数据到结果", "大数据时代的最佳选择"],
            ["前向传播：计算网络输出和损失", "反向传播：从输出层向输入层传递误差", "链式法则：计算每层参数的梯度", "参数更新：使用梯度下降优化"],
            ["SGD：随机梯度下降", "Momentum：带动量的梯度下降", "Adam：自适应学习率优化器", "学习率调度：动态调整学习率"],
            ["正则化：L1和L2正则化", "Dropout：随机丢弃神经元", "早停法：监控验证集性能", "数据增强：扩充训练数据"]
        ]
    },
    {
        "id": "09",
        "title": "卷积神经网络",
        "slides": [
            {"slide_index": 1, "title": "卷积操作原理"},
            {"slide_index": 2, "title": "CNN基本组件"},
            {"slide_index": 3, "title": "经典CNN架构"},
            {"slide_index": 4, "title": "使用Keras构建CNN"}
        ],
        "bullets": [
            ["卷积核：用于提取局部特征的滤波器", "滑动窗口：在输入图像上滑动计算", "特征图：卷积操作的输出", "参数共享：大幅减少参数数量"],
            ["卷积层（Conv2D）：提取空间特征", "池化层（MaxPool）：降低特征图尺寸", "全连接层（Dense）：分类决策", "激活函数（ReLU）：引入非线性"],
            ["LeNet：最早的CNN，用于手写数字识别", "AlexNet：2012年ImageNet冠军", "VGG：使用小卷积核的深层网络", "ResNet：残差连接，实现超深网络训练"],
            ["Conv2D：二维卷积层", "MaxPooling2D：最大池化层", "Flatten：展平层", "实战：MNIST手写数字识别"]
        ]
    },
    {
        "id": "10",
        "title": "目标检测基础",
        "slides": [
            {"slide_index": 1, "title": "目标检测任务"},
            {"slide_index": 2, "title": "目标检测方法演进"},
            {"slide_index": 3, "title": "YOLO算法简介"},
            {"slide_index": 4, "title": "目标检测评估指标"}
        ],
        "bullets": [
            ["定位：确定目标在图像中的位置（边界框）", "分类：识别目标的类别", "多目标检测：同时检测多个不同类别的目标", "应用场景：自动驾驶、安防监控、医学影像"],
            ["传统方法：滑动窗口 + 手工特征", "两阶段方法：R-CNN系列", "单阶段方法：YOLO、SSD", "发展趋势：更快、更准、更轻量"],
            ["You Only Look Once：一次性预测所有目标", "将图像划分为网格，每个网格预测边界框", "实时检测：可达到30FPS以上", "版本演进：YOLOv1到YOLOv8"],
            ["IoU（交并比）：预测框与真实框的重合度", "Precision和Recall：精确率和召回率", "mAP（平均精度均值）：综合评估指标", "FPS：每秒处理帧数，衡量速度"]
        ]
    }
]


def main():
    """主函数"""
    print("=" * 60)
    print("生成《神经网络与深度学习》课程视频")
    print("=" * 60)

    Path(VIDEO_DIR).mkdir(parents=True, exist_ok=True)

    for chapter in CHAPTERS_CONTENT:
        success = create_video_from_slides(chapter["id"], chapter)
        if success:
            print(f"✅ 章节 {chapter['id']} 视频已完成")
        else:
            print(f"❌ 章节 {chapter['id']} 视频生成失败")

    print("\n" + "=" * 60)
    print("视频生成完成")
    print(f"保存位置: {VIDEO_DIR}")
    print("=" * 60)

    # 列出生成的文件
    video_files = list(Path(VIDEO_DIR).glob("*.mp4"))
    print(f"共生成 {len(video_files)} 个视频文件")
    for vf in sorted(video_files):
        print(f"  - {vf.name}")


if __name__ == "__main__":
    main()
