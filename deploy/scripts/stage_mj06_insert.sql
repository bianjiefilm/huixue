-- ============================================================
-- MJ6: 监督学习: 回归
-- practice_id=7, order_in_practice=6
-- v2 (4-attack + 5-redline validated)
-- ============================================================

BEGIN;

WITH new_task AS (
    INSERT INTO tasks (
        practice_id, title, task_type, order_in_practice, difficulty,
        handbook_markdown, question_data, created_at, updated_at
    ) VALUES (
        7,
        $v$监督学习: 回归$v$,
        'PRACTICE',
        6,
        $v$intermediate$v$,
        $v$## 线性回归与最小二乘

## 1.1 回归任务的位置

回归 (Regression) 是监督学习的另一支柱 — 与分类的区别在于**目标变量是连续数值**, 不是离散类别。比如:
- 房价预测 (千元 ~ 千万)
- 销量预测 (单位/月)
- 股价预测 (元)
- 医疗指标 (血压/血糖)

回归的预测函数形态多样, 最简单也最重要的是**线性回归**:

$\hat{y} = w_1 x_1 + w_2 x_2 + \cdots + w_d x_d + b$

其中 $w_i$ 是各特征的权重, $b$ 是偏置 (截距)。线性回归不只是入门工具 — 在金融、计量经济、医学统计场景, 因其**可解释性**和**统计性质明确**, 仍然是首选模型。

## 1.2 最小二乘 (OLS)

给定 N 个样本 $(\mathbf{x}_i, y_i)$, 我们要找让"预测平均偏离真值最少"的权重。最小二乘选择**平方误差和**作为目标:

$\text{Loss}(w, b) = \sum_{i=1}^{N} (y_i - \hat{y}_i)^2$

为什么用平方而不是绝对值?
- 平方对大误差惩罚更重 (相对线性)
- 平方损失关于参数处处可导, 优化数学性质好
- 平方损失对应的概率假设 (高斯噪声) 在工程上常成立


## 正规方程闭式解

## 2.1 矩阵形式

把全部样本堆成矩阵 $X$ (形状 $N \times d$, 每行一个样本) 与向量 $\mathbf{y}$ (长度 $N$), 平方误差损失等价于:

$\text{Loss}(\mathbf{w}) = (\mathbf{y} - X\mathbf{w})^T (\mathbf{y} - X\mathbf{w})$

(这里把 $b$ 吸收进 $\mathbf{w}$, 给 $X$ 多加一列全 1 即可。)

## 2.2 闭式解推导

对 $\mathbf{w}$ 求导并令导数为 0:

$\frac{\partial \text{Loss}}{\partial \mathbf{w}} = -2 X^T (\mathbf{y} - X\mathbf{w}) = 0$

$X^T X \mathbf{w} = X^T \mathbf{y}$

$\mathbf{w}^* = (X^T X)^{-1} X^T \mathbf{y}$

这就是**正规方程** (normal equation) — 线性回归的闭式解, 无需迭代优化。

## 2.3 正规方程的限制

- $X^T X$ 必须可逆: 当特征间高度共线 (multicollinearity) 时奇异, 需要先做特征工程或加正则化
- 计算复杂度 $O(d^3)$: 特征极多 (d > 10000) 时变慢, 工程上改用迭代法 (梯度下降)
- 数值精度: 大规模实数据建议用 SVD 分解避免矩阵求逆的数值不稳

工程实务: 中小数据集用正规方程一行搞定; 大数据集用梯度下降; 完全不可逆/严重共线时加正则化项 (下一节)。


## Ridge 与 Lasso 正则化

## 3.1 过拟合的源头

OLS 没有任何对权重大小的限制, 当特征多于样本或特征间高度相关时, 会学出极大幅度的权重 — 一个上下浮动 ±1000 的特征系数会让模型对训练集过度敏感, 对新样本表现差。这就是回归的过拟合。

正则化的思路: 在 OLS 损失上**加一个惩罚项**, 限制权重总幅度。

## 3.2 Ridge (L2 正则化)

$\text{Loss}_{ridge}(\mathbf{w}) = (\mathbf{y} - X\mathbf{w})^T (\mathbf{y} - X\mathbf{w}) + \alpha \sum_{j} w_j^2$

闭式解: $\mathbf{w}^* = (X^T X + \alpha I)^{-1} X^T \mathbf{y}$

L2 惩罚的特点是**权重收缩到接近 0 但不会精确为 0**。$\alpha$ 越大, 收缩越强。Ridge 适合保留所有特征但希望它们影响均匀的场景。

## 3.3 Lasso (L1 正则化)

$\text{Loss}_{lasso}(\mathbf{w}) = (\mathbf{y} - X\mathbf{w})^T (\mathbf{y} - X\mathbf{w}) + \alpha \sum_{j} |w_j|$

L1 惩罚没有闭式解, 需要迭代优化。它的特点是**会把不重要的特征权重精确压到 0**, 实现自动特征选择。Lasso 适合**怀疑只有少量特征真正重要**的高维场景。

## 3.4 三者的取舍口诀

| 方法 | 何时用 |
|------|--------|
| OLS (无正则) | 特征数 << 样本数, 不担心共线 |
| Ridge | 特征间共线; 想保留所有特征做收缩 |
| Lasso | 高维; 怀疑大部分特征是噪声; 要稀疏解 |
| ElasticNet (L1+L2) | 想要 Lasso 的稀疏 + Ridge 的稳定 |


## 评估指标与房价业务案例

## 4.1 MSE 与 MAE

$\text{MSE} = \frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2$

$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} |y_i - \hat{y}_i|$

MSE 对大误差惩罚重 (一个偏差 10 的样本贡献 100); MAE 一视同仁 (贡献 10)。当数据有明显异常值时, MAE 更鲁棒; 不希望大偏差出现的场景 (医疗剂量预测), 用 MSE 警示。

## 4.2 R² 决定系数

$R^2 = 1 - \frac{\sum_i (y_i - \hat{y}_i)^2}{\sum_i (y_i - \bar{y})^2}$

分子是模型剩余的误差平方和 (SS_res), 分母是只用均值预测的误差 (SS_tot)。直觉:
- $R^2 = 1$: 模型完美拟合
- $R^2 = 0$: 模型表现等同于"永远预测均值"的基线
- $R^2 < 0$: 模型还不如基线 — 这是 v1 课程容易忽略的关键事实, **R² 可以是负数**

关键陷阱: 评测器若只验证 $R^2 \geq 0$, 任何返回 0.5 的占位实现都能通过。正确的评测必须用已知数据手算 R² 数值精确断言。

## 4.3 业务案例: 房价预测

房产中介接到任务: 用历史成交记录预测新房挂牌价。数据 5000 条, 特征 12 个 (面积/楼层/朝向/学区/装修/年限/...). 走完一遍回归全流程:

**步 1 EDA**: 房价分布右偏 (均值 ≈ 800 万, 中位数 ≈ 600 万), 有少数千万级豪宅。考虑对房价取对数让分布近似对称。

**步 2 预处理**: 分类特征 (朝向/学区) 编码; 数值特征标准化 (复习 MJ03)。

**步 3 模型对比**: OLS 训练 R² = 0.72; 加 Ridge (α=1.0) R² = 0.71 (略降但更稳); 加 Lasso (α=0.5) R² = 0.69 同时把"小区距离地铁站米数 < 50"等弱特征压到 0。

**步 4 评估**: 测试集 MSE=4500 (单位百万²), MAE=42 (百万)。业务方反馈 MAE 42 万的平均偏差对千万级房产可接受, 但需要看 P90 (90 分位偏差) — 这是回归在业务上更有用的指标。

**步 5 上线**: 对豪宅 (>2000 万) 单独训一个模型, 因为它们的价格驱动因素不同 (品牌/稀缺) 与普通住宅 (面积/学区) 不一样。

## 4.4 核心提醒

回归虽然简单, 业务上有 3 个常见错误:
- **盲目追 R²**: R²=0.95 的模型可能 MAE 远大于 R²=0.85 的, 业务上后者更有用
- **没看残差分布**: 平均 MAE 30 万但 5% 样本偏差 500 万, 这种"长尾失败"才是上线灾难
- **没考虑标签变换**: 房价/销量/收入这类右偏数据先 log, 模型表现往往大幅提升

$v$,
        $v${"questions": [{"id": "q06-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_mj06.py 中的 4 个函数; 评测以 test_mj06.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_mse_textbook$v$, $v$[3,-0.5,2,7], [2.5,0,2,8] → 0.375$v$, false, $v$[3,-0.5,2,7], [2.5,0,2,8] → 0.375$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_mse_perfect$v$, $v$完美预测 → 0.0$v$, false, $v$完美预测 → 0.0$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_mse_large$v$, $v$[10,20], [0,0] → (100+400)/2 = 250$v$, false, $v$[10,20], [0,0] → (100+400)/2 = 250$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_mse_doubled$v$, $v$[1,2,3], [2,4,6] → (1+4+9)/3 = 14/3$v$, false, $v$[1,2,3], [2,4,6] → (1+4+9)/3 = 14/3$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_mse_half_off$v$, $v$[5,5,5,5], [4,5,5,4] → (1+0+0+1)/4 = 0.5$v$, false, $v$[5,5,5,5], [4,5,5,4] → (1+0+0+1)/4 = 0.5$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_mse_raises_on_empty$v$, $v$mse raises on empty$v$, false, $v$mse raises on empty$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_mse_raises_on_length_mismatch$v$, $v$mse raises on length mismatch$v$, false, $v$mse raises on length mismatch$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_mse_raises_on_non_list$v$, $v$mse raises on non list$v$, false, $v$mse raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_r2_perfect$v$, $v$完美 → 1.0$v$, false, $v$完美 → 1.0$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_r2_096$v$, $v$y=[10,20,30,40], y_pred=[12,18,32,38] → SS_res=16, SS_tot=500, R²=0.968$v$, false, $v$y=[10,20,30,40], y_pred=[12,18,32,38] → SS_res=16, SS_tot=500, R²=0.968$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_r2_negative$v$, $v$y=[1,2,3], y_pred=[3,3,3] → SS_res=5, SS_tot=2, R²=-1.5 (负, v1 漏)$v$, false, $v$y=[1,2,3], y_pred=[3,3,3] → SS_res=5, SS_tot=2, R²=-1.5 (负, v1 漏)$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_r2_080$v$, $v$y=[2,4,6,8], y_pred=[3,5,7,9] (恒偏 1) → SS_res=4, SS_tot=20, R²=0.8$v$, false, $v$y=[2,4,6,8], y_pred=[3,5,7,9] (恒偏 1) → SS_res=4, SS_tot=20, R²=0.8$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_r2_098$v$, $v$y=[1,2,3,4,5], y_pred=[1.1,2.1,2.9,4.2,4.8] → R²=0.989$v$, false, $v$y=[1,2,3,4,5], y_pred=[1.1,2.1,2.9,4.2,4.8] → R²=0.989$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_r2_raises_on_zero_variance$v$, $v$y_true 全相同 → SS_tot=0, ValueError$v$, false, $v$y_true 全相同 → SS_tot=0, ValueError$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_r2_raises_on_empty$v$, $v$r2 raises on empty$v$, false, $v$r2 raises on empty$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_r2_raises_on_non_list$v$, $v$r2 raises on non list$v$, false, $v$r2 raises on non list$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_lp_textbook$v$, $v$X=[[1,2],[3,4]], w=[0.5,-0.3], b=0.1 → [0.0, 0.4]$v$, true, $v$X=[[1,2],[3,4]], w=[0.5,-0.3], b=0.1 → [0.0, 0.4]$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_lp_simple_doubling$v$, $v$X=[[1],[2],[3]], w=[2.0], b=0 → [2,4,6]$v$, true, $v$X=[[1],[2],[3]], w=[2.0], b=0 → [2,4,6]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_lp_three_features$v$, $v$X=[[1,1,1]], w=[1,1,1], b=0 → [3]$v$, true, $v$X=[[1,1,1]], w=[1,1,1], b=0 → [3]$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_lp_only_bias$v$, $v$X=[[0,0],[0,0]], w=[1,2], b=5 → [5,5]$v$, true, $v$X=[[0,0],[0,0]], w=[1,2], b=5 → [5,5]$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_lp_negative_weights$v$, $v$X=[[10]], w=[-2], b=3 → [-17]$v$, true, $v$X=[[10]], w=[-2], b=3 → [-17]$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_lp_raises_on_empty$v$, $v$lp raises on empty$v$, true, $v$lp raises on empty$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_lp_raises_on_dim_mismatch$v$, $v$X 行宽与 weights 长度不一致$v$, true, $v$X 行宽与 weights 长度不一致$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_lp_raises_on_non_list$v$, $v$lp raises on non list$v$, true, $v$lp raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_ne_y_equals_x$v$, $v$X=[[1,1],[1,2],[1,3],[1,4]] y=[1,2,3,4] (intercept+slope) → w=[0,1]$v$, true, $v$X=[[1,1],[1,2],[1,3],[1,4]] y=[1,2,3,4] (intercept+slope) → w=[0,1]$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_ne_y_2plus_x$v$, $v$X=[[1,0],[1,1],[1,2]] y=[2,3,4] → w=[2,1]$v$, true, $v$X=[[1,0],[1,1],[1,2]] y=[2,3,4] → w=[2,1]$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_ne_y_1plus_2x$v$, $v$X=[[1,1],[1,2],[1,3]] y=[3,5,7] → w=[1,2]$v$, true, $v$X=[[1,1],[1,2],[1,3]] y=[3,5,7] → w=[1,2]$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_ne_two_features$v$, $v$X=[[1,1,2],[1,2,4],[1,3,6],[1,4,8]] y = 1 + 0*x1 + 0.5*x2 → w=[1,0,0.5] 第 3 特征是第 2 特征的 2 倍 (共线), 但因为我们设计 y 也对应正确解就能解出唯一权重 — 实际上 X^T X 是奇异的, 这种共线场景在数值上会失败. 改用独立两特征: x1=[1,2,3,4] x2=[2,1,4,3] (不共线), y =$v$, true, $v$X=[[1,1,2],[1,2,4],[1,3,6],[1,4,8]] y = 1 + 0*x1 + 0.5*x2 → w=[1,0,0.5] 第 3 特征是第 2 特征的 2 倍 (共线), 但因为我们设计 y 也对应正确解就能解出唯一权重 — 实际上 X^T X 是奇异的, 这种共线场景在数值上会失败. 改用独立两特征: x1=[1,2,3,4] x2=[2,1,4,3] (不共线), y =$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_ne_single_sample$v$, $v$X=[[1]] y=[5] → w=[5] (1 sample 1 feature 唯一解)$v$, true, $v$X=[[1]] y=[5] → w=[5] (1 sample 1 feature 唯一解)$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_ne_raises_on_singular$v$, $v$X 重复行 → X^T X 奇异 → ValueError$v$, true, $v$X 重复行 → X^T X 奇异 → ValueError$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_ne_raises_on_empty$v$, $v$ne raises on empty$v$, true, $v$ne raises on empty$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_ne_raises_on_non_list$v$, $v$ne raises on non list$v$, true, $v$ne raises on non list$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
