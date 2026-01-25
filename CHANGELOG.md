# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-25

### Added
- **Core Features**
  - PDF resume ingestion with Gemini-powered extraction
  - Atomic unit extraction (bullets, skills, education, projects)
  - Job description parsing (URL or text input)
  - LLM-direct scoring of experience against job requirements
  - Resume compilation with provenance tracking
  - PDF export via RenderCV/LaTeX

- **Frontend**
  - Modern Next.js 14 app with App Router
  - Three-step wizard: Upload → Parse JD → Review
  - Vault page for viewing extracted atomic units
  - Responsive design with Tailwind CSS + shadcn/ui
  - Dark mode support

- **Backend**
  - FastAPI async API
  - MongoDB Atlas integration for document storage
  - Gemini API integration with rate limiting
  - CORS configuration for frontend deployment

- **DevOps**
  - GitHub Actions CI (lint, type check, build, tests)
  - GitHub Actions CD (DigitalOcean deployment)
  - Security scanning (gitleaks, pip-audit, npm audit)
  - Dependabot for automated dependency updates
  - Pre-commit hooks for code quality

- **Resume Sections Support**
  - Standard: Experience, Education, Projects, Skills
  - Extended: Involvement, Leadership, Volunteer, Awards
  - Additional: Certifications, Publications, Languages, Interests

### Security
- Environment variable validation at startup
- Secret scanning in CI pipeline
- No hardcoded credentials

## [0.1.0] - 2026-01-24

### Added
- Initial project setup
- Basic FastAPI backend structure
- Next.js frontend scaffold
- MongoDB connection setup
- Gemini API integration prototype
