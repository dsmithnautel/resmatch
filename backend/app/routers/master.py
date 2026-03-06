"""Master Resume management endpoints."""

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.db.mongodb import get_database
from app.models import AtomicUnit, MasterResumeResponse, MasterVersion
from app.services.ingestion import ingest_multiple_pdfs, ingest_pdf

router = APIRouter()

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/ingest", response_model=MasterResumeResponse)
async def ingest_master_resume(file: UploadFile = File(...)):
    """
    Upload and process a master resume PDF.

    Extracts atomic units using Gemini and stores in MongoDB.
    Returns the extracted units for user review/editing.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")

    try:
        result = await ingest_pdf(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e

    return result


@router.post("/ingest-multiple", response_model=MasterResumeResponse)
async def ingest_multiple_resumes(files: list[UploadFile] = File(...)):
    """
    Upload multiple resume PDFs and merge them into a single master resume.

    Extracts atomic units from each file, deduplicates across all files
    (removing exact and near-duplicate entries), and stores the merged
    result as one master version.
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least one PDF file is required")

    pdf_pairs: list[tuple[bytes, str]] = []
    for f in files:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"Only PDF files are accepted (got: {f.filename})",
            )
        content = await f.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large: {f.filename}. Maximum size is 10MB.",
            )
        pdf_pairs.append((content, f.filename))

    try:
        result = await ingest_multiple_pdfs(pdf_pairs)
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e

    return result


@router.get("/{version_id}", response_model=MasterResumeResponse)
async def get_master_resume(version_id: str):
    """Get a master resume by version ID."""
    try:
        db = await get_database()

        version = await db.master_versions.find_one({"master_version_id": version_id})
        if not version:
            raise HTTPException(status_code=404, detail=f"Master version {version_id} not found")

        units_cursor = db.atomic_units.find({"version": version_id})
        units = [AtomicUnit(**doc) async for doc in units_cursor]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e

    counts: dict[str, int] = {}
    for unit in units:
        section = unit.section.value
        counts[section] = counts.get(section, 0) + 1

    warnings: list[str] = []

    return MasterResumeResponse(
        master_version_id=version_id, atomic_units=units, counts=counts, warnings=warnings
    )


@router.put("/{version_id}/units/{unit_id}")
async def update_atomic_unit(version_id: str, unit_id: str, unit: AtomicUnit):
    """Update an atomic unit (for user corrections)."""
    try:
        db = await get_database()

        existing = await db.atomic_units.find_one({"id": unit_id, "version": version_id})

        if not existing:
            raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")

        result = await db.atomic_units.update_one(
            {"id": unit_id, "version": version_id}, {"$set": unit.model_dump()}
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update unit")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e

    return {"status": "updated", "unit_id": unit_id}


@router.delete("/{version_id}/units/{unit_id}")
async def delete_atomic_unit(version_id: str, unit_id: str):
    """Delete an atomic unit."""
    try:
        db = await get_database()

        result = await db.atomic_units.delete_one({"id": unit_id, "version": version_id})

        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e

    return {"status": "deleted", "unit_id": unit_id}


@router.get("/", response_model=list[MasterVersion])
async def list_master_versions():
    """List all master resume versions."""
    try:
        db = await get_database()

        cursor = db.master_versions.find().sort("created_at", -1)
        versions = [MasterVersion(**doc) async for doc in cursor]
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e

    return versions
