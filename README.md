# ResMatch

[![CI](https://github.com/dsmithnautel/resmatch/actions/workflows/ci.yml/badge.svg)](https://github.com/dsmithnautel/resmatch/actions/workflows/ci.yml)
[![CD](https://github.com/dsmithnautel/resmatch/actions/workflows/cd.yml/badge.svg)](https://github.com/dsmithnautel/resmatch/actions/workflows/cd.yml)
[![GitHub release](https://img.shields.io/github/v/release/dsmithnautel/resmatch)](https://github.com/dsmithnautel/resmatch/releases)

> Truth-first resume tailoring engine - compiles verified experience into job-targeted resumes with zero hallucinations.

## Overview

ResMatch treats your resume like source code and job descriptions like build targets. It:

1. **Extracts** every bullet point from your master resume as verified "atomic units"
2. **Parses** job descriptions to identify requirements and keywords
3. **Tailors** each bullet by rewriting it to highlight relevance to the JD — without fabricating anything
4. **Compiles** all tailored bullets into a professional PDF with full provenance

**Key guarantee**: Every output bullet traces back to your original resume. Nothing is fabricated.

## Features

- **PDF Resume Ingestion** — Upload your master resume and extract atomic units
- **Job Description Parsing** — Parse a JD from URL or pasted text
- **LLM-Direct Tailoring** — Rewrite bullets to highlight JD relevance using Gemini, without fabricating anything
- **Resume Compilation** — Compile a tailored resume with full provenance tracking
- **PDF Export** — Generate a professional, ATS-ready PDF via LaTeX

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js <!-- NEXTJS_VERSION_START -->16.1.6<!-- NEXTJS_VERSION_END --> | React app with App Router |
| Styling | Tailwind CSS <!-- TAILWIND_VERSION_START -->4.2.1<!-- TAILWIND_VERSION_END --> + shadcn/ui | Modern UI components |
| Backend | FastAPI <!-- FASTAPI_VERSION_START -->0.109.0<!-- FASTAPI_VERSION_END --> | Python async API |
| AI | Google Gemini API | Extraction + LLM tailoring |
| Database | MongoDB Atlas | Document storage |
| Hosting | DigitalOcean | Backend deployment |
| PDF | RenderCV | LaTeX resume generation |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB Atlas account (free tier works)
- Google Gemini API key

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
```

Visit `http://localhost:3000` to use the app.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/master/ingest` | Upload master resume PDF |
| GET | `/master/{version_id}` | Get atomic units for a version |
| PUT | `/master/{version_id}/units/{unit_id}` | Update an atomic unit |
| DELETE | `/master/{version_id}/units/{unit_id}` | Delete an atomic unit |
| POST | `/job/parse` | Parse job description from URL or text |
| GET | `/job/{jd_id}` | Get a previously parsed JD |
| POST | `/resume/compile` | Compile tailored resume |
| GET | `/resume/{compile_id}` | Get compile results |
| GET | `/resume/{compile_id}/pdf` | Download PDF |
| GET | `/resume/{compile_id}/provenance` | Get full provenance JSON |

## How It Works

### 1. Ingestion

Upload your master resume PDF. Gemini extracts every bullet as an "atomic unit" with:
- Text (verbatim from resume)
- Section (experience, projects, education, skills)
- Organization and role
- Skills tags
- Source evidence for provenance

### 2. Job Parsing

Paste a job description URL or text. Gemini extracts:
- Must-have requirements
- Nice-to-have qualifications
- Key responsibilities
- Technical keywords

### 3. LLM Tailoring

Each atomic unit is sent to Gemini along with the parsed JD. Gemini rewrites each bullet to:
- Use active voice and strong action verbs
- Incorporate JD keywords naturally where honest
- Improve clarity and impact without changing core facts
- Preserve the original meaning — nothing is fabricated

Each rewritten bullet also receives a relevance score (0–10) for transparency.

We use **LLM-direct tailoring** (not vector search) because:
- ~30-50 atomic units fit easily in context
- Gemini can reason holistically about fit and rewrite intelligently
- Simpler architecture, no embedding overhead

### 4. Rendering

All tailored bullets are compiled via RenderCV into a professional PDF. Full provenance JSON is generated alongside it.

## Hackathon Challenges

- **Best Use of Gemini API** - Core extraction + LLM tailoring
- **Best Use of MongoDB Atlas** - Document storage
- **Best Use of DigitalOcean** - Backend hosting
- **GitHub "Ship It"** - PRs, issues, releases
- **Human-Centered Design** - Wizard UX, provenance panel
- **Best User Design** - Review UI, bullet toggles

## Project Structure

<!-- PROJECT_STRUCTURE_START -->
```text
.
├── CHANGELOG.md
├── README.md
├── backend
│   ├── Dockerfile
│   ├── app
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── db
│   │   ├── main.py
│   │   ├── models
│   │   ├── routers
│   │   ├── services
│   │   └── templates
│   ├── coverage.xml
│   ├── find_id.py
│   ├── pyproject.toml
│   ├── request_body.json
│   ├── request_parse.json
│   ├── requirements.txt
│   ├── test_db_connection.py
│   ├── test_llm_render.py
│   ├── test_mongo.py
│   ├── test_renderer.py
│   └── tests
│       ├── __init__.py
│       ├── conftest.py
│       ├── test_api.py
│       ├── test_config.py
│       ├── test_gemini.py
│       ├── test_health.py
│       ├── test_ingestion.py
│       ├── test_jd_parser.py
│       ├── test_models.py
│       ├── test_optimizer.py
│       ├── test_rendercv_mapper.py
│       ├── test_renderer.py
│       └── test_scoring.py
├── debug_tokens.py
├── frontend
│   ├── app
│   │   ├── apple-icon.png
│   │   ├── compile
│   │   ├── globals.css
│   │   ├── icon.png
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── review
│   │   └── vault
│   ├── components
│   │   ├── file-upload.tsx
│   │   ├── flow-diagram.tsx
│   │   ├── navigation.tsx
│   │   ├── stepper-tabs.tsx
│   │   └── ui
│   ├── lib
│   │   ├── api.ts
│   │   └── utils.ts
│   ├── next-env.d.ts
│   ├── next.config.js
│   ├── package-lock.json
│   ├── package.json
│   ├── postcss.config.js
│   ├── public
│   │   ├── apple-touch-icon.png
│   │   └── favicon.png
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vercel.json
└── package-lock.json

18 directories, 52 files
```

<!-- PROJECT_STRUCTURE_END -->

## Frequently Asked Questions (FAQ)

### How is ResMatch different from ChatGPT resume help?

ChatGPT and similar tools can fabricate experience or embellish your background. ResMatch enforces a strict truth constraint—we only use content that already exists in your uploaded resume. Every bullet point in your tailored resume can be traced back to an exact line in your original document. We never generate, invent, or embellish any experience. No hallucinations and no invented metrics.

### What does 'source tracking' mean?

For every bullet we include in your tailored resume, you can click 'View source' to see exactly where it came from in your original resume, including the page number and line number. This proves nothing was invented.

### Do I need to create an account?

No. ResMatch works without sign-up. Just upload your resume, paste a job description, and export your tailored PDF immediately.

### What file formats are supported?

We currently support PDF uploads. The exported tailored resume is also delivered as a PDF optimized for ATS systems.

### Is ResMatch really free?

Yes. ResMatch is free and open source. You can view the source code on GitHub and even self-host if you prefer.

### How long does it take to generate a tailored resume?

Typically under a minute. The process involves extracting your resume content, parsing the job description, scoring and tailoring each bullet, and compiling the final PDF.

### Can I edit the tailored resume before exporting?

Yes. After the tailoring step, you can review all matched bullets, toggle individual items on or off, and adjust relevance before generating your final PDF.

### What is a relevance score?

Each bullet receives a score from 0–10 indicating how well it matches the job requirements. Higher scores mean stronger alignment with the JD keywords and responsibilities.

### Will the tailored resume pass ATS systems?

Yes. The exported PDF uses a clean, single-column LaTeX template designed to be parsed correctly by Applicant Tracking Systems. No fancy graphics or multi-column layouts that confuse ATS parsers.

### Can I tailor the same resume for multiple jobs?

Absolutely. Upload your master resume once, then paste different job descriptions to generate a uniquely tailored version for each role.

### What happens to my resume data?

Your resume is processed to extract bullet points and stored temporarily for the session. We do not sell or share your data. For maximum privacy, you can self-host the application.

### What if my resume has multiple pages?

ResMatch handles multi-page PDFs. All content is extracted and parsed regardless of length, though we recommend keeping resumes concise (1 page) for best results.

## Team

Built with love for SwampHacks XI 💙🧡🐊

## License

MIT
