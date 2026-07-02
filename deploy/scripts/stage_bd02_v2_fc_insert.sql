-- BD02 (task_id=131) function_call task_tests — 27 条

BEGIN;

DELETE FROM task_tests WHERE task_id=131;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (131, 'fc_block_300mb', $${"function": "compute_hdfs_block_count", "args": [314572800, 134217728], "kwargs": {}}$$, $${"result": 3}$$, false, 'function_call', 1),
  (131, 'fc_block_just_over', $${"function": "compute_hdfs_block_count", "args": [135266304, 134217728], "kwargs": {}}$$, $${"result": 2}$$, true, 'function_call', 2),
  (131, 'fc_block_default_blocksize', $${"function": "compute_hdfs_block_count", "args": [314572800], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 3),
  (131, 'fc_block_custom_64mb', $${"function": "compute_hdfs_block_count", "args": [314572800, 67108864], "kwargs": {}}$$, $${"result": 5}$$, true, 'function_call', 4),
  (131, 'fc_block_zero_file', $${"function": "compute_hdfs_block_count", "args": [0], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 5),
  (131, 'fc_block_raises_on_zero_blocksize', $${"function": "compute_hdfs_block_count", "args": [100, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 6),
  (131, 'fc_block_raises_on_negative_filesize', $${"function": "compute_hdfs_block_count", "args": [-1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 7),
  (131, 'fc_block_raises_on_non_int', $${"function": "compute_hdfs_block_count", "args": [100.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 8),
  (131, 'fc_storage_default', $${"function": "compute_storage_with_replication", "args": [104857600], "kwargs": {}}$$, $${"result": 314572800}$$, false, 'function_call', 9),
  (131, 'fc_storage_replication_1', $${"function": "compute_storage_with_replication", "args": [100, 1], "kwargs": {}}$$, $${"result": 100}$$, true, 'function_call', 10),
  (131, 'fc_storage_replication_5', $${"function": "compute_storage_with_replication", "args": [100, 5], "kwargs": {}}$$, $${"result": 500}$$, true, 'function_call', 11),
  (131, 'fc_storage_large_file', $${"function": "compute_storage_with_replication", "args": [1073741824], "kwargs": {}}$$, $${"result": 3221225472}$$, true, 'function_call', 12),
  (131, 'fc_storage_raises_on_negative_replication', $${"function": "compute_storage_with_replication", "args": [100, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 13),
  (131, 'fc_storage_raises_on_non_int', $${"function": "compute_storage_with_replication", "args": [100.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 14),
  (131, 'fc_block_size_64mb_valid', $${"function": "is_block_size_valid", "args": [67108864], "kwargs": {}}$$, $${"result": true}$$, false, 'function_call', 15),
  (131, 'fc_block_size_too_small', $${"function": "is_block_size_valid", "args": [524288], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 16),
  (131, 'fc_block_size_too_big', $${"function": "is_block_size_valid", "args": [2147483648], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 17),
  (131, 'fc_block_size_not_power_of_2', $${"function": "is_block_size_valid", "args": [104857600], "kwargs": {}}$$, $${"result": false}$$, true, 'function_call', 18),
  (131, 'fc_block_size_raises_on_non_int', $${"function": "is_block_size_valid", "args": [128.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 19),
  (131, 'fc_meta_one_million', $${"function": "compute_namenode_metadata_size", "args": [1000000], "kwargs": {}}$$, $${"result": 150000000}$$, false, 'function_call', 20),
  (131, 'fc_meta_100_files', $${"function": "compute_namenode_metadata_size", "args": [100], "kwargs": {}}$$, $${"result": 15000}$$, true, 'function_call', 21),
  (131, 'fc_meta_custom_bytes', $${"function": "compute_namenode_metadata_size", "args": [100, 200], "kwargs": {}}$$, $${"result": 20000}$$, true, 'function_call', 22),
  (131, 'fc_meta_zero_files', $${"function": "compute_namenode_metadata_size", "args": [0], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 23),
  (131, 'fc_meta_default_bytes', $${"function": "compute_namenode_metadata_size", "args": [50], "kwargs": {}}$$, $${"result": 7500}$$, true, 'function_call', 24),
  (131, 'fc_meta_raises_on_negative_files', $${"function": "compute_namenode_metadata_size", "args": [-1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 25),
  (131, 'fc_meta_raises_on_zero_bytes', $${"function": "compute_namenode_metadata_size", "args": [100, 0], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 26),
  (131, 'fc_meta_raises_on_non_int', $${"function": "compute_namenode_metadata_size", "args": [100.0], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 27);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=131 GROUP BY task_id;

COMMIT;