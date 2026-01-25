"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowRight, Loader2, Link as LinkIcon, FileText, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { parseJobDescription, compileResume, type ParsedJD, type CompileResponse } from "@/lib/api";

function CompilePageContent() {
  const searchParams = useSearchParams();
  const masterVersion = searchParams.get("version");

  const [jdInput, setJdInput] = useState("");
  const [inputMode, setInputMode] = useState<"url" | "text">("url");
  const [isParsingJD, setIsParsingJD] = useState(false);
  const [parsedJD, setParsedJD] = useState<ParsedJD | null>(null);
  const [isCompiling, setIsCompiling] = useState(false);
  const [compileResult, setCompileResult] = useState<CompileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Redirect if no master version
  useEffect(() => {
    if (!masterVersion) {
      // Could redirect to vault
    }
  }, [masterVersion]);

  const handleParseJD = async () => {
    if (!jdInput.trim()) return;

    setIsParsingJD(true);
    setError(null);

    try {
      const result = await parseJobDescription(
        inputMode === "url" ? jdInput : undefined,
        inputMode === "text" ? jdInput : undefined
      );
      setParsedJD(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to parse job description");
    } finally {
      setIsParsingJD(false);
    }
  };

  const handleCompile = async () => {
    if (!masterVersion || !parsedJD) return;

    setIsCompiling(true);
    setError(null);

    try {
      const result = await compileResume(masterVersion, parsedJD.jd_id);
      setCompileResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to tailor resume");
    } finally {
      setIsCompiling(false);
    }
  };

  // If we have compile results, redirect to review
  if (compileResult) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Card className="max-w-2xl mx-auto text-center">
          <CardContent className="pt-6">
            <div className="text-green-600 text-6xl mb-4">✓</div>
            <h2 className="text-2xl font-bold mb-2">Resume Tailored!</h2>
            <p className="text-gray-600 dark:text-gray-300 mb-6">
              Selected {compileResult.selected_units.length} bullets with{" "}
              {Math.round(compileResult.coverage.coverage_score * 100)}% requirement coverage.
            </p>
            <Link href={`/review/${compileResult.compile_id}`}>
              <Button size="lg" className="gap-2">
                Review & Export
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <Link href="/vault" className="text-blue-600 hover:underline text-sm mb-2 inline-block">
          &larr; Back to Upload
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Add Job Description
        </h1>
        <p className="text-gray-600 dark:text-gray-300 mt-2">
          Paste a job description to tailor your resume.
          {masterVersion && (
            <span className="ml-2 text-blue-600">Using: {masterVersion}</span>
          )}
        </p>
      </div>

      {!masterVersion && (
        <Card className="max-w-2xl mx-auto bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-yellow-700 dark:text-yellow-300">
              <AlertCircle className="w-5 h-5" />
              <span>No resume uploaded.</span>
              <Link href="/vault" className="underline">Upload one first.</Link>
            </div>
          </CardContent>
        </Card>
      )}

      {masterVersion && !parsedJD && (
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>Job Description</CardTitle>
            <CardDescription>
              Paste a job posting URL or the full text of the job description.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Input Mode Toggle */}
            <div className="flex gap-2">
              <Button
                variant={inputMode === "url" ? "default" : "outline"}
                size="sm"
                onClick={() => setInputMode("url")}
                className="gap-2"
              >
                <LinkIcon className="w-4 h-4" />
                URL
              </Button>
              <Button
                variant={inputMode === "text" ? "default" : "outline"}
                size="sm"
                onClick={() => setInputMode("text")}
                className="gap-2"
              >
                <FileText className="w-4 h-4" />
                Paste Text
              </Button>
            </div>

            {/* Input Field */}
            {inputMode === "url" ? (
              <input
                type="url"
                placeholder="https://careers.example.com/job/123"
                value={jdInput}
                onChange={(e) => setJdInput(e.target.value)}
                className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-700"
              />
            ) : (
              <textarea
                placeholder="Paste the full job description here..."
                value={jdInput}
                onChange={(e) => setJdInput(e.target.value)}
                rows={10}
                className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:border-gray-700"
              />
            )}

            {error && (
              <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg flex items-center gap-2 text-red-700 dark:text-red-300">
                <AlertCircle className="w-5 h-5" />
                {error}
              </div>
            )}

            <Button
              onClick={handleParseJD}
              disabled={!jdInput.trim() || isParsingJD}
              className="w-full"
            >
              {isParsingJD ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Parsing...
                </>
              ) : (
                "Parse Job Description"
              )}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Parsed JD Display */}
      {parsedJD && (
        <div className="space-y-6 max-w-3xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>{parsedJD.role_title}</CardTitle>
              <CardDescription>{parsedJD.company}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Must Haves */}
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Must-Have Requirements ({parsedJD.must_haves.length})
                </h4>
                <ul className="space-y-1">
                  {parsedJD.must_haves.map((req, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="text-red-500 mt-1">•</span>
                      <span>{req}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Responsibilities */}
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Key Responsibilities ({parsedJD.responsibilities.length})
                </h4>
                <ul className="space-y-1">
                  {parsedJD.responsibilities.map((resp, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm">
                      <span className="text-blue-500 mt-1">•</span>
                      <span>{resp}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Keywords */}
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  Keywords
                </h4>
                <div className="flex flex-wrap gap-2">
                  {parsedJD.keywords.map((kw) => (
                    <span
                      key={kw}
                      className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-sm"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg flex items-center gap-2 text-red-700 dark:text-red-300">
              <AlertCircle className="w-5 h-5" />
              {error}
            </div>
          )}

          <div className="flex justify-center">
            <Button
              size="lg"
              onClick={handleCompile}
              disabled={isCompiling}
              className="gap-2"
            >
              {isCompiling ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Tailoring...
                </>
              ) : (
                <>
                  Tailor My Resume
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

export default function CompilePage() {
  return (
    <Suspense fallback={
      <div className="container mx-auto py-8 px-4 flex justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    }>
      <CompilePageContent />
    </Suspense>
  );
}
