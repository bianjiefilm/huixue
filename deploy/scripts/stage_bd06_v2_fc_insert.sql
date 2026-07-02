-- BD06 (task_id=135) function_call task_tests — 30 条

BEGIN;

DELETE FROM task_tests WHERE task_id=135;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (135, 'fc_cont_8tb_8gb', $${"function": "compute_yarn_container_count", "args": [8000, 8], "kwargs": {}}$$, $${"result": 1000}$$, false, 'function_call', 1),
  (135, 'fc_cont_partial', $${"function": "compute_yarn_container_count", "args": [100, 8], "kwargs": {}}$$, $${"result": 12}$$, true, 'function_call', 2),
  (135, 'fc_cont_exact', $${"function": "compute_yarn_container_count", "args": [64, 16], "kwargs": {}}$$, $${"result": 4}$$, true, 'function_call', 3),
  (135, 'fc_cont_uneven', $${"function": "compute_yarn_container_count", "args": [50, 4], "kwargs": {}}$$, $${"result": 12}$$, true, 'function_call', 4),
  (135, 'fc_cont_raises_on_zero_total', $${"function": "compute_yarn_container_count", "args": [0, 8], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 5),
  (135, 'fc_cont_raises_on_zero_container', $${"function": "compute_yarn_container_count", "args": [100, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (135, 'fc_cont_raises_on_non_int', $${"function": "compute_yarn_container_count", "args": [100.0, 8], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (135, 'fc_req_too_much_mem', $${"function": "is_resource_request_valid", "args": [50, 4], "kwargs": {}}$$, $${"result": false}$$, false, 'function_call', 8),
  (135, 'fc_req_too_much_cpu', $${"function": "is_resource_request_valid", "args": [8, 20], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 9),
  (135, 'fc_req_zero_mem', $${"function": "is_resource_request_valid", "args": [0, 4], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 10),
  (135, 'fc_req_at_max_boundary', $${"function": "is_resource_request_valid", "args": [32, 16], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 11),
  (135, 'fc_req_custom_limits', $${"function": "is_resource_request_valid", "args": [10, 6, 16, 8], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 12),
  (135, 'fc_req_raises_on_non_int', $${"function": "is_resource_request_valid", "args": [8.0, 4], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 13),
  (135, 'fc_queue_production_high', $${"function": "assign_yarn_queue", "args": [10], "kwargs": {}}$$, $${"result": "production"}$$, false, 'function_call', 14),
  (135, 'fc_queue_production_at_8', $${"function": "assign_yarn_queue", "args": [8], "kwargs": {}}$$, $${"result": "production"}$$, true, 'function_call', 15),
  (135, 'fc_queue_default_at_4', $${"function": "assign_yarn_queue", "args": [4], "kwargs": {}}$$, $${"result": "default"}$$, true, 'function_call', 16),
  (135, 'fc_queue_default_at_7', $${"function": "assign_yarn_queue", "args": [7], "kwargs": {}}$$, $${"result": "default"}$$, true, 'function_call', 17),
  (135, 'fc_queue_low_at_3', $${"function": "assign_yarn_queue", "args": [3], "kwargs": {}}$$, $${"result": "low"}$$, true, 'function_call', 18),
  (135, 'fc_queue_low_at_0', $${"function": "assign_yarn_queue", "args": [0], "kwargs": {}}$$, $${"result": "low"}$$, true, 'function_call', 19),
  (135, 'fc_queue_low_negative', $${"function": "assign_yarn_queue", "args": [-5], "kwargs": {}}$$, $${"result": "low"}$$, true, 'function_call', 20),
  (135, 'fc_queue_raises_on_non_int', $${"function": "assign_yarn_queue", "args": [5.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 21),
  (135, 'fc_share_third', $${"function": "compute_fair_share_for_job", "args": [10, 30, 8000], "kwargs": {}}$$, $${"result": 2666}$$, false, 'function_call', 22),
  (135, 'fc_share_quarter', $${"function": "compute_fair_share_for_job", "args": [2, 8, 1000], "kwargs": {}}$$, $${"result": 250}$$, true, 'function_call', 23),
  (135, 'fc_share_half', $${"function": "compute_fair_share_for_job", "args": [5, 10, 100], "kwargs": {}}$$, $${"result": 50}$$, true, 'function_call', 24),
  (135, 'fc_share_full', $${"function": "compute_fair_share_for_job", "args": [10, 10, 500], "kwargs": {}}$$, $${"result": 500}$$, true, 'function_call', 25),
  (135, 'fc_share_floor_truncate', $${"function": "compute_fair_share_for_job", "args": [1, 3, 100], "kwargs": {}}$$, $${"result": 33}$$, true, 'function_call', 26),
  (135, 'fc_share_zero_resources', $${"function": "compute_fair_share_for_job", "args": [5, 10, 0], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 27),
  (135, 'fc_share_raises_on_zero_weight', $${"function": "compute_fair_share_for_job", "args": [0, 10, 100], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 28),
  (135, 'fc_share_raises_on_zero_total', $${"function": "compute_fair_share_for_job", "args": [5, 0, 100], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 29),
  (135, 'fc_share_raises_on_non_int', $${"function": "compute_fair_share_for_job", "args": [5.0, 10, 100], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 30);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=135 GROUP BY task_id;

COMMIT;