import importlib, os, pytest
student = importlib.import_module(os.environ.get("STUDENT_MODULE", "student_edu04"))
PROFILE = {"avg_score":86,"budget":50000,"interests":["ai","data"],"skills":["python","math"]}
CATALOG = [
 {"path_id":"P1","min_score":80,"cost":30000,"tags":["ai","research"],"required_skills":["python","math"]},
 {"path_id":"P2","min_score":70,"cost":20000,"tags":["business","data"],"required_skills":["sql"]},
 {"path_id":"P3","min_score":90,"cost":10000,"tags":["ai"],"required_skills":["python"]},
 {"path_id":"P4","min_score":75,"cost":80000,"tags":["data"],"required_skills":["python"]},
]

def test_filters_score_and_budget():
    ids = [r["path_id"] for r in student.recommend_advancement_paths(PROFILE, CATALOG)]
    assert ids == ["P1", "P2"]

def test_fields_present():
    row = student.recommend_advancement_paths(PROFILE, CATALOG)[0]
    assert set(row) == {"path_id", "fit_score", "missing_skills", "reason_tags"}

def test_missing_skills_reported():
    row = [r for r in student.recommend_advancement_paths(PROFILE, CATALOG) if r["path_id"] == "P2"][0]
    assert row["missing_skills"] == ["sql"]

def test_reason_tags_sorted():
    assert student.recommend_advancement_paths(PROFILE, CATALOG)[0]["reason_tags"] == ["ai"]

def test_top_three_limit():
    catalog = [{"path_id":f"P{i}","min_score":1,"cost":1,"tags":["ai"],"required_skills":[]} for i in range(5)]
    assert len(student.recommend_advancement_paths(PROFILE, catalog)) == 3

def test_tie_break_path_id():
    catalog = [{"path_id":"B","min_score":1,"cost":1},{"path_id":"A","min_score":1,"cost":1}]
    assert [r["path_id"] for r in student.recommend_advancement_paths(PROFILE, catalog)] == ["A", "B"]

def test_empty_catalog():
    assert student.recommend_advancement_paths(PROFILE, []) == []

def test_rejects_bad_inputs():
    with pytest.raises(ValueError): student.recommend_advancement_paths([], CATALOG)
    with pytest.raises(ValueError): student.recommend_advancement_paths(PROFILE, {})

def test_string_numbers_supported():
    profile = {"avg_score":"90","budget":"100"}
    catalog = [{"path_id":"P","min_score":"80","cost":"99"}]
    assert student.recommend_advancement_paths(profile, catalog)[0]["path_id"] == "P"

def test_expensive_path_filtered():
    assert student.recommend_advancement_paths({"avg_score":100,"budget":1}, [{"path_id":"P","min_score":1,"cost":2}]) == []

def test_low_score_filtered():
    assert student.recommend_advancement_paths({"avg_score":50,"budget":100}, [{"path_id":"P","min_score":80,"cost":1}]) == []

def test_ignores_bad_catalog_rows():
    assert student.recommend_advancement_paths(PROFILE, ["bad", {}, CATALOG[0]])[0]["path_id"] == "P1"
