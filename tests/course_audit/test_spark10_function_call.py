import importlib
import os

import pytest


MODULE_NAME = os.environ.get(
    "SPARK10_MODULE", "content_orchestrator.stages_config.spark.student_spark10"
)


def _student():
    return importlib.import_module(MODULE_NAME)


GRAPH = {
    "vertices": [1, 2, 3, 4, 5],
    "edges": [[1, 2], [1, 3], [2, 3], [4, 5]],
    "attrs": {"1": "A", "2": "B", "3": "C", "4": "D", "5": "E", 1: "A", 2: "B", 3: "C", 4: "D", 5: "E"},
}


CASES = [
    (GRAPH, "num_vertices", None, 5),
    (GRAPH, "num_edges", None, 4),
    (GRAPH, "out_degree", 1, 2),
    (GRAPH, "in_degree", 3, 2),
    (GRAPH, "top_out_degree", 2, [[1, 2], [2, 1]]),
    (GRAPH, "triplets", None, ["A->B", "A->C", "B->C", "D->E"]),
    (GRAPH, "connected_components_count", None, 2),
    (GRAPH, "aggregate_messages_length", None, 3),
    (GRAPH, "neighbors", 1, [2, 3]),
    (GRAPH, "has_direct_edge", [4, 5], True),
    ({"vertices": [1, 2, 3], "edges": [[1, 2]]}, "isolated_vertices", None, [3]),
    ({"vertices": [], "edges": []}, "num_edges", None, 0),
    (GRAPH, "unknown", None, {"error": "unsupported_operation"}),
]


@pytest.mark.parametrize("graph,operation,param,expected", CASES)
def test_run_graph_operation(graph, operation, param, expected):
    assert _student().run_graph_operation(graph, operation, param) == expected


def test_rejects_non_dict_graph():
    with pytest.raises(TypeError):
        _student().run_graph_operation([], "num_edges")


def test_rejects_non_string_operation():
    with pytest.raises(TypeError):
        _student().run_graph_operation({}, None)
