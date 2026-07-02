-- BD11 (task_id=140) function_call task_tests — 29 条

BEGIN;

DELETE FROM task_tests WHERE task_id=140;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (140, 'fc_assign_3c_3p', $${"function": "assign_consumer_partitions", "args": [["c1", "c2", "c3"], [0, 1, 2]], "kwargs": {}}$$, $${"result": {"c1": [0], "c2": [1], "c3": [2]}}$$, false, 'function_call', 1),
  (140, 'fc_assign_2c_4p', $${"function": "assign_consumer_partitions", "args": [["c1", "c2"], [0, 1, 2, 3]], "kwargs": {}}$$, $${"result": {"c1": [0, 2], "c2": [1, 3]}}$$, true, 'function_call', 2),
  (140, 'fc_assign_3c_5p', $${"function": "assign_consumer_partitions", "args": [["c1", "c2", "c3"], [0, 1, 2, 3, 4]], "kwargs": {}}$$, $${"result": {"c1": [0, 3], "c2": [1, 4], "c3": [2]}}$$, true, 'function_call', 3),
  (140, 'fc_assign_more_consumers_than_partitions', $${"function": "assign_consumer_partitions", "args": [["c1", "c2", "c3", "c4"], [0, 1]], "kwargs": {}}$$, $${"result": {"c1": [0], "c2": [1], "c3": [], "c4": []}}$$, true, 'function_call', 4),
  (140, 'fc_assign_one_consumer', $${"function": "assign_consumer_partitions", "args": [["c1"], [0, 1, 2, 3, 4]], "kwargs": {}}$$, $${"result": {"c1": [0, 1, 2, 3, 4]}}$$, true, 'function_call', 5),
  (140, 'fc_assign_raises_on_empty_consumers', $${"function": "assign_consumer_partitions", "args": [[], [0, 1]], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (140, 'fc_assign_raises_on_non_list', $${"function": "assign_consumer_partitions", "args": ["c1,c2", [0, 1]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (140, 'fc_repl_basic_3broker_ft2', $${"function": "compute_minimum_replication", "args": [2, 3], "kwargs": {}}$$, $${"result": 3}$$, false, 'function_call', 8),
  (140, 'fc_repl_ft0', $${"function": "compute_minimum_replication", "args": [0, 5], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 9),
  (140, 'fc_repl_ft1', $${"function": "compute_minimum_replication", "args": [1, 3], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 10),
  (140, 'fc_repl_more_brokers', $${"function": "compute_minimum_replication", "args": [2, 10], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 11),
  (140, 'fc_repl_raises_when_insufficient_brokers', $${"function": "compute_minimum_replication", "args": [5, 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 12),
  (140, 'fc_repl_raises_on_negative_ft', $${"function": "compute_minimum_replication", "args": [-1, 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (140, 'fc_repl_raises_on_zero_brokers', $${"function": "compute_minimum_replication", "args": [0, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 14),
  (140, 'fc_repl_raises_on_non_int', $${"function": "compute_minimum_replication", "args": [2.0, 3], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 15),
  (140, 'fc_lag_normal', $${"function": "is_message_lag_critical", "args": [900, 1000], "kwargs": {}}$$, $${"result": false}$$, false, 'function_call', 16),
  (140, 'fc_lag_critical', $${"function": "is_message_lag_critical", "args": [0, 2000], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 17),
  (140, 'fc_lag_at_threshold', $${"function": "is_message_lag_critical", "args": [0, 1000], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 18),
  (140, 'fc_lag_just_above', $${"function": "is_message_lag_critical", "args": [0, 1001], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 19),
  (140, 'fc_lag_zero', $${"function": "is_message_lag_critical", "args": [500, 500], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 20),
  (140, 'fc_lag_custom_threshold', $${"function": "is_message_lag_critical", "args": [0, 200, 100], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 21),
  (140, 'fc_lag_raises_on_consumer_gt_log_end', $${"function": "is_message_lag_critical", "args": [100, 50], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (140, 'fc_lag_raises_on_non_int', $${"function": "is_message_lag_critical", "args": [100.0, 200], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23),
  (140, 'fc_tput_typical', $${"function": "compute_throughput_bytes_per_sec", "args": [1000000, 200], "kwargs": {}}$$, $${"result": 200000000}$$, false, 'function_call', 24),
  (140, 'fc_tput_small', $${"function": "compute_throughput_bytes_per_sec", "args": [1000, 100], "kwargs": {}}$$, $${"result": 100000}$$, true, 'function_call', 25),
  (140, 'fc_tput_large_messages', $${"function": "compute_throughput_bytes_per_sec", "args": [100, 1048576], "kwargs": {}}$$, $${"result": 104857600}$$, true, 'function_call', 26),
  (140, 'fc_tput_minimum', $${"function": "compute_throughput_bytes_per_sec", "args": [1, 1], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 27),
  (140, 'fc_tput_raises_on_zero', $${"function": "compute_throughput_bytes_per_sec", "args": [0, 100], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 28),
  (140, 'fc_tput_raises_on_non_int', $${"function": "compute_throughput_bytes_per_sec", "args": [1000.0, 100], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 29);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=140 GROUP BY task_id;

COMMIT;