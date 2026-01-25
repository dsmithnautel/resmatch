"use client";

import { motion, useReducedMotion } from "framer-motion";
import { FileText, Target, Download, CheckCircle, ArrowDown, Sparkles } from "lucide-react";

interface FlowDiagramProps {
  activeStep: number;
}

// Simple step node
function StepNode({
  stepNum,
  icon,
  label,
  description,
  isActive,
  isCompleted,
  delay = 0,
}: {
  stepNum: number;
  icon: React.ReactNode;
  label: string;
  description: string;
  isActive: boolean;
  isCompleted: boolean;
  delay?: number;
}) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
      className={`
        flex items-center gap-4 p-4 rounded-xl border-2 bg-card
        transition-all duration-300
        ${isActive ? "border-primary shadow-lg shadow-primary/10" : "border-border"}
        ${isCompleted ? "border-green-500/50 bg-green-50/50 dark:bg-green-950/20" : ""}
      `}
    >
      {/* Step Number */}
      <div
        className={`
          flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold
          transition-colors
          ${isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}
          ${isCompleted ? "bg-green-500 text-white" : ""}
        `}
      >
        {isCompleted ? <CheckCircle className="w-6 h-6" /> : stepNum}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-muted-foreground">{icon}</span>
          <span className="font-semibold text-foreground">{label}</span>
        </div>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
    </motion.div>
  );
}

// Arrow connector
function ArrowConnector({ isActive, delay = 0 }: { isActive: boolean; delay?: number }) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay, duration: 0.3 }}
      className="flex justify-center py-2"
    >
      <ArrowDown className={`w-5 h-5 ${isActive ? "text-primary" : "text-border"}`} />
    </motion.div>
  );
}

export function FlowDiagram({ activeStep }: FlowDiagramProps) {
  return (
    <div className="w-full max-w-md mx-auto space-y-2">
      <StepNode
        stepNum={1}
        icon={<FileText className="w-4 h-4" />}
        label="Upload your resume"
        description="PDF format. We extract your experience automatically."
        isActive={activeStep === 1}
        isCompleted={activeStep > 1}
        delay={0.1}
      />

      <ArrowConnector isActive={activeStep >= 1} delay={0.2} />

      <StepNode
        stepNum={2}
        icon={<Target className="w-4 h-4" />}
        label="Paste a job description"
        description="Copy from any job posting."
        isActive={activeStep === 2}
        isCompleted={activeStep > 2}
        delay={0.3}
      />

      <ArrowConnector isActive={activeStep >= 2} delay={0.4} />

      <StepNode
        stepNum={3}
        icon={<Sparkles className="w-4 h-4" />}
        label="Review matches + missing"
        description="Every match links to exact bullet source."
        isActive={activeStep === 3}
        isCompleted={activeStep > 3}
        delay={0.5}
      />

      <ArrowConnector isActive={activeStep >= 3} delay={0.6} />

      <StepNode
        stepNum={4}
        icon={<Download className="w-4 h-4" />}
        label="Export a tailored version"
        description="Download ready-to-submit PDF."
        isActive={activeStep === 4}
        isCompleted={false}
        delay={0.7}
      />
    </div>
  );
}
