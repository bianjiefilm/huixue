import importlib
import os
import pytest

student = importlib.import_module(os.environ.get("STUDENT_MODULE", "student_edu05"))

RAW = [
    {"student_id":"S1","course":"math","score":95,"completion":1.1,"minutes":80,"grade":"G1"},
    {"student_id":"S1","course":"english","score":70,"completion":0.8,"minutes":40,"grade":"G1"},
    {"student_id":"S2","course":"math","score":45,"completion":0.45,"minutes":20,"grade":"G1"},
    {"student_id":"S2","course":"english","score":"55","completion":0.5,"minutes":15,"grade":"G1"},
    {"student_id":"S3","course":"math","score":78,"completion":0.9,"minutes":35,"grade":"G2"},
    {"student_id":"S3","course":"english","score":82,"completion":0.95,"minutes":45,"grade":"G2"},
    {"student_id":"","course":"bad","score":100},
]
PATHS = [
    {"path_id":"P_math","target_courses":["math"],"base_priority":5},
    {"path_id":"P_eng","target_courses":["english"],"base_priority":4},
    {"path_id":"P_general","target_courses":[],"base_priority":2},
]

def clean():
    return student.load_and_clean_school_records(RAW)

def test_clean_count_and_sort():
    rows = clean()
    assert len(rows) == 6
    assert rows[0]["student_id"] == "S1" and rows[0]["completion"] == 0.8

def test_clean_clamps_values():
    rows = clean()
    math = [r for r in rows if r["student_id"] == "S1" and r["course"] == "math"][0]
    assert math["completion"] == 1.0 and math["score"] == 95.0

def test_clean_rejects_non_list():
    with pytest.raises(ValueError): student.load_and_clean_school_records({})

def test_course_insight_count():
    assert len(student.build_course_insights(clean())) == 2

def test_course_insight_math_metrics():
    row = [r for r in student.build_course_insights(clean()) if r["course"] == "math"][0]
    assert row["student_count"] == 3
    assert abs(row["avg_score"] - 72.67) < 0.01
    assert row["active_rate"] == 0.6667

def test_course_insight_sorted():
    rows = student.build_course_insights(clean())
    assert rows[0]["avg_score"] >= rows[1]["avg_score"]

def test_risk_count_and_order():
    rows = student.score_student_risk(clean())
    assert len(rows) == 3 and rows[0]["student_id"] == "S2"

def test_high_risk_detected():
    row = student.score_student_risk(clean())[0]
    assert row["risk_level"] == "high"
    assert row["weak_courses"] == ["english", "math"]

def test_low_risk_detected():
    row = [r for r in student.score_student_risk(clean()) if r["student_id"] == "S3"][0]
    assert row["risk_level"] == "low"

def test_medium_or_low_threshold():
    rows = student.score_student_risk([{"student_id":"S","course":"c","score":65,"completion":0.7,"minutes":80}])
    assert rows[0]["risk_level"] in {"medium", "low"}

def test_recommendation_count():
    recs = student.recommend_learning_paths(student.score_student_risk(clean()), PATHS)
    assert len(recs) == 3
    assert all(len(r["recommendations"]) == 2 for r in recs)

def test_recommend_high_risk_priority_bonus():
    risk = [{"student_id":"S","risk_level":"high","weak_courses":["math"]}]
    rec = student.recommend_learning_paths(risk, PATHS)[0]["recommendations"][0]
    assert rec["path_id"] == "P_math" and rec["priority"] == 35.0

def test_recommend_rejects_bad_inputs():
    with pytest.raises(ValueError): student.recommend_learning_paths({}, PATHS)

def test_recommend_ignores_bad_catalog():
    recs = student.recommend_learning_paths([{"student_id":"S","risk_level":"low","weak_courses":[]}], ["bad", {}, PATHS[0]])
    assert recs[0]["recommendations"][0]["path_id"] == "P_math"

def test_report_core_counts():
    rows = clean(); risks = student.score_student_risk(rows); recs = student.recommend_learning_paths(risks, PATHS)
    report = student.summarize_campus_report(rows, risks, recs)
    assert report["student_count"] == 3 and report["course_count"] == 2

def test_report_risk_counts():
    rows = clean(); risks = student.score_student_risk(rows); recs = student.recommend_learning_paths(risks, PATHS)
    report = student.summarize_campus_report(rows, risks, recs)
    assert report["high_risk_students"] == 1 and report["medium_risk_students"] >= 0

def test_report_recommendation_count():
    rows = clean(); risks = student.score_student_risk(rows); recs = student.recommend_learning_paths(risks, PATHS)
    assert student.summarize_campus_report(rows, risks, recs)["recommendation_count"] == 6

def test_report_status_urgent():
    report = student.summarize_campus_report([{"student_id":"S","course":"c"}], [{"risk_level":"high"}], [])
    assert report["campus_status"] == "urgent"

def test_report_status_watch():
    report = student.summarize_campus_report([{"student_id":"S","course":"c"}], [{"risk_level":"low"}, {"risk_level":"high"}, {"risk_level":"low"}, {"risk_level":"low"}], [])
    assert report["campus_status"] == "watch"

def test_report_status_stable():
    assert student.summarize_campus_report([], [], [])["campus_status"] == "stable"

def test_end_to_end_flow():
    rows = clean(); insights = student.build_course_insights(rows); risks = student.score_student_risk(rows); recs = student.recommend_learning_paths(risks, PATHS); report = student.summarize_campus_report(rows, risks, recs)
    assert len(insights) == 2 and report["recommendation_count"] == 6

def test_course_insight_empty():
    assert student.build_course_insights([]) == []

def test_risk_empty():
    assert student.score_student_risk([]) == []

def test_recommend_empty():
    assert student.recommend_learning_paths([], PATHS) == []

def test_bad_rows_do_not_crash():
    assert student.load_and_clean_school_records(["bad", {}, {"student_id":"S", "course":"c"}])[0]["score"] == 0.0

def test_report_handles_bad_rows():
    report = student.summarize_campus_report(["bad", {"student_id":"S","course":"c"}], ["bad"], ["bad"])
    assert report["student_count"] == 1 and report["course_count"] == 1

def test_risk_weak_course_sorting():
    row = student.score_student_risk([{"student_id":"S","course":"z","score":50,"completion":1,"minutes":40}, {"student_id":"S","course":"a","score":90,"completion":0.5,"minutes":40}])[0]
    assert row["weak_courses"] == ["a", "z"]

def test_clean_string_numbers():
    row = student.load_and_clean_school_records([{"student_id":"S","course":"c","score":"88","completion":"0.8","minutes":"30"}])[0]
    assert row["score"] == 88.0 and row["completion"] == 0.8

def test_recommend_sort_tie_path_id():
    rec = student.recommend_learning_paths([{"student_id":"S","risk_level":"low","weak_courses":[]}], [{"path_id":"B"}, {"path_id":"A"}])[0]
    assert [r["path_id"] for r in rec["recommendations"]] == ["A", "B"]

def test_report_medium_count():
    assert student.summarize_campus_report([], [{"risk_level":"medium"}], [])["medium_risk_students"] == 1
