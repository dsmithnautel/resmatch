"use client";

import { motion, useReducedMotion } from "framer-motion";
import { FileText, Target, Sparkles, Download, CheckCircle } from "lucide-react";

interface FlowDiagramProps {
  activeStep: number;
}

// Node component with artifact chip
function FlowNode({
  icon,
  label,
  chip,
  isActive,
  isCompleted,
  delay = 0,
}: {
  icon: React.ReactNode;
  label: string;
  chip: string;
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
        relative flex flex-col items-center gap-2 p-4 rounded-xl border-2 bg-card
        transition-all duration-300
        ${isActive ? "border-primary shadow-lg shadow-primary/10 scale-105" : "border-border"}
        ${isCompleted ? "border-green-500/50 bg-green-50/50 dark:bg-green-950/20" : ""}
      `}
    >
      {/* Icon */}
      <div
        className={`
          w-10 h-10 rounded-lg flex items-center justify-center transition-colors
          ${isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"}
          ${isCompleted ? "bg-green-500 text-white" : ""}
        `}
      >
        {isCompleted ? <CheckCircle className="w-5 h-5" /> : icon}
      </div>

      {/* Label */}
      <span className="text-sm font-medium text-center">{label}</span>

      {/* Artifact Chip */}
      <motion.span
        initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, scale: 0.9 }}
        animate={isActive || isCompleted ? { opacity: 1, scale: 1 } : { opacity: 0.5, scale: 0.95 }}
        className={`
          text-xs px-2 py-1 rounded-full
          ${isActive ? "bg-primary/10 text-primary font-medium" : "bg-muted text-muted-foreground"}
          ${isCompleted ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" : ""}
        `}
      >
        {chip}
      </motion.span>
    </motion.div>
  );
}

// Connector line with animation
function ConnectorLine({
  direction,
  isActive,
  delay = 0,
}: {
  direction: "vertical" | "horizontal" | "diagonal-left" | "diagonal-right";
  isActive: boolean;
  delay?: number;
}) {
  const shouldReduceMotion = useReducedMotion();

  if (direction === "vertical") {
    return (
      <div className="flex justify-center py-2">
        <motion.div
          initial={shouldReduceMotion ? { scaleY: 1 } : { scaleY: 0 }}
          animate={{ scaleY: 1 }}
          transition={{ delay, duration: 0.4 }}
          style={{ originY: 0 }}
          className={`w-0.5 h-8 transition-colors duration-300 ${
            isActive ? "bg-primary" : "bg-border"
          }`}
        />
      </div>
    );
  }

  if (direction === "horizontal") {
    return (
      <motion.div
        initial={shouldReduceMotion ? { scaleX: 1 } : { scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ delay, duration: 0.4 }}
        style={{ originX: 0 }}
        className={`h-0.5 flex-1 transition-colors duration-300 ${
          isActive ? "bg-primary" : "bg-border"
        }`}
      />
    );
  }

  return null;
}

export function FlowDiagram({ activeStep }: FlowDiagramProps) {
  const shouldReduceMotion = useReducedMotion();

  // Determine which nodes are active based on step
  const resumeRailActive = activeStep === 1;
  const jobRailActive = activeStep === 2;
  const matchActive = activeStep === 3;
  const exportActive = activeStep === 4;

  // Completed states
  const resumeRailCompleted = activeStep > 1;
  const jobRailCompleted = activeStep > 2;
  const matchCompleted = activeStep > 3;

  return (
    <div className="w-full max-w-lg mx-auto">
      {/* Two Rails */}
      <div className="grid grid-cols-2 gap-8">
        {/* Resume Rail (Left) */}
        <div className="space-y-2">
          <motion.div
            initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xs font-semibold text-muted-foreground uppercase tracking-wider text-center mb-4"
          >
            Resume Rail
          </motion.div>

          <FlowNode
            icon={<FileText className="w-5 h-5" />}
            label="Upload Resume"
            chip="PDF input"
            isActive={resumeRailActive}
            isCompleted={resumeRailCompleted}
            delay={0.1}
          />

          <ConnectorLine
            direction="vertical"
            isActive={resumeRailActive || resumeRailCompleted}
            delay={0.2}
          />

          <FlowNode
            icon={<Sparkles className="w-5 h-5" />}
            label="Extract Bullets"
            chip="12 bullets found"
            isActive={resumeRailActive}
            isCompleted={resumeRailCompleted}
            delay={0.3}
          />
        </div>

        {/* Job Rail (Right) */}
        <div className="space-y-2">
          <motion.div
            initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-xs font-semibold text-muted-foreground uppercase tracking-wider text-center mb-4"
          >
            Job Rail
          </motion.div>

          <FlowNode
            icon={<Target className="w-5 h-5" />}
            label="Paste Job Description"
            chip="Text input"
            isActive={jobRailActive}
            isCompleted={jobRailCompleted}
            delay={0.15}
          />

          <ConnectorLine
            direction="vertical"
            isActive={jobRailActive || jobRailCompleted}
            delay={0.25}
          />

          <FlowNode
            icon={<Sparkles className="w-5 h-5" />}
            label="Extract Requirements"
            chip="8 requirements"
            isActive={jobRailActive}
            isCompleted={jobRailCompleted}
            delay={0.35}
          />
        </div>
      </div>

      {/* Converging Lines */}
      <div className="relative h-12 my-2">
        {/* Left diagonal line */}
        <motion.svg
          className="absolute inset-0 w-full h-full"
          initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
        >
          <motion.line
            x1="25%"
            y1="0"
            x2="50%"
            y2="100%"
            stroke={matchActive || matchCompleted || resumeRailCompleted ? "hsl(var(--primary))" : "hsl(var(--border))"}
            strokeWidth="2"
            initial={shouldReduceMotion ? { pathLength: 1 } : { pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ delay: 0.5, duration: 0.4 }}
          />
          <motion.line
            x1="75%"
            y1="0"
            x2="50%"
            y2="100%"
            stroke={matchActive || matchCompleted || jobRailCompleted ? "hsl(var(--primary))" : "hsl(var(--border))"}
            strokeWidth="2"
            initial={shouldReduceMotion ? { pathLength: 1 } : { pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={{ delay: 0.55, duration: 0.4 }}
          />
        </motion.svg>
      </div>

      {/* Match Node (Center) */}
      <div className="flex justify-center">
        <div className="w-full max-w-[200px]">
          <FlowNode
            icon={<Sparkles className="w-5 h-5" />}
            label="Match & Score"
            chip="92% match · View source"
            isActive={matchActive}
            isCompleted={matchCompleted}
            delay={0.6}
          />
        </div>
      </div>

      {/* Connector to Export */}
      <ConnectorLine
        direction="vertical"
        isActive={exportActive || matchCompleted}
        delay={0.7}
      />

      {/* Export Node */}
      <div className="flex justify-center">
        <div className="w-full max-w-[200px]">
          <FlowNode
            icon={<Download className="w-5 h-5" />}
            label="Export PDF"
            chip="One-page · ATS-ready"
            isActive={exportActive}
            isCompleted={false}
            delay={0.8}
          />
        </div>
      </div>
    </div>
  );
}
