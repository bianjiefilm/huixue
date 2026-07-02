"""
Pydantic schemas for adversarial review output.
"""
from typing import Optional
from pydantic import BaseModel, Field


class AdversarialBug(BaseModel):
    """Bug found during adversarial testing."""
    bug_id: str = Field(..., description="Unique bug ID, e.g., 'BUG-001'")
    question_id: Optional[str] = Field(None, description="Question ID with the bug")
    severity: str = Field(..., description="Severity: critical, high, medium, low")
    category: str = Field(..., description="Category: multiple_correct_answers, wrong_output, etc.")
    description: str = Field(..., description="Detailed description of the bug")
    evidence: Optional[str] = Field(None, description="Evidence, e.g., Python output showing the bug")
    reproduction_steps: Optional[str] = Field(None, description="Steps to reproduce")
    must_fix: bool = Field(True, description="Whether this bug must be fixed before shipping")

    class Config:
        json_schema_extra = {
            "example": {
                "bug_id": "BUG-001",
                "question_id": "q2-6",
                "severity": "critical",
                "category": "multiple_correct_answers",
                "description": "Both B and D produce the same output [0, 4, 16, 36, 64]",
                "evidence": "B: [i**2 for i in range(0, 10, 2)] = [0, 4, 16, 36, 64]\nD: [(2*i)**2 for i in range(5)] = [0, 4, 16, 36, 64]",
                "reproduction_steps": "python3 -c \"print([i**2 for i in range(0, 10, 2)])\"",
                "must_fix": True
            }
        }


class AdversarialResult(BaseModel):
    """Result from adversarial review."""
    bugs: list[AdversarialBug] = Field(default_factory=list, description="List of bugs found")
    total_bugs: int = Field(..., description="Total number of bugs")
    critical_count: int = Field(0, description="Number of critical bugs")
    high_count: int = Field(0, description="Number of high severity bugs")
    summary: str = Field(..., description="Brief summary of findings")

    @property
    def has_critical_or_high(self) -> bool:
        """Check if there are any critical or high severity bugs."""
        return self.critical_count > 0 or self.high_count > 0

    @property
    def is_acceptable(self) -> bool:
        """Check if the content is acceptable (no critical/high bugs)."""
        return not self.has_critical_or_high

    def get_bug_by_id(self, bug_id: str) -> Optional[AdversarialBug]:
        """Get a specific bug by ID."""
        for bug in self.bugs:
            if bug.bug_id == bug_id:
                return bug
        return None

    class Config:
        json_schema_extra = {
            "example": {
                "bugs": [
                    {
                        "bug_id": "BUG-001",
                        "question_id": "q2-6",
                        "severity": "critical",
                        "category": "multiple_correct_answers",
                        "description": "...",
                        "must_fix": True
                    }
                ],
                "total_bugs": 1,
                "critical_count": 1,
                "high_count": 0,
                "summary": "Found 1 critical bug in q2-6"
            }
        }
