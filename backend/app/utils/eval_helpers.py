"""
Pure helper functions for the evaluation system.

Extracted from services/evaluation_system.py — no DB, no I/O, no subprocess.
"""
import json
import re
from typing import Dict, List, Any, Optional


def normalize_test_case(tc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a test case dict to use DB field names.

    Accepts both JSON-style field names (input/expected/hidden) and
    DB-style field names (input_data/expected_output/is_hidden).
    Returns a dict with DB field names for consistent DB writes.
    Also preserves all other fields unchanged.
    """
    result = dict(tc)  # shallow copy to avoid mutating original

    # Normalize input field: JSON "input" → DB "input_data"
    if "input" in result and "input_data" not in result:
        result["input_data"] = result.pop("input")
    elif "input_data" in result:
        pass  # already DB-style, no change needed

    # Normalize expected field: JSON "expected" → DB "expected_output"
    # Also handle "expected_output" which may already be present (e.g. from DB model)
    if "expected" in result and "expected_output" not in result:
        result["expected_output"] = result.pop("expected")
    elif "expected" in result and "expected_output" in result:
        # Both present (e.g. JSON merged with DB row) — prefer DB-style
        result.pop("expected")
    # else: already DB-style or not present

    # Normalize hidden field: JSON "hidden" → DB "is_hidden"
    if "hidden" in result and "is_hidden" not in result:
        result["is_hidden"] = bool(result.pop("hidden"))
    elif "hidden" in result and "is_hidden" in result:
        result.pop("hidden")
    # else: already DB-style or not present

    return result


# ==================== Output matching ====================

def match_output(output: str, expected: str, rule: str) -> bool:
    """
    Compare actual output against expected using the given match rule.

    Supported rules: 'exact', 'regex', 'json_equal', 'subset'.
    Unknown rules fall back to exact match.
    """
    if rule == "exact":
        return output == expected
    elif rule == "regex":
        return bool(re.match(expected, output))
    elif rule == "json_equal":
        try:
            return json.loads(output) == json.loads(expected)
        except (json.JSONDecodeError, TypeError):
            return False
    elif rule == "subset":
        return expected in output
    else:
        return output == expected


# ==================== Test case formatting ====================

def format_testcase(tc: Dict[str, Any], subtype: str) -> Dict[str, Any]:
    """
    Normalize a raw test case dict into a standard format based on subtype.

    Subtypes: script_io, sql_query, api_service, web_static,
              dataframe_task, function_unit (default).
    """
    formatted: Dict[str, Any] = {
        'id': tc.get('id', ''),
        'visible': tc.get('visible', False),
        'match_rule': tc.get('match_rule', 'exact'),
    }

    if subtype == "script_io":
        formatted.update({
            'input': tc.get('input', ''),
            'expected': tc.get('expected', tc.get('output', '')),
        })
    elif subtype == "sql_query":
        formatted.update({
            'sql': tc.get('sql', ''),
            'expected_rows': tc.get('expected_rows', []),
        })
    elif subtype == "api_service":
        formatted.update({
            'method': tc.get('method', 'GET'),
            'url': tc.get('url', '/'),
            'payload': tc.get('payload'),
            'expect_status': tc.get('expect_status', 200),
            'expect_json': tc.get('expect_json'),
        })
    elif subtype == "web_static":
        formatted.update({
            'page': tc.get('page', 'index.html'),
            'assert': tc.get('assert', {}),
        })
    elif subtype == "dataframe_task":
        formatted.update({
            'check': tc.get('check', 'shape'),
            'expected': tc.get('expected'),
            'tolerance': tc.get('tolerance', {'abs': 0.01}),
        })
    else:
        # function_unit default
        formatted.update({
            'function': tc.get('function', 'main'),
            'args': tc.get('args', []),
            'expected': tc.get('expected'),
        })

    return formatted


# ==================== Script generation ====================

def create_unit_test_script(testcases: List[Dict[str, Any]]) -> str:
    """
    Generate a Python unit test runner script from test case dicts.

    Each test case should have: function, args, expected, id, visible.
    """
    lines = [
        "import sys",
        "import json",
        "from submission import *",
        "",
        "results = []",
        "",
    ]

    for i, tc in enumerate(testcases):
        function = tc.get('function', 'main')
        args = tc.get('args', [])
        expected = tc.get('expected')
        test_id = tc.get('id', i + 1)
        visible = tc.get('visible', False)

        lines.append(f"# Test case {i + 1}")
        lines.append("try:")
        lines.append(f"    result = {function}({', '.join(map(repr, args))})")
        lines.append(f"    passed = result == {repr(expected)}")
        lines.append(f"    results.append({{'test_id': {repr(test_id)}, 'passed': passed, 'visible': {visible}}})")
        lines.append("except Exception as e:")
        lines.append(f"    results.append({{'test_id': {repr(test_id)}, 'passed': False, 'error': str(e), 'visible': {visible}}})")
        lines.append("")

    lines.append("print(json.dumps({'results': results}))")
    lines.append("sys.exit(0 if all(r['passed'] for r in results) else 1)")
    lines.append("")

    return "\n".join(lines)


def create_dataframe_eval_script(testcases: List[Dict[str, Any]]) -> str:
    """
    Generate a pandas DataFrame evaluation script from test case dicts.

    Supported checks: 'shape', 'columns'.
    """
    lines = [
        "import sys",
        "import json",
        "import pandas as pd",
        "import numpy as np",
        "from submission import *",
        "",
        "results = []",
        "df = get_dataframe()",
        "",
    ]

    for i, tc in enumerate(testcases):
        check = tc.get('check', 'shape')
        expected = tc.get('expected')
        test_id = tc.get('id', i + 1)
        visible = tc.get('visible', False)

        if check == 'shape':
            lines.append(f"# Check shape")
            lines.append(f"passed = df.shape == tuple({repr(expected)})")
        elif check == 'columns':
            lines.append(f"# Check columns")
            lines.append(f"passed = list(df.columns) == {repr(expected)}")
        else:
            lines.append(f"# Unknown check: {check}")
            lines.append("passed = False")

        lines.append(
            f"results.append({{'test_id': {repr(test_id)}, 'passed': passed, 'visible': {visible}}})"
        )
        lines.append("")

    lines.append("print(json.dumps({'results': results}))")
    lines.append("sys.exit(0 if all(r['passed'] for r in results) else 1)")
    lines.append("")

    return "\n".join(lines)
