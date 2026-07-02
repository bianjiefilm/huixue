import pytest, sys
sys.path.insert(0, '/Users/jimfu/Work/huixue')
from student_mj01 import get_crisp_dm_phases, classify_problem_type, evaluate_classifier, detect_overfitting
import numpy as np

def test_crisp_dm_phases():
    result = get_crisp_dm_phases()
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, list), f"期望 list，实际 {type(result).__name__}"
    assert len(result) == 6, f"应有6个阶段，实际 {len(result)}"
    # 检查关键阶段名
    phases_lower = [p.lower() for p in result]
    assert any('business' in p or '业务' in p for p in phases_lower), "缺少业务理解阶段"
    assert any('model' in p or '建模' in p for p in phases_lower), "缺少建模阶段"

def test_classify_supervised():
    X = np.array([[1, 2], [3, 4], [5, 6], [7, 8]])
    y = np.array([0, 0, 1, 1])
    result = classify_problem_type(X, y)
    assert result is not None, "pass-only 不得分"
    assert result == 'supervised', f"有标签应为 supervised，实际 {result}"

def test_evaluate_classifier():
    y_true = np.array([1, 1, 0, 0, 1])
    y_pred = np.array([1, 0, 0, 0, 1])
    result = evaluate_classifier(y_true, y_pred)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, dict), f"期望 dict，实际 {type(result).__name__}"
    assert all(k in result for k in ['accuracy', 'precision', 'recall', 'f1']), f"缺少指标: {result}"
    assert 0 <= result['accuracy'] <= 1, f"accuracy 应在0~1之间: {result['accuracy']}"

def test_detect_overfitting():
    result = detect_overfitting(0.99, 0.60)
    assert result is not None, "pass-only 不得分"
    assert isinstance(result, dict)
    assert 'is_overfitting' in result and 'gap' in result
    assert result['is_overfitting'] == True, "training=0.99 test=0.60 应判定为过拟合"
    assert result['gap'] == 0.39, f"gap 应为 0.39，实际 {result['gap']}"
