"""Resume compilation endpoints."""

import json
import time
import traceback
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import BaseModel

from app.db.mongodb import get_database
from app.models import CompileRequest, CompileResponse, CoverageStats, ParsedJD, Provenance
from app.services.renderer import render_resume
from app.services.scoring import tailor_units_against_jd

router = APIRouter()


# ── Preview endpoint models ──

class PreviewHeader(BaseModel):
    name: str = "Your Name"
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""


class PreviewUnit(BaseModel):
    text: str
    section: str
    org: str | None = None
    role: str | None = None
    dates: dict | None = None


class PreviewRequest(BaseModel):
    header: PreviewHeader
    units: list[PreviewUnit]


@router.post("/preview")
async def preview_resume(request: PreviewRequest):
    """
    Generate a PDF preview from structured resume data.

    Uses LLM-based LaTeX generation (Gemini + prompts.py) + Tectonic compilation.
    """
    from app.services.renderer import render_from_units

    header = request.header.model_dump()
    units = [u.model_dump() for u in request.units]

    try:
        pdf_bytes, _latex = await render_from_units(header, units)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Cache-Control": "no-cache"},
    )


class PatchLatexPatch(BaseModel):
    old_text: str
    new_text: str


class PatchLatexRequest(BaseModel):
    latex: str
    patches: list[PatchLatexPatch]


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters in user text."""
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
        ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


@router.post("/patch-latex")
async def patch_latex(request: PatchLatexRequest):
    """
    Patch bullet text in stored LaTeX and recompile to PDF.

    No LLM — just string replacement + Tectonic (~130ms).
    """
    from app.services.tectonic import compile_pdf

    latex = request.latex
    for patch in request.patches:
        escaped_new = _escape_latex(patch.new_text)
        escaped_old = _escape_latex(patch.old_text)
        latex = latex.replace(escaped_old, escaped_new)

    try:
        pdf_bytes = await compile_pdf(latex)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LaTeX compilation failed: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Cache-Control": "no-cache"},
    )


class CompileLatexRequest(BaseModel):
    latex: str


@router.post("/compile-latex")
async def compile_latex(request: CompileLatexRequest):
    """
    Compile raw LaTeX source to PDF using Tectonic.

    Takes the stored LaTeX (from the compile result) and returns a PDF.
    """
    from app.services.tectonic import compile_pdf

    try:
        pdf_bytes = await compile_pdf(request.latex)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LaTeX compilation failed: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Cache-Control": "no-cache"},
    )

class RescoreBullet(BaseModel):
    id: str
    text: str


class RescoreRequest(BaseModel):
    jd_id: str
    bullets: list[RescoreBullet]


class RescoreResult(BaseModel):
    id: str
    score: float
    reasoning: str


@router.post("/rescore", response_model=list[RescoreResult])
async def rescore_bullets(request: RescoreRequest):
    """
    Score bullets against a JD without rewriting.

    Lighter than tailoring — returns only relevance scores and explanations.
    """
    from app.services.gemini import generate_json

    db = await get_database()

    jd_doc = await db.parsed_jds.find_one({"jd_id": request.jd_id})
    if not jd_doc:
        raise HTTPException(status_code=404, detail=f"JD {request.jd_id} not found")
    parsed_jd = ParsedJD(**jd_doc)

    bullets_json = [{"id": b.id, "text": b.text} for b in request.bullets]

    prompt = f"""Score each resume bullet for relevance to this job. Do NOT rewrite — only score.

JOB: {parsed_jd.role_title} at {parsed_jd.company}
REQUIREMENTS: {', '.join(parsed_jd.must_haves)}
KEYWORDS: {', '.join(parsed_jd.keywords)}

BULLETS:
{json.dumps(bullets_json)}

Return JSON array: [{{"id":"...","score":0.0,"reasoning":"Brief explanation of score"}}]"""

    try:
        raw = await generate_json(prompt)
        return [
            RescoreResult(
                id=item.get("id", ""),
                score=float(item.get("score", 5.0)),
                reasoning=item.get("reasoning", ""),
            )
            for item in raw
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rescoring failed: {e}")


@router.post("/compile", response_model=CompileResponse)
async def compile_resume(request: CompileRequest):
    """
    Compile a tailored resume from master resume + job description.

    Pipeline:
    1. Fetch all atomic units for master_version_id
    2. Get or parse job description
    3. Tailor each unit to JD using Gemini LLM (1 call — rewording)
    4. Generate PDF deterministically (no LLM)
    5. Return results with full provenance
    """
    db = await get_database()

    units_cursor = db.atomic_units.find({"version": request.master_version_id})
    units = [doc async for doc in units_cursor]

    if not units:
        raise HTTPException(
            status_code=404,
            detail=f"No atomic units found for master version {request.master_version_id}",
        )

    # 2. Get job description
    if request.jd_id:
        jd_doc = await db.parsed_jds.find_one({"jd_id": request.jd_id})
        if not jd_doc:
            raise HTTPException(status_code=404, detail=f"JD {request.jd_id} not found")
        parsed_jd = ParsedJD(**jd_doc)
    elif request.jd_text:
        from app.services.jd_parser import parse_job_description

        parsed_jd = await parse_job_description(text=request.jd_text)
    else:
        raise HTTPException(status_code=400, detail="Either jd_id or jd_text must be provided")

    # 3. Tailor units (single Gemini call)
    try:
        start_tailor = time.time()
        selected_units = await tailor_units_against_jd(units, parsed_jd)
        print(f"Tailoring took {time.time() - start_tailor:.2f}s")
    except Exception as e:
        with open("debug_tailor.log", "w") as f:
            f.write(f"Tailoring Failed: {e}\n")
            traceback.print_exc(file=f)
        raise

    # 4. Coverage stats
    coverage = CoverageStats(
        must_haves_matched=len(parsed_jd.must_haves),
        must_haves_total=len(parsed_jd.must_haves),
        coverage_score=1.0,
    )

    # 5. Compile ID and provenance
    compile_id = f"cmp_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"

    provenance = [
        Provenance(
            compile_id=compile_id,
            output_line_id=f"resume.{unit.section}.{i}",
            atomic_unit_id=unit.unit_id,
            matched_requirements=unit.matched_requirements,
            llm_score=unit.llm_score,
            llm_reasoning=unit.reasoning,
        )
        for i, unit in enumerate(selected_units)
    ]

    # 6. Render PDF deterministically (no LLM call)
    pdf_url = None
    tailored_latex = None
    try:
        start_render = time.time()
        _pdf_path, tailored_latex = await render_resume(
            compile_id, selected_units, request.master_version_id
        )
        print(f"Rendering took {time.time() - start_render:.2f}s")
        pdf_url = f"/resume/{compile_id}/pdf"
    except Exception as e:
        print(f"PDF generation failed: {e}")
        with open("debug_error.log", "w") as f:
            f.write(f"Error: {e}\n")
            traceback.print_exc(file=f)

    result = CompileResponse(
        compile_id=compile_id,
        master_version_id=request.master_version_id,
        jd_id=parsed_jd.jd_id,
        selected_units=selected_units,
        coverage=coverage,
        provenance=provenance,
        pdf_url=pdf_url,
        tailored_latex=tailored_latex,
    )

    await db.compiles.insert_one(result.model_dump())

    return result


@router.get("/{compile_id}")
async def get_compile_result(compile_id: str):
    """Get a compilation result by ID."""
    db = await get_database()

    doc = await db.compiles.find_one({"compile_id": compile_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Compile {compile_id} not found")

    return CompileResponse(**doc)


@router.get("/{compile_id}/pdf")
async def get_compile_pdf(compile_id: str):
    """Download the compiled PDF."""
    import os

    # Look for the PDF file
    pdf_path = os.path.abspath(f"output/{compile_id}/resume.pdf")

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found. Try recompiling.")

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"resume_{compile_id}.pdf")


@router.get("/{compile_id}/provenance")
async def get_provenance(compile_id: str):
    """Get the provenance JSON for a compilation."""
    db = await get_database()

    doc = await db.compiles.find_one({"compile_id": compile_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Compile {compile_id} not found")

    return JSONResponse(content={"provenance": doc.get("provenance", [])})


@router.get("/{compile_id}/narrate")
async def narrate_resume(compile_id: str):
    """
    Generate voice narration of the compiled resume (stretch goal).

    Requires ELEVENLABS_API_KEY to be configured.
    """
    from fastapi.responses import StreamingResponse

    from app.services.voice import format_resume_for_narration, generate_resume_narration

    db = await get_database()
    doc = await db.compiles.find_one({"compile_id": compile_id})

    if not doc:
        raise HTTPException(status_code=404, detail=f"Compile {compile_id} not found")

    # Format resume for narration
    selected_units = doc.get("selected_units", [])
    narration_text = format_resume_for_narration(selected_units)

    # Generate audio
    audio_bytes: bytes | None = await generate_resume_narration(narration_text)

    if audio_bytes is None:
        raise HTTPException(
            status_code=503,
            detail="Voice narration not available. ElevenLabs API key not configured.",
        )

    return StreamingResponse(
        iter([audio_bytes]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f"attachment; filename=resume_{compile_id}.mp3"},
    )
