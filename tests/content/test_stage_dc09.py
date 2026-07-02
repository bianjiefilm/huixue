"""
DC09: 日志格式解析与采集
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
    keyword_files = [f for f in candidates if any(k in f.name.lower() for k in ["log", "nginx", "日志"])]
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


class TestDC09JSONStructure:
    def test_json_exists(self):
        p = find_json("stage_9_")
        assert p is not None, "No stage_9_*.json found in output/"

    def test_title_contains_log(self):
        data = load_json("stage_9_")
        title = data.get("title", "")
        assert any(k in title for k in ["日志", "Log", "log", "Nginx", "nginx"]), \
            f"Title '{title}' must mention log-related content"


class TestDC09HandbookContent:
    def _load_handbook(self):
        data = load_json("stage_9_")
        return data.get("handbook_markdown", "")

    def test_handbook_mentions_nginx(self):
        h = self._load_handbook()
        assert "nginx" in h.lower() or "Nginx" in h, \
            "Handbook must mention Nginx log format"

    def test_handbook_mentions_log_parsing(self):
        h = self._load_handbook()
        has_parsing = any(k in h.lower() for k in ["解析", "parse", "regex", "re模块", "split"])
        assert has_parsing, "Handbook must cover log parsing"

    def test_handbook_min_3000_chars(self):
        h = self._load_handbook()
        assert len(h) >= 3000, f"Handbook too short: {len(h)} < 3000"

    def test_handbook_code_blocks(self):
        h = self._load_handbook()
        blocks = h.count("```")
        assert blocks >= 6, f"Need >=3 code blocks, got {blocks // 2}"

    def test_handbook_mentions_json_log(self):
        h = self._load_handbook()
        text = h.lower()
        # Should mention structured/json log format
        has_structured = any(k in text for k in ["结构化", "json log", "json.log", "json日志"])
        assert has_structured, "Handbook must cover structured/JSON log format"


class TestDC09ContentCorrectness:
    def test_log_parsing_exceeds_async(self):
        data = load_json("stage_9_")
        text = json.dumps(data, ensure_ascii=False).lower()
        log_n = text.count("日志") + text.count("nginx") + text.count("log")
        async_n = text.count("异步") + text.count("async") + text.count("httpx")
        assert log_n > async_n, \
            f"Log mentions ({log_n}) should dominate over async ({async_n})"


class TestDC09QuestionsAndTests:
    def test_has_question_data(self):
        data = load_json("stage_9_")
        assert "question_data" in data, "Must have question_data"

    def test_has_questions(self):
        data = load_json("stage_9_")
        qd = data.get("question_data", [])
        if isinstance(qd, dict):
            # May have multiple_choice and/or programming arrays
            questions = qd.get("multiple_choice", []) + qd.get("programming", [])
        elif isinstance(qd, list):
            questions = qd
        else:
            questions = []
        assert len(questions) >= 3, f"Need >=3 questions, got {len(questions)}"

    def test_has_test_cases(self):
        data = load_json("stage_9_")
        tcs = data.get("test_cases", [])
        if not tcs:
            qd = data.get("question_data", {})
            if isinstance(qd, dict):
                # Check programming questions for embedded test_cases
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


class TestDC09BaselineCode:
    def test_has_baseline_code(self):
        data = load_json("stage_9_")
        qd = data.get("question_data", [])
        baseline = ""
        if isinstance(qd, dict):
            # Check programming questions for baseline_code
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
