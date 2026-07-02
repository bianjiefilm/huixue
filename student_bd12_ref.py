"""BD12 ref."""
from typing import List, Dict


def validate_pipeline_input_schema(stages):
    if not isinstance(stages, list):
        raise TypeError("stages must be list")
    for s in stages:
        if not isinstance(s, dict):
            raise TypeError("stage must be dict")
        if "name" not in s or "tool" not in s or "output_size_gb" not in s:
            return False
        if not isinstance(s["name"], str) or not isinstance(s["tool"], str):
            return False
        sz = s["output_size_gb"]
        if not isinstance(sz, (int, float)) or isinstance(sz, bool) or sz < 0:
            return False
    return True


def get_tool_for_purpose(purpose):
    if not isinstance(purpose, str):
        raise TypeError("purpose must be str")
    mapping = {'storage': 'hdfs', 'compute': 'mapreduce', 'scheduling': 'yarn',
               'sql': 'hive', 'nosql': 'hbase', 'streaming': 'kafka', 'migration': 'sqoop'}
    if purpose not in mapping:
        raise ValueError(f"unknown purpose: {purpose}")
    return mapping[purpose]


def compute_pipeline_total_size(stages):
    if not isinstance(stages, list):
        raise TypeError("stages must be list")
    total = 0.0
    for s in stages:
        if not isinstance(s, dict) or "output_size_gb" not in s:
            raise ValueError("stage missing output_size_gb")
        sz = s["output_size_gb"]
        if not isinstance(sz, (int, float)) or isinstance(sz, bool):
            raise TypeError("output_size_gb must be number")
        if sz < 0:
            raise ValueError("output_size_gb must be >= 0")
        total += sz
    return float(total)


def combine_bd_pipeline_report(stages_done, stages_total, errors):
    if not isinstance(stages_done, int) or isinstance(stages_done, bool):
        raise TypeError("stages_done must be int")
    if not isinstance(stages_total, int) or isinstance(stages_total, bool):
        raise TypeError("stages_total must be int")
    if not isinstance(errors, dict):
        raise TypeError("errors must be dict")
    if stages_total <= 0:
        raise ValueError("stages_total must be > 0")
    if stages_done < 0 or stages_done > stages_total:
        raise ValueError("stages_done out of [0, stages_total]")
    for k, v in errors.items():
        if not isinstance(v, int) or isinstance(v, bool) or v < 0:
            raise ValueError(f"errors[{k}] must be non-negative int")
    progress = stages_done / stages_total
    total_errors = sum(errors.values())
    return {
        'stages_done': stages_done,
        'stages_total': stages_total,
        'progress_ratio': progress,
        'errors': errors,
        'total_errors': total_errors,
        'is_success': progress == 1.0 and total_errors == 0,
    }
