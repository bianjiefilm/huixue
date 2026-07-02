import importlib
import os

import pytest


MODULE_NAME = os.environ.get(
    "SPARK03_MODULE", "content_orchestrator.stages_config.spark.student_spark03"
)


def _student():
    return importlib.import_module(MODULE_NAME)


CASES = [
    ([1, 2, 3, 4, 5], "coalesce_partitions", 2, 2),
    ([("a", 1), ("a", 2), ("b", 5), ("c", 3)], "reduce_by_key_count", None, 3),
    ([("x", 1), ("x", 2), ("y", 3)], "self_join_count", None, 5),
    ([4, 1, 9, 3], "sort_desc_first", None, 9),
    ([1, 2, 3, 3], "union_distinct_count", [3, 4, 5], 5),
    ([1, 2, 3, 4, 5], "map_double_sum", None, 30),
    ([7, 8, 9, 10, 11], "flatmap_triple_count", None, 15),
    ([0, 1, 2, 3, 4, 5, 6, 7], "collect_length", None, 8),
    ([1, 3, 6, 12], "filter_gt_max", 2, 12),
    ([1, 2, 3, 4, 5], "cartesian_count", None, 25),
    ([1, 2, 4, 5, 6, 7], "filter_even_count", None, 3),
    ([9, 2, 7, 4], "take_top_n", 2, [9, 7]),
    ([], "cartesian_count", None, 0),
]


@pytest.mark.parametrize("data,operation,param,expected", CASES)
def test_run_transform_action(data, operation, param, expected):
    assert _student().run_transform_action(data, operation, param) == expected


def test_rejects_non_list_data():
    with pytest.raises(TypeError):
        _student().run_transform_action("1,2,3", "collect_length")


def test_rejects_non_string_operation():
    with pytest.raises(TypeError):
        _student().run_transform_action([], None)
