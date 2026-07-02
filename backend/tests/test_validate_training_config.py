"""
训练资源配置验证工具的单元测试
测试validate_training_config.py的功能
"""

import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from validate_training_config import (
    TrainingConfigValidator,
    ValidationSeverity,
    validate_single_training,
    validate_all_trainings
)


class TestTrainingConfigValidator:
    """测试TrainingConfigValidator类"""

    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.training_dir = self.temp_dir / "test-training"
        self.training_dir.mkdir()

        # 创建有效的metadata.json
        self.valid_metadata = {
            "schema_version": "1.0.0",
            "id": "test-training-v1",
            "title": "测试实训项目",
            "training_type": "drag_and_drop",
            "intro": "这是一个测试实训项目",
            "industry": "金融科技",
            "difficulty": "intermediate",
            "course_hours": 40,
            "estimated_completion_time": "10周",
            "prerequisites": ["基础知识", "编程基础"],
            "learning_objectives": ["掌握数据分析", "学会可视化"],
            "tags": ["数据分析", "可视化", "金融"],
            "handbook_content_path": "handbook/README.md",
            "assignment_nodes": [
                {
                    "node_name": "数据分析任务",
                    "tool_type": "BI",
                    "description": "完成数据分析任务",
                    "estimated_time": "8小时"
                }
            ],
            "require_design_files": True,
            "require_experiment_report": True,
            "max_students": 30,
            "is_active": True
        }

    def teardown_method(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def create_test_files(self):
        """创建测试文件结构"""
        # 创建handbook目录和文件
        handbook_dir = self.training_dir / "handbook"
        handbook_dir.mkdir(exist_ok=True)

        readme_file = handbook_dir / "README.md"
        readme_file.write_text("# 测试手册\n\n这是测试内容。")

        # 创建datasets目录
        datasets_dir = self.training_dir / "datasets"
        datasets_dir.mkdir(exist_ok=True)

        data_file = datasets_dir / "test_data.sql"
        data_file.write_text("-- 测试数据文件\nSELECT * FROM test_table;")

        # 创建assets目录
        assets_dir = self.training_dir / "assets"
        assets_dir.mkdir(exist_ok=True)

        asset_file = assets_dir / "test_asset.tpo"
        asset_file.write_text("fake bi template content")

    def test_valid_config(self):
        """测试有效配置"""
        # 创建测试文件
        self.create_test_files()

        # 创建metadata.json
        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.valid_metadata, f, ensure_ascii=False, indent=2)

        # 验证配置
        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 应该没有错误
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        assert len(errors) == 0

        # 可能有警告（例如封面文件不存在）
        warnings = [r for r in results if r.severity == ValidationSeverity.WARNING]
        assert len(warnings) >= 0

    def test_missing_required_field(self):
        """测试缺少必填字段"""
        # 创建不完整的metadata
        invalid_metadata = self.valid_metadata.copy()
        del invalid_metadata["title"]  # 删除必填字段

        self.create_test_files()
        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_metadata, f, ensure_ascii=False, indent=2)

        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 应该有错误
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0

        # 检查错误消息
        error_messages = [r.message for r in errors]
        assert any("缺少必填字段: title" in msg for msg in error_messages)

    def test_invalid_enum_value(self):
        """测试无效的枚举值"""
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata["difficulty"] = "invalid_level"  # 无效的难度级别

        self.create_test_files()
        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_metadata, f, ensure_ascii=False, indent=2)

        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 应该有错误
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0

        # 检查错误消息
        error_messages = [r.message for r in errors]
        assert any("无效的difficulty" in msg for msg in error_messages)

    def test_missing_file(self):
        """测试缺少必需文件"""
        # 不创建handbook文件
        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.valid_metadata, f, ensure_ascii=False, indent=2)

        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 应该有错误
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0

        # 检查错误消息
        error_messages = [r.message for r in errors]
        assert any("handbook文件不存在" in msg for msg in error_messages)

    def test_invalid_json(self):
        """测试无效的JSON格式"""
        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            f.write("invalid json content {")

        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 应该有错误
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0

        # 检查错误消息
        error_messages = [r.message for r in errors]
        assert any("JSON格式错误" in msg for msg in error_messages)

    def test_missing_metadata_file(self):
        """测试缺少metadata.json文件"""
        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 应该有错误
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0

        # 检查错误消息
        error_messages = [r.message for r in errors]
        assert any("metadata.json文件不存在" in msg for msg in error_messages)

    def test_logic_validation(self):
        """测试逻辑验证"""
        # 测试course_hours为负数
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata["course_hours"] = -10

        self.create_test_files()
        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_metadata, f, ensure_ascii=False, indent=2)

        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 应该有错误
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0

    def test_type_validation(self):
        """测试类型验证"""
        # 测试course_hours不是整数
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata["course_hours"] = "forty"  # 字符串而不是整数

        self.create_test_files()
        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_metadata, f, ensure_ascii=False, indent=2)

        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 应该有错误
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0

        # 检查错误消息
        error_messages = [r.message for r in errors]
        assert any("course_hours应为整数" in msg for msg in error_messages)

    def test_array_validation(self):
        """测试数组验证"""
        # 测试prerequisites不是数组
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata["prerequisites"] = "not an array"

        self.create_test_files()
        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_metadata, f, ensure_ascii=False, indent=2)

        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 应该有错误
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0

    def test_uniqueness_validation(self):
        """测试唯一性验证"""
        # 测试assignment_nodes中有重复的node_name
        invalid_metadata = self.valid_metadata.copy()
        invalid_metadata["assignment_nodes"] = [
            {
                "node_name": "重复任务",
                "tool_type": "BI",
                "description": "任务1",
                "estimated_time": "4小时"
            },
            {
                "node_name": "重复任务",  # 重复的node_name
                "tool_type": "AI",
                "description": "任务2",
                "estimated_time": "6小时"
            }
        ]

        self.create_test_files()
        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_metadata, f, ensure_ascii=False, indent=2)

        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 应该有错误
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        assert len(errors) > 0

        # 检查错误消息
        error_messages = [r.message for r in errors]
        assert any("重复" in msg for msg in error_messages)


class TestValidationFunctions:
    """测试独立的验证函数"""

    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.training_dir = self.temp_dir / "test-training"
        self.training_dir.mkdir()

    def teardown_method(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def create_valid_training(self):
        """创建有效的训练配置"""
        # 创建目录结构
        handbook_dir = self.training_dir / "handbook"
        handbook_dir.mkdir(parents=True)
        readme_file = handbook_dir / "README.md"
        readme_file.write_text("# 测试手册")

        # 创建metadata.json
        valid_metadata = {
            "schema_version": "1.0.0",
            "id": "test-training-v1",
            "title": "测试实训项目",
            "training_type": "drag_and_drop",
            "intro": "这是一个测试实训项目",
            "industry": "金融科技",
            "difficulty": "intermediate",
            "course_hours": 40,
            "handbook_content_path": "handbook/README.md"
        }

        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(valid_metadata, f, ensure_ascii=False, indent=2)

    def test_validate_single_training_valid(self):
        """测试验证单个有效训练"""
        self.create_valid_training()

        # 验证应该成功
        success = validate_single_training(str(self.training_dir))
        assert success == True

    def test_validate_single_training_invalid(self):
        """测试验证单个无效训练"""
        # 创建无效的metadata.json（缺少必填字段）
        invalid_metadata = {
            "schema_version": "1.0.0",
            "id": "test-training-v1"
            # 缺少title等必填字段
        }

        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_metadata, f, ensure_ascii=False, indent=2)

        # 验证应该失败
        success = validate_single_training(str(self.training_dir))
        assert success == False

    def test_validate_single_training_missing_file(self):
        """测试验证不存在的训练目录"""
        # 验证应该失败
        success = validate_single_training(str(self.training_dir / "nonexistent"))
        assert success == False

    def test_validate_all_trainings(self):
        """测试验证所有训练"""
        # 创建ziyuan目录结构
        ziyuan_dir = self.temp_dir / "ziyuan"
        ziyuan_dir.mkdir()

        training_dir = ziyuan_dir / "实训资源" / "test-training"
        training_dir.mkdir(parents=True)

        # 保存当前目录
        old_training_dir = self.training_dir
        self.training_dir = training_dir

        try:
            # 创建有效的训练
            self.create_valid_training()

            # 创建另一个有问题的训练
            invalid_training_dir = ziyuan_dir / "实训资源" / "invalid-training"
            invalid_training_dir.mkdir()
            invalid_metadata_file = invalid_training_dir / "metadata.json"
            with open(invalid_metadata_file, 'w', encoding='utf-8') as f:
                json.dump({"id": "invalid"}, f, ensure_ascii=False, indent=2)

            # 验证所有训练
            total, valid, invalid = validate_all_trainings(str(ziyuan_dir))

            # 应该有2个训练，其中1个有效，1个无效
            assert total == 2
            assert valid == 1
            assert invalid == 1

        finally:
            self.training_dir = old_training_dir


class TestValidationOutput:
    """测试验证输出格式"""

    def setup_method(self):
        """设置测试环境"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.training_dir = self.temp_dir / "test-training"
        self.training_dir.mkdir()

    def teardown_method(self):
        """清理测试环境"""
        shutil.rmtree(self.temp_dir)

    def test_validation_result_format(self):
        """测试验证结果格式"""
        # 创建无效配置
        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({"id": "test"}, f, ensure_ascii=False, indent=2)  # 缺少必填字段

        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 检查结果格式
        for result in results:
            assert hasattr(result, 'severity')
            assert hasattr(result, 'message')
            assert hasattr(result, 'field')
            assert isinstance(result.severity, ValidationSeverity)

    def test_has_errors_warnings(self):
        """测试错误和警告检测"""
        # 创建有警告的配置（缺少可选文件）
        self.create_minimal_valid_config()

        validator = TrainingConfigValidator(self.training_dir)
        results = validator.validate()

        # 检查方法存在
        assert hasattr(validator, 'has_errors')
        assert hasattr(validator, 'has_warnings')

        # 检查结果
        has_errors = validator.has_errors()
        has_warnings = validator.has_warnings()

        assert isinstance(has_errors, bool)
        assert isinstance(has_warnings, bool)

    def create_minimal_valid_config(self):
        """创建最小有效配置"""
        # 创建handbook文件
        handbook_dir = self.training_dir / "handbook"
        handbook_dir.mkdir(exist_ok=True)
        readme_file = handbook_dir / "README.md"
        readme_file.write_text("# 测试")

        # 创建metadata.json
        metadata = {
            "schema_version": "1.0.0",
            "id": "test-training-v1",
            "title": "测试实训",
            "training_type": "drag_and_drop",
            "intro": "测试简介",
            "industry": "测试行业",
            "difficulty": "intermediate",
            "course_hours": 20,
            "handbook_content_path": "handbook/README.md"
        }

        metadata_file = self.training_dir / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
