"""Job Description parsing models."""

from datetime import datetime

from pydantic import BaseModel, Field


class JDParseRequest(BaseModel):
    """Request to parse a job description."""

    url: str | None = None  # URL to scrape
    text: str | None = None  # Raw JD text (fallback)

    class Config:
        json_schema_extra = {"example": {"url": "https://careers.google.com/jobs/123"}}


class ParsedJD(BaseModel):
    """
    Structured representation of a job description.
    Extracted via Gemini for consistent parsing.
    """

    jd_id: str = Field(..., description="Unique identifier for this JD")
    role_title: str
    company: str
    must_haves: list[str] = Field(
        default_factory=list, description="Required skills/qualifications"
    )
    nice_to_haves: list[str] = Field(default_factory=list, description="Preferred qualifications")
    responsibilities: list[str] = Field(default_factory=list, description="Key job duties")
    keywords: list[str] = Field(
        default_factory=list, description="Technical terms, tools, frameworks"
    )
    source_url: str | None = None
    raw_text: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "jd_id": "jd_google_swe_20260124",
                "role_title": "Software Engineer",
                "company": "Google",
                "must_haves": [
                    "3+ years Python experience",
                    "Distributed systems knowledge",
                    "BS in Computer Science",
                ],
                "nice_to_haves": ["Kubernetes experience", "ML/AI background"],
                "responsibilities": [
                    "Design and implement scalable backend services",
                    "Collaborate with cross-functional teams",
                ],
                "keywords": ["Python", "Go", "Kubernetes", "GCP", "distributed systems"],
            }
        }
