import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_ecom05"))
EVENTS=[{"sku":"A","customer_id":"C1","quantity":5,"unit_price":1000,"category":"phone"},{"sku":"A","customer_id":"C2","quantity":"8","unit_price":"1000","category":"phone","is_refund":True},{"sku":"B","customer_id":"C1","quantity":2,"unit_price":500,"category":"audio"},{"sku":"BAD","quantity":0,"unit_price":1}]
INV=[{"sku":"A","stock":1,"safety_stock":3},{"sku":"B","stock":20,"safety_stock":2}]
PRODUCTS=[{"sku":"A","category":"phone","rating":5,"margin":0.2},{"sku":"B","category":"audio","rating":4,"margin":0.5},{"sku":"C","category":"audio","rating":4.8,"margin":0.3}]
def clean(): return student.clean_order_events(EVENTS)
def perf(): return student.summarize_product_performance(clean())
def test_clean_count(): assert len(clean())==3
def test_clean_sort_and_string_number(): assert clean()[0]["quantity"]==13 or clean()[0]["sku"]=="A"
def test_clean_rejects_non_list():
    with pytest.raises(ValueError): student.clean_order_events({})
def test_clean_ignores_zero(): assert all(r["sku"]!="BAD" for r in clean())
def test_performance_count(): assert len(perf())==2
def test_performance_a_revenue(): assert perf()[0]["sku"]=="A" and perf()[0]["revenue"]==13000
def test_performance_refund(): assert perf()[0]["refund_rate"]==0.5
def test_replenishment_urgent(): assert student.forecast_replenishment(perf(),INV)[0]["sku"]=="A"
def test_replenishment_qty(): assert student.forecast_replenishment(perf(),INV)[0]["reorder_qty"]==28
def test_replenishment_ok(): assert [r for r in student.forecast_replenishment(perf(),INV) if r["sku"]=="B"][0]["priority"]=="ok"
def test_recommend_filters_bought(): assert [r["sku"] for r in student.build_product_recommendations({"customer_id":"C1","preferred_categories":["audio"]},PRODUCTS,clean())]==["C"]
def test_recommend_reason(): assert student.build_product_recommendations({"customer_id":"C3","preferred_categories":["audio"]},PRODUCTS,clean())[0]["reason"]=="偏好匹配"
def test_recommend_limit(): assert len(student.build_product_recommendations({},[{"sku":str(i)} for i in range(8)],[]))==5
def test_report_counts():
    r=student.summarize_sales_operation(perf(),student.forecast_replenishment(perf(),INV),student.build_product_recommendations({"customer_id":"C3"},PRODUCTS,clean())); assert r["product_count"]==2 and r["recommendation_count"]==3
def test_report_status_urgent(): assert student.summarize_sales_operation(perf(),student.forecast_replenishment(perf(),INV),[])["operation_status"]=="urgent"
def test_report_status_growth(): assert student.summarize_sales_operation([{"revenue":20000}],[],[])["operation_status"]=="growth"
def test_report_status_stable(): assert student.summarize_sales_operation([],[],[])["operation_status"]=="stable"
def test_end_to_end():
    rows=clean(); p=student.summarize_product_performance(rows); repl=student.forecast_replenishment(p,INV); rec=student.build_product_recommendations({"customer_id":"C3","preferred_categories":["audio"]},PRODUCTS,rows); report=student.summarize_sales_operation(p,repl,rec); assert report["total_revenue"]==14000
def test_empty_clean(): assert student.clean_order_events([])==[]
def test_empty_performance(): assert student.summarize_product_performance([])==[]
def test_empty_replenishment(): assert student.forecast_replenishment([],[])==[]
def test_empty_recommend(): assert student.build_product_recommendations({},[],[])==[]
def test_bad_rows_safe(): assert student.clean_order_events(["bad",{}, {"sku":"S","quantity":1}])[0]["sku"]=="S"
def test_tie_recommend_sku(): assert [r["sku"] for r in student.build_product_recommendations({},[{"sku":"B"},{"sku":"A"}],[])]==["A","B"]
def test_missing_inventory_defaults(): assert student.forecast_replenishment([{"sku":"X","units":2,"revenue":1}],[])[0]["priority"]=="watch"
def test_report_urgent_count(): assert student.summarize_sales_operation([], [{"priority":"urgent"},{"priority":"ok"}], [1])["urgent_replenishments"]==1
def test_clean_negative_price_clamped(): assert student.clean_order_events([{"sku":"S","quantity":1,"unit_price":-9}])[0]["unit_price"]==0
def test_perf_sort_tie(): assert [r["sku"] for r in student.summarize_product_performance([{"sku":"B","quantity":1,"unit_price":1},{"sku":"A","quantity":1,"unit_price":1}])]==["A","B"]
def test_replenishment_sort_tie(): assert [r["sku"] for r in student.forecast_replenishment([{"sku":"B","units":10},{"sku":"A","units":10}],[])]==["A","B"]
def test_recommend_seen_buy(): assert student.build_product_recommendations({"customer_id":"C"},[{"sku":"S"}],[{"customer_id":"C","sku":"S"}])==[]
