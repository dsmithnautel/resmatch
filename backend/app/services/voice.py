"""ElevenLabs voice service for resume narration (stretch goal)."""

from app.config import get_settings


async def generate_resume_narration(
    text: str,
    voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # Default voice (Rachel)
) -> bytes | None:
    """
    Generate voice narration of resume content using ElevenLabs.

    This is a stretch goal feature for the hackathon.

    Args:
        text: The resume text to narrate
        voice_id: ElevenLabs voice ID

    Returns:
        Audio bytes (MP3) or None if not configured
    """
    settings = get_settings()

    if not settings.elevenlabs_api_key:
        return None

    try:
        from elevenlabs import generate, set_api_key

        set_api_key(settings.elevenlabs_api_key)

        audio = generate(text=text, voice=voice_id, model="eleven_monolingual_v1")

        return audio

    except Exception as e:
        print(f"ElevenLabs error: {e}")
        return None


def format_resume_for_narration(selected_units: list) -> str:
    """
    Format selected resume units for natural speech.

    Converts bullet points into a narrative format suitable for
    text-to-speech.
    """
    sections = {}

    for unit in selected_units:
        section = unit.get("section", "experience")
        if section not in sections:
            sections[section] = []
        sections[section].append(unit)

    narration_parts = []

    # Experience section
    if "experience" in sections:
        narration_parts.append("Here's a summary of my professional experience:")
        for unit in sections["experience"]:
            org = unit.get("org", "")
            role = unit.get("role", "")
            text = unit.get("text", "")
            if org and role:
                narration_parts.append(f"At {org} as {role}: {text}")
            else:
                narration_parts.append(text)

    # Projects section
    if "projects" in sections:
        narration_parts.append("Some of my key projects include:")
        for unit in sections["projects"]:
            narration_parts.append(unit.get("text", ""))

    # Education section
    if "education" in sections:
        narration_parts.append("Regarding my education:")
        for unit in sections["education"]:
            narration_parts.append(unit.get("text", ""))

    return " ".join(narration_parts)
