-- NN12: 综合项目: 手写数字识别端到端
-- practice_id=8, order_in_practice=12, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$综合项目: 手写数字识别端到端$v$,
        'PRACTICE',
        12,
        $v$advanced$v$,
        $v$## 项目目标与数据约定

## 1.1 业务背景

手写数字识别是图像分类的经典任务: 输入图像, 输出 0-9 类别。
本关验证你对前 11 关知识的整合: 构造 100 样本 / 10 类不平衡数据, 走完端到端建模。

与 MJ12 同款原则: 不预填数据 (学生自构造) + 4 步独立函数 + 内部一致性 (只用 NN01-NN11 概念)。

## 1.2 数据 schema (5 字段)

| 字段名 | 类型 | 含义 | 取值约束 |
|--------|------|------|----------|
| images | list[list[list[float]]] | 100 张 8×8 灰度图像 | 像素 ∈ [0, 16] (sklearn.digits 标准) |
| labels | list[int] | 100 个数字标签 | 0-9, 类别不平衡 |

数据规模: **100 张图像, 10 类**。类别比例: **5 / 8 / 10 / 12 / 15 / 8 / 10 / 12 / 10 / 10** (总 100)。

不平衡设计模拟真实场景 — 实际数据采集很少均匀, 部分类别天然样本少。

## 1.3 项目的 4 步流水线

```
load_mnist_subset()
  ↓ (images, labels)
preprocess_and_split(data, test_size)
  ↓ (X_train, X_test, y_train, y_test)
train_simple_classifier(X_train, y_train, n_epochs, lr)
  ↓ trained state (W, b)
evaluate_classifier(state, X_test, y_test)
  ↓ 5 metrics dict
```

4 步独立, 每一步可单独 unit test。这是工业级 ML 项目的标准结构。


## 复用前 11 关的预处理与建模

## 2.1 步 1 扁平化 (复用 NN09 概念反向)

8×8 图像扁平化为 64 维向量, 让线性分类器可以处理:

$X \in \mathbb{R}^{100 \times 8 \times 8} \to \mathbb{R}^{100 \times 64}$

工程提醒: 扁平化丢弃了空间结构 (邻近像素关系), 这正是 CNN (NN09) 的优势所在。简单线性分类器虽然牺牲性能, 但作为入门骨架够用。

## 2.2 步 2 标准化 (复用 NN03 / MJ03)

手写数字像素值在 [0, 16], 不同位置像素分布差异大。z-score 标准化让每列零均值单位方差:

$\tilde{x}_{ij} = \frac{x_{ij} - \mu_j}{\sigma_j + \epsilon}$

关键: **必须先 split, 再用 train 的 μ/σ 来 transform train+test** (NN03 提到的 data leakage 陷阱)。

## 2.3 步 3 分层划分 (复用 MJ03 / MJ10)

80/20 划分。**不平衡数据必须 stratify** 让 train/test 都保持 10 类比例, 否则 test 可能丢失整个类别 (复习 MJ01 类别不平衡讨论)。

## 2.4 步 4 简单线性 softmax 分类器 (复用 NN03 / NN04 / NN07)

模型结构 (避免完整 MLP, CPU 友好):
- 输入 64 维 → 全连接 → 10 维 logits
- softmax 转概率
- 多元交叉熵损失

训练流程:
- SGD 单步更新 (复用 NN07)
- n_epochs 轮 (典型 10-20 epoch 收敛)
- 训练后返回 (W, b) 状态供推理用

为什么不上 MLP / CNN:
- 100 样本太少, 复杂模型必过拟合
- 评测器 CPU 跑 N epoch 训练已经接近 1-2 秒, 复杂模型超时
- 项目核心是验证"学生能正确组合前 11 关知识", 不是刷准确率


## 多分类评估的 5 指标

## 3.1 多分类的指标考量

二分类 5 指标 (NN11) 都基于二元 confusion matrix。多分类有 C 个类, 需要按"宏平均"扩展。

给定 multiclass confusion matrix $M \in \mathbb{R}^{C \times C}$ ($M_{ij}$ = 真为 i 预测为 j 的样本数):
- **整体准确率 (accuracy)**: $\frac{\sum_c M_{cc}}{\sum_{i,j} M_{ij}}$
- **每类准确率 (per-class)**: $\text{acc}_c = \frac{M_{cc}}{\sum_j M_{cj}}$ (该类的 recall)
- **宏平均 precision**: $\frac{1}{C} \sum_c \frac{M_{cc}}{\sum_i M_{ic}}$
- **宏平均 recall**: $\frac{1}{C} \sum_c \text{acc}_c$
- **宏平均 F1**: $\frac{1}{C} \sum_c F_{1,c}$, 其中 $F_{1,c} = \frac{2 P_c R_c}{P_c + R_c}$

宏平均的意思: 各类先各自计算 metric, 再算平均 — 让每类的"权重"相同, 不平衡数据集很重要 (避免被多数类淹没)。

## 3.2 不平衡数据的指标解读

场景: 10 类, 类 4 占 15%, 类 0 占 5%。

"无脑全部预测为类 4 的模型":
- accuracy = 15% (只对类 4 全对)
- macro-precision = 0.015 (只有类 4 P 不为 0)
- macro-recall = 0.10 (只有类 4 R = 1.0, 其他都 0; 0+0+...+1.0/10)
- macro-F1 极低

所以不平衡数据看 macro-F1 比 accuracy 更可靠 (复习 MJ01 / NN08 的口诀)。

## 3.3 与二分类对比

多分类宏平均把 binary 的 P/R/F1 推广到 C 类 — 各类先算 metric, 再取平均。

NN12 的 5 键 dict: accuracy / macro_precision / macro_recall / macro_f1 / per_class_accuracy (前 4 是 float 标量, 后者是 list 长 10)。


## 工程口诀与内部一致性

## 4.1 业务案例: 100 样本快速 demo

客户要 demo 一个手写数字 API, 100 张标注图。按 4 步流水线: 加载 → 扁平化+标准化+分层划分 → 线性 softmax 20 epoch → 评估。test accuracy 约 60-70% (100 样本上限), macro-F1 约 0.55。客户看到 demo 后决定生产环境用 5 万样本重训, 准确率到 95%+。

## 4.2 内部一致性核对表 (NN12 用的概念在 NN01-11 都教过)

| NN12 用到 | 来源关 |
|-----------|--------|
| 输入模态判断 (图像) | NN01 |
| softmax 概念 | NN03 (output activation) |
| 多元交叉熵 | NN03 |
| SGD 单步更新 | NN07 |
| train/val/test 划分 | NN01 / NN10 / MJ03 / MJ10 |
| macro 平均指标 | NN08 / NN11 推广 |
| 类别不平衡 | NN08 / MJ01 / MJ12 |

0 个超出 NN01-NN11 的概念。综合项目是前 11 关的整合应用, 不引入新算法。

## 4.3 综合项目的工程口诀

- **不要嵌完整数据**: 数据是学生工作的一部分, 嵌进 student.py 等于送分 (MJ12 v1 灾难教训)
- **CPU 友好**: 评测器 ≤ 30 秒, 复杂模型不要上, 用线性分类器或浅 MLP
- **指标全报**: 不平衡数据上 accuracy 误导, 必须看 macro-F1 + per-class
- **流程独立**: 4 步分别可测, 不要写一个大函数嵌套调用
- **业务对齐**: demo 项目和生产项目要求不同, 100 样本能跑通就是合格 demo

$v$,
        $v${"questions": [{"id": "q12-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn12.py 中的 4 个函数; 评测以 test_nn12.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_load_dict_2_keys$v$, $v$load dict 2 keys$v$, false, $v$load dict 2 keys$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_load_100_samples$v$, $v$load 100 samples$v$, false, $v$load 100 samples$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_load_image_shape_8x8$v$, $v$load image shape 8x8$v$, false, $v$load image shape 8x8$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_load_pixel_range$v$, $v$load pixel range$v$, false, $v$load pixel range$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_load_labels_in_0_9$v$, $v$load labels in 0 9$v$, false, $v$load labels in 0 9$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_load_class_imbalance$v$, $v$10 类比例 [5,8,10,12,15,8,10,12,10,10]$v$, false, $v$10 类比例 [5,8,10,12,15,8,10,12,10,10]$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_load_pixel_diversity$v$, $v$图像不能全 0 或全 16 (有变化)$v$, false, $v$图像不能全 0 或全 16 (有变化)$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_pre_returns_4tuple$v$, $v$pre returns 4tuple$v$, false, $v$pre returns 4tuple$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_pre_split_80_20$v$, $v$pre split 80 20$v$, false, $v$pre split 80 20$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_pre_flatten_to_64$v$, $v$pre flatten to 64$v$, false, $v$pre flatten to 64$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_pre_stratified_class_balance$v$, $v$80/20 分层后, train 类计数 = ceil(0.8 × 原计数), 大致保持比例$v$, false, $v$80/20 分层后, train 类计数 = ceil(0.8 × 原计数), 大致保持比例$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_pre_numeric_features$v$, $v$pre numeric features$v$, false, $v$pre numeric features$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_pre_raises_on_missing_field$v$, $v$data 缺 images → 抛错$v$, true, $v$data 缺 images → 抛错$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_train_returns_dict$v$, $v$train returns dict$v$, true, $v$train returns dict$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_train_W_shape$v$, $v$train W shape$v$, true, $v$train W shape$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_train_b_shape$v$, $v$train b shape$v$, true, $v$train b shape$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_train_W_not_zero_after_training$v$, $v$训练后 W 应该不再是初始全 0 (有更新)$v$, true, $v$训练后 W 应该不再是初始全 0 (有更新)$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_eval_returns_5_keys$v$, $v$eval returns 5 keys$v$, true, $v$eval returns 5 keys$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_eval_accuracy_in_range$v$, $v$eval accuracy in range$v$, true, $v$eval accuracy in range$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_eval_per_class_length_10$v$, $v$eval per class length 10$v$, true, $v$eval per class length 10$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_eval_above_baseline$v$, $v$训练后准确率应高于随机猜测 (1/10 = 0.1)$v$, true, $v$训练后准确率应高于随机猜测 (1/10 = 0.1)$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_eval_macro_metrics_in_range$v$, $v$eval macro metrics in range$v$, true, $v$eval macro metrics in range$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_eval_raises_on_invalid_state$v$, $v$eval raises on invalid state$v$, true, $v$eval raises on invalid state$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_eval_actually_uses_state$v$, $v$用 2 个不同的 state (零权重 vs 训练权重), accuracy 应不同 — 防 hardcode 返回常量$v$, true, $v$用 2 个不同的 state (零权重 vs 训练权重), accuracy 应不同 — 防 hardcode 返回常量$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_train_different_n_epochs_differ$v$, $v$n_epochs=1 vs n_epochs=20 训练结果应不同$v$, true, $v$n_epochs=1 vs n_epochs=20 训练结果应不同$v$, NULL, 25)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
