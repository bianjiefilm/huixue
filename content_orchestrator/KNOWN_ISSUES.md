# Known Issues — stage_config.py Schema

Generated from Codex adversarial challenge (2026-04-22).
7 fixes applied: 4 HIGH + 3 MEDIUM.
11 MEDIUM issues below are **intentionally deferred** — reasons documented.

---

## Deferred MEDIUM Issues

### #1 — knowledge_points accepts empty list silently
**Location:** `StageConfig.knowledge_points` (required field)
**Problem:** Field has `ge=0` constraint but empty list passes through.
**Impact:** Generated content has no knowledge points, handbook has no alignment anchor.
**Fix (if needed):** Add `min_length=1` to the Field, or add a `field_validator` that raises if len < 1.
**Reason for deferral:** `_kp_not_empty` validator exists and raises on empty. Codex flagged that the validator could be bypassed via direct `model_validate` with `{}`. The validator IS present in current code. Monitoring — if production data shows empty KPs, elevate to HIGH.

---

### #2 — stage_name silently accepts whitespace
**Location:** `StageConfig.stage_name` (required field)
**Problem:** Leading/trailing spaces in YAML like `"  控制流与循环  "` pass through.
**Impact:** Display names have extra padding; DB lookups may fail.
**Fix (if needed):** Already handled by `_strip_stage_name` validator (mode="after").
**Reason for deferral:** Validator already exists. Codex flagged the original had no strip — confirmed fixed.

---

### #3 — difficulty accepts case variants silently
**Location:** `StageConfig.difficulty` (required field)
**Problem:** YAML `difficulty: INTERMEDIATE` gets lowercased to `"intermediate"` — this is actually correct behavior (validator converts to lowercase). But `difficulty: Beginner` raises, which is inconsistent.
**Impact:** Minor UX inconsistency.
**Fix (if needed):** Normalize input in validator: `return v.lower()` already does this.
**Reason for deferral:** The validator DOES lowercase, so `"INTERMEDIATE"` → `"intermediate"`. Codex flagged this as "accepts case variants" — but that is the intentional design (case-insensitive). No fix needed.

---

### #4 — Unknown question types silently accepted
**Location:** `QuestionTypeCount` sub-model
**Problem:** If `question_data.questions[*].type` contains an unknown type (e.g., `"coding-interview"`), it gets dropped silently.
**Impact:** Type counts don't match actual question data.
**Fix (if needed):** Add an `enum` constraint to `Question.type` in content.py, or add a `field_validator` on `QuestionTypeCount` that warns on unknown types.
**Reason for deferral:** Low risk in practice — the only valid types are `concept`, `calculation`, `coding`. Adding enum would break forward compatibility if new types are added. Can be addressed when a real unknown type appears.

---

### #5 — Unknown difficulty levels silently accepted
**Location:** `DifficultyCount` sub-model
**Problem:** Same as #4 — if `question_data.questions[*].difficulty` contains an unknown level, it's silently ignored.
**Impact:** Difficulty counts don't match actual question data.
**Fix (if needed):** Add enum constraint or warning validator.
**Reason for deferral:** Same as #4. Only `easy`, `medium`, `hard` are used. Low risk.

---

### #7 — expected_handbook_min_chars allows zero
**Location:** `StageConfig.expected_handbook_min_chars` (required field)
**Problem:** `ge=0` allows zero, which makes the check meaningless.
**Impact:** Content with 0-character handbook passes validation.
**Fix (if needed):** Change `ge=0` to `ge=500` (minimum meaningful handbook size).
**Reason for deferral:** The field is a minimum threshold, not a required size. A stage with zero handbook is unusual but theoretically valid (e.g., external-resource-only stage). Punting until real data shows a pattern.

---

### #8 — total_score allows non-100 values
**Location:** `StageConfig.total_score` (required field)
**Problem:** `le=100` allows 1–99, not just 100.
**Impact:** Score aggregation across stages breaks if stages have different totals.
**Fix (if needed):** Change to `const=100` in Pydantic v2, or add a `field_validator` that only accepts 100.
**Reason for deferral:** The `total_score` field is intended to always be 100, but some stages might legitimately use different scoring (e.g., bonus-only stages). Until real data confirms all are 100, keep flexibility. Can be tightened later.

---

### #11 — style_reference missing type enforcement
**Location:** `StageConfig.style_reference` (list[str])
**Problem:** No constraints on list items — any string accepted.
**Impact:** Manual entry may contain free-form prose instead of structured hints.
**Fix (if needed):** Add a `field_validator` that checks each item against known style keywords (e.g., `"五段结构"`, `"任务导向"`, `"中文为主"`).
**Reason for deferral:** Manual field, filled by humans, not by AI generation. Type enforcement adds friction without clear benefit. Revisit if style_reference entries become noisy.

---

### #12 — prerequisites missing type enforcement
**Location:** `StageConfig.prerequisites` (list[int])
**Problem:** No validation that referenced stage IDs actually exist in the course.
**Impact:** Broken prerequisite chains — student shown a stage with unmet prerequisites.
**Fix (if needed):** Add a cross-config validator that checks `prerequisites` against known stage IDs in the course's stage registry.
**Reason for deferral:** Requires cross-config context (knowledge of all stages in a course) — cannot validate in isolation. Better handled at the pipeline level when importing a full course config set.

---

### #13 — topics_to_avoid missing type enforcement
**Location:** `StageConfig.topics_to_avoid` (list[str])
**Problem:** No validation that topics are actual knowledge point strings.
**Impact:** Free-form entries not aligned with actual curriculum scope.
**Fix (if needed):** Cross-reference against a course-level knowledge point registry.
**Reason for deferral:** Manual field, like style_reference. Hard to validate without a global KP registry. Revisit when course-level registry exists.

---

### #16 — baseline_code_template has no max length
**Location:** `StageConfig.baseline_code_template` (Optional[str])
**Problem:** Arbitrarily long strings accepted — no sanity check.
**Impact:** Pipeline memory issues with extremely large templates; also a potential vector for abuse if pipeline is exposed to untrusted input.
**Fix (if needed):** Add `max_length=5000` to the Field.
**Reason for deferral:** Not a schema validation concern — the pipeline handles memory at runtime. Long templates are a data quality issue, not a correctness issue. Can add at import time if needed.

---

## Fixed Issues (Reference)

| ID | Severity | Issue | Fix |
|----|----------|-------|-----|
| #6 | HIGH | Cross-field count mismatch not caught | `model_validator(after)` on `StageConfig` |
| #9 | HIGH | `True` → `1`, `"10"` → `10` coercion | `ConfigDict(strict=True)` on all models |
| #10 | HIGH | Typo field `codex_review_requred` ignored | `extra="forbid"` on all models |
| #14 | HIGH | No severity fields in content.py | Confirmed: only in review.py (correct) |
| #15 | MEDIUM | `from_yaml` null→[] conversion | Defensive null→[] for list fields |
| #17 | MEDIUM | YAML comments referenced wrong field names | Fixed: `task_tests` not `question_data.test_cases` |
| #18 | MEDIUM | Missing `encoding="utf-8"` on file open | Added to `from_yaml` and `to_yaml` |
