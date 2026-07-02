-- BD08 (task_id=137) function_call task_tests — 24 条

BEGIN;

DELETE FROM task_tests WHERE task_id=137;

INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule, test_order) VALUES
  (137, 'fc_pps_overlap_2', $${"function": "compute_partition_pruning_set", "args": [["a", "b", "c"], ["b", "c", "d"]], "kwargs": {}}$$, $${"result": ["b", "c"]}$$, false, 'function_call', 1),
  (137, 'fc_pps_no_overlap', $${"function": "compute_partition_pruning_set", "args": [["x"], ["a", "b"]], "kwargs": {}}$$, $${"result": []}$$, true, 'function_call', 2),
  (137, 'fc_pps_all_in_filter', $${"function": "compute_partition_pruning_set", "args": [["c", "a"], ["a", "b", "c"]], "kwargs": {}}$$, $${"result": ["a", "c"]}$$, true, 'function_call', 3),
  (137, 'fc_pps_dedup_filter', $${"function": "compute_partition_pruning_set", "args": [["a", "a", "b"], ["a", "b", "c"]], "kwargs": {}}$$, $${"result": ["a", "b"]}$$, true, 'function_call', 4),
  (137, 'fc_pps_dates', $${"function": "compute_partition_pruning_set", "args": [["2026-04-25", "2026-04-26", "2026-04-30"], ["2026-04-25", "2026-04-26", "2026-04-27", "2026-04-28"]], "kwargs": {}}$$, $${"result": ["2026-04-25", "2026-04-26"]}$$, true, 'function_call', 5),
  (137, 'fc_pps_raises_on_non_list', $${"function": "compute_partition_pruning_set", "args": ["a,b", ["a"]], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 6),
  (137, 'fc_cost_no_join', $${"function": "estimate_query_cost", "args": [1000, 0], "kwargs": {}}$$, $${"result": 1000}$$, false, 'function_call', 7),
  (137, 'fc_cost_one_join', $${"function": "estimate_query_cost", "args": [1000, 1], "kwargs": {}}$$, $${"result": 2000}$$, true, 'function_call', 8),
  (137, 'fc_cost_three_joins', $${"function": "estimate_query_cost", "args": [500, 3], "kwargs": {}}$$, $${"result": 2000}$$, true, 'function_call', 9),
  (137, 'fc_cost_large', $${"function": "estimate_query_cost", "args": [1000000, 1], "kwargs": {}}$$, $${"result": 2000000}$$, true, 'function_call', 10),
  (137, 'fc_cost_raises_on_negative_rows', $${"function": "estimate_query_cost", "args": [-1, 1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 11),
  (137, 'fc_cost_raises_on_negative_joins', $${"function": "estimate_query_cost", "args": [100, -1], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 12),
  (137, 'fc_cost_raises_on_non_int', $${"function": "estimate_query_cost", "args": [100.0, 1], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 13),
  (137, 'fc_bcast_right_small', $${"function": "should_use_broadcast_join", "args": [10000000, 1000], "kwargs": {}}$$, $${"result": "broadcast"}$$, false, 'function_call', 14),
  (137, 'fc_bcast_both_large', $${"function": "should_use_broadcast_join", "args": [5000000, 10000000], "kwargs": {}}$$, $${"result": "shuffle"}$$, true, 'function_call', 15),
  (137, 'fc_bcast_at_threshold', $${"function": "should_use_broadcast_join", "args": [1000000, 5000000], "kwargs": {}}$$, $${"result": "shuffle"}$$, true, 'function_call', 16),
  (137, 'fc_bcast_custom_threshold', $${"function": "should_use_broadcast_join", "args": [50, 1000, 100], "kwargs": {}}$$, $${"result": "broadcast"}$$, true, 'function_call', 17),
  (137, 'fc_bcast_raises_on_zero', $${"function": "should_use_broadcast_join", "args": [0, 100], "kwargs": {}}$$, $${"raises": "ValueError"}$$, true, 'function_call', 18),
  (137, 'fc_bcast_raises_on_non_int', $${"function": "should_use_broadcast_join", "args": [100.0, 200], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 19),
  (137, 'fc_dist_typical', $${"function": "count_distinct_simple", "args": [[1, 2, 3, 2, 1]], "kwargs": {}}$$, $${"result": 3}$$, false, 'function_call', 20),
  (137, 'fc_dist_all_same', $${"function": "count_distinct_simple", "args": [[1, 1, 1]], "kwargs": {}}$$, $${"result": 1}$$, true, 'function_call', 21),
  (137, 'fc_dist_strings', $${"function": "count_distinct_simple", "args": [["a", "b", "a", "c"]], "kwargs": {}}$$, $${"result": 3}$$, true, 'function_call', 22),
  (137, 'fc_dist_empty', $${"function": "count_distinct_simple", "args": [[]], "kwargs": {}}$$, $${"result": 0}$$, true, 'function_call', 23),
  (137, 'fc_dist_raises_on_non_list', $${"function": "count_distinct_simple", "args": ["abc"], "kwargs": {}}$$, $${"raises": "TypeError"}$$, true, 'function_call', 24);

SELECT task_id, COUNT(*) AS total, COUNT(DISTINCT match_rule) AS rules,
       string_agg(DISTINCT match_rule, ',') AS rule_set,
       SUM(CASE WHEN is_hidden THEN 1 ELSE 0 END) AS hidden_count
  FROM task_tests WHERE task_id=137 GROUP BY task_id;

COMMIT;