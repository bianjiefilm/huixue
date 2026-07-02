"""
AI Features Service Module

This module provides AI-powered features for the Huixue education platform,
integrating with PromptPilot (Volcengine) for prompt management.

Features:
- Dashboard Recommendation: Personalized course recommendations
- AI Brainstorm: Creative idea generation for projects
- Command Palette NLU: Natural language understanding for commands
- Code Suggestion: Proactive code optimization suggestions
- Code Explanation: On-demand code explanation
- Error Diagnosis: Evaluation error diagnosis
- General Chat: General AI conversation
"""

from .feature_service import PromptPilotFeatureService

__all__ = ["PromptPilotFeatureService"]

