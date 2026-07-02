-- NN10: 循环神经网络基础
-- practice_id=8, order_in_practice=10, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$循环神经网络基础$v$,
        'PRACTICE',
        10,
        $v$advanced$v$,
        $v$## 为什么需要循环结构

## 1.1 序列数据的特点

文本、语音、时序信号都是序列 — 元素之间有顺序依赖。复习 NN05 的 MLP / NN09 的 CNN, 它们对静态向量或网格 (图像) 设计, 不直接处理"序列长度可变 + 时间依赖"。

序列建模的核心需求:
- **共享参数**: 同样的"理解机制"应该应用到序列每个位置 (类似 CNN 的权重共享)
- **历史记忆**: 当前位置的处理需要参考之前的位置
- **变长支持**: 一句话可能 5 个词或 50 个词, 模型应该都能处理

RNN (Recurrent Neural Network) 的设计响应这三个需求: 一个共享的"细胞" (cell) 在序列上滑动, 每步输入当前元素 + 之前的隐藏状态, 输出新的隐藏状态。

## 1.2 朴素 RNN 的单步公式

给定输入 $x_t$ (当前位置) 与 $h_{t-1}$ (上一步隐藏状态):

$h_t = \tanh\left(W_{xh} \cdot x_t + W_{hh} \cdot h_{t-1} + b_h\right)$

$W_{xh}$ 处理输入, $W_{hh}$ 处理历史, $b_h$ 是偏置, tanh 提供非线性 (NN02)。

训练时反向传播沿时间轴展开 (BPTT, Backpropagation Through Time), 等价于一个深度等于序列长度的网络 — 这带来 NN06 提到的梯度消失/爆炸问题, 是朴素 RNN 难训长序列的根本原因。

## 1.3 长序列的挑战

朴素 RNN 在序列长度 > 20 时几乎学不到长距离依赖 — 反向传播经过 20+ 步乘法 (导数), 梯度被指数级衰减。

LSTM 与 GRU 是解决这个问题的两种主流改进, 都引入"门控机制"控制信息流。


## LSTM: 4 个门

## 2.1 LSTM 的核心思想

LSTM (Long Short-Term Memory) 在 RNN 之上引入两个关键设计:
- **细胞状态** $c_t$: 一条贯穿序列的"信息高速公路", 让长距离信息直接传输
- **门控** (gate): 学习"何时让信息通过"的开关, sigmoid 输出 (0, 1) 表示"通过比例"

4 个门各有职责:
- **input gate** $i_t$: 决定新信息有多少进入 cell
- **forget gate** $f_t$: 决定旧 cell 状态保留多少
- **output gate** $o_t$: 决定 cell 状态多少暴露给隐藏状态
- **candidate** $g_t$: 候选新信息 (tanh 激活, 不是门)

## 2.2 单步公式

把 $x_t$ 与 $h_{t-1}$ 拼接为 $[x_t; h_{t-1}]$, 4 个门分别用各自的 W 与 b:

$i_t = \sigma(W_i \cdot [x_t; h_{t-1}] + b_i)$
$f_t = \sigma(W_f \cdot [x_t; h_{t-1}] + b_f)$
$o_t = \sigma(W_o \cdot [x_t; h_{t-1}] + b_o)$
$g_t = \tanh(W_g \cdot [x_t; h_{t-1}] + b_g)$

然后更新 cell 与隐藏状态:
$c_t = f_t \odot c_{t-1} + i_t \odot g_t$
$h_t = o_t \odot \tanh(c_t)$

$\odot$ 是逐元素相乘。本关只要求计算 4 门, cell/hidden 更新由 framework 处理。

## 2.3 LSTM 为什么能学长依赖

关键在 cell 状态的更新: $c_t = f_t c_{t-1} + i_t g_t$。当 $f_t \approx 1$, 旧信息几乎无损穿过 — 不像朴素 RNN 每步都要经过 tanh + 矩阵乘法。这让长距离梯度可以"绕过"激活函数饱和与指数衰减。

工程实务: LSTM 是 2014-2017 年序列建模主流, 后被 Transformer (后续课程介绍) 取代但在小数据 / 有时序结构数据上仍有用武之地。


## GRU: 3 个门

## 3.1 GRU 的简化设计

GRU (Gated Recurrent Unit) 是 LSTM 的简化版:
- 把 input + forget 合并为一个 update gate
- 没有独立 cell 状态, 只有 hidden state
- 3 个门 (update / reset / candidate), 比 LSTM 少 1 个

参数数量比 LSTM 少 ~25%, 训练快, 在中小数据集上常表现接近或更好。

## 3.2 单步公式

$z_t = \sigma(W_z \cdot [x_t; h_{t-1}] + b_z)$
$r_t = \sigma(W_r \cdot [x_t; h_{t-1}] + b_r)$
$\tilde{h}_t = \tanh(W_h \cdot [x_t; r_t \odot h_{t-1}] + b_h)$

$h_t = (1 - z_t) \odot h_{t-1} + z_t \odot \tilde{h}_t$

- $z_t$ (update): 决定新候选 vs 旧状态的混合比例
- $r_t$ (reset): 决定多少历史影响候选计算
- $\tilde{h}_t$ (candidate): 候选新隐藏状态

本关只要求返回 3 门 (z, r, h_tilde), 最终 $h_t$ 更新由 framework 处理。

## 3.3 LSTM vs GRU 选型

- **数据量小 (< 10k)**: GRU 略优 (参数少不易过拟合)
- **数据量大 (> 100k)**: 接近, GRU 略快
- **复杂任务 (机器翻译)**: LSTM 经验略优 (参数多表达力强)

不知道选什么 → GRU (大多数情况够用 + 训练快)。


## 序列截断与业务案例

## 4.1 为什么要截断序列

现实中文本/序列长度差异极大 (1 个 token ~ 10000 个 token)。RNN 单步计算量恒定, 序列越长总计算越大。同 batch 内序列长度必须对齐 (padding 到最长), 极长样本会让整个 batch 慢。

截断策略:
- 设 `max_len`, 超过的样本取前 `max_len` (或末 `max_len`, 看任务)
- 不足的样本 padding 到 `max_len`

`compute_sequence_length_after_truncate(seq_len, max_len) = min(seq_len, max_len)`

工程上 max_len 选择平衡两个考量:
- 太短 (max_len=50): 长样本信息丢失, 但训练快
- 太长 (max_len=1000): 全部信息保留, 但 batch 慢且 padding 浪费

经验值: 文本 max_len=128~512, 时序信号根据采样率定。

## 4.2 业务案例: 电商评论情感分析

场景: 50 万条电商评论, 二分类 (正面/负面)。评论长度分布:
- P50 = 30 词, P90 = 120 词, P99 = 800 词

架构:
- 词嵌入层: 把每个词映射到 128 维向量
- 双向 GRU 隐藏维度 256
- 全连接 → sigmoid 输出概率

max_len 选择:
- max_len=50 (P50 附近): 容易训练但 P90+ 长评论的关键转折信息丢失
- max_len=200 (P99 附近): 计算量大但保留绝大多数信息
- max_len=120 (P90): 折中选择 — 90% 的样本完整保留, 10% 长评论截前 120 词 (情感往往体现在开头几句)

训练后效果: 短评论 (< 50 词) 准确率 95%; 长评论 (> 200 词) 准确率 88% (截断信息损失)。

## 4.3 工程口诀

- **GRU 是默认**: 不知道选 → GRU
- **max_len 看分布**: 取长度直方图 P90-P95 之间
- **梯度裁剪**: RNN 易爆梯度, clip max-norm = 1.0 标配

$v$,
        $v${"questions": [{"id": "q10-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn10.py 中的 4 个函数; 评测以 test_nn10.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_rnn_zero_input_zero_hidden$v$, $v$tanh(0+0+0) = 0$v$, false, $v$tanh(0+0+0) = 0$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_rnn_unit_input$v$, $v$x=[1] h=[0] W_xh=[[1]] W_hh=[[1]] b=[0] → tanh(1) ≈ 0.7616$v$, false, $v$x=[1] h=[0] W_xh=[[1]] W_hh=[[1]] b=[0] → tanh(1) ≈ 0.7616$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_rnn_with_hidden$v$, $v$x=[0] h=[2] W_hh=[[0.5]] b=[0] → tanh(0+1+0)=tanh(1)$v$, false, $v$x=[0] h=[2] W_hh=[[0.5]] b=[0] → tanh(0+1+0)=tanh(1)$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_rnn_two_dim$v$, $v$x=[1,1] h=[0,0], W_xh=[[1,0],[0,1]] (id), W_hh=[[0,0],[0,0]] (zero), b=[0,0] → tanh([1, 1]) = [tanh(1), tanh(1)]$v$, false, $v$x=[1,1] h=[0,0], W_xh=[[1,0],[0,1]] (id), W_hh=[[0,0],[0,0]] (zero), b=[0,0] → tanh([1, 1]) = [tanh(1), tanh(1)]$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_rnn_with_bias$v$, $v$x=[0] h=[0] b=[5] → tanh(5) ≈ 0.9999$v$, false, $v$x=[0] h=[0] b=[5] → tanh(5) ≈ 0.9999$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_rnn_raises_on_dim_mismatch$v$, $v$rnn raises on dim mismatch$v$, false, $v$rnn raises on dim mismatch$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_rnn_raises_on_empty$v$, $v$rnn raises on empty$v$, false, $v$rnn raises on empty$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_rnn_raises_on_non_list$v$, $v$rnn raises on non list$v$, false, $v$rnn raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_lstm_basic$v$, $v$x=[1], h=[0], 4 门各自 W=[[0.5],[0.3]] (concat 2 dim → 1 hidden) concat = [1, 0] z = 1*0.5 + 0*0.3 + 0 = 0.5 i = sigmoid(0.5) ≈ 0.6225 f = sigmoid(0.5) ≈ 0.6225 (用相同 W, 不同 b 区分) o = sigmoid(0.5) ≈ 0.6225$v$, false, $v$x=[1], h=[0], 4 门各自 W=[[0.5],[0.3]] (concat 2 dim → 1 hidden) concat = [1, 0] z = 1*0.5 + 0*0.3 + 0 = 0.5 i = sigmoid(0.5) ≈ 0.6225 f = sigmoid(0.5) ≈ 0.6225 (用相同 W, 不同 b 区分) o = sigmoid(0.5) ≈ 0.6225$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_lstm_different_gates$v$, $v$各门用不同 W 区分$v$, false, $v$各门用不同 W 区分$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_lstm_with_h_prev$v$, $v$h_prev 非零, x=0, W=[[0],[1]] → z=h_prev$v$, false, $v$h_prev 非零, x=0, W=[[0],[1]] → z=h_prev$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_lstm_with_bias$v$, $v$全 0 输入, b=[1] → z=1$v$, false, $v$全 0 输入, b=[1] → z=1$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_lstm_raises_on_wrong_W_count$v$, $v$W_list 必须 4 个$v$, false, $v$W_list 必须 4 个$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_lstm_raises_on_dim_mismatch$v$, $v$lstm raises on dim mismatch$v$, false, $v$lstm raises on dim mismatch$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_lstm_raises_on_non_list$v$, $v$lstm raises on non list$v$, false, $v$lstm raises on non list$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_gru_basic$v$, $v$x=[1] h=[0] W=[[0.5],[0]] b=[0] for all 3 z = sigmoid(0.5) ≈ 0.6225 r = sigmoid(0.5) ≈ 0.6225 h_tilde = tanh([1; r*0] @ [[0.5],[0]] + 0) = tanh(0.5)$v$, true, $v$x=[1] h=[0] W=[[0.5],[0]] b=[0] for all 3 z = sigmoid(0.5) ≈ 0.6225 r = sigmoid(0.5) ≈ 0.6225 h_tilde = tanh([1; r*0] @ [[0.5],[0]] + 0) = tanh(0.5)$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_gru_with_hidden_no_reset$v$, $v$x=[0] h=[1], W_z=[[0],[1]] (z 直接读 h), W_r=[[0],[0]] (r=sigmoid(0)=0.5) W_h=[[0],[1]] → h_tilde 输入 [0; 0.5*1] = [0, 0.5] h_tilde = tanh(0*0 + 0.5*1 + 0) = tanh(0.5)$v$, true, $v$x=[0] h=[1], W_z=[[0],[1]] (z 直接读 h), W_r=[[0],[0]] (r=sigmoid(0)=0.5) W_h=[[0],[1]] → h_tilde 输入 [0; 0.5*1] = [0, 0.5] h_tilde = tanh(0*0 + 0.5*1 + 0) = tanh(0.5)$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_gru_zero_input_and_hidden$v$, $v$全 0, b=0 → 全 0.5/0.5/0$v$, true, $v$全 0, b=0 → 全 0.5/0.5/0$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_gru_with_bias$v$, $v$全 0 输入 + b=1 各门$v$, true, $v$全 0 输入 + b=1 各门$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_gru_raises_on_wrong_W_count$v$, $v$gru raises on wrong W count$v$, true, $v$gru raises on wrong W count$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_gru_raises_on_dim_mismatch$v$, $v$gru raises on dim mismatch$v$, true, $v$gru raises on dim mismatch$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_gru_raises_on_non_list$v$, $v$gru raises on non list$v$, true, $v$gru raises on non list$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_trunc_within_max$v$, $v$trunc within max$v$, true, $v$trunc within max$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_trunc_exceeds_max$v$, $v$trunc exceeds max$v$, true, $v$trunc exceeds max$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_trunc_equal$v$, $v$trunc equal$v$, true, $v$trunc equal$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_trunc_zero_seq$v$, $v$trunc zero seq$v$, true, $v$trunc zero seq$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_trunc_one_seq$v$, $v$trunc one seq$v$, true, $v$trunc one seq$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_trunc_raises_on_negative_seq$v$, $v$trunc raises on negative seq$v$, true, $v$trunc raises on negative seq$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_trunc_raises_on_zero_max$v$, $v$trunc raises on zero max$v$, true, $v$trunc raises on zero max$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_trunc_raises_on_non_int$v$, $v$trunc raises on non int$v$, true, $v$trunc raises on non int$v$, NULL, 30)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
