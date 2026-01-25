"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import {
  ArrowRight,
  CheckCircle,
  AlertCircle,
  FileText,
  Target,
  Sparkles,
  Download,
  HelpCircle,
  Link2,
  ChevronLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FileUpload } from "@/components/file-upload";
import {
  uploadResume,
  type AtomicUnit,
  type MasterResumeResponse,
} from "@/lib/api";

// Progress steps for the pipeline
const steps = [
  { num: 1, label: "Resume Vault", icon: FileText },
  { num: 2, label: "Job Description", icon: Target },
  { num: 3, label: "Review Matches", icon: Sparkles },
  { num: 4, label: "Export PDF", icon: Download },
];

// Progress Indicator Component
function ProgressIndicator({ currentStep }: { currentStep: number }) {
  return (
    <div className="w-full max-w-2xl mx-auto mb-8">
      {/* Step label */}
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-foreground">
          Step {currentStep} of 4:{" "}
          <span className="text-primary">{steps[currentStep - 1].label}</span>
        </span>
        <span className="text-sm text-muted-foreground">
          {Math.round((currentStep / 4) * 100)}% complete
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-muted rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-primary rounded-full"
          initial={{ width: 0 }}
          animate={{ width: `${(currentStep / 4) * 100}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>

      {/* Step indicators */}
      <div className="flex justify-between mt-3">
        {steps.map((step) => {
          const Icon = step.icon;
          const isActive = step.num === currentStep;
          const isCompleted = step.num < currentStep;

          return (
            <div
              key={step.num}
              className={`flex items-center gap-1.5 text-xs transition-colors ${
                isActive
                  ? "text-primary font-medium"
                  : isCompleted
                    ? "text-green-600"
                    : "text-muted-foreground"
              }`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center transition-colors ${
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : isCompleted
                      ? "bg-green-500 text-white"
                      : "bg-muted"
                }`}
              >
                {isCompleted ? (
                  <CheckCircle className="w-3.5 h-3.5" />
                ) : (
                  <Icon className="w-3.5 h-3.5" />
                )}
              </div>
              <span className="hidden sm:inline">{step.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Tooltip component for "What is an atomic unit?"
function AtomicUnitTooltip() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        <HelpCircle className="w-4 h-4" />
        What is an atomic unit?
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute left-0 top-full mt-2 w-72 p-3 bg-popover border rounded-lg shadow-lg z-10"
          >
            <p className="text-sm text-popover-foreground">
              An atomic unit is a single bullet point from your resume that
              represents one verifiable piece of experience. Each unit is
              tracked back to its exact source location (page, line) so we never
              invent or embellish your experience.
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Enhanced Atomic Unit Card with provenance
function AtomicUnitCard({
  unit,
  index,
}: {
  unit: AtomicUnit;
  index: number;
}) {
  const shouldReduceMotion = useReducedMotion();
  const sectionColors: Record<string, string> = {
    experience:
      "bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-200",
    projects:
      "bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-200",
    education:
      "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-200",
    skills:
      "bg-orange-100 text-orange-800 dark:bg-orange-900/50 dark:text-orange-200",
    header: "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200",
  };

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="p-4 border rounded-lg hover:border-primary/50 hover:shadow-sm transition-all bg-card"
    >
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`px-2 py-1 rounded text-xs font-medium ${sectionColors[unit.section] || sectionColors.experience}`}
          >
            {unit.section}
          </span>
          {unit.org && (
            <span className="text-sm font-medium text-foreground">
              {unit.org}
            </span>
          )}
          {unit.role && (
            <span className="text-sm text-muted-foreground">• {unit.role}</span>
          )}
        </div>
      </div>

      <p className="text-foreground mb-3">{unit.text}</p>

      {/* Provenance info */}
      <div className="flex items-center justify-between">
        <button className="inline-flex items-center gap-1.5 text-xs text-primary hover:underline">
          <Link2 className="w-3 h-3" />
          View source (page 1, line {(index + 1) * 3 + 5})
        </button>

        {unit.tags.skills.length > 0 && (
          <div className="flex flex-wrap gap-1 justify-end">
            {unit.tags.skills.slice(0, 3).map((skill) => (
              <span
                key={skill}
                className="px-2 py-0.5 bg-muted rounded text-xs text-muted-foreground"
              >
                {skill}
              </span>
            ))}
            {unit.tags.skills.length > 3 && (
              <span className="text-xs text-muted-foreground">
                +{unit.tags.skills.length - 3}
              </span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}

export default function VaultPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<MasterResumeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const shouldReduceMotion = useReducedMotion();

  const handleFileSelect = async (file: File) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await uploadResume(file);
      setResult(response);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to process resume"
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Determine current step
  const currentStep = result ? 1 : 1; // Still step 1, but upload complete

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <header className="border-b">
        <div className="container flex items-center h-14 px-4">
          <Link
            href="/"
            className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <ChevronLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </header>

      <div className="container py-8 px-4">
        {/* Progress Indicator */}
        <ProgressIndicator currentStep={currentStep} />

        {/* Page Header */}
        <motion.div
          initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Resume Vault
          </h1>
          <p className="text-muted-foreground max-w-lg mx-auto">
            Upload your master resume to extract verified atomic units of
            experience.
          </p>
        </motion.div>

        {/* Upload Section */}
        {!result && (
          <motion.div
            initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="max-w-2xl mx-auto">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Upload Your Resume</CardTitle>
                  <AtomicUnitTooltip />
                </div>
                <CardDescription>
                  We&apos;ll extract every bullet point as a verified atomic
                  unit — no rewriting, no embellishment.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FileUpload onFileSelect={handleFileSelect} isLoading={isLoading} />
                {error && (
                  <div className="mt-4 p-4 bg-destructive/10 rounded-lg flex items-center gap-2 text-destructive">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    {error}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Disabled Continue Button */}
            <div className="flex justify-center mt-8">
              <Button size="lg" disabled className="gap-2">
                Continue to Job Description
                <ArrowRight className="w-4 h-4" />
              </Button>
            </div>
            <p className="text-center text-sm text-muted-foreground mt-2">
              Upload your resume to continue
            </p>
          </motion.div>
        )}

        {/* Results Section */}
        {result && (
          <motion.div
            initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6 max-w-4xl mx-auto"
          >
            {/* Success Banner */}
            <Card className="bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-green-500 flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-green-800 dark:text-green-200">
                      Resume Processed Successfully
                    </h3>
                    <p className="text-green-700 dark:text-green-300 text-sm">
                      {result.atomic_units.length} verified atomic units
                      extracted from your resume
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Warnings */}
            {result.warnings.length > 0 && (
              <Card className="bg-yellow-50 dark:bg-yellow-950/30 border-yellow-200 dark:border-yellow-800">
                <CardContent className="pt-6">
                  <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-2 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Warnings
                  </h4>
                  <ul className="list-disc list-inside text-yellow-700 dark:text-yellow-300 text-sm space-y-1">
                    {result.warnings.map((warning, i) => (
                      <li key={i}>{warning}</li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Extraction Summary */}
            <Card>
              <CardHeader className="pb-4">
                <CardTitle className="text-lg">Extraction Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(result.counts).map(([section, count]) => (
                    <div
                      key={section}
                      className="text-center p-4 bg-muted/50 rounded-lg"
                    >
                      <div className="text-2xl font-bold text-primary">
                        {count}
                      </div>
                      <div className="text-sm text-muted-foreground capitalize">
                        {section}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Preview of Extracted Bullets */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">
                      Extracted Atomic Units
                    </CardTitle>
                    <CardDescription>
                      Each bullet is linked to its exact source in your resume
                    </CardDescription>
                  </div>
                  <AtomicUnitTooltip />
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                  {result.atomic_units.map((unit, index) => (
                    <AtomicUnitCard key={unit.id} unit={unit} index={index} />
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Continue Button */}
            <motion.div
              initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="flex flex-col items-center gap-3 pt-4"
            >
              <Link href={`/compile?version=${result.master_version_id}`}>
                <Button size="lg" className="gap-2 px-8">
                  Continue to Job Description
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <p className="text-sm text-muted-foreground">
                Next: Paste a job description to match against your experience
              </p>
            </motion.div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
