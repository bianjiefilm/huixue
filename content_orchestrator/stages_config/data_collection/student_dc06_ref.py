import json


def evaluate_collection_project(records, total_requests, successful_requests, failed_requests, collection_time_seconds):
    """Evaluate a data collection project."""
    if not isinstance(records, list):
        raise TypeError("records must be a list")
    if not all(isinstance(record, dict) for record in records):
        raise TypeError("each record must be a dict")
    if any(not isinstance(value, (int, float)) for value in (total_requests, successful_requests, failed_requests, collection_time_seconds)):
        raise TypeError("request counts and collection time must be numeric")
    if total_requests < 0 or successful_requests < 0 or failed_requests < 0 or collection_time_seconds < 0:
        raise ValueError("metrics must be non-negative")
    if successful_requests + failed_requests > total_requests:
        raise ValueError("successful_requests + failed_requests cannot exceed total_requests")
    if not records:
        return {
            "quality_report": {"completeness": 0.0, "accuracy": 0.0, "duplicate_rate": 0.0},
            "efficiency_report": {"success_rate": 0.0, "throughput": 0.0},
            "overall_score": 0.0,
        }

    total_fields = sum(len(record) for record in records)
    non_null_fields = sum(1 for record in records for value in record.values() if value is not None)
    valid_fields = sum(
        1
        for record in records
        for value in record.values()
        if value is not None and not (isinstance(value, (int, float)) and value < 0)
    )
    fingerprints = [json.dumps(record, sort_keys=True, ensure_ascii=False) for record in records]
    duplicate_rate = (len(fingerprints) - len(set(fingerprints))) / len(fingerprints) * 100
    completeness = non_null_fields / total_fields * 100 if total_fields else 0.0
    accuracy = valid_fields / total_fields * 100 if total_fields else 0.0
    success_rate = successful_requests / total_requests * 100 if total_requests else 0.0
    throughput = len(records) / collection_time_seconds if collection_time_seconds else 0.0
    throughput_score = min(100.0, throughput * 50)
    overall_score = (completeness + accuracy + success_rate + throughput_score) / 4

    return {
        "quality_report": {
            "completeness": round(completeness, 2),
            "accuracy": round(accuracy, 2),
            "duplicate_rate": round(duplicate_rate, 2),
        },
        "efficiency_report": {
            "success_rate": round(success_rate, 2),
            "throughput": round(throughput, 2),
        },
        "overall_score": round(overall_score, 2),
    }
