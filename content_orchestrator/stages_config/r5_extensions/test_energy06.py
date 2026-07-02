import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_energy06"))
RAW=[{"entity_id":"A","risk_score":0.95,"business_value":10000,"action_cost":1000,"impact":5000,"category":"core"},{"entity_id":"B","risk_score":"0.55","business_value":"4000","action_cost":"800","impact":"2000","category":"growth"},{"entity_id":"C","risk_score":0.1,"business_value":1000,"action_cost":200,"impact":100,"category":"watch"},{"entity_id":"","risk_score":1}]
def clean(): return student.clean_extension_events(RAW)
def actions(): return student.rank_extension_actions(clean())
def test_clean_count(): assert len(clean())==3
def test_clean_sort(): assert clean()[0]["entity_id"]=="A"
def test_clean_clamp(): assert student.clean_extension_events([{"entity_id":"X","risk_score":2}])[0]["risk_score"]==1.0
def test_clean_negative_clamp(): assert student.clean_extension_events([{"entity_id":"X","business_value":-1,"action_cost":-2}])[0]["business_value"]==0
def test_clean_string_numbers(): assert clean()[1]["risk_score"]==0.55
def test_clean_reject():
    with pytest.raises(ValueError): student.clean_extension_events({})
def test_clean_empty(): assert student.clean_extension_events([])==[]
def test_clean_bad_rows(): assert student.clean_extension_events(["bad",{},{"entity_id":"X"}])[0]["entity_id"]=="X"
def test_action_count(): assert len(actions())==3
def test_action_immediate(): assert actions()[0]["action"]=="immediate"
def test_action_scheduled_or_monitor(): assert [a for a in actions() if a["entity_id"]=="B"][0]["action"] in {"scheduled","monitor"}
def test_action_monitor(): assert [a for a in actions() if a["entity_id"]=="C"][0]["action"]=="monitor"
def test_action_sort(): assert actions()[0]["priority_score"]>=actions()[1]["priority_score"]
def test_action_net_gain(): assert actions()[0]["net_gain"]==4000
def test_action_reject():
    with pytest.raises(ValueError): student.rank_extension_actions({})
def test_action_empty(): assert student.rank_extension_actions([])==[]
def test_action_bad_rows(): assert student.rank_extension_actions(["bad",{},{"entity_id":"X"}])[0]["entity_id"]=="X"
def test_report_fields(): assert set(student.summarize_extension_report(clean(),actions()))=={"event_count","total_value","immediate_actions","scheduled_actions","expected_net_gain","status"}
def test_report_counts():
    r=student.summarize_extension_report(clean(),actions()); assert r["event_count"]==3 and r["immediate_actions"]==1
def test_report_value(): assert student.summarize_extension_report(clean(),actions())["total_value"]==15000
def test_report_status_urgent(): assert student.summarize_extension_report(clean(),actions())["status"]=="urgent"
def test_report_watch(): assert student.summarize_extension_report([], [{"action":"scheduled","net_gain":1}])["status"]=="watch"
def test_report_stable(): assert student.summarize_extension_report([], [{"action":"monitor","net_gain":1}])["status"]=="stable"
def test_report_net_gain(): assert student.summarize_extension_report(clean(),actions())["expected_net_gain"]==5100
def test_tie_sort_entity(): assert [r["entity_id"] for r in student.clean_extension_events([{"entity_id":"B","risk_score":1},{"entity_id":"A","risk_score":1}])]==["A","B"]
def test_bool_risk_default(): assert student.clean_extension_events([{"entity_id":"X","risk_score":True}])[0]["risk_score"]==0
def test_default_impact(): assert student.clean_extension_events([{"entity_id":"X","business_value":10,"action_cost":3}])[0]["impact"]==7
def test_action_high_risk_bonus(): assert student.rank_extension_actions([{"entity_id":"X","risk_score":0.8,"business_value":1,"action_cost":0,"impact":1}])[0]["priority_score"]>=63
def test_report_handles_bad_actions(): assert student.summarize_extension_report([], ["bad",{}])["expected_net_gain"]==0
def test_end_to_end():
    rows=clean(); acts=student.rank_extension_actions(rows); rep=student.summarize_extension_report(rows,acts); assert rep["status"]=="urgent" and rep["event_count"]==3
