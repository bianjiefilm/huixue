"""NN11 evaluator (v2)."""
import sys
import pytest

sys.path.insert(0, '/Users/jimfu/Work/huixue')

from student_nn11 import (
    train_step_linear,
    early_stopping_check,
    compute_validation_metrics,
    format_training_log,
)

TOL = 1e-4


# F1: train_step_linear
def test_tsl_textbook():
    """W=[0.5], b=1.0, X=[[10]], y=[8], lr=0.01
    yhat=10*0.5+1=6, loss=(8-6)^2/1=4
    dW = 2(yhat-y)*X/N = 2*(-2)*10/1 = -40
    db = 2(yhat-y)/N = -4
    W_new = 0.5 - 0.01*(-40) = 0.9
    b_new = 1.0 - 0.01*(-4) = 1.04"""
    W_new, b_new, loss = train_step_linear([0.5], 1.0, [[10]], [8.0], 0.01)
    assert abs(W_new[0] - 0.9) < TOL
    assert abs(b_new - 1.04) < TOL
    assert abs(loss - 4.0) < TOL

def test_tsl_loss_nonzero():
    """非完美预测 → loss > 0 且 W 必须真的更新 (防 identity 不变)"""
    W_new, b_new, loss = train_step_linear([1.0], 0.0, [[1]], [3.0], 0.5)
    # yhat=1, loss=4, dW = 2*(-2)/1 = -4, W_new = 1 - 0.5*(-4) = 3.0
    # db = -4, b_new = 0 - 0.5*(-4) = 2.0
    assert abs(loss - 4.0) < TOL
    assert abs(W_new[0] - 3.0) < TOL
    assert abs(b_new - 2.0) < TOL

def test_tsl_zero_lr():
    """lr=0 → params 不变, loss 仍计算"""
    W_new, b_new, loss = train_step_linear([0.5], 0.0, [[10]], [8.0], 0.0)
    assert abs(W_new[0] - 0.5) < TOL
    assert abs(b_new - 0.0) < TOL
    # yhat=5, loss=9
    assert abs(loss - 9.0) < TOL

def test_tsl_two_features():
    """W=[1,1], b=0, X=[[1,2]], y=[5], lr=0.1
    yhat=3, loss=4
    dW = 2*(-2)*[1,2]/1 = [-4, -8]
    db = -4
    W_new = [1.4, 1.8], b_new = 0.4"""
    W_new, b_new, loss = train_step_linear([1.0, 1.0], 0.0, [[1, 2]], [5.0], 0.1)
    assert abs(loss - 4.0) < TOL
    assert abs(W_new[0] - 1.4) < TOL
    assert abs(W_new[1] - 1.8) < TOL
    assert abs(b_new - 0.4) < TOL

def test_tsl_batch_two_samples():
    """W=[1], b=0, X=[[1],[2]], y=[2,4] → yhat=[1,2], loss=mean(1+4)/2=2.5
    dW = 2*([-1,-2]·[1,2])/2 = 2*(-1-4)/2 = -5
    db = 2*(-1-2)/2 = -3
    W_new = 1 - 0.1*(-5) = 1.5
    b_new = 0 - 0.1*(-3) = 0.3"""
    W_new, b_new, loss = train_step_linear([1.0], 0.0, [[1], [2]], [2.0, 4.0], 0.1)
    assert abs(loss - 2.5) < TOL
    assert abs(W_new[0] - 1.5) < TOL
    assert abs(b_new - 0.3) < TOL

def test_tsl_raises_on_dim_mismatch():
    with pytest.raises(ValueError):
        train_step_linear([1.0, 2.0], 0.0, [[1]], [2.0], 0.1)

def test_tsl_raises_on_empty():
    with pytest.raises(ValueError):
        train_step_linear([], 0.0, [], [], 0.1)

def test_tsl_raises_on_non_list():
    with pytest.raises(TypeError):
        train_step_linear("ab", 0.0, [[1]], [2.0], 0.1)


# F2: early_stopping_check
def test_es_too_short():
    """序列短于 patience+1 → False"""
    assert early_stopping_check([0.5, 0.4], patience=5) is False

def test_es_still_improving():
    """val_losses 持续下降 → False"""
    assert early_stopping_check([0.6, 0.5, 0.4, 0.3, 0.2, 0.1], patience=3) is False

def test_es_stagnant():
    """[0.5, 0.4, 0.3, 0.3, 0.3, 0.3] best_before(min[0:3])=0.3 也 best_recent(min[3:])=0.3
    diff=0 < min_delta=1e-4 → True"""
    assert early_stopping_check([0.5, 0.4, 0.3, 0.3, 0.3, 0.3], patience=3) is True

def test_es_diverging():
    """val 反弹 → True"""
    assert early_stopping_check([0.5, 0.4, 0.3, 0.4, 0.5, 0.6], patience=3) is True

def test_es_raises_on_empty():
    with pytest.raises(ValueError):
        early_stopping_check([], patience=3)

def test_es_raises_on_zero_patience():
    with pytest.raises(ValueError):
        early_stopping_check([0.5, 0.4], patience=0)

def test_es_raises_on_non_list():
    with pytest.raises(TypeError):
        early_stopping_check("ab", patience=3)


# F3: compute_validation_metrics
def test_cvm_perfect():
    r = compute_validation_metrics([1, 1, 0, 0], [1, 1, 0, 0])
    for k in ["accuracy", "precision", "recall", "f1", "specificity"]:
        assert abs(r[k] - 1.0) < TOL

def test_cvm_all_wrong():
    r = compute_validation_metrics([1, 1, 0, 0], [0, 0, 1, 1])
    for k in ["accuracy", "precision", "recall", "f1", "specificity"]:
        assert abs(r[k] - 0.0) < TOL

def test_cvm_specific():
    """y=[1,1,0,0,1] pred=[1,0,0,0,1]
    tp=2 fp=0 tn=2 fn=1
    accuracy=4/5=0.8 precision=1.0 recall=2/3≈0.667 f1=0.8 specificity=1.0"""
    r = compute_validation_metrics([1, 1, 0, 0, 1], [1, 0, 0, 0, 1])
    assert abs(r["accuracy"] - 0.8) < TOL
    assert abs(r["precision"] - 1.0) < TOL
    assert abs(r["recall"] - 2 / 3) < TOL
    assert abs(r["f1"] - 0.8) < TOL
    assert abs(r["specificity"] - 1.0) < TOL

def test_cvm_imbalanced():
    """y=[0,0,0,0,1] pred=[0,0,0,0,0]: tp=0, fp=0, tn=4, fn=1
    accuracy=4/5=0.8, precision=0, recall=0, f1=0, specificity=1.0"""
    r = compute_validation_metrics([0, 0, 0, 0, 1], [0, 0, 0, 0, 0])
    assert abs(r["accuracy"] - 0.8) < TOL
    assert abs(r["precision"] - 0.0) < TOL
    assert abs(r["specificity"] - 1.0) < TOL

def test_cvm_dict_keys():
    """5 keys 全在"""
    r = compute_validation_metrics([1, 0], [1, 0])
    assert set(r.keys()) == {"accuracy", "precision", "recall", "f1", "specificity"}

def test_cvm_raises_on_length_mismatch():
    with pytest.raises(ValueError):
        compute_validation_metrics([1, 0], [1])

def test_cvm_raises_on_invalid_label():
    with pytest.raises(ValueError):
        compute_validation_metrics([1, 2], [1, 0])

def test_cvm_raises_on_non_list():
    with pytest.raises(TypeError):
        compute_validation_metrics("ab", "ab")


# F4: format_training_log
def test_ftl_basic():
    """epoch=0 train=0.69 val=0.68 acc=0.55 f1=0.50"""
    log = format_training_log(0, 0.69, 0.68, {"accuracy": 0.55, "f1": 0.50})
    assert "Epoch 0" in log
    assert "train_loss=0.6900" in log
    assert "val_loss=0.6800" in log
    assert "acc=0.550" in log
    assert "f1=0.500" in log

def test_ftl_format_precision():
    """train/val 4 位小数, acc/f1 3 位小数"""
    log = format_training_log(10, 0.123456, 0.234567,
                              {"accuracy": 0.892345, "f1": 0.901234})
    assert "train_loss=0.1235" in log
    assert "val_loss=0.2346" in log
    assert "acc=0.892" in log
    assert "f1=0.901" in log

def test_ftl_separator_pipe():
    """字段用 | 分隔"""
    log = format_training_log(5, 0.5, 0.5, {"accuracy": 0.5, "f1": 0.5})
    assert log.count("|") >= 4  # 4 个分隔符 → 5 个字段

def test_ftl_returns_string():
    """返回类型必须 str"""
    log = format_training_log(0, 0.5, 0.5, {"accuracy": 0.5, "f1": 0.5})
    assert isinstance(log, str)

def test_ftl_full_format_string():
    """完整格式严格校验 (防 identity 'Epoch X' 残缺与 shape 全 0 巧合)"""
    log = format_training_log(7, 0.3456, 0.4123, {"accuracy": 0.756, "f1": 0.701})
    expected = "Epoch 7 | train_loss=0.3456 | val_loss=0.4123 | acc=0.756 | f1=0.701"
    assert log == expected

def test_ftl_raises_on_negative_epoch():
    with pytest.raises(ValueError):
        format_training_log(-1, 0.5, 0.5, {"accuracy": 0.5, "f1": 0.5})

def test_ftl_raises_on_missing_metric():
    with pytest.raises(ValueError):
        format_training_log(0, 0.5, 0.5, {"accuracy": 0.5})

def test_ftl_raises_on_non_int_epoch():
    with pytest.raises(TypeError):
        format_training_log("0", 0.5, 0.5, {"accuracy": 0.5, "f1": 0.5})
