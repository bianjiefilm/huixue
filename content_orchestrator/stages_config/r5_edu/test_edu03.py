import importlib, os, pytest
student = importlib.import_module(os.environ.get("STUDENT_MODULE", "student_edu03"))
DATA = [
 {"student_id":"S1","avg_score":55,"completion_rate":0.55,"attendance_rate":0.7,"late_submissions":6,"score_trend":-8},
 {"student_id":"S2","avg_score":76,"completion_rate":0.82,"attendance_rate":0.9,"late_submissions":1,"score_trend":1},
 {"student_id":"S3","avg_score":68,"completion_rate":0.72,"attendance_rate":0.83,"late_submissions":2,"score_trend":-2},
]

def test_fields_and_count():
    res = student.predict_academic_risk(DATA)
    assert len(res) == 3 and set(res[0]) == {"student_id","risk_score","risk_level","recommended_actions"}

def test_high_risk_sorted_first():
    res = student.predict_academic_risk(DATA)
    assert res[0]["student_id"] == "S1" and res[0]["risk_level"] == "high"

def test_low_risk_regular_observation():
    row = [r for r in student.predict_academic_risk(DATA) if r["student_id"] == "S2"][0]
    assert row["risk_level"] == "low" and row["recommended_actions"] == ["保持常规观察"]

def test_medium_risk():
    row = [r for r in student.predict_academic_risk(DATA) if r["student_id"] == "S3"][0]
    assert row["risk_level"] in {"medium", "low"}
    assert row["risk_score"] > 0

def test_actions_cover_attendance():
    row = student.predict_academic_risk([{"student_id":"S","avg_score":80,"completion_rate":1,"attendance_rate":0.5}])[0]
    assert "联系辅导员" in row["recommended_actions"]

def test_actions_cover_completion():
    row = student.predict_academic_risk([{"student_id":"S","avg_score":80,"completion_rate":0.4,"attendance_rate":1}])[0]
    assert "跟进任务完成" in row["recommended_actions"]

def test_actions_cover_score():
    row = student.predict_academic_risk([{"student_id":"S","avg_score":50,"completion_rate":1,"attendance_rate":1}])[0]
    assert "安排基础补学" in row["recommended_actions"]

def test_string_numbers_supported():
    assert student.predict_academic_risk([{"student_id":"S","avg_score":"90","completion_rate":"1","attendance_rate":"1"}])[0]["risk_level"] == "low"

def test_empty_returns_empty():
    assert student.predict_academic_risk([]) == []

def test_rejects_non_list():
    with pytest.raises(ValueError): student.predict_academic_risk({})

def test_ignores_bad_rows():
    assert student.predict_academic_risk(["bad", {}, {"student_id":"S"}])[0]["student_id"] == "S"

def test_caps_late_penalty():
    a = student.predict_academic_risk([{"student_id":"A","late_submissions":10}])[0]["risk_score"]
    b = student.predict_academic_risk([{"student_id":"B","late_submissions":100}])[0]["risk_score"]
    assert abs(a - b) < 0.001
