import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_retail03"))
H=[{"value":100},{"value":120},{"value":140},{"value":160},{"value":180},{"value":200}]
def test_fields(): assert set(student.forecast_store_sales(H,2))=={"baseline","trend","forecast","confidence"}
def test_baseline(): assert student.forecast_store_sales(H,2)["baseline"]==180
def test_trend(): assert student.forecast_store_sales(H,2)["trend"]==20
def test_forecast(): assert student.forecast_store_sales(H,2)["forecast"]==220
def test_high_confidence(): assert student.forecast_store_sales(H,2)["confidence"]=="high"
def test_medium_confidence(): assert student.forecast_store_sales(H[:3],1)["confidence"]=="medium"
def test_low_empty(): assert student.forecast_store_sales([],1)["confidence"]=="low"
def test_reject():
    with pytest.raises(ValueError): student.forecast_store_sales({},1)
def test_string_values(): assert student.forecast_store_sales([{"value":"10"},{"value":"20"}],1)["forecast"]==25
def test_negative_ignored(): assert student.forecast_store_sales([{"value":-1},{"value":10}],1)["forecast"]==10
def test_horizon_min(): assert student.forecast_store_sales(H,0)["forecast"]==200
def test_bool_ignored(): assert student.forecast_store_sales([{"value":True}],1)["forecast"]==0
