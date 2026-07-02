-- NN11: 模型训练实战
-- practice_id=8, order_in_practice=11, v2 (4-attack + 5-redline validated)
BEGIN;

WITH new_task AS (
    INSERT INTO tasks (practice_id, title, task_type, order_in_practice, difficulty, handbook_markdown, question_data, created_at, updated_at)
    VALUES (
        8,
        $v$模型训练实战$v$,
        'PRACTICE',
        11,
        $v$advanced$v$,
        $v$## 训练循环的组件化

## 1.1 训练循环的标准结构

一个完整训练循环包含以下组件 (高层视角):

```
for epoch in range(N_EPOCH):
    # 训练
    for batch in train_loader:
        loss, params = train_step(params, batch)

    # 验证
    val_loss = validate(params, val_data)
    val_metrics = compute_metrics(...)

    # 日志
    log = format_log(epoch, train_loss, val_loss, val_metrics)
    print(log)

    # 早停
    if should_stop(val_history, patience):
        break
```

本关把训练循环拆成 4 个独立组件 (单步/单次), 让学生分别实现, 而不是写一个整体训练循环 (CPU 评测不友好)。

## 1.2 为什么要组件化

把训练循环拆成独立函数有 3 个工程优势:
- **测试**: 每个组件单独可测, 不需要跑完整训练
- **复用**: 早停 / metrics / 日志在不同模型中复用同一份实现
- **替换**: 想换优化器只改 `train_step`, 想加新指标只扩 `compute_metrics`

工程实务: PyTorch / Keras 的 fit() / Trainer 都是这种组件化抽象的标准化版本。


## 单步训练: 线性模型作为最小例

## 2.1 单步训练的 4 个动作

给定权重 $W$, 偏置 $b$, 一个 batch $(X, y)$, 学习率 $\eta$:

1. **前向**: $\hat{y} = X \cdot W + b$ (复习 NN03)
2. **损失**: $L = \frac{1}{N} \sum (y - \hat{y})^2$ (MSE)
3. **梯度**: $dW = \frac{2}{N} X^T (\hat{y} - y)$, $db = \frac{2}{N} \sum (\hat{y} - y)$ (复习 NN04)
4. **更新**: $W \leftarrow W - \eta \cdot dW$, $b \leftarrow b - \eta \cdot db$ (复习 NN07)

返回更新后的 $(W, b, L)$。这是最简单的"线性回归 + SGD"训练单步, 是更复杂模型 (NN05 MLP / NN09 CNN) 训练的最小骨架。

## 2.2 单步训练的工程提醒

- **shape 一致性**: 前向输出 $\hat{y}$ 与真值 $y$ 必须同形状, 否则 broadcasting 会出 silent bug
- **学习率配合 batch size**: 学习率与 batch size 大致成线性关系, batch 翻倍时 lr 也应翻倍
- **梯度爆炸**: 训练初期梯度可能极大, 应配合 NN08 的梯度裁剪或合理初始化 (NN06)
- **数值稳定**: 含 log 或除法时 (NN03 BCE) 必须 clip / eps, 否则训练 NaN


## 早停: 何时停下

## 3.1 早停的核心逻辑

早停 (Early Stopping) 是防过拟合最简单的工具 (NN08 介绍):
- 监控 val_loss 是否还在改善
- 连续 `patience` 个 epoch 未改善 (新 val_loss 未比历史最佳低 `min_delta`) 就停训

公式化:
```
stop = (best_val_loss - min(val_losses[-patience:])) < min_delta
```

其中 `best_val_loss` 是 patience 之前的最佳。如果最近 `patience` 个 epoch 没有比之前最好低 `min_delta` 以上, 就停。

## 3.2 patience 与 min_delta 的取舍

- **patience 大 (10-20)**: 容忍更多波动, 不易误停, 但浪费计算资源
- **patience 小 (3-5)**: 快速停, 但可能误停 (val_loss 偶有反弹但还会下降)
- **min_delta 0.001**: 默认; 比这个小的改善被视为"无意义", 不重置 counter
- **min_delta 0**: 任何改善都重置, 极度敏感, 几乎不会停 (除非完全平坦)

工程经验: patience=5-10, min_delta=1e-4 是大多数任务的合理起点。

## 3.3 早停 vs 学习率衰减

两者都让训练"自动调节":
- 学习率衰减 (NN07) 让训练后期慢下来精细调
- 早停在过拟合迹象出现时停下来

实务通常两者配合: 衰减让训练继续走, 早停作为兜底保险。


## 5 指标评估 + 日志 + 业务案例

## 4.1 5 指标 dict

二分类任务的完整评估 (复习 MJ12):
- **accuracy**: $\frac{TP + TN}{N}$ (整体正确)
- **precision**: $\frac{TP}{TP + FP}$ (预测正中正确比)
- **recall**: $\frac{TP}{TP + FN}$ (真正中识别比)
- **f1**: $\frac{2PR}{P+R}$ (P/R 调和平均)
- **specificity**: $\frac{TN}{TN + FP}$ (真负中识别比)

除零情况 (分母 0): 该指标取 0.0。

## 4.2 训练日志格式

工程实务的标准日志格式:
`Epoch X | train_loss=Y.YY | val_loss=Z.ZZ | acc=A.AAA | f1=B.BBB`

- 整数 (epoch) 不带小数
- loss 保留 4 位小数 (训练后期 loss 很小, 需要精度)
- 指标保留 3 位小数 (人类阅读够用)
- 用 `|` 分隔字段, 易解析

日志格式统一是工程纪律 — 后续可以正则提取曲线数据, 接 wandb / tensorboard 等可视化工具。

## 4.3 业务案例: 金融时序预测训练

场景: 预测股票次日涨跌 (二分类), 数据 5 万样本, 训练目标 50 epoch 内 val accuracy ≥ 60%。

训练日志样例:
```
Epoch 0 | train_loss=0.6911 | val_loss=0.6905 | acc=0.512 | f1=0.487
Epoch 5 | train_loss=0.6512 | val_loss=0.6580 | acc=0.580 | f1=0.554
Epoch 10 | train_loss=0.6210 | val_loss=0.6450 | acc=0.605 | f1=0.582
Epoch 15 | train_loss=0.5890 | val_loss=0.6480 | acc=0.598 | f1=0.575  (val 反弹)
Epoch 20 | train_loss=0.5520 | val_loss=0.6520 | acc=0.585 | f1=0.560  (持续反弹)
...
```

早停 (patience=5, min_delta=1e-3) 在 epoch 15 触发: val_loss 从 epoch 10 的 0.6450 起 5 步内未改善 → 停训, 加载 epoch 10 的权重作为最终模型。最终 val accuracy 60.5%, 达标。

## 4.4 工程口诀

- **组件化, 不要写大循环**: 4 个独立组件比一个 200 行循环可维护
- **日志格式固定**: 上线后日志要解析, 格式不一致 = 后期返工
- **patience 不要太小**: < 3 几乎一定误停
- **5 指标全报**: 单一 accuracy 在不平衡数据上误导 (复习 MJ01)

$v$,
        $v${"questions": [{"id": "q11-coding", "type": "coding", "difficulty": "medium", "question": "请实现 student_nn11.py 中的 4 个函数; 评测以 test_nn11.py 全部通过为准.", "options": null, "answer": null, "explanation": null}]}$v$,
        NOW(), NOW()
    )
    RETURNING id
)
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, description, match_rule, test_order)
SELECT id, c.case_id, c.input_data, c.expected_output, c.is_hidden, c.description, c.match_rule, c.test_order
FROM new_task,
(VALUES
    ($v$tc_1$v$, $v$test_tsl_textbook$v$, $v$W=[0.5], b=1.0, X=[[10]], y=[8], lr=0.01 yhat=10*0.5+1=6, loss=(8-6)^2/1=4 dW = 2(yhat-y)*X/N = 2*(-2)*10/1 = -40 db = 2(yhat-y)/N = -4 W_new = 0.5 - 0.01*(-40) = 0.9 b_new = 1.0 - 0.01*(-4) = 1.04$v$, false, $v$W=[0.5], b=1.0, X=[[10]], y=[8], lr=0.01 yhat=10*0.5+1=6, loss=(8-6)^2/1=4 dW = 2(yhat-y)*X/N = 2*(-2)*10/1 = -40 db = 2(yhat-y)/N = -4 W_new = 0.5 - 0.01*(-40) = 0.9 b_new = 1.0 - 0.01*(-4) = 1.04$v$, NULL, 1),
    ($v$tc_2$v$, $v$test_tsl_loss_nonzero$v$, $v$非完美预测 → loss > 0 且 W 必须真的更新 (防 identity 不变)$v$, false, $v$非完美预测 → loss > 0 且 W 必须真的更新 (防 identity 不变)$v$, NULL, 2),
    ($v$tc_3$v$, $v$test_tsl_zero_lr$v$, $v$lr=0 → params 不变, loss 仍计算$v$, false, $v$lr=0 → params 不变, loss 仍计算$v$, NULL, 3),
    ($v$tc_4$v$, $v$test_tsl_two_features$v$, $v$W=[1,1], b=0, X=[[1,2]], y=[5], lr=0.1 yhat=3, loss=4 dW = 2*(-2)*[1,2]/1 = [-4, -8] db = -4 W_new = [1.4, 1.8], b_new = 0.4$v$, false, $v$W=[1,1], b=0, X=[[1,2]], y=[5], lr=0.1 yhat=3, loss=4 dW = 2*(-2)*[1,2]/1 = [-4, -8] db = -4 W_new = [1.4, 1.8], b_new = 0.4$v$, NULL, 4),
    ($v$tc_5$v$, $v$test_tsl_batch_two_samples$v$, $v$W=[1], b=0, X=[[1],[2]], y=[2,4] → yhat=[1,2], loss=mean(1+4)/2=2.5 dW = 2*([-1,-2]·[1,2])/2 = 2*(-1-4)/2 = -5 db = 2*(-1-2)/2 = -3 W_new = 1 - 0.1*(-5) = 1.5 b_new = 0 - 0.1*(-3) = 0.3$v$, false, $v$W=[1], b=0, X=[[1],[2]], y=[2,4] → yhat=[1,2], loss=mean(1+4)/2=2.5 dW = 2*([-1,-2]·[1,2])/2 = 2*(-1-4)/2 = -5 db = 2*(-1-2)/2 = -3 W_new = 1 - 0.1*(-5) = 1.5 b_new = 0 - 0.1*(-3) = 0.3$v$, NULL, 5),
    ($v$tc_6$v$, $v$test_tsl_raises_on_dim_mismatch$v$, $v$tsl raises on dim mismatch$v$, false, $v$tsl raises on dim mismatch$v$, NULL, 6),
    ($v$tc_7$v$, $v$test_tsl_raises_on_empty$v$, $v$tsl raises on empty$v$, false, $v$tsl raises on empty$v$, NULL, 7),
    ($v$tc_8$v$, $v$test_tsl_raises_on_non_list$v$, $v$tsl raises on non list$v$, false, $v$tsl raises on non list$v$, NULL, 8),
    ($v$tc_9$v$, $v$test_es_too_short$v$, $v$序列短于 patience+1 → False$v$, false, $v$序列短于 patience+1 → False$v$, NULL, 9),
    ($v$tc_10$v$, $v$test_es_still_improving$v$, $v$val_losses 持续下降 → False$v$, false, $v$val_losses 持续下降 → False$v$, NULL, 10),
    ($v$tc_11$v$, $v$test_es_stagnant$v$, $v$[0.5, 0.4, 0.3, 0.3, 0.3, 0.3] best_before(min[0:3])=0.3 也 best_recent(min[3:])=0.3 diff=0 < min_delta=1e-4 → True$v$, false, $v$[0.5, 0.4, 0.3, 0.3, 0.3, 0.3] best_before(min[0:3])=0.3 也 best_recent(min[3:])=0.3 diff=0 < min_delta=1e-4 → True$v$, NULL, 11),
    ($v$tc_12$v$, $v$test_es_diverging$v$, $v$val 反弹 → True$v$, false, $v$val 反弹 → True$v$, NULL, 12),
    ($v$tc_13$v$, $v$test_es_raises_on_empty$v$, $v$es raises on empty$v$, false, $v$es raises on empty$v$, NULL, 13),
    ($v$tc_14$v$, $v$test_es_raises_on_zero_patience$v$, $v$es raises on zero patience$v$, false, $v$es raises on zero patience$v$, NULL, 14),
    ($v$tc_15$v$, $v$test_es_raises_on_non_list$v$, $v$es raises on non list$v$, false, $v$es raises on non list$v$, NULL, 15),
    ($v$tc_16$v$, $v$test_cvm_perfect$v$, $v$cvm perfect$v$, true, $v$cvm perfect$v$, NULL, 16),
    ($v$tc_17$v$, $v$test_cvm_all_wrong$v$, $v$cvm all wrong$v$, true, $v$cvm all wrong$v$, NULL, 17),
    ($v$tc_18$v$, $v$test_cvm_specific$v$, $v$y=[1,1,0,0,1] pred=[1,0,0,0,1] tp=2 fp=0 tn=2 fn=1 accuracy=4/5=0.8 precision=1.0 recall=2/3≈0.667 f1=0.8 specificity=1.0$v$, true, $v$y=[1,1,0,0,1] pred=[1,0,0,0,1] tp=2 fp=0 tn=2 fn=1 accuracy=4/5=0.8 precision=1.0 recall=2/3≈0.667 f1=0.8 specificity=1.0$v$, NULL, 18),
    ($v$tc_19$v$, $v$test_cvm_imbalanced$v$, $v$y=[0,0,0,0,1] pred=[0,0,0,0,0]: tp=0, fp=0, tn=4, fn=1 accuracy=4/5=0.8, precision=0, recall=0, f1=0, specificity=1.0$v$, true, $v$y=[0,0,0,0,1] pred=[0,0,0,0,0]: tp=0, fp=0, tn=4, fn=1 accuracy=4/5=0.8, precision=0, recall=0, f1=0, specificity=1.0$v$, NULL, 19),
    ($v$tc_20$v$, $v$test_cvm_dict_keys$v$, $v$5 keys 全在$v$, true, $v$5 keys 全在$v$, NULL, 20),
    ($v$tc_21$v$, $v$test_cvm_raises_on_length_mismatch$v$, $v$cvm raises on length mismatch$v$, true, $v$cvm raises on length mismatch$v$, NULL, 21),
    ($v$tc_22$v$, $v$test_cvm_raises_on_invalid_label$v$, $v$cvm raises on invalid label$v$, true, $v$cvm raises on invalid label$v$, NULL, 22),
    ($v$tc_23$v$, $v$test_cvm_raises_on_non_list$v$, $v$cvm raises on non list$v$, true, $v$cvm raises on non list$v$, NULL, 23),
    ($v$tc_24$v$, $v$test_ftl_basic$v$, $v$epoch=0 train=0.69 val=0.68 acc=0.55 f1=0.50$v$, true, $v$epoch=0 train=0.69 val=0.68 acc=0.55 f1=0.50$v$, NULL, 24),
    ($v$tc_25$v$, $v$test_ftl_format_precision$v$, $v$train/val 4 位小数, acc/f1 3 位小数$v$, true, $v$train/val 4 位小数, acc/f1 3 位小数$v$, NULL, 25),
    ($v$tc_26$v$, $v$test_ftl_separator_pipe$v$, $v$字段用 | 分隔$v$, true, $v$字段用 | 分隔$v$, NULL, 26),
    ($v$tc_27$v$, $v$test_ftl_returns_string$v$, $v$返回类型必须 str$v$, true, $v$返回类型必须 str$v$, NULL, 27),
    ($v$tc_28$v$, $v$test_ftl_full_format_string$v$, $v$完整格式严格校验 (防 identity 'Epoch X' 残缺与 shape 全 0 巧合)$v$, true, $v$完整格式严格校验 (防 identity 'Epoch X' 残缺与 shape 全 0 巧合)$v$, NULL, 28),
    ($v$tc_29$v$, $v$test_ftl_raises_on_negative_epoch$v$, $v$ftl raises on negative epoch$v$, true, $v$ftl raises on negative epoch$v$, NULL, 29),
    ($v$tc_30$v$, $v$test_ftl_raises_on_missing_metric$v$, $v$ftl raises on missing metric$v$, true, $v$ftl raises on missing metric$v$, NULL, 30),
    ($v$tc_31$v$, $v$test_ftl_raises_on_non_int_epoch$v$, $v$ftl raises on non int epoch$v$, true, $v$ftl raises on non int epoch$v$, NULL, 31)
) AS c(case_id, input_data, expected_output, is_hidden, description, match_rule, test_order);

COMMIT;
