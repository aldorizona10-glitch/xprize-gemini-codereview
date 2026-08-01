"""
CodeLens AI - Pydantic Models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ReviewRequest(BaseModel):
    code: str = Field(..., description="Code to review", min_length=1)
    language: str = Field(default="python", description="Programming language")
    context: str = Field(default="", description="Additional context for review")


class ReviewIssue(BaseModel):
    severity: str
    line: Optional[int] = None
    title: str
    description: str
    suggestion: str


class ReviewResponse(BaseModel):
    review_id: str
    timestamp: str
    language: str
    lines_reviewed: int
    score: int
    summary: str
    issues: List[ReviewIssue]
    strengths: List[str]
    recommendations: List[str]
    security: dict
    performance: dict
    powered_by: str
