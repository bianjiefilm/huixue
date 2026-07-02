"""
DC08: 定时任务调度 (APScheduler + crontab)
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
    keyword_files = [f for f in candidates if any(k in f.name.lower() for k in ["scheduler", "scheduling", "apscheduler", "cron", "定时"])]
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


class TestDC08JSONStructure:
    """T1-T2: JSON must exist and title mentions scheduling."""

    def test_json_exists(self):
        p = find_json("stage_8_")
        assert p is not None, "No stage_8_*.json found in output/"

    def test_title_contains_scheduler(self):
        data = load_json("stage_8_")
        title = data.get("title", "")
        assert any(k in title for k in ["调度", "Scheduler", "scheduler", "APScheduler"]), \
            f"Title '{title}' must mention scheduling"


class TestDC08HandbookContent:
    """T3-T7: Handbook must cover APScheduler and/or crontab."""

    def _load_handbook(self):
        data = load_json("stage_8_")
        return data.get("handbook_markdown", "")

    def test_handbook_mentions_apscheduler(self):
        h = self._load_handbook()
        assert "APScheduler" in h or "apscheduler" in h.lower(), \
            "Handbook must mention APScheduler"

    def test_handbook_mentions_cron_or_scheduling(self):
        h = self._load_handbook()
        has_cron = any(k in h.lower() for k in ["cron", "crontab", "定时", "调度"])
        assert has_cron, "Handbook must mention cron/crontab/scheduling"

    def test_handbook_min_3000_chars(self):
        h = self._load_handbook()
        assert len(h) >= 3000, f"Handbook too short: {len(h)} < 3000"

    def test_handbook_code_blocks(self):
        h = self._load_handbook()
        blocks = h.count("```")
        assert blocks >= 6, f"Need >=3 code blocks, got {blocks // 2}"

    def test_handbook_has_python_code(self):
        h = self._load_handbook()
        assert "python" in h.lower() and "import" in h, \
            "Handbook must have Python code examples"


class TestDC08ContentCorrectness:
    """T8-T9: Must be about scheduling, not anti-crawl."""

    def test_scheduler_mentions_exceed_anticrawl(self):
        data = load_json("stage_8_")
        text = json.dumps(data, ensure_ascii=False).lower()
        sched_n = text.count("调度") + text.count("scheduler") + text.count("cron") + text.count("apscheduler")
        crawl_n = text.count("反爬") + text.count("代理") + text.count("proxy") + text.count("验证码")
        assert sched_n > crawl_n, \
            f"Scheduler mentions ({sched_n}) should dominate over anti-crawl ({crawl_n})"

    def test_handbook_covers_scheduled_tasks(self):
        data = load_json("stage_8_")
        h = data.get("handbook_markdown", "")
        has_scheduled = any(k in h.lower() for k in ["定时", "调度", "scheduler", "cron", "interval", "cronjob"])
        assert has_scheduled, "Handbook must discuss scheduled tasks"


class TestDC08QuestionsAndTests:
    """T10-T12: Must have questions and test cases."""

    def test_has_question_data(self):
        data = load_json("stage_8_")
        assert "question_data" in data, "Must have question_data"

    def test_has_questions(self):
        data = load_json("stage_8_")
        qd = data.get("question_data", [])
        # question_data can be a list of questions or a dict with questions array
        if isinstance(qd, list):
            questions = qd
        elif isinstance(qd, dict):
            questions = qd.get("questions", [])
        else:
            questions = []
        assert len(questions) >= 3, f"Need >=3 questions, got {len(questions)}"

    def test_has_test_cases(self):
        data = load_json("stage_8_")
        # test_cases may be at top level, inside question_data dict, or inside individual questions
        # First check top level
        tcs = data.get("test_cases", [])
        if not tcs:
            qd = data.get("question_data", [])
            if isinstance(qd, list):
                for q in qd:
                    if isinstance(q, dict) and "test_cases" in q:
                        tcs = q["test_cases"]
                        break
            elif isinstance(qd, dict):
                tcs = qd.get("test_cases", [])
        assert len(tcs) >= 4, f"Need >=4 test cases, got {len(tcs)}"


class TestDC08BaselineCode:
    """T13: Must have baseline code."""

    def test_has_baseline_code(self):
        data = load_json("stage_8_")
        qd = data.get("question_data", [])
        # baseline_code may be in question_data dict, or embedded in questions
        baseline = ""
        if isinstance(qd, dict):
            baseline = qd.get("baseline_code", qd.get("starter_code", ""))
        elif isinstance(qd, list):
            # Check if any question has baseline_code
            for q in qd:
                if isinstance(q, dict):
                    bc = q.get("baseline_code", q.get("starter_code", ""))
                    if len(bc) > len(baseline):
                        baseline = bc
        assert len(baseline) >= 50, f"baseline_code too short: {len(baseline)} < 50"
