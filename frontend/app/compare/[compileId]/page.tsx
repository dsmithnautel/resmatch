"use client";

import "./compare.css";

import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";
import {
    getCompileResult,
    getPreviewPdf,
    compileLatex,
    patchLatex,
    getOriginalPdfUrl,
    rescoreBullets,
    ScoredUnit,
    CompileResponse,
    PreviewHeader,
    PreviewUnit,
} from "@/lib/api";

// Configure pdf.js worker (v4+ uses .mjs extension)
if (typeof window !== "undefined") {
    pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;
}

/* ───────── Helpers ───────── */

function formatDates(dates?: { start?: string; end?: string } | null): string {
    if (!dates) return "";
    const months = [
        "", "Jan.", "Feb.", "Mar.", "Apr.", "May", "June",
        "July", "Aug.", "Sep.", "Oct.", "Nov.", "Dec.",
    ];
    const fmt = (d: string | undefined) => {
        if (!d) return "";
        const parts = d.split("-");
        if (parts.length === 2) {
            const m = parseInt(parts[1], 10);
            return `${months[m] || parts[1]} ${parts[0]}`;
        }
        return d;
    };
    const start = fmt(dates.start);
    const end = dates.end ? fmt(dates.end) : "Present";
    if (start && end) return `${start} – ${end}`;
    return start || end;
}

/** Convert ScoredUnit[] to PreviewUnit[] for the API */
function toPreviewUnits(units: ScoredUnit[], field: "text" | "original_text"): PreviewUnit[] {
    return units.map((u) => ({
        text: field === "original_text" ? (u.original_text || u.text) : u.text,
        section: u.section,
        org: u.org || null,
        role: u.role || null,
        dates: u.dates || null,
    }));
}

/** Group units by (section, org, role) for the editable text pane */
interface EditBullet {
    unitId: string;
    text: string;
    score: number;
    reasoning: string;
    stale: boolean;
}

interface EditGroup {
    section: string;
    org: string;
    role: string;
    dates?: { start?: string; end?: string } | null;
    bullets: EditBullet[];
}

function groupForEditing(
    units: ScoredUnit[],
    field: "text" | "original_text",
    dirtyIds: Set<string>,
): EditGroup[] {
    const groups: EditGroup[] = [];

    for (const u of units) {
        const text = field === "original_text" ? (u.original_text || u.text) : u.text;
        const org = u.org || "";
        const role = u.role || "";

        const bullet: EditBullet = {
            unitId: u.unit_id,
            text,
            score: u.llm_score,
            reasoning: u.reasoning,
            stale: dirtyIds.has(u.unit_id),
        };

        if (u.section === "projects" && u.org && !groups.find(g =>
            g.section === "projects" && g.org === u.org
        )) {
            groups.push({
                section: u.section,
                org,
                role,
                dates: u.dates,
                bullets: [],
            });
            continue;
        }

        const lastGroup = groups.length > 0 ? groups[groups.length - 1] : null;
        if (
            lastGroup &&
            lastGroup.section === u.section &&
            lastGroup.org === org &&
            lastGroup.role === role
        ) {
            lastGroup.bullets.push(bullet);
        } else {
            groups.push({
                section: u.section,
                org,
                role,
                dates: u.dates,
                bullets: [bullet],
            });
        }
    }

    return groups;
}

/* ───────── PDF Preview Component ───────── */

function PdfPreview({
    pdfBlob,
    loading,
    label,
}: {
    pdfBlob: string | null;
    loading: boolean;
    label: string;
}) {
    const [numPages, setNumPages] = useState(1);
    const [currentPage, setCurrentPage] = useState(1);

    return (
        <div className="pdf-preview-container">
            <div className="pdf-preview-label">{label}</div>
            <div className="pdf-preview-wrapper">
                {loading && (
                    <div className="pdf-preview-loading">
                        <div className="compare-spinner" />
                        <span>Compiling...</span>
                    </div>
                )}
                {pdfBlob && (
                    <Document
                        file={pdfBlob}
                        onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                        loading={null}
                    >
                        <Page
                            pageNumber={currentPage}
                            width={612} /* 8.5in * 72dpi */
                            renderTextLayer={false}
                            renderAnnotationLayer={false}
                        />
                    </Document>
                )}
                {!pdfBlob && !loading && (
                    <div className="pdf-preview-empty">
                        Edit the text to generate a preview
                    </div>
                )}
            </div>
            {numPages > 1 && (
                <div className="pdf-page-nav">
                    {Array.from({ length: numPages }, (_, i) => i + 1).map((p) => (
                        <button
                            key={p}
                            onClick={() => setCurrentPage(p)}
                            className={`pdf-page-btn ${p === currentPage ? "pdf-page-btn-active" : ""}`}
                        >
                            {p}
                        </button>
                    ))}
                    <span className="pdf-page-label">Page {currentPage} of {numPages}</span>
                </div>
            )}
        </div>
    );
}

/* ───────── Score Badge ───────── */

function ScoreBadge({ score, stale }: { score: number; stale: boolean }) {
    const colorClass =
        score >= 8 ? "bullet-score-high" :
        score >= 6 ? "bullet-score-mid" :
        "bullet-score-low";

    return (
        <span className={`bullet-score ${colorClass} ${stale ? "bullet-stale" : ""}`}>
            {score.toFixed(1)}
        </span>
    );
}

/* ───────── Editable Text Pane ───────── */

function EditablePane({
    groups,
    onBulletChange,
    label,
    onRescore,
    rescoring,
    dirtyCount,
    rescoreDisabled,
}: {
    groups: EditGroup[];
    onBulletChange: (unitId: string, newText: string) => void;
    label: string;
    onRescore?: () => void;
    rescoring?: boolean;
    dirtyCount?: number;
    rescoreDisabled?: boolean;
}) {
    const [expandedId, setExpandedId] = useState<string | null>(null);

    const sectionOrder = ["education", "experience", "projects", "leadership", "skills"];
    const sectionNames: Record<string, string> = {
        education: "Education",
        experience: "Experience",
        projects: "Projects",
        leadership: "Leadership",
        skills: "Technical Skills",
    };

    const bySection = new Map<string, EditGroup[]>();
    for (const g of groups) {
        const sec = g.section;
        if (!bySection.has(sec)) bySection.set(sec, []);
        bySection.get(sec)!.push(g);
    }

    return (
        <div className="edit-pane">
            <div className="edit-pane-header">
                <div className="edit-pane-label">{label}</div>
                {onRescore && (
                    <button
                        className="rescore-btn"
                        onClick={onRescore}
                        disabled={rescoreDisabled || rescoring || (dirtyCount ?? 0) === 0}
                    >
                        {rescoring
                            ? "Rescoring..."
                            : `Recalculate Relevance Scores${dirtyCount ? ` (${dirtyCount})` : ""}`}
                    </button>
                )}
            </div>
            <div className="edit-pane-content">
                {sectionOrder.map((sec) => {
                    const sectionGroups = bySection.get(sec);
                    if (!sectionGroups || sectionGroups.length === 0) return null;

                    return (
                        <div key={sec} className="edit-section">
                            <h3 className="edit-section-title">{sectionNames[sec] || sec}</h3>
                            {sectionGroups.map((group, gi) => (
                                <div key={gi} className="edit-group">
                                    {(group.org || group.role) && (
                                        <div className="edit-group-header">
                                            {group.role && (
                                                <span className="edit-group-role">{group.role}</span>
                                            )}
                                            {group.org && (
                                                <span className="edit-group-org">{group.org}</span>
                                            )}
                                            {group.dates && (
                                                <span className="edit-group-dates">
                                                    {formatDates(group.dates)}
                                                </span>
                                            )}
                                        </div>
                                    )}
                                    <ul className="edit-bullets">
                                        {group.bullets.map((b) => (
                                            <li key={b.unitId} className="edit-bullet">
                                                <textarea
                                                    className="edit-textarea"
                                                    value={b.text}
                                                    onChange={(e) =>
                                                        onBulletChange(b.unitId, e.target.value)
                                                    }
                                                    rows={2}
                                                />
                                                <div className="bullet-meta">
                                                    <ScoreBadge score={b.score} stale={b.stale} />
                                                    {b.reasoning && (
                                                        <button
                                                            className="bullet-reasoning-toggle"
                                                            onClick={() =>
                                                                setExpandedId(
                                                                    expandedId === b.unitId ? null : b.unitId
                                                                )
                                                            }
                                                        >
                                                            {expandedId === b.unitId ? "Hide" : "Why?"}
                                                        </button>
                                                    )}
                                                    {b.stale && (
                                                        <span className="bullet-stale-label">edited</span>
                                                    )}
                                                </div>
                                                {expandedId === b.unitId && b.reasoning && (
                                                    <div className="bullet-reasoning">
                                                        {b.reasoning}
                                                    </div>
                                                )}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            ))}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

/* ───────── Main Page ───────── */

export default function ComparePage() {
    const params = useParams();
    const router = useRouter();
    const compileId = params.compileId as string;

    const [compileResult, setCompileResult] = useState<CompileResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Editable unit state
    const [tailoredUnits, setTailoredUnits] = useState<ScoredUnit[]>([]);
    const [dirtyIds, setDirtyIds] = useState<Set<string>>(new Set());
    const [rescoring, setRescoring] = useState(false);

    // Original tailored text per unit (for computing LaTeX patches)
    const originalTextsRef = useRef<Map<string, string>>(new Map());
    // Current working LaTeX source (patched in-place on edits)
    const currentLatexRef = useRef<string | null>(null);

    // PDF preview state
    const [originalPdfUrl, setOriginalPdfUrl] = useState<string | null>(null);
    const [tailoredPdfUrl, setTailoredPdfUrl] = useState<string | null>(null);
    const [originalLoading, setOriginalLoading] = useState(false);
    const [tailoredLoading, setTailoredLoading] = useState(false);

    // Header info
    const [header, setHeader] = useState<PreviewHeader>({
        name: "Your Name",
        email: "",
        phone: "",
        linkedin: "",
        github: "",
    });

    // Debounce timer
    const debounceRef = useRef<NodeJS.Timeout | null>(null);

    // Fetch compile result, original PDF, and tailored PDF
    useEffect(() => {
        async function load() {
            try {
                const result = await getCompileResult(compileId);
                setCompileResult(result);
                setTailoredUnits(result.selected_units);

                // Store original tailored text for each unit (used for LaTeX patching)
                const origMap = new Map<string, string>();
                for (const u of result.selected_units) {
                    origMap.set(u.unit_id, u.text);
                }
                originalTextsRef.current = origMap;
                currentLatexRef.current = result.tailored_latex || null;

                // Fetch original PDF as blob (avoids cross-origin issues with react-pdf worker)
                if (result.master_version_id) {
                    setOriginalLoading(true);
                    try {
                        const pdfRes = await fetch(getOriginalPdfUrl(result.master_version_id));
                        if (pdfRes.ok) {
                            const blob = await pdfRes.blob();
                            setOriginalPdfUrl(URL.createObjectURL(blob));
                        }
                    } catch (err) {
                        console.error("Failed to fetch original PDF:", err);
                    } finally {
                        setOriginalLoading(false);
                    }
                }

                // Tailored resume: compile stored LaTeX, or fall back to LLM preview
                if (result.tailored_latex) {
                    setTailoredLoading(true);
                    try {
                        const blob = await compileLatex(result.tailored_latex);
                        setTailoredPdfUrl(URL.createObjectURL(blob));
                    } catch (err) {
                        console.error("LaTeX compilation failed, falling back to preview:", err);
                        try {
                            const previewUnits = toPreviewUnits(result.selected_units, "text");
                            const blob = await getPreviewPdf(header, previewUnits);
                            setTailoredPdfUrl(URL.createObjectURL(blob));
                        } catch (err2) {
                            console.error("Preview fallback also failed:", err2);
                        }
                    } finally {
                        setTailoredLoading(false);
                    }
                } else {
                    setTailoredLoading(true);
                    try {
                        const previewUnits = toPreviewUnits(result.selected_units, "text");
                        const blob = await getPreviewPdf(header, previewUnits);
                        setTailoredPdfUrl(URL.createObjectURL(blob));
                    } catch (err) {
                        console.error("Preview generation failed:", err);
                    } finally {
                        setTailoredLoading(false);
                    }
                }
            } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to load");
            } finally {
                setLoading(false);
            }
        }
        load();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [compileId]);

    // Compile stored LaTeX directly via Tectonic
    const compileFromLatex = useCallback(
        async (
            latex: string,
            setUrl: (url: string | null) => void,
            setLoading: (loading: boolean) => void
        ) => {
            setLoading(true);
            try {
                const blob = await compileLatex(latex);
                const url = URL.createObjectURL(blob);
                setUrl(url);
            } catch (err) {
                console.error("LaTeX compilation failed:", err);
            } finally {
                setLoading(false);
            }
        },
        []
    );

    // Generate PDF from units
    const generatePdf = useCallback(
        async (
            units: ScoredUnit[],
            field: "text" | "original_text",
            setUrl: (url: string | null) => void,
            setLoading: (loading: boolean) => void
        ) => {
            setLoading(true);
            try {
                const previewUnits = toPreviewUnits(units, field);
                const blob = await getPreviewPdf(header, previewUnits);
                const url = URL.createObjectURL(blob);
                setUrl(url);
            } catch (err) {
                console.error("PDF generation failed:", err);
            } finally {
                setLoading(false);
            }
        },
        [header]
    );

    // Handle bullet change with debounce — uses fast LaTeX patching when available
    const handleTailoredBulletChange = useCallback(
        (unitId: string, newText: string) => {
            setDirtyIds((prev) => new Set(prev).add(unitId));
            setTailoredUnits((prev) => {
                const updated = prev.map((u) =>
                    u.unit_id === unitId ? { ...u, text: newText } : u
                );

                if (debounceRef.current) clearTimeout(debounceRef.current);
                debounceRef.current = setTimeout(async () => {
                    const latex = currentLatexRef.current;
                    if (latex) {
                        // Fast path: patch LaTeX string + Tectonic recompile (~130ms)
                        const patches: { old_text: string; new_text: string }[] = [];
                        for (const u of updated) {
                            const orig = originalTextsRef.current.get(u.unit_id);
                            if (orig && orig !== u.text) {
                                patches.push({ old_text: orig, new_text: u.text });
                            }
                        }
                        if (patches.length > 0) {
                            setTailoredLoading(true);
                            try {
                                const blob = await patchLatex(latex, patches);
                                setTailoredPdfUrl(URL.createObjectURL(blob));
                            } catch (err) {
                                console.error("Patch-latex failed, falling back to preview:", err);
                                generatePdf(updated, "text", setTailoredPdfUrl, setTailoredLoading);
                                return;
                            } finally {
                                setTailoredLoading(false);
                            }
                        }
                    } else {
                        // Slow path: LLM-based preview (no stored LaTeX)
                        generatePdf(updated, "text", setTailoredPdfUrl, setTailoredLoading);
                    }
                }, 1500);

                return updated;
            });
        },
        [generatePdf]
    );

    // Rescore all edited bullets via Gemini
    const handleRescore = useCallback(async () => {
        if (!compileResult?.jd_id || dirtyIds.size === 0) return;

        setRescoring(true);
        try {
            const bulletsToScore = tailoredUnits
                .filter((u) => dirtyIds.has(u.unit_id))
                .map((u) => ({ id: u.unit_id, text: u.text }));

            const results = await rescoreBullets(compileResult.jd_id, bulletsToScore);

            const scoreMap = new Map(results.map((r) => [r.id, r]));
            setTailoredUnits((prev) =>
                prev.map((u) => {
                    const res = scoreMap.get(u.unit_id);
                    if (res) {
                        return { ...u, llm_score: res.score, reasoning: res.reasoning };
                    }
                    return u;
                })
            );
            setDirtyIds(new Set());
        } catch (err) {
            console.error("Rescoring failed:", err);
        } finally {
            setRescoring(false);
        }
    }, [compileResult?.jd_id, dirtyIds, tailoredUnits]);

    if (loading) {
        return (
            <div className="compare-loading">
                <div className="compare-spinner" />
                <p>Loading comparison view...</p>
            </div>
        );
    }

    if (error || !compileResult) {
        return (
            <div className="compare-error">
                <h2>Error</h2>
                <p>{error || "Failed to load compile result"}</p>
                <button onClick={() => router.back()}>Go Back</button>
            </div>
        );
    }

    const editGroups = groupForEditing(tailoredUnits, "text", dirtyIds);

    return (
        <div className="compare-page">
            {/* Top bar */}
            <div className="compare-topbar">
                <Link href="/compile" className="compare-back">
                    ← Back to Compile
                </Link>
                <div className="compare-actions">
                    <button
                        className="compare-btn compare-btn-primary"
                        onClick={() => {
                            if (tailoredPdfUrl) {
                                const a = document.createElement("a");
                                a.href = tailoredPdfUrl;
                                a.download = `resume_${compileId}.pdf`;
                                a.click();
                            }
                        }}
                    >
                        Download Tailored PDF
                    </button>
                </div>
            </div>

            {/* Main layout: edit pane + two PDF previews */}
            <div className="compare-layout">
                <EditablePane
                    groups={editGroups}
                    onBulletChange={handleTailoredBulletChange}
                    label="Edit Tailored Resume"
                    onRescore={handleRescore}
                    rescoring={rescoring}
                    dirtyCount={dirtyIds.size}
                    rescoreDisabled={!compileResult?.jd_id}
                />

                <div className="compare-previews">
                    <PdfPreview
                        pdfBlob={originalPdfUrl}
                        loading={originalLoading}
                        label="Original Resume"
                    />
                    <PdfPreview
                        pdfBlob={tailoredPdfUrl}
                        loading={tailoredLoading}
                        label="Tailored Resume"
                    />
                </div>
            </div>
        </div>
    );
}
