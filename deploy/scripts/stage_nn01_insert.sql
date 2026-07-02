-- NN1: 神经网络与深度学习概述
-- practice_id=8, order_in_practice=1, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$神经网络与深度学习概述$v$,
        'PRACTICE',
        1,
        $v$beginner$v$,
        $v$## 神经网络的发展简史

## 1.1 三次浪潮

神经网络不是新概念, 它在过去 60 多年里经历了三次"沉浮":

**第一次 (1958-1969)**: Frank Rosenblatt 发明 Perceptron, 单层神经元能学习简单线性分类。但 Minsky 1969 年指出 Perceptron 无法学习 XOR (异或), 业界陷入第一次"AI 寒冬"。

**第二次 (1986-1995)**: Rumelhart 提出多层网络 + 反向传播, 理论上能逼近任意连续函数, 但当时算力不足, SVM 等传统方法在小数据集上表现更好, 神经网络再次降温。

**第三次 (2012-至今)**: AlexNet 在 ImageNet 大幅打败传统方法, 触发深度学习大爆发。GPU 计算 + 大规模标注数据 + 一系列工程算法改进共同促成。2017 年 Transformer 架构出现, 2022 年 ChatGPT 引爆大语言模型时代。

## 1.2 为什么这一次不一样

第三次浪潮的成功依赖三个要素同时到位:
- **算力**: GPU 并行让大型矩阵乘法可行, NVIDIA 单卡算力从 2010 年的 1 TFLOPS 增长到 2024 年的 100+ TFLOPS
- **数据**: ImageNet (1400 万图像) / 互联网文本 (TB 级) / 标注众包 (Mechanical Turk) 让大模型有训练材料
- **算法**: 多个工程突破让大网络可训练 (合理初始化 / 优化器 / 残差结构 / 正则化技术)

理解这三个要素是理解神经网络"为什么能 work"的根本。算法改进只是其中一项, 没有算力与数据, 算法再好也跑不动。


## 三大主干网络类型

## 2.1 三大架构与适用场景

神经网络主要分三大类, 各有适配的输入数据类型:

| 架构 | 输入数据特点 | 典型应用 |
|------|------------|---------|
| 全连接 (FC) | 表格、向量化特征 | 信贷违约预测、推荐系统排序 |
| 卷积 (CNN) | 网格状空间结构 (图像/视频) | 图像分类、目标检测、医学影像 |
| 循环 (RNN) | 序列结构 (时间/语言) | 时序预测、语音识别、机器翻译 |

工程上还有 Transformer (源自 RNN 但用注意力机制取代循环) 已成为 NLP / 多模态的主流, 后续课程会专门展开。本关只要求理解三大主干架构的区分。

## 2.2 输入模态判别

给定一份输入数据, 通过它的 shape (维度形状) 可以快速判断适合哪类网络:

| 输入 shape | 模态 | 适用网络 |
|-----------|------|---------|
| (n_features,) | tabular | FC |
| (T, features) | sequence | RNN / Transformer |
| (H, W, C) | image | CNN |
| (T, H, W, C) | video | 3D-CNN / CNN+RNN |

shape 维度本身不能 100% 决定网络选择 — 业务上的"是否需要建模时间依赖"、"是否需要建模空间局部性"也是关键考量。但形状判别给了一个快速起点。

## 2.3 模型不是越深越好

工程实务中, 选择网络规模需要平衡:
- 数据量 1k-10k: 浅 FC (1-3 隐层) 通常足够, 深网络反而过拟合
- 数据量 10k-100k: 中等深度 FC 或简单 CNN
- 数据量 100k-10M: 深网络 (ResNet 量级 / 几十层)
- 数据量 10M+: 大模型 (百层 / 亿参数+)

"数据量决定模型容量"是工程实务的第一定律。盲目套用大模型在小数据上几乎一定灾难。


## 模型规模与工程考量

## 3.1 参数量计算

全连接网络的参数数量 = 各层 (权重 W + 偏置 b) 之和:

$\text{params} = \sum_{i=1}^{L-1} \left( s_i \cdot s_{i+1} + s_{i+1} \right)$

其中 $s_i$ 是第 $i$ 层神经元数, $L$ 是层数。$s_i \cdot s_{i+1}$ 是 W 的元素数, $s_{i+1}$ 是 b 的元素数。

例: 一个 [784, 128, 10] 的网络 (典型小图像分类入门尺寸):
- 第 1 层: 784 × 128 + 128 = 100,480
- 第 2 层: 128 × 10 + 10 = 1,290
- 总参数 = 101,770

## 3.2 存储估算

参数通常用 fp32 (单精度) 或 fp16 (半精度) 保存:

$\text{size}_{MB} = \text{params} \cdot \text{bytes\_per\_param} / 1024^2$

fp32 是 4 bytes, fp16 是 2 bytes。一个 100M 参数的模型在 fp32 下约 381 MB, fp16 下约 191 MB — 这决定了能否放进显存。

工程实务: 显存 80GB 的 GPU 训练大模型时, 模型参数 + 梯度 + 优化器状态 + 激活值, 常需要 4-8 倍模型参数大小的显存。所以"参数 100M 的模型需要 80GB 显存"听起来很离谱, 但确实是后续课程中介绍的优化器场景下的真实开销。

## 3.3 训练/验证/测试集划分

神经网络训练相比传统机器学习, 多一个**验证集 (val)** 维度:

- **train**: 用来更新网络权重 (反向传播)
- **val**: 训练过程中用来选超参数与早停 (不参与权重更新)
- **test**: 上线前最终评估, **整个训练过程不能看**

常见比例 70/15/15 或 80/10/10。数据量少时 (< 10k) 可放宽 val 到 20%; 数据量极大时 val 可压到 1% 也足够 (统计上 1% × 1M = 10k val 已经稳定)。


## 业务案例: 智能门禁人脸识别

## 4.1 场景

某园区要部署 100 个摄像头门禁, 用神经网络做人脸识别。约束:
- 每天 1 万人次进出, 比对延迟 < 200ms (用户接受度)
- 误识别率 (FAR) < 0.001% (安全要求)
- 漏识别率 (FRR) < 1% (用户体验)

## 4.2 设计选择

**网络类型**: 输入是 RGB 图像 (224, 224, 3), 选 CNN。

**模型规模**: 候选 ResNet-50 (25M 参数) 或 MobileNet-v2 (3.5M 参数)。
- ResNet-50 准确率高但 fp32 约 95 MB, 单次推理 ~50ms (GPU) / ~500ms (CPU)
- MobileNet-v2 准确率略低但 fp32 约 13 MB, 单次推理 ~10ms (GPU) / ~50ms (CPU)
- 100 个门禁同时高峰每秒 100 次, GPU 集中部署还是单点边缘推理 → 选 MobileNet-v2 边缘部署, 满足 200ms 延迟

**数据划分**: 收集 50000 张人脸样本, 70/15/15 = 35000 train / 7500 val / 7500 test。每个员工至少 5 张样本保证类别覆盖。

**失败模式**: 戴口罩 / 戴墨镜 / 极端光照 — 这些边界条件需要单独收集数据增强训练, 不能假设 50000 张"普通"样本就够。

## 4.3 NN 工程的常见陷阱

- **数据决定上限, 算法决定逼近上限的速度**: 数据脏任何算法救不回来; 数据干净简单网络足够
- **train 与 inference 性能不对称**: 训练 1 周, 推理要 < 200ms; 模型选择必须照顾推理时长 + 内存
- **指标的业务对齐**: 安防 FAR 比 FRR 致命, 推荐相反 — 按业务代价不对称定取舍

神经网络是工具, 不是答案。这门课会逐关展开它的内部机制, 让你能从工具使用者升级成"会判断什么时候不该用神经网络"的工程师。

$v$,
        $v${"questions": [{"id": "q01-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn01.py 中的 4 个函数; 评测以 test_nn01.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_dp_two_layers$v$, $v$[3, 4] → 3*4 + 4 = 16$v$, false, $v$[3, 4] → 3*4 + 4 = 16$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_dp_three_layers$v$, $v$[3, 4, 2] → 16 + (4*2+2) = 26$v$, false, $v$[3, 4, 2] → 16 + (4*2+2) = 26$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_dp_typical_mnist$v$, $v$[784, 128, 10] → 784*128+128 + 128*10+10 = 100480 + 1290 = 101770$v$, false, $v$[784, 128, 10] → 784*128+128 + 128*10+10 = 100480 + 1290 = 101770$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_dp_minimal$v$, $v$[1, 1] → 1*1+1 = 2$v$, false, $v$[1, 1] → 1*1+1 = 2$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_dp_four_layers$v$, $v$[100, 50, 25, 10] → 5050 + 1275 + 260 = 6585$v$, false, $v$[100, 50, 25, 10] → 5050 + 1275 + 260 = 6585$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_dp_single_layer$v$, $v$边界: [5] 单层无连接 → 0$v$, false, $v$边界: [5] 单层无连接 → 0$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_dp_raises_on_empty$v$, $v$边界: 空列表 → ValueError$v$, false, $v$边界: 空列表 → ValueError$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_dp_raises_on_non_list$v$, $v$负例: 非 list → TypeError$v$, false, $v$负例: 非 list → TypeError$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_cim_tabular$v$, $v$(1000,) → 'tabular'$v$, false, $v$(1000,) → 'tabular'$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_cim_sequence$v$, $v$(50, 64) → 'sequence'$v$, false, $v$(50, 64) → 'sequence'$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_cim_image$v$, $v$(224, 224, 3) → 'image'$v$, false, $v$(224, 224, 3) → 'image'$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_cim_video$v$, $v$(16, 224, 224, 3) → 'video'$v$, false, $v$(16, 224, 224, 3) → 'video'$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_cim_short_tabular$v$, $v$(5,) → 'tabular'$v$, false, $v$(5,) → 'tabular'$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_cim_long_video$v$, $v$(32, 96, 128, 3) → 'video'$v$, false, $v$(32, 96, 128, 3) → 'video'$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_cim_raises_on_empty_tuple$v$, $v$边界: () → ValueError$v$, false, $v$边界: () → ValueError$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_cim_raises_on_5d$v$, $v$边界: 5D 不支持 → ValueError$v$, false, $v$边界: 5D 不支持 → ValueError$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_cim_raises_on_non_tuple$v$, $v$负例: 非 tuple → TypeError$v$, false, $v$负例: 非 tuple → TypeError$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_cdss_70_15_15$v$, $v$100, [0.7, 0.15, 0.15] → [70, 15, 15]$v$, true, $v$100, [0.7, 0.15, 0.15] → [70, 15, 15]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_cdss_50_50$v$, $v$10, [0.5, 0.5] → [5, 5]$v$, true, $v$10, [0.5, 0.5] → [5, 5]$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_cdss_remainder_to_last$v$, $v$99, [0.6, 0.2, 0.2] → [59, 19, 21] (余数 21 给最后) int(99*0.6)=59, int(99*0.2)=19, 99-59-19=21$v$, true, $v$99, [0.6, 0.2, 0.2] → [59, 19, 21] (余数 21 给最后) int(99*0.6)=59, int(99*0.2)=19, 99-59-19=21$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_cdss_8_2_split$v$, $v$4, [0.8, 0.2] → [3, 1] (int(4*0.8)=3, 4-3=1)$v$, true, $v$4, [0.8, 0.2] → [3, 1] (int(4*0.8)=3, 4-3=1)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_cdss_large$v$, $v$1000, [0.6, 0.2, 0.2] → [600, 200, 200]$v$, true, $v$1000, [0.6, 0.2, 0.2] → [600, 200, 200]$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_cdss_zero_total$v$, $v$边界: total=0, ratios=[0.5,0.5] → [0, 0]$v$, true, $v$边界: total=0, ratios=[0.5,0.5] → [0, 0]$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_cdss_raises_on_bad_ratios$v$, $v$边界: ratios sum != 1.0 → ValueError$v$, true, $v$边界: ratios sum != 1.0 → ValueError$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_cdss_raises_on_negative_total$v$, $v$边界: total 负 → ValueError$v$, true, $v$边界: total 负 → ValueError$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_cdss_raises_on_non_list$v$, $v$负例: ratios 非 list → TypeError$v$, true, $v$负例: ratios 非 list → TypeError$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_espm_one_million$v$, $v$1M params → 4M bytes / 1024^2 ≈ 3.8147 MB$v$, true, $v$1M params → 4M bytes / 1024^2 ≈ 3.8147 MB$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_espm_zero$v$, $v$0 params → 0 MB$v$, true, $v$0 params → 0 MB$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_espm_small_thousand$v$, $v$1000 params → 0.0038 MB$v$, true, $v$1000 params → 0.0038 MB$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_espm_resnet50$v$, $v$25M params (ResNet-50 量级) → ~95.37 MB$v$, true, $v$25M params (ResNet-50 量级) → ~95.37 MB$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_espm_hundred_million$v$, $v$100M params → ~381.47 MB$v$, true, $v$100M params → ~381.47 MB$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_espm_mobilenet$v$, $v$3.5M params (MobileNet 量级) → ~13.35 MB$v$, true, $v$3.5M params (MobileNet 量级) → ~13.35 MB$v$, NULL, 32),
    ($v$tc_33$v$, $v$test_espm_raises_on_negative$v$, $v$边界: 负 → ValueError$v$, true, $v$边界: 负 → ValueError$v$, NULL, 33),
    ($v$tc_34$v$, $v$test_espm_raises_on_non_int$v$, $v$负例: 非 int → TypeError$v$, true, $v$负例: 非 int → TypeError$v$, NULL, 34)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
