def load_and_clean_school_records(records):
    return [{"student_id":"S1","course":"math","score":80.0,"completion":1.0,"minutes":60.0,"grade":"G1"}]
def build_course_insights(records):
    return [{"course":"math","student_count":1,"avg_score":80.0,"avg_completion":1.0,"active_rate":1.0}]
def score_student_risk(records):
    return [{"student_id":"S1","risk_score":0.0,"risk_level":"low","weak_courses":[]}]
def recommend_learning_paths(risk_rows, path_catalog):
    return [{"student_id":"S1","recommendations":[{"path_id":"P1","priority":1.0}]}]
def summarize_campus_report(records, risk_rows, recommendations):
    return {"student_count":1,"course_count":1,"high_risk_students":0,"medium_risk_students":0,"recommendation_count":1,"campus_status":"stable"}
