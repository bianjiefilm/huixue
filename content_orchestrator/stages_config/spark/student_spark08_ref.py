def run_structured_streaming_operation(events, operation, param=None):
    """Run a Structured Streaming-style operation on event dictionaries."""
    if not isinstance(events, list):
        raise TypeError("events must be a list")
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")

    if operation == "is_streaming":
        return True
    if operation == "watermark_count_by_key":
        cutoff = param
        counts = {}
        for event in events:
            if event["minute"] >= cutoff:
                counts[event["key"]] = counts.get(event["key"], 0) + 1
        return dict(sorted(counts.items()))
    if operation == "start_query":
        return {"format": param["format"], "mode": param["mode"], "started": True}
    if operation == "trigger_interval":
        return f"ProcessingTime({param} seconds)"
    if operation == "await_status":
        return "TERMINATED" if param else "ACTIVE"
    if operation == "left_outer_join_streaming":
        ids = {event["id"] for event in events}
        return [{"id": row["id"], "matched": row["id"] in ids} for row in param]
    if operation == "query_status_message":
        return "ACTIVE" if events else "IDLE"
    if operation == "output_mode":
        return f"{param} mode set"
    if operation == "kafka_source":
        return {"source": "kafka", "topic": param, "loaded": True}
    if operation == "checkpoint_enabled":
        return bool(param and str(param).startswith("/"))
    if operation == "stop_is_active":
        return False
    if operation == "append_recent_values":
        return [event["value"] for event in events if event["minute"] >= param]
    return {"error": "unsupported_operation"}
