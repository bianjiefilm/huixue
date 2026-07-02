-- BD10 (task_id=139) function_call task_tests — 23 条

BEGIN;

DELETE FROM task_tests WHERE task_id=139;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (139, 'fc_split_typical', $${"function": "compute_split_size", "args": [102400, 16], "kwargs": {}}$$, $${"result": 6400}$$, false, 'function_call', 1),
  (139, 'fc_split_partial_ceil', $${"function": "compute_split_size", "args": [100, 3], "kwargs": {}}$$, $${"result": 34}$$, true, 'function_call', 2),
  (139, 'fc_split_default_mappers', $${"function": "compute_split_size", "args": [1000, 4], "kwargs": {}}$$, $${"result": 250}$$, true, 'function_call', 3),
  (139, 'fc_split_small_table', $${"function": "compute_split_size", "args": [10, 4], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 4),
  (139, 'fc_split_raises_on_zero_mappers', $${"function": "compute_split_size", "args": [100, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 5),
  (139, 'fc_split_raises_on_zero_table', $${"function": "compute_split_size", "args": [0, 4], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (139, 'fc_split_raises_on_non_int', $${"function": "compute_split_size", "args": [100.0, 4], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 7),
  (139, 'fc_inc_valid', $${"function": "is_incremental_import_valid", "args": [1000, 1500], "kwargs": {}}$$, $${"result": true}$$, false, 'function_call', 8),
  (139, 'fc_inc_no_new', $${"function": "is_incremental_import_valid", "args": [1000, 1000], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 9),
  (139, 'fc_inc_decreased', $${"function": "is_incremental_import_valid", "args": [1000, 999], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 10),
  (139, 'fc_inc_raises_on_negative', $${"function": "is_incremental_import_valid", "args": [-1, 100], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 11),
  (139, 'fc_inc_raises_on_non_int', $${"function": "is_incremental_import_valid", "args": [100.0, 200], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 12),
  (139, 'fc_mig_1m_default', $${"function": "compute_migration_time_seconds", "args": [1000000], "kwargs": {}}$$, $${"result": 100.0, "tolerance": 1e-06}$$, false, 'function_call', 13),
  (139, 'fc_mig_partial', $${"function": "compute_migration_time_seconds", "args": [1500], "kwargs": {}}$$, $${"result": 0.15, "tolerance": 1e-06}$$, true, 'function_call', 14),
  (139, 'fc_mig_custom_throughput', $${"function": "compute_migration_time_seconds", "args": [100000, 50000], "kwargs": {}}$$, $${"result": 2.0, "tolerance": 1e-06}$$, true, 'function_call', 15),
  (139, 'fc_mig_zero_rows', $${"function": "compute_migration_time_seconds", "args": [0], "kwargs": {}}$$, $${"result": 0.0, "tolerance": 1e-06}$$, true, 'function_call', 16),
  (139, 'fc_mig_large', $${"function": "compute_migration_time_seconds", "args": [100000000], "kwargs": {}}$$, $${"result": 10000.0, "tolerance": 1e-06}$$, true, 'function_call', 17),
  (139, 'fc_mig_raises_on_zero_throughput', $${"function": "compute_migration_time_seconds", "args": [100, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (139, 'fc_mig_raises_on_non_int', $${"function": "compute_migration_time_seconds", "args": [100.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 19),
  (139, 'fc_sel_one_col', $${"function": "select_split_column_strategy", "args": [1], "kwargs": {}}$$, $${"result": "numeric_pk"}$$, false, 'function_call', 20),
  (139, 'fc_sel_no_cols', $${"function": "select_split_column_strategy", "args": [0], "kwargs": {}}$$, $${"result": "manual"}$$, true, 'function_call', 21),
  (139, 'fc_sel_raises_on_negative', $${"function": "select_split_column_strategy", "args": [-1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 22),
  (139, 'fc_sel_raises_on_non_int', $${"function": "select_split_column_strategy", "args": [1.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 23);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=139 GROUP BY task_id;

COMMIT;