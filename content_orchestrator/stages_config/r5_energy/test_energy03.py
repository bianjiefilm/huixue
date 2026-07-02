import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_energy03"))
H=[{"value":100},{"value":120},{"value":140},{"value":160},{"value":180},{"value":200}]
def test_fields(): assert set(student.identify_saving_opportunities(H,2))=={"baseline","trend","forecast","confidence"}
def test_baseline(): assert student.identify_saving_opportunities(H,2)["baseline"]==180
def test_trend(): assert student.identify_saving_opportunities(H,2)["trend"]==20
def test_forecast(): assert student.identify_saving_opportunities(H,2)["forecast"]==220
def test_high_confidence(): assert student.identify_saving_opportunities(H,2)["confidence"]=="high"
def test_medium_confidence(): assert student.identify_saving_opportunities(H[:3],1)["confidence"]=="medium"
def test_low_empty(): assert student.identify_saving_opportunities([],1)["confidence"]=="low"
def test_reject():
    with pytest.raises(ValueError): student.identify_saving_opportunities({},1)
def test_string_values(): assert student.identify_saving_opportunities([{"value":"10"},{"value":"20"}],1)["forecast"]==25
def test_negative_ignored(): assert student.identify_saving_opportunities([{"value":-1},{"value":10}],1)["forecast"]==10
def test_horizon_min(): assert student.identify_saving_opportunities(H,0)["forecast"]==200
def test_bool_ignored(): assert student.identify_saving_opportunities([{"value":True}],1)["forecast"]==0
