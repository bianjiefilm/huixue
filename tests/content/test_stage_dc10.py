"""
DC10: 数据质量检查 (去重/补缺/校验)
硬约束规则2: 测试文件
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def find_json(prefix):
    candidates = list(OUTPUT_DIR.glob(f"{prefix}*.json"))
    keyword_files = [f for f in candidates if any(k in f.name.lower() for k in ["quality", "data", "去重", "校验", "clean"])]
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


class TestDC10JSONStructure:
    def test_json_exists(self):
        p = find_json("stage_10_")
        assert p is not None, "No stage_10_*.json found in output/"

    def test_title_contains_quality(self):
        data = load_json("stage_10_")
        title = data.get("title", "")
        assert any(k in title for k in ["质量", "Quality", "quality", "检查", "校验"]), \
            f"Title '{title}' must mention data quality"


class TestDC10HandbookContent:
    def _load_handbook(self):
        data = load_json("stage_10_")
        return data.get("handbook_markdown", "")

    def test_handbook_mentions_deduplication(self):
        h = self._load_handbook()
        assert any(k in h.lower() for k in ["去重", "dedup", "duplicate", "重复"]), \
            "Handbook must mention deduplication"

    def test_handbook_mentions_missing_values(self):
        h = self._load_handbook()
        assert any(k in h.lower() for k in ["缺失", "missing", "nan", "none", "null"]), \
            "Handbook must cover missing value handling"

    def test_handbook_mentions_validation(self):
        h = self._load_handbook()
        assert any(k in h.lower() for k in ["校验", "validate", "validation", "格式"]), \
            "Handbook must cover data validation"

    def test_handbook_min_3000_chars(self):
        h = self._load_handbook()
        assert len(h) >= 3000, f"Handbook too short: {len(h)} < 3000"

    def test_handbook_code_blocks(self):
        h = self._load_handbook()
        blocks = h.count("```")
        assert blocks >= 6, f"Need >=3 code blocks, got {blocks // 2}"


class TestDC10ContentCorrectness:
    def test_quality_mentions_exceed_async(self):
        data = load_json("stage_10_")
        text = json.dumps(data, ensure_ascii=False).lower()
        qual_n = text.count("质量") + text.count("去重") + text.count("校验") + text.count("missing") + text.count("duplicate") + text.count("validation")
        async_n = text.count("异步") + text.count("async") + text.count("httpx") + text.count("爬虫")
        assert qual_n > async_n, \
            f"Quality mentions ({qual_n}) should dominate over async ({async_n})"


class TestDC10QuestionsAndTests:
    def test_has_question_data(self):
        data = load_json("stage_10_")
        assert "question_data" in data, "Must have question_data"

    def test_has_questions(self):
        data = load_json("stage_10_")
        qd = data.get("question_data", [])
        if isinstance(qd, dict):
            questions = qd.get("multiple_choice", []) + qd.get("programming", [])
        elif isinstance(qd, list):
            questions = qd
        else:
            questions = []
        assert len(questions) >= 3, f"Need >=3 questions, got {len(questions)}"

    def test_has_test_cases(self):
        data = load_json("stage_10_")
        tcs = data.get("test_cases", [])
        if not tcs:
            qd = data.get("question_data", {})
            if isinstance(qd, dict):
                for q in qd.get("programming", []):
                    if isinstance(q, dict) and "test_cases" in q:
                        tcs = q["test_cases"]
                        break
            elif isinstance(qd, list):
                for q in qd:
                    if isinstance(q, dict) and "test_cases" in q:
                        tcs = q["test_cases"]
                        break
        assert len(tcs) >= 4, f"Need >=4 test cases, got {len(tcs)}"


class TestDC10BaselineCode:
    def test_has_baseline_code(self):
        data = load_json("stage_10_")
        qd = data.get("question_data", [])
        baseline = ""
        if isinstance(qd, dict):
            for q in qd.get("programming", []):
                if isinstance(q, dict):
                    bc = q.get("baseline_code", q.get("starter_code", ""))
                    if len(bc) > len(baseline):
                        baseline = bc
        elif isinstance(qd, list):
            for q in qd:
                if isinstance(q, dict):
                    bc = q.get("baseline_code", q.get("starter_code", ""))
                    if len(bc) > len(baseline):
                        baseline = bc
        assert len(baseline) >= 50, f"baseline_code too short: {len(baseline)} < 50"
