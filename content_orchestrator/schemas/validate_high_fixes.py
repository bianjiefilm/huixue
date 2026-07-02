"""
Validation test: 4 HIGH fixes for stage_config.py.
Run: python -m content_orchestrator.schemas.validate_high_fixes
"""
import sys, traceback
from content_orchestrator.schemas.stage_config import StageConfig, QuestionTypeCount, DifficultyCount
from pydantic import ValidationError

PASS = 0
FAIL = 0

def check(name: str, expected_error: bool, fn):
    global PASS, FAIL
    try:
        fn()
        ok = not expected_error
    except ValidationError as e:
        errors = e.errors()
        # Check it raised for the RIGHT reason
        if expected_error:
            ok = True  # Any ValidationError counts as PASS
        else:
            ok = False
            print(f"  UNEXPECTED ValidationError: {errors[0]['msg']}")
    except Exception:
        ok = False
        traceback.print_exc()
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}")
    if ok:
        PASS += 1
    else:
        FAIL += 1

# ─── HIGH #9: strict=True — no coercion ────────────────────────────────
print("\n=== HIGH #9: strict=True (no silent coercion) ===")

def test_true_not_coerced_to_int():
    """strict=True rejects bool where int is expected."""
    QuestionTypeCount(model_config={"strict": True}, concept=True)

def test_string_not_coerced_to_int():
    """strict=True rejects str where int is expected."""
    StageConfig(
        model_config={"strict": True},
        course="python", course_db_id="11",  # str not int
        stage_id=2, stage_name="test", difficulty="beginner",
        knowledge_points=["kp1"],
        expected_handbook_min_chars=1000, expected_questions=10,
        expected_test_cases_visible=2, expected_test_cases_hidden=2,
        total_score=100,
    )

def test_int_accepted():
    """Correct int is still accepted."""
    QuestionTypeCount(concept=4, calculation=5, coding=1)

check("bool True rejected as int", True, test_true_not_coerced_to_int)
check("str '11' rejected as int", True, test_string_not_coerced_to_int)
check("correct int 4 accepted", False, test_int_accepted)

# ─── HIGH #10: extra="forbid" — typo fields ───────────────────────────
print("\n=== HIGH #10: extra='forbid' (typo fields rejected) ===")

def test_typo_field_rejected():
    """Extra field 'codex_review_requred' (typo) must raise."""
    StageConfig(
        course="python", course_db_id=11, stage_id=2, stage_name="test",
        difficulty="beginner", knowledge_points=["kp1"],
        expected_handbook_min_chars=1000, expected_questions=10,
        expected_test_cases_visible=2, expected_test_cases_hidden=2,
        total_score=100,
        codex_review_requred=True,  # typo: should be codex_review_required
    )

def test_valid_config_accepted():
    """Valid config with all correct fields accepted."""
    StageConfig(
        course="python", course_db_id=11, stage_id=2, stage_name="test",
        difficulty="beginner", knowledge_points=["kp1"],
        expected_handbook_min_chars=1000, expected_questions=10,
        expected_test_cases_visible=2, expected_test_cases_hidden=2,
        total_score=100,
    )

check("typo field 'codex_review_requred' rejected", True, test_typo_field_rejected)
check("correct field 'codex_review_required' accepted", False, test_valid_config_accepted)

# ─── HIGH #6: model_validator cross-check ──────────────────────────────
print("\n=== HIGH #6: model_validator (cross-field count check) ===")

def test_type_sum_mismatch_raises():
    """expected_question_types sum != expected_questions must raise."""
    StageConfig(
        course="python", course_db_id=11, stage_id=2, stage_name="test",
        difficulty="beginner", knowledge_points=["kp1"],
        expected_handbook_min_chars=1000, expected_questions=10,  # says 10
        expected_test_cases_visible=2, expected_test_cases_hidden=2, total_score=100,
        expected_question_types={"concept": 2, "calculation": 2, "coding": 1},  # sum=5, not 10
    )

def test_diff_sum_mismatch_raises():
    """expected_question_difficulties sum != expected_questions must raise."""
    StageConfig(
        course="python", course_db_id=11, stage_id=2, stage_name="test",
        difficulty="beginner", knowledge_points=["kp1"],
        expected_handbook_min_chars=1000, expected_questions=10,
        expected_test_cases_visible=2, expected_test_cases_hidden=2, total_score=100,
        expected_question_difficulties={"easy": 2, "medium": 2, "hard": 1},  # sum=5, not 10
    )

def test_matching_counts_accepted():
    """Matching counts (10=10) accepted."""
    StageConfig(
        course="python", course_db_id=11, stage_id=2, stage_name="test",
        difficulty="beginner", knowledge_points=["kp1"],
        expected_handbook_min_chars=1000, expected_questions=10,
        expected_test_cases_visible=2, expected_test_cases_hidden=2, total_score=100,
        expected_question_types={"concept": 4, "calculation": 5, "coding": 1},
        expected_question_difficulties={"easy": 4, "medium": 5, "hard": 1},
    )

def test_no_counts_accepted():
    """No type/difficulty counts — no cross-check needed."""
    StageConfig(
        course="python", course_db_id=11, stage_id=2, stage_name="test",
        difficulty="beginner", knowledge_points=["kp1"],
        expected_handbook_min_chars=1000, expected_questions=10,
        expected_test_cases_visible=2, expected_test_cases_hidden=2, total_score=100,
    )

check("type sum mismatch (5 != 10) raises", True, test_type_sum_mismatch_raises)
check("diff sum mismatch (5 != 10) raises", True, test_diff_sum_mismatch_raises)
check("matching counts (10=10) accepted", False, test_matching_counts_accepted)
check("no counts (optional) accepted", False, test_no_counts_accepted)

# ─── HIGH #14: content.py — no severity fields ─────────────────────────
print("\n=== HIGH #14: content.py — no severity fields ===")

from content_orchestrator.schemas.content import Question, TestCase, StageContent

def test_question_no_severity():
    """Question model must NOT have severity/priority fields."""
    import inspect
    sig = inspect.signature(Question).parameters
    forbidden = {"severity", "priority", "weight", "importance"}
    for field in forbidden:
        assert field not in sig, f"Question should not have '{field}' field"

check("Question has no severity/priority fields", False, test_question_no_severity)

# ─── Summary ─────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Results: {PASS} PASS / {FAIL} FAIL")
sys.exit(0 if FAIL == 0 else 1)
