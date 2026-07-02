"""
Pydantic schemas for review output.
"""
from typing import Optional
from pydantic import BaseModel, Field


class ReviewIssue(BaseModel):
    """Individual issue found in review."""
    question_id: str = Field(..., description="Question ID with the issue")
    issue_type: str = Field(..., description="Type: answer_error, ambiguous, difficulty_mismatch, etc.")
    severity: str = Field(..., description="Severity: critical, high, medium, low")
    description: str = Field(..., description="Description of the issue")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix if applicable")


class ReviewResult(BaseModel):
    """Result from review agent."""
    score: int = Field(..., ge=0, le=100, description="Overall quality score (0-100)")
    issues: list[ReviewIssue] = Field(default_factory=list, description="List of issues found")
    strengths: list[str] = Field(default_factory=list, description="What's done well")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    summary: str = Field(..., description="Brief summary of the review")

    @property
    def has_critical_or_high(self) -> bool:
        """Check if there are any critical or high severity issues."""
        return any(i.severity in ("critical", "high") for i in self.issues)

    @property
    def passing(self) -> bool:
        """Check if the content passes review."""
        return self.score >= 85 and not self.has_critical_or_high

    class Config:
        json_schema_extra = {
            "example": {
                "score": 88,
                "issues": [
                    {
                        "question_id": "q2-4",
                        "issue_type": "answer_error",
                        "severity": "critical",
                        "description": "Answer should be 12, not 7",
                        "suggested_fix": "Change answer to '12'"
                    }
                ],
                "strengths": ["Good coverage of topics", "Clear explanations"],
                "suggestions": ["Add more test cases"],
                "summary": "Good content with one critical issue"
            }
        }
