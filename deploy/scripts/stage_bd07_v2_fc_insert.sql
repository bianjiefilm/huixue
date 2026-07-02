-- BD07 (task_id=136) function_call task_tests — 25 条

BEGIN;

DELETE FROM task_tests WHERE task_id=136;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (136, 'fc_part_typical', $${"function": "compute_partition_count", "args": [100000000, 1000000], "kwargs": {}}$$, $${"result": 100}$$, false, 'function_call', 1),
  (136, 'fc_part_partial_ceil', $${"function": "compute_partition_count", "args": [1500000, 1000000], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 2),
  (136, 'fc_part_just_one', $${"function": "compute_partition_count", "args": [500000, 1000000], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 3),
  (136, 'fc_part_zero_rows', $${"function": "compute_partition_count", "args": [0, 1000], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 4),
  (136, 'fc_part_exact', $${"function": "compute_partition_count", "args": [3000000, 1000000], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 5),
  (136, 'fc_part_raises_on_zero_per_partition', $${"function": "compute_partition_count", "args": [100, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (136, 'fc_part_raises_on_non_int', $${"function": "compute_partition_count", "args": [100.0, 10], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (136, 'fc_prune_helpful_1_of_90', $${"function": "is_partition_pruning_helpful", "args": [1, 90], "kwargs": {}}$$, $${"result": true}$$, false, 'function_call', 8),
  (136, 'fc_prune_not_helpful_60_of_90', $${"function": "is_partition_pruning_helpful", "args": [60, 90], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 9),
  (136, 'fc_prune_at_threshold', $${"function": "is_partition_pruning_helpful", "args": [45, 90], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 10),
  (136, 'fc_prune_custom_threshold_03', $${"function": "is_partition_pruning_helpful", "args": [20, 100, 0.3], "kwargs": {}}$$, $${"result": true}$$, true, 'function_call', 11),
  (136, 'fc_prune_raises_on_zero_total', $${"function": "is_partition_pruning_helpful", "args": [0, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 12),
  (136, 'fc_dw_default_orc', $${"function": "compute_data_warehouse_size", "args": [1000, 3, 0.2], "kwargs": {}}$$, $${"result": 600.0, "tolerance": 1e-06}$$, false, 'function_call', 13),
  (136, 'fc_dw_no_compression', $${"function": "compute_data_warehouse_size", "args": [1000, 3, 1.0], "kwargs": {}}$$, $${"result": 3000.0, "tolerance": 1e-06}$$, true, 'function_call', 14),
  (136, 'fc_dw_replication_1', $${"function": "compute_data_warehouse_size", "args": [500, 1, 0.5], "kwargs": {}}$$, $${"result": 250.0, "tolerance": 1e-06}$$, true, 'function_call', 15),
  (136, 'fc_dw_zero_size', $${"function": "compute_data_warehouse_size", "args": [0, 3, 0.5], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 16),
  (136, 'fc_dw_decimal_compression', $${"function": "compute_data_warehouse_size", "args": [100, 3, 0.25], "kwargs": {}}$$, $${"result": 75.0, "tolerance": 1e-06}$$, true, 'function_call', 17),
  (136, 'fc_dw_raises_on_negative_size', $${"function": "compute_data_warehouse_size", "args": [-1, 3, 0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (136, 'fc_dw_raises_on_zero_replication', $${"function": "compute_data_warehouse_size", "args": [100, 0, 0.5], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 19),
  (136, 'fc_format_analytical', $${"function": "get_hive_storage_format", "args": ["analytical"], "kwargs": {}}$$, $${"result": "orc"}$$, false, 'function_call', 20),
  (136, 'fc_format_compatibility', $${"function": "get_hive_storage_format", "args": ["compatibility"], "kwargs": {}}$$, $${"result": "parquet"}$$, true, 'function_call', 21),
  (136, 'fc_format_simple', $${"function": "get_hive_storage_format", "args": ["simple"], "kwargs": {}}$$, $${"result": "textfile"}$$, true, 'function_call', 22),
  (136, 'fc_format_raises_on_unknown', $${"function": "get_hive_storage_format", "args": ["unknown"], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 23),
  (136, 'fc_format_raises_on_empty', $${"function": "get_hive_storage_format", "args": [""], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 24),
  (136, 'fc_format_raises_on_non_string', $${"function": "get_hive_storage_format", "args": [123], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 25);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=136 GROUP BY task_id;

COMMIT;