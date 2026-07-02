-- CV6: 形态学操作
-- practice_id=9, order_in_practice=6, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        9,
        $v$形态学操作$v$,
        'PRACTICE',
        6,
        $v$intermediate$v$,
        $v$## 二值图像与形态学动机

## 1.1 二值图像

二值图像 (binary image) 只有两个像素值, 通常 0 (黑/背景) 与 1 (白/前景)。在工业检测/医学影像中, 经过阈值化的图像就是二值图: 缺陷像素 = 1, 正常像素 = 0。

二值图像看起来简单, 但常有问题:
- **小噪点**: 单个像素的孤立白点, 不是真正的缺陷
- **细小连接**: 两个本不该相连的区域被一两个像素连起来
- **小孔洞**: 缺陷区域中间有小黑洞, 不是真孔
- **不光滑边界**: 锯齿状边缘, 影响测量精度

形态学操作 (Morphological Operations) 就是解决这些问题的工具集。

## 1.2 结构元 (Structuring Element)

形态学的核心是**结构元** (SE), 也叫"核"或"探针"。常见 3×3 结构元:

$\text{Square (方形, 全 1)} = \begin{pmatrix} 1 & 1 & 1 \\ 1 & 1 & 1 \\ 1 & 1 & 1 \end{pmatrix}$
$\quad \text{Cross (十字, 中心+四邻)} = \begin{pmatrix} 0 & 1 & 0 \\ 1 & 1 & 1 \\ 0 & 1 & 0 \end{pmatrix}$

方形 SE 考虑 8 邻域, 十字 SE 只考虑 4 邻域。十字保留更多细节, 方形效果更"厚实"。

## 1.3 SE 的中心 (anchor)

结构元有一个**中心点 (anchor)**, 形态学操作时, 把 SE 的中心对齐到当前像素位置, SE 的其他位置就对应当前像素的邻域。3×3 SE 的中心通常在 (1, 1) 即矩阵的中间位置。

工程实务: OpenCV 的 cv2.getStructuringElement 默认 anchor 在中心, 一般不动。

## 1.4 形态学的两类应用

- **几何整形**: 平滑边界、连接断裂、填补孔洞 — 主要是开/闭运算
- **结构提取**: 边界提取 (原图 - 腐蚀)、骨架化、距离变换 — 进阶应用

本关聚焦四个基础操作 (腐蚀/膨胀/开/闭), 结构提取作为知识储备。


## 腐蚀与膨胀

## 2.1 腐蚀 (Erosion)

定义: 中心像素位置上, **结构元覆盖的所有 SE=1 位置, 全部对应输入 = 1, 输出 = 1; 否则输出 = 0**。

用 AND 表达: $E(p) = \text{AND}_{q \in SE} I(p+q)$ (只对 SE=1 的位置算 AND)

效果: 前景区域**变小** (被边界"啃掉"一圈)。可以:
- **去除小白噪点**: 单像素的孤立 1 被腐蚀成 0
- **断开细连接**: 两个区域间一两个像素的连接消失
- **代价**: 真正的缺陷区域也会缩小, 边界丢失细节

## 2.2 膨胀 (Dilation)

定义: 中心像素位置上, **结构元覆盖的任一 SE=1 位置, 对应输入 = 1, 输出 = 1; 全部 = 0 才输出 0**。

用 OR 表达: $D(p) = \text{OR}_{q \in SE} I(p+q)$ (只对 SE=1 的位置算 OR)

效果: 前景区域**变大** (向外"长一圈")。可以:
- **填补小黑洞**: 区域中间的小孔被填上
- **连接近距离区域**: 几个像素差距的两个区域连成一块
- **代价**: 区域边界向外扩, 细节模糊

## 2.3 对偶性

腐蚀与膨胀是数学**对偶**操作: 对图像取反 (1↔0) 再做对偶操作再取反, 等价于原操作。即 $\text{Erode}(I) = \neg \text{Dilate}(\neg I)$。

工程意义: 写代码时只实现一个操作, 另一个用对偶式即可。


## 开运算 / 闭运算 / 业务案例

## 3.1 开运算 (Opening)

定义: 先腐蚀, 再膨胀。$\text{Open}(I) = \text{Dilate}(\text{Erode}(I))$

效果:
- 腐蚀阶段: 去掉小白噪点
- 膨胀阶段: 把保留的真区域恢复到原大小 (近似)

用途: **去除小尺寸的前景噪声**, 保留大区域的形状。

## 3.2 闭运算 (Closing)

定义: 先膨胀, 再腐蚀。$\text{Close}(I) = \text{Erode}(\text{Dilate}(I))$

效果:
- 膨胀阶段: 填上小黑洞
- 腐蚀阶段: 把外扩的边界缩回原大小 (近似)

用途: **填补小孔洞、连接细缝隙**, 保留大区域的形状。

## 3.3 业务案例: 工业掩码清理

场景: 工业流水线视觉检测, 已经通过阈值化得到"疑似缺陷"二值掩码, 但掩码有噪点和孔洞, 需要清理。

清理流水线:
1. **开运算 (3×3 方形 SE)**: 去掉孤立的传感器噪点 (单像素白点)
2. **闭运算 (3×3 方形 SE)**: 填补真缺陷区域中的小孔洞
3. 连通区域分析 → 测量缺陷面积/形状

经验:
- **先开后闭**: 噪点去掉后再填洞, 不让噪点扩散到周围
- **SE 大小 3×3 起步**: 太大会丢真缺陷, 太小没效果
- **十字 vs 方形**: 十字保边更好, 方形效果更猛, 工业默认方形

## 3.4 工程口诀

- **腐蚀 = 缩**: 去白噪点、断细连接
- **膨胀 = 长**: 填黑洞、连近区域
- **开 = 去前景噪**: erosion + dilation
- **闭 = 填前景洞**: dilation + erosion
- **形态学是二值后处理标配**: 阈值后必有形态学清理
- **结构元小起步**: 3×3 通常够, 5×5 是上限

形态学操作主要对二值图像有效。灰度图也可以做形态学 (灰度腐蚀: 邻域取最小值; 灰度膨胀: 邻域取最大值), 但工程中以二值为主。

最后一个常见错误: **SE 大小要与图像尺寸匹配**。对 4K 分辨率的图像用 3×3 SE 几乎没效果, 应该用 5×5 或 7×7。对小图 (224×224) 用 5×5 已经很激进。

$v$,
        $v${"questions": [{"id": "q06-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_cv06.py 中的 4 个函数; 评测以 test_cv06.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_erode_1d_one_zero_left$v$, $v$[0,1,1,1,1] k=3 → [0,1,1]$v$, false, $v$[0,1,1,1,1] k=3 → [0,1,1]$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_erode_1d_one_zero_right$v$, $v$[1,1,1,1,0] k=3 → [1,1,0]$v$, false, $v$[1,1,1,1,0] k=3 → [1,1,0]$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_erode_1d_long_mixed$v$, $v$[1,1,1,0,1,1,1] k=3 → [1,0,0,0,1]$v$, false, $v$[1,1,1,0,1,1,1] k=3 → [1,0,0,0,1]$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_erode_1d_partial_5$v$, $v$[1,1,1,1,0,1] k=3 → [1,1,0,0]$v$, false, $v$[1,1,1,1,0,1] k=3 → [1,1,0,0]$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_erode_1d_all_zeros$v$, $v$全 0 → 全 0 (boundary)$v$, false, $v$全 0 → 全 0 (boundary)$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_erode_1d_kernel_5_mixed$v$, $v$[1,0,1,1,1,1,1] k=5 → [0,0,1]$v$, false, $v$[1,0,1,1,1,1,1] k=5 → [0,0,1]$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_erode_1d_raises_on_even_kernel$v$, $v$erode 1d raises on even kernel$v$, false, $v$erode 1d raises on even kernel$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_erode_1d_raises_on_invalid_value$v$, $v$erode 1d raises on invalid value$v$, false, $v$erode 1d raises on invalid value$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_erode_1d_raises_on_non_list$v$, $v$erode 1d raises on non list$v$, false, $v$erode 1d raises on non list$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_dilate_1d_one_one_left$v$, $v$[1,0,0,0,0] k=3 → [1,0,0]$v$, false, $v$[1,0,0,0,0] k=3 → [1,0,0]$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_dilate_1d_one_one_right$v$, $v$[0,0,0,0,1] k=3 → [0,0,1]$v$, false, $v$[0,0,0,0,1] k=3 → [0,0,1]$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_dilate_1d_long_sparse$v$, $v$[0,0,0,1,0,0,0] k=3 → [0,1,1,1,0]$v$, false, $v$[0,0,0,1,0,0,0] k=3 → [0,1,1,1,0]$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_dilate_1d_partial_5$v$, $v$[0,0,1,0,0,1] k=3 → [1,1,1,1]$v$, false, $v$[0,0,1,0,0,1] k=3 → [1,1,1,1]$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_dilate_1d_all_zeros$v$, $v$全 0 → 全 0 (boundary)$v$, false, $v$全 0 → 全 0 (boundary)$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_dilate_1d_kernel_5_mixed$v$, $v$[0,0,1,0,0,0,1] k=5 → [1,1,1]$v$, false, $v$[0,0,1,0,0,0,1] k=5 → [1,1,1]$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_dilate_1d_raises_on_even_kernel$v$, $v$dilate 1d raises on even kernel$v$, true, $v$dilate 1d raises on even kernel$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_dilate_1d_raises_on_invalid_value$v$, $v$dilate 1d raises on invalid value$v$, true, $v$dilate 1d raises on invalid value$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_dilate_1d_raises_on_non_list$v$, $v$dilate 1d raises on non list$v$, true, $v$dilate 1d raises on non list$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_order_erosion$v$, $v$order erosion$v$, true, $v$order erosion$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_order_dilation$v$, $v$order dilation$v$, true, $v$order dilation$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_order_opening$v$, $v$开 = 先腐蚀再膨胀$v$, true, $v$开 = 先腐蚀再膨胀$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_order_closing$v$, $v$闭 = 先膨胀再腐蚀$v$, true, $v$闭 = 先膨胀再腐蚀$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_order_raises_on_unknown$v$, $v$order raises on unknown$v$, true, $v$order raises on unknown$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_order_raises_on_empty$v$, $v$空字符串边界$v$, true, $v$空字符串边界$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_order_raises_on_non_string$v$, $v$order raises on non string$v$, true, $v$order raises on non string$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_cross_shape$v$, $v$cross shape$v$, true, $v$cross shape$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_cross_full_match$v$, $v$完整十字: [[0,1,0],[1,1,1],[0,1,0]]$v$, true, $v$完整十字: [[0,1,0],[1,1,1],[0,1,0]]$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_cross_corners_zero$v$, $v$4 角必 0$v$, true, $v$4 角必 0$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_cross_center_one$v$, $v$中心必 1$v$, true, $v$中心必 1$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_cross_edges_one$v$, $v$4 个边中点必 1$v$, true, $v$4 个边中点必 1$v$, NULL, 30)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
