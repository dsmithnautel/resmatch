# Resume.compile()

> Truth-first resume tailoring engine - compiles verified experience into job-targeted resumes with zero hallucinations.

Built for **SwampHacks XI** | Using **Gemini API** (MLH), **MongoDB Atlas** (MLH), **DigitalOcean** (MLH)

## Overview

Resume.compile() treats your resume like source code and job descriptions like build targets. It:

1. **Extracts** every bullet point from your master resume as verified "atomic units"
2. **Parses** job descriptions to identify requirements and keywords
3. **Scores** your experience against the JD using LLM-direct scoring
4. **Compiles** the best-matching bullets into a one-page, tailored PDF

**Key guarantee**: Every output bullet traces back to your original resume. Nothing is fabricated.

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 14 | React app with App Router |
| Styling | Tailwind CSS + shadcn/ui | Modern UI components |
| Backend | FastAPI | Python async API |
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

```
restailor/
├── frontend/          # Next.js 14 app
│   ├── app/           # Pages (vault, compile, review)
│   ├── components/    # UI components
│   └── lib/           # API client, utilities
├── backend/           # FastAPI server
│   ├── app/
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Business logic
│   │   ├── models/    # Pydantic schemas
│   │   └── db/        # MongoDB setup
│   └── requirements.txt
└── docs/              # PRD and planning
```

## Frequently Asked Questions (FAQ)

### How does Resume.compile() ensure zero hallucinations?

We only use content that already exists in your uploaded resume. Every bullet point in your tailored resume can be traced back to an exact line in your original document. We never generate, invent, or embellish any experience.

### What does 'source tracking' mean?

For every bullet we include in your tailored resume, you can click 'View source' to see exactly where it came from in your original resume, including the page number and line number. This proves nothing was invented.

### Is my resume data stored or shared?

Your resume is processed in-memory and not stored permanently. We do not share your data with third parties. You can read our full privacy policy for details.

### Do I need to create an account?

No. Resume.compile() works without sign-up. Just upload your resume, paste a job description, and export your tailored PDF immediately.

### What file formats are supported?

We currently support PDF uploads. The exported tailored resume is also delivered as a PDF optimized for ATS systems.

### Is Resume.compile() really free?

Yes. Resume.compile() is free and open source. You can view the source code on GitHub and even self-host if you prefer.

## Team

Built with love for SwampHacks XI 💙🧡🐊

## License

MIT
