"""Master Resume management endpoints."""

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.db.mongodb import get_database
from app.models import AtomicUnit, MasterResumeResponse, MasterVersion
from app.services.ingestion import ingest_pdf

router = APIRouter()


@router.get("/{version_id}/pdf")
async def get_original_pdf(version_id: str):
    """Serve the originally uploaded PDF for this master version."""
    import os

    pdf_path = os.path.abspath(f"uploads/{version_id}.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Original PDF not found")

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"original_{version_id}.pdf")


@router.post("/ingest", response_model=MasterResumeResponse)
async def ingest_master_resume(file: UploadFile = File(...)):
    """
    Upload and process a master resume PDF.

    Extracts atomic units using Gemini and stores in MongoDB.
    Returns the extracted units for user review/editing.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    # Read file content
    content = await file.read()

    # Process with ingestion service
    result = await ingest_pdf(content, file.filename)

    return result


@router.get("/{version_id}", response_model=MasterResumeResponse)
async def get_master_resume(version_id: str):
    """Get a master resume by version ID."""
    db = await get_database()

    # Get version metadata
    version = await db.master_versions.find_one({"master_version_id": version_id})
    if not version:
        raise HTTPException(status_code=404, detail=f"Master version {version_id} not found")

    # Get atomic units
    units_cursor = db.atomic_units.find({"version": version_id})
    units = [AtomicUnit(**doc) async for doc in units_cursor]

    # Count by section
    counts: dict[str, int] = {}
    for unit in units:
        section = unit.section.value
        counts[section] = counts.get(section, 0) + 1

    # Initialize warnings as an empty list of strings
    warnings: list[str] = []

    return MasterResumeResponse(
        master_version_id=version_id, atomic_units=units, counts=counts, warnings=warnings
    )


@router.put("/{version_id}/units/{unit_id}")
async def update_atomic_unit(version_id: str, unit_id: str, unit: AtomicUnit):
    """Update an atomic unit (for user corrections)."""
    db = await get_database()

    # Verify the unit exists
    existing = await db.atomic_units.find_one({"id": unit_id, "version": version_id})

    if not existing:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")

    # Update the unit
    result = await db.atomic_units.update_one(
        {"id": unit_id, "version": version_id}, {"$set": unit.model_dump()}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update unit")

    return {"status": "updated", "unit_id": unit_id}


@router.delete("/{version_id}/units/{unit_id}")
async def delete_atomic_unit(version_id: str, unit_id: str):
    """Delete an atomic unit."""
    db = await get_database()

    result = await db.atomic_units.delete_one({"id": unit_id, "version": version_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Unit {unit_id} not found")

    return {"status": "deleted", "unit_id": unit_id}


@router.get("/", response_model=list[MasterVersion])
async def list_master_versions():
    """List all master resume versions."""
    db = await get_database()

    cursor = db.master_versions.find().sort("created_at", -1)
    versions = [MasterVersion(**doc) async for doc in cursor]

    return versions
