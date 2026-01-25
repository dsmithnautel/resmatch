"use client";

import { motion, useReducedMotion } from "framer-motion";
import { FileText, Target, Sparkles, Download } from "lucide-react";

interface Step {
  num: number;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const steps: Step[] = [
  {
    num: 1,
    title: "Upload your master resume",
    description:
      "Upload your PDF. We extract bullets as verified atomic units — no rewriting, no embellishment.",
    icon: <FileText className="w-5 h-5" />,
  },
  {
    num: 2,
    title: "Paste the job description",
    description:
      "Paste the job posting. We extract requirements and keywords to match against your verified bullets.",
    icon: <Target className="w-5 h-5" />,
  },
  {
    num: 3,
    title: "Review matched bullets",
    description:
      "See which bullets match which requirements, with match scores and source links for every selection.",
    icon: <Sparkles className="w-5 h-5" />,
  },
  {
    num: 4,
    title: "Export your tailored PDF",
    description:
      "Download a clean, one-page resume with source links. Every bullet traceable to your original.",
    icon: <Download className="w-5 h-5" />,
  },
];

interface StepperTabsProps {
  activeStep: number;
  onStepChange: (step: number) => void;
}

export function StepperTabs({ activeStep, onStepChange }: StepperTabsProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="space-y-3">
      {steps.map((step) => {
        const isActive = activeStep === step.num;
        const isCompleted = activeStep > step.num;

        return (
          <motion.button
            key={step.num}
            onClick={() => onStepChange(step.num)}
            initial={shouldReduceMotion ? { opacity: 1 } : { opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: step.num * 0.1, duration: 0.3 }}
            className={`
              w-full flex items-start gap-4 p-4 rounded-xl text-left
              transition-all duration-200 border-2
              ${isActive
                ? "border-primary bg-primary/5 shadow-sm"
                : "border-transparent hover:border-border hover:bg-muted/50"
              }
              ${isCompleted ? "opacity-70" : ""}
            `}
          >
            {/* Step Number */}
            <div
              className={`
                flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
                text-sm font-semibold transition-colors duration-200
                ${isActive
                  ? "bg-primary text-primary-foreground"
                  : isCompleted
                    ? "bg-green-500 text-white"
                    : "bg-muted text-muted-foreground"
                }
              `}
            >
              {isCompleted ? "✓" : step.num}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <h3
                className={`
                  font-semibold transition-colors duration-200
                  ${isActive ? "text-foreground" : "text-muted-foreground"}
                `}
              >
                {step.title}
              </h3>
              <motion.p
                initial={shouldReduceMotion ? { height: "auto", opacity: 1 } : { height: 0, opacity: 0 }}
                animate={
                  isActive
                    ? { height: "auto", opacity: 1 }
                    : { height: 0, opacity: 0 }
                }
                transition={{ duration: 0.2 }}
                className="text-sm text-muted-foreground mt-1 overflow-hidden"
              >
                {step.description}
              </motion.p>
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}
