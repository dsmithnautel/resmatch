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

    result = await parse_job_description(url=request.url, text=request.text)

    # Store in database
    db = await get_database()
    await db.parsed_jds.insert_one(result.model_dump())

    return result


@router.get("/{jd_id}", response_model=ParsedJD)
async def get_parsed_jd(jd_id: str):
    """Get a previously parsed job description."""
    db = await get_database()

    doc = await db.parsed_jds.find_one({"jd_id": jd_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"JD {jd_id} not found")

    return ParsedJD(**doc)


@router.get("/", response_model=list[ParsedJD])
async def list_parsed_jds(limit: int = 20):
    """List recently parsed job descriptions."""
    db = await get_database()

    cursor = db.parsed_jds.find().sort("created_at", -1).limit(limit)
    jds = [ParsedJD(**doc) async for doc in cursor]

    return jds
