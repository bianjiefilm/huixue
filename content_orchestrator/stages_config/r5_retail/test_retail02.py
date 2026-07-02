import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_retail02"))
ITEMS=[{"item_id":"A","margin":0.8,"affinity":0.9,"velocity":80,"stock":5},{"item_id":"B","margin":0.3,"affinity":0.4,"velocity":20,"stock":3},{"item_id":"C","margin":0.1,"affinity":0.1,"velocity":1,"stock":0}]
def test_sort(): assert [r["item_id"] for r in student.optimize_product_bundle(ITEMS)]==["A","B","C"]
def test_core(): assert student.optimize_product_bundle(ITEMS)[0]["tag"]=="core"
def test_addon(): assert [r for r in student.optimize_product_bundle(ITEMS) if r["item_id"]=="B"][0]["tag"]=="addon"
def test_avoid(): assert student.optimize_product_bundle(ITEMS)[-1]["tag"]=="avoid"
def test_empty(): assert student.optimize_product_bundle([])==[]
def test_reject():
    with pytest.raises(ValueError): student.optimize_product_bundle({})
def test_string_numbers(): assert student.optimize_product_bundle([{"item_id":"X","margin":"1","affinity":"1","velocity":"100","stock":"1"}])[0]["tag"]=="core"
def test_bad_rows(): assert student.optimize_product_bundle(["bad",{},{"item_id":"X"}])[0]["item_id"]=="X"
def test_tie_sort(): assert [r["item_id"] for r in student.optimize_product_bundle([{"item_id":"B"},{"item_id":"A"}])]==["A","B"]
def test_no_stock_penalty(): assert student.optimize_product_bundle([{"item_id":"X","margin":1,"affinity":1,"velocity":100,"stock":0}])[0]["bundle_score"]<95
def test_bool_margin(): assert student.optimize_product_bundle([{"item_id":"X","margin":True,"affinity":1}])[0]["bundle_score"]==15
def test_score_round(): assert isinstance(student.optimize_product_bundle(ITEMS)[0]["bundle_score"], float)
