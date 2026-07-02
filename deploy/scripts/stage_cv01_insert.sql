-- CV1: 计算机视觉概述与流程
-- practice_id=9, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$计算机视觉概述与流程$v$,
        'PRACTICE',
        1,
        $v$beginner$v$,
        $v$## CV 任务的全景

## 1.1 CV 与 NN 的关系

计算机视觉 (Computer Vision, CV) 是一个应用领域, 现代 CV 的主流技术是基于神经网络的方法 (NN09 卷积神经网络是 CV 的标准工具)。但 CV 的工程实务远不止"训练神经网络" — 还包括图像预处理、几何变换、传统算法 (滤波/边缘/形态学) 与神经网络方法的混合。

CV 课程目标: 从图像数据到模型应用走完一遍, 理解 CV 工程的完整流水线。

## 1.2 4 类主流 CV 任务

| 任务 | 输入 | 输出 | 典型场景 |
|------|------|------|----------|
| **图像分类** | 图像 | 类别标签 | 商品识别、医疗诊断 |
| **目标检测** | 图像 | 边界框 + 标签列表 | 自动驾驶、安防 |
| **图像像素级标注** | 图像 | 像素级标签 | 医学影像、自动驾驶 |
| **人脸/物体识别** | 图像 | 身份/实例 ID | 门禁、刷脸支付 |

四个任务难度递增 — 分类只需 1 个全局预测, 检测要框出多个对象, 像素级标注要每像素标签, 识别要区分同类不同实例 (如不同的人)。

## 1.3 输入模态与维度

CV 数据的形状 (复习 NN01 输入模态):

| shape | 含义 | 示例 |
|-------|------|------|
| (H, W) | 单通道图 | (28, 28) MNIST 风格 |
| (H, W, C) | 彩色图 | (224, 224, 3) ImageNet 标准 |
| (T, H, W, C) | 视频 | (16, 256, 256, 3) 16 帧片段 |

$C$ (channels) 通常是 1 (单通道) 或 3 (彩色)。后续课程会展开色彩空间细节。


## 图像存储与缩放

## 2.1 原始图像的存储

未压缩的图像存储 = $W \times H \times C \times \text{bytes/pixel}$。

uint8 (一字节/像素) 是默认, 一张 1920×1080×3 的彩色图 ≈ 6.2 MB。

工程实务: 数据集存储很少用 uint8 原始格式, 常用 PNG / JPEG 压缩 (JPEG 通常压缩到 1/10)。但内存中处理时, 加载到张量后是 uint8 或 fp32 形式。

## 2.2 长宽比缩放

把图像缩放到统一大小是 CV 工程的高频步骤。直接 resize 到 (224, 224) 会破坏长宽比, 让方形物体变形。**保持长宽比 + 短边对齐目标尺寸**是更合理的做法:

给定原始 $(W_o, H_o)$ 与目标最大边 $T$:

$\text{ratio} = T / \max(W_o, H_o)$
$W' = \text{round}(W_o \cdot \text{ratio})$
$H' = \text{round}(H_o \cdot \text{ratio})$

例: 原图 (1920, 1080), 目标 max=224. ratio = 224/1920 ≈ 0.1167. W' = 224, H' = 126.

短边小于目标时, 通常配合 padding 补到正方形 (224, 224)。本关只要求计算缩放后尺寸。

## 2.3 像素归一化

原始像素值在 [0, 255] (uint8), 神经网络输入希望 [0, 1] 或 [-1, 1]:

$\tilde{x} = x / 255.0$ (映射到 [0, 1])

或更精细:
$\tilde{x} = (x - \mu) / \sigma$ (标准化, 用预计算的 ImageNet $\mu / \sigma$)

工程实务: ImageNet 预训练模型用 $\mu = [0.485, 0.456, 0.406]$, $\sigma = [0.229, 0.224, 0.225]$ (复习 MJ03 z-score 标准化思想)。

本关只要求 [0, 1] 归一化, 进阶标准化在后续课程展开。


## 业务案例: 智慧城市图像处理流水线

## 3.1 场景

智慧城市部署 1000 路监控摄像头, 每路每秒 30 帧 (1080p 彩色), 实时识别异常行为 (打架、聚集、跌倒) 并报警。

架构 (高层):
- 边缘端: 摄像头 → 抽帧 (1 fps) + 缩放到 (224, 224) + uint8→fp32 归一化 → 上传
- 云端: 神经网络推理 → 返回类别概率 → 阈值后报警

## 3.2 数据流估算

原始数据: 1000 路 × 30 fps × 1920×1080×3×1 byte = 186 GB/秒。完全不能直接传输, 必须边缘处理。

边缘抽帧 + 缩放后: 1000 路 × 1 fps × 224×224×3×1 byte = 150 MB/秒。压缩传输后约 15 MB/秒, 网络可承受。

## 3.3 4 步流水线

| 步骤 | 函数 (本关对应) | 业务含义 |
|------|----------------|----------|
| 1 任务定位 | classify_cv_task | 决定用什么模型 (分类还是检测) |
| 2 存储估算 | compute_image_size_bytes | 决定边缘/云端分工 |
| 3 保持长宽比缩放 | resize_aspect_ratio | 标准化输入大小 |
| 4 像素归一化 | normalize_pixel_array | 转为模型期望的输入分布 |

4 步看似简单, 但任何一步出错 (任务选错 / 存储估错爆显存 / 缩放变形 / 归一化错误) 都会让上线失败。

## 3.4 CV 工程口诀

- **任务先定位**: 分类 / 检测 / 像素标注完全不同模型, 不要先选模型
- **存储与延迟**: 上线前先估算, 比训练完才发现内存不够好
- **保长宽比**: 直接 resize 让物体变形, 几乎一定降准确率
- **归一化不能省**: 神经网络对输入分布敏感, 这是必修项, 不是可选

$v$,
        $v${"questions": [{"id": "q01-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv01.py 中的 4 个函数; 评测以 test_cv01.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_cls_classification$v$, $v$cls classification$v$, false, $v$cls classification$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_cls_detection$v$, $v$cls detection$v$, false, $v$cls detection$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_cls_pixel_annotation$v$, $v$cls pixel annotation$v$, false, $v$cls pixel annotation$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_cls_recognition$v$, $v$cls recognition$v$, false, $v$cls recognition$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_cls_different_size_image$v$, $v$不同尺寸但仍是 3D$v$, false, $v$不同尺寸但仍是 3D$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_cls_raises_on_wrong_shape_length$v$, $v$cls raises on wrong shape length$v$, false, $v$cls raises on wrong shape length$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_cls_raises_on_invalid_output_type$v$, $v$cls raises on invalid output type$v$, false, $v$cls raises on invalid output type$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_cls_raises_on_non_tuple$v$, $v$cls raises on non tuple$v$, false, $v$cls raises on non tuple$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_bytes_uint8_rgb$v$, $v$1920×1080×3×1 = 6220800$v$, false, $v$1920×1080×3×1 = 6220800$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_bytes_uint8_grayscale$v$, $v$28×28×1×1 = 784$v$, false, $v$28×28×1×1 = 784$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_bytes_fp32$v$, $v$224×224×3×4 = 602112$v$, false, $v$224×224×3×4 = 602112$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_bytes_fp16$v$, $v$512×512×3×2 = 1572864$v$, false, $v$512×512×3×2 = 1572864$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_bytes_minimal$v$, $v$1×1×1×1 = 1$v$, false, $v$1×1×1×1 = 1$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_bytes_raises_on_zero$v$, $v$bytes raises on zero$v$, false, $v$bytes raises on zero$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_bytes_raises_on_negative$v$, $v$bytes raises on negative$v$, false, $v$bytes raises on negative$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_bytes_raises_on_non_int$v$, $v$bytes raises on non int$v$, false, $v$bytes raises on non int$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_rar_landscape$v$, $v$1920×1080 → max=224. ratio=224/1920≈0.1167. W'=224, H'=126$v$, true, $v$1920×1080 → max=224. ratio=224/1920≈0.1167. W'=224, H'=126$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_rar_portrait$v$, $v$1080×1920 → max=224. ratio=224/1920. H'=224, W'=126$v$, true, $v$1080×1920 → max=224. ratio=224/1920. H'=224, W'=126$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_rar_square$v$, $v$500×500 → max=300. W'=H'=300$v$, true, $v$500×500 → max=300. W'=H'=300$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_rar_no_resize_needed$v$, $v$100×50 → max=100. ratio=1, 不变$v$, true, $v$100×50 → max=100. ratio=1, 不变$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_rar_2_to_1_ratio$v$, $v$800×400 → max=200. ratio=0.25. W'=200, H'=100$v$, true, $v$800×400 → max=200. ratio=0.25. W'=200, H'=100$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_rar_raises_on_zero$v$, $v$rar raises on zero$v$, true, $v$rar raises on zero$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_rar_raises_on_negative_target$v$, $v$rar raises on negative target$v$, true, $v$rar raises on negative target$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_rar_raises_on_non_int$v$, $v$rar raises on non int$v$, true, $v$rar raises on non int$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_npa_basic$v$, $v$[0, 127, 255] / 255 → [0, 0.498, 1.0]$v$, true, $v$[0, 127, 255] / 255 → [0, 0.498, 1.0]$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_npa_all_zeros$v$, $v$全 0 → 全 0$v$, true, $v$全 0 → 全 0$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_npa_all_max$v$, $v$全 255 → 全 1.0$v$, true, $v$全 255 → 全 1.0$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_npa_custom_max$v$, $v$[0, 8, 16] max_value=16 → [0, 0.5, 1.0] (sklearn.digits 风格)$v$, true, $v$[0, 8, 16] max_value=16 → [0, 0.5, 1.0] (sklearn.digits 风格)$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_npa_intermediate$v$, $v$[64, 128, 192] / 255$v$, true, $v$[64, 128, 192] / 255$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_npa_raises_on_empty$v$, $v$npa raises on empty$v$, true, $v$npa raises on empty$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_npa_raises_on_out_of_range$v$, $v$超出 [0, max_value] 范围$v$, true, $v$超出 [0, max_value] 范围$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_npa_raises_on_non_list$v$, $v$npa raises on non list$v$, true, $v$npa raises on non list$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
