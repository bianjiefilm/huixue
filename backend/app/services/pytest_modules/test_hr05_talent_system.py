import importlib
import os

import pytest

MODULE_NAME = os.environ.get("STUDENT_MODULE", "student_hr05")
student = importlib.import_module(MODULE_NAME)

EMPLOYEES = [
    {"employee_id": "E1", "department": "Tech", "salary": 32000, "tenure_months": 4, "salary_market_ratio": 0.82, "overtime_hours": 50, "months_since_promotion": 6},
    {"employee_id": "E2", "department": "Tech", "salary": "28000", "tenure_months": 36, "salary_market_ratio": 1.05, "overtime_hours": 20, "months_since_promotion": 30},
    {"employee_id": "E3", "department": "Sales", "salary": 16000, "tenure_months": 18, "salary_market_ratio": 0.95, "overtime_hours": 10, "months_since_promotion": 10},
]
CANDIDATES = [{"role": "Engineer", "stage": s} for s in ["applied", "screen", "interview", "offer", "hired"]] + [{"role": "Sales", "stage": s} for s in ["screen", "interview"]]
ENGAGEMENT = [{"employee_id": "E1", "engagement_score": 52, "manager_score": 70}, {"employee_id": "E2", "engagement_score": 78, "manager_score": 55}, {"employee_id": "E3", "engagement_score": 90, "manager_score": 90}]
REVIEWS = [{"employee_id": "E1", "goal_score": 96, "competency_score": 94, "values_score": 92, "peer_score": 90}, {"employee_id": "E2", "goal_score": 88, "competency_score": 82, "values_score": 90, "peer_score": 80}, {"employee_id": "E3", "goal_score": 62, "competency_score": 70, "values_score": 80, "peer_score": 65}]


def _salary(): return student.analyze_salary_structure(EMPLOYEES)
def _funnel(): return student.analyze_recruiting_funnel(CANDIDATES)
def _attrition(): return student.predict_attrition_risk(EMPLOYEES, ENGAGEMENT)
def _performance(): return student.evaluate_performance_reviews(REVIEWS)


def test_01_salary_order(): assert [x["department"] for x in _salary()] == ["Tech", "Sales"]
def test_02_salary_tech_high(): assert _salary()[0]["salary_band"] == "high"
def test_03_salary_rejects_bad_type():
    with pytest.raises(ValueError): student.analyze_salary_structure({})
def test_04_salary_bad_rows(): assert student.analyze_salary_structure(["bad", {"department": "A", "salary": 100}])[0]["department"] == "A"
def test_05_salary_empty(): assert student.analyze_salary_structure([]) == []
def test_06_funnel_engineer_hire(): assert _funnel()[0]["hire_rate"] == 0.5
def test_07_funnel_sales_offer_bottleneck(): assert [x for x in _funnel() if x["role"] == "Sales"][0]["bottleneck"] == "offer"
def test_08_funnel_rejects_bad_type():
    with pytest.raises(ValueError): student.analyze_recruiting_funnel({})
def test_09_funnel_unknown_stage(): assert student.analyze_recruiting_funnel([{"role": "A", "stage": "bad"}]) == []
def test_10_funnel_tie_break(): assert [x["role"] for x in student.analyze_recruiting_funnel([{"role":"B","stage":"applied"},{"role":"A","stage":"applied"}])] == ["A","B"]
def test_11_attrition_top_critical(): assert _attrition()[0]["employee_id"] == "E1" and _attrition()[0]["risk_level"] == "critical"
def test_12_attrition_manager_action(): assert [x for x in _attrition() if x["employee_id"] == "E2"][0]["retention_action"] == "manager_intervention"
def test_13_attrition_rejects_bad_type():
    with pytest.raises(ValueError): student.predict_attrition_risk({})
def test_14_attrition_bad_engagement():
    with pytest.raises(ValueError): student.predict_attrition_risk([], {})
def test_15_attrition_empty(): assert student.predict_attrition_risk([]) == []
def test_16_performance_a_player(): assert _performance()[0]["rating"] == "A"
def test_17_performance_focus(): assert _performance()[-1]["development_focus"] == ["collaboration", "goal_execution", "skill_growth"]
def test_18_performance_rejects_bad_type():
    with pytest.raises(ValueError): student.evaluate_performance_reviews({})
def test_19_performance_missing_scores(): assert student.evaluate_performance_reviews([{"employee_id":"X"}])[0]["rating"] == "D"
def test_20_performance_empty(): assert student.evaluate_performance_reviews([]) == []
def test_21_report_exact():
    assert student.summarize_hr_report(_salary(), _funnel(), _attrition(), _performance()) == {"departments": 2, "high_salary_departments": 1, "open_roles": 2, "critical_attrition": 1, "a_players": 1, "overall_status": "retention_emergency"}
def test_22_report_growth_ready(): assert student.summarize_hr_report([], [], [{"risk_level":"low"}], [{"rating":"A"}])["overall_status"] == "talent_growth_ready"
def test_23_report_stable(): assert student.summarize_hr_report([], [], [], [])["overall_status"] == "stable"
def test_24_report_rejects_bad_type():
    with pytest.raises(ValueError): student.summarize_hr_report({}, [], [], [])
def test_25_end_to_end_pipeline(): assert student.summarize_hr_report(_salary(), _funnel(), _attrition(), _performance())["departments"] == 2
def test_26_salary_bool_ignored(): assert student.analyze_salary_structure([{"department":"A","salary":True}]) == []
def test_27_attrition_score_cap(): assert student.predict_attrition_risk([{"employee_id":"X","tenure_months":1,"salary_market_ratio":0.1,"overtime_hours":99,"months_since_promotion":99}], [{"employee_id":"X","engagement_score":0,"manager_score":0}])[0]["attrition_score"] == 1.0
def test_28_performance_boundary_b(): assert student.evaluate_performance_reviews([{"employee_id":"X","goal_score":75,"competency_score":75,"values_score":75,"peer_score":75}])[0]["rating"] == "B"
def test_29_funnel_hired_all_rates_one(): assert student.analyze_recruiting_funnel([{"role":"A","stage":"hired"}])[0]["hire_rate"] == 1.0
def test_30_salary_boundary_medium(): assert student.analyze_salary_structure([{"department":"A","salary":18000}])[0]["salary_band"] == "medium"
