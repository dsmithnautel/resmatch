"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Download, FileText, CheckCircle, Info, Loader2, RotateCcw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getCompileResult, getPdfUrl, type CompileResponse, type ScoredUnit, type Provenance } from "@/lib/api";
import { toast } from "sonner";

export default function ReviewPage() {
  const params = useParams();
  const compileId = params.compileId as string;

  const [result, setResult] = useState<CompileResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedUnit, setSelectedUnit] = useState<ScoredUnit | null>(null);

  const loadResult = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getCompileResult(compileId);
      setResult(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load results";
      setError(message);
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (compileId) {
      loadResult();
    }
  }, [compileId]); // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Card className="max-w-lg mx-auto">
          <CardContent className="pt-6 text-center space-y-4">
            <div className="text-red-500 text-4xl mb-4">!</div>
            <p className="text-gray-600">{error || "Result not found"}</p>
            <div className="flex items-center justify-center gap-3">
              <Button variant="outline" onClick={loadResult} className="gap-2">
                <RotateCcw className="w-4 h-4" />
                Try Again
              </Button>
              <Link href="/vault" className="text-blue-600 hover:underline">
                Start over
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const provMap = new Map(result.provenance.map((p) => [p.atomic_unit_id, p]));

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-8">
        <Link href="/compile" className="text-blue-600 hover:underline text-sm mb-2 inline-block">
          &larr; Back to Job Description
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Review & Export
            </h1>
            <p className="text-gray-600 dark:text-gray-300 mt-2">
              Compile ID: {compileId}
            </p>
          </div>
          <div className="flex gap-3">
            <Button variant="outline" asChild>
              <a href={`/api/provenance/${compileId}`} download>
                <FileText className="w-4 h-4 mr-2" />
                Source Data (JSON)
              </a>
            </Button>
            <Button asChild>
              <a href={getPdfUrl(compileId)} download>
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </a>
            </Button>
          </div>
        </div>
      </div>

      {/* Coverage Stats */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600">
                {result.selected_units.length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-300">
                Bullets Selected
              </div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600">
                {Math.round(result.coverage.coverage_score * 100)}%
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-300">
                Requirement Coverage
              </div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600">
                {result.coverage.must_haves_matched}/{result.coverage.must_haves_total}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-300">
                Must-Haves Matched
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Selected Bullets */}
        <Card>
          <CardHeader>
            <CardTitle>Selected Bullets</CardTitle>
            <CardDescription>
              Click any bullet to see why it was included
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {result.selected_units.map((unit) => (
                <div
                  key={unit.unit_id}
                  onClick={() => setSelectedUnit(unit)}
                  className={`p-4 border rounded-lg cursor-pointer transition-all ${
                    selectedUnit?.unit_id === unit.unit_id
                      ? "border-blue-500 bg-blue-50 dark:bg-blue-900/20"
                      : "hover:border-gray-400"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs capitalize">
                        {unit.section}
                      </span>
                      {unit.org && (
                        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                          {unit.org}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <span
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          unit.llm_score >= 8
                            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                            : unit.llm_score >= 6
                            ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                            : "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200"
                        }`}
                      >
                        Score: {unit.llm_score.toFixed(1)}
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-800 dark:text-gray-200 text-sm">
                    {unit.text}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Provenance Panel */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Info className="w-5 h-5" />
              Why Included?
            </CardTitle>
            <CardDescription>
              {selectedUnit
                ? "See how this bullet matches the job requirements"
                : "Select a bullet to see why it was included"}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedUnit ? (
              <div className="space-y-4">
                {/* Unit Details */}
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    Selected Bullet
                  </h4>
                  <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <p className="text-sm">{selectedUnit.text}</p>
                    <div className="flex gap-2 mt-2 text-xs text-gray-500">
                      <span>ID: {selectedUnit.unit_id}</span>
                      {selectedUnit.org && <span>• {selectedUnit.org}</span>}
                      {selectedUnit.role && <span>• {selectedUnit.role}</span>}
                    </div>
                  </div>
                </div>

                {/* LLM Score */}
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    Relevance Score
                  </h4>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-600"
                        style={{ width: `${selectedUnit.llm_score * 10}%` }}
                      />
                    </div>
                    <span className="text-lg font-bold text-blue-600">
                      {selectedUnit.llm_score.toFixed(1)}/10
                    </span>
                  </div>
                </div>

                {/* Reasoning */}
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    AI Reasoning
                  </h4>
                  <p className="text-sm text-gray-600 dark:text-gray-300 italic">
                    &quot;{selectedUnit.reasoning || "No reasoning provided"}&quot;
                  </p>
                </div>

                {/* Matched Requirements */}
                <div>
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                    Matched Requirements
                  </h4>
                  {selectedUnit.matched_requirements.length > 0 ? (
                    <ul className="space-y-1">
                      {selectedUnit.matched_requirements.map((req, i) => (
                        <li key={i} className="flex items-center gap-2 text-sm">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>{req}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-sm text-gray-500">No specific matches recorded</p>
                  )}
                </div>

                {/* Source Record */}
                {provMap.has(selectedUnit.unit_id) && (
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                      Source Record
                    </h4>
                    <pre className="text-xs bg-gray-100 dark:bg-gray-800 p-3 rounded overflow-x-auto">
                      {JSON.stringify(provMap.get(selectedUnit.unit_id), null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Info className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>Select a bullet from the left panel to see why it was included</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
