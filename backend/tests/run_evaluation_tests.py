"""
测试运行脚本
支持分类运行和报告生成
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(test_type: str, verbose: bool = False, coverage: bool = False):
    """运行指定类型的测试"""
    
    base_dir = Path(__file__).parent
    test_patterns = {
        "unit": "test_task_evaluation_unit.py",
        "api": "test_task_evaluation_api.py",
        "integration": "test_task_evaluation_integration.py",
        "performance": "test_task_evaluation_performance.py",
        "security": "test_task_evaluation_security.py",
        "boundary": "test_task_evaluation_boundary.py",
        "all": "test_task_evaluation*.py"
    }
    
    if test_type not in test_patterns:
        print(f"未知的测试类型: {test_type}")
        print(f"支持的测试类型: {', '.join(test_patterns.keys())}")
        return False
    
    pattern = test_patterns[test_type]
    test_file = base_dir / pattern
    
    cmd = ["python3", "-m", "pytest"]
    
    if test_type == "all":
        cmd.append(str(base_dir / pattern))
    else:
        cmd.append(str(test_file))
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=html", "--cov-report=term"])
    
    cmd.extend(["--tb=short", "-x"])  # 遇到失败立即停止
    
    print(f"运行测试: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=base_dir.parent.parent)
    
    return result.returncode == 0


def generate_report(test_type: str):
    """生成测试报告"""
    base_dir = Path(__file__).parent
    
    cmd = [
        "python3", "-m", "pytest",
        str(base_dir / f"test_task_evaluation_{test_type}.py"),
        "--html=test_report.html",
        "--self-contained-html",
        "-v"
    ]
    
    print(f"生成测试报告: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=base_dir.parent.parent)
    
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="运行任务评测测试")
    parser.add_argument(
        "test_type",
        choices=["unit", "api", "integration", "performance", "security", "boundary", "all"],
        help="测试类型"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--coverage", action="store_true", help="生成覆盖率报告")
    parser.add_argument("--report", action="store_true", help="生成HTML报告")
    
    args = parser.parse_args()
    
    success = run_tests(args.test_type, args.verbose, args.coverage)
    
    if args.report:
        generate_report(args.test_type)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()


