"""Resume compilation models."""

from datetime import datetime

from pydantic import BaseModel, Field


class CompileConstraints(BaseModel):
    """Constraints for resume compilation."""

    page_limit: int = Field(default=1, ge=1, le=3)
    max_experience_bullets: int = Field(default=6, ge=1, le=20)
    max_project_bullets: int = Field(default=4, ge=0, le=10)
    max_bullets_per_role: int = Field(default=2, ge=1, le=5)
    max_total_chars: int = Field(default=3500, ge=1000, le=10000)
    min_must_have_coverage: float = Field(default=0.7, ge=0, le=1)


class CompilePreferences(BaseModel):
    """User preferences for compilation."""

    emphasis_domains: list[str] = Field(default_factory=list)
    preferred_roles: list[str] = Field(default_factory=list)


class CompileRequest(BaseModel):
    """Request to compile a tailored resume."""

    master_version_id: str
    jd_id: str | None = None  # Use existing parsed JD
    jd_text: str | None = None  # Or provide raw JD text
    constraints: CompileConstraints = Field(default_factory=CompileConstraints)
    preferences: CompilePreferences = Field(default_factory=CompilePreferences)


class ScoredUnit(BaseModel):
    """An atomic unit with its LLM-generated score."""

    unit_id: str
    text: str
    original_text: str | None = None
    section: str
    org: str | None = None
    role: str | None = None
    dates: dict | None = None
    tags: dict | None = None
    llm_score: float = Field(..., ge=0, le=10)
    matched_requirements: list[str] = Field(default_factory=list)
    reasoning: str = ""
    selected: bool = False


class Provenance(BaseModel):
    """
    Provenance record for a single output line.
    Guarantees traceability from output to source.
    """

    compile_id: str
    output_line_id: str
    atomic_unit_id: str
    matched_requirements: list[str]
    llm_score: float
    llm_reasoning: str


class CoverageStats(BaseModel):
    """Coverage statistics for the compiled resume."""

    must_haves_matched: int
    must_haves_total: int
    coverage_score: float


class CompileResponse(BaseModel):
    """Response from resume compilation."""

    compile_id: str
    master_version_id: str = ""
    jd_id: str | None = None
    selected_units: list[ScoredUnit]
    coverage: CoverageStats
    provenance: list[Provenance]
    pdf_url: str | None = None
    tailored_latex: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
