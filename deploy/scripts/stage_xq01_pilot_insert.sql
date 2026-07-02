-- XQ01 试点 (临时 task_id=999) — 学生学业表现基础统计 — 32 cases

BEGIN;

-- 1) 创建临时 task (task_id=999) 含 handbook
INSERT INTO tasks (id, practice_id, title, task_type, coin)
VALUES (999, 6, 'XQ01-试点-学生学业表现基础统计', 'CODE', 10);

-- 2) 插入 task_tests
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (999, 'fc_pr_basic_8_pass_2_fail', $${"function": "compute_pass_rate", "args": [[{"student_id": "S000", "score": 75}, {"student_id": "S001", "score": 88}, {"student_id": "S002", "score": 60}, {"student_id": "S003", "score": 45}, {"student_id": "S004", "score": 92}, {"student_id": "S005", "score": 70}, {"student_id": "S006", "score": 58}, {"student_id": "S007", "score": 80}, {"student_id": "S008", "score": 65}, {"student_id": "S009", "score": 71}], 60], "kwargs": {}}$$, $${"result": {"pass_count": 8, "fail_count": 2, "pass_rate": 0.8}, "tolerance": 1e-06}$$, false, 'function_call', 1),
  (999, 'fc_pr_all_pass', $${"function": "compute_pass_rate", "args": [[{"student_id": "S0", "score": 80}, {"student_id": "S1", "score": 80}, {"student_id": "S2", "score": 80}, {"student_id": "S3", "score": 80}, {"student_id": "S4", "score": 80}], 60], "kwargs": {}}$$, $${"result": {"pass_count": 5, "fail_count": 0, "pass_rate": 1.0}, "tolerance": 1e-06}$$, true, 'function_call', 2),
  (999, 'fc_pr_all_fail', $${"function": "compute_pass_rate", "args": [[{"student_id": "S0", "score": 30}, {"student_id": "S1", "score": 30}, {"student_id": "S2", "score": 30}, {"student_id": "S3", "score": 30}, {"student_id": "S4", "score": 30}], 60], "kwargs": {}}$$, $${"result": {"pass_count": 0, "fail_count": 5, "pass_rate": 0.0}, "tolerance": 1e-06}$$, true, 'function_call', 3),
  (999, 'fc_pr_at_threshold_pass', $${"function": "compute_pass_rate", "args": [[{"student_id": "S001", "score": 60}], 60], "kwargs": {}}$$, $${"result": {"pass_count": 1, "fail_count": 0, "pass_rate": 1.0}, "tolerance": 1e-06}$$, true, 'function_call', 4),
  (999, 'fc_pr_custom_threshold_70', $${"function": "compute_pass_rate", "args": [[{"student_id": "S000", "score": 75}, {"student_id": "S001", "score": 88}, {"student_id": "S002", "score": 60}, {"student_id": "S003", "score": 45}, {"student_id": "S004", "score": 92}, {"student_id": "S005", "score": 70}, {"student_id": "S006", "score": 58}, {"student_id": "S007", "score": 80}, {"student_id": "S008", "score": 65}, {"student_id": "S009", "score": 71}], 70], "kwargs": {}}$$, $${"result": {"pass_count": 6, "fail_count": 4, "pass_rate": 0.6}, "tolerance": 1e-06}$$, true, 'function_call', 5),
  (999, 'fc_pr_single_student', $${"function": "compute_pass_rate", "args": [[{"student_id": "S001", "score": 95}], 60], "kwargs": {}}$$, $${"result": {"pass_count": 1, "fail_count": 0, "pass_rate": 1.0}, "tolerance": 1e-06}$$, true, 'function_call', 6),
  (999, 'fc_pr_raises_on_empty', $${"function": "compute_pass_rate", "args": [[], 60], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (999, 'fc_pr_raises_on_non_list', $${"function": "compute_pass_rate", "args": ["not a list", 60], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (999, 'fc_id_basic_avg_70', $${"function": "item_difficulty", "args": [[60, 70, 80], 100], "kwargs": {}}$$, $${"result": 0.7, "tolerance": 1e-06}$$, false, 'function_call', 9),
  (999, 'fc_id_all_zeros', $${"function": "item_difficulty", "args": [[0, 0, 0, 0, 0], 100], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 10),
  (999, 'fc_id_all_full_marks', $${"function": "item_difficulty", "args": [[100, 100, 100], 100], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, true, 'function_call', 11),
  (999, 'fc_id_mixed_avg_78', $${"function": "item_difficulty", "args": [[50, 75, 80, 90, 95], 100], "kwargs": {}}$$, $${"result": 0.78, "tolerance": 1e-06}$$, true, 'function_call', 12),
  (999, 'fc_id_custom_max_score', $${"function": "item_difficulty", "args": [[40, 60, 80], 80], "kwargs": {}}$$, $${"result": 0.75, "tolerance": 1e-06}$$, true, 'function_call', 13),
  (999, 'fc_id_single_score', $${"function": "item_difficulty", "args": [[85], 100], "kwargs": {}}$$, $${"result": 0.85, "tolerance": 1e-06}$$, true, 'function_call', 14),
  (999, 'fc_id_raises_on_empty', $${"function": "item_difficulty", "args": [[], 100], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 15),
  (999, 'fc_id_raises_on_non_list', $${"function": "item_difficulty", "args": ["abc", 100], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 16),
  (999, 'fc_ec_basic_5_courses', $${"function": "enrollment_concentration", "args": [[{"course_id": "C0", "enroll_count": 40}, {"course_id": "C1", "enroll_count": 30}, {"course_id": "C2", "enroll_count": 15}, {"course_id": "C3", "enroll_count": 10}, {"course_id": "C4", "enroll_count": 5}]], "kwargs": {}}$$, $${"result": 0.285, "tolerance": 1e-06}$$, false, 'function_call', 17),
  (999, 'fc_ec_fully_concentrated', $${"function": "enrollment_concentration", "args": [[{"course_id": "C1", "enroll_count": 100}]], "kwargs": {}}$$, $${"result": 1.0, "tolerance": 1e-06}$$, true, 'function_call', 18),
  (999, 'fc_ec_uniform_4_equal', $${"function": "enrollment_concentration", "args": [[{"course_id": "C0", "enroll_count": 25}, {"course_id": "C1", "enroll_count": 25}, {"course_id": "C2", "enroll_count": 25}, {"course_id": "C3", "enroll_count": 25}]], "kwargs": {}}$$, $${"result": 0.25, "tolerance": 1e-06}$$, true, 'function_call', 19),
  (999, 'fc_ec_dominant_course', $${"function": "enrollment_concentration", "args": [[{"course_id": "C0", "enroll_count": 80}, {"course_id": "C1", "enroll_count": 10}, {"course_id": "C2", "enroll_count": 10}]], "kwargs": {}}$$, $${"result": 0.66, "tolerance": 1e-06}$$, true, 'function_call', 20),
  (999, 'fc_ec_two_course_uneven', $${"function": "enrollment_concentration", "args": [[{"course_id": "C0", "enroll_count": 60}, {"course_id": "C1", "enroll_count": 40}]], "kwargs": {}}$$, $${"result": 0.52, "tolerance": 1e-06}$$, true, 'function_call', 21),
  (999, 'fc_ec_very_dispersed', $${"function": "enrollment_concentration", "args": [[{"course_id": "C0", "enroll_count": 10}, {"course_id": "C1", "enroll_count": 10}, {"course_id": "C2", "enroll_count": 10}, {"course_id": "C3", "enroll_count": 10}, {"course_id": "C4", "enroll_count": 10}, {"course_id": "C5", "enroll_count": 10}, {"course_id": "C6", "enroll_count": 10}, {"course_id": "C7", "enroll_count": 10}, {"course_id": "C8", "enroll_count": 10}, {"course_id": "C9", "enroll_count": 10}]], "kwargs": {}}$$, $${"result": 0.1, "tolerance": 1e-06}$$, true, 'function_call', 22),
  (999, 'fc_ec_raises_on_empty', $${"function": "enrollment_concentration", "args": [[]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (999, 'fc_ec_raises_on_zero_total', $${"function": "enrollment_concentration", "args": [[{"course_id": "C1", "enroll_count": 0}, {"course_id": "C2", "enroll_count": 0}]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 24),
  (999, 'fc_gpa_basic_5_buckets', $${"function": "gpa_distribution_buckets", "args": [[0.5, 1.5, 2.5, 3.0, 3.5, 4.0, 2.0, 1.0, 3.2, 2.8], [0, 1.0, 2.0, 3.0, 4.0]], "kwargs": {}}$$, $${"result": {"0.00-1.00": 1, "1.00-2.00": 2, "2.00-3.00": 3, "3.00-4.00": 4}}$$, false, 'function_call', 25),
  (999, 'fc_gpa_all_in_one_bucket', $${"function": "gpa_distribution_buckets", "args": [[3.2, 3.5, 3.8, 3.0, 4.0], [0, 1.0, 2.0, 3.0, 4.0]], "kwargs": {}}$$, $${"result": {"0.00-1.00": 0, "1.00-2.00": 0, "2.00-3.00": 0, "3.00-4.00": 5}}$$, true, 'function_call', 26),
  (999, 'fc_gpa_uniform_4_buckets', $${"function": "gpa_distribution_buckets", "args": [[0.5, 1.5, 2.5, 3.5], [0, 1.0, 2.0, 3.0, 4.0]], "kwargs": {}}$$, $${"result": {"0.00-1.00": 1, "1.00-2.00": 1, "2.00-3.00": 1, "3.00-4.00": 1}}$$, true, 'function_call', 27),
  (999, 'fc_gpa_left_inclusive_right_exclusive', $${"function": "gpa_distribution_buckets", "args": [[1.0, 2.0, 3.0], [0, 1.0, 2.0, 3.0, 4.0]], "kwargs": {}}$$, $${"result": {"0.00-1.00": 0, "1.00-2.00": 1, "2.00-3.00": 1, "3.00-4.00": 1}}$$, true, 'function_call', 28),
  (999, 'fc_gpa_last_bucket_inclusive', $${"function": "gpa_distribution_buckets", "args": [[4.0], [0, 1.0, 2.0, 3.0, 4.0]], "kwargs": {}}$$, $${"result": {"0.00-1.00": 0, "1.00-2.00": 0, "2.00-3.00": 0, "3.00-4.00": 1}}$$, true, 'function_call', 29),
  (999, 'fc_gpa_custom_2_buckets', $${"function": "gpa_distribution_buckets", "args": [[1.0, 2.0, 3.0, 4.0], [0, 2.5, 4.0]], "kwargs": {}}$$, $${"result": {"0.00-2.50": 2, "2.50-4.00": 2}}$$, true, 'function_call', 30),
  (999, 'fc_gpa_raises_on_empty', $${"function": "gpa_distribution_buckets", "args": [[], [0, 1.0, 2.0, 3.0, 4.0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (999, 'fc_gpa_raises_on_buckets_not_increasing', $${"function": "gpa_distribution_buckets", "args": [[1.0, 2.0], [4.0, 2.0, 1.0]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 32);

-- 3) 验证
SELECT id, practice_id, title, coin FROM tasks WHERE id=999;
SELECT task_id, COUNT(*), string_agg(DISTINCT match_rule, ','), SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden
  FROM task_tests WHERE task_id=999 GROUP BY task_id;

COMMIT;