def run_performance_operation(config, operation, param=None):
    """Run a Spark performance-optimization style operation."""
    if not isinstance(config, dict):
        raise TypeError("config must be a dict")
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")

    if operation == "config_pairs":
        return [[key, value] for key, value in sorted(config.items())]
    if operation == "log_level":
        return config.get("logLevel", "INFO")
    if operation == "shuffle_partitions":
        return int(config.get("spark.sql.shuffle.partitions", 200))
    if operation == "serializer":
        return config.get("spark.serializer", "JavaSerializer")
    if operation == "coalesce_partitions":
        current, target = param
        return min(current, target)
    if operation == "repartition_partitions":
        return param
    if operation == "cache_decision":
        return config.get("reuse_count", 0) >= 2 and config.get("size_mb", 0) <= config.get("memory_mb", 0)
    if operation == "skew_salt_keys":
        key, salts = param
        return [f"{key}_{index}" for index in range(salts)]
    if operation == "executor_memory_mb":
        value = config.get("spark.executor.memory", "1g")
        return int(value[:-1]) * 1024 if value.endswith("g") else int(value[:-1])
    if operation == "recommended_parallelism":
        return config.get("cores", 1) * 2
    if operation == "broadcast_threshold_mb":
        return int(config.get("spark.sql.autoBroadcastJoinThreshold", 10485760) / 1024 / 1024)
    return {"error": "unsupported_operation"}
