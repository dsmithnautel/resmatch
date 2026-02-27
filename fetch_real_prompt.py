
import asyncio
import json
import sys
import os
from pprint import pprint

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.db.mongodb import get_database, close_database
from app.models import ParsedJD
from app.services.scoring import TAILORING_PROMPT

from dotenv import load_dotenv
load_dotenv('backend/.env')

async def fetch_and_print_prompt():
    # 1. Load Request Data (for master_version_id and JD text)
    with open('backend/request_body.json', 'r') as f:
        request_data = json.load(f)
        master_version_id = request_data.get('master_version_id')
        jd_text = request_data.get('jd_text', '')

    print(f"DEBUG: Fetching units for version: {master_version_id}")

    # 2. Connect to Database (using regular app logic)
    db = await get_database()

    # 3. Fetch Atomic Units
    cursor = db.atomic_units.find({"version": master_version_id})
    units = await cursor.to_list(length=2000)

    print(f"DEBUG: Found {len(units)} units in total.")

    if not units:
        print("ERROR: No units found! Check if master_version_id is correct in request_body.json or if DB is populated.")
        await close_database()
        return

    # Filter for tailorable units
    tailorable = [u for u in units if u.get("type") in ["bullet", "project"]]
    print(f"DEBUG: Found {len(tailorable)} tailorable bullets.")

    # Prepare bullets for the prompt
    bullets_for_prompt = []
    for u in tailorable:
        bullets_for_prompt.append(
            {
                "id": u.get("id"),
                "text": u.get("text"),
                "section": u.get("section"),
                "org": u.get("org"),
                "role": u.get("role"),
            }
        )

    # 4. Parse JD (REAL execution using Gemini)
    from app.services.jd_parser import parse_job_description
    print("DEBUG: Parsing JD with Gemini (this may take a few seconds)...")
    
    # We use the text from the request body
    try:
        parsed_jd = await parse_job_description(text=jd_text)
        print(f"DEBUG: JD Parsed successfully. Role: {parsed_jd.role_title}, Company: {parsed_jd.company}")
    except Exception as e:
        print(f"ERROR: JD Parsing failed: {e}")
        await close_database()
        return

    # 5. Format the Prompt
    prompt = TAILORING_PROMPT.format(
        company=parsed_jd.company,
        role_title=parsed_jd.role_title,
        must_haves="\n".join(f"- {req}" for req in parsed_jd.must_haves),
        responsibilities="\n".join(f"- {resp}" for resp in parsed_jd.responsibilities),
        keywords=", ".join(parsed_jd.keywords),
        bullets_json=json.dumps(bullets_for_prompt, indent=2),
    )

    print("\n" + "="*80)
    print("FULL TAILORING PROMPT (Copy below):")
    print("="*80 + "\n")
    print(prompt)
    print("\n" + "="*80)

    await close_database()

if __name__ == "__main__":
    asyncio.run(fetch_and_print_prompt())
