/**
 * API client for ResMatch backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  code: string;
  status: number;
  retryAfter: number | null;

  constructor(message: string, code: string, status: number, retryAfter: number | null = null) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
    this.retryAfter = retryAfter;
  }
}

const ERROR_MESSAGES: Record<string, string> = {
  rate_limit: "The AI service is busy. Please wait a moment and try again.",
  db_unavailable: "We're having trouble reaching our servers. Please try again.",
  validation_error: "Please check your input and try again.",
  internal_error: "An unexpected error occurred. Please try again.",
};

async function handleErrorResponse(response: Response): Promise<never> {
  let code = "internal_error";
  let detail = "An unexpected error occurred";
  let retryAfter: number | null = null;

  try {
    const body = await response.json();
    code = body.error || code;
    detail = ERROR_MESSAGES[code] || body.detail || detail;
    retryAfter = body.retry_after || null;
  } catch {
    // response wasn't JSON
  }

  throw new ApiError(detail, code, response.status, retryAfter);
}

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

export interface MergeStats {
  files_processed: number;
  total_units_before_dedup: number;
  duplicates_removed: number;
  final_unit_count: number;
  per_file_counts: Record<string, number>;
}

export interface MasterResumeResponse {
  master_version_id: string;
  atomic_units: AtomicUnit[];
  counts: Record<string, number>;
  warnings: string[];
  merge_stats?: MergeStats;
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
  section: string;
  org?: string;
  role?: string;
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
  selected_units: ScoredUnit[];
  coverage: {
    must_haves_matched: number;
    must_haves_total: number;
    coverage_score: number;
  };
  provenance: Provenance[];
  pdf_url?: string;
}

/**
 * API Functions
 */

export async function uploadResume(file: File): Promise<MasterResumeResponse> {
  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch(`${API_BASE}/master/ingest`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      await handleErrorResponse(response);
    }

    return response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      "Unable to connect to the server. Check your internet connection.",
      "network_error",
      0
    );
  }
}

export async function uploadMultipleResumes(
  files: File[]
): Promise<MasterResumeResponse> {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  try {
    const response = await fetch(`${API_BASE}/master/ingest-multiple`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      await handleErrorResponse(response);
    }

    return response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      "Unable to connect to the server. Check your internet connection.",
      "network_error",
      0
    );
  }
}

export async function getMasterResume(versionId: string): Promise<MasterResumeResponse> {
  try {
    const response = await fetch(`${API_BASE}/master/${versionId}`);

    if (!response.ok) {
      await handleErrorResponse(response);
    }

    return response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      "Unable to connect to the server. Check your internet connection.",
      "network_error",
      0
    );
  }
}

export async function parseJobDescription(
  url?: string,
  text?: string
): Promise<ParsedJD> {
  try {
    const response = await fetch(`${API_BASE}/job/parse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, text }),
    });

    if (!response.ok) {
      await handleErrorResponse(response);
    }

    return response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      "Unable to connect to the server. Check your internet connection.",
      "network_error",
      0
    );
  }
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
  try {
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
      await handleErrorResponse(response);
    }

    return response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      "Unable to connect to the server. Check your internet connection.",
      "network_error",
      0
    );
  }
}

export async function getCompileResult(compileId: string): Promise<CompileResponse> {
  try {
    const response = await fetch(`${API_BASE}/resume/${compileId}`);

    if (!response.ok) {
      await handleErrorResponse(response);
    }

    return response.json();
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      "Unable to connect to the server. Check your internet connection.",
      "network_error",
      0
    );
  }
}

export function getPdfUrl(compileId: string): string {
  return `${API_BASE}/resume/${compileId}/pdf`;
}
