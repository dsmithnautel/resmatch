/**
 * API client for ResMatch backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Types
 */
export interface AtomicUnit {
  id: string;
  type: "bullet" | "skill_group" | "education" | "project" | "header";
  section: "experience" | "projects" | "education" | "skills" | "header";
  org?: string;
  role?: string;
  dates?: { start?: string; end?: string };
  text: string;
  tags: { skills: string[]; domains: string[]; seniority?: string };
  evidence?: { source: string; page?: number; line_hint?: string };
  version: string;
}

export interface MasterResumeResponse {
  master_version_id: string;
  atomic_units: AtomicUnit[];
  counts: Record<string, number>;
  warnings: string[];
}

export interface ParsedJD {
  jd_id: string;
  role_title: string;
  company: string;
  must_haves: string[];
  nice_to_haves: string[];
  responsibilities: string[];
  keywords: string[];
  source_url?: string;
}

export interface ScoredUnit {
  unit_id: string;
  text: string;
  original_text?: string;
  section: string;
  org?: string;
  role?: string;
  dates?: { start?: string; end?: string };
  llm_score: number;
  matched_requirements: string[];
  reasoning: string;
  selected: boolean;
}

export interface Provenance {
  compile_id: string;
  output_line_id: string;
  atomic_unit_id: string;
  matched_requirements: string[];
  llm_score: number;
  llm_reasoning: string;
}

export interface CompileResponse {
  compile_id: string;
  master_version_id?: string;
  jd_id?: string;
  selected_units: ScoredUnit[];
  coverage: {
    must_haves_matched: number;
    must_haves_total: number;
    coverage_score: number;
  };
  provenance: Provenance[];
  pdf_url?: string;
  tailored_latex?: string;
}

export interface RescoreResult {
  id: string;
  score: number;
  reasoning: string;
}

/**
 * API Functions
 */

export async function uploadResume(file: File): Promise<MasterResumeResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/master/ingest`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to upload resume");
  }

  return response.json();
}

export async function getMasterResume(versionId: string): Promise<MasterResumeResponse> {
  const response = await fetch(`${API_BASE}/master/${versionId}`);

  if (!response.ok) {
    throw new Error("Failed to fetch master resume");
  }

  return response.json();
}

export async function parseJobDescription(
  url?: string,
  text?: string
): Promise<ParsedJD> {
  const response = await fetch(`${API_BASE}/job/parse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, text }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to parse job description");
  }

  return response.json();
}

export async function compileResume(
  masterVersionId: string,
  jdId?: string,
  jdText?: string,
  constraints?: {
    max_experience_bullets?: number;
    max_project_bullets?: number;
  }
): Promise<CompileResponse> {
  const response = await fetch(`${API_BASE}/resume/compile`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      master_version_id: masterVersionId,
      jd_id: jdId,
      jd_text: jdText,
      constraints,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to compile resume");
  }

  return response.json();
}

export async function getCompileResult(compileId: string): Promise<CompileResponse> {
  const response = await fetch(`${API_BASE}/resume/${compileId}`);

  if (!response.ok) {
    throw new Error("Failed to fetch compile result");
  }

  return response.json();
}

export function getPdfUrl(compileId: string): string {
  return `${API_BASE}/resume/${compileId}/pdf`;
}

export function getOriginalPdfUrl(masterVersionId: string): string {
  return `${API_BASE}/master/${masterVersionId}/pdf`;
}

export interface PreviewHeader {
  name: string;
  email: string;
  phone: string;
  linkedin: string;
  github: string;
}

export interface PreviewUnit {
  text: string;
  section: string;
  org?: string | null;
  role?: string | null;
  dates?: { start?: string; end?: string } | null;
}

export async function getPreviewPdf(
  header: PreviewHeader,
  units: PreviewUnit[]
): Promise<Blob> {
  const response = await fetch(`${API_BASE}/resume/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ header, units }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Preview failed: ${detail}`);
  }

  return response.blob();
}

export async function compileLatex(latex: string): Promise<Blob> {
  const response = await fetch(`${API_BASE}/resume/compile-latex`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ latex }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`LaTeX compilation failed: ${detail}`);
  }

  return response.blob();
}

export async function rescoreBullets(
  jdId: string,
  bullets: { id: string; text: string }[]
): Promise<RescoreResult[]> {
  const response = await fetch(`${API_BASE}/resume/rescore`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ jd_id: jdId, bullets }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to rescore bullets");
  }

  return response.json();
}
