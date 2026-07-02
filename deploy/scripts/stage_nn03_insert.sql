-- NN3: 前向传播与损失函数
-- practice_id=8, order_in_practice=3, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$前向传播与损失函数$v$,
        'PRACTICE',
        3,
        $v$intermediate$v$,
        $v$## 从单神经元到一层

## 1.1 单神经元的前向

复习 NN02 的神经元结构: 输入 $\mathbf{x} = (x_1, \ldots, x_d)$, 权重 $\mathbf{w} = (w_1, \ldots, w_d)$, 偏置 $b$:

$z = \sum_{i=1}^{d} w_i x_i + b = \mathbf{w} \cdot \mathbf{x} + b$

$z$ 是"打分", 经过 NN02 的激活函数后变成神经元输出 $a = f(z)$。

## 1.2 多神经元一层

一层有 $h$ 个神经元, 每个神经元独立有自己的权重向量与偏置。把 $h$ 个神经元的权重并排成矩阵 $W$, 偏置并成向量 $\mathbf{b}$:

$W \in \mathbb{R}^{d \times h}, \quad \mathbf{b} \in \mathbb{R}^{h}$

对一个样本 $\mathbf{x}$, 一层的输出 (激活前):
$\mathbf{z} = \mathbf{x} \cdot W + \mathbf{b} \in \mathbb{R}^{h}$

## 1.3 批量化: 多样本一起算

单样本太慢, 工程上批处理 $N$ 个样本同时算:

$X \in \mathbb{R}^{N \times d}, \quad W \in \mathbb{R}^{d \times h}, \quad \mathbf{b} \in \mathbb{R}^{h}$

$Z = X \cdot W + \mathbf{b}$ (广播相加) 形状 $(N, h)$

矩阵乘法是深度网络计算量的 99%。GPU 的并行能力对应到这一步, 是深度学习能跑得动的根本。

工程提醒: 实现时 $\mathbf{b}$ 的广播容易写错。`X @ W` 形状 $(N, h)$, 加 $\mathbf{b}$ (形状 $h$) 应该让 $\mathbf{b}$ 沿样本维度复制 $N$ 次。numpy/torch 自动广播, 但手写 Python 列表时需要在每行加上同样的偏置。


## 三大损失函数

## 2.1 MSE: 回归任务的"距离损失"

均方误差 (Mean Squared Error):

$\text{MSE} = \frac{1}{N} \sum_{i=1}^{N} (y_i - \hat{y}_i)^2$

$y_i$ 是真值 (连续数值), $\hat{y}_i$ 是模型预测。MSE 适合**回归任务** (房价、温度、销量), 复习 MJ06 的回归内容。

## 2.2 二元交叉熵: 二分类的"概率损失"

二元交叉熵 (Binary Cross Entropy):

$\text{BCE} = -\frac{1}{N} \sum_{i=1}^{N} \left[ y_i \log(p_i) + (1 - y_i) \log(1 - p_i) \right]$

$y_i \in \{0, 1\}$ 是真实标签, $p_i \in (0, 1)$ 是模型给的"类别 1 的概率" (通常是 sigmoid 输出)。直观理解:
- $y_i = 1$ 时: 损失是 $-\log(p_i)$, $p_i \to 1$ 损失趋 0, $p_i \to 0$ 损失趋 $+\infty$ (惩罚错误置信)
- $y_i = 0$ 时: 损失是 $-\log(1 - p_i)$, 反过来

数值要点: $\log(0)$ 是 $-\infty$, 实现时要做数值稳定 (例如 $p_i$ 加 $\epsilon = 10^{-12}$ 防止 0)。

## 2.3 多元交叉熵: 多分类的"扩展版本"

多元交叉熵 (Categorical Cross Entropy):

$\text{CCE} = -\frac{1}{N} \sum_{i=1}^{N} \log(p_{i, y_i})$

$y_i \in \{0, 1, \ldots, C-1\}$ 是样本 $i$ 的真实类别索引 (整数), $p_{i, y_i}$ 是模型给的"该样本属于真实类别的概率"。模型对每样本给一个 $C$ 维概率向量 (各分量 ≥ 0, 和 = 1, 通常是 softmax 输出)。

注意: 这里假设标签用**类别索引**形式 (sparse), 实际深度学习框架还有 one-hot 形式 ($y_i$ 是长度 $C$ 的 0/1 向量), 两种公式等价但数据形式不同。

## 2.4 三者的对应关系

| 任务 | 输出层激活 | 损失函数 | 真值类型 |
|------|----------|---------|---------|
| 回归 | linear (无激活) | MSE | 连续数值 |
| 二分类 | sigmoid | BCE | 0 或 1 |
| 多分类 | softmax | CCE | 0~C-1 整数 |

选错就崩: 二分类用 MSE 训练会"学不动" (sigmoid + MSE 非凸, 复习 MJ04 课程的提醒)。


## 数值稳定与边界

## 3.1 log(0) 的处理

二元/多元交叉熵都涉及 $\log(p)$, 当 $p = 0$ 时是 $-\infty$, 计算崩溃。

工程做法:
- 在 $\log$ 之前: 把 $p$ clip 到 $[\epsilon, 1-\epsilon]$, 常用 $\epsilon = 10^{-12}$ 或 $10^{-15}$
- 或用 stable formulation (融合 sigmoid + BCE 计算, 避开中间步骤)

本关测试不要求 stable formulation, 但要求避免 $\log(0) = -\infty$ 的运行时错误。

## 3.2 softmax 概率必须和为 1

多元交叉熵假设每样本的概率向量和为 1 (是合法的概率分布)。如果输入 $p$ 不归一, 计算结果不可解释。实务上输入 $p$ 应该是 softmax 输出, 自动归一。

## 3.3 形状对齐

多层前向中, 形状不对齐是最常见 bug。训练前打印每层 shape 是工程实务标准。


## 业务案例: 信贷违约二分类前向

## 4.1 场景

银行风控部用神经网络做违约预测, 输入 12 个特征 (复习 MJ03 信贷案例), 输出"违约概率"。

架构 (高层):
- 输入: $(N, 12)$
- 隐层: 16 个神经元 (具体训练后续课程)
- 输出层: 1 个神经元 + sigmoid → 概率

## 4.2 前向计算

对 batch 大小 $N = 64$:
1. 隐层输入 $Z_1 = X \cdot W_1 + \mathbf{b}_1$, 形状 $(64, 16)$
2. 隐层激活 $A_1 = \text{ReLU}(Z_1)$
3. 输出层 $Z_2 = A_1 \cdot W_2 + \mathbf{b}_2$, 形状 $(64, 1)$
4. 输出层激活 $\hat{p} = \sigma(Z_2)$, 形状 $(64, 1)$

## 4.3 损失计算

$y$ 是真实违约标签 $(64,)$, 取值 0 或 1。

$\text{BCE} = -\frac{1}{64} \sum_{i=1}^{64} \left[ y_i \log(\hat{p}_i) + (1-y_i) \log(1 - \hat{p}_i) \right]$

具体数字: 假设第一个 batch 平均 BCE = 0.69 (接近 $\ln 2$, 随机猜测水平)。训练后期 BCE 降到 0.20 即接近 92% 准确率。

## 4.4 工程口诀

- **shape 永远先检查**: 80% 的训练 bug 是 shape 错位
- **损失值在心里有数**: BCE 随机 ≈ 0.69, CCE-10类随机 ≈ 2.30
- **NaN 多半是 log(0)**: 训练崩溃 90% 是 $p = 0$ 没 clip
- **回归用 MSE / 二分类用 BCE / 多分类用 CCE**: 别混

$v$,
        $v${"questions": [{"id": "q03-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn03.py 中的 4 个函数; 评测以 test_nn03.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_lf_textbook$v$, $v$x=[1,2], w=[0.5,-0.3], b=0.1 → 0.5-0.6+0.1 = 0.0$v$, false, $v$x=[1,2], w=[0.5,-0.3], b=0.1 → 0.5-0.6+0.1 = 0.0$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_lf_simple_doubling$v$, $v$x=[3], w=[2.0], b=0 → 6$v$, false, $v$x=[3], w=[2.0], b=0 → 6$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_lf_only_bias$v$, $v$x=[0,0], w=[1,2], b=5 → 5$v$, false, $v$x=[0,0], w=[1,2], b=5 → 5$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_lf_three_features$v$, $v$x=[1,1,1], w=[0.5,0.5,0.5], b=0.5 → 2.0$v$, false, $v$x=[1,1,1], w=[0.5,0.5,0.5], b=0.5 → 2.0$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_lf_negative_result$v$, $v$x=[2], w=[-1], b=0 → -2$v$, false, $v$x=[2], w=[-1], b=0 → -2$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_lf_raises_on_length_mismatch$v$, $v$lf raises on length mismatch$v$, false, $v$lf raises on length mismatch$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_lf_raises_on_empty$v$, $v$lf raises on empty$v$, false, $v$lf raises on empty$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_lf_raises_on_non_list$v$, $v$lf raises on non list$v$, false, $v$lf raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_lfb_textbook$v$, $v$X=[[1,2]], W=[[3],[4]], b=[5] → [[1*3+2*4+5]] = [[16]]$v$, false, $v$X=[[1,2]], W=[[3],[4]], b=[5] → [[1*3+2*4+5]] = [[16]]$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_lfb_two_samples_two_outputs$v$, $v$X=[[1,0],[0,1]], W=[[1,2],[3,4]], b=[0,0] → [[1,2],[3,4]]$v$, false, $v$X=[[1,0],[0,1]], W=[[1,2],[3,4]], b=[0,0] → [[1,2],[3,4]]$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_lfb_with_bias_broadcast$v$, $v$X=[[1,1]], W=[[1],[1]], b=[10] → [[12]]$v$, false, $v$X=[[1,1]], W=[[1],[1]], b=[10] → [[12]]$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_lfb_three_samples_one_output$v$, $v$X=[[1],[2],[3]], W=[[2]], b=[1] → [[3],[5],[7]]$v$, false, $v$X=[[1],[2],[3]], W=[[2]], b=[1] → [[3],[5],[7]]$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_lfb_zero_input$v$, $v$X=[[0,0,0]], W=[[1],[2],[3]], b=[7] → [[7]]$v$, false, $v$X=[[0,0,0]], W=[[1],[2],[3]], b=[7] → [[7]]$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_lfb_raises_on_dim_mismatch$v$, $v$X 列数 ≠ W 行数$v$, false, $v$X 列数 ≠ W 行数$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_lfb_raises_on_empty$v$, $v$lfb raises on empty$v$, false, $v$lfb raises on empty$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_lfb_raises_on_non_list$v$, $v$lfb raises on non list$v$, false, $v$lfb raises on non list$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_bce_perfect$v$, $v$y=[1,0], p=[1,0] → ~0 (concept: log(1)=0)$v$, true, $v$y=[1,0], p=[1,0] → ~0 (concept: log(1)=0)$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_bce_uniform_half$v$, $v$y=[1,0], p=[0.5,0.5] → -mean(log(0.5)+log(0.5)) = -log(0.5) = log(2) ≈ 0.6931$v$, true, $v$y=[1,0], p=[0.5,0.5] → -mean(log(0.5)+log(0.5)) = -log(0.5) = log(2) ≈ 0.6931$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_bce_known_specific$v$, $v$y=[1,0,1,0], p=[0.9,0.1,0.8,0.2] → -mean(log0.9+log0.9+log0.8+log0.8)/4 = -mean(-0.10536-0.10536-0.22314-0.22314)/4 = 0.16425$v$, true, $v$y=[1,0,1,0], p=[0.9,0.1,0.8,0.2] → -mean(log0.9+log0.9+log0.8+log0.8)/4 = -mean(-0.10536-0.10536-0.22314-0.22314)/4 = 0.16425$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_bce_all_correct_high_conf$v$, $v$y=[1,1,0,0], p=[0.99,0.99,0.01,0.01] → 接近 0 但非 0$v$, true, $v$y=[1,1,0,0], p=[0.99,0.99,0.01,0.01] → 接近 0 但非 0$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_bce_extreme_zero_clipped$v$, $v$y=[1], p=[0.0] 应被 clip, 不应 inf/nan$v$, true, $v$y=[1], p=[0.0] 应被 clip, 不应 inf/nan$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_bce_raises_on_length_mismatch$v$, $v$bce raises on length mismatch$v$, true, $v$bce raises on length mismatch$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_bce_raises_on_empty$v$, $v$bce raises on empty$v$, true, $v$bce raises on empty$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_bce_raises_on_non_list$v$, $v$bce raises on non list$v$, true, $v$bce raises on non list$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_cce_perfect$v$, $v$y=[0,1,2], p=[[1,0,0],[0,1,0],[0,0,1]] (one-hot 完美) → ~0$v$, true, $v$y=[0,1,2], p=[[1,0,0],[0,1,0],[0,0,1]] (one-hot 完美) → ~0$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_cce_uniform_3class$v$, $v$3 class 均匀概率: 真值任意 → -log(1/3) = log(3) ≈ 1.0986$v$, true, $v$3 class 均匀概率: 真值任意 → -log(1/3) = log(3) ≈ 1.0986$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_cce_two_class$v$, $v$2 class 等价 BCE: y=[0,1], p=[[0.7,0.3],[0.4,0.6]] → -mean(log0.7+log0.6)$v$, true, $v$2 class 等价 BCE: y=[0,1], p=[[0.7,0.3],[0.4,0.6]] → -mean(log0.7+log0.6)$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_cce_specific_known$v$, $v$y=[1,2,0], p=[[0.1,0.8,0.1],[0.2,0.3,0.5],[0.6,0.3,0.1]] → -mean(log0.8 + log0.5 + log0.6) / 3$v$, true, $v$y=[1,2,0], p=[[0.1,0.8,0.1],[0.2,0.3,0.5],[0.6,0.3,0.1]] → -mean(log0.8 + log0.5 + log0.6) / 3$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_cce_zero_clipped$v$, $v$真实类概率为 0 应 clip, 不 inf$v$, true, $v$真实类概率为 0 应 clip, 不 inf$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_cce_raises_on_index_out_of_range$v$, $v$cce raises on index out of range$v$, true, $v$cce raises on index out of range$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_cce_raises_on_length_mismatch$v$, $v$cce raises on length mismatch$v$, true, $v$cce raises on length mismatch$v$, NULL, 31),
    ($v$tc_32$v$, $v$test_cce_raises_on_non_list$v$, $v$cce raises on non list$v$, true, $v$cce raises on non list$v$, NULL, 32)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
