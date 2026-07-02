import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_ecom02"))
INV=[{"sku":"A","stock":10,"lead_days":3,"safety_stock":8},{"sku":"B","stock":50,"lead_days":2,"safety_stock":10},{"sku":"C","stock":0,"lead_days":1,"safety_stock":5}]
SALES=[{"sku":"A","sold_qty":12,"date":"d1"},{"sku":"A","sold_qty":8,"date":"d2"},{"sku":"B","sold_qty":5,"date":"d1"},{"sku":"C","sold_qty":0,"date":"d1"}]
def test_count(): assert len(student.forecast_inventory_needs(INV,SALES))==3
def test_urgent_first(): assert student.forecast_inventory_needs(INV,SALES)[0]["sku"]=="A"
def test_a_metrics():
    a=student.forecast_inventory_needs(INV,SALES)[0]; assert a["daily_velocity"]==10 and a["reorder_qty"]==28 and a["priority"]=="urgent"
def test_ok_item(): assert [r for r in student.forecast_inventory_needs(INV,SALES) if r["sku"]=="B"][0]["priority"]=="ok"
def test_zero_velocity_days(): assert [r for r in student.forecast_inventory_needs(INV,SALES) if r["sku"]=="C"][0]["days_of_stock"]==999.0
def test_empty_sales(): assert student.forecast_inventory_needs([{"sku":"X","stock":1}],[])[0]["priority"]=="ok"
def test_rejects_bad_inputs():
    with pytest.raises(ValueError): student.forecast_inventory_needs({},[])
def test_string_numbers(): assert student.forecast_inventory_needs([{"sku":"X","stock":"0","lead_days":"2","safety_stock":"2"}],[{"sku":"X","sold_qty":"4","date":"d"}])[0]["reorder_qty"]==10
def test_ignores_bad_rows(): assert student.forecast_inventory_needs(["bad",{}, {"sku":"X","stock":1}],[])[0]["sku"]=="X"
def test_negative_sales_not_counted(): assert student.forecast_inventory_needs([{"sku":"X","stock":1}],[{"sku":"X","sold_qty":-5,"date":"d"}])[0]["daily_velocity"]==0
def test_watch_priority(): assert student.forecast_inventory_needs([{"sku":"X","stock":9,"lead_days":1,"safety_stock":5}],[{"sku":"X","sold_qty":10,"date":"d1"},{"sku":"X","sold_qty":10,"date":"d2"}])[0]["priority"]=="watch"
def test_bool_stock_defaults(): assert student.forecast_inventory_needs([{"sku":"X","stock":True}],[])[0]["days_of_stock"]==999.0
