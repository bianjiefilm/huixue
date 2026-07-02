-- Phase D: 5 综合关 task_tests pytest_module 协议入库
-- 每关 1 行: input_data 含 test_module + student_module_name, match_rule='pytest_module'
-- backend execute_pytest_module 解析 stdout 'X passed' 计 score

BEGIN;

-- WX12 (task_id=129) 数据清洗流水线综合项目
DELETE FROM task_tests WHERE task_id=129;
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (129, 'pytest_wx12', '{"test_module": "test_wx12_comprehensive.py", "student_module_name": "student_wx12"}', '{"placeholder": "pytest_module 28 cases"}', false, 'pytest_module', 1);

-- CV12 (task_id=117) 物体识别端到端
DELETE FROM task_tests WHERE task_id=117;
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (117, 'pytest_cv12', '{"test_module": "test_cv12_comprehensive.py", "student_module_name": "student_cv12"}', '{"placeholder": "pytest_module 30 cases"}', false, 'pytest_module', 1);

-- BD12 (task_id=141) 大数据综合项目
DELETE FROM task_tests WHERE task_id=141;
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (141, 'pytest_bd12', '{"test_module": "test_bd12_comprehensive.py", "student_module_name": "student_bd12"}', '{"placeholder": "pytest_module 28 cases"}', false, 'pytest_module', 1);

-- MJ12 (task_id=93) 客户流失预测
DELETE FROM task_tests WHERE task_id=93;
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (93, 'pytest_mj12', '{"test_module": "test_mj12_comprehensive.py", "student_module_name": "student_mj12"}', '{"placeholder": "pytest_module 24 cases"}', false, 'pytest_module', 1);

-- NN12 (task_id=105) 手写数字识别
DELETE FROM task_tests WHERE task_id=105;
INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (105, 'pytest_nn12', '{"test_module": "test_nn12_comprehensive.py", "student_module_name": "student_nn12"}', '{"placeholder": "pytest_module 24 cases"}', false, 'pytest_module', 1);

COMMIT;
