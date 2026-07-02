import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_energy04"))
ROWS=[{"period":"morning","visitors":120,"buyers":12,"dwell_minutes":20},{"period":"evening","visitors":600,"buyers":90,"dwell_minutes":30},{"period":"morning","visitors":"80","buyers":"8","dwell_minutes":"10"},{"period":"night","visitors":20,"buyers":1,"dwell_minutes":5}]
def test_sort(): assert [r["period"] for r in student.optimize_energy_cost(ROWS)]==["evening","morning","night"]
def test_conversion(): assert [r for r in student.optimize_energy_cost(ROWS) if r["period"]=="morning"][0]["conversion_rate"]==0.1
def test_peak(): assert student.optimize_energy_cost(ROWS)[0]["traffic_level"]=="peak"
def test_low(): assert student.optimize_energy_cost(ROWS)[-1]["traffic_level"]=="low"
def test_dwell_avg(): assert [r for r in student.optimize_energy_cost(ROWS) if r["period"]=="morning"][0]["avg_dwell"]==15
def test_empty(): assert student.optimize_energy_cost([])==[]
def test_reject():
    with pytest.raises(ValueError): student.optimize_energy_cost({})
def test_bad_rows(): assert student.optimize_energy_cost(["bad",{},{"period":"p","visitors":1}])[0]["period"]=="p"
def test_zero_visitors(): assert student.optimize_energy_cost([{"period":"p","visitors":0,"buyers":9}])[0]["conversion_rate"]==0
def test_negative_clamped(): assert student.optimize_energy_cost([{"period":"p","visitors":-1,"buyers":-1}])[0]["visitors"]==0
def test_tie_sort(): assert [r["period"] for r in student.optimize_energy_cost([{"period":"b","visitors":1},{"period":"a","visitors":1}])]==["a","b"]
def test_bool_visitors_default(): assert student.optimize_energy_cost([{"period":"p","visitors":True}])[0]["visitors"]==0
