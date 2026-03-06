"""Job Description parsing endpoints."""

from fastapi import APIRouter, HTTPException

from app.db.mongodb import get_database
from app.models import JDParseRequest, ParsedJD
from app.services.jd_parser import parse_job_description

router = APIRouter()


@router.post("/parse", response_model=ParsedJD)
async def parse_jd(request: JDParseRequest):
    """
    Parse a job description from URL or text.

    If URL is provided, scrapes the page first.
    Uses Gemini to extract structured requirements.
    """
    if not request.url and not request.text:
        raise HTTPException(status_code=400, detail="Either url or text must be provided")

    try:
        result = await parse_job_description(url=request.url, text=request.text)
    except ValueError as e:
        raise HTTPException(status_code=429, detail=str(e)) from e

    try:
        db = await get_database()
        await db.parsed_jds.insert_one(result.model_dump())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e

    return result


@router.get("/{jd_id}", response_model=ParsedJD)
async def get_parsed_jd(jd_id: str):
    """Get a previously parsed job description."""
    try:
        db = await get_database()

        doc = await db.parsed_jds.find_one({"jd_id": jd_id})
        if not doc:
            raise HTTPException(status_code=404, detail=f"JD {jd_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e

    return ParsedJD(**doc)


@router.get("/", response_model=list[ParsedJD])
async def list_parsed_jds(limit: int = 20):
    """List recently parsed job descriptions."""
    try:
        db = await get_database()

        cursor = db.parsed_jds.find().sort("created_at", -1).limit(limit)
        jds = [ParsedJD(**doc) async for doc in cursor]
    except Exception as e:
        raise HTTPException(status_code=503, detail="Database temporarily unavailable") from e

    return jds
