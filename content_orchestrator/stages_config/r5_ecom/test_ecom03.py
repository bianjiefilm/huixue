import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_ecom03"))
CUSTOMERS=[{"customer_id":"C1","total_spend":8000,"orders":8,"days_since_last_order":10},{"customer_id":"C2","total_spend":1500,"orders":2,"days_since_last_order":20},{"customer_id":"C3","total_spend":100,"orders":1,"days_since_last_order":10},{"customer_id":"C4","total_spend":200,"orders":3,"days_since_last_order":200}]
def test_segments_count(): assert {r["segment"] for r in student.build_customer_segments(CUSTOMERS)}=={"high_value","potential","new_user","inactive"}
def test_high_value_ids(): assert [r for r in student.build_customer_segments(CUSTOMERS) if r["segment"]=="high_value"][0]["customer_ids"]==["C1"]
def test_potential_avg(): assert [r for r in student.build_customer_segments(CUSTOMERS) if r["segment"]=="potential"][0]["avg_spend"]==1500
def test_new_user(): assert [r for r in student.build_customer_segments(CUSTOMERS) if r["segment"]=="new_user"][0]["customer_ids"]==["C3"]
def test_inactive(): assert [r for r in student.build_customer_segments(CUSTOMERS) if r["segment"]=="inactive"][0]["customer_ids"]==["C4"]
def test_empty(): assert student.build_customer_segments([])==[]
def test_rejects_non_list():
    with pytest.raises(ValueError): student.build_customer_segments({})
def test_string_numbers(): assert student.build_customer_segments([{"customer_id":"C","total_spend":"6000","orders":"6"}])[0]["segment"]=="high_value"
def test_ignores_bad_rows(): assert student.build_customer_segments(["bad",{}, {"customer_id":"C"}])[0]["customer_ids"]==["C"]
def test_sort_by_count():
    res=student.build_customer_segments(CUSTOMERS+[{"customer_id":"C5","total_spend":100,"orders":1,"days_since_last_order":5}]); assert res[0]["segment"]=="new_user"
def test_id_sort(): assert student.build_customer_segments([{"customer_id":"B","orders":1},{"customer_id":"A","orders":1}])[0]["customer_ids"]==["A","B"]
def test_bool_spend_defaults(): assert student.build_customer_segments([{"customer_id":"C","total_spend":True,"orders":True}])[0]["segment"]=="inactive"
