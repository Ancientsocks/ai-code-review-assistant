from typing import Literal
from pydantic import BaseModel, Field, ConfigDict


class ReviewRequest(BaseModel):
    language: str = Field(min_length=1, max_length=40)
    code: str = Field(min_length=1, max_length=50000)

    model_config = ConfigDict(str_strip_whitespace=False)


class Finding(BaseModel):
    source: Literal["ruff", "bandit", "ai", "system"]
    severity: Literal["critical", "high", "medium", "low", "info"]
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=4000)
    line: int | None = Field(default=None, ge=1)
    rule_id: str | None = Field(default=None, max_length=100)
    suggestion: str | None = Field(default=None, max_length=4000)


class ReviewResult(BaseModel):
    summary: str = Field(max_length=4000)
    findings: list[Finding] = Field(default_factory=list)


class ReviewResponse(ReviewResult):
    id: int | None = None
    language: str
    created_at: str | None = None
