-- ============================================================
-- MJ8: 无监督学习: 降维
-- practice_id=7, order_in_practice=8
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$无监督学习: 降维$v$,
        'PRACTICE',
        8,
        $v$intermediate$v$,
        $v$## 为什么需要降维

## 1.1 维度灾难

高维数据在分析与建模时遇到三类困难, 统称"维度灾难":

- **距离失效**: 在高维空间 (d > 50), 样本间欧氏距离的方差会越来越小 — 几乎所有样本看起来都"差不多远", 距离度量失去判别力。这直接影响 K-Means、KNN 等基于距离的算法。
- **样本稀疏**: 维度每翻倍, 要保持同样密度需要的样本数指数级增长。300 维 + 1000 样本听起来不少, 实际密度极低, 模型学不到稳定模式。
- **过拟合风险**: 特征数 > 样本数时, OLS 与多数监督模型必过拟合。Ridge/Lasso 是缓解, 不是解决。

解决思路有两条: **特征筛选** (复习 MJ03 方差过滤) 与**特征压缩** (本关 PCA / t-SNE)。

## 1.2 PCA 的核心思想

Principal Component Analysis (PCA) 找一组**正交方向**, 使得数据在这些方向上的方差最大化保留。直觉:
- 第一主成分 = 数据"最长的伸展方向"
- 第二主成分 = 在第一主成分正交平面里"最长的伸展方向"
- ...

把数据投影到前 k 个主成分上, 就用 k 维数据近似表达原始 d 维数据 (k << d), 同时尽量少丢方差信息。


## PCA 的 3 步骨架

## 2.1 步 1: 中心化

对每列 (特征) 减去该列均值:

$\tilde{x}_{ij} = x_{ij} - \bar{x}_j$

中心化后的矩阵记为 $\tilde{X}$, 列均值变为 0。中心化是 PCA 的强制前提 — 没中心化, 协方差矩阵就不正确, 主成分方向会被均值偏置带歪。

## 2.2 步 2: 协方差矩阵

协方差矩阵 $C$ 是 $d \times d$ 对称矩阵:

$C = \frac{1}{N} \tilde{X}^T \tilde{X}$

$C_{jk}$ 表示第 $j$ 与第 $k$ 个特征的协方差。对角线 $C_{jj}$ 是第 $j$ 个特征的方差。注意: 这里用 $N$ 作分母 (population covariance), 与 sklearn 默认一致。

关键性质: 协方差矩阵是**对称半正定**, 这保证特征值都是非负实数 — 对应方差物理意义。

## 2.3 步 3: 特征值分解

对 $C$ 做特征值分解, 得到 $d$ 对 (特征值, 特征向量):

$C \mathbf{v}_i = \lambda_i \mathbf{v}_i$

- 特征向量 $\mathbf{v}_i$ 是主成分的方向 (单位向量, 互相正交)
- 特征值 $\lambda_i$ 是该方向上的方差大小
- 按 $\lambda$ 从大到小排序, 取前 $k$ 个 $\mathbf{v}_i$ 组成投影矩阵 $W$

投影: 新坐标 $\tilde{X} W$, 形状从 $N \times d$ 变为 $N \times k$。

## 2.4 解释方差比例

第 $i$ 个主成分的解释方差比例:

$r_i = \frac{\lambda_i}{\sum_j \lambda_j}$

累计前 $k$ 个的比例和反映了"用 k 维近似原数据保留多少方差"。工程经验: 选 $k$ 让累计方差 $\geq 95\%$ 是常见标准。


## 示例与限制

## 3.1 走通一个最小例子

数据: $X = \{(1,2), (2,4), (3,6), (4,8), (5,10)\}$ — 显然 $y = 2x$ 完美线性关系。

中心化: $\bar{x}_1 = 3, \bar{x}_2 = 6$, 中心化矩阵:
$\tilde{X} = [(-2,-4), (-1,-2), (0,0), (1,2), (2,4)]$

协方差矩阵:
$C = \begin{bmatrix} 2 & 4 \\ 4 & 8 \end{bmatrix}$

特征值分解 (det $(C-\lambda I)=0$): $\lambda(\lambda - 10) = 0$, 得 $\lambda_1 = 10, \lambda_2 = 0$。

解释方差比例: $r = (10/10, 0/10) = (1.0, 0.0)$ — PC1 完美保留所有方差, PC2 没贡献。这吻合数据本质上是 1 维。

工程提醒: 真实数据不会这么干净, 但若 PC1 + PC2 的解释方差比例 $\geq 95\%$, 通常说明数据本质维度不超过 2, 可以可视化。

## 3.2 PCA 的局限

- **只捕捉线性关系**: 数据若是流形 (例: 螺旋) 嵌入高维, PCA 会把它"压扁"丢信息
- **对量纲敏感**: 不同特征量纲差异大时必须先标准化, 否则高量纲特征主导主成分
- **可解释性下降**: 主成分是原特征的线性组合, 业务上"PC1 = 0.7×身高 - 0.3×体重 + ..." 不像原特征那样直观

## 3.3 t-SNE 与 PCA 的区别

t-SNE (t-Distributed Stochastic Neighbor Embedding) 是另一类降维方法, 与 PCA 互补:

- PCA 保**全局结构** (大尺度方向), 适合压缩 + 重建
- t-SNE 保**局部结构** (邻居关系), 适合可视化但不能用于压缩
- PCA 可逆 (能从 PC 空间近似重建原始), t-SNE 不可逆

实务工作流: 先 PCA 降到 30-50 维 (去噪), 再 t-SNE 到 2 维 (可视化)。


## 业务案例: 人脸表征压缩

## 4.1 场景

智能门禁系统每张人脸 224×224 灰度像素 = 50176 维原始特征。直接做相似度比对极慢, 想压缩到 100 维做"人脸指纹"。

## 4.2 PCA 流程

**步 1**: 收集 10000 张人脸样本, 拉直成 10000 × 50176 矩阵。

**步 2**: 中心化 (减"平均脸") → 协方差矩阵 50176 × 50176 (内存爆炸)。实际工程用 SVD 分解避开显式协方差矩阵, 这是 sklearn 内部做的事。

**步 3**: 取前 100 个主成分 (累计解释方差 ≈ 92%)。每张脸压缩成 100 维向量。

**步 4**: 上线后, 比对两张脸用 100 维向量的欧氏距离, 阈值 < T 判定为同一人。

## 4.3 业务收益

- 存储: 50176 → 100, 每张脸节省 99.8% 空间
- 查询: O(50176) → O(100), 比对速度提升 500 倍
- 鲁棒: 主成分捕捉了"光照、姿态"等系统性变化, 比对原始像素更稳

## 4.4 PCA 不是万能

重要警告: PCA 是无监督方法, **不知道下游任务是什么**。如果下游是分类 (例: 性别识别), PCA 选的主成分可能不是最有判别力的方向 — 因为 PCA 只看方差不看类别。监督场景下 LDA (Linear Discriminant Analysis) 等监督降维更合适。

工程口诀: **降维前先问下游用途**。无标签纯压缩用 PCA; 有标签且看分类边界用监督降维; 只为可视化用 t-SNE。

$v$,
        $v${"questions": [{"id": "q08-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj08.py 中的 4 个函数; 评测以 test_mj08.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_cd_3x2_known_mean$v$, $v$X=[[1,2],[3,4],[5,6]] mean=[3,4] centered=[[-2,-2],[0,0],[2,2]]$v$, false, $v$X=[[1,2],[3,4],[5,6]] mean=[3,4] centered=[[-2,-2],[0,0],[2,2]]$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_cd_1d_4_samples$v$, $v$X=[[1],[2],[3],[4]] mean=[2.5] centered=[[-1.5],[-0.5],[0.5],[1.5]]$v$, false, $v$X=[[1],[2],[3],[4]] mean=[2.5] centered=[[-1.5],[-0.5],[0.5],[1.5]]$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_cd_3d$v$, $v$X=[[1,2,3],[4,5,6]] mean=[2.5,3.5,4.5]$v$, false, $v$X=[[1,2,3],[4,5,6]] mean=[2.5,3.5,4.5]$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_cd_constant_data$v$, $v$边界: X=[[5,5],[5,5]] mean=[5,5] centered=[[0,0],[0,0]]$v$, false, $v$边界: X=[[5,5],[5,5]] mean=[5,5] centered=[[0,0],[0,0]]$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_cd_single_sample$v$, $v$边界: X=[[10,20]] 单样本 → mean=[10,20], centered=[[0,0]]$v$, false, $v$边界: X=[[10,20]] 单样本 → mean=[10,20], centered=[[0,0]]$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_cd_raises_on_empty$v$, $v$cd raises on empty$v$, false, $v$cd raises on empty$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_cd_raises_on_inconsistent_rows$v$, $v$cd raises on inconsistent rows$v$, false, $v$cd raises on inconsistent rows$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_cd_raises_on_non_list$v$, $v$cd raises on non list$v$, false, $v$cd raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_cov_y_2x$v$, $v$中心化后 [[-2,-4],[-1,-2],[0,0],[1,2],[2,4]] → cov=[[2,4],[4,8]]$v$, false, $v$中心化后 [[-2,-4],[-1,-2],[0,0],[1,2],[2,4]] → cov=[[2,4],[4,8]]$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_cov_diagonal$v$, $v$中心化 [[1,0],[-1,0]] → cov=[[1,0],[0,0]]$v$, false, $v$中心化 [[1,0],[-1,0]] → cov=[[1,0],[0,0]]$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_cov_3d$v$, $v$中心化 [[1,1,1],[-1,-1,-1]] → cov=[[1,1,1],[1,1,1],[1,1,1]]$v$, false, $v$中心化 [[1,1,1],[-1,-1,-1]] → cov=[[1,1,1],[1,1,1],[1,1,1]]$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_cov_identity_data$v$, $v$中心化 [[1,0],[0,1],[-1,0],[0,-1]] → cov 接近 [[0.5,0],[0,0.5]]$v$, false, $v$中心化 [[1,0],[0,1],[-1,0],[0,-1]] → cov 接近 [[0.5,0],[0,0.5]]$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_cov_anti_correlated$v$, $v$[[1,-1],[-1,1]] → cov=[[1,-1],[-1,1]]$v$, false, $v$[[1,-1],[-1,1]] → cov=[[1,-1],[-1,1]]$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_cov_raises_on_empty$v$, $v$cov raises on empty$v$, false, $v$cov raises on empty$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_cov_raises_on_inconsistent_rows$v$, $v$cov raises on inconsistent rows$v$, false, $v$cov raises on inconsistent rows$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_cov_raises_on_non_list$v$, $v$cov raises on non list$v$, false, $v$cov raises on non list$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_pt_project_to_first_axis$v$, $v$投影到 x 轴: components=[[1,0]], X=[[1,2],[3,4]] → [[1],[3]] (k=1 严格)$v$, true, $v$投影到 x 轴: components=[[1,0]], X=[[1,2],[3,4]] → [[1],[3]] (k=1 严格)$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_pt_project_to_y_axis$v$, $v$投影到 y 轴: components=[[0,1]], X=[[1,2],[3,4]] → [[2],[4]] (k=1 严格)$v$, true, $v$投影到 y 轴: components=[[0,1]], X=[[1,2],[3,4]] → [[2],[4]] (k=1 严格)$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_pt_project_diagonal$v$, $v$对角方向: X=[[1,2]], components=[[1/sqrt(2), 1/sqrt(2)]] → [[3/sqrt(2)]]$v$, true, $v$对角方向: X=[[1,2]], components=[[1/sqrt(2), 1/sqrt(2)]] → [[3/sqrt(2)]]$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_pt_two_components_3d$v$, $v$X=[[1,2,3]], components=[[1,0,0],[0,1,0]] → [[1, 2]] (k=2 严格)$v$, true, $v$X=[[1,2,3]], components=[[1,0,0],[0,1,0]] → [[1, 2]] (k=2 严格)$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_pt_zero_input$v$, $v$边界: X=[[0,0]] components=[[1,0]] → [[0]] (k=1 严格)$v$, true, $v$边界: X=[[0,0]] components=[[1,0]] → [[0]] (k=1 严格)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_pt_raises_on_empty_X$v$, $v$pt raises on empty X$v$, true, $v$pt raises on empty X$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_pt_raises_on_dim_mismatch$v$, $v$pt raises on dim mismatch$v$, true, $v$pt raises on dim mismatch$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_pt_raises_on_non_list$v$, $v$pt raises on non list$v$, true, $v$pt raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_evr_y_2x_perfect$v$, $v$eigvals=[10, 0] → [1.0, 0.0]$v$, true, $v$eigvals=[10, 0] → [1.0, 0.0]$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_evr_uniform$v$, $v$eigvals=[1,1,1,1] → [0.25]*4$v$, true, $v$eigvals=[1,1,1,1] → [0.25]*4$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_evr_proportional$v$, $v$eigvals=[2, 4, 6, 8] → [0.1, 0.2, 0.3, 0.4]$v$, true, $v$eigvals=[2, 4, 6, 8] → [0.1, 0.2, 0.3, 0.4]$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_evr_typical_pca$v$, $v$eigvals=[50, 30, 15, 5] → [0.5, 0.3, 0.15, 0.05]$v$, true, $v$eigvals=[50, 30, 15, 5] → [0.5, 0.3, 0.15, 0.05]$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_evr_decimals$v$, $v$eigvals=[0.5, 0.5] → [0.5, 0.5]$v$, true, $v$eigvals=[0.5, 0.5] → [0.5, 0.5]$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_evr_raises_on_all_zero$v$, $v$evr raises on all zero$v$, true, $v$evr raises on all zero$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_evr_raises_on_negative$v$, $v$evr raises on negative$v$, true, $v$evr raises on negative$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_evr_raises_on_non_list$v$, $v$evr raises on non list$v$, true, $v$evr raises on non list$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
