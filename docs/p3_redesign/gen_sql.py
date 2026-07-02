#!/usr/bin/env python3
"""Generate SQL UPDATE statements for task_tests."""
import json

with open('/tmp/p3_redesign/all_cases.json') as f:
    cases = json.load(f)

# task_id -> [func_name]
TASK_FUNCS = {
    118: ['classify_value_status', 'compute_quality_ratio', 'get_cleaning_priority', 'decide_drop_or_fill'],
    119: ['is_missing', 'count_missing', 'fill_missing_with_constant', 'fill_missing_with_mean'],
    120: ['is_exact_duplicate', 'count_duplicate_rows', 'dedup_keep_first', 'dedup_preserve_first'],
    121: ['is_outlier_iqr', 'count_outliers', 'compute_iqr_bounds', 'clip_value_to_range'],
    122: ['is_valid_email_basic', 'normalize_email_lower', 'normalize_phone_digits', 'parse_simple_date_iso'],
    123: ['is_pure_ascii', 'has_utf8_bom', 'count_non_ascii', 'remove_control_chars'],
    124: ['collapse_internal_whitespace', 'trim_whitespace', 'truncate_to_length', 'remove_punctuation'],
    125: ['is_numeric_string', 'clip_to_range', 'parse_numeric_string', 'round_half_up'],
    126: ['has_unique_keys', 'is_one_to_one_mapping', 'count_referential_violations', 'find_orphan_keys'],
    127: ['compute_merge_size', 'merge_inner_by_key', 'merge_left_by_key', 'dedup_dicts_by_key'],
    128: ['compute_completeness', 'compute_uniqueness', 'compute_validity_in_range', 'quality_summary_dict'],
    130: ['get_hadoop_component_role', 'compute_cluster_node_count', 'is_hadoop_safe_mode_ok', 'get_hadoop_default_port'],
    131: ['is_block_size_valid', 'compute_hdfs_block_count', 'compute_namenode_metadata_size', 'compute_storage_with_replication'],
    132: ['is_replication_factor_valid', 'count_blocks_to_re_replicate', 'compute_data_locality_score', 'assign_replicas_round_robin'],
    133: ['is_combinable_operation', 'partition_by_hash', 'compute_map_task_count', 'compute_reduce_task_count'],
    134: ['top_k_frequent', 'inverted_index', 'compute_co_occurrence', 'word_count'],
    135: ['is_resource_request_valid', 'compute_yarn_container_count', 'assign_yarn_queue', 'compute_fair_share_for_job'],
    136: ['is_partition_pruning_helpful', 'compute_partition_count', 'get_hive_storage_format', 'compute_data_warehouse_size'],
    137: ['estimate_query_cost', 'should_use_broadcast_join', 'count_distinct_simple', 'compute_partition_pruning_set'],
    138: ['is_hot_row_key', 'compute_region_count', 'compute_block_cache_hit_rate', 'design_row_key_with_salt'],
    139: ['is_incremental_import_valid', 'select_split_column_strategy', 'compute_split_size', 'compute_migration_time_seconds'],
    140: ['is_message_lag_critical', 'compute_minimum_replication', 'compute_throughput_bytes_per_sec', 'assign_consumer_partitions'],
}

def make_input_data(fn, args):
    return {"function": fn, "args": args, "kwargs": {}}

def make_expected(exp):
    if exp == 'raises':
        return None
    if isinstance(exp, float) or isinstance(exp, int):
        return {"result": exp, "tolerance": 1e-06}
    if isinstance(exp, dict) or isinstance(exp, list):
        return {"result": exp}
    return {"result": exp}

def get_prefix(task_id):
    if task_id in TASK_FUNCS and task_id < 130:
        return f"wx{task_id-117:02d}"
    return f"bd{task_id-128:02d}"

# Generate SQL
sql_lines = []
sql_lines.append("-- P3 audit redesign: replace 22 WX/BD tasks task_tests")
sql_lines.append("-- Generated from /tmp/p3_redesign/all_cases.json")
sql_lines.append("-- Total: 22 tasks, 88 functions, ~800 test cases")
sql_lines.append("")
sql_lines.append("BEGIN;")
sql_lines.append("")

total = 0
for tid, funcs in TASK_FUNCS.items():
    sql_lines.append(f"-- Task {tid}: {len(funcs)} functions")
    sql_lines.append(f"DELETE FROM task_tests WHERE task_id = {tid};")
    new_cases = 0
    prefix = get_prefix(tid)
    for fn in funcs:
        if fn not in cases:
            continue
        for i, tc in enumerate(cases[fn]):
            inp = make_input_data(fn, tc['args'])
            exp = tc['exp']
            if exp == 'raises':
                expected = {"raises": "ValueError"}
            else:
                expected = make_expected(exp)
            case_id = f"fc_{prefix}_{fn}_{i}"
            sql_lines.append(
                f"INSERT INTO task_tests (task_id, case_id, input_data, expected_output, is_hidden, match_rule) "
                f"VALUES ({tid}, '{case_id}', "
                f"'{json.dumps(inp, ensure_ascii=False)}', "
                f"'{json.dumps(expected, ensure_ascii=False)}', false, 'function_call');"
            )
            new_cases += 1
            total += 1
    sql_lines.append(f"-- Task {tid}: inserted {new_cases} test cases")
    sql_lines.append("")

sql_lines.append("COMMIT;")
sql_lines.append(f"-- Total: {total} test cases inserted across {len(TASK_FUNCS)} tasks")

with open('/tmp/p3_redesign/apply_tests.sql', 'w') as f:
    f.write('\n'.join(sql_lines))

print(f"Generated SQL with {total} test cases for {len(TASK_FUNCS)} tasks")
print(f"Written to /tmp/p3_redesign/apply_tests.sql")
print(f"File size: {sum(1 for _ in open('/tmp/p3_redesign/apply_tests.sql'))} lines")