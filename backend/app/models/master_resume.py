"""Master Resume version tracking models."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.atomic_unit import AtomicUnit


class MasterVersion(BaseModel):
    """
    Tracks a specific version of the master resume.
    All compiled resumes reference a master_version_id for reproducibility.
    """

    master_version_id: str = Field(..., description="Unique version ID")
    source_type: str = Field(..., description="pdf, json, or manual")
    source_hash: str | None = None  # SHA256 of source file
    atomic_unit_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: str | None = None

    class Config:
        json_schema_extra = {
            "example": {
                "master_version_id": "master_v4",
                "source_type": "pdf",
                "source_hash": "sha256:abc123...",
                "atomic_unit_count": 47,
                "notes": "Updated with Amazon internship",
            }
        }


class MasterResumeResponse(BaseModel):
    """Response from master resume ingestion."""

    master_version_id: str
    atomic_units: list[AtomicUnit]
    counts: dict[str, int] = Field(default_factory=dict, description="Count of units by section")
    warnings: list[str] = Field(default_factory=list, description="Any parsing warnings")


class MasterResumeListResponse(BaseModel):
    """List of master resume versions."""

    versions: list[MasterVersion]
    total: int
