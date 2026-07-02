import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_retail01"))
ROWS=[{"unit_id":"A","revenue":12000,"cost":7000,"visitors":300,"area":100},{"unit_id":"A","revenue":"9000","cost":"2000","visitors":200,"area":100},{"unit_id":"B","revenue":5000,"cost":6500,"visitors":120,"area":50},{"unit_id":"C","revenue":3000,"cost":1000,"visitors":90,"area":30}]
def test_count_sort(): assert [r["unit_id"] for r in student.analyze_store_performance(ROWS)]==["A","C","B"]
def test_a_metrics():
    a=student.analyze_store_performance(ROWS)[0]; assert a["total_revenue"]==21000 and a["profit"]==12000 and a["level"]=="excellent"
def test_loss_level(): assert [r for r in student.analyze_store_performance(ROWS) if r["unit_id"]=="B"][0]["level"]=="loss"
def test_efficiency(): assert [r for r in student.analyze_store_performance(ROWS) if r["unit_id"]=="C"][0]["efficiency"]==100
def test_empty(): assert student.analyze_store_performance([])==[]
def test_rejects_non_list():
    with pytest.raises(ValueError): student.analyze_store_performance({})
def test_bad_rows(): assert student.analyze_store_performance(["bad",{},{"unit_id":"X","revenue":1}])[0]["unit_id"]=="X"
def test_negative_clamped(): assert student.analyze_store_performance([{"unit_id":"X","revenue":-1,"cost":-2}])[0]["profit"]==0
def test_string_numbers(): assert student.analyze_store_performance([{"unit_id":"X","revenue":"10","cost":"3"}])[0]["profit"]==7
def test_tie_sort(): assert [r["unit_id"] for r in student.analyze_store_performance([{"unit_id":"B","revenue":1},{"unit_id":"A","revenue":1}])]==["A","B"]
def test_area_default(): assert student.analyze_store_performance([{"unit_id":"X","revenue":10}])[0]["efficiency"]==10
def test_bool_revenue_default(): assert student.analyze_store_performance([{"unit_id":"X","revenue":True,"cost":1}])[0]["profit"]==-1
