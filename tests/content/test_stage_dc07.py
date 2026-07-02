"""
DC07: JSON/XML 数据解析 (深度嵌套结构)
硬约束规则2: 测试文件
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def find_json(prefix):
    """Find JSON file matching prefix. Prefer 'json' or 'xml' in name."""
    candidates = list(OUTPUT_DIR.glob(f"{prefix}*.json"))
    keyword_files = [f for f in candidates if "json" in f.name.lower() or "xml" in f.name.lower()]
    if keyword_files:
        return keyword_files[0]
    if candidates:
        return candidates[0]
    return None


def load_json(prefix):
    p = find_json(prefix)
    if p is None:
        pytest.fail(f"No JSON found matching {prefix}*.json")
    return json.loads(p.read_text(encoding="utf-8"))


class TestDC07JSONStructure:
    """T1-T2: JSON file must exist and have correct title."""

    def test_json_exists(self):
        p = find_json("stage_7_")
        assert p is not None, "No stage_7_*.json found in output/"

    def test_title_contains_json(self):
        data = load_json("stage_7_")
        title = data.get("title", "")
        assert "JSON" in title or "json" in title.lower(), \
            f"Title '{title}' must mention JSON or json"


class TestDC07HandbookContent:
    """T3-T7: Handbook must cover JSON/XML parsing topics."""

    def _load_handbook(self):
        data = load_json("stage_7_")
        return data.get("handbook_markdown", "")

    def test_handbook_mentions_json_module(self):
        h = self._load_handbook()
        has_json = ("json" in h.lower() and ("json.loads" in h or "json.load" in h or "json.dumps" in h))
        assert has_json, "Handbook must cover Python json module (loads/dumps)"

    def test_handbook_mentions_xml_parsing(self):
        h = self._load_handbook()
        has_xml = ("xml" in h.lower() or "ElementTree" in h or "etree" in h.lower())
        assert has_xml, "Handbook must mention XML parsing (xml.etree or ElementTree)"

    def test_handbook_min_3000_chars(self):
        h = self._load_handbook()
        assert len(h) >= 3000, f"Handbook too short: {len(h)} < 3000"

    def test_handbook_code_blocks(self):
        h = self._load_handbook()
        blocks = h.count("```")
        assert blocks >= 6, f"Need >=3 code blocks, got {blocks // 2}"

    def test_handbook_mentions_nested_structures(self):
        h = self._load_handbook()
        text = h.lower()
        # Should mention nested/深度/recursive or similar
        mentions_nested = any(k in text for k in ["嵌套", "nested", "recursive", "递归"])
        assert mentions_nested, "Handbook must discuss nested/recursive data structures"


class TestDC07ContentCorrectness:
    """T8-T9: Must be about JSON/XML parsing, not storage/cleaning."""

    def test_json_xml_mentions_exceed_storage(self):
        data = load_json("stage_7_")
        text = json.dumps(data, ensure_ascii=False).lower()
        json_n = text.count("json")
        xml_n = text.count("xml")
        # Should NOT be about data storage (CSV/pandas/SQLite)
        storage_n = text.count("csv") + text.count("pandas") + text.count("sqlite")
        assert (json_n + xml_n) > storage_n, \
            f"JSON/XML mentions ({json_n}+{xml_n}) should dominate over storage mentions ({storage_n})"

    def test_handbook_covers_json_normalization(self):
        data = load_json("stage_7_")
        h = data.get("handbook_markdown", "")
        # Should discuss extracting from nested JSON
        has_nested_extract = any(k in h.lower() for k in ["嵌套", "nested", "多层", "递归"])
        assert has_nested_extract, "Handbook must cover nested JSON extraction"


class TestDC07QuestionsAndTests:
    """T10-T12: Must have questions and test cases."""

    def test_has_question_data(self):
        data = load_json("stage_7_")
        assert "question_data" in data, "Must have question_data"

    def test_has_questions(self):
        data = load_json("stage_7_")
        qd = data.get("question_data", {})
        questions = qd.get("questions", []) if isinstance(qd, dict) else []
        assert len(questions) >= 3, f"Need >=3 questions, got {len(questions)}"

    def test_has_test_cases(self):
        data = load_json("stage_7_")
        qd = data.get("question_data", {})
        tcs = qd.get("test_cases", [])
        if not tcs:
            tcs = data.get("test_cases", [])
        assert len(tcs) >= 4, f"Need >=4 test cases, got {len(tcs)}"


class TestDC07BaselineCode:
    """T13: Must have baseline code."""

    def test_has_baseline_code(self):
        data = load_json("stage_7_")
        qd = data.get("question_data", {})
        baseline = ""
        if isinstance(qd, dict):
            baseline = qd.get("baseline_code", qd.get("starter_code", ""))
        assert len(baseline) >= 50, f"baseline_code too short: {len(baseline)} < 50"
