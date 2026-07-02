#!/usr/bin/env python3
"""Map functions to tasks and run attack analysis."""
import json
from collections import Counter

with open('/tmp/p3_redesign/all_cases.json') as f:
    cases = json.load(f)

# Map: task_id -> {func_name, sig}
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

def hashable(v):
    if isinstance(v, dict):
        return tuple(sorted((str(k), hashable(val)) for k, val in v.items()))
    if isinstance(v, list):
        return tuple(hashable(x) for x in v)
    return v

def analyze_function(test_list):
    n = len(test_list)
    result_cases = [t for t in test_list if t['exp'] != 'raises']
    if not result_cases:
        return {'stub_fail': 1.0, 'hard_best_pass': 0, 'hard_generic_pass': 0, 'identity_pass': 0, 'fail_rate': 1.0, 'need_fix': False}
    stub_fail = len(result_cases) / n
    vals = [t['exp'] for t in result_cases]
    vals_h = [hashable(v) for v in vals]
    cnt = Counter(vals_h)
    best_cnt = cnt.most_common(1)[0][1]
    hard_best_pass = best_cnt / len(vals)
    generic_vals = (0, 1, True, False, "", None)
    generic_hits = sum(1 for t in result_cases if t['exp'] in generic_vals)
    hard_generic_pass = generic_hits / len(result_cases)
    identity_hits = sum(1 for t in result_cases if t['args'] and t['args'][0] == t['exp'])
    identity_pass = identity_hits / len(result_cases)
    worst_pass = max(hard_best_pass, hard_generic_pass, identity_pass)
    fail_rate = 1 - worst_pass
    need_fix = fail_rate < 0.8
    return {
        'stub_fail': stub_fail, 'hard_best_pass': hard_best_pass,
        'hard_generic_pass': hard_generic_pass, 'identity_pass': identity_pass,
        'fail_rate': fail_rate, 'need_fix': need_fix
    }

print(f"{'='*90}")
print(f"  P3 Redesign Attack Analysis - 22 关 × 4 函数 × 7-12 测试")
print(f"{'='*90}")
print(f"{'Task':>6} {'Title':<28} {'Tests':>6} {'Funcs':>5} {'A.Stub':>7} {'B.HBest':>8} {'Fix':>10}")
print(f"{'-'*90}")

all_need_fix = []
total_tasks_pass = 0
total_tasks = 0

# WX first
for tid in [118,119,120,121,122,123,124,125,126,127,128]:
    fns = TASK_FUNCS[tid]
    test_count = sum(len(cases[fn]) for fn in fns if fn in cases)
    any_fix = False
    worst_best = 0
    for fn in fns:
        if fn in cases:
            a = analyze_function(cases[fn])
            if a['need_fix']: any_fix = True
            worst_best = max(worst_best, a['hard_best_pass'])
    total_tasks += 1
    if not any_fix: total_tasks_pass += 1
    all_need_fix.append(any_fix)
    flag = 'YES ⚠️' if any_fix else 'PASS ✓'
    print(f"{tid:>6} {'(WX) 关卡'+str(tid-117):<28} {test_count:>6} {len(fns):>5} {'':>7} {worst_best:>7.0%} {flag:>10}")
    for fn in fns:
        if fn in cases:
            a = analyze_function(cases[fn])
            marker = ' ⚠️' if a['need_fix'] else ' ✓'
            print(f"      {fn:<28} n={len(cases[fn]):>2} stub={a['stub_fail']:>5.0%} hbest={a['hard_best_pass']:>5.0%} hgen={a['hard_generic_pass']:>5.0%} iden={a['identity_pass']:>5.0%} fail={a['fail_rate']:>5.0%}{marker}")

print()
for tid in [130,131,132,133,134,135,136,137,138,139,140]:
    fns = TASK_FUNCS[tid]
    test_count = sum(len(cases[fn]) for fn in fns if fn in cases)
    any_fix = False
    worst_best = 0
    for fn in fns:
        if fn in cases:
            a = analyze_function(cases[fn])
            if a['need_fix']: any_fix = True
            worst_best = max(worst_best, a['hard_best_pass'])
    total_tasks += 1
    if not any_fix: total_tasks_pass += 1
    all_need_fix.append(any_fix)
    flag = 'YES ⚠️' if any_fix else 'PASS ✓'
    print(f"{tid:>6} {'(BD) 关卡'+str(tid-128):<28} {test_count:>6} {len(fns):>5} {'':>7} {worst_best:>7.0%} {flag:>10}")
    for fn in fns:
        if fn in cases:
            a = analyze_function(cases[fn])
            marker = ' ⚠️' if a['need_fix'] else ' ✓'
            print(f"      {fn:<28} n={len(cases[fn]):>2} stub={a['stub_fail']:>5.0%} hbest={a['hard_best_pass']:>5.0%} hgen={a['hard_generic_pass']:>5.0%} iden={a['identity_pass']:>5.0%} fail={a['fail_rate']:>5.0%}{marker}")

print(f"\n{'='*90}")
print(f"  总计: {total_tasks} 关, {total_tasks_pass} PASS, {total_tasks - total_tasks_pass} 需要修复")
print(f"{'='*90}")
