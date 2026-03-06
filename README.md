# ResMatch

[![CI](https://github.com/dsmithnautel/resmatch/actions/workflows/ci.yml/badge.svg)](https://github.com/dsmithnautel/resmatch/actions/workflows/ci.yml)
[![CD](https://github.com/dsmithnautel/resmatch/actions/workflows/cd.yml/badge.svg)](https://github.com/dsmithnautel/resmatch/actions/workflows/cd.yml)
[![GitHub release](https://img.shields.io/github/v/release/dsmithnautel/resmatch)](https://github.com/dsmithnautel/resmatch/releases)

> Truth-first resume tailoring engine - compiles verified experience into job-targeted resumes with zero hallucinations.

**[Live Demo](https://restailor.vercel.app)** | **[Demo Video](https://youtu.be/YOUR_VIDEO_ID)** *(replace with actual link)*

Built for **SwampHacks XI** | Using **Gemini API** (MLH), **MongoDB Atlas** (MLH), **DigitalOcean** (MLH)

## Overview

ResMatch treats your resume like source code and job descriptions like build targets. It:

1. **Extracts** every bullet point from your master resume as verified "atomic units"
2. **Parses** job descriptions to identify requirements and keywords
3. **Scores** your experience against the JD using LLM-direct scoring
4. **Compiles** the best-matching bullets into a one-page, tailored PDF

**Key guarantee**: Every output bullet traces back to your original resume. Nothing is fabricated.

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js <!-- NEXTJS_VERSION_START -->16.1.6<!-- NEXTJS_VERSION_END --> | React app with App Router |
| Styling | Tailwind CSS <!-- TAILWIND_VERSION_START -->3.4.1<!-- TAILWIND_VERSION_END --> + shadcn/ui | Modern UI components |
| Backend | FastAPI <!-- FASTAPI_VERSION_START -->0.109.0<!-- FASTAPI_VERSION_END --> | Python async API |
| AI | Google Gemini API | Extraction + LLM scoring |
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
| GET | `/master/{version_id}` | Get atomic units |
| POST | `/job/parse` | Parse job description |
| POST | `/resume/compile` | Compile tailored resume |
| GET | `/resume/{compile_id}` | Get compile results |
| GET | `/resume/{compile_id}/pdf` | Download PDF |

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

### 3. LLM Scoring

Each atomic unit is scored against the JD:
- Score (0-10) indicating relevance
- Matched requirements
- Reasoning for the score

We use **LLM-direct scoring** (not vector search) because:
- ~30-50 atomic units fit easily in context
- Gemini can reason holistically about fit
- Simpler architecture, no embedding overhead

### 4. Optimization

Greedy selection under constraints:
- Max bullets per section
- One-page character budget
- Diversity (max 2 bullets per role)
- Must-have coverage prioritization

### 5. Rendering

Selected bullets are compiled via RenderCV into a professional PDF. Full provenance JSON is generated.

## Hackathon Challenges

- **Best Use of Gemini API** - Core extraction + scoring
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
│   │   ├── error.tsx
│   │   ├── global-error.tsx
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

18 directories, 54 files
```

<!-- PROJECT_STRUCTURE_END -->

## Frequently Asked Questions (FAQ)

### How does ResMatch ensure zero hallucinations?

We only use content that already exists in your uploaded resume. Every bullet point in your tailored resume can be traced back to an exact line in your original document. We never generate, invent, or embellish any experience.

### What does 'source tracking' mean?

For every bullet we include in your tailored resume, you can click 'View source' to see exactly where it came from in your original resume, including the page number and line number. This proves nothing was invented.

### Do I need to create an account?

No. ResMatch works without sign-up. Just upload your resume, paste a job description, and export your tailored PDF immediately.

### What file formats are supported?

We currently support PDF uploads. The exported tailored resume is also delivered as a PDF optimized for ATS systems.

### Is ResMatch really free?

Yes. ResMatch is free and open source. You can view the source code on GitHub and even self-host if you prefer.

## Team

Built with love for SwampHacks XI 💙🧡🐊

## License

MIT
