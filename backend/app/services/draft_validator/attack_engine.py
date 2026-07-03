"""对抗攻击门禁引擎（慧学AI升级方案-v2 第九章）。

职责：
  1. 给定一份 evaluator 测试代码（pytest 文件路径或字符串）+ 一份可通过的参考答案代码，
     针对参考答案中定义的每个顶层函数，自动生成 4 类攻击提交：
       A. Stub      —— 函数体只有 `pass` / `return None`
       B. Hardcode  —— 返回数值常量 / 全 0 dict / 全 0 array
       C. Shape-only —— 返回形状对但内容错的值（np.eye / np.zeros 等价物）
       D. Identity  —— 直接原样返回第一个参数，不做任何变换
  2. 把每类攻击提交换掉参考答案对应的学生模块，实际用 subprocess 跑 pytest
     （复用 backend/app/services/code_executor.py 里 execute_pytest_module 同样的
     "student module 写入 tmpdir + pytest 跑测试文件" 打法），统计 fail 率。
  3. 判定标准：A 类必须 100% fail；B/C/D 类必须 >= 80% fail。
  4. 同时提供 5 条 test_cases 红线检查 (check_redlines)。

本模块不导入、不依赖 code_executor.py 中任何符号，只是复用同样的执行范式，
避免与其他并行开发的模块产生耦合。
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


PYTEST_TIMEOUT_SECONDS = 60

# 判定标准（第九章）
STUB_REQUIRED_FAIL_RATE = 1.0
HARDCODE_REQUIRED_FAIL_RATE = 0.8
SHAPE_REQUIRED_FAIL_RATE = 0.8
IDENTITY_REQUIRED_FAIL_RATE = 0.8

_SUMMARY_RE = re.compile(
    r"(?:(?P<failed>\d+) failed)?.*?(?:(?P<passed>\d+) passed)?.*?in [\d.]+s"
)
# pytest -q 摘要行形如 "3 failed, 5 passed in 0.12s" 或 "5 passed in 0.05s"
_PASSED_RE = re.compile(r"(\d+) passed")
_FAILED_RE = re.compile(r"(\d+) failed")
_ERROR_RE = re.compile(r"(\d+) error")


@dataclass
class PytestRunResult:
    """一次 pytest 子进程运行的结构化结果。"""

    total: int
    passed: int
    failed: int
    errored: int
    fail_rate: float
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False

    @property
    def ok_ran(self) -> bool:
        """是否成功跑起来了 pytest（不代表测试都通过）。"""
        return not self.timed_out and self.total > 0


def _parse_pytest_summary(stdout: str) -> Dict[str, int]:
    """从 pytest -q 的 stdout 尾部解析 passed/failed/error 数量。"""
    passed = 0
    failed = 0
    errored = 0
    # 只看末尾摘要行，避免误匹配测试内容里的数字
    tail_lines = [l for l in stdout.strip().splitlines()[-5:]]
    tail = "\n".join(tail_lines)
    m = _PASSED_RE.search(tail)
    if m:
        passed = int(m.group(1))
    m = _FAILED_RE.search(tail)
    if m:
        failed = int(m.group(1))
    m = _ERROR_RE.search(tail)
    if m:
        errored = int(m.group(1))
    return {"passed": passed, "failed": failed, "errored": errored}


def run_pytest_module(
    test_file_name: str,
    test_file_content: str,
    student_module_name: str,
    student_code: str,
    timeout: int = PYTEST_TIMEOUT_SECONDS,
) -> PytestRunResult:
    """在临时目录内实际用 subprocess 跑一次 pytest_module 协议测试。

    打法与 backend/app/services/code_executor.py::execute_pytest_module 一致：
      tmpdir/<student_module_name>.py = student_code
      tmpdir/<test_file_name>         = test_file_content
      python -m pytest <test_file_name> --tb=line --no-header -q
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        student_file = Path(tmpdir) / f"{student_module_name}.py"
        student_file.write_text(student_code, encoding="utf-8")

        test_file = Path(tmpdir) / test_file_name
        test_file.write_text(test_file_content, encoding="utf-8")

        try:
            proc = subprocess.run(
                [
                    sys.executable, "-m", "pytest", str(test_file),
                    "--tb=line", "--no-header", "-q", f"--rootdir={tmpdir}",
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired as e:
            return PytestRunResult(
                total=0, passed=0, failed=0, errored=0, fail_rate=1.0,
                returncode=-1, stdout=e.stdout or "", stderr=e.stderr or "",
                timed_out=True,
            )

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        summary = _parse_pytest_summary(stdout)
        total = summary["passed"] + summary["failed"] + summary["errored"]
        fail_count = summary["failed"] + summary["errored"]
        fail_rate = (fail_count / total) if total > 0 else 1.0

        return PytestRunResult(
            total=total,
            passed=summary["passed"],
            failed=summary["failed"],
            errored=summary["errored"],
            fail_rate=fail_rate,
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr,
        )


# ============================================================
# 攻击提交生成
# ============================================================

def _extract_top_level_functions(reference_code: str) -> List[ast.FunctionDef]:
    """从参考答案源码里取出所有顶层函数定义（不含内部函数/方法）。"""
    tree = ast.parse(reference_code)
    return [n for n in tree.body if isinstance(n, ast.FunctionDef)]


def _function_signature_source(node: ast.FunctionDef) -> str:
    """还原函数签名（def name(args):）文本，兼容 *args/**kwargs/默认值。"""
    args = node.args
    parts: List[str] = []

    defaults = list(args.defaults)
    n_no_default = len(args.args) - len(defaults)
    for i, a in enumerate(args.args):
        if i >= n_no_default:
            default_node = defaults[i - n_no_default]
            parts.append(f"{a.arg}={ast.unparse(default_node)}")
        else:
            parts.append(a.arg)

    if args.vararg:
        parts.append(f"*{args.vararg.arg}")
    elif args.kwonlyargs:
        parts.append("*")

    for kw, default_node in zip(args.kwonlyargs, args.kw_defaults):
        if default_node is not None:
            parts.append(f"{kw.arg}={ast.unparse(default_node)}")
        else:
            parts.append(kw.arg)

    if args.kwarg:
        parts.append(f"**{args.kwarg.arg}")

    return f"def {node.name}({', '.join(parts)}):"


def _first_param_name(node: ast.FunctionDef) -> Optional[str]:
    if node.args.args:
        return node.args.args[0].arg
    if node.args.vararg:
        return node.args.vararg.arg
    return None


def build_stub_submission(reference_code: str) -> str:
    """A. Stub 攻击：所有函数体替换为 `pass`（隐式 return None）。"""
    lines = ["import numpy as np", ""]
    for node in _extract_top_level_functions(reference_code):
        lines.append(_function_signature_source(node))
        lines.append("    pass")
        lines.append("")
    return "\n".join(lines)


def build_hardcode_submission(reference_code: str) -> str:
    """B. Hardcode 攻击：所有函数返回常量 0 / 空 dict / 空 list，不看输入。"""
    lines = ["import numpy as np", ""]
    for node in _extract_top_level_functions(reference_code):
        lines.append(_function_signature_source(node))
        lines.append("    return 0")
        lines.append("")
    return "\n".join(lines)


def build_shape_only_submission(reference_code: str) -> str:
    """C. Shape-only 攻击：形状对内容错——用 dict()/list()/np.zeros 占位。"""
    lines = ["import numpy as np", ""]
    for node in _extract_top_level_functions(reference_code):
        lines.append(_function_signature_source(node))
        # 尝试猜测返回类型：函数名含 list -> [], 含 dict/summarize/report -> {}
        name = node.name.lower()
        if "dict" in name or "summar" in name or "report" in name:
            lines.append("    return {}")
        elif "count" in name or "num" in name or "rate" in name:
            lines.append("    return 0")
        else:
            lines.append("    return []")
        lines.append("")
    return "\n".join(lines)


def build_identity_submission(reference_code: str) -> str:
    """D. Identity 攻击：直接原样返回第一个参数，不做任何变换。"""
    lines = ["import numpy as np", ""]
    for node in _extract_top_level_functions(reference_code):
        first_param = _first_param_name(node)
        lines.append(_function_signature_source(node))
        if first_param:
            lines.append(f"    return {first_param}")
        else:
            lines.append("    return None")
        lines.append("")
    return "\n".join(lines)


ATTACK_BUILDERS = {
    "stub": build_stub_submission,
    "hardcode": build_hardcode_submission,
    "shape": build_shape_only_submission,
    "identity": build_identity_submission,
}

ATTACK_THRESHOLDS = {
    "stub": STUB_REQUIRED_FAIL_RATE,
    "hardcode": HARDCODE_REQUIRED_FAIL_RATE,
    "shape": SHAPE_REQUIRED_FAIL_RATE,
    "identity": IDENTITY_REQUIRED_FAIL_RATE,
}


@dataclass
class AttackMatrixResult:
    stub_fail_rate: float
    hardcode_fail_rate: float
    shape_fail_rate: float
    identity_fail_rate: float
    passed: bool
    detail: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "stub_fail_rate": self.stub_fail_rate,
            "hardcode_fail_rate": self.hardcode_fail_rate,
            "shape_fail_rate": self.shape_fail_rate,
            "identity_fail_rate": self.identity_fail_rate,
            "passed": self.passed,
            "detail": self.detail,
        }


def run_attack_matrix(
    test_file_name: str,
    test_file_content: str,
    student_module_name: str,
    reference_code: str,
    timeout: int = PYTEST_TIMEOUT_SECONDS,
    custom_submissions: Optional[Dict[str, str]] = None,
) -> AttackMatrixResult:
    """跑完整 4 类攻击矩阵，返回结构化结果 (写入 ai_validation_results 攻击矩阵字段)。

    custom_submissions: 可选，{"stub": "...", "hardcode": "...", ...}
        用于跳过自动生成、直接指定攻击提交代码（例如验收脚本手写的攻击样例）。
    """
    custom_submissions = custom_submissions or {}
    detail: Dict[str, Any] = {}
    rates: Dict[str, float] = {}

    for attack_type, builder in ATTACK_BUILDERS.items():
        submission = custom_submissions.get(attack_type) or builder(reference_code)
        result = run_pytest_module(
            test_file_name=test_file_name,
            test_file_content=test_file_content,
            student_module_name=student_module_name,
            student_code=submission,
            timeout=timeout,
        )
        rates[attack_type] = result.fail_rate
        detail[attack_type] = {
            "fail_rate": result.fail_rate,
            "total": result.total,
            "passed": result.passed,
            "failed": result.failed,
            "errored": result.errored,
            "threshold": ATTACK_THRESHOLDS[attack_type],
            "meets_threshold": result.fail_rate >= ATTACK_THRESHOLDS[attack_type],
            "timed_out": result.timed_out,
            "returncode": result.returncode,
            "stdout_tail": "\n".join((result.stdout or "").strip().splitlines()[-10:]),
        }

    passed = all(d["meets_threshold"] for d in detail.values())

    return AttackMatrixResult(
        stub_fail_rate=rates["stub"],
        hardcode_fail_rate=rates["hardcode"],
        shape_fail_rate=rates["shape"],
        identity_fail_rate=rates["identity"],
        passed=passed,
        detail=detail,
    )


# ============================================================
# 5 条 test_cases 红线检查
# ============================================================

_TOLERANCE_ASSERT_RE = re.compile(r"abs\s*\([^)]*\)\s*<")
_FLOAT_EQ_RE = re.compile(r"==\s*-?\d+\.\d+|(?<![\w.])-?\d+\.\d+\s*==")
_RAISES_RE = re.compile(r"pytest\.raises|with\s+self\.assertRaises")
_SENTINEL_RE = re.compile(r"is\s+None|==\s*None|is\s+False|==\s*-1")


def _group_asserts_by_test_function(test_code: str) -> Dict[str, List[str]]:
    """把测试代码按 `def test_xxx(...):` 分组，每组收集函数体源码行。

    启发式实现：不要求完美 AST 精度，只用于红线粗检查。
    """
    tree = ast.parse(test_code)
    groups: Dict[str, List[str]] = {}
    lines = test_code.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            start = node.lineno - 1
            end = getattr(node, "end_lineno", start + 1)
            groups[node.name] = lines[start:end]
    return groups


def _count_distinct_call_args(source_lines: List[str]) -> int:
    """粗略统计一个测试函数体里出现的"看起来像独立输入"的函数调用参数组合数。

    启发式：统计非空括号调用的次数作为独立输入的下界估计。
    """
    text = "\n".join(source_lines)
    calls = re.findall(r"\w+\s*\(([^()]*)\)", text)
    non_empty = [c for c in calls if c.strip()]
    return len(non_empty)


_BOUNDARY_HINTS = re.compile(
    r"\[\]|\{\}|None|0\b|-1\b|float\(['\"]inf['\"]\)|len\(.*\)\s*==\s*0|empty|single|极值|边界"
)


def check_redlines(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
    """检查 5 条 test_cases 红线，返回 每函数 x 5 列 的 ✓/✗ 矩阵。

    test_cases: 可以是
      - [{"function": "clean_operation_rows", "test_code": "def test_..."}, ...] 结构化条目, 或
      - [{"test_code": "<整份测试文件源码>"}] 单条整份源码

    返回结构:
      {
        "matrix": {func_name: {"r1_min3_inputs": bool, "r2_boundary": bool,
                                 "r3_negative_type_assert": bool,
                                 "r4_tolerance_not_eq": bool,
                                 "r5_full_coverage_assert": bool}},
        "all_passed": bool,
      }
    """
    # 汇总所有测试源码文本
    full_source_parts: List[str] = []
    for case in test_cases:
        code = case.get("test_code") or case.get("source") or ""
        if code:
            full_source_parts.append(code)
    full_source = "\n\n".join(full_source_parts)

    if not full_source.strip():
        return {"matrix": {}, "all_passed": False, "error": "test_cases 为空或不含 test_code"}

    try:
        by_func = _group_asserts_by_test_function(full_source)
    except SyntaxError as e:
        return {"matrix": {}, "all_passed": False, "error": f"test_code 解析失败: {e}"}

    if not by_func:
        return {"matrix": {}, "all_passed": False, "error": "未找到任何 test_ 开头的测试函数"}

    # 按「被测函数名」聚合（从测试函数体里提取被调用的非 test_ 函数名做粗略归类）
    call_name_re = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")

    def _guess_target_function(body_lines: List[str]) -> str:
        text = "\n".join(body_lines)
        names = call_name_re.findall(text)
        candidates = [n for n in names if not n.startswith("test_") and n not in (
            "assert", "len", "abs", "isinstance", "str", "int", "float", "list", "dict",
            "set", "range", "sorted", "sum", "print",
        )]
        return candidates[0] if candidates else "_unknown"

    grouped: Dict[str, List[List[str]]] = {}
    for test_name, body_lines in by_func.items():
        target = _guess_target_function(body_lines)
        grouped.setdefault(target, []).append(body_lines)

    matrix: Dict[str, Dict[str, bool]] = {}
    for func_name, test_bodies in grouped.items():
        combined_lines = [l for body in test_bodies for l in body]
        combined_text = "\n".join(combined_lines)

        # ① 每函数至少 3 个独立输入 —— 用「覆盖该函数的独立 test_ 函数数」作代理指标
        r1 = len(test_bodies) >= 3

        # ② 至少 1 个边界用例
        r2 = bool(_BOUNDARY_HINTS.search(combined_text))

        # ③ 至少 1 个负例 type 断言（raise 或 sentinel 判断）
        r3 = bool(_RAISES_RE.search(combined_text) or _SENTINEL_RE.search(combined_text))

        # ④ 数值断言用 tolerance，禁止浮点 == 严格相等
        has_float_eq = bool(_FLOAT_EQ_RE.search(combined_text))
        has_tolerance = bool(_TOLERANCE_ASSERT_RE.search(combined_text))
        # 只要没有浮点 == 严格比较即可通过；若压根没有浮点断言，视为不适用 -> 通过
        r4 = (not has_float_eq) or has_tolerance

        # ⑤ dict/list 返回断言覆盖所有 key/element（启发式：出现 keys()/all(/in / 逐项断言）
        r5 = bool(re.search(r"\.keys\(\)|all\(|for\s+\w+\s+in\s+|==\s*\[.+\]|==\s*\{.+\}", combined_text))

        matrix[func_name] = {
            "r1_min3_inputs": r1,
            "r2_boundary": r2,
            "r3_negative_type_assert": r3,
            "r4_tolerance_not_eq": r4,
            "r5_full_coverage_assert": r5,
        }

    all_passed = all(all(row.values()) for row in matrix.values())
    return {"matrix": matrix, "all_passed": all_passed}


class AttackEngine:
    """面向 draft_id 的攻击门禁引擎入口，封装 run_attack_matrix + check_redlines。

    典型用法::

        engine = AttackEngine(
            test_file_name="test_xx.py",
            test_file_content=open(test_path).read(),
            student_module_name="student_xx",
        )
        result = engine.run(reference_code=reference_answer_code)
        redlines = engine.check_redlines(test_cases)
    """

    def __init__(self, test_file_name: str, test_file_content: str, student_module_name: str,
                 timeout: int = PYTEST_TIMEOUT_SECONDS):
        self.test_file_name = test_file_name
        self.test_file_content = test_file_content
        self.student_module_name = student_module_name
        self.timeout = timeout

    def run_reference(self, reference_code: str) -> PytestRunResult:
        """先验证参考答案本身能不能通过（不属于攻击验证，但通常作为前置条件）。"""
        return run_pytest_module(
            self.test_file_name, self.test_file_content,
            self.student_module_name, reference_code, timeout=self.timeout,
        )

    def run(self, reference_code: str,
            custom_submissions: Optional[Dict[str, str]] = None) -> AttackMatrixResult:
        return run_attack_matrix(
            test_file_name=self.test_file_name,
            test_file_content=self.test_file_content,
            student_module_name=self.student_module_name,
            reference_code=reference_code,
            timeout=self.timeout,
            custom_submissions=custom_submissions,
        )

    @staticmethod
    def check_redlines(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        return check_redlines(test_cases)
