"""
资源同步CLI工具的测试
测试命令行接口的功能
"""
import subprocess
import sys
import json
from pathlib import Path
import pytest
import tempfile
import shutil


class TestResourceSyncCLI:
    """测试资源同步CLI工具"""

    def test_cli_validate_command(self, temp_ziyuan_dir):
        """测试验证命令"""
        # 运行CLI验证命令
        result = self._run_cli_command(['validate'], temp_ziyuan_dir)

        assert result.returncode == 0
        output = result.stdout.decode('utf-8')

        # 检查输出包含预期内容
        assert "发现" in output
        assert "个资源" in output
        assert "有效资源" in output

    def test_cli_health_command(self, temp_ziyuan_dir):
        """测试健康检查命令"""
        result = self._run_cli_command(['health'], temp_ziyuan_dir)

        assert result.returncode == 0
        output = result.stdout.decode('utf-8')

        # 检查输出包含健康状态信息
        assert "整体健康" in output
        assert "成功率" in output

    def test_cli_sync_dry_run(self, temp_ziyuan_dir):
        """测试同步干运行"""
        result = self._run_cli_command(['sync', '--dry-run'], temp_ziyuan_dir)

        assert result.returncode == 0
        output = result.stdout.decode('utf-8')

        # 检查输出包含同步计划信息
        assert "同步计划" in output
        assert "create:" in output
        assert "干运行模式" in output

    def test_cli_sync_resource_command(self, temp_ziyuan_dir):
        """测试单个资源同步命令"""
        result = self._run_cli_command(
            ['sync-resource', '--resource-id', 'test-practice-course', '--dry-run'],
            temp_ziyuan_dir
        )

        assert result.returncode == 0
        output = result.stdout.decode('utf-8')

        # 检查输出包含资源同步信息
        assert "test-practice-course" in output

    def test_cli_invalid_resource_id(self, temp_ziyuan_dir):
        """测试无效资源ID"""
        result = self._run_cli_command(
            ['sync-resource', '--resource-id', 'non-existent-resource'],
            temp_ziyuan_dir
        )

        # 应该失败并返回非零退出码
        assert result.returncode != 0

    def test_cli_help_command(self, temp_ziyuan_dir):
        """测试帮助命令"""
        result = self._run_cli_command(['--help'], temp_ziyuan_dir)

        assert result.returncode == 0
        output = result.stdout.decode('utf-8')

        # 检查帮助信息
        assert "usage:" in output
        assert "validate" in output
        assert "sync" in output
        assert "health" in output

    def test_cli_invalid_command(self, temp_ziyuan_dir):
        """测试无效命令"""
        result = self._run_cli_command(['invalid-command'], temp_ziyuan_dir)

        # 应该失败
        assert result.returncode != 0

    def test_cli_missing_resource_id(self, temp_ziyuan_dir):
        """测试缺少资源ID参数"""
        result = self._run_cli_command(['sync-resource'], temp_ziyuan_dir)

        # 应该失败并显示错误信息
        assert result.returncode != 0
        error_output = result.stderr.decode('utf-8')
        assert "required" in error_output.lower()

    def _run_cli_command(self, args, ziyuan_path):
        """运行CLI命令"""
        cmd = [
            sys.executable, '-m', 'scripts.sync_resources'
        ] + args

        # 设置环境变量
        env = {
            **dict(os.environ),
            'PYTHONPATH': str(Path(__file__).parent.parent)
        }

        # 临时修改工作目录到backend
        original_cwd = os.getcwd()
        backend_dir = Path(__file__).parent.parent

        try:
            os.chdir(backend_dir)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=False,  # 我们稍后会解码
                env=env,
                timeout=30
            )
        finally:
            os.chdir(original_cwd)

        return result

    def test_cli_log_levels(self, temp_ziyuan_dir):
        """测试不同日志级别"""
        # 测试DEBUG级别
        result = self._run_cli_command(
            ['--log-level', 'DEBUG', 'validate'],
            temp_ziyuan_dir
        )
        assert result.returncode == 0

        # 测试INFO级别
        result = self._run_cli_command(
            ['--log-level', 'INFO', 'validate'],
            temp_ziyuan_dir
        )
        assert result.returncode == 0

    def test_cli_force_flag(self, temp_ziyuan_dir):
        """测试强制执行标志"""
        # 这个测试主要验证标志被正确解析，不会被实际执行
        result = self._run_cli_command(
            ['sync', '--dry-run', '--force'],
            temp_ziyuan_dir
        )
        assert result.returncode == 0


class TestCLIPerformance:
    """测试CLI性能"""

    def test_cli_performance_under_load(self, temp_ziyuan_dir):
        """测试CLI在负载下的性能"""
        import time

        start_time = time.time()
        result = self._run_cli_command(['validate'], temp_ziyuan_dir)
        end_time = time.time()

        assert result.returncode == 0

        duration = end_time - start_time
        # 验证应该在合理时间内完成
        assert duration < 5.0  # 5秒内完成


class TestCLIIntegration:
    """测试CLI集成"""

    def test_cli_workflow_integration(self, temp_ziyuan_dir):
        """测试完整的CLI工作流程"""
        # 1. 验证资源
        result = self._run_cli_command(['validate'], temp_ziyuan_dir)
        assert result.returncode == 0

        # 2. 检查健康状态
        result = self._run_cli_command(['health'], temp_ziyuan_dir)
        assert result.returncode == 0

        # 3. 执行干运行同步
        result = self._run_cli_command(['sync', '--dry-run'], temp_ziyuan_dir)
        assert result.returncode == 0

        # 4. 同步单个资源
        result = self._run_cli_command(
            ['sync-resource', '--resource-id', 'test-practice-course', '--dry-run'],
            temp_ziyuan_dir
        )
        assert result.returncode == 0


# 导入需要的模块
import os
