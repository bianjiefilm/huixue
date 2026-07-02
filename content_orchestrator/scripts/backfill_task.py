"""
反向生成脚本: 从 DB Task 提取 stage YAML 配置。

用法:
    python scripts/backfill_task.py --task-id 100
    python scripts/backfill_task.py --task-id 100 --course python

原理:
    从 tasks 表 + practices 表 + task_tests 表反向推断 stage_N.yaml 的字段值。
    只写能从 DB 直接读取的字段；无法推断的字段留空待人工填写。

字段分类:
    DB 可推断 (自动): course, course_db_id, stage_id, stage_name, difficulty,
                      knowledge_points, expected_handbook_min_chars,
                      expected_questions, expected_question_types,
                      expected_question_difficulties,
                      expected_test_cases_visible, expected_test_cases_hidden,
                      total_score, baseline_code_template
    需人工填写  (留空): style_reference, prerequisites, topics_to_avoid,
                       codex_review_required
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml

# 确保可以导入上一级包的 schema
sys.path.insert(0, str(Path(__file__).parent.parent))
from schemas.stage_config import StageConfig


# ------------------------------------------------------------------
# 数据库路径
# ------------------------------------------------------------------

def _db_path() -> Path:
    """优先从环境变量读取 DB 路径，fallback 到 backend/huixue_local.db"""
    import os
    from dotenv import load_dotenv

    backend_env = Path(__file__).parent.parent / "backend" / ".env"
    if backend_env.exists():
        load_dotenv(backend_env)

    db_url = os.environ.get("DATABASE_URL", "")
    if db_url.startswith("sqlite:///"):
        # sqlite:///./huixue_local.db  → 相对路径
        rel = db_url.replace("sqlite:///", "").lstrip("/")
        return Path(rel) if rel else Path("backend") / "huixue_local.db"
    return Path("backend") / "huixue_local.db"


# ------------------------------------------------------------------
# Markdown 解析: 从 handbook 提取知识要点
# ------------------------------------------------------------------

def _extract_knowledge_points(handbook_md: str | None) -> list[str]:
    """
    从 handbook_markdown 提取 ## 和 ### 级别的章节标题作为知识要点。

    过滤规则:
    - 跳过"学习目标"、"学习资源"、"任务描述"、"实践目标"等非知识点章节
    - 跳过包含"mp4"、"pdf"、"docx"的行（资源链接，不是知识点）
    - 跳过太短的标题（<4 字符，可能是空标题或脚注）
    """
    if not handbook_md:
        return []

    # 提取 ## 和 ### 标题
    # ## 3.1 条件判断语句(if-elif-else)
    # ### 3.1.1 xxx
    heading_pattern = re.compile(r"^(#{2,3})\s+(.+)$", re.MULTILINE)
    skip_keywords = [
        "学习目标", "学习资源", "任务描述", "实践目标",
        "重点概念", "总结", "思考题", "本章小结",
        "references", "参考", "附录",
    ]

    kps: list[str] = []
    for match in heading_pattern.finditer(handbook_md):
        level, text = match.group(1), match.group(2).strip()
        # 跳过非知识点章节
        if any(kw in text for kw in skip_keywords):
            continue
        # 跳过太短的标题
        if len(text) < 4:
            continue
        # 跳过包含文件扩展名的行（资源引用）
        if re.search(r"\.(mp4|pdf|docx|pptx)$", text, re.I):
            continue
        # 清理标题: 去掉编号前缀 3.1, 3.1.1 等
        cleaned = re.sub(r"^[\d\.\s]+", "", text).strip()
        if cleaned:
            kps.append(cleaned)

    return kps


# ------------------------------------------------------------------
# 主逻辑: 反向生成 YAML
# ------------------------------------------------------------------

def backfill_task(task_id: int, course: str | None = None) -> dict:
    """
    从 DB 反向推断 stage YAML 字段值。

    Returns:
        dict: YAML 字段值字典
    """
    db_path = _db_path()
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ---- 查询 task ----
    cur.execute(
        """
        SELECT t.id, t.title, t.practice_id, t.handbook_markdown,
               t.question_data, t.order_in_practice,
               p.id as practice_id_check,
               p.title as practice_title, p.category, p.difficulty
        FROM tasks t
        JOIN practices p ON t.practice_id = p.id
        WHERE t.id = ?
        """,
        (task_id,),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Task ID {task_id} not found in database")

    row = dict(row)

    # ---- 查询 task_tests ----
    # NOTE: SQLite BOOLEAN stores as integer 0/1, dict keys are integers.
    # SQLite GROUP BY returns 0 or 1 as integer keys. Use only integer key.
    # SQLite does NOT distinguish False/True as separate keys (False == 0, True == 1).
    cur.execute(
        """
        SELECT is_hidden, COUNT(*) as cnt
        FROM task_tests
        WHERE task_id = ?
        GROUP BY is_hidden
        """,
        (task_id,),
    )
    test_rows = {r["is_hidden"]: r["cnt"] for r in cur.fetchall()}
    visible_count = test_rows.get(0, 0)   # False == 0 in Python dict
    hidden_count = test_rows.get(1, 0)    # True == 1 in Python dict

    conn.close()

    # ---- 解析 question_data ----
    # NOTE: question_data can be NULL, malformed JSON, or a non-dict value.
    # Handle all cases gracefully.
    qd = None
    questions: list[dict] = []
    baseline_code = None
    test_cases: list[dict] = []

    if row["question_data"]:
        try:
            qd = json.loads(row["question_data"])
            if isinstance(qd, dict):
                questions = [q for q in (qd.get("questions") or []) if isinstance(q, dict)]
                baseline_code = qd.get("baseline_code")
                test_cases = [tc for tc in (qd.get("test_cases") or []) if isinstance(tc, dict)]
            else:
                # JSON is valid but not a dict (e.g., null, array, string)
                questions = []
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass

    # ---- 统计题目类型和难度 ----
    type_counter = Counter(q.get("type") for q in questions if q.get("type"))
    diff_counter = Counter(q.get("difficulty") for q in questions if q.get("difficulty"))

    # ---- 推断 stage_id ----
    # 约定: tasks.title 包含 "关卡 N" 或 task 在 practice 中的顺序
    # 如果 title 是 "xxx - 关卡 2" → stage_id = 2
    # 否则用 order_in_practice
    title = row["title"] or ""
    stage_id_match = re.search(r"关卡\s*(\d+)", title)
    if stage_id_match:
        stage_id = int(stage_id_match.group(1))
    else:
        stage_id = row.get("order_in_practice") or 1

    # ---- 推断 course ----
    # category 字段示例: "Python", "Python编程", "机器学习"
    # 映射到小写的 course 名: python, ml 等
    category = row["category"] or ""
    if course:
        course_name = course.lower()
    else:
        # 从 category 推断
        cat_lower = category.lower()
        if "python" in cat_lower:
            course_name = "python"
        elif "机器学习" in category or "数据挖掘" in category:
            course_name = "ml"
        elif "神经网络" in category or "深度学习" in category:
            course_name = "dl"
        elif "spark" in cat_lower:
            course_name = "spark"
        elif "hadoop" in cat_lower or "大数据" in category:
            course_name = "bigdata"
        else:
            course_name = "unknown"

    # ---- 推断 knowledge_points ----
    knowledge_points = _extract_knowledge_points(row["handbook_markdown"])

    # ---- 推断 expected_handbook_min_chars ----
    handbook_text = row["handbook_markdown"] or ""
    handbook_len = len(handbook_text)
    expected_handbook_min_chars = max(0, handbook_len - 100)

    # ---- 构建字段字典 ----
    fields: dict = {
        "course": course_name,
        "course_db_id": row["practice_id"],
        "stage_id": stage_id,
        "stage_name": (row["title"] or "").strip(),
        "difficulty": (row["difficulty"] or "intermediate").lower(),
        "knowledge_points": knowledge_points,
        "expected_handbook_min_chars": expected_handbook_min_chars,
        "expected_questions": len(questions),
        "expected_test_cases_visible": visible_count,
        # NOTE: Schema requires hidden >= 1 (ge=1). 如果 DB 无数据，验证会失败，这是正确行为。
        # task_tests 为空时 hidden_count=0，Schema 验证报错，脚本不写文件。
        "expected_test_cases_hidden": hidden_count,
        "total_score": 100,
    }

    # ---- 子模型字段 ----
    if type_counter:
        fields["expected_question_types"] = {
            "concept": type_counter.get("concept", 0),
            "calculation": type_counter.get("calculation", 0),
            "coding": type_counter.get("coding", 0),
        }

    if diff_counter:
        fields["expected_question_difficulties"] = {
            "easy": diff_counter.get("easy", 0),
            "medium": diff_counter.get("medium", 0),
            "hard": diff_counter.get("hard", 0),
        }

    if baseline_code:
        fields["baseline_code_template"] = baseline_code

    # ---- 人工填写字段 (留空) ----
    fields["style_reference"] = []
    fields["prerequisites"] = []
    fields["topics_to_avoid"] = []
    fields["codex_review_required"] = True

    return fields


def generate_backfill_report(task_id: int, fields: dict) -> str:
    """生成反向推断对照报告 markdown。"""
    now = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# 关卡 {fields['stage_id']} 反向推断对照报告",
        f"# DB Source: tasks.id={task_id}, practices.id={fields['course_db_id']}",
        f"# 生成时间: {now}",
        "",
        "## 一、字段推导来源",
        "",
        "| 字段 | 值 | 来源 |",
        "|------|-----|------|",
    ]

    source_map = {
        "course": f"practices.category → {fields['course']}",
        "course_db_id": f"tasks.practice_id",
        "stage_id": "从 tasks.title 中提取 '关卡 N' 编号",
        "stage_name": "tasks.title",
        "difficulty": "practices.difficulty",
        "knowledge_points": f"handbook_markdown ##/### 章节标题 (共 {len(fields['knowledge_points'])} 条)",
        "expected_handbook_min_chars": f"len(handbook_markdown)={fields['expected_handbook_min_chars'] + 100} - 100余量",
        "expected_questions": f"question_data.questions 数组长度",
        "expected_test_cases_visible": "task_tests WHERE is_hidden = false",
        "expected_test_cases_hidden": "task_tests WHERE is_hidden = true",
        "total_score": "固定值 100",
        "baseline_code_template": "question_data.baseline_code (如有)",
    }

    for key, src in source_map.items():
        val = fields.get(key, "")
        if isinstance(val, list):
            val_str = f"[{len(val)} 项]"
        elif isinstance(val, dict):
            val_str = str(val)
        else:
            val_str = repr(val)
        lines.append(f"| {key} | {val_str} | {src} |")

    lines += [
        "",
        "## 二、不可反向推断的字段（留空待人工填写）",
        "",
        "| 字段 | 说明 | 填写建议 |",
        "|------|------|---------|",
        "| style_reference | 风格参考（来自调研报告） | 从 content_orchestrator/knowledge_base/ 提取 |",
        "| prerequisites | 前置关卡 | 根据知识点依赖关系确定 |",
        "| topics_to_avoid | 避免的知识点 | 根据教学大纲确定 |",
        "| codex_review_required | 是否需要Codex审查 | 默认为 true |",
        "",
        "## 三、数据完整性检查",
        "",
        f"- [x] tasks 表: Task ID={task_id} 存在",
        f"- [x] handbook 长度: {fields['expected_handbook_min_chars'] + 100} 字符",
        f"- [x] 知识要点: {len(fields['knowledge_points'])} 条（从 ##/### 标题提取）",
        f"- [x] 题目数: {fields['expected_questions']}",
        f"- [x] 可见测试用例: {fields['expected_test_cases_visible']}",
        f"- [x] 隐藏测试用例: {fields['expected_test_cases_hidden']}",
    ]

    return "\n".join(lines)


# ------------------------------------------------------------------
# CLI 入口
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="反向生成 stage YAML 配置")
    parser.add_argument("--task-id", type=int, required=True, help="DB tasks.id")
    parser.add_argument("--course", type=str, default=None, help="课程名（小写，如 python）")
    parser.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    parser.add_argument("--force", action="store_true",
                        help="Schema 验证失败时仍写入文件（用于手工修复）")
    args = parser.parse_args()

    print(f"正在从 DB 反向生成 Task ID={args.task_id} ...")

    try:
        fields = backfill_task(args.task_id, args.course)
    except ValueError as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)

    # 验证 YAML 格式 (strict 模式)
    validation_errors: list[str] = []
    try:
        cfg = StageConfig.model_validate(fields)
        print(f"Schema 验证通过: stage_id={cfg.stage_id}, kps={len(cfg.knowledge_points)}, "
              f"questions={cfg.expected_questions}")
    except Exception as e:
        errors = getattr(e, "errors", lambda: [{"msg": str(e)}])()
        for err in errors:
            msg = err.get("msg", str(err))
            loc = ".".join(str(l) for l in err.get("loc", []))
            validation_errors.append(f"  {'.'.join(str(x) for x in err.get('loc', []))}: {msg}")
        print(f"Schema 验证失败 ({len(validation_errors)} 项):", file=sys.stderr)
        for ve in validation_errors:
            print(ve, file=sys.stderr)
        if not args.force:
            print("\n使用 --force 强制写入（需手工修复后再运行）", file=sys.stderr)
            sys.exit(1)
        print("\n[--force] Schema 验证失败但仍写入文件", file=sys.stderr)

    # 生成文件路径
    course = fields["course"]
    stage = fields["stage_id"]
    base = Path(__file__).parent.parent / "stages_config" / course
    base.mkdir(parents=True, exist_ok=True)
    yaml_path = base / f"stage_{stage}.yaml"
    report_path = base / f"stage_{stage}_backfill_report.md"

    yaml_content = yaml.safe_dump(fields, allow_unicode=True, sort_keys=False, default_flow_style=False)
    report_content = generate_backfill_report(args.task_id, fields)

    if args.dry_run:
        print("\n=== stage YAML ===")
        print(yaml_content)
        print("\n=== backfill report ===")
        print(report_content)
    else:
        yaml_path.write_text(yaml_content, encoding="utf-8")
        report_path.write_text(report_content, encoding="utf-8")
        print(f"\n已生成:")
        print(f"  YAML:   {yaml_path}")
        print(f"  报告:   {report_path}")
        print(f"\n知识要点 ({len(fields['knowledge_points'])} 条):")
        for kp in fields["knowledge_points"]:
            print(f"  - {kp}")


if __name__ == "__main__":
    main()
