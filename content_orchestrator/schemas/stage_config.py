"""
Pydantic schema for stage configuration YAML files.
Defines the structure of stages_config/<course>/stage_{n}.yaml.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ------------------------------------------------------------------
# Sub-models for aggregate counts
# ------------------------------------------------------------------

class QuestionTypeCount(BaseModel):
    """Expected count of each question type (field names match DB question_type values)."""
    model_config = ConfigDict(strict=True, extra="forbid")

    concept: int = Field(0, ge=0)
    calculation: int = Field(0, ge=0)
    coding: int = Field(0, ge=0)


class DifficultyCount(BaseModel):
    """Expected count of each difficulty level."""
    model_config = ConfigDict(strict=True, extra="forbid")

    easy: int = Field(0, ge=0)
    medium: int = Field(0, ge=0)
    hard: int = Field(0, ge=0)


# ------------------------------------------------------------------
# Main schema
# ------------------------------------------------------------------

class StageConfig(BaseModel):
    """
    Stage configuration loaded from YAML.

    必填 11 个:
      course, course_db_id, stage_id, stage_name, difficulty,
      knowledge_points, expected_handbook_min_chars, expected_questions,
      expected_test_cases_visible, expected_test_cases_hidden, total_score

    可选 7 个:
      expected_question_types, expected_question_difficulties,
      baseline_code_template, style_reference, prerequisites,
      topics_to_avoid, codex_review_required
    """
    model_config = ConfigDict(strict=True, extra="forbid")

    # --- 11 required fields -----------------------------------------
    course: str = Field(..., description="Course name, e.g. 'python'")
    course_db_id: int = Field(..., description="DB practices.id for this course")
    stage_id: int = Field(..., ge=1, description="Stage number")
    stage_name: str = Field(..., description="Stage title in Chinese")
    difficulty: str = Field(..., description="Difficulty: beginner | intermediate | advanced")
    knowledge_points: list[str] = Field(
        ...,
        description="List of knowledge points covered in this stage",
    )
    expected_handbook_min_chars: int = Field(
        ...,
        ge=0,
        description="Minimum expected handbook character count",
    )
    expected_questions: int = Field(..., ge=1, description="Expected question count")
    expected_test_cases_visible: int = Field(
        ...,
        ge=0,
        description="Expected number of visible (non-hidden) test cases",
    )
    expected_test_cases_hidden: int = Field(
        ...,
        ge=1,
        description="Expected number of hidden test cases (anti-cheat, must be >= 1)",
    )
    total_score: int = Field(
        ...,
        ge=1,
        le=100,
        description="Total score",
    )

    # --- 7 optional fields ------------------------------------------
    expected_question_types: Optional[QuestionTypeCount] = Field(
        None,
        description="Expected distribution of question types",
    )
    expected_question_difficulties: Optional[DifficultyCount] = Field(
        None,
        description="Expected distribution of difficulty levels",
    )
    baseline_code_template: Optional[str] = Field(
        None,
        description="Starter code template shown to students",
    )
    style_reference: list[str] = Field(
        default_factory=list,
        description="Style hints from research report (filled manually)",
    )
    prerequisites: list[int] = Field(
        default_factory=list,
        description="Prerequisite stage IDs (filled manually)",
    )
    topics_to_avoid: list[str] = Field(
        default_factory=list,
        description="Topics to avoid in this stage (filled manually)",
    )
    codex_review_required: bool = Field(
        True,
        description="Whether Codex manual review is required before import",
    )

    # --- Validators -----------------------------------------------
    @field_validator("difficulty")
    @classmethod
    def _difficulty_values(cls, v: str) -> str:
        allowed = {"beginner", "intermediate", "advanced"}
        if v.lower() not in allowed:
            raise ValueError(f"difficulty must be one of {allowed}, got '{v}'")
        return v.lower()

    @field_validator("knowledge_points")
    @classmethod
    def _kp_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("knowledge_points cannot be empty")
        return v

    @field_validator("stage_name", mode="after")
    @classmethod
    def _strip_stage_name(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def _cross_check_counts(self) -> "StageConfig":
        """Cross-check expected_questions vs type/difficulty counts."""
        if self.expected_question_types is not None:
            type_sum = (
                self.expected_question_types.concept
                + self.expected_question_types.calculation
                + self.expected_question_types.coding
            )
            if type_sum != self.expected_questions:
                raise ValueError(
                    f"expected_question_types sum ({type_sum}) != "
                    f"expected_questions ({self.expected_questions})"
                )
        if self.expected_question_difficulties is not None:
            diff_sum = (
                self.expected_question_difficulties.easy
                + self.expected_question_difficulties.medium
                + self.expected_question_difficulties.hard
            )
            if diff_sum != self.expected_questions:
                raise ValueError(
                    f"expected_question_difficulties sum ({diff_sum}) != "
                    f"expected_questions ({self.expected_questions})"
                )
        return self

    # --- Helpers -------------------------------------------------
    @classmethod
    def from_yaml(cls, path: str | Path) -> StageConfig:
        """Load and validate a YAML config file."""
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if raw is None:
            raise ValueError(f"Empty YAML file: {path}")
        # Defensive: convert nulls to [] for list fields that have defaults
        list_fields = {"style_reference", "prerequisites", "topics_to_avoid"}
        for field in list_fields:
            if field in raw and raw[field] is None:
                raw[field] = []
        return cls.model_validate(raw)

    def to_yaml(self, path: str | Path) -> None:
        """Write validated config to YAML file."""
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.model_dump(), f, allow_unicode=True, sort_keys=False)

    def log_source_map(self) -> dict[str, dict[str, Any]]:
        """Per-field provenance map for backfill reporting."""
        return {
            "course": {"source": "practices.category (fixed)", "note": ""},
            "course_db_id": {"source": "tasks.practice_id", "note": "DB practices.id"},
            "stage_id": {"source": "fixed naming", "note": ""},
            "stage_name": {"source": "tasks.title", "note": ""},
            "difficulty": {"source": "practices.difficulty", "note": ""},
            "knowledge_points": {"source": "handbook_markdown §3 headings", "note": "extracted verbatim"},
            "expected_handbook_min_chars": {
                "source": "len(handbook_markdown) - 100",
                "note": "actual minus buffer",
            },
            "expected_questions": {
                "source": "question_data.questions length",
                "note": "",
            },
            "expected_test_cases_visible": {
                "source": "task_tests WHERE is_hidden = false",
                "note": "",
            },
            "expected_test_cases_hidden": {
                "source": "task_tests WHERE is_hidden = true",
                "note": "",
            },
            "total_score": {"source": "fixed constant", "note": "always 100"},
            "expected_question_types": {
                "source": "question_data.questions[*].type",
                "note": "aggregate by type",
            },
            "expected_question_difficulties": {
                "source": "question_data.questions[*].difficulty",
                "note": "aggregate by difficulty",
            },
            "baseline_code_template": {
                "source": "question_data.baseline_code",
                "note": "",
            },
            "style_reference": {"source": "manual", "note": "from research report"},
            "prerequisites": {"source": "manual", "note": "teaching dependency"},
            "topics_to_avoid": {"source": "manual", "note": "curriculum scope"},
            "codex_review_required": {"source": "manual", "note": "default true"},
        }
