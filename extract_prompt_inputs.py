
import json
import sys
import os
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.models import ParsedJD
from app.services.scoring import TAILORING_PROMPT

def extract_prompt():
    # 1. Load Request Data (Job Description)
    try:
        with open('backend/request_body.json', 'r') as f:
            request_data = json.load(f)
            jd_text = request_data.get('jd_text', '')
    except FileNotFoundError:
        jd_text = "Sample JD Text"

    # Mock ParsedJD
    parsed_jd = ParsedJD(
        jd_id="test_jd_123",
        role_title="Software Engineer Intern", 
        company="Adobe",
        must_haves=[
            "Currently enrolled full time in Computer Science",
            "Proficiency in Java, Python, or Go",
            "Familiar with software development lifecycle"
        ],
        responsibilities=[
            "Develop efficient, reliable, testable services code",
            "Work closely with engineers on the team",
            "Participate in development process"
        ],
        keywords=["Python", "Go", "Java", "Web Development", "API"],
        source_url=None,
        raw_text=jd_text
    )

    # 2. Hardcoded Sample Bullets (since file was empty)
    bullets_for_prompt = [
        {
            "id": "exp_atlassian_007",
            "text": "Developed an API within a Spring Boot microservice that automatically reorganizes Confluence page hierarchies via semantic analysis, reducing manual reorganization time by 50%.",
            "section": "experience",
            "org": "Atlassian",
            "role": "Software Engineering Intern"
        },
        {
            "id": "exp_atlassian_008",
            "text": "Experimented with integrating an AWS SageMaker semantic reranker model and later led the development of a cross-service LLM workflow, attaining an organizational accuracy of 98% with the LLM workflow.",
            "section": "experience",
            "org": "Atlassian",
            "role": "Software Engineering Intern"
        },
        {
            "id": "pro_devsight_018",
            "text": "Engineered a developer performance analytics platform using FastAPI and Python, aggregating data via GitHub and Atlassian MCP servers (Jira, Confluence) to deliver comprehensive real-time performance scores.",
            "section": "projects",
            "org": "DevSight",
            "role": None
        }
    ]

    # 3. Format the Prompt
    prompt = TAILORING_PROMPT.format(
        company=parsed_jd.company,
        role_title=parsed_jd.role_title,
        must_haves="\n".join(f"- {req}" for req in parsed_jd.must_haves),
        responsibilities="\n".join(f"- {resp}" for resp in parsed_jd.responsibilities),
        keywords=", ".join(parsed_jd.keywords),
        bullets_json=json.dumps(bullets_for_prompt, indent=2),
    )

    print(prompt)

if __name__ == "__main__":
    extract_prompt()
