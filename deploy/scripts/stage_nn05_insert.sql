-- NN5: 浅层神经网络实战
-- practice_id=8, order_in_practice=5, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$浅层神经网络实战$v$,
        'PRACTICE',
        5,
        $v$intermediate$v$,
        $v$## 浅层 MLP 的结构

## 1.1 一隐层 MLP

浅层 MLP 是最简单的深度网络: 一个隐藏层 + 一个输出层。流水线:

$X (N, d) \xrightarrow{W_1, b_1} z_1 (N, h) \xrightarrow{\text{ReLU}} a_1 \xrightarrow{W_2, b_2} z_2 (N, 1) \xrightarrow{\sigma} a_2$

参数: $W_1 \in \mathbb{R}^{d \times h}, b_1 \in \mathbb{R}^h, W_2 \in \mathbb{R}^{h \times 1}, b_2 \in \mathbb{R}^1$

## 1.2 为什么是这种组合

- **隐藏层 ReLU**: NN02 介绍的 ReLU 是中间层默认选择 (训练快、不饱和)
- **输出层 Sigmoid**: 二分类需要"概率解释" (NN02), Sigmoid 输出落在 (0, 1)
- **损失 BCE**: NN03 介绍的二元交叉熵, 与 Sigmoid 配合数值稳定

这种 ReLU 隐层 + Sigmoid 输出 + BCE 是二分类的"工业标准"。回归任务把输出 Sigmoid 换成 linear (无激活), BCE 换成 MSE。

## 1.3 浅层 vs 深层

浅层 MLP (1-2 个隐藏层) 在工程上仍有用武之地:
- 表格数据建模 (信贷、广告 CTR、推荐排序等结构化任务)
- 数据量小 (< 10k), 深网络反而过拟合
- 推理延迟敏感, 浅层快

数据非结构化 (图像/文本/语音) 时浅层 MLP 力不从心, 后续课程介绍卷积、循环等专用结构。


## 前向传播的具体计算

## 2.1 一次前向的四个张量

给定一个 batch $X$ 形状 $(N, d)$, 浅层 MLP 一次前向产出 4 个中间张量:

$z_1 = X \cdot W_1 + b_1 \in \mathbb{R}^{N \times h}$ (隐层线性输出)
$a_1 = \text{ReLU}(z_1) \in \mathbb{R}^{N \times h}$ (隐层激活)
$z_2 = a_1 \cdot W_2 + b_2 \in \mathbb{R}^{N \times 1}$ (输出层线性)
$a_2 = \sigma(z_2) \in \mathbb{R}^{N \times 1}$ (输出概率)

4 个中间结果都要保留 — 反向传播会用到 $z_1$ (求 ReLU 导数), $a_1$ (求 dW2), $a_2$ (求 dz2)。

## 2.2 偏置广播

$b_1$ 形状 $(h,)$, 但要加到 $X \cdot W_1$ 形状 $(N, h)$ 上。这里靠**广播**: $b_1$ 沿样本维度复制 $N$ 次, 每行加同样的偏置向量。numpy / torch 自动处理, 手写 Python list 时要逐行加。

## 2.3 数值规模直觉

新手训练 NN 时, 看激活值规模能快速诊断:
- $z_1, z_2$ 健康范围 $|z| < 10$ (Sigmoid 不饱和)
- $a_1$ 应有正负混合分布 (ReLU 后 50% 接近 0 是健康的)
- $a_2$ 训练初期应散布在 $[0.3, 0.7]$, 完全收敛后才会出现接近 0 或 1

$|z|$ 突然爆炸 ($> 100$) 通常是初始化或学习率问题; $a_1$ 几乎全 0 是 ReLU 死亡 (NN02)。


## 反向传播与梯度公式

## 3.1 BCE + Sigmoid 的"美妙"组合

数学上 BCE 损失对 $z_2$ 的梯度有一个简洁的封闭式:

$\frac{\partial L}{\partial z_2} = a_2 - y$

这是"BCE+sigmoid 组合梯度"的简化结果, 推导时 $\sigma'(z_2) = \sigma(z_2)(1-\sigma(z_2))$ 与 BCE 关于 $a_2$ 的偏导互相抵消, 留下 $a_2 - y$。

工程上利用这个简化, 直接从 $a_2 - y$ 反传, 跳过两次求导, 数值更稳定。

## 3.2 完整反向四步

给定一个 batch (N 个样本), 反向传播的四个梯度 (BCE 取 mean):

**步 1**: $dz_2 = a_2 - y$ (形状 $N \times 1$)
$dW_2 = \frac{1}{N} a_1^T \cdot dz_2$ (形状 $h \times 1$)
$db_2 = \frac{1}{N} \sum_i dz_2^{(i)}$ (形状 $1$)

**步 2** 反传到 $a_1$:
$da_1 = dz_2 \cdot W_2^T$ (形状 $N \times h$)

**步 3** 反传到 $z_1$ (ReLU 导数 = 0/1 mask):
$dz_1 = da_1 \odot \mathbb{1}[z_1 > 0]$ (形状 $N \times h$)

**步 4**:
$dW_1 = \frac{1}{N} X^T \cdot dz_1$ (形状 $d \times h$)
$db_1 = \frac{1}{N} \sum_i dz_1^{(i)}$ (形状 $h$)

返回 4 个梯度 $(dW_1, db_1, dW_2, db_2)$, 接下来 NN07 优化算法用这些梯度更新参数。

## 3.3 ReLU 反向的 mask 写法

$\text{ReLU}(z) = \max(0, z)$, 导数:
$\text{ReLU}'(z) = \begin{cases} 1 & z > 0 \\ 0 & z \leq 0 \end{cases}$

反向时不需要重新算 ReLU, 而是用前向保存的 $z_1$ 直接生成 0/1 mask, 与 $da_1$ 相乘即得 $dz_1$。复用前向中间结果是工程实务的核心。


## 推理 / 评估与业务案例

## 4.1 推理: Sigmoid 输出转标签

训练好的网络对新样本做预测:
1. 完整前向得到 $a_2$ (形状 $(N, 1)$, 取值 $(0, 1)$)
2. 用阈值 $T$ (默认 0.5) 转成 0/1: $\hat{y}_i = 1$ 当 $a_{2,i} \geq T$, 否则 0

阈值的业务取舍 (NN03/04 已介绍): Recall 重要场景 (流失/漏诊) 调低 $T$, Precision 重要场景 (反欺诈) 调高。

## 4.2 准确率评估

$\text{Accuracy} = \frac{\sum_i \mathbb{1}[\hat{y}_i = y_i]}{N}$

二分类准确率与多分类公式相同 — 都是"预测对的样本占比"。和 NN03 的 BCE 损失对应, BCE 越低 accuracy 越高 (但不严格单调, 类别不平衡时背离)。

## 4.3 业务案例: 信贷违约浅层 MLP

复习 MJ03 信贷数据 (12 特征 / 80%/20% 不平衡), 用浅层 MLP:
- 输入 $X$ 形状 $(N, 12)$
- 隐藏层 $h = 32$ (经验: 输入特征数的 2-4 倍是好起点)
- 输出 1 维 sigmoid

训练得到 $W_1$ 形状 $(12, 32)$, $W_2$ 形状 $(32, 1)$, $b_1$ 长 32, $b_2$ 长 1。

推理一个新申贷样本: 先把 12 个特征做 NN03 介绍的标准化, 然后过浅层 MLP 得到违约概率, 再按业务阈值判定。

预期效果对比 (与 MJ04 逻辑回归):
- 逻辑回归 AUC ≈ 0.78
- 浅层 MLP AUC ≈ 0.82 (+4 点, 因为非线性表达力)

浅层 MLP 在结构化数据上提升有限 (4 点典型), 这是为什么很多金融场景仍偏好可解释的逻辑回归。NN 真正的优势在非结构化 (CV/NLP), 后续课程展开。

## 4.4 工程口诀

- **隐层数**: 表格数据 1 隐层够, 2 上限; 非结构化数据后续课程展开
- **隐层宽度**: 输入特征数的 2-4 倍是经验起点
- **batch 在第 0 维**: 工业框架的统一约定
- **前向中间结果保留**: 反向传播必用

$v$,
        $v${"questions": [{"id": "q05-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn05.py 中的 4 个函数; 评测以 test_nn05.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_fp_zero_input$v$, $v$X=[[0]] W1=[[1]] b1=[0] W2=[[1]] b2=[0] → z1=[[0]] a1=[[0]] z2=[[0]] a2=[[0.5]]$v$, false, $v$X=[[0]] W1=[[1]] b1=[0] W2=[[1]] b2=[0] → z1=[[0]] a1=[[0]] z2=[[0]] a2=[[0.5]]$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_fp_unit_input$v$, $v$X=[[1]] W1=[[1]] b1=[0] W2=[[1]] b2=[0] → z1=[[1]] a1=[[1]] z2=[[1]] a2=[[σ(1)]]$v$, false, $v$X=[[1]] W1=[[1]] b1=[0] W2=[[1]] b2=[0] → z1=[[1]] a1=[[1]] z2=[[1]] a2=[[σ(1)]]$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_fp_negative_z1_relu_zeros$v$, $v$X=[[-2]] W1=[[1]] b1=[0] W2=[[1]] b2=[0] → z1=[[-2]] a1=[[0]] (ReLU 截断)$v$, false, $v$X=[[-2]] W1=[[1]] b1=[0] W2=[[1]] b2=[0] → z1=[[-2]] a1=[[0]] (ReLU 截断)$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_fp_two_by_two$v$, $v$X=[[1,0],[0,1]] W1=I W2=[[1],[1]] b=0 → 详见 handbook 推导$v$, false, $v$X=[[1,0],[0,1]] W1=I W2=[[1],[1]] b=0 → 详见 handbook 推导$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_fp_with_bias$v$, $v$X=[[0]] W1=[[1]] b1=[5] W2=[[1]] b2=[3] → z1=[[5]] a1=[[5]] z2=[[8]] a2=[[σ(8)]]$v$, false, $v$X=[[0]] W1=[[1]] b1=[5] W2=[[1]] b2=[3] → z1=[[5]] a1=[[5]] z2=[[8]] a2=[[σ(8)]]$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_fp_raises_on_dim_mismatch$v$, $v$fp raises on dim mismatch$v$, false, $v$fp raises on dim mismatch$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_fp_raises_on_empty$v$, $v$fp raises on empty$v$, false, $v$fp raises on empty$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_fp_raises_on_non_list$v$, $v$fp raises on non list$v$, false, $v$fp raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_bp_textbook_2x2$v$, $v$与 handbook 一致的 2x2 案例: 完整反向梯度 y=[1,0], a2=[[σ(1)],[σ(1)]] → dz2=[[σ(1)-1],[σ(1)]]$v$, false, $v$与 handbook 一致的 2x2 案例: 完整反向梯度 y=[1,0], a2=[[σ(1)],[σ(1)]] → dz2=[[σ(1)-1],[σ(1)]]$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_bp_zero_loss_gradient$v$, $v$y=a2 → dz2=0 → 所有梯度=0$v$, false, $v$y=a2 → dz2=0 → 所有梯度=0$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_bp_relu_mask_zeros_negative$v$, $v$z1 含负值, ReLU 反向 mask 应让对应 dz1 = 0$v$, false, $v$z1 含负值, ReLU 反向 mask 应让对应 dz1 = 0$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_bp_dW2_shape$v$, $v$dW2 形状必须 (h, 1)$v$, false, $v$dW2 形状必须 (h, 1)$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_bp_raises_on_dim_mismatch$v$, $v$y 长度 2 vs X 长度 1 → ValueError$v$, false, $v$y 长度 2 vs X 长度 1 → ValueError$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_bp_raises_on_empty$v$, $v$bp raises on empty$v$, false, $v$bp raises on empty$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_bp_raises_on_non_list$v$, $v$bp raises on non list$v$, false, $v$bp raises on non list$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_pl_basic$v$, $v$[[0.1],[0.5],[0.9]] → [0, 1, 1] (0.5 边界 >=)$v$, true, $v$[[0.1],[0.5],[0.9]] → [0, 1, 1] (0.5 边界 >=)$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_pl_high_threshold$v$, $v$阈值 0.95: [[0.5],[0.99]] → [0, 1]$v$, true, $v$阈值 0.95: [[0.5],[0.99]] → [0, 1]$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_pl_low_threshold$v$, $v$阈值 0.1: [[0.05],[0.2]] → [0, 1]$v$, true, $v$阈值 0.1: [[0.05],[0.2]] → [0, 1]$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_pl_all_above$v$, $v$全部 >= 0.5 → 全 1$v$, true, $v$全部 >= 0.5 → 全 1$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_pl_all_below$v$, $v$全部 < 0.5 → 全 0$v$, true, $v$全部 < 0.5 → 全 0$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_pl_raises_on_wrong_shape$v$, $v$非 (N, 1) 形状 → ValueError$v$, true, $v$非 (N, 1) 形状 → ValueError$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_pl_raises_on_empty$v$, $v$空列表 → ValueError$v$, true, $v$空列表 → ValueError$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_pl_raises_on_non_list$v$, $v$pl raises on non list$v$, true, $v$pl raises on non list$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_acc_perfect$v$, $v$全对 → 1.0$v$, true, $v$全对 → 1.0$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_acc_all_wrong$v$, $v$全错 → 0.0$v$, true, $v$全错 → 0.0$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_acc_three_quarters$v$, $v$3/4 对 → 0.75$v$, true, $v$3/4 对 → 0.75$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_acc_half$v$, $v$1/2 对 → 0.5$v$, true, $v$1/2 对 → 0.5$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_acc_one_third$v$, $v$1/3 对 → 1/3$v$, true, $v$1/3 对 → 1/3$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_acc_raises_on_length_mismatch$v$, $v$acc raises on length mismatch$v$, true, $v$acc raises on length mismatch$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_acc_raises_on_empty$v$, $v$acc raises on empty$v$, true, $v$acc raises on empty$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_acc_raises_on_invalid_label$v$, $v$acc raises on invalid label$v$, true, $v$acc raises on invalid label$v$, NULL, 31)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
