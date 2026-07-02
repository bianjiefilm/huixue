import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_retail04"))
ROWS=[{"period":"morning","visitors":120,"buyers":12,"dwell_minutes":20},{"period":"evening","visitors":600,"buyers":90,"dwell_minutes":30},{"period":"morning","visitors":"80","buyers":"8","dwell_minutes":"10"},{"period":"night","visitors":20,"buyers":1,"dwell_minutes":5}]
def test_sort(): assert [r["period"] for r in student.analyze_foot_traffic(ROWS)]==["evening","morning","night"]
def test_conversion(): assert [r for r in student.analyze_foot_traffic(ROWS) if r["period"]=="morning"][0]["conversion_rate"]==0.1
def test_peak(): assert student.analyze_foot_traffic(ROWS)[0]["traffic_level"]=="peak"
def test_low(): assert student.analyze_foot_traffic(ROWS)[-1]["traffic_level"]=="low"
def test_dwell_avg(): assert [r for r in student.analyze_foot_traffic(ROWS) if r["period"]=="morning"][0]["avg_dwell"]==15
def test_empty(): assert student.analyze_foot_traffic([])==[]
def test_reject():
    with pytest.raises(ValueError): student.analyze_foot_traffic({})
def test_bad_rows(): assert student.analyze_foot_traffic(["bad",{},{"period":"p","visitors":1}])[0]["period"]=="p"
def test_zero_visitors(): assert student.analyze_foot_traffic([{"period":"p","visitors":0,"buyers":9}])[0]["conversion_rate"]==0
def test_negative_clamped(): assert student.analyze_foot_traffic([{"period":"p","visitors":-1,"buyers":-1}])[0]["visitors"]==0
def test_tie_sort(): assert [r["period"] for r in student.analyze_foot_traffic([{"period":"b","visitors":1},{"period":"a","visitors":1}])]==["a","b"]
def test_bool_visitors_default(): assert student.analyze_foot_traffic([{"period":"p","visitors":True}])[0]["visitors"]==0
