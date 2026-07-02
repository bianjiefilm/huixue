-- BD01 (task_id=130) function_call task_tests — 32 条

BEGIN;

DELETE FROM task_tests WHERE task_id=130;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (130, 'fc_role_hdfs', $${"function": "get_hadoop_component_role", "args": ["hdfs"], "kwargs": {}}$$, $${"result": "storage"}$$, false, 'function_call', 1),
  (130, 'fc_role_mapreduce', $${"function": "get_hadoop_component_role", "args": ["mapreduce"], "kwargs": {}}$$, $${"result": "compute"}$$, true, 'function_call', 2),
  (130, 'fc_role_yarn', $${"function": "get_hadoop_component_role", "args": ["yarn"], "kwargs": {}}$$, $${"result": "scheduling"}$$, true, 'function_call', 3),
  (130, 'fc_role_hive', $${"function": "get_hadoop_component_role", "args": ["hive"], "kwargs": {}}$$, $${"result": "data_warehouse"}$$, true, 'function_call', 4),
  (130, 'fc_role_hbase', $${"function": "get_hadoop_component_role", "args": ["hbase"], "kwargs": {}}$$, $${"result": "nosql"}$$, true, 'function_call', 5),
  (130, 'fc_role_kafka', $${"function": "get_hadoop_component_role", "args": ["kafka"], "kwargs": {}}$$, $${"result": "streaming"}$$, true, 'function_call', 6),
  (130, 'fc_role_sqoop', $${"function": "get_hadoop_component_role", "args": ["sqoop"], "kwargs": {}}$$, $${"result": "migration"}$$, true, 'function_call', 7),
  (130, 'fc_role_raises_on_unknown', $${"function": "get_hadoop_component_role", "args": ["unknown"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 8),
  (130, 'fc_role_raises_on_empty', $${"function": "get_hadoop_component_role", "args": [""], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 9),
  (130, 'fc_role_raises_on_non_string', $${"function": "get_hadoop_component_role", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 10),
  (130, 'fc_node_typical', $${"function": "compute_cluster_node_count", "args": [100.0, 10.0, 3], "kwargs": {}}$$, $${"result": 30}$$, false, 'function_call', 11),
  (130, 'fc_node_partial_ceil', $${"function": "compute_cluster_node_count", "args": [95.0, 10.0, 3], "kwargs": {}}$$, $${"result": 29}$$, true, 'function_call', 12),
  (130, 'fc_node_default_replication', $${"function": "compute_cluster_node_count", "args": [100.0, 10.0], "kwargs": {}}$$, $${"result": 30}$$, true, 'function_call', 13),
  (130, 'fc_node_replication_1', $${"function": "compute_cluster_node_count", "args": [100.0, 10.0, 1], "kwargs": {}}$$, $${"result": 10}$$, true, 'function_call', 14),
  (130, 'fc_node_replication_2', $${"function": "compute_cluster_node_count", "args": [100.0, 10.0, 2], "kwargs": {}}$$, $${"result": 20}$$, true, 'function_call', 15),
  (130, 'fc_node_small_data', $${"function": "compute_cluster_node_count", "args": [1.0, 10.0, 3], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 16),
  (130, 'fc_node_raises_on_zero_data', $${"function": "compute_cluster_node_count", "args": [0, 10, 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 17),
  (130, 'fc_node_raises_on_zero_capacity', $${"function": "compute_cluster_node_count", "args": [100, 0, 3], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (130, 'fc_node_raises_on_non_numeric', $${"function": "compute_cluster_node_count", "args": ["100", 10, 3], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 19),
  (130, 'fc_safe_at_threshold', $${"function": "is_hadoop_safe_mode_ok", "args": [1000], "kwargs": {}}$$, $${"result": true}$$, false, 'function_call', 20),
  (130, 'fc_safe_above_threshold', $${"function": "is_hadoop_safe_mode_ok", "args": [1500], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 21),
  (130, 'fc_safe_zero', $${"function": "is_hadoop_safe_mode_ok", "args": [0], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 22),
  (130, 'fc_safe_custom_threshold', $${"function": "is_hadoop_safe_mode_ok", "args": [100, 50], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 23),
  (130, 'fc_safe_raises_on_negative', $${"function": "is_hadoop_safe_mode_ok", "args": [-1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 24),
  (130, 'fc_safe_raises_on_non_int', $${"function": "is_hadoop_safe_mode_ok", "args": [500.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 25),
  (130, 'fc_port_namenode', $${"function": "get_hadoop_default_port", "args": ["namenode"], "kwargs": {}}$$, $${"result": 9000}$$, false, 'function_call', 26),
  (130, 'fc_port_datanode', $${"function": "get_hadoop_default_port", "args": ["datanode"], "kwargs": {}}$$, $${"result": 9866}$$, true, 'function_call', 27),
  (130, 'fc_port_namenode_ui', $${"function": "get_hadoop_default_port", "args": ["namenode_ui"], "kwargs": {}}$$, $${"result": 9870}$$, true, 'function_call', 28),
  (130, 'fc_port_resourcemanager', $${"function": "get_hadoop_default_port", "args": ["resourcemanager"], "kwargs": {}}$$, $${"result": 8088}$$, true, 'function_call', 29),
  (130, 'fc_port_jobhistory', $${"function": "get_hadoop_default_port", "args": ["jobhistory"], "kwargs": {}}$$, $${"result": 19888}$$, true, 'function_call', 30),
  (130, 'fc_port_raises_on_unknown', $${"function": "get_hadoop_default_port", "args": ["unknown_svc"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 31),
  (130, 'fc_port_raises_on_non_string', $${"function": "get_hadoop_default_port", "args": [9000], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 32);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=130 GROUP BY task_id;

COMMIT;