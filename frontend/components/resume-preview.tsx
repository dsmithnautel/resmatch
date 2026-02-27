"use client";

import "./resume-preview.css";
import { useState, useRef, useEffect, useCallback } from "react";

/* ───────── Types ───────── */

export interface HeaderInfo {
    name: string;
    email: string;
    phone: string;
    linkedin: string;
    github: string;
}

export interface SectionEntry {
    unitId: string;
    org?: string;
    role?: string;
    dates?: { start?: string; end?: string } | string;
    bullets: { id: string; text: string }[];
    techs?: string;
}

export interface SkillGroup {
    category: string;
    skills: string;
}

export interface ResumePreviewProps {
    header: HeaderInfo;
    sections: {
        education?: SectionEntry[];
        experience?: SectionEntry[];
        projects?: SectionEntry[];
        leadership?: SectionEntry[];
        skills?: SkillGroup[];
    };
    editable?: boolean;
    onBulletChange?: (bulletId: string, newText: string) => void;
    label?: string;
    formatDates?: (dates?: { start?: string; end?: string } | string) => string;
}

/* ───────── Sub-components ───────── */

function ResumeHeader({ header }: { header: HeaderInfo }) {
    const contactParts = [
        header.phone,
        header.email ? (
            <a key="email" href={`mailto:${header.email}`} className="rp-link">
                {header.email}
            </a>
        ) : null,
        header.linkedin ? (
            <a key="li" href={header.linkedin} className="rp-link" target="_blank" rel="noopener noreferrer">
                {header.linkedin.replace(/^https?:\/\//, "")}
            </a>
        ) : null,
        header.github ? (
            <a key="gh" href={header.github} className="rp-link" target="_blank" rel="noopener noreferrer">
                {header.github.replace(/^https?:\/\//, "")}
            </a>
        ) : null,
    ].filter(Boolean);

    return (
        <div className="rp-header">
            <h1 className="rp-header-name">{header.name}</h1>
            <div className="rp-header-contact">
                {contactParts.map((part, i) => (
                    <span key={i}>
                        {i > 0 && <span className="rp-separator"> | </span>}
                        {part}
                    </span>
                ))}
            </div>
        </div>
    );
}

function SectionHeading({ title }: { title: string }) {
    return <h2 className="rp-section-heading">{title}</h2>;
}

/**
 * Experience/Leadership subheading — matches Jake's template:
 *   Row 1: **Role** (bold left)   |   Dates (right)
 *   Row 2:  _Org_ (italic left)
 */
function ExperienceSubheading({
    role,
    org,
    dates,
    fmtDates,
}: {
    role: string;
    org: string;
    dates?: { start?: string; end?: string } | string;
    fmtDates: (d?: { start?: string; end?: string } | string) => string;
}) {
    return (
        <div className="rp-subheading-group">
            <div className="rp-subheading-row">
                <span className="rp-subheading-bold">{role}</span>
                <span className="rp-subheading-right">{fmtDates(dates)}</span>
            </div>
            {org && (
                <div className="rp-subheading-row">
                    <span className="rp-subheading-italic">{org}</span>
                </div>
            )}
        </div>
    );
}

/**
 * Education subheading — matches Jake's template:
 *   Row 1: **School** (bold left)   |   Location (right)
 *   Row 2:  _Degree_ (italic left)  |   Dates (right)
 */
function EducationSubheading({
    org,
    role,
    dates,
    fmtDates,
}: {
    org: string;
    role: string;
    dates?: { start?: string; end?: string } | string;
    fmtDates: (d?: { start?: string; end?: string } | string) => string;
}) {
    return (
        <div className="rp-subheading-group">
            <div className="rp-subheading-row">
                <span className="rp-subheading-bold">{org}</span>
            </div>
            {role && (
                <div className="rp-subheading-row">
                    <span className="rp-subheading-italic">{role}</span>
                    <span className="rp-subheading-right rp-subheading-italic">{fmtDates(dates)}</span>
                </div>
            )}
        </div>
    );
}

function BulletItem({
    id,
    text,
    editable,
    onChange,
}: {
    id: string;
    text: string;
    editable: boolean;
    onChange?: (id: string, text: string) => void;
}) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = textareaRef.current.scrollHeight + "px";
        }
    }, [text]);

    if (!editable) {
        return <li className="rp-bullet-item">{text}</li>;
    }

    return (
        <li className="rp-bullet-item">
            <textarea
                ref={textareaRef}
                className="rp-bullet-textarea"
                value={text}
                onChange={(e) => onChange?.(id, e.target.value)}
                rows={1}
            />
        </li>
    );
}

function defaultFormatDates(dates?: { start?: string; end?: string } | string): string {
    if (!dates) return "";
    if (typeof dates === "string") return dates;
    const parts = [dates.start, dates.end].filter(Boolean);
    return parts.join(" – ");
}

/**
 * Renders a list of entries with experience-style subheadings (role bold, org italic)
 */
function ExperienceSection({
    entries,
    editable,
    onBulletChange,
    fmtDates,
}: {
    entries: SectionEntry[];
    editable: boolean;
    onBulletChange?: (id: string, text: string) => void;
    fmtDates: (d?: { start?: string; end?: string } | string) => string;
}) {
    return (
        <div className="rp-list">
            {entries.map((entry, i) => (
                <div key={i} className="rp-entry">
                    <ExperienceSubheading
                        role={entry.role || ""}
                        org={entry.org || ""}
                        dates={entry.dates}
                        fmtDates={fmtDates}
                    />
                    {entry.bullets.length > 0 && (
                        <ul className="rp-bullet-list">
                            {entry.bullets.map((b) => (
                                <BulletItem
                                    key={b.id}
                                    id={b.id}
                                    text={b.text}
                                    editable={editable}
                                    onChange={onBulletChange}
                                />
                            ))}
                        </ul>
                    )}
                </div>
            ))}
        </div>
    );
}

/* ───────── Main Component ───────── */

export function ResumePreview({
    header,
    sections,
    editable = false,
    onBulletChange,
    label,
    formatDates: fmtDatesProp,
}: ResumePreviewProps) {
    const pageRef = useRef<HTMLDivElement>(null);
    const [pageCount, setPageCount] = useState(1);
    const [currentPage, setCurrentPage] = useState(1);
    const fmtDates = fmtDatesProp || defaultFormatDates;

    const checkPageCount = useCallback(() => {
        if (pageRef.current) {
            const pageHeightPx = 11 * 96;
            const contentHeight = pageRef.current.scrollHeight;
            const pages = Math.max(1, Math.ceil(contentHeight / pageHeightPx));
            setPageCount(pages);
        }
    }, []);

    useEffect(() => {
        checkPageCount();
    });

    useEffect(() => {
        window.addEventListener("resize", checkPageCount);
        return () => window.removeEventListener("resize", checkPageCount);
    }, [checkPageCount]);

    return (
        <div className="rp-container">
            {label && <div className="rp-label">{label}</div>}

            <div className="rp-page-wrapper">
                <div
                    ref={pageRef}
                    className="rp-page"
                    style={{
                        transform: `translateY(-${(currentPage - 1) * 11}in)`,
                    }}
                >
                    <ResumeHeader header={header} />

                    {/* Education */}
                    {sections.education && sections.education.length > 0 && (
                        <>
                            <SectionHeading title="Education" />
                            <div className="rp-list">
                                {sections.education.map((entry, i) => (
                                    <div key={i} className="rp-edu-entry">
                                        {entry.org && (
                                            <EducationSubheading
                                                org={entry.org}
                                                role={entry.role || ""}
                                                dates={entry.dates}
                                                fmtDates={fmtDates}
                                            />
                                        )}
                                        {entry.bullets.length > 0 && (
                                            <ul className="rp-bullet-list">
                                                {entry.bullets.map((b) => (
                                                    <BulletItem
                                                        key={b.id}
                                                        id={b.id}
                                                        text={b.text}
                                                        editable={editable}
                                                        onChange={onBulletChange}
                                                    />
                                                ))}
                                            </ul>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </>
                    )}

                    {/* Experience */}
                    {sections.experience && sections.experience.length > 0 && (
                        <>
                            <SectionHeading title="Experience" />
                            <ExperienceSection
                                entries={sections.experience}
                                editable={editable}
                                onBulletChange={onBulletChange}
                                fmtDates={fmtDates}
                            />
                        </>
                    )}

                    {/* Projects */}
                    {sections.projects && sections.projects.length > 0 && (
                        <>
                            <SectionHeading title="Projects" />
                            <div className="rp-list">
                                {sections.projects.map((entry, i) => (
                                    <div key={i} className="rp-entry">
                                        <div className="rp-subheading-row">
                                            <span>
                                                <span className="rp-subheading-bold">{entry.org || ""}</span>
                                                {entry.techs && (
                                                    <span className="rp-project-techs"> | <em>{entry.techs}</em></span>
                                                )}
                                            </span>
                                            <span className="rp-subheading-right">{fmtDates(entry.dates)}</span>
                                        </div>
                                        {entry.bullets.length > 0 && (
                                            <ul className="rp-bullet-list">
                                                {entry.bullets.map((b) => (
                                                    <BulletItem
                                                        key={b.id}
                                                        id={b.id}
                                                        text={b.text}
                                                        editable={editable}
                                                        onChange={onBulletChange}
                                                    />
                                                ))}
                                            </ul>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </>
                    )}

                    {/* Leadership */}
                    {sections.leadership && sections.leadership.length > 0 && (
                        <>
                            <SectionHeading title="Leadership" />
                            <ExperienceSection
                                entries={sections.leadership}
                                editable={editable}
                                onBulletChange={onBulletChange}
                                fmtDates={fmtDates}
                            />
                        </>
                    )}

                    {/* Technical Skills */}
                    {sections.skills && sections.skills.length > 0 && (
                        <>
                            <SectionHeading title="Technical Skills" />
                            <div className="rp-skills">
                                {sections.skills.map((sg, i) => (
                                    <div key={i} className="rp-skill-row">
                                        <span className="rp-skill-category">{sg.category}</span>
                                        <span>{sg.skills}</span>
                                    </div>
                                ))}
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* Page navigation */}
            {pageCount > 1 && (
                <div className="rp-page-nav">
                    {Array.from({ length: pageCount }, (_, i) => i + 1).map((p) => (
                        <button
                            key={p}
                            onClick={() => setCurrentPage(p)}
                            className={`rp-page-btn ${p === currentPage ? "rp-page-btn-active" : ""}`}
                        >
                            {p}
                        </button>
                    ))}
                    <span className="rp-page-label">
                        Page {currentPage} of {pageCount}
                    </span>
                </div>
            )}
        </div>
    );
}
