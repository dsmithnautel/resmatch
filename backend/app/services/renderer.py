import json
import os
import re
import shutil
import subprocess

import yaml

from app.db.mongodb import get_database
from app.models import ScoredUnit
from app.services.gemini import generate_text
from app.services.prompts import generate_latex_prompt


async def render_resume(
    compile_id: str, selected_units: list[ScoredUnit], master_version_id: str
) -> str:
    """
    Render resume using LLM-generated LaTeX (Jake's Resume).

    1. Get header info from master resume
    2. Group atomic units by section/role
    3. Generate LaTeX using LLM
    4. Compile LaTeX to PDF
    5. Return path to generated PDF
    """
    # Get header info from database
    db = await get_database()

    # Fetch ALL header units
    header_cursor = db.atomic_units.find({"version": master_version_id, "type": "header"})
    header_units = [doc async for doc in header_cursor]
    header_info = extract_header_info(header_units)

    # Prepare data for LLM
    resume_data = prepare_resume_data(header_info, selected_units)
    resume_json = json.dumps(resume_data, indent=2)

    # Generate LaTeX Prompt
    prompt = generate_latex_prompt(resume_json)

    # Call Gemini to get LaTeX
    try:
        latex_content = await generate_text(prompt)
        # Clean up code blocks if present
        if latex_content.startswith("```latex"):
            latex_content = latex_content.replace("```latex", "", 1)
        elif latex_content.startswith("```tex"):
            latex_content = latex_content.replace("```tex", "", 1)
        
        if latex_content.startswith("```"):
             latex_content = latex_content.replace("```", "", 1)
             
        if latex_content.endswith("```"):
            latex_content = latex_content[:-3]
            
        latex_content = latex_content.strip()
        
    except Exception as e:
        raise RuntimeError(f"Failed to generate LaTeX from LLM: {e}")

    # Create output directory
    output_dir = os.path.abspath(f"output/{compile_id}")
    os.makedirs(output_dir, exist_ok=True)

    # Save LaTeX file
    tex_path = os.path.join(output_dir, "cv.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_content)

    # Compile with pdflatex
    # We run pdflatex twice to ensure formatting (though once might be enough for this simple template)
    try:
        # Check if pdflatex is available
        if shutil.which("pdflatex") is None:
             # Fallback logic could go here, but for now we expect a LaTeX environment
             pass
        
        cmd = ["pdflatex", "-interaction=nonstopmode", "-output-directory", output_dir, tex_path]

        with open(os.path.join(output_dir, "debug_renderer.log"), "w") as log:
            log.write(f"Starting pdflatex in {output_dir}\n")
            log.write(f"TeX Path: {tex_path}\n")

        # Run 1
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Run 2 (optional, but good practice for layout)
        # subprocess.run(cmd, capture_output=True, text=True, check=True)

        print(f"pdflatex Output: {result.stdout}")
        with open(os.path.join(output_dir, "debug_renderer.log"), "a") as log:
            log.write("pdflatex Success:\n")
            log.write(result.stdout)
            log.write("\n")

    except subprocess.CalledProcessError as e:
        print(f"pdflatex Failed: {e.stderr}")
        with open(os.path.join(output_dir, "debug_renderer.log"), "a") as log:
            log.write("pdflatex FAILED:\n")
            log.write(e.stdout) # pdflatex often puts errors in stdout
            log.write(e.stderr)
            log.write("\n")
        raise RuntimeError(f"LaTeX compilation failed. see {output_dir}/debug_renderer.log. Error: {e.stdout}")
    except FileNotFoundError:
        raise RuntimeError("pdflatex not found. Please install a LaTeX distribution (e.g., TeX Live, MacTeX, MiKTeX).")

    # Find the generated PDF
    # pdflatex should generate cv.pdf in output_dir
    generated_pdf = os.path.join(output_dir, "cv.pdf")
    target_pdf = os.path.join(output_dir, "resume.pdf")

    if os.path.exists(generated_pdf):
        shutil.move(generated_pdf, target_pdf)
        return target_pdf
    else:
        raise FileNotFoundError(f"PDF not generated. Check logs in {output_dir}")


def prepare_resume_data(header_info: dict, units: list[ScoredUnit]) -> dict:
    """
    Organize flat list of atomic units into a structured dictionary.
    """
    data = {"header": header_info, "sections": {}}

    # Group by section
    for unit in units:
        section = unit.section
        # Lowercase section for consistency
        section_key = section.lower() if section else "other"
        
        if section_key not in data["sections"]:
            data["sections"][section_key] = []
        
        # We need to group bullets under their org/role/dates tuple
        # This is a heuristic grouping
        
        # Check if we can add to the last entry
        added = False
        if data["sections"][section_key]:
            last_entry = data["sections"][section_key][-1]
            if (
                last_entry.get("org") == unit.org
                and last_entry.get("role") == unit.role
                # Relax date check or verify if strict equality needed
            ):
                last_entry["bullets"].append(unit.text)
                added = True
        
        if not added:
            # Create new entry
            entry = {
                "org": unit.org,
                "role": unit.role,
                "dates": unit.dates,  # Keep as dict or string
                "bullets": [unit.text]
            }
            data["sections"][section_key].append(entry)
            
    # Clean up dates format if needed (atomic unit dates can be dicts or None)
    return data


def extract_header_info(header_units: list[dict]) -> dict:
    """
    Extract name, email, phone, LinkedIn, GitHub from header units.
    Prioritizes structured 'tags' from LLM, then falls back to regex on text.
    """
    if not header_units:
        return {}
        
    info = {
        "name": "Your Name",  # Default if not found
        "email": "",
        "phone": "",
        "linkedin": "",
        "github": "",
    }

    # 1. Try extracted metadata from tags (New Ingestion)
    full_text_parts = []
    
    for unit in header_units:
        # Accumulate text for fallback
        if unit.get("text"):
            full_text_parts.append(unit["text"])
            # If prompt followed, first unit text is Name
            if info["name"] == "Your Name":
                info["name"] = unit["text"]

        # Check tags
        tags = unit.get("tags") or {}
        if isinstance(tags, dict):
            if tags.get("email"): info["email"] = tags["email"]
            if tags.get("phone"): info["phone"] = tags["phone"]
            if tags.get("linkedin"): info["linkedin"] = tags["linkedin"]
            if tags.get("github"): info["github"] = tags["github"]
            
    # 2. Regex Fallback (Old Ingestion or LLM miss)
    full_text = "\n".join(full_text_parts)
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]
    
    # Extract email if missing
    if not info["email"]:
        email_pattern = r"[\w\.-]+@[\w\.-]+\.\w+"
        for line in lines:
            if match := re.search(email_pattern, line):
                info["email"] = match.group(0)
                break
                
    # Extract phone if missing
    if not info["phone"]:
        phone_pattern = r"\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4}"
        for line in lines:
            if match := re.search(phone_pattern, line):
                info["phone"] = match.group(0).strip()
                break
                
    # Extract LinkedIn if missing
    if not info["linkedin"]:
        for line in lines:
            if "linkedin.com" in line.lower():
                if match := re.search(r"https?://[^\s]+", line):
                    info["linkedin"] = match.group(0)
                else:
                    clean = line.replace("|", "").strip()
                    for part in clean.split():
                        if "linkedin.com" in part:
                            info["linkedin"] = f"https://{part}" if not part.startswith("http") else part
                            break
                break

    # Extract GitHub if missing
    if not info["github"]:
        for line in lines:
            if "github.com" in line.lower():
                if match := re.search(r"https?://[^\s]+", line):
                    info["github"] = match.group(0)
                else:
                    clean = line.replace("|", "").strip()
                    for part in clean.split():
                        if "github.com" in part:
                            info["github"] = f"https://{part}" if not part.startswith("http") else part
                            break
                break

    return info
