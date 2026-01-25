"""Atomic Unit model - the fundamental building block of a resume."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AtomicUnitType(str, Enum):
    """Type of atomic unit."""
    BULLET = "bullet"           # A bullet point (experience, involvement, etc.)
    SKILL_GROUP = "skill_group" # A group of skills
    EDUCATION = "education"     # An education entry
    PROJECT = "project"         # A project entry
    HEADER = "header"           # Header info (name, contact)
    AWARD = "award"             # An award or honor
    CERTIFICATION = "certification"  # A certification
    PUBLICATION = "publication" # A publication
    LANGUAGE = "language"       # A language entry
    INTEREST = "interest"       # An interest/hobby


class SectionType(str, Enum):
    """Resume section type."""
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    EDUCATION = "education"
    SKILLS = "skills"
    HEADER = "header"
    # Additional sections (issue #28)
    INVOLVEMENT = "involvement"     # Activities, clubs, organizations
    LEADERSHIP = "leadership"       # Leadership roles
    VOLUNTEER = "volunteer"         # Volunteer experience
    AWARDS = "awards"               # Awards and honors
    CERTIFICATIONS = "certifications"  # Professional certifications
    PUBLICATIONS = "publications"   # Papers, articles, books
    LANGUAGES = "languages"         # Language proficiencies
    INTERESTS = "interests"         # Hobbies and interests
    # Catch-all for unrecognized sections
    OTHER = "other"                 # Any section not matching above


class DateRange(BaseModel):
    """Date range for experience/education."""
    start: Optional[str] = None  # YYYY-MM format
    end: Optional[str] = None    # YYYY-MM or "present"


class Tags(BaseModel):
    """Tags for filtering and matching."""
    skills: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    seniority: Optional[str] = None


class Evidence(BaseModel):
    """Source evidence for provenance tracking."""
    source: str  # Original file name
    page: Optional[int] = None
    line_hint: Optional[str] = None


class AtomicUnit(BaseModel):
    """
    An atomic unit is the smallest verifiable piece of resume content.
    It can be a bullet point, skill group, education entry, or project.
    
    The system guarantees that all output traces back to an atomic unit ID.
    """
    id: str = Field(..., description="Unique identifier (e.g., exp_amazon_sde19_b03)")
    type: AtomicUnitType
    section: SectionType
    org: Optional[str] = None  # Company, school, or organization
    role: Optional[str] = None  # Job title or degree
    dates: Optional[DateRange] = None
    text: str = Field(..., description="Exact text from resume - never modified")
    tags: Tags = Field(default_factory=Tags)
    evidence: Optional[Evidence] = None
    version: str = Field(..., description="Master resume version ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "exp_amazon_sde19_b03",
                "type": "bullet",
                "section": "experience",
                "org": "Amazon",
                "role": "SDE Intern",
                "dates": {"start": "2025-06", "end": "2025-08"},
                "text": "Built real-time monitoring dashboard reducing incident response time by 40% using AWS CloudWatch and Lambda",
                "tags": {
                    "skills": ["AWS Lambda", "CloudWatch", "Python"],
                    "domains": ["backend", "observability"],
                    "seniority": "intern"
                },
                "evidence": {
                    "source": "master_resume_v4.pdf",
                    "page": 1,
                    "line_hint": "Experience -> Amazon -> bullet 3"
                },
                "version": "master_v4"
            }
        }
