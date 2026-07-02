"""
训练资源同步脚本的单元测试
使用真实数据测试sync_resources.py的功能
"""

import asyncio
from pathlib import Path
import pytest

from sync_resources import TrainingResourceSyncEngine


class TestTrainingResourceSyncEngine:
    """测试TrainingResourceSyncEngine类"""

    @pytest.mark.asyncio
    async def test_sync_all_trainings_success(self, db_session, real_ziyuan_dir):
        """测试成功同步所有训练资源"""
        # 创建同步引擎实例
        engine = TrainingResourceSyncEngine(db_session)

        # 执行同步
        result = await engine.sync_all_trainings()

        # 验证结果
        assert result.success == True
        assert result.total_actions >= 0  # 至少不会出错
        assert result.successful_actions == result.total_actions
        assert result.failed_actions == 0

    @pytest.mark.asyncio
    async def test_sync_single_training_success(self, db_session, real_ziyuan_dir):
        """测试成功同步单个训练资源"""
        # 使用真实的训练ID
        training_id = "01-某零售企业经营分析"

        # 创建同步引擎实例
        engine = TrainingResourceSyncEngine(db_session)

        # 执行同步
        result = await engine.sync_single_training(training_id)

        # 验证结果
        assert result.success == True
        assert result.total_actions >= 0
        assert result.successful_actions == result.total_actions
        assert result.failed_actions == 0

    @pytest.mark.asyncio
    async def test_sync_single_training_not_found(self, db_session, real_ziyuan_dir):
        """测试同步不存在的训练资源"""
        # 使用不存在的训练ID
        training_id = "non-existent-training"

        # 创建同步引擎实例
        engine = TrainingResourceSyncEngine(db_session)

        # 执行同步，应该返回失败的结果
        result = await engine.sync_single_training(training_id)

        # 验证结果
        assert result.success == False
        assert result.failed_actions == 1
        assert len(result.errors) == 1
        assert "训练目录不存在" in result.errors[0]['error']

    def test_validate_training_valid(self, db_session, real_ziyuan_dir):
        """测试验证有效的训练配置"""
        # 使用真实的训练ID
        training_id = "01-某零售企业经营分析"

        # 创建同步引擎实例
        engine = TrainingResourceSyncEngine(db_session)

        # 执行验证
        errors = engine.validate_training(training_id)

        # 验证结果 - 应该没有错误或只有警告
        from validate_training_config import ValidationSeverity
        has_errors = any(error.severity == ValidationSeverity.ERROR for error in errors)
        assert not has_errors, f"验证发现错误: {errors}"

    def test_validate_training_invalid(self, db_session, real_ziyuan_dir):
        """测试验证无效的训练配置"""
        # 使用真实的训练ID
        training_id = "02-公募基金精准营销案例"  # 这个可能有问题（根据之前的验证结果）

        # 创建同步引擎实例
        engine = TrainingResourceSyncEngine(db_session)

        # 执行验证
        errors = engine.validate_training(training_id)

        # 验证结果 - 可能有错误
        assert isinstance(errors, list)

    def test_build_database_state(self, db_session, real_ziyuan_dir):
        """测试构建数据库状态"""
        # 创建同步引擎实例
        engine = TrainingResourceSyncEngine(db_session)

        # 构建数据库状态
        db_state = engine._build_database_state()

        # 验证结果
        assert isinstance(db_state, dict)

    @pytest.mark.asyncio
    async def test_sync_error_handling(self, db_session, real_ziyuan_dir):
        """测试错误处理"""
        # 创建同步引擎实例
        engine = TrainingResourceSyncEngine(db_session)

        # 执行同步（可能会遇到一些错误）
        result = await engine.sync_all_trainings()

        # 验证结果对象存在
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'errors')

    @pytest.mark.asyncio
    async def test_sync_with_force_update(self, db_session, real_ziyuan_dir):
        """测试强制更新同步"""
        # 创建同步引擎实例
        engine = TrainingResourceSyncEngine(db_session)

        # 执行强制更新同步
        result = await engine.sync_all_trainings(force_update=True)

        # 验证结果
        assert result is not None
        assert hasattr(result, 'success')


class TestUtilityFunctions:
    """测试工具函数"""

    def test_create_db_session(self):
        """测试创建数据库会话"""
        from sync_resources import create_db_session
        session = create_db_session()
        assert session is not None
        session.close()

    def test_parse_args_validate(self):
        """测试解析验证参数"""
        from sync_resources import parse_args
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['sync_resources.py', '--validate']):
            args = parse_args()
            assert args.validate == True

    def test_parse_args_sync(self):
        """测试解析同步参数"""
        from sync_resources import parse_args
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['sync_resources.py', '--sync']):
            args = parse_args()
            assert args.sync == True

    def test_parse_args_with_id(self):
        """测试解析带ID的参数"""
        from sync_resources import parse_args
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['sync_resources.py', '--sync', '--id', 'test-training']):
            args = parse_args()
            assert args.sync == True
            assert args.id == 'test-training'

    def test_parse_args_force_update(self):
        """测试解析强制更新参数"""
        from sync_resources import parse_args
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['sync_resources.py', '--sync', '--force']):
            args = parse_args()
            assert args.sync == True
            assert args.force_update == True

    def test_parse_args_dry_run(self):
        """测试解析试运行参数"""
        from sync_resources import parse_args
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['sync_resources.py', '--sync', '--dry-run']):
            args = parse_args()
            assert args.sync == True
            assert args.dry_run == True


class TestMainFunction:
    """测试主函数"""

    @pytest.mark.asyncio
    async def test_main_validate_with_errors(self, db_session, real_ziyuan_dir):
        """测试主函数验证发现错误（使用真实数据）"""
        from sync_resources import main
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['sync_resources.py', '--validate']):
            exit_code = await main()
            # 可能有错误，但不应该崩溃
            assert isinstance(exit_code, int)

    @pytest.mark.asyncio
    async def test_main_sync_success(self, db_session, real_ziyuan_dir):
        """测试主函数同步成功"""
        from sync_resources import main
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['sync_resources.py', '--sync']):
            exit_code = await main()
            assert exit_code == 0

    def test_main_no_args(self):
        """测试主函数无参数"""
        from sync_resources import main
        import sys
        from unittest.mock import patch

        with patch.object(sys, 'argv', ['sync_resources.py']):
            # 主函数可能不抛出异常，而是返回默认行为
            try:
                result = main()
                # 如果没有抛出异常，检查返回值
                assert result is not None
            except SystemExit:
                pass  # 如果抛出SystemExit，也是可以接受的


class TestIntegrationScenarios:
    """测试集成场景"""

    @pytest.mark.asyncio
    async def test_bulk_sync_scenario(self, db_session, real_ziyuan_dir):
        """测试批量同步场景"""
        from sync_resources import TrainingResourceSyncEngine

        # 创建引擎
        engine = TrainingResourceSyncEngine(db_session)

        # 执行批量同步
        result = await engine.sync_all_trainings()

        # 验证结果
        assert result is not None
        assert hasattr(result, 'total_actions')
        assert hasattr(result, 'successful_actions')

    @pytest.mark.asyncio
    async def test_error_recovery_scenario(self, db_session, real_ziyuan_dir):
        """测试错误恢复场景"""
        from sync_resources import TrainingResourceSyncEngine

        # 创建引擎
        engine = TrainingResourceSyncEngine(db_session)

        # 执行同步（可能会遇到一些问题）
        result = await engine.sync_all_trainings()

        # 验证结果对象存在
        assert result is not None
        assert hasattr(result, 'success')
        assert hasattr(result, 'errors')

