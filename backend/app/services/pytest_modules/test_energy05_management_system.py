import importlib, os, pytest
student=importlib.import_module(os.environ.get("STUDENT_MODULE","student_energy05"))
RAW=[{"unit_id":"A","metric":15000,"cost":3000,"volume":100,"period":"d1"},{"unit_id":"A","metric":"9000","cost":"2000","volume":80,"period":"d2"},{"unit_id":"B","metric":2000,"cost":5000,"volume":50,"period":"d1"},{"unit_id":"C","metric":4000,"cost":1000,"volume":0,"period":"d1"},{"unit_id":"","metric":9}]
def clean(): return student.clean_operation_rows(RAW)
def perf(): return student.summarize_unit_performance(clean())
def test_clean_count(): assert len(clean())==4
def test_clean_sort(): assert clean()[0]["unit_id"]=="A"
def test_clean_reject():
    with pytest.raises(ValueError): student.clean_operation_rows({})
def test_clean_negative(): assert student.clean_operation_rows([{"unit_id":"X","metric":-1,"cost":-1}])[0]["metric"]==0
def test_perf_count(): assert len(perf())==3
def test_perf_a(): assert perf()[0]["unit_id"]=="A" and perf()[0]["status"]=="excellent"
def test_perf_risk(): assert [r for r in perf() if r["unit_id"]=="B"][0]["status"]=="risk"
def test_efficiency_zero_volume(): assert [r for r in perf() if r["unit_id"]=="C"][0]["efficiency"]==0
def test_forecast_baseline(): assert student.forecast_operation_metric([{"metric":10},{"metric":20},{"metric":30}],1)["baseline"]==20
def test_forecast_trend(): assert student.forecast_operation_metric([{"metric":10},{"metric":20},{"metric":30}],1)["trend"]==10
def test_forecast_empty(): assert student.forecast_operation_metric([],1)["forecast"]==0
def test_forecast_rejects_bad_history(): assert student.forecast_operation_metric([{"metric":"8"}],1)["forecast"]==8
def test_actions_count(): assert len(student.recommend_operation_actions(perf(),[]))==3
def test_action_risk(): assert student.recommend_operation_actions(perf(),[])[0]["action"]=="立即诊断"
def test_action_growth(): assert student.recommend_operation_actions([{"unit_id":"A","net_value":10,"status":"watch"}],[{"unit_id":"A","forecast":20}])[0]["action"]=="加大投入"
def test_action_regular(): assert student.recommend_operation_actions([{"unit_id":"A","net_value":10,"status":"watch"}],[{"unit_id":"A","forecast":11}])[0]["action"]=="常规优化"
def test_report_counts():
    actions=student.recommend_operation_actions(perf(),[]); r=student.summarize_operation_report(perf(),actions); assert r["unit_count"]==3 and r["urgent_actions"]==1
def test_report_status_urgent(): assert student.summarize_operation_report(perf(),student.recommend_operation_actions(perf(),[]))["operation_status"]=="urgent"
def test_report_stable(): assert student.summarize_operation_report([{"status":"excellent","net_value":1}],[])["operation_status"]=="stable"
def test_end_to_end():
    p=perf(); actions=student.recommend_operation_actions(p,[]); report=student.summarize_operation_report(p,actions); assert report["risk_units"]==1
def test_bad_rows_safe(): assert student.clean_operation_rows(["bad",{},{"unit_id":"X"}])[0]["unit_id"]=="X"
def test_perf_empty(): assert student.summarize_unit_performance([])==[]
def test_actions_empty(): assert student.recommend_operation_actions([],[])==[]
def test_report_empty(): assert student.summarize_operation_report([],[])["operation_status"]=="stable"
def test_forecast_horizon_min(): assert student.forecast_operation_metric([{"metric":10},{"metric":20}],0)["forecast"]==25
def test_action_sort_tie(): assert [r["unit_id"] for r in student.recommend_operation_actions([{"unit_id":"B","status":"risk"},{"unit_id":"A","status":"risk"}],[])]==["A","B"]
def test_perf_sort_tie(): assert [r["unit_id"] for r in student.summarize_unit_performance([{"unit_id":"B","metric":1},{"unit_id":"A","metric":1}])]==["A","B"]
def test_report_total(): assert student.summarize_operation_report([{"net_value":1},{"net_value":"2"}],[])["total_net_value"]==3
def test_bool_metric_default(): assert student.clean_operation_rows([{"unit_id":"X","metric":True}])[0]["metric"]==0
def test_forecast_negative_ignored(): assert student.forecast_operation_metric([{"metric":-1},{"metric":5}],1)["forecast"]==5
