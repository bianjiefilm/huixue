"""Spark12 综合关 pytest_module 测试.

31 cases, pure Python. The student module must be named ``student_spark12``.
"""

import json

import pytest

from student_spark12 import (
    aggregate_user_purchase_metrics,
    build_recommendation_candidates,
    compute_window_product_sales,
    plan_partitioned_output,
)


TOL = 1e-6


def _events(seed_shift=0):
    base = [
        {"user_id": "u1", "item_id": "sku1", "event_type": "view", "event_time": 5, "amount": 0.0, "quantity": 1, "dt": "2026-04-30", "hour": "09"},
        {"user_id": "u1", "item_id": "sku2", "event_type": "cart", "event_time": 8, "amount": 0.0, "quantity": 1, "dt": "2026-04-30", "hour": "09"},
        {"user_id": "u1", "item_id": "sku2", "event_type": "purchase", "event_time": 14, "amount": 120.0, "quantity": 2, "dt": "2026-04-30", "hour": "09"},
        {"user_id": "u2", "item_id": "sku1", "event_type": "purchase", "event_time": 59, "amount": 50.0, "quantity": 1, "dt": "2026-04-30", "hour": "09"},
        {"user_id": "u2", "item_id": "sku3", "event_type": "purchase", "event_time": 60, "amount": 80.0, "quantity": 1, "dt": "2026-04-30", "hour": "10"},
        {"user_id": "u3", "item_id": "sku3", "event_type": "view", "event_time": 64, "amount": 0.0, "quantity": 1, "dt": "2026-04-30", "hour": "10"},
        {"user_id": "u3", "item_id": "sku4", "event_type": "cart", "event_time": 70, "amount": 0.0, "quantity": 1, "dt": "2026-04-30", "hour": "10"},
        {"user_id": "u4", "item_id": "sku4", "event_type": "purchase", "event_time": 130, "amount": 200.0, "quantity": 3, "dt": "2026-04-30", "hour": "11"},
        {"user_id": "u4", "item_id": "sku5", "event_type": "purchase", "event_time": 131, "amount": 90.0, "quantity": 1, "dt": "2026-04-30", "hour": "11"},
        {"user_id": "u5", "item_id": "sku5", "event_type": "refund", "event_time": 150, "amount": 90.0, "quantity": 1, "dt": "2026-04-30", "hour": "11"},
        {"user_id": "u6", "item_id": "sku6", "event_type": "purchase", "event_time": 300, "amount": 300.0, "quantity": 4, "dt": "2026-04-30", "hour": "14"},
        {"user_id": "u7", "item_id": "sku7", "event_type": "view", "event_time": 310, "amount": 0.0, "quantity": 1, "dt": "2026-04-30", "hour": "14"},
    ]
    if seed_shift:
        shifted = []
        for row in base:
            r = dict(row)
            r["user_id"] = f"{r['user_id']}_s{seed_shift}"
            r["item_id"] = f"{r['item_id']}_s{seed_shift}"
            r["event_time"] += seed_shift
            shifted.append(r)
        return shifted
    return base


def _partition_size(rows):
    return sum(len(json.dumps(row, sort_keys=True, ensure_ascii=False)) for row in rows)


# F1 aggregate_user_purchase_metrics: 7 cases


def test_aup_basic_metrics():
    rows = aggregate_user_purchase_metrics(_events())
    by_user = {r["user_id"]: r for r in rows}
    assert by_user["u1"]["purchase_count"] == 1
    assert abs(by_user["u1"]["total_amount"] - 120.0) < TOL
    assert by_user["u4"]["purchase_count"] == 2
    assert abs(by_user["u4"]["total_amount"] - 290.0) < TOL
    shifted = aggregate_user_purchase_metrics(_events(seed_shift=7))
    shifted_by_user = {r["user_id"]: r for r in shifted}
    assert shifted_by_user["u1_s7"]["purchase_count"] == 1
    assert abs(shifted_by_user["u4_s7"]["total_amount"] - 290.0) < TOL


def test_aup_ignores_non_purchase():
    rows = aggregate_user_purchase_metrics(_events())
    assert "u3" not in {r["user_id"] for r in rows}
    assert "u5" not in {r["user_id"] for r in rows}
    shifted = aggregate_user_purchase_metrics(_events(seed_shift=2))
    shifted_ids = {r["user_id"] for r in shifted}
    assert "u3_s2" not in shifted_ids
    assert all(uid.endswith("_s2") for uid in shifted_ids)


def test_aup_sorting():
    rows = aggregate_user_purchase_metrics(_events())
    assert [r["user_id"] for r in rows[:3]] == ["u6", "u4", "u2"]
    shifted = aggregate_user_purchase_metrics(_events(seed_shift=5))
    assert [r["user_id"] for r in shifted[:3]] == ["u6_s5", "u4_s5", "u2_s5"]


def test_aup_empty():
    assert aggregate_user_purchase_metrics([]) == []


def test_aup_avg_order_value():
    rows = aggregate_user_purchase_metrics(_events())
    u4 = [r for r in rows if r["user_id"] == "u4"][0]
    assert abs(u4["avg_order_value"] - 145.0) < TOL
    shifted = aggregate_user_purchase_metrics(_events(seed_shift=6))
    u4_shifted = [r for r in shifted if r["user_id"] == "u4_s6"][0]
    assert abs(u4_shifted["avg_order_value"] - 145.0) < TOL


def test_aup_raises_on_non_list():
    with pytest.raises(TypeError):
        aggregate_user_purchase_metrics("not events")


def test_aup_raises_on_bad_amount():
    bad = _events() + [{"user_id": "u8", "item_id": "sku8", "event_type": "purchase", "event_time": 1, "amount": -1, "quantity": 1}]
    with pytest.raises(ValueError):
        aggregate_user_purchase_metrics(bad)


# F2 compute_window_product_sales: 8 cases


def test_cwps_basic_window():
    rows = compute_window_product_sales(_events(), window_minutes=60, watermark_minutes=400)
    by_key = {(r["window_start"], r["item_id"]): r["quantity"] for r in rows}
    assert by_key[(0, "sku2")] == 2
    assert by_key[(0, "sku1")] == 1
    shifted = compute_window_product_sales(_events(seed_shift=7), window_minutes=60, watermark_minutes=400)
    shifted_by_key = {(r["window_start"], r["item_id"]): r["quantity"] for r in shifted}
    assert shifted_by_key[(0, "sku2_s7")] == 2
    assert shifted_by_key[(60, "sku1_s7")] == 1


def test_cwps_multiple_items():
    rows = compute_window_product_sales(_events(), window_minutes=60, watermark_minutes=400)
    win60 = [r for r in rows if r["window_start"] == 60]
    assert {r["item_id"] for r in win60} == {"sku3"}
    shifted = compute_window_product_sales(_events(seed_shift=7), window_minutes=60, watermark_minutes=400)
    shifted_win60 = [r for r in shifted if r["window_start"] == 60]
    assert {r["item_id"] for r in shifted_win60} == {"sku1_s7", "sku3_s7"}


def test_cwps_watermark_filters_late():
    rows = compute_window_product_sales(_events(), window_minutes=60, watermark_minutes=120)
    keys = {(r["window_start"], r["item_id"]) for r in rows}
    assert (0, "sku2") not in keys
    assert (300, "sku6") in keys


def test_cwps_ignores_non_purchase():
    rows = compute_window_product_sales(_events(), window_minutes=60, watermark_minutes=400)
    assert "sku7" not in {r["item_id"] for r in rows}


def test_cwps_sorting():
    rows = compute_window_product_sales(_events(), window_minutes=60, watermark_minutes=400)
    assert rows[0]["window_start"] == 0
    win0 = [r for r in rows if r["window_start"] == 0]
    assert [r["quantity"] for r in win0] == sorted([r["quantity"] for r in win0], reverse=True)
    shifted = compute_window_product_sales(_events(seed_shift=11), window_minutes=60, watermark_minutes=400)
    assert shifted[0]["window_start"] == 0
    assert all(r["item_id"].endswith("_s11") for r in shifted)


def test_cwps_boundary_event_on_window_edge():
    rows = compute_window_product_sales(_events(), window_minutes=60, watermark_minutes=400)
    by_key = {(r["window_start"], r["item_id"]): r["quantity"] for r in rows}
    assert (60, "sku3") in by_key
    assert (0, "sku3") not in by_key
    shifted = compute_window_product_sales(_events(seed_shift=7), window_minutes=60, watermark_minutes=400)
    shifted_by_key = {(r["window_start"], r["item_id"]): r["quantity"] for r in shifted}
    assert (60, "sku3_s7") in shifted_by_key
    assert (0, "sku3_s7") not in shifted_by_key


def test_cwps_raises_bad_window():
    with pytest.raises(ValueError):
        compute_window_product_sales(_events(), window_minutes=0)


def test_cwps_raises_bad_quantity():
    bad = _events() + [{"user_id": "u9", "item_id": "sku9", "event_type": "purchase", "event_time": 10, "amount": 1.0, "quantity": 0}]
    with pytest.raises(ValueError):
        compute_window_product_sales(bad, watermark_minutes=400)


# F3 build_recommendation_candidates: 8 cases


def test_brc_returns_dict():
    recs = build_recommendation_candidates(_events())
    assert isinstance(recs, dict)
    assert "u1" in recs and recs["u1"]
    shifted = build_recommendation_candidates(_events(seed_shift=3))
    assert "u1_s3" in shifted and shifted["u1_s3"]


def test_brc_top_n_limit():
    recs = build_recommendation_candidates(_events(), top_n=2)
    assert recs
    assert all(0 < len(v) <= 2 for v in recs.values())
    shifted = build_recommendation_candidates(_events(seed_shift=5), top_n=2)
    assert shifted
    assert all(uid.endswith("_s5") for uid in shifted)


def test_brc_excludes_purchased():
    recs = build_recommendation_candidates(_events(), top_n=5)
    assert "sku2" not in [r["item_id"] for r in recs["u1"]]


def test_brc_score_ordering():
    recs = build_recommendation_candidates(_events(), top_n=4)
    for items in recs.values():
        scores = [x["score"] for x in items]
        assert scores == sorted(scores, reverse=True)
    shifted = build_recommendation_candidates(_events(seed_shift=8), top_n=4)
    assert all(item["item_id"].endswith("_s8") for items in shifted.values() for item in items)


def test_brc_user_specific():
    recs = build_recommendation_candidates(_events(), top_n=3)
    assert recs["u1"] != recs["u3"]
    shifted = build_recommendation_candidates(_events(seed_shift=4), top_n=3)
    assert shifted["u1_s4"] != shifted["u3_s4"]


def test_brc_empty():
    assert build_recommendation_candidates([]) == {}


def test_brc_uses_global_popularity_for_sparse_user():
    recs = build_recommendation_candidates(_events(), top_n=3)
    assert "u7" in recs
    assert len(recs["u7"]) >= 1


def test_brc_raises_bad_top_n():
    with pytest.raises(ValueError):
        build_recommendation_candidates(_events(), top_n=0)


# F4 plan_partitioned_output: 8 cases


def test_ppo_basic_dt_hour():
    rows = plan_partitioned_output(_events())
    assert {"dt": "2026-04-30", "hour": "09"} in [r["partition"] for r in rows]
    shifted = plan_partitioned_output(_events(seed_shift=8), partition_cols=("user_id",))
    assert {"user_id": "u1_s8"} in [r["partition"] for r in shifted]


def test_ppo_counts():
    rows = plan_partitioned_output(_events())
    by_part = {tuple(sorted(r["partition"].items())): r for r in rows}
    assert by_part[(("dt", "2026-04-30"), ("hour", "09"))]["row_count"] == 4
    shifted = plan_partitioned_output(_events(seed_shift=8), partition_cols=("user_id",))
    shifted_by_part = {tuple(sorted(r["partition"].items())): r for r in shifted}
    assert shifted_by_part[(("user_id", "u1_s8"),)]["row_count"] == 3


def test_ppo_estimated_size():
    rows = plan_partitioned_output(_events())
    assert rows
    assert all(r["estimated_size"] > 0 for r in rows)
    shifted = plan_partitioned_output(_events(seed_shift=9), partition_cols=("dt",))
    assert shifted[0]["estimated_size"] == _partition_size(_events(seed_shift=9))


def test_ppo_estimated_size_uses_json_bytes():
    source = _events()
    rows = plan_partitioned_output(source)
    part_rows = [r for r in source if r["hour"] == "09"]
    p09 = [r for r in rows if r["partition"] == {"dt": "2026-04-30", "hour": "09"}][0]
    assert p09["estimated_size"] == _partition_size(part_rows)


def test_ppo_custom_partition():
    rows = plan_partitioned_output(_events(), partition_cols=("dt",))
    assert rows == [{"partition": {"dt": "2026-04-30"}, "row_count": 12, "estimated_size": _partition_size(_events())}]
    shifted = plan_partitioned_output(_events(seed_shift=9), partition_cols=("dt",))
    assert shifted == [{"partition": {"dt": "2026-04-30"}, "row_count": 12, "estimated_size": _partition_size(_events(seed_shift=9))}]


def test_ppo_empty():
    assert plan_partitioned_output([]) == []


def test_ppo_raises_missing_partition():
    with pytest.raises(ValueError):
        plan_partitioned_output([{"dt": "2026-04-30"}])


def test_ppo_raises_non_list():
    with pytest.raises(TypeError):
        plan_partitioned_output("not rows")
