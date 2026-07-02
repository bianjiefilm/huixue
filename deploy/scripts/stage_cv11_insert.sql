-- CV11: 图像分割 (二值 / 语义)
-- practice_id=9, order_in_practice=11, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$图像分割 (二值 / 语义)$v$,
        'PRACTICE',
        11,
        $v$hard$v$,
        $v$## 图像分割的本质

## 1.1 分割 vs 检测 vs 分类

复习 CV09 的分类与 CV10 的检测, 分割是 CV 任务谱系的下一层粒度:
- **分类**: 一图一类别
- **检测**: 一图多 BBox + 类别
- **分割**: 一图每个像素一个类别

分割的输出是与输入图同尺寸的"标签图" — 每个像素有自己的类别。

## 1.2 分割的两大范式

- **二值分割 (binary segmentation)**: 输出 0/1 mask, 区分前景与背景。例: 缺陷检测把"是缺陷"标 1, 其他标 0。
- **多类分割 (multi-class)**: 每个像素属于 N 类之一。例: 自动驾驶把每个像素标为道路/车辆/行人/天空等。多类分割也叫"语义分割"。

本关聚焦二值分割 (最常见的工业场景), 多类分割是延伸概念。

## 1.3 分割的评估指标

像素级任务有专门的评估指标:

### Pixel Accuracy

$\text{PA} = \frac{\text{正确预测的像素数}}{\text{总像素数}}$

简单直观, 但对**类别不平衡**敏感: 99% 背景 + 1% 前景的图, 全预测背景就有 99% PA, 看起来很好实际无用。

### Dice 系数 / IoU 系数

Dice 系数 (= F1 score) 解决类别不平衡:

$\text{Dice}(A, B) = \frac{2 |A \cap B|}{|A| + |B|}$

其中 $|A|$ 是预测前景像素数, $|B|$ 是真值前景像素数, $|A \cap B|$ 是两者都为前景的像素数。

IoU 系数 (复习 CV10 BBox IoU, 这里是像素 IoU):

$\text{IoU} = \frac{|A \cap B|}{|A \cup B|}$

关系: Dice = $\frac{2 \cdot \text{IoU}}{1 + \text{IoU}}$, 两者数值不同但单调对应。

工程实务: 医学影像/分割比赛常用 Dice, 工业检测两者都用。


## 二值阈值分割与连通区域

## 2.1 二值阈值分割

最简单的二值分割方法: 用一个全局阈值 $T$:

$\text{mask}(x, y) = \begin{cases} 1 & \text{if } I(x, y) \geq T \\ 0 & \text{otherwise} \end{cases}$

工程实务: 全局阈值假设光照均匀, 不均匀场景需要局部自适应阈值 (Otsu, 自适应 Gaussian)。

## 2.2 阈值的选择

- **太低**: 噪声被当作前景, 假阳性多
- **太高**: 弱目标被丢掉, 假阴性多
- **经验起点**: 灰度图均值 / 中位数

Otsu 算法可以自动找最优阈值 (基于类间方差最大化), 工业场景标配。本关用固定阈值, Otsu 作为知识储备。

## 2.3 连通区域 (Connected Components)

二值分割后得到 0/1 mask, 但前景往往是**多个独立目标** (例如图像里有 3 个零件), 我们要数有多少个目标 = 多少个连通区域。

**连通**定义:
- **4-连通**: 上下左右相邻
- **8-连通**: 加上四个对角线相邻

算法 (1D 简化版): 给定 1D 二值序列, 数 1 的连续段个数 = 连通区域数。

**例**: [0, 1, 1, 0, 1, 0, 0, 1, 1, 1] 有 3 个连通区域 (索引 1-2, 4, 7-9)。

工程实务: 2D 用 BFS/DFS 或 union-find 找连通域, 1D 是简单线性扫描。

## 2.4 业务案例: 工业掩码连通分析

场景: 流水线产品图, 已知缺陷掩码 (二值), 数有几处缺陷:

流水线:
1. 灰度 + 滤波 (CV02-04 复习)
2. **二值阈值分割** (本关) 把缺陷区域设为 1
3. 形态学清理 (CV06 开闭运算复习) 去噪
4. **连通区域计数** (本关) 数缺陷个数
5. 决策: 缺陷 > 3 → 报废


## 评估指标公式与业务案例

## 3.1 Dice 系数公式 (1D 简化)

给定预测 mask $A$ 与真实 mask $B$ (都是 1D 二值序列, 同长度):

$|A \cap B| = \sum_i A_i \cdot B_i$ (两者都为 1 的像素数)
$|A| = \sum_i A_i$ (预测前景像素数)
$|B| = \sum_i B_i$ (真实前景像素数)

$\text{Dice} = \frac{2 |A \cap B|}{|A| + |B|}$

**特殊情况**: 都为全 0 (无前景), $|A| = |B| = 0$ 分母为 0, 约定 Dice = 1 (完美一致)。

**范围**: $[0, 1]$, 1 = 完美预测, 0 = 完全错。

## 3.2 Pixel Accuracy 公式

$\text{PA} = \frac{\sum_i [A_i = B_i]}{N}$

其中 $[A_i = B_i]$ 是指示函数 (1 if equal, else 0), $N$ 是总像素数。

工程实务: PA 总是值得算 (基线指标), 但不能单看 PA 判优劣, 必须配 Dice/IoU。

## 3.3 业务案例: 医学影像肿瘤分割

场景: CT 扫描图, 分割肿瘤区域 (前景 = 肿瘤, 背景 = 正常组织), 评估算法精度。

流水线:
1. CT 图灰度化 + 标准化 (复习 CV01-02)
2. **二值阈值分割** (本关) 或更复杂的 ML 模型
3. 形态学清理 (CV06 复习)
4. **Dice 系数** (本关) 与 ground truth 比较 → 评估精度
5. 多个病人取平均 Dice = 模型整体性能

经验: 医学影像 Dice ≥ 0.8 算"可临床用"。

## 3.4 工程口诀

- **分割是像素级**: 不要混淆与 BBox 检测
- **类别不平衡是分割的硬伤**: 必须用 Dice/IoU, 不能只看 PA
- **二值阈值看场景**: 光照均匀用 Otsu, 不均匀用自适应
- **连通域去小**: 阈值后小连通域常是噪声, 面积过滤
- **Dice 全 0 boundary 约定 = 1**: 不要写出 0/0 NaN

$v$,
        $v${"questions": [{"id": "q11-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv11.py 中的 4 个函数; 评测以 test_cv11.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_seg_basic$v$, $v$[0.1, 0.5, 0.9] thresh=0.5 → [0, 1, 1]$v$, false, $v$[0.1, 0.5, 0.9] thresh=0.5 → [0, 1, 1]$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_seg_at_threshold$v$, $v$边界 == thresh → 1$v$, false, $v$边界 == thresh → 1$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_seg_all_below$v$, $v$全部 < thresh → 全 0$v$, false, $v$全部 < thresh → 全 0$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_seg_all_above$v$, $v$全部 >= thresh → 全 1$v$, false, $v$全部 >= thresh → 全 1$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_seg_negative_values$v$, $v$[-0.1, -0.5, 0.5, 1.0] thresh=0.0 → [0, 0, 1, 1]$v$, false, $v$[-0.1, -0.5, 0.5, 1.0] thresh=0.0 → [0, 0, 1, 1]$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_seg_mixed_decimals$v$, $v$[0.49, 0.51, 0.5, 0.4] thresh=0.5 → [0, 1, 1, 0]$v$, false, $v$[0.49, 0.51, 0.5, 0.4] thresh=0.5 → [0, 1, 1, 0]$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_seg_single_above$v$, $v$[0.7] thresh=0.5 → [1] (boundary 单元素)$v$, false, $v$[0.7] thresh=0.5 → [1] (boundary 单元素)$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_seg_raises_on_empty$v$, $v$seg raises on empty$v$, false, $v$seg raises on empty$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_seg_raises_on_non_list$v$, $v$seg raises on non list$v$, false, $v$seg raises on non list$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_cc_no_ones$v$, $v$全 0 → 0$v$, false, $v$全 0 → 0$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_cc_all_ones$v$, $v$全 1 → 1 (一个段)$v$, false, $v$全 1 → 1 (一个段)$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_cc_two_segments$v$, $v$[1, 1, 0, 0, 1, 1] → 2 (zero-seg=1 不同, kills shape)$v$, false, $v$[1, 1, 0, 0, 1, 1] → 2 (zero-seg=1 不同, kills shape)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_cc_alternating$v$, $v$[1, 0, 1, 0, 1] → 3$v$, false, $v$[1, 0, 1, 0, 1] → 3$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_cc_start_with_one$v$, $v$[1, 1, 0, 1] → 2$v$, false, $v$[1, 1, 0, 1] → 2$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_cc_two_long$v$, $v$[1, 1, 1, 0, 1, 1] → 2 (zero-seg=1 不同, kills shape)$v$, false, $v$[1, 1, 1, 0, 1, 1] → 2 (zero-seg=1 不同, kills shape)$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_cc_single_one$v$, $v$[0, 0, 1, 0] → 1 (boundary 单 1)$v$, false, $v$[0, 0, 1, 0] → 1 (boundary 单 1)$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_cc_raises_on_invalid_value$v$, $v$cc raises on invalid value$v$, false, $v$cc raises on invalid value$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_cc_raises_on_non_list$v$, $v$cc raises on non list$v$, true, $v$cc raises on non list$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_dice_perfect$v$, $v$完全相同 → 1$v$, true, $v$完全相同 → 1$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_dice_disjoint$v$, $v$无交集 → 0$v$, true, $v$无交集 → 0$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_dice_partial$v$, $v$[1,1,1,0] vs [1,1,0,0]: A∩B=2, |A|=3, |B|=2, Dice=4/5=0.8$v$, true, $v$[1,1,1,0] vs [1,1,0,0]: A∩B=2, |A|=3, |B|=2, Dice=4/5=0.8$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_dice_one_pred_three_gt$v$, $v$[1,0,0,0] vs [1,1,1,0]: A∩B=1, |A|=1, |B|=3, Dice=2/4=0.5$v$, true, $v$[1,0,0,0] vs [1,1,1,0]: A∩B=1, |A|=1, |B|=3, Dice=2/4=0.5$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_dice_both_empty$v$, $v$两者全 0 → 1.0 约定$v$, true, $v$两者全 0 → 1.0 约定$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_dice_one_overlap_in_5$v$, $v$[1,1,0,1,0] vs [0,1,1,0,1]: A∩B=1, |A|=3, |B|=3, Dice=2/6=1/3$v$, true, $v$[1,1,0,1,0] vs [0,1,1,0,1]: A∩B=1, |A|=3, |B|=3, Dice=2/6=1/3$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_dice_raises_on_length_mismatch$v$, $v$dice raises on length mismatch$v$, true, $v$dice raises on length mismatch$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_dice_raises_on_non_list$v$, $v$dice raises on non list$v$, true, $v$dice raises on non list$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_pa_perfect$v$, $v$完全相同 → 1$v$, true, $v$完全相同 → 1$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_pa_all_wrong$v$, $v$全错 → 0$v$, true, $v$全错 → 0$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_pa_one_quarter$v$, $v$[1,1,1,0] vs [1,0,0,0]: 正确 [✓,✗,✗,✓] = 2/4 = 0.5 — 不, 实际 [1=1,1≠0,1≠0,0=0] = 2/4=0.5 改用: [1,1,1,1] vs [1,0,0,0]: 1/4 = 0.25 (1-PA = 0.75 不同)$v$, true, $v$[1,1,1,0] vs [1,0,0,0]: 正确 [✓,✗,✗,✓] = 2/4 = 0.5 — 不, 实际 [1=1,1≠0,1≠0,0=0] = 2/4=0.5 改用: [1,1,1,1] vs [1,0,0,0]: 1/4 = 0.25 (1-PA = 0.75 不同)$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_pa_three_of_four$v$, $v$[1,1,0,1] vs [1,1,1,1]: 3/4 = 0.75$v$, true, $v$[1,1,0,1] vs [1,1,1,1]: 3/4 = 0.75$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_pa_two_of_five$v$, $v$[1,1,1,1,1] vs [1,0,0,0,1]: 2/5 = 0.4$v$, true, $v$[1,1,1,1,1] vs [1,0,0,0,1]: 2/5 = 0.4$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_pa_imbalanced_class$v$, $v$所有背景预测对: [0,0,0,0,1] vs [0,0,0,0,0]: 4/5 = 0.8 (boundary 类别不平衡)$v$, true, $v$所有背景预测对: [0,0,0,0,1] vs [0,0,0,0,0]: 4/5 = 0.8 (boundary 类别不平衡)$v$, NULL, 32),
    ($v$tc_33$v$, $v$test_pa_raises_on_length_mismatch$v$, $v$pa raises on length mismatch$v$, true, $v$pa raises on length mismatch$v$, NULL, 33),
    ($v$tc_34$v$, $v$test_pa_raises_on_empty$v$, $v$pa raises on empty$v$, true, $v$pa raises on empty$v$, NULL, 34)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
