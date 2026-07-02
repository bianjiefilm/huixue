def validate_pipeline_input_schema(stages):
    if not isinstance(stages, list):
        raise TypeError("stages must be list")
    required = {"name", "tool", "output_size_gb"}
    for stage in stages:
        if not isinstance(stage, dict):
            raise TypeError("stage must be dict")
        if not required.issubset(stage):
            return False
        if not isinstance(stage["name"], str) or not isinstance(stage["tool"], str):
            return False
        if stage["output_size_gb"] < 0:
            return False
    return True


def get_tool_for_purpose(purpose):
    mapping = {
        "storage": "hdfs",
        "compute": "mapreduce",
        "scheduling": "yarn",
        "sql": "hive",
        "nosql": "hbase",
        "streaming": "kafka",
        "migration": "sqoop",
    }
    if purpose not in mapping:
        raise ValueError("unknown purpose")
    return mapping[purpose]


def compute_pipeline_total_size(stages):
    if not isinstance(stages, list):
        raise TypeError("stages must be list")
    total = 0.0
    for stage in stages:
        if "output_size_gb" not in stage:
            raise ValueError("missing size")
        size = stage["output_size_gb"]
        if size < 0:
            raise ValueError("negative size")
        total += size
    return total


def combine_bd_pipeline_report(done_stages, total_stages, errors):
    if total_stages <= 0 or done_stages < 0 or done_stages > total_stages:
        raise ValueError("invalid stages")
    total_errors = 0
    for count in errors.values():
        if count < 0:
            raise ValueError("invalid error count")
        total_errors += count
    progress_ratio = done_stages / total_stages
    return {
        "progress_ratio": progress_ratio,
        "total_errors": total_errors,
        "is_success": progress_ratio == 1.0 and total_errors == 0,
    }
