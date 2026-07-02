import importlib
import os

import pytest


MODULE_NAME = os.environ.get(
    "SPARK11_MODULE", "content_orchestrator.stages_config.spark.student_spark11"
)


def _student():
    return importlib.import_module(MODULE_NAME)


BASE_CONFIG = {
    "appName": "test",
    "master": "yarn",
    "logLevel": "WARN",
    "spark.sql.shuffle.partitions": 200,
    "spark.serializer": "KryoSerializer",
    "spark.executor.memory": "4g",
    "cores": 8,
    "spark.sql.autoBroadcastJoinThreshold": 20971520,
}


CASES = [
    ({"appName": "test", "master": "yarn"}, "config_pairs", None, [["appName", "test"], ["master", "yarn"]]),
    (BASE_CONFIG, "log_level", None, "WARN"),
    (BASE_CONFIG, "shuffle_partitions", None, 200),
    (BASE_CONFIG, "serializer", None, "KryoSerializer"),
    (BASE_CONFIG, "coalesce_partitions", [10, 4], 4),
    (BASE_CONFIG, "repartition_partitions", 12, 12),
    ({"reuse_count": 3, "size_mb": 200, "memory_mb": 512}, "cache_decision", None, True),
    ({"reuse_count": 1, "size_mb": 200, "memory_mb": 512}, "cache_decision", None, False),
    (BASE_CONFIG, "skew_salt_keys", ["hot", 3], ["hot_0", "hot_1", "hot_2"]),
    (BASE_CONFIG, "executor_memory_mb", None, 4096),
    (BASE_CONFIG, "recommended_parallelism", None, 16),
    (BASE_CONFIG, "broadcast_threshold_mb", None, 20),
    (BASE_CONFIG, "unknown", None, {"error": "unsupported_operation"}),
]


@pytest.mark.parametrize("config,operation,param,expected", CASES)
def test_run_performance_operation(config, operation, param, expected):
    assert _student().run_performance_operation(config, operation, param) == expected


def test_rejects_non_dict_config():
    with pytest.raises(TypeError):
        _student().run_performance_operation([], "log_level")


def test_rejects_non_string_operation():
    with pytest.raises(TypeError):
        _student().run_performance_operation({}, None)
