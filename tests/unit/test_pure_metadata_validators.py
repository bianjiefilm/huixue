"""
Unit tests for backend/app/utils/metadata_validators.py — metadata validation pure functions.
"""
import pytest
from app.utils.metadata_validators import (
    clean_empty_values,
    migrate_legacy_format,
    validate_required_fields,
    validate_data_formats,
    validate_content_resources,
    validate_business_rules,
    suggest_fixes,
)


# ==================== clean_empty_values ====================

class TestCleanEmptyValues:

    def test_removes_none(self):
        assert clean_empty_values({"a": 1, "b": None}) == {"a": 1}

    def test_removes_empty_string(self):
        assert clean_empty_values({"a": "ok", "b": ""}) == {"a": "ok"}

    def test_keeps_zero_and_false(self):
        result = clean_empty_values({"a": 0, "b": False})
        assert result == {"a": 0, "b": False}

    def test_recursive_dict(self):
        data = {"a": {"x": 1, "y": None}, "b": "ok"}
        result = clean_empty_values(data)
        assert result == {"a": {"x": 1}, "b": "ok"}

    def test_list_removes_none_items(self):
        data = {"items": [1, None, 3]}
        result = clean_empty_values(data)
        assert result == {"items": [1, 3]}

    def test_empty_dict(self):
        assert clean_empty_values({}) == {}

    def test_all_none(self):
        assert clean_empty_values({"a": None, "b": ""}) == {}

    def test_nested_empty_dict_preserved(self):
        # An empty dict after cleaning is still a dict (not removed)
        data = {"a": {"x": None}}
        result = clean_empty_values(data)
        assert result == {"a": {}}


# ==================== migrate_legacy_format ====================

class TestMigrateLegacyFormat:

    def test_drag_drop_mapping(self):
        data = {"training_type": "DRAG_DROP"}
        result = migrate_legacy_format(data)
        assert result["training_type"] == "drag_and_drop"

    def test_coding_mapping(self):
        data = {"training_type": "CODING"}
        result = migrate_legacy_format(data)
        assert result["training_type"] == "coding"

    def test_already_new_format_untouched(self):
        data = {"training_type": "drag_and_drop"}
        result = migrate_legacy_format(data)
        assert result["training_type"] == "drag_and_drop"

    def test_difficulty_easy(self):
        data = {"difficulty": "easy"}
        result = migrate_legacy_format(data)
        assert result["difficulty"] == "beginner"

    def test_difficulty_medium(self):
        data = {"difficulty": "medium"}
        result = migrate_legacy_format(data)
        assert result["difficulty"] == "intermediate"

    def test_difficulty_hard(self):
        data = {"difficulty": "hard"}
        result = migrate_legacy_format(data)
        assert result["difficulty"] == "advanced"

    def test_difficulty_already_new(self):
        data = {"difficulty": "beginner"}
        result = migrate_legacy_format(data)
        assert result["difficulty"] == "beginner"

    def test_no_fields_to_migrate(self):
        data = {"title": "hello"}
        result = migrate_legacy_format(data)
        assert result == {"title": "hello"}

    def test_does_not_mutate_original(self):
        original = {"training_type": "CODING", "title": "x"}
        result = migrate_legacy_format(original)
        assert original["training_type"] == "CODING"  # unchanged
        assert result["training_type"] == "coding"


# ==================== validate_required_fields ====================

class TestValidateRequiredFields:

    @pytest.fixture
    def valid_base(self):
        return {
            "id": "test_01",
            "title": "测试实训",
            "intro": "简介",
            "difficulty": "beginner",
            "course_hours": 8,
            "handbook_content_path": "handbook.md",
            "environment_config": {
                "env_type": "JUPYTER",
                "docker_image_name": "jupyter:latest",
            },
        }

    def test_all_present(self, valid_base):
        errors = validate_required_fields(valid_base)
        assert errors == []

    def test_missing_id(self, valid_base):
        del valid_base["id"]
        errors = validate_required_fields(valid_base)
        assert any("id" in e for e in errors)

    def test_empty_title(self, valid_base):
        valid_base["title"] = ""
        errors = validate_required_fields(valid_base)
        assert any("title" in e for e in errors)

    def test_none_intro(self, valid_base):
        valid_base["intro"] = None
        errors = validate_required_fields(valid_base)
        assert any("intro" in e for e in errors)

    def test_missing_env_config(self, valid_base):
        del valid_base["environment_config"]
        errors = validate_required_fields(valid_base)
        assert any("environment_config" in e for e in errors)

    def test_env_config_not_dict(self, valid_base):
        valid_base["environment_config"] = "bad"
        errors = validate_required_fields(valid_base)
        assert any("必须是对象" in e for e in errors)

    def test_env_config_missing_env_type(self, valid_base):
        del valid_base["environment_config"]["env_type"]
        errors = validate_required_fields(valid_base)
        assert any("env_type" in e for e in errors)

    def test_env_config_missing_docker_image(self, valid_base):
        del valid_base["environment_config"]["docker_image_name"]
        errors = validate_required_fields(valid_base)
        assert any("docker_image_name" in e for e in errors)

    def test_training_requires_training_type(self, valid_base):
        errors = validate_required_fields(valid_base, is_training=True)
        assert any("training_type" in e for e in errors)

    def test_training_requires_industry(self, valid_base):
        valid_base["training_type"] = "coding"
        errors = validate_required_fields(valid_base, is_training=True)
        assert any("industry" in e for e in errors)

    def test_training_all_present(self, valid_base):
        valid_base["training_type"] = "coding"
        valid_base["industry"] = "金融"
        errors = validate_required_fields(valid_base, is_training=True)
        assert errors == []

    def test_practice_no_extra_required(self, valid_base):
        errors = validate_required_fields(valid_base, is_training=False)
        assert errors == []


# ==================== validate_data_formats ====================

class TestValidateDataFormats:

    def test_valid_id(self):
        errors = validate_data_formats({"id": "my_resource-01"})
        assert not any("id" in e for e in errors)

    def test_invalid_id_special_chars(self):
        errors = validate_data_formats({"id": "bad id!"})
        assert any("id" in e for e in errors)

    def test_valid_version(self):
        errors = validate_data_formats({"version": "2.1.0"})
        assert not any("version" in e for e in errors)

    def test_invalid_version(self):
        errors = validate_data_formats({"version": "v1.0"})
        assert any("version" in e for e in errors)

    def test_course_hours_valid(self):
        errors = validate_data_formats({"course_hours": 50})
        assert not any("course_hours" in e for e in errors)

    def test_course_hours_zero(self):
        errors = validate_data_formats({"course_hours": 0})
        assert any("1-100" in e for e in errors)

    def test_course_hours_101(self):
        errors = validate_data_formats({"course_hours": 101})
        assert any("1-100" in e for e in errors)

    def test_course_hours_not_number(self):
        errors = validate_data_formats({"course_hours": "abc"})
        assert any("整数" in e for e in errors)

    def test_handbook_path_md(self):
        errors = validate_data_formats({"handbook_content_path": "docs/guide.md"})
        assert not any("handbook" in e for e in errors)

    def test_handbook_path_bad_ext(self):
        errors = validate_data_formats({"handbook_content_path": "docs/guide.txt"})
        assert any("handbook" in e and "markdown" in e for e in errors)

    def test_cover_path_png(self):
        errors = validate_data_formats({"cover_url_path": "img/cover.png"})
        assert not any("cover" in e for e in errors)

    def test_cover_path_bad_ext(self):
        errors = validate_data_formats({"cover_url_path": "img/cover.bmp"})
        assert any("cover" in e and "图片" in e for e in errors)

    def test_empty_data(self):
        assert validate_data_formats({}) == []


# ==================== validate_content_resources ====================

class TestValidateContentResources:

    def test_valid_empty(self):
        cr = {"datasets": [], "sql_scripts": [], "bi_templates": [], "ai_models": []}
        assert validate_content_resources(cr) == []

    def test_not_dict(self):
        errors = validate_content_resources("bad")
        assert any("必须是对象" in e for e in errors)

    def test_missing_keys_auto_filled(self):
        # Missing keys get auto-initialized to []
        cr = {}
        errors = validate_content_resources(cr)
        assert errors == []
        assert cr["datasets"] == []

    def test_not_list(self):
        cr = {"datasets": "not_a_list", "sql_scripts": [], "bi_templates": [], "ai_models": []}
        errors = validate_content_resources(cr)
        assert any("必须是数组" in e for e in errors)

    def test_item_not_dict(self):
        cr = {"datasets": ["bad"], "sql_scripts": [], "bi_templates": [], "ai_models": []}
        errors = validate_content_resources(cr)
        assert any("必须是对象" in e for e in errors)

    def test_missing_path(self):
        cr = {"datasets": [{"name": "data"}], "sql_scripts": [], "bi_templates": [], "ai_models": []}
        errors = validate_content_resources(cr)
        assert any("缺少path" in e for e in errors)

    def test_sql_script_wrong_ext(self):
        cr = {
            "datasets": [],
            "sql_scripts": [{"path": "init.txt", "name": "init"}],
            "bi_templates": [],
            "ai_models": [],
        }
        errors = validate_content_resources(cr)
        assert any(".sql" in e for e in errors)

    def test_sql_script_correct(self):
        cr = {
            "datasets": [],
            "sql_scripts": [{"path": "init.sql", "name": "init"}],
            "bi_templates": [],
            "ai_models": [],
        }
        errors = validate_content_resources(cr)
        assert errors == []

    def test_bi_template_zip(self):
        cr = {
            "datasets": [],
            "sql_scripts": [],
            "bi_templates": [{"path": "template.zip", "name": "t"}],
            "ai_models": [],
        }
        assert validate_content_resources(cr) == []

    def test_bi_template_json(self):
        cr = {
            "datasets": [],
            "sql_scripts": [],
            "bi_templates": [{"path": "template.json", "name": "t"}],
            "ai_models": [],
        }
        assert validate_content_resources(cr) == []

    def test_bi_template_wrong_ext(self):
        cr = {
            "datasets": [],
            "sql_scripts": [],
            "bi_templates": [{"path": "template.csv", "name": "t"}],
            "ai_models": [],
        }
        errors = validate_content_resources(cr)
        assert any("bi_templates" in e for e in errors)


# ==================== validate_business_rules ====================

class TestValidateBusinessRules:

    def test_practice_no_rules(self):
        errors = validate_business_rules({"title": "x"}, is_training=False)
        assert errors == []

    def test_training_drag_drop_generic_industry(self):
        data = {"training_type": "drag_and_drop", "industry": "计算机科学"}
        errors = validate_business_rules(data, is_training=True)
        assert any("一般性行业" in e for e in errors)

    def test_training_drag_drop_empty_industry(self):
        data = {"training_type": "drag_and_drop", "industry": ""}
        errors = validate_business_rules(data, is_training=True)
        assert any("一般性行业" in e for e in errors)

    def test_training_drag_drop_specific_industry(self):
        data = {"training_type": "drag_and_drop", "industry": "金融分析"}
        errors = validate_business_rules(data, is_training=True)
        assert errors == []

    def test_training_coding_any_industry(self):
        data = {"training_type": "coding", "industry": "计算机科学"}
        errors = validate_business_rules(data, is_training=True)
        assert errors == []

    def test_assignment_nodes_valid(self):
        data = {"assignment_nodes": [{"node_name": "n1", "tool_type": "BI"}]}
        errors = validate_business_rules(data)
        assert errors == []

    def test_assignment_nodes_invalid_tool_type(self):
        data = {"assignment_nodes": [{"node_name": "n1", "tool_type": "EXCEL"}]}
        errors = validate_business_rules(data)
        assert any("tool_type" in e for e in errors)

    def test_assignment_nodes_not_list(self):
        data = {"assignment_nodes": "bad"}
        errors = validate_business_rules(data)
        assert any("必须是数组" in e for e in errors)

    def test_assignment_node_not_dict(self):
        data = {"assignment_nodes": ["bad"]}
        errors = validate_business_rules(data)
        assert any("必须是对象" in e for e in errors)

    def test_no_assignment_nodes(self):
        errors = validate_business_rules({})
        assert errors == []


# ==================== suggest_fixes ====================

class TestSuggestFixes:

    def test_missing_field_suggestion(self):
        errors = ["缺少必需字段: title"]
        result = suggest_fixes(errors)
        assert len(result["fixes"]) == 1
        assert result["fixes"][0]["field"] == "title"
        assert result["fixes"][0]["type"] == "add_required_field"

    def test_handbook_path_suggestion(self):
        errors = ["handbook_content_path必须指向markdown文件"]
        result = suggest_fixes(errors)
        assert len(result["fixes"]) == 1
        assert result["fixes"][0]["field"] == "handbook_content_path"

    def test_cover_path_suggestion(self):
        errors = ["cover_url_path必须指向图片文件"]
        result = suggest_fixes(errors)
        assert len(result["fixes"]) == 1
        assert result["fixes"][0]["field"] == "cover_url_path"

    def test_no_matching_errors(self):
        errors = ["some random error"]
        result = suggest_fixes(errors)
        assert result["fixes"] == []
        assert result["warnings"] == []

    def test_empty_errors(self):
        result = suggest_fixes([])
        assert result["fixes"] == []

    def test_multiple_errors(self):
        errors = [
            "缺少必需字段: id",
            "缺少必需字段: title",
            "handbook_content_path必须指向markdown文件",
        ]
        result = suggest_fixes(errors)
        assert len(result["fixes"]) == 3
