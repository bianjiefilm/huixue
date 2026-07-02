import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_ecom04"))
USER={"preferred_categories":["phone","audio"],"budget":3000}
CAT=[{"sku":"A","category":"phone","price":2500,"rating":4.8,"margin":0.2},{"sku":"B","category":"audio","price":600,"rating":4.5,"margin":0.5},{"sku":"C","category":"home","price":1000,"rating":4.9,"margin":0.1},{"sku":"D","category":"phone","price":5000,"rating":5,"margin":0.9}]
INT=[{"sku":"A","event":"buy"}]
def test_filters_seen_and_budget(): assert [r["sku"] for r in student.recommend_products(USER,CAT,INT)]==["B","C"]
def test_reason_preference(): assert student.recommend_products(USER,CAT,INT)[0]["reason"]=="偏好匹配"
def test_fields(): assert set(student.recommend_products(USER,CAT,INT)[0])=={"sku","recommend_score","category","reason"}
def test_top5_limit(): assert len(student.recommend_products({"budget":999999},[{"sku":str(i),"price":1,"rating":1} for i in range(8)],[]))==5
def test_empty_catalog(): assert student.recommend_products(USER,[],[])==[]
def test_rejects_bad_inputs():
    with pytest.raises(ValueError): student.recommend_products([],CAT,[])
def test_string_numbers(): assert student.recommend_products({"budget":"100"},[{"sku":"S","price":"50","rating":"5","margin":"0.1"}],[])[0]["sku"]=="S"
def test_ignores_bad_rows(): assert student.recommend_products({"budget":9},["bad",{}, {"sku":"S","price":1}],[])[0]["sku"]=="S"
def test_cart_seen_filtered(): assert student.recommend_products({"budget":9},[{"sku":"S","price":1}],[{"sku":"S","event":"cart"}])==[]
def test_view_not_filtered(): assert student.recommend_products({"budget":9},[{"sku":"S","price":1}],[{"sku":"S","event":"view"}])[0]["sku"]=="S"
def test_tie_break_sku(): assert [r["sku"] for r in student.recommend_products({"budget":9},[{"sku":"B","price":1},{"sku":"A","price":1}],[])]==["A","B"]
def test_budget_default(): assert student.recommend_products({},[{"sku":"S","price":999999}],[])[0]["sku"]=="S"
