import importlib, os, pytest
student = importlib.import_module(os.environ.get("STUDENT_MODULE", "student_edu02"))
DATA = [
    {"student_id":"S1","scores":{"math":90,"programming":95,"english":70}},
    {"student_id":"S2","scores":{"math":80,"programming":85,"english":75}},
    {"student_id":"S3","scores":{"math":70,"programming":74,"english":90}},
    {"student_id":"S4","scores":{"math":60,"programming":65,"english":95}},
]

def test_returns_three_pairs():
    assert len(student.analyze_course_correlation(DATA)) == 3

def test_top_pair_strong_positive():
    top = student.analyze_course_correlation(DATA)[0]
    assert top["course_pair"] == ["math", "programming"]
    assert top["strength"] == "strong"
    assert top["correlation"] > 0.99

def test_negative_correlation_detected():
    rows = student.analyze_course_correlation(DATA)
    pair = [r for r in rows if r["course_pair"] == ["english", "math"]][0]
    assert pair["correlation"] < -0.85
    assert pair["strength"] == "strong"

def test_sample_size_ignores_missing():
    rows = student.analyze_course_correlation(DATA + [{"student_id":"S5","scores":{"math":88}}])
    assert [r for r in rows if r["course_pair"] == ["math", "programming"]][0]["sample_size"] == 4

def test_constant_course_is_zero_corr():
    rows = student.analyze_course_correlation([{"scores":{"a":1,"b":5}}, {"scores":{"a":1,"b":8}}, {"scores":{"a":1,"b":9}}])
    assert rows[0]["correlation"] == 0.0

def test_medium_strength():
    rows = student.analyze_course_correlation([{"scores":{"a":1,"b":1}}, {"scores":{"a":2,"b":3}}, {"scores":{"a":3,"b":2}}, {"scores":{"a":4,"b":5}}])
    assert rows[0]["strength"] in {"medium", "strong"}

def test_weak_strength_for_unrelated():
    rows = student.analyze_course_correlation([{"scores":{"a":1,"b":3}}, {"scores":{"a":2,"b":1}}, {"scores":{"a":3,"b":4}}, {"scores":{"a":4,"b":2}}])
    assert any(r["strength"] == "weak" for r in rows)

def test_rejects_non_list():
    with pytest.raises(ValueError): student.analyze_course_correlation({})

def test_empty_returns_empty():
    assert student.analyze_course_correlation([]) == []

def test_string_scores_supported():
    res = student.analyze_course_correlation([{"scores":{"a":"1","b":"2"}}, {"scores":{"a":"2","b":"4"}}])
    assert res[0]["correlation"] == 1.0

def test_bool_scores_ignored():
    assert student.analyze_course_correlation([{"scores":{"a":True,"b":2}}, {"scores":{"a":3,"b":4}}])[0]["sample_size"] == 1

def test_sort_tie_by_course_pair():
    res = student.analyze_course_correlation([{"scores":{"a":1,"b":2,"c":3}}, {"scores":{"a":2,"b":3,"c":4}}])
    assert res[0]["course_pair"] == ["a", "b"]
