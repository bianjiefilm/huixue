"""
resource_scanner_helpers.py 纯函数单元测试

覆盖: 资源类型检测、数据标准化、BI关卡提取、智能提取、目录名解析
"""
import pytest
from app.utils.resource_scanner_helpers import (
    detect_resource_type,
    standardize_course_data,
    extract_bi_stages,
    item_to_stage,
    intelligent_extraction,
    parse_bi_project_data,
    parse_directory_name,
    result_key_for_type,
    DEFAULT_RESOURCE_PATTERNS,
)


# ==================== 资源类型检测 ====================

class TestDetectResourceType:

    def test_course_resource(self):
        assert detect_resource_type("/ziyuan/课程资源/python入门") == "course"

    def test_course_material(self):
        assert detect_resource_type("/ziyuan/课程资料/data") == "course"

    def test_practice_resource(self):
        assert detect_resource_type("/ziyuan/实践资源/lab1") == "practice"

    def test_micro_experiment(self):
        assert detect_resource_type("/some/微型实验/exp1") == "practice"

    def test_training_resource(self):
        assert detect_resource_type("/ziyuan/实训资源/t1") == "practice"

    def test_training_keyword(self):
        assert detect_resource_type("/ziyuan/实训/bi") == "training"

    def test_training_alt(self):
        assert detect_resource_type("/path/训练/x") == "training"

    def test_material(self):
        assert detect_resource_type("/ziyuan/教材/ch1") == "material"

    def test_teaching_material(self):
        assert detect_resource_type("/ziyuan/教学材料/unit") == "material"

    def test_question_bank(self):
        assert detect_resource_type("/ziyuan/题库/set1") == "question"

    def test_exercise(self):
        assert detect_resource_type("/ziyuan/习题/q1") == "question"

    def test_exam(self):
        assert detect_resource_type("/ziyuan/考试/final") == "question"

    def test_no_match(self):
        assert detect_resource_type("/some/random/path") is None

    def test_empty_string(self):
        assert detect_resource_type("") is None

    def test_case_insensitive_chinese(self):
        """中文无大小写，但路径中英文部分应 lower"""
        assert detect_resource_type("/ZIYUAN/课程资源/P1") == "course"

    def test_custom_patterns(self):
        custom = {"lab": ["laboratory", "实验室"]}
        assert detect_resource_type("/path/laboratory/exp", custom) == "lab"
        assert detect_resource_type("/path/实验室/e", custom) == "lab"

    def test_custom_patterns_no_match(self):
        custom = {"lab": ["laboratory"]}
        assert detect_resource_type("/path/课程资源/x", custom) is None

    def test_first_match_wins(self):
        """多个模式匹配时返回第一个"""
        result = detect_resource_type("/ziyuan/实训资源/训练")
        # 实训资源 matches "practice", 训练 matches "training"
        # dict iteration order: course → practice → training → ...
        assert result == "practice"


# ==================== 数据标准化 ====================

class TestStandardizeCourseData:

    def test_with_title(self):
        data = {"title": "Python入门", "description": "基础课程"}
        result = standardize_course_data(data)
        assert result["title"] == "Python入门"
        assert result["description"] == "基础课程"
        assert result["type"] == "course"
        assert result["difficulty"] == "beginner"

    def test_with_name_fallback(self):
        data = {"name": "数据分析"}
        result = standardize_course_data(data)
        assert result["title"] == "数据分析"

    def test_unnamed_fallback(self):
        data = {}
        result = standardize_course_data(data)
        assert result["title"] == "未命名课程"

    def test_preserves_metadata(self):
        data = {"title": "T", "extra_field": 42}
        result = standardize_course_data(data)
        assert result["metadata"]["extra_field"] == 42

    def test_all_fields(self):
        data = {
            "title": "Full",
            "description": "desc",
            "type": "practice",
            "difficulty": "advanced",
            "duration": 90,
            "topics": ["AI"],
            "stages": [{"title": "s1"}],
            "resources": [{"url": "http://x"}],
        }
        result = standardize_course_data(data)
        assert result["type"] == "practice"
        assert result["difficulty"] == "advanced"
        assert result["duration"] == 90
        assert result["topics"] == ["AI"]
        assert len(result["stages"]) == 1
        assert len(result["resources"]) == 1

    def test_title_over_name(self):
        """title 优先于 name"""
        data = {"title": "A", "name": "B"}
        assert standardize_course_data(data)["title"] == "A"

    def test_empty_title_uses_name(self):
        """title 为空字符串时 fallback 到 name"""
        data = {"title": "", "name": "B"}
        assert standardize_course_data(data)["title"] == "B"


# ==================== BI关卡提取 ====================

class TestExtractBIStages:

    def test_empty_data(self):
        assert extract_bi_stages({}) == []

    def test_data_sources_only(self):
        stages = extract_bi_stages({"dataSources": [{"name": "mysql"}]})
        assert len(stages) == 1
        assert stages[0]["title"] == "数据源配置"

    def test_datasets_only(self):
        stages = extract_bi_stages({"datasets": [{"name": "sales"}]})
        assert len(stages) == 1
        assert stages[0]["title"] == "数据集创建"

    def test_dashboards(self):
        data = {"dashboards": [{"name": "销售概览"}, {"name": "库存监控"}]}
        stages = extract_bi_stages(data)
        assert len(stages) == 2
        assert "销售概览" in stages[0]["title"]
        assert "库存监控" in stages[1]["title"]

    def test_full_project(self):
        data = {
            "dataSources": [{}],
            "datasets": [{}],
            "dashboards": [{"name": "D1"}],
        }
        stages = extract_bi_stages(data)
        assert len(stages) == 3
        assert stages[0]["title"] == "数据源配置"
        assert stages[1]["title"] == "数据集创建"
        assert "D1" in stages[2]["title"]

    def test_dashboard_without_name(self):
        stages = extract_bi_stages({"dashboards": [{}]})
        assert len(stages) == 1
        # fallback to index number
        assert "1" in stages[0]["title"]

    def test_tasks_present(self):
        stages = extract_bi_stages({"dataSources": [{}]})
        assert len(stages[0]["tasks"]) == 2


# ==================== 列表项 → 关卡 ====================

class TestItemToStage:

    def test_with_title(self):
        result = item_to_stage({"title": "关卡1", "description": "描述", "tasks": ["t1"]})
        assert result["title"] == "关卡1"
        assert result["description"] == "描述"
        assert result["tasks"] == ["t1"]

    def test_name_fallback(self):
        result = item_to_stage({"name": "N1"})
        assert result["title"] == "N1"

    def test_empty_dict(self):
        result = item_to_stage({})
        assert result["title"] == "未命名关卡"
        assert result["description"] == ""
        assert result["tasks"] == []

    def test_title_over_name(self):
        result = item_to_stage({"title": "A", "name": "B"})
        assert result["title"] == "A"

    def test_empty_title_uses_name(self):
        result = item_to_stage({"title": "", "name": "B"})
        assert result["title"] == "B"


# ==================== 智能字段提取 ====================

class TestIntelligentExtraction:

    def test_title_field(self):
        result = intelligent_extraction({"title": "X"})
        assert result["title"] == "X"

    def test_name_field(self):
        result = intelligent_extraction({"name": "Y"})
        assert result["title"] == "Y"

    def test_courseName_field(self):
        result = intelligent_extraction({"courseName": "Z"})
        assert result["title"] == "Z"

    def test_projectTitle_field(self):
        result = intelligent_extraction({"projectTitle": "P"})
        assert result["title"] == "P"

    def test_chinese_title_field(self):
        result = intelligent_extraction({"课程名称": "中文课程"})
        assert result["title"] == "中文课程"

    def test_description_field(self):
        result = intelligent_extraction({"title": "T", "description": "D"})
        assert result["description"] == "D"

    def test_desc_field(self):
        result = intelligent_extraction({"title": "T", "desc": "D2"})
        assert result["description"] == "D2"

    def test_intro_field(self):
        result = intelligent_extraction({"title": "T", "intro": "I"})
        assert result["description"] == "I"

    def test_chinese_desc_field(self):
        result = intelligent_extraction({"title": "T", "简介": "简短介绍"})
        assert result["description"] == "简短介绍"

    def test_fallback_title(self):
        result = intelligent_extraction({}, fallback_title="目录名")
        assert result["title"] == "目录名"

    def test_fallback_type(self):
        result = intelligent_extraction({}, fallback_type="practice")
        assert result["type"] == "practice"

    def test_defaults(self):
        result = intelligent_extraction({})
        assert result["difficulty"] == "beginner"
        assert result["duration"] == 60
        assert result["topics"] == []
        assert result["stages"] == []

    def test_metadata_preserved(self):
        data = {"title": "T", "custom_key": 42}
        assert intelligent_extraction(data)["metadata"]["custom_key"] == 42

    def test_priority_order(self):
        """title 优先于 name 优先于 courseName"""
        data = {"courseName": "C", "name": "N", "title": "T"}
        assert intelligent_extraction(data)["title"] == "T"


# ==================== BI项目数据标准化 ====================

class TestParseBIProjectData:

    def test_basic(self):
        data = {"projectTitle": "零售分析", "projectDescription": "分析零售数据"}
        result = parse_bi_project_data(data)
        assert result["title"] == "零售分析"
        assert result["description"] == "分析零售数据"
        assert result["type"] == "practice"
        assert "BI" in result["topics"]

    def test_fallback_to_parent_name(self):
        data = {}
        result = parse_bi_project_data(data, parent_name="my-project")
        assert result["title"] == "my-project"

    def test_numbered_directory(self):
        data = {}
        result = parse_bi_project_data(data, parent_name="01-销售分析")
        assert result["title"] == "销售分析"

    def test_title_not_overridden_by_dir(self):
        data = {"projectTitle": "官方标题"}
        result = parse_bi_project_data(data, parent_name="01-目录名")
        assert result["title"] == "官方标题"

    def test_stages_extracted(self):
        data = {"projectTitle": "T", "dataSources": [{}], "datasets": [{}]}
        result = parse_bi_project_data(data)
        assert len(result["stages"]) == 2

    def test_difficulty_intermediate(self):
        result = parse_bi_project_data({"projectTitle": "T"})
        assert result["difficulty"] == "intermediate"

    def test_duration_120(self):
        result = parse_bi_project_data({"projectTitle": "T"})
        assert result["duration"] == 120


# ==================== 目录名解析 ====================

class TestParseDirectoryName:

    def test_numbered(self):
        num, title = parse_directory_name("01-Python基础")
        assert num == "01"
        assert title == "Python基础"

    def test_plain_name(self):
        num, title = parse_directory_name("my_project")
        assert num is None
        assert title == "my_project"

    def test_multi_digit(self):
        num, title = parse_directory_name("123-高级实训")
        assert num == "123"
        assert title == "高级实训"

    def test_hyphen_in_name(self):
        num, title = parse_directory_name("01-some-thing")
        assert num == "01"
        assert title == "some-thing"

    def test_empty_string(self):
        num, title = parse_directory_name("")
        assert num is None
        assert title == ""


# ==================== 结果集路由 ====================

class TestResultKeyForType:

    def test_all_types(self):
        assert result_key_for_type("course") == "courses"
        assert result_key_for_type("practice") == "practices"
        assert result_key_for_type("training") == "trainings"
        assert result_key_for_type("material") == "materials"
        assert result_key_for_type("question") == "questions"

    def test_unknown_type(self):
        assert result_key_for_type("unknown") == "courses"

    def test_empty_type(self):
        assert result_key_for_type("") == "courses"
