#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评测分层系统核心模块
基于现有数据结构实现多种评测类型
"""

import json
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import logging
from app.utils.eval_helpers import (
    match_output as _match_output,
    format_testcase as _format_testcase,
    create_unit_test_script as _create_unit_test_script,
    create_dataframe_eval_script as _create_dataframe_eval_script,
)

logger = logging.getLogger(__name__)


class PracticalSubtype(str, Enum):
    """实践子类型枚举"""
    SCRIPT_IO = "script_io"          # stdin/stdout 比对
    FUNCTION_UNIT = "function_unit"  # 单元测试
    CLI_TOOL = "cli_tool"           # 命令行工具
    WEB_STATIC = "web_static"       # DOM/截图断言
    API_SERVICE = "api_service"     # HTTP服务测试
    SQL_QUERY = "sql_query"         # SQL查询
    DATAFRAME_TASK = "dataframe_task"  # 数据分析
    DOCKERFILE_BUILD = "dockerfile_build"  # Docker构建
    SCRIPT_OPS = "script_ops"       # 系统脚本


class EnvType(str, Enum):
    """环境类型枚举"""
    PYTHON = "python"
    NODE = "node"
    JAVA = "java"
    GO = "go"
    CPP = "cpp"
    RUST = "rust"
    DOTNET = "dotnet"
    BROWSER = "browser"
    SQLITE = "sqlite"
    POSTGRES = "postgres_ephemeral"
    MULTI_SERVICE = "multi_service"
    DATASCI = "datasci"
    STATIC_ANALYSIS = "static_analysis"


class EvalMode(str, Enum):
    """评测模式枚举"""
    CLI = "cli"
    UNIT = "unit"
    HTTP = "http"
    SQL = "sql"
    SNAPSHOT = "snapshot"
    STATIC = "static"


class MatchRule(str, Enum):
    """匹配规则枚举"""
    EXACT = "exact"
    REGEX = "regex"
    JSON_EQUAL = "json_equal"
    SUBSET = "subset"
    TOLERANCE = "tolerance"


class PracticeTypeResolver:
    """实践类型解析器"""
    
    @staticmethod
    def get_practical_subtype(task) -> str:
        """从任务推断实践子类型"""
        
        # 1. 优先从 question_data 读取
        if task.question_data:
            try:
                data = json.loads(task.question_data)
                if 'practical_subtype' in data:
                    return data['practical_subtype']
            except (json.JSONDecodeError, TypeError):
                pass
        
        # 2. 基于文件和命令推断
        eval_script = task.evaluation_script_path or ""
        eval_cmd = task.evaluation_command or ""
        
        # 检查评测脚本内容
        if eval_script and os.path.exists(eval_script):
            with open(eval_script, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'unittest' in content or 'pytest' in content:
                    return PracticalSubtype.FUNCTION_UNIT
                if 'subprocess' in content and 'stdin' in content:
                    return PracticalSubtype.SCRIPT_IO
        
        # 基于其他特征判断
        if task.enable_page_preview:
            return PracticalSubtype.WEB_STATIC
        
        if 'sql' in eval_cmd.lower():
            return PracticalSubtype.SQL_QUERY
        
        if task.skills:
            skills_str = str(task.skills).lower()
            if 'pandas' in skills_str or 'numpy' in skills_str:
                return PracticalSubtype.DATAFRAME_TASK
            if 'api' in skills_str or 'fastapi' in skills_str:
                return PracticalSubtype.API_SERVICE
        
        # 默认为脚本IO类型
        return PracticalSubtype.SCRIPT_IO
    
    @staticmethod
    def get_env_type(task) -> str:
        """获取环境类型"""
        
        # 1. 从 question_data 读取
        if task.question_data:
            try:
                data = json.loads(task.question_data)
                if 'env_type' in data:
                    return data['env_type']
            except (json.JSONDecodeError, TypeError):
                pass
        
        # 2. 基于现有 env_type 映射
        env_mapping = {
            'online-code': EnvType.PYTHON,
            'html': EnvType.BROWSER,
            'cli': EnvType.PYTHON,
            'vdi': EnvType.MULTI_SERVICE
        }
        
        if task.env_type in env_mapping:
            return env_mapping[task.env_type]
        
        # 3. 基于实践类型推断
        subtype = PracticeTypeResolver.get_practical_subtype(task)
        if subtype == PracticalSubtype.WEB_STATIC:
            return EnvType.BROWSER
        elif subtype == PracticalSubtype.SQL_QUERY:
            return EnvType.SQLITE
        elif subtype == PracticalSubtype.DATAFRAME_TASK:
            return EnvType.DATASCI
        
        return EnvType.PYTHON  # 默认
    
    @staticmethod
    def get_eval_mode(task) -> str:
        """获取评测模式"""
        subtype = PracticeTypeResolver.get_practical_subtype(task)
        
        mode_mapping = {
            PracticalSubtype.SCRIPT_IO: EvalMode.CLI,
            PracticalSubtype.FUNCTION_UNIT: EvalMode.UNIT,
            PracticalSubtype.WEB_STATIC: EvalMode.SNAPSHOT,
            PracticalSubtype.API_SERVICE: EvalMode.HTTP,
            PracticalSubtype.SQL_QUERY: EvalMode.SQL,
            PracticalSubtype.DATAFRAME_TASK: EvalMode.UNIT,
        }
        
        return mode_mapping.get(subtype, EvalMode.CLI)


class TestcaseManager:
    """测试用例管理器"""
    
    @staticmethod
    def get_testcases(task) -> List[Dict[str, Any]]:
        """获取任务的测试用例"""
        
        # 1. 从 question_data 获取
        if task.question_data:
            try:
                data = json.loads(task.question_data)
                if 'testcases' in data:
                    return data['testcases']
            except (json.JSONDecodeError, TypeError):
                pass
        
        # 2. 从关联的测试数据文件获取
        test_data_files = [
            'test_data.json',
            'testcases.json',
            'tests.json'
        ]
        
        base_dir = Path(task.evaluation_script_path).parent if task.evaluation_script_path else Path('.')
        
        for filename in test_data_files:
            test_file = base_dir / filename
            if test_file.exists():
                try:
                    with open(test_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'test_cases' in data:
                            return data['test_cases']
                        elif isinstance(data, list):
                            return data
                except (json.JSONDecodeError, IOError):
                    continue
        
        # 3. 从数据库 TaskTest 表获取（如果存在）
        # 这里需要数据库会话，暂时返回空列表
        return []
    
    @staticmethod
    def format_testcase(tc: Dict[str, Any], subtype: str) -> Dict[str, Any]:
        """格式化测试用例为标准格式（委托给纯函数）"""
        return _format_testcase(tc, subtype)


class UnifiedEvaluator:
    """统一评测执行器"""
    
    def __init__(self):
        self.temp_dir = None
        
    def evaluate(self, task, submission_code: str) -> Dict[str, Any]:
        """执行评测"""
        
        # 1. 解析实践类型
        subtype = PracticeTypeResolver.get_practical_subtype(task)
        env_type = PracticeTypeResolver.get_env_type(task)
        eval_mode = PracticeTypeResolver.get_eval_mode(task)
        
        # 2. 获取测试用例
        testcases = TestcaseManager.get_testcases(task)
        
        # 3. 格式化测试用例
        formatted_testcases = [
            TestcaseManager.format_testcase(tc, subtype) 
            for tc in testcases
        ]
        
        # 4. 根据类型选择执行策略
        evaluator_map = {
            PracticalSubtype.SCRIPT_IO: self.evaluate_script_io,
            PracticalSubtype.FUNCTION_UNIT: self.evaluate_function_unit,
            PracticalSubtype.WEB_STATIC: self.evaluate_web_static,
            PracticalSubtype.API_SERVICE: self.evaluate_api_service,
            PracticalSubtype.SQL_QUERY: self.evaluate_sql_query,
            PracticalSubtype.DATAFRAME_TASK: self.evaluate_dataframe_task,
        }
        
        evaluator = evaluator_map.get(subtype, self.evaluate_script_io)
        
        try:
            # 创建临时工作目录
            self.temp_dir = tempfile.mkdtemp(prefix='eval_')
            
            # 执行评测
            results = evaluator(task, submission_code, formatted_testcases)
            
            # 计算统计信息
            total = len(results)
            passed = sum(1 for r in results if r.get('passed', False))
            
            return {
                'success': True,
                'subtype': subtype,
                'env_type': env_type,
                'eval_mode': eval_mode,
                'total_tests': total,
                'passed_tests': passed,
                'score': int(100 * passed / total) if total > 0 else 0,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"评测执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'subtype': subtype,
                'results': []
            }
        finally:
            # 清理临时目录
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
    
    def evaluate_script_io(self, task, submission_code: str, testcases: List[Dict]) -> List[Dict]:
        """Script-IO 类型评测"""
        results = []
        
        # 保存提交代码
        submission_file = os.path.join(self.temp_dir, 'submission.py')
        with open(submission_file, 'w', encoding='utf-8') as f:
            f.write(submission_code)
        
        for tc in testcases:
            try:
                # 运行程序
                process = subprocess.run(
                    ['python3', submission_file],
                    input=tc.get('input', ''),
                    capture_output=True,
                    text=True,
                    timeout=task.evaluation_timeout_seconds or 300
                )
                
                output = process.stdout.strip()
                expected = tc.get('expected', '').strip()
                
                # 匹配输出
                passed = self.match_output(output, expected, tc.get('match_rule', MatchRule.EXACT))
                
                results.append({
                    'test_id': tc.get('id', ''),
                    'passed': passed,
                    'output': output if tc.get('visible', False) else None,
                    'expected': expected if tc.get('visible', False) else None,
                    'visible': tc.get('visible', False)
                })
                
            except subprocess.TimeoutExpired:
                results.append({
                    'test_id': tc.get('id', ''),
                    'passed': False,
                    'error': 'Timeout',
                    'visible': tc.get('visible', False)
                })
            except Exception as e:
                results.append({
                    'test_id': tc.get('id', ''),
                    'passed': False,
                    'error': str(e),
                    'visible': tc.get('visible', False)
                })
        
        return results
    
    def evaluate_function_unit(self, task, submission_code: str, testcases: List[Dict]) -> List[Dict]:
        """Function-Unit 类型评测"""
        results = []
        
        # 保存提交代码
        submission_file = os.path.join(self.temp_dir, 'submission.py')
        with open(submission_file, 'w', encoding='utf-8') as f:
            f.write(submission_code)
        
        # 创建测试脚本
        test_script = self.create_unit_test_script(testcases)
        test_file = os.path.join(self.temp_dir, 'test_runner.py')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_script)
        
        try:
            # 运行测试
            process = subprocess.run(
                ['python3', test_file],
                capture_output=True,
                text=True,
                timeout=task.evaluation_timeout_seconds or 300,
                cwd=self.temp_dir
            )
            
            # 解析测试结果
            output = process.stdout
            if process.returncode == 0:
                # 所有测试通过
                for tc in testcases:
                    results.append({
                        'test_id': tc.get('id', ''),
                        'passed': True,
                        'visible': tc.get('visible', False)
                    })
            else:
                # 解析失败的测试
                # 这里需要更复杂的解析逻辑
                for tc in testcases:
                    results.append({
                        'test_id': tc.get('id', ''),
                        'passed': False,
                        'visible': tc.get('visible', False)
                    })
                    
        except Exception as e:
            logger.error(f"单元测试执行失败: {e}")
            for tc in testcases:
                results.append({
                    'test_id': tc.get('id', ''),
                    'passed': False,
                    'error': str(e),
                    'visible': tc.get('visible', False)
                })
        
        return results
    
    def evaluate_web_static(self, task, submission_code: str, testcases: List[Dict]) -> List[Dict]:
        """Web-Static 类型评测（简化版）"""
        # 这里需要集成 Playwright 或 Puppeteer
        # 暂时返回模拟结果
        return [
            {
                'test_id': tc.get('id', ''),
                'passed': True,  # 模拟通过
                'visible': tc.get('visible', False)
            }
            for tc in testcases
        ]
    
    def evaluate_api_service(self, task, submission_code: str, testcases: List[Dict]) -> List[Dict]:
        """API-Service 类型评测（简化版）"""
        # 需要启动服务并发送HTTP请求
        # 暂时返回模拟结果
        return [
            {
                'test_id': tc.get('id', ''),
                'passed': True,  # 模拟通过
                'visible': tc.get('visible', False)
            }
            for tc in testcases
        ]
    
    def evaluate_sql_query(self, task, submission_code: str, testcases: List[Dict]) -> List[Dict]:
        """SQL-Query 类型评测"""
        results = []
        
        try:
            import sqlite3
            
            # 创建临时数据库
            db_file = os.path.join(self.temp_dir, 'test.db')
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # 执行初始化SQL（如果有）
            # 这里需要从任务配置中获取
            
            # 执行学生的SQL
            cursor.execute(submission_code)
            student_result = cursor.fetchall()
            
            # 比对结果
            for tc in testcases:
                expected_rows = tc.get('expected_rows', [])
                passed = student_result == expected_rows
                
                results.append({
                    'test_id': tc.get('id', ''),
                    'passed': passed,
                    'visible': tc.get('visible', False)
                })
            
            conn.close()
            
        except Exception as e:
            logger.error(f"SQL评测失败: {e}")
            for tc in testcases:
                results.append({
                    'test_id': tc.get('id', ''),
                    'passed': False,
                    'error': str(e),
                    'visible': tc.get('visible', False)
                })
        
        return results
    
    def evaluate_dataframe_task(self, task, submission_code: str, testcases: List[Dict]) -> List[Dict]:
        """DataFrame-Task 类型评测"""
        results = []
        
        # 保存提交代码
        submission_file = os.path.join(self.temp_dir, 'submission.py')
        with open(submission_file, 'w', encoding='utf-8') as f:
            f.write(submission_code)
        
        # 创建评测脚本
        eval_script = self.create_dataframe_eval_script(testcases)
        eval_file = os.path.join(self.temp_dir, 'eval_dataframe.py')
        with open(eval_file, 'w', encoding='utf-8') as f:
            f.write(eval_script)
        
        try:
            # 运行评测
            process = subprocess.run(
                ['python3', eval_file],
                capture_output=True,
                text=True,
                timeout=task.evaluation_timeout_seconds or 300,
                cwd=self.temp_dir
            )
            
            # 解析结果
            if process.returncode == 0:
                # 解析JSON输出
                output = json.loads(process.stdout)
                results = output.get('results', [])
            else:
                for tc in testcases:
                    results.append({
                        'test_id': tc.get('id', ''),
                        'passed': False,
                        'error': process.stderr,
                        'visible': tc.get('visible', False)
                    })
                    
        except Exception as e:
            logger.error(f"DataFrame评测失败: {e}")
            for tc in testcases:
                results.append({
                    'test_id': tc.get('id', ''),
                    'passed': False,
                    'error': str(e),
                    'visible': tc.get('visible', False)
                })
        
        return results
    
    def match_output(self, output: str, expected: str, rule: str) -> bool:
        """匹配输出结果（委托给纯函数）"""
        return _match_output(output, expected, rule)
    
    def create_unit_test_script(self, testcases: List[Dict]) -> str:
        """创建单元测试脚本（委托给纯函数）"""
        return _create_unit_test_script(testcases)
    
    def create_dataframe_eval_script(self, testcases: List[Dict]) -> str:
        """创建DataFrame评测脚本（委托给纯函数）"""
        return _create_dataframe_eval_script(testcases)


# 导出主要类
__all__ = [
    'PracticalSubtype',
    'EnvType',
    'EvalMode',
    'MatchRule',
    'PracticeTypeResolver',
    'TestcaseManager',
    'UnifiedEvaluator'
]