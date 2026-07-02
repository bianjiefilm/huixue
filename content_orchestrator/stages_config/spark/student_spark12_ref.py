"""Spark12 reference implementation, pure Python."""

import json
from collections import defaultdict


def _require_list(value, name):
    if not isinstance(value, list):
        raise TypeError(f"{name} must be list")


def _require_dict_rows(rows, name):
    _require_list(rows, name)
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError(f"{name} row must be dict")


def _number(value, name):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be number")
    return float(value)


def aggregate_user_purchase_metrics(events):
    _require_dict_rows(events, "events")
    by_user = {}
    for event in events:
        if event.get("event_type") != "purchase":
            continue
        user_id = event.get("user_id")
        if not isinstance(user_id, str) or not user_id:
            raise ValueError("purchase event missing user_id")
        amount = _number(event.get("amount"), "amount")
        if amount < 0:
            raise ValueError("amount must be >= 0")
        item = by_user.setdefault(user_id, {"user_id": user_id, "purchase_count": 0, "total_amount": 0.0})
        item["purchase_count"] += 1
        item["total_amount"] += amount

    result = []
    for user_id, item in by_user.items():
        count = item["purchase_count"]
        total = item["total_amount"]
        result.append(
            {
                "user_id": user_id,
                "purchase_count": count,
                "total_amount": round(total, 6),
                "avg_order_value": round(total / count, 6),
            }
        )
    result.sort(key=lambda r: (-r["total_amount"], r["user_id"]))
    return result


def compute_window_product_sales(events, window_minutes=60, watermark_minutes=120):
    _require_dict_rows(events, "events")
    if not isinstance(window_minutes, int) or isinstance(window_minutes, bool) or window_minutes <= 0:
        raise ValueError("window_minutes must be positive int")
    if not isinstance(watermark_minutes, int) or isinstance(watermark_minutes, bool) or watermark_minutes < 0:
        raise ValueError("watermark_minutes must be non-negative int")
    if not events:
        return []

    event_times = []
    for event in events:
        t = event.get("event_time")
        if not isinstance(t, int) or isinstance(t, bool):
            raise TypeError("event_time must be int")
        event_times.append(t)
    cutoff = max(event_times) - watermark_minutes

    grouped = defaultdict(int)
    for event in events:
        if event.get("event_type") != "purchase":
            continue
        t = event["event_time"]
        if t < cutoff:
            continue
        item_id = event.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("purchase event missing item_id")
        quantity = event.get("quantity")
        if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
            raise ValueError("quantity must be positive int")
        window_start = (t // window_minutes) * window_minutes
        grouped[(window_start, item_id)] += quantity

    result = [
        {"window_start": window_start, "item_id": item_id, "quantity": quantity}
        for (window_start, item_id), quantity in grouped.items()
    ]
    result.sort(key=lambda r: (r["window_start"], -r["quantity"], r["item_id"]))
    return result


def build_recommendation_candidates(events, top_n=3):
    _require_dict_rows(events, "events")
    if not isinstance(top_n, int) or isinstance(top_n, bool) or top_n <= 0:
        raise ValueError("top_n must be positive int")
    if not events:
        return {}

    weights = {"view": 1.0, "cart": 3.0, "purchase": 6.0}
    user_scores = defaultdict(lambda: defaultdict(float))
    global_scores = defaultdict(float)
    purchased = defaultdict(set)
    users = set()

    for event in events:
        user_id = event.get("user_id")
        item_id = event.get("item_id")
        event_type = event.get("event_type")
        if not isinstance(user_id, str) or not user_id:
            raise ValueError("event missing user_id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("event missing item_id")
        users.add(user_id)
        if event_type not in weights:
            continue
        score = weights[event_type]
        user_scores[user_id][item_id] += score
        global_scores[item_id] += score
        if event_type == "purchase":
            purchased[user_id].add(item_id)

    result = {}
    for user_id in sorted(users):
        candidate_scores = defaultdict(float)
        for item_id, score in global_scores.items():
            if item_id not in purchased[user_id]:
                candidate_scores[item_id] += 0.35 * score
        for item_id, score in user_scores[user_id].items():
            if item_id not in purchased[user_id]:
                candidate_scores[item_id] += score
        ordered = sorted(candidate_scores.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]
        result[user_id] = [{"item_id": item_id, "score": round(score, 6)} for item_id, score in ordered]
    return result


def plan_partitioned_output(rows, partition_cols=("dt", "hour")):
    _require_dict_rows(rows, "rows")
    if not isinstance(partition_cols, (list, tuple)):
        raise TypeError("partition_cols must be list or tuple")
    if not partition_cols:
        raise ValueError("partition_cols must not be empty")
    for col in partition_cols:
        if not isinstance(col, str) or not col:
            raise TypeError("partition column must be non-empty str")
    if not rows:
        return []

    partitions = defaultdict(list)
    for row in rows:
        missing = [col for col in partition_cols if col not in row]
        if missing:
            raise ValueError(f"row missing partition cols: {missing}")
        key = tuple((col, row[col]) for col in partition_cols)
        partitions[key].append(row)

    result = []
    for key, part_rows in partitions.items():
        partition = dict(key)
        estimated_size = sum(len(json.dumps(row, sort_keys=True, ensure_ascii=False)) for row in part_rows)
        result.append(
            {
                "partition": partition,
                "row_count": len(part_rows),
                "estimated_size": estimated_size,
            }
        )
    result.sort(key=lambda r: tuple(r["partition"][col] for col in partition_cols))
    return result
