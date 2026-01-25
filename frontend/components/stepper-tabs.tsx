"use client";

import { motion, useReducedMotion } from "framer-motion";
import { FileText, Target, Download, Sparkles } from "lucide-react";

interface Step {
  num: number;
  title: string;
  description: string;
  icon: React.ReactNode;
}

const steps: Step[] = [
  {
    num: 1,
    title: "Upload your resume",
    description:
      "PDF format. We extract your experience automatically.",
    icon: <FileText className="w-5 h-5" />,
  },
  {
    num: 2,
    title: "Paste a job description",
    description:
      "Copy and paste any job posting.",
    icon: <Target className="w-5 h-5" />,
  },
  {
    num: 3,
    title: "Review matches + missing requirements",
    description:
      "Every match links to the exact bullet we used.",
    icon: <Sparkles className="w-5 h-5" />,
  },
  {
    num: 4,
    title: "Export a tailored version",
    description:
      "Download ready-to-submit PDF.",
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
              <motion.div
                initial={shouldReduceMotion ? { height: "auto", opacity: 1 } : { height: 0, opacity: 0 }}
                animate={
                  isActive
                    ? { height: "auto", opacity: 1 }
                    : { height: 0, opacity: 0 }
                }
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <p className="text-sm text-muted-foreground mt-1">
                  {step.description}
                </p>
              </motion.div>
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}
