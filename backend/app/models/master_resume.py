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
    source_type: str = Field(..., description="pdf, json, manual, or multi_pdf")
    source_hash: str | None = None  # SHA256 of source file (or combined hash for multi)
    source_files: list[str] = Field(default_factory=list, description="Original filenames")
    atomic_unit_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notes: str | None = None
    user_id: str | None = Field(default=None, description="For future account linking")

    class Config:
        json_schema_extra = {
            "example": {
                "master_version_id": "master_v4",
                "source_type": "multi_pdf",
                "source_hash": "sha256:abc123...",
                "source_files": ["resume_v1.pdf", "resume_v2.pdf"],
                "atomic_unit_count": 47,
                "notes": "Combined from 2 files",
                "user_id": None,
            }
        }


class MergeStats(BaseModel):
    """Statistics from merging multiple resume PDFs."""

    files_processed: int = 0
    total_units_before_dedup: int = 0
    duplicates_removed: int = 0
    final_unit_count: int = 0
    per_file_counts: dict[str, int] = Field(
        default_factory=dict, description="Units extracted per source file"
    )


class MasterResumeResponse(BaseModel):
    """Response from master resume ingestion."""

    master_version_id: str
    atomic_units: list[AtomicUnit]
    counts: dict[str, int] = Field(default_factory=dict, description="Count of units by section")
    warnings: list[str] = Field(default_factory=list, description="Any parsing warnings")
    merge_stats: MergeStats | None = Field(
        default=None, description="Present when multiple files were merged"
    )


class MasterResumeListResponse(BaseModel):
    """List of master resume versions."""

    versions: list[MasterVersion]
    total: int
