import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_ecom01"))
ORDERS=[{"sku":"A","quantity":3,"unit_price":1000},{"sku":"A","quantity":"8","unit_price":"1000","is_refund":True},{"sku":"B","quantity":2,"unit_price":1200},{"sku":"C","quantity":1,"unit_price":500},{"sku":"BAD","quantity":0,"unit_price":9}]
def test_count_and_sort():
    res=student.analyze_product_sales(ORDERS); assert [r["sku"] for r in res]==["A","B","C"]
def test_a_metrics():
    a=student.analyze_product_sales(ORDERS)[0]; assert a["units"]==11 and a["revenue"]==11000 and a["sales_band"]=="hot"
def test_refund_rate(): assert student.analyze_product_sales(ORDERS)[0]["refund_rate"]==0.5
def test_avg_price(): assert student.analyze_product_sales(ORDERS)[1]["avg_price"]==1200
def test_cold_band(): assert student.analyze_product_sales(ORDERS)[-1]["sales_band"]=="cold"
def test_empty(): assert student.analyze_product_sales([])==[]
def test_rejects_non_list():
    with pytest.raises(ValueError): student.analyze_product_sales({})
def test_ignores_bad_rows(): assert student.analyze_product_sales(["bad",{}, {"sku":"X","quantity":1,"unit_price":2}])[0]["sku"]=="X"
def test_negative_price_ignored(): assert student.analyze_product_sales([{"sku":"X","quantity":1,"unit_price":-1}])==[]
def test_zero_price_allowed(): assert student.analyze_product_sales([{"sku":"X","quantity":2,"unit_price":0}])[0]["revenue"]==0
def test_tie_break_sku(): assert [r["sku"] for r in student.analyze_product_sales([{"sku":"B","quantity":1,"unit_price":1},{"sku":"A","quantity":1,"unit_price":1}])]==["A","B"]
def test_bool_quantity_ignored(): assert student.analyze_product_sales([{"sku":"X","quantity":True,"unit_price":1}])==[]
