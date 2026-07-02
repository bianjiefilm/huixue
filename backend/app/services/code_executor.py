#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代码执行服务
用于在安全环境中执行学生提交的代码并进行评测
"""

import json
import subprocess
import tempfile
import os
import sys
import traceback
from typing import Dict, Any, List, Optional
from pathlib import Path
import shutil
import time

class CodeExecutor:
    """代码执行器"""
    
    def __init__(self, timeout: int = 5):
        """
        初始化代码执行器
        
        Args:
            timeout: 执行超时时间（秒），默认5秒以确保系统稳定性
        """
        self.timeout = timeout
        
    def execute_python_code(self, 
                          student_code: str, 
                          test_code: str,
                          test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行Python代码并返回测试结果
        
        Args:
            student_code: 学生提交的代码
            test_code: 测试评估代码
            test_cases: 测试用例列表
            
        Returns:
            执行结果字典
        """
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # 写入学生代码
                student_file = Path(tmpdir) / "student.py"
                with open(student_file, 'w', encoding='utf-8') as f:
                    f.write(student_code)
                
                # 预处理测试用例数据
                processed_test_cases = []
                for test_case in test_cases:
                    processed_case = {
                        'input_data': test_case.get('input_data', {}) if isinstance(test_case.get('input_data'), dict) else json.loads(test_case.get('input', '{}')),
                        'expected_output': test_case.get('expected_output', {}) if isinstance(test_case.get('expected_output'), dict) else json.loads(test_case.get('expected', '{}')),
                        'is_hidden': test_case.get('is_hidden', False)
                    }
                    processed_test_cases.append(processed_case)

                # 写入测试数据
                test_data_file = Path(tmpdir) / "test_cases.json"
                with open(test_data_file, 'w', encoding='utf-8') as f:
                    json.dump(processed_test_cases, f, ensure_ascii=False, indent=2)
                
                # 创建测试运行脚本
                runner_code = f"""
import sys
import json
import traceback
from pathlib import Path

# 添加临时目录到路径
sys.path.insert(0, r'{tmpdir}')

# 读取测试用例（已经预处理过了）
with open(r'{test_data_file}', 'r', encoding='utf-8') as f:
    test_cases = json.load(f)

# 执行测试
results = []
total_score = 0
max_score = 100

# 尝试导入学生代码中的函数（根据任务类型动态导入）
student_functions = {{}}
try:
    # 尝试导入常见的函数名
    function_names = ['process_student_info', 'calculate_result', 'analyze_data', 'solve_problem']
    for func_name in function_names:
        try:
            exec(f"from student import {{func_name}}")
            student_functions[func_name] = locals()[func_name]
        except ImportError:
            continue

    if not student_functions:
        print("ERROR: 无法导入任何学生函数")
        student_loaded = False
    else:
        student_loaded = True

except Exception as e:
    print(f"ERROR: 导入学生代码时出错 - {{e}}")
    student_loaded = False

if student_loaded:

    for i, test_case in enumerate(test_cases):
        test_result = {{
            'case_id': i + 1,
            'passed': False,
            'score': 0,
            'error_message': None
        }}

        try:
            input_data = test_case.get('input_data', {{}})
            expected_output = test_case.get('expected_output', {{}})

            # 动态调用学生函数
            actual_output = None

            # 尝试调用不同的函数
            if 'process_student_info' in student_functions:
                # 变量与数据类型操作任务
                func = student_functions['process_student_info']
                # 从输入数据中提取参数
                if isinstance(input_data, dict):
                    # 假设输入数据是字典，包含函数参数
                    args = []
                    if 'name' in input_data and 'age_str' in input_data and 'score_str' in input_data and 'is_monitor_str' in input_data:
                        args = [input_data['name'], input_data['age_str'], input_data['score_str'], input_data['is_monitor_str']]
                    elif isinstance(input_data, list):
                        args = input_data
                    else:
                        args = [input_data]

                    if args:
                        actual_output = func(*args)
                else:
                    # 如果输入数据不是字典，直接传递
                    actual_output = func(input_data)

            elif 'calculate_result' in student_functions:
                func = student_functions['calculate_result']
                actual_output = func(input_data)

            elif 'analyze_data' in student_functions:
                func = student_functions['analyze_data']
                actual_output = func(input_data)

            elif 'solve_problem' in student_functions:
                func = student_functions['solve_problem']
                actual_output = func(input_data)

            else:
                # 如果没有找到合适的函数，使用第一个可用的函数
                func_name = list(student_functions.keys())[0]
                func = student_functions[func_name]
                actual_output = func(input_data)

            # 比较结果
            if actual_output == expected_output:
                test_result['passed'] = True
                test_result['score'] = 25  # 每个测试用例25分
            else:
                test_result['error_message'] = f"输出不匹配。期望: {{expected_output}}, 实际: {{actual_output}}"

        except Exception as e:
            test_result['error_message'] = f"执行错误: {{str(e)}}"
            traceback.print_exc()

        results.append(test_result)
        if test_result['passed']:
            total_score += test_result['score']

else:
    print("ERROR: 学生代码加载失败")

# 输出结果
output = {{
    'test_results': results,
    'total_score': total_score,
    'max_score': max_score,
    'status': 'pass' if total_score >= 60 else 'fail'
}}

print(json.dumps(output, ensure_ascii=False))
"""
                
                runner_file = Path(tmpdir) / "test_runner.py"
                with open(runner_file, 'w', encoding='utf-8') as f:
                    f.write(runner_code)
                
                # 执行测试
                start_time = time.time()
                process = subprocess.run(
                    [sys.executable, str(runner_file)],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    cwd=tmpdir
                )
                execution_time = (time.time() - start_time) * 1000  # 毫秒
                
                if process.returncode != 0:
                    return {
                        'status': 'error',
                        'score': 0,
                        'error_message': process.stderr or "代码执行失败",
                        'execution_time': execution_time
                    }
                
                # 解析输出
                try:
                    result = json.loads(process.stdout)
                    result['execution_time'] = execution_time
                    return result
                except json.JSONDecodeError:
                    return {
                        'status': 'error',
                        'score': 0,
                        'error_message': f"无法解析输出: {process.stdout}",
                        'execution_time': execution_time
                    }
                    
            except subprocess.TimeoutExpired:
                return {
                    'status': 'timeout',
                    'score': 0,
                    'error_message': f"代码执行超时（{self.timeout}秒）",
                    'execution_time': self.timeout * 1000
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'score': 0,
                    'error_message': f"执行异常: {str(e)}",
                    'execution_time': 0
                }

    def execute_io_based_code(self, 
                              student_code: str, 
                              test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行基于标准输入/输出的Python代码
        
        Args:
            student_code: 学生提交的代码
            test_cases: 测试用例列表
            
        Returns:
            执行结果字典
        """
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # 写入学生代码
                student_file = Path(tmpdir) / "solution.py"
                with open(student_file, 'w', encoding='utf-8') as f:
                    f.write(student_code)
                
                # 执行测试
                results = []
                total_score = 0
                max_score = 100
                score_per_test = max_score / len(test_cases) if test_cases else 0
                
                for i, test_case in enumerate(test_cases):
                    test_result = {
                        'case_id': i + 1,
                        'passed': False,
                        'score': 0,
                        'error_message': None
                    }
                    
                    try:
                        # 获取输入和期望输出
                        input_data = test_case.get('input_data', {})
                        expected_output = test_case.get('expected_output', {})
                        
                        # 将输入数据转换为JSON字符串
                        input_json = json.dumps(input_data, ensure_ascii=False)
                        
                        # 执行学生代码（在独立的子进程中运行，确保安全隔离）
                        start_time = time.time()
                        process = subprocess.run(
                            [sys.executable, str(student_file)],
                            input=input_json,
                            capture_output=True,
                            text=True,
                            timeout=self.timeout,
                            cwd=tmpdir
                        )
                        execution_time = (time.time() - start_time) * 1000  # 毫秒
                        
                        # 【步骤1和2：全面的I/O捕获 - 检查进程退出码和stderr】
                        # 添加调试日志
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.info(f"Test case {i+1} execution - returncode: {process.returncode}, stdout: {process.stdout[:100] if process.stdout else 'empty'}, stderr: {process.stderr[:100] if process.stderr else 'empty'}")
                        
                        # 检查进程退出码：非零退出码表示代码执行失败（语法错误、运行时错误等）
                        if process.returncode != 0:
                            # 提取错误信息
                            error_msg = process.stderr.strip() if process.stderr else "代码执行失败"
                            # 识别错误类型
                            if "SyntaxError" in error_msg:
                                test_result['error_message'] = f"语法错误: {error_msg.split('File')[0].strip()}"
                            elif "NameError" in error_msg:
                                test_result['error_message'] = f"名称错误: {error_msg.split('File')[0].strip()}"
                            elif "IndentationError" in error_msg:
                                test_result['error_message'] = f"缩进错误: {error_msg.split('File')[0].strip()}"
                            else:
                                test_result['error_message'] = f"执行错误: {error_msg}"
                            # 明确标记为失败
                            test_result['passed'] = False
                        # 【步骤3：检查stderr是否为空 - 即使退出码为0，stderr也可能包含警告或错误】
                        elif process.stderr and process.stderr.strip():
                            # 即使退出码为0，如果stderr有内容，说明代码执行时产生了错误或警告
                            test_result['error_message'] = f"代码执行产生错误或警告: {process.stderr.strip()}"
                            test_result['passed'] = False
                        else:
                            # 【步骤4：完善测试用例断言逻辑 - 只有代码正确执行且输出匹配时才通过】
                            # 代码执行成功（退出码为0且stderr为空），现在检查输出
                            try:
                                # 对于简单的print任务，直接比较stdout字符串
                                actual_output_raw = process.stdout.strip()
                                
                                # 如果期望输出是字符串（如"Hello, World!"），直接比较
                                if isinstance(expected_output, str):
                                    if actual_output_raw == expected_output:
                                        test_result['passed'] = True
                                        test_result['score'] = score_per_test
                                        total_score += score_per_test
                                    else:
                                        # 输出不匹配
                                        if test_case.get('is_hidden', False):
                                            test_result['error_message'] = "答案错误"
                                        else:
                                            test_result['error_message'] = f"输出不匹配。期望: {expected_output}, 实际: {actual_output_raw}"
                                        test_result['passed'] = False
                                else:
                                    # 尝试解析JSON输出（适用于需要JSON格式的任务）
                                    try:
                                        actual_output = json.loads(actual_output_raw)
                                        
                                        # 比较输出
                                        if actual_output == expected_output:
                                            test_result['passed'] = True
                                            test_result['score'] = score_per_test
                                            total_score += score_per_test
                                        else:
                                            # 添加调试信息
                                            import logging
                                            logging.info(f"输出不匹配 - 实际: {actual_output}, 期望: {expected_output}")
                                            
                                            # 提供更详细的错误信息（但对隐藏测试用例保护详情）
                                            if test_case.get('is_hidden', False):
                                                test_result['error_message'] = "答案错误"
                                            else:
                                                # 对于非隐藏测试用例，提供更多详情
                                                test_result['error_message'] = f"输出不匹配"
                                                test_result['debug_info'] = {
                                                    'expected': expected_output,
                                                    'actual': actual_output
                                                }
                                            test_result['passed'] = False
                                    except json.JSONDecodeError:
                                        # JSON解析失败，但期望输出是字典类型
                                        test_result['error_message'] = f"输出格式错误: 期望JSON格式，实际: {actual_output_raw}"
                                        test_result['passed'] = False
                                    
                            except Exception as e:
                                test_result['error_message'] = f"输出处理异常: {str(e)}"
                                test_result['passed'] = False
                                
                    except subprocess.TimeoutExpired:
                        # 【步骤3：严格超时策略 - 自动终止超时进程】
                        test_result['error_message'] = f"执行超时（超过{self.timeout}秒）。代码可能包含无限循环或死循环。"
                        test_result['passed'] = False
                    except Exception as e:
                        test_result['error_message'] = f"执行异常: {str(e)}"
                        test_result['passed'] = False
                    
                    # 隐藏测试用例的详细信息（如果标记为隐藏）
                    if test_case.get('is_hidden', False) and not test_result['passed']:
                        test_result['error_message'] = "答案错误"
                    
                    results.append(test_result)

                # 返回结果
                # 【P1-A 修复】严格通过判定：必须全部测试用例通过，不允许部分通过算 pass
                passed_count = sum(1 for r in results if r['passed'])
                is_passed = (passed_count == len(test_cases))
                return {
                    'status': 'pass' if is_passed else 'fail',
                    'score': int(total_score),
                    'max_score': max_score,
                    'test_results': results,
                    'total_tests': len(test_cases),
                    'passed_tests': passed_count,
                    'error_message': self._format_error_message(results),
                    'execution_time': 0  # 总执行时间
                }
                
            except Exception as e:
                return {
                    'status': 'error',
                    'score': 0,
                    'error_message': f"系统错误: {str(e)}",
                    'test_results': [],
                    'total_tests': len(test_cases),
                    'passed_tests': 0,
                    'execution_time': 0
                }
    
    def _format_error_message(self, results: List[Dict]) -> str:
        """格式化错误消息"""
        failed_cases = [r for r in results if not r['passed']]
        if not failed_cases:
            return ""
        
        # 构建错误消息
        messages = []
        for r in failed_cases:
            if r.get('error_message'):
                messages.append(f"Case{r['case_id']} FAIL: {r['error_message']}")
        
        return " | ".join(messages[:3])  # 最多显示3个错误

    # ============================================================
    # V2 function_call protocol (per-case subprocess isolation)
    # ============================================================

    # 单 case subprocess 超时 (秒). 秒级 function_call 足够; 再叠加总预算,
    # 避免 30 cases * self.timeout 打穿 backend 上层超时.
    FUNCTION_CALL_PER_CASE_TIMEOUT = 2
    FUNCTION_CALL_TOTAL_TIMEOUT = 30
    FUNCTION_CALL_TEACHER_MSG_LIMIT = 500

    def execute_function_call_code(self,
                                   student_code: str,
                                   test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """V2 function_call protocol: per-case subprocess isolation.

        Each test_case has:
          input_data:      {"function": "fn_name", "args": [...], "kwargs": {...}}
          expected_output: {"result": <value>} OR {"raises": "ExceptionName"}
                           (+ optional "tolerance": <float>)
          is_hidden:       bool

        Per-case isolation: each test runs in its own subprocess, fresh
        student.py import. Cross-case namespace pollution / monkey-patching
        is prevented.
        """
        if not test_cases:
            return {
                'status': 'fail',
                'score': 0,
                'max_score': 100,
                'test_results': [],
                'total_tests': 0,
                'passed_tests': 0,
                'error_message': 'function_call 协议 task_tests 为空',
                'execution_time': 0,
            }

        start_time = time.monotonic()

        with tempfile.TemporaryDirectory() as tmpdir:
            student_file = Path(tmpdir) / "student.py"
            with open(student_file, 'w', encoding='utf-8') as f:
                f.write(student_code)

            # Per-case runner: stdin = single test_case dict,
            # stdout = single result JSON. Always exit(0) so subprocess.run
            # treats non-zero exit as runner-level error (vs runner returns
            # {"ok": False} for student-level errors caught inside).
            #
            # Stage 3 升级: _serialize 递归把 set/frozenset → {"__set__": [...]},
            # tuple-key dict → {"__pairs__": [[k,v],...]}, 让 JSON 可序列化且 _values_equal
            # 能识别比较.
            runner_code = (
                'import json, sys, importlib.util, os\n'
                '\n'
                'def _emit(payload):\n'
                '    try:\n'
                '        print(json.dumps(payload, ensure_ascii=False))\n'
                '    except Exception as e:\n'
                '        fallback = {"ok": False, "error_type": "runner_emit_failed", "error": type(e).__name__ + ": " + str(e)[:200]}\n'
                '        print(json.dumps(fallback, ensure_ascii=False))\n'
                '    sys.exit(0)\n'
                '\n'
                'def _serialize(o):\n'
                '    """递归把 set/frozenset/tuple-key dict 转成 JSON 安全形式."""\n'
                '    if isinstance(o, dict):\n'
                '        if any(isinstance(k, tuple) for k in o.keys()):\n'
                '            pairs = [[list(k) if isinstance(k, tuple) else k, _serialize(v)] for k, v in o.items()]\n'
                '            pairs.sort(key=lambda p: json.dumps(p, sort_keys=True, ensure_ascii=False))\n'
                '            return {"__pairs__": pairs}\n'
                '        return {k: _serialize(v) for k, v in o.items()}\n'
                '    if isinstance(o, (set, frozenset)):\n'
                '        items = [_serialize(x) for x in o]\n'
                '        items.sort(key=lambda x: json.dumps(x, sort_keys=True, ensure_ascii=False))\n'
                '        return {"__set__": items}\n'
                '    if isinstance(o, tuple):\n'
                '        return [_serialize(x) for x in o]\n'
                '    if isinstance(o, list):\n'
                '        return [_serialize(x) for x in o]\n'
                '    try:\n'
                '        json.dumps(o, ensure_ascii=False)\n'
                '    except Exception as e:\n'
                '        raise TypeError(type(o).__name__ + " is not JSON serializable") from e\n'
                '    return o\n'
                '\n'
                'try:\n'
                '    input_obj = json.loads(sys.stdin.read())\n'
                'except Exception as e:\n'
                '    _emit({"ok": False, "error_type": "runner_input", "error": "stdin_not_json: " + str(e)})\n'
                '\n'
                'fn_name = input_obj.get("function") if isinstance(input_obj, dict) else None\n'
                'if not fn_name:\n'
                '    _emit({"ok": False, "error_type": "runner_input", "error": "input_data missing function key"})\n'
                '\n'
                'student_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student.py")\n'
                'try:\n'
                '    spec = importlib.util.spec_from_file_location("student", student_path)\n'
                '    mod = importlib.util.module_from_spec(spec)\n'
                '    spec.loader.exec_module(mod)\n'
                'except BaseException as e:\n'
                '    _emit({"ok": False, "error_type": "import_failed", "error": type(e).__name__ + ": " + str(e)[:300]})\n'
                '\n'
                'if not hasattr(mod, fn_name):\n'
                '    _emit({"ok": False, "error_type": "function_not_defined", "error": fn_name})\n'
                '\n'
                'fn = getattr(mod, fn_name)\n'
                'args = input_obj.get("args", []) or []\n'
                'kwargs = input_obj.get("kwargs", {}) or {}\n'
                'if not isinstance(args, list):\n'
                '    _emit({"ok": False, "error_type": "runner_input", "error": "args must be list"})\n'
                'if not isinstance(kwargs, dict):\n'
                '    _emit({"ok": False, "error_type": "runner_input", "error": "kwargs must be dict"})\n'
                '\n'
                'try:\n'
                '    actual = fn(*args, **kwargs)\n'
                'except BaseException as e:\n'
                '    _emit({"ok": True, "raised": type(e).__name__, "msg": str(e)[:300]})\n'
                '\n'
                'try:\n'
                '    safe_actual = _serialize(actual)\n'
                '    _emit({"ok": True, "actual": safe_actual})\n'
                'except Exception as e:\n'
                '    _emit({"ok": False, "error_type": "result_not_json_serializable", "error": str(e)[:200]})\n'
            )

            runner_file = Path(tmpdir) / "runner.py"
            with open(runner_file, 'w', encoding='utf-8') as f:
                f.write(runner_code)

            # 单 case 上限: 取 self.timeout 与 PER_CASE 较小者; 同时受 30s 总预算限制.
            per_case_timeout = min(self.timeout, self.FUNCTION_CALL_PER_CASE_TIMEOUT)

            results = []
            score_per_test = 100 / len(test_cases) if test_cases else 0
            total_score = 0.0

            for i, tc in enumerate(test_cases, start=1):
                elapsed = time.monotonic() - start_time
                remaining_budget = self.FUNCTION_CALL_TOTAL_TIMEOUT - elapsed
                if remaining_budget <= 0:
                    results.append({
                        'case_id': i,
                        'passed': False,
                        'score': 0,
                        'error_message': '执行超时',
                        'error_message_teacher': (
                            f"function_call total timeout > {self.FUNCTION_CALL_TOTAL_TIMEOUT}s "
                            f"before case {i}"
                        )[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT],
                    })
                    continue

                input_data = tc.get('input_data', {})
                expected = tc.get('expected_output', {})
                is_hidden = tc.get('is_hidden', False)

                case_result = {
                    'case_id': i,
                    'passed': False,
                    'score': 0,
                    'error_message': None,
                    'error_message_teacher': None,
                }

                # 必改 4: input_data 必须含 function 字段
                if not isinstance(input_data, dict) or 'function' not in input_data:
                    case_result['error_message'] = "测试用例配置错误"
                    case_result['error_message_teacher'] = (
                        f"input_data missing 'function' key: {input_data!r}"
                    )[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT]
                    results.append(case_result)
                    continue

                if not isinstance(expected, dict):
                    case_result['error_message'] = "测试用例配置错误"
                    case_result['error_message_teacher'] = (
                        f"expected_output must be dict, got {type(expected).__name__}: {expected!r}"
                    )[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT]
                    results.append(case_result)
                    continue

                try:
                    proc = subprocess.run(
                        [sys.executable, str(runner_file)],
                        input=json.dumps(input_data, ensure_ascii=False),
                        capture_output=True,
                        text=True,
                        timeout=min(per_case_timeout, max(0.1, remaining_budget)),
                        cwd=tmpdir,
                    )
                except subprocess.TimeoutExpired:
                    case_result['error_message'] = "执行超时"
                    case_result['error_message_teacher'] = (
                        f"subprocess timeout > {per_case_timeout}s on case {i}"
                    )[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT]
                    results.append(case_result)
                    continue
                except Exception as e:
                    case_result['error_message'] = "执行异常"
                    case_result['error_message_teacher'] = (
                        f"subprocess error: {repr(e)}"
                    )[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT]
                    results.append(case_result)
                    continue

                if proc.returncode != 0:
                    err_short = (proc.stderr or "").strip()[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT]
                    case_result['error_message'] = "答案错误" if is_hidden else "运行时错误"
                    case_result['error_message_teacher'] = (
                        f"runner returncode={proc.returncode}, stderr={err_short}"
                    )[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT]
                    results.append(case_result)
                    continue

                try:
                    actual_response = json.loads(proc.stdout)
                except json.JSONDecodeError:
                    # 学生代码 import 时可能 print 到 stdout. runner 的协议 JSON 固定在最后一行;
                    # 先做 last-line JSON 兜底, 仍失败才判 runner 输出异常.
                    json_lines = [line for line in (proc.stdout or '').splitlines() if line.strip()]
                    actual_response = None
                    for line in reversed(json_lines):
                        try:
                            candidate = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(candidate, dict) and 'ok' in candidate:
                            actual_response = candidate
                            break
                    if actual_response is None:
                        stdout_short = (proc.stdout or '')[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT]
                        stderr_short = (proc.stderr or '')[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT]
                        case_result['error_message'] = "执行异常"
                        case_result['error_message_teacher'] = (
                            f"runner output not JSON: stdout={stdout_short!r}, stderr={stderr_short!r}"
                        )[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT]
                        results.append(case_result)
                        continue

                passed, student_msg, teacher_msg = self._compare_function_call(
                    actual_response, expected, is_hidden
                )
                case_result['passed'] = passed
                case_result['error_message'] = student_msg
                case_result['error_message_teacher'] = (
                    teacher_msg[:self.FUNCTION_CALL_TEACHER_MSG_LIMIT]
                    if teacher_msg else None
                )
                if passed:
                    case_result['score'] = score_per_test
                    total_score += score_per_test

                results.append(case_result)

            passed_count = sum(1 for r in results if r['passed'])
            is_passed = (passed_count == len(test_cases) and len(test_cases) > 0)
            return {
                'status': 'pass' if is_passed else 'fail',
                'score': int(total_score),
                'max_score': 100,
                'test_results': results,
                'total_tests': len(test_cases),
                'passed_tests': passed_count,
                'error_message': self._format_error_message(results),
                'execution_time': 0,
            }

    def _compare_function_call(self, actual_response, expected, is_hidden):
        """Compare runner output {ok, actual|raised|error} vs expected
        {result|raises, tolerance?}.

        Returns (passed: bool, student_msg: str|None, teacher_msg: str|None).
        """
        if not isinstance(actual_response, dict):
            return (False,
                    "执行异常",
                    f"runner response must be dict, got {type(actual_response).__name__}: {actual_response!r}")

        if not isinstance(expected, dict):
            return (False,
                    "测试用例配置错误",
                    f"expected_output must be dict, got {type(expected).__name__}: {expected!r}")

        # runner 自身错误 (import / function 未定义 / 序列化失败 / stdin 非 JSON)
        if not actual_response.get('ok'):
            err = actual_response.get('error', 'unknown')
            err_type = actual_response.get('error_type', 'runner_error')
            if err_type == 'runner_input':
                return (False,
                        "测试用例配置错误",
                        f"runner input error: {err}")
            if err_type == 'function_not_defined':
                return (False,
                        "答案错误" if is_hidden else f"函数未定义: {err}",
                        f"function_not_defined: {err}")
            if err_type == 'import_failed':
                return (False,
                        "答案错误" if is_hidden else f"代码导入失败: {err}",
                        f"import_failed: {err}")
            if err_type == 'result_not_json_serializable':
                return (False,
                        "答案错误" if is_hidden else f"返回值不可序列化: {err}",
                        f"result_not_json_serializable: {err}")
            return (False,
                    "答案错误" if is_hidden else f"代码错误: {err}",
                    f"runner not_ok ({err_type}): {err}")

        # 期望抛异常 (必改 3: 严格类名匹配, 不做 mro 父类匹配)
        if 'raises' in expected:
            expected_exc = expected['raises']
            if 'raised' in actual_response:
                actual_exc = actual_response['raised']
                if actual_exc == expected_exc:
                    return (True, None, None)
                return (False,
                        "答案错误" if is_hidden else f"期望抛 {expected_exc}, 实际抛 {actual_exc}",
                        (f"raises mismatch: expected={expected_exc}, "
                         f"actual={actual_exc}, msg={actual_response.get('msg', '')}"))
            ret = actual_response.get('actual')
            return (False,
                    "答案错误" if is_hidden else f"期望抛 {expected_exc}, 实际返回 {ret!r}",
                    f"raises expected but returned: expected={expected_exc}, returned={ret!r}")

        # 期望返回值
        if 'result' in expected:
            exp = expected['result']
            tol = expected.get('tolerance')
            if 'raised' in actual_response:
                actual_exc = actual_response['raised']
                return (False,
                        "答案错误" if is_hidden else f"期望返回值, 实际抛 {actual_exc}",
                        f"unexpected raise: {actual_exc} ({actual_response.get('msg', '')})")
            actual = actual_response.get('actual')
            if self._values_equal(actual, exp, tol):
                return (True, None, None)
            return (False,
                    "答案错误" if is_hidden else f"输出不匹配, 期望 {exp!r}, 实际 {actual!r}",
                    f"value mismatch: expected={exp!r}, actual={actual!r}, tolerance={tol}")

        # expected_output 缺 'result' 与 'raises' (task_tests 配置 bug)
        return (False,
                "测试用例配置错误",
                f"expected_output missing 'result' or 'raises': {expected!r}")

    def _values_equal(self, actual, expected, tolerance=None):
        """递归比较, 必改 2: tolerance 单一全局浮点容差, 应用到任意叶节点 (int/float).
        嵌套 list / dict 结构所有数值用同一 tolerance.
        bool 不参与容差比较 (True/False 必须严格匹配).
        JSON 序列化把 tuple 转 list, 比较时容忍 actual=list / expected=tuple.

        Stage 3 升级:
        - set/frozenset 输出: 通过 {"__set__": [sorted_items]} marker 比较 (无序)
        - tuple-key dict 输出: 通过 {"__pairs__": [[k,v],...]} marker 比较 (无序)
        runner.py 的 _serialize 自动加 marker, expected 在 task_tests 里手动写 marker.
        """
        # bool 是 int 子类, 但评测语义必须严格同类型同值, 避免 True == 1.0 漏过.
        if isinstance(expected, bool) or isinstance(actual, bool):
            return isinstance(expected, bool) and isinstance(actual, bool) and actual == expected

        # 数值容差: 仅 int/float, 排除 bool
        if (tolerance is not None
                and isinstance(expected, (int, float)) and not isinstance(expected, bool)
                and isinstance(actual, (int, float)) and not isinstance(actual, bool)):
            return abs(actual - expected) < tolerance

        # tuple 与 list 互相容忍 (JSON 反序列化总是 list)
        if isinstance(expected, tuple):
            return isinstance(actual, (list, tuple)) and self._values_equal(list(actual), list(expected), tolerance)

        if isinstance(actual, tuple):
            return isinstance(expected, (list, tuple)) and self._values_equal(list(actual), list(expected), tolerance)

        # __set__ marker: set/frozenset 输出 (无序比较)
        if isinstance(expected, dict) and "__set__" in expected and len(expected) == 1:
            if not (isinstance(actual, dict) and "__set__" in actual and len(actual) == 1):
                return False
            exp_items = expected["__set__"]
            act_items = actual["__set__"]
            if not isinstance(exp_items, list) or not isinstance(act_items, list):
                return False
            if len(exp_items) != len(act_items):
                return False
            # 已 canonical 排序; 直接位置比较 (递归处理含 tolerance 的数值)
            return all(self._values_equal(a, e, tolerance) for a, e in zip(act_items, exp_items))

        # __pairs__ marker: tuple-key dict 输出 (键无序比较)
        if isinstance(expected, dict) and "__pairs__" in expected and len(expected) == 1:
            if not (isinstance(actual, dict) and "__pairs__" in actual and len(actual) == 1):
                return False
            exp_pairs = expected["__pairs__"]
            act_pairs = actual["__pairs__"]
            if not isinstance(exp_pairs, list) or not isinstance(act_pairs, list):
                return False
            if len(exp_pairs) != len(act_pairs):
                return False
            return all(self._values_equal(a, e, tolerance) for a, e in zip(act_pairs, exp_pairs))

        if isinstance(expected, list):
            if not isinstance(actual, (list, tuple)) or len(actual) != len(expected):
                return False
            return all(self._values_equal(a, e, tolerance) for a, e in zip(list(actual), expected))

        if isinstance(expected, dict):
            if not isinstance(actual, dict) or set(actual.keys()) != set(expected.keys()):
                return False
            return all(self._values_equal(actual[k], expected[k], tolerance) for k in expected)

        return actual == expected

    # ============================================================
    # V2 pytest_module protocol (Stage 3 综合关)
    # ============================================================

    PYTEST_MODULE_TIMEOUT = 60  # 综合关 pytest 全模块跑 60s 上限

    def execute_pytest_module(self,
                              student_code: str,
                              test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """V2 pytest_module protocol: 综合关协议.

        task_tests 第 1 行的 input_data 应含:
          {"test_module": "test_mj12.py", "student_module_name": "student_mj12"}

        Backend 内置 test 模块在 backend/app/services/pytest_modules/<test_module>.

        流程:
          1. tmpdir/<student_module_name>.py = student_code
          2. tmpdir/<test_module> = pytest_modules/<test_module> 内容
          3. python -m pytest <test_module> --tb=line --no-header -q
          4. 解析 stdout 末行 "X passed, Y failed in Zs"
          5. 计 passed/total, 转成 score
        """
        if not test_cases:
            return {
                'status': 'fail', 'score': 0, 'max_score': 100,
                'test_results': [], 'total_tests': 0, 'passed_tests': 0,
                'error_message': 'pytest_module 协议 task_tests 为空',
                'execution_time': 0,
            }

        first_case = test_cases[0]
        input_data = first_case.get('input_data', {})
        if not isinstance(input_data, dict):
            return {
                'status': 'fail', 'score': 0, 'max_score': 100,
                'test_results': [{'case_id': 1, 'passed': False, 'score': 0,
                                  'error_message': '配置错误',
                                  'error_message_teacher': f'input_data 不是 dict: {input_data!r}'}],
                'total_tests': 1, 'passed_tests': 0,
                'error_message': 'pytest_module input_data 不是 dict',
                'execution_time': 0,
            }

        test_module = input_data.get('test_module', '')
        student_module_name = input_data.get('student_module_name', 'student')
        if not test_module:
            return {
                'status': 'fail', 'score': 0, 'max_score': 100,
                'test_results': [{'case_id': 1, 'passed': False, 'score': 0,
                                  'error_message': '配置错误',
                                  'error_message_teacher': 'input_data 缺 test_module 字段'}],
                'total_tests': 1, 'passed_tests': 0,
                'error_message': 'pytest_module 缺 test_module',
                'execution_time': 0,
            }

        # 找 backend 预存的 test 文件
        modules_dir = Path(__file__).parent / 'pytest_modules'
        test_path = modules_dir / test_module
        if not test_path.exists():
            return {
                'status': 'fail', 'score': 0, 'max_score': 100,
                'test_results': [{'case_id': 1, 'passed': False, 'score': 0,
                                  'error_message': '配置错误',
                                  'error_message_teacher': f'test_module 文件不存在: {test_path}'}],
                'total_tests': 1, 'passed_tests': 0,
                'error_message': f'pytest_module 文件未找到: {test_module}',
                'execution_time': 0,
            }

        with open(test_path, 'r', encoding='utf-8') as f:
            test_content = f.read()

        with tempfile.TemporaryDirectory() as tmpdir:
            student_file = Path(tmpdir) / f"{student_module_name}.py"
            with open(student_file, 'w', encoding='utf-8') as f:
                f.write(student_code)
            test_file = Path(tmpdir) / test_module
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_content)

            try:
                proc = subprocess.run(
                    [sys.executable, '-m', 'pytest', str(test_file),
                     '--tb=line', '--no-header', '-q', f'--rootdir={tmpdir}'],
                    capture_output=True, text=True,
                    timeout=self.PYTEST_MODULE_TIMEOUT,
                    cwd=tmpdir,
                )
            except subprocess.TimeoutExpired:
                return {
                    'status': 'fail', 'score': 0, 'max_score': 100,
                    'test_results': [{'case_id': 1, 'passed': False, 'score': 0,
                                      'error_message': '执行超时',
                                      'error_message_teacher': f'pytest > {self.PYTEST_MODULE_TIMEOUT}s'}],
                    'total_tests': 1, 'passed_tests': 0,
                    'error_message': '综合测试超时',
                    'execution_time': 0,
                }
            except Exception as e:
                return {
                    'status': 'fail', 'score': 0, 'max_score': 100,
                    'test_results': [{'case_id': 1, 'passed': False, 'score': 0,
                                      'error_message': '执行异常',
                                      'error_message_teacher': f'pytest 启动失败: {e!r}'}],
                    'total_tests': 1, 'passed_tests': 0,
                    'error_message': '综合测试启动失败',
                    'execution_time': 0,
                }

            stdout = proc.stdout or ''
            stderr = proc.stderr or ''

            # 解析末行 "X passed, Y failed in Zs" 或 "X passed in Zs"
            # Codex 审计 P1 修: 只看末 5 行, 防止学生 print "9999 passed"
            # 在 stdout 早期注入伪造满分. pytest 自己的 summary 总在末行.
            import re
            passed = 0
            failed = 0
            errors = 0
            tail = '\n'.join(stdout.strip().splitlines()[-5:])
            m_passed = re.search(r'(\d+)\s+passed', tail)
            m_failed = re.search(r'(\d+)\s+failed', tail)
            m_errors = re.search(r'(\d+)\s+error', tail)
            if m_passed: passed = int(m_passed.group(1))
            if m_failed: failed = int(m_failed.group(1))
            if m_errors: errors = int(m_errors.group(1))

            total = passed + failed + errors
            if total == 0:
                # 没解析到 — 可能学生 import 失败
                return {
                    'status': 'fail', 'score': 0, 'max_score': 100,
                    'test_results': [{'case_id': 1, 'passed': False, 'score': 0,
                                      'error_message': '代码错误',
                                      'error_message_teacher': f'pytest 无 passed/failed 输出. stdout[:500]={stdout[:500]!r}, stderr[:500]={stderr[:500]!r}'}],
                    'total_tests': 1, 'passed_tests': 0,
                    'error_message': f'综合测试启动失败 (可能是 import 错): {stderr[:200]}',
                    'execution_time': 0,
                }

            score = int(passed / total * 100) if total > 0 else 0
            is_pass = (failed == 0 and errors == 0 and passed > 0)

            return {
                'status': 'pass' if is_pass else 'fail',
                'score': score,
                'max_score': 100,
                'test_results': [{
                    'case_id': 1,
                    'passed': is_pass,
                    'score': score,
                    'error_message': None if is_pass else f'综合测试 {passed}/{total} 通过',
                    'error_message_teacher': f'pytest output:\n{stdout[-1500:]}',
                }],
                'total_tests': total,
                'passed_tests': passed,
                'error_message': None if is_pass else f'综合测试 {passed}/{total} 通过',
                'execution_time': 0,
            }

    def execute_html_evaluation(self,
                                html_content: str,
                                test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行HTML评测（基于DOM检查）
        
        Args:
            html_content: 学生提交的HTML代码
            test_cases: 测试用例列表，格式:
                {
                    "check_type": "dom",  # dom, text, attribute, style
                    "selector": "#login-btn",  # CSS选择器
                    "expected": {
                        "exists": true,
                        "text_contains": "登录",
                        "attribute": {"type": "submit"},
                        "tag_name": "button"
                    }
                }
        
        Returns:
            评测结果字典
        """
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return {
                'status': 'error',
                'score': 0,
                'error_message': '系统缺少HTML解析库，请联系管理员安装beautifulsoup4',
                'test_results': [],
                'total_tests': len(test_cases),
                'passed_tests': 0,
                'execution_time': 0
            }
        
        start_time = time.time()
        results = []
        
        try:
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            if not test_cases:
                # 没有测试用例，只检查HTML是否有效
                return {
                    'status': 'pass',
                    'score': 100,
                    'error_message': '',
                    'test_results': [{'case_id': '1', 'passed': True, 'message': 'HTML解析成功'}],
                    'total_tests': 1,
                    'passed_tests': 1,
                    'execution_time': int((time.time() - start_time) * 1000)
                }
            
            total_score = 0
            score_per_test = 100 // len(test_cases)
            
            for i, test_case in enumerate(test_cases):
                case_id = test_case.get('case_id', str(i + 1))
                test_result = {
                    'case_id': case_id,
                    'passed': False,
                    'score': 0,
                    'expected_output': '',
                    'actual_output': '',
                    'error_message': ''
                }
                
                try:
                    # 获取检查配置
                    check_type = test_case.get('check_type', 'dom')
                    selector = test_case.get('selector', '')
                    
                    # 解析expected（可能是JSON字符串）
                    expected_raw = test_case.get('expected_output') or test_case.get('expected', {})
                    if isinstance(expected_raw, str):
                        try:
                            expected = json.loads(expected_raw)
                        except json.JSONDecodeError:
                            expected = {'text_contains': expected_raw}
                    else:
                        expected = expected_raw
                    
                    # 解析input_data中的选择器（兼容不同格式）
                    input_data = test_case.get('input_data', {})
                    if isinstance(input_data, str):
                        try:
                            input_data = json.loads(input_data)
                        except json.JSONDecodeError:
                            input_data = {}
                    
                    if not selector and input_data.get('selector'):
                        selector = input_data.get('selector')
                    if not selector and input_data.get('check_type'):
                        check_type = input_data.get('check_type')
                    
                    test_result['expected_output'] = str(expected)
                    
                    if not selector:
                        # 如果没有选择器，检查整个页面
                        test_result['passed'] = True
                        test_result['score'] = score_per_test
                        test_result['actual_output'] = 'HTML结构有效'
                    else:
                        # 查找元素
                        element = soup.select_one(selector)
                        
                        if element is None:
                            # 元素不存在
                            if expected.get('exists') == False:
                                test_result['passed'] = True
                                test_result['score'] = score_per_test
                                test_result['actual_output'] = f'元素 {selector} 不存在（符合预期）'
                            else:
                                test_result['error_message'] = f'未找到元素: {selector}'
                                test_result['actual_output'] = '元素不存在'
                        else:
                            # 元素存在，进行各项检查
                            passed = True
                            actual_info = []
                            
                            # 检查是否要求元素存在
                            if expected.get('exists') == True or 'exists' not in expected:
                                actual_info.append(f'元素 {selector} 存在')
                            
                            # 检查文本内容
                            if 'text_contains' in expected:
                                text_content = element.get_text(strip=True)
                                expected_text = expected['text_contains']
                                actual_info.append(f'文本内容: "{text_content}"')
                                if expected_text not in text_content:
                                    passed = False
                                    test_result['error_message'] = f'文本不匹配，期望包含"{expected_text}"，实际为"{text_content}"'
                            
                            # 检查精确文本
                            if 'text_equals' in expected:
                                text_content = element.get_text(strip=True)
                                expected_text = expected['text_equals']
                                actual_info.append(f'文本内容: "{text_content}"')
                                if text_content != expected_text:
                                    passed = False
                                    test_result['error_message'] = f'文本不匹配，期望"{expected_text}"，实际为"{text_content}"'
                            
                            # 检查标签名
                            if 'tag_name' in expected:
                                actual_tag = element.name.lower()
                                expected_tag = expected['tag_name'].lower()
                                actual_info.append(f'标签: <{actual_tag}>')
                                if actual_tag != expected_tag:
                                    passed = False
                                    test_result['error_message'] = f'标签不匹配，期望<{expected_tag}>，实际为<{actual_tag}>'
                            
                            # 检查属性
                            if 'attribute' in expected:
                                for attr_name, attr_value in expected['attribute'].items():
                                    actual_value = element.get(attr_name, '')
                                    actual_info.append(f'{attr_name}="{actual_value}"')
                                    if actual_value != attr_value:
                                        passed = False
                                        test_result['error_message'] = f'属性不匹配，{attr_name}期望"{attr_value}"，实际为"{actual_value}"'
                            
                            # 检查class
                            if 'has_class' in expected:
                                classes = element.get('class', [])
                                expected_class = expected['has_class']
                                actual_info.append(f'class="{" ".join(classes)}"')
                                if expected_class not in classes:
                                    passed = False
                                    test_result['error_message'] = f'缺少class: {expected_class}'
                            
                            # 检查子元素数量
                            if 'min_children' in expected:
                                children_count = len(element.find_all(recursive=False))
                                actual_info.append(f'子元素数量: {children_count}')
                                if children_count < expected['min_children']:
                                    passed = False
                                    test_result['error_message'] = f'子元素数量不足，期望至少{expected["min_children"]}个，实际{children_count}个'
                            
                            test_result['actual_output'] = ', '.join(actual_info)
                            test_result['passed'] = passed
                            if passed:
                                test_result['score'] = score_per_test
                    
                    if test_result['passed']:
                        total_score += test_result['score']
                        
                except Exception as e:
                    test_result['error_message'] = f'检查过程出错: {str(e)}'
                
                results.append(test_result)
            
            passed_count = sum(1 for r in results if r['passed'])
            
            return {
                'status': 'pass' if passed_count == len(test_cases) else 'fail',
                'score': int(total_score),
                'error_message': self._format_error_message(results) if passed_count < len(test_cases) else '',
                'test_results': results,
                'total_tests': len(test_cases),
                'passed_tests': passed_count,
                'execution_time': int((time.time() - start_time) * 1000)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'score': 0,
                'error_message': f'HTML解析错误: {str(e)}',
                'test_results': [],
                'total_tests': len(test_cases),
                'passed_tests': 0,
                'execution_time': int((time.time() - start_time) * 1000)
            }

# 单例实例
code_executor = CodeExecutor(timeout=30)
