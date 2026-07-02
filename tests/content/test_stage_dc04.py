"""
DC04: Scrapy 框架基础 (Spider + Item + Pipeline)
Red phase: tests should FAIL on old content
Green phase: fix JSON until all tests pass
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
from pathlib import Path

import pytest

# Path constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def find_json(prefix):
    """Find JSON file matching prefix. Prefer 'scrapy' in name."""
    candidates = list(OUTPUT_DIR.glob(f"{prefix}*.json"))
    # Prefer files with 'scrapy' in name (for DC04)
    scrapy_files = [f for f in candidates if "scrapy" in f.name.lower()]
    if scrapy_files:
        return scrapy_files[0]
    if candidates:
        return candidates[0]
    return None


def load_json(prefix):
    p = find_json(prefix)
    if p is None:
        pytest.fail(f"No JSON found matching {prefix}*.json")
    return json.loads(p.read_text(encoding="utf-8"))


class TestDC04JSONStructure:
    """T1-T2: JSON file must exist and have correct structure."""

    def test_json_exists(self):
        p = find_json("stage_4_")
        assert p is not None, "No stage_4_*.json found in output/"

    def test_title_contains_scrapy(self):
        data = load_json("stage_4_")
        title = data.get("title", "")
        assert "Scrapy" in title, f"Title '{title}' must contain 'Scrapy'"


class TestDC04HandbookContent:
    """T3-T7: Handbook must cover Scrapy topics, not regex."""

    def _load_handbook(self):
        data = load_json("stage_4_")
        return data.get("handbook_markdown", "")

    def test_handbook_mentions_spider(self):
        h = self._load_handbook()
        assert "Spider" in h or "spider" in h.lower(), "Handbook must mention Spider"

    def test_handbook_mentions_item(self):
        h = self._load_handbook()
        assert "Item" in h or "item" in h.lower(), "Handbook must mention Item"

    def test_handbook_mentions_pipeline(self):
        h = self._load_handbook()
        assert "Pipeline" in h or "pipeline" in h.lower(), "Handbook must mention Pipeline"

    def test_handbook_min_3000_chars(self):
        h = self._load_handbook()
        assert len(h) >= 3000, f"Handbook too short: {len(h)} < 3000"

    def test_handbook_code_blocks(self):
        h = self._load_handbook()
        blocks = h.count("```")
        assert blocks >= 6, f"Need >=3 code blocks, got {blocks // 2}"


class TestDC04ContentCorrectness:
    """T8-T10: Must be about Scrapy, not old regex topic."""

    def test_scrapy_mentions_exceed_regex(self):
        data = load_json("stage_4_")
        text = json.dumps(data, ensure_ascii=False).lower()
        scrapy_n = text.count("scrapy")
        regex_n = text.count("正则")
        assert scrapy_n > 0, "Must mention Scrapy"
        assert scrapy_n > regex_n, \
            f"Scrapy mentions ({scrapy_n}) must exceed regex mentions ({regex_n})"

    def test_handbook_covers_css_or_xpath(self):
        data = load_json("stage_4_")
        h = data.get("handbook_markdown", "")
        has_css = "css" in h.lower() and ("selector" in h.lower() or "response.css" in h)
        has_xpath = "xpath" in h.lower() and ("response.xpath" in h or "XPath" in h)
        assert has_css or has_xpath, "Handbook must cover CSS selector or XPath"

    def test_handbook_covers_itemloader(self):
        data = load_json("stage_4_")
        h = data.get("handbook_markdown", "")
        assert "ItemLoader" in h or "itemloader" in h.lower(), \
            "Handbook must mention ItemLoader"


class TestDC04QuestionsAndTests:
    """T11-T13: Must have questions and test cases."""

    def test_has_question_data(self):
        data = load_json("stage_4_")
        assert "question_data" in data, "Must have question_data"

    def test_has_questions(self):
        data = load_json("stage_4_")
        qd = data.get("question_data", {})
        questions = qd.get("questions", []) if isinstance(qd, dict) else []
        assert len(questions) >= 3, f"Need >=3 questions, got {len(questions)}"

    def test_has_test_cases(self):
        data = load_json("stage_4_")
        tcs = data.get("test_cases", [])
        if not tcs:
            qd = data.get("question_data", {})
            tcs = qd.get("test_cases", []) if isinstance(qd, dict) else []
        assert len(tcs) >= 4, f"Need >=4 test cases, got {len(tcs)}"


class TestDC04BaselineCode:
    """T14: Must have baseline code."""

    def test_has_baseline_code(self):
        data = load_json("stage_4_")
        qd = data.get("question_data", {})
        baseline = ""
        if isinstance(qd, dict):
            baseline = qd.get("baseline_code", qd.get("starter_code", ""))
        assert len(baseline) >= 50, f"baseline_code too short: {len(baseline)} < 50"

    def test_baseline_has_scrapy_code(self):
        data = load_json("stage_4_")
        qd = data.get("question_data", {})
        baseline = ""
        if isinstance(qd, dict):
            baseline = qd.get("baseline_code", qd.get("starter_code", ""))
        assert "scrapy" in baseline.lower() or "Spider" in baseline, \
            "baseline_code must contain Scrapy-related code"
