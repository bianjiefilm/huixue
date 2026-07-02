import importlib
import os

import pytest


MODULE_NAME = os.environ.get(
    "SPARK09_MODULE", "content_orchestrator.stages_config.spark.student_spark09"
)


def _student():
    return importlib.import_module(MODULE_NAME)


CASES = [
    ([{"x": 1}], "train_status", None, "model trained"),
    ([[1, 2], [3, 4], [5, 6]], "kmeans_center_count", 3, 3),
    ([{"label": "B"}, {"label": "A"}, {"label": "C"}, {"label": "A"}], "string_indexer_labels", None, ["A", "B", "C"]),
    ([{"text": "a"}], "pipeline_stage_count", ["tokenizer", "lr"], 2),
    ([{"user": 1}], "als_rank", {"rank": 10, "maxIter": 5}, 10),
    ([{"x": 2, "y": 3}], "vector_assemble_first", ["x", "y"], [2.0, 3.0]),
    ([{"v": 2}, {"v": 4}, {"v": 6}], "minmax_scale", "v", [0.0, 0.5, 1.0]),
    ([{"score": 0.2}, {"score": 0.8}], "threshold_predict", {"feature": "score", "threshold": 0.5}, [0, 1]),
    ([{"label": 1, "prediction": 1}, {"label": 0, "prediction": 1}, {"label": 0, "prediction": 0}], "accuracy", None, 0.6667),
    ([{"user": 7, "item": "A", "score": 0.2}, {"user": 7, "item": "B", "score": 0.9}], "top_recommendation", 7, "B"),
    ([[1, 2, 3], [4, 5, 6]], "dot_similarity", None, 32),
    ([], "train_status", None, "no data"),
    ([{"x": 1}], "unknown", None, {"error": "unsupported_operation"}),
]


@pytest.mark.parametrize("data,operation,param,expected", CASES)
def test_run_mllib_operation(data, operation, param, expected):
    assert _student().run_mllib_operation(data, operation, param) == expected


def test_rejects_non_list_data():
    with pytest.raises(TypeError):
        _student().run_mllib_operation({"x": 1}, "train_status")


def test_rejects_non_string_operation():
    with pytest.raises(TypeError):
        _student().run_mllib_operation([], None)
