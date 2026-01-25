"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { motion, useInView, useReducedMotion } from "framer-motion";
import {
  FileText,
  Target,
  Download,
  CheckCircle,
  Link2,
  Shield,
  Eye,
  Sparkles,
  Lock,
  Github,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Navigation } from "@/components/navigation";
import { FlowDiagram } from "@/components/flow-diagram";
import { StepperTabs } from "@/components/stepper-tabs";

// Animation variants
const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

const fadeIn = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

// Animated section wrapper
function AnimatedSection({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      ref={ref}
      initial={shouldReduceMotion ? "visible" : "hidden"}
      animate={isInView ? "visible" : "hidden"}
      variants={fadeInUp}
      transition={{ duration: 0.5, delay }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

// Product Preview Component with demo loop
function ProductPreview() {
  const [step, setStep] = useState(0);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    if (shouldReduceMotion) return;

    const interval = setInterval(() => {
      setStep((prev) => (prev + 1) % 5);
    }, 1500);

    return () => clearInterval(interval);
  }, [shouldReduceMotion]);

  return (
    <Card className="w-full max-w-md shadow-lg border-border/50">
      <CardContent className="p-0">
        {/* Preview Header */}
        <div className="flex items-center gap-2 px-4 py-3 border-b bg-muted/30">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-400" />
            <div className="w-3 h-3 rounded-full bg-yellow-400" />
            <div className="w-3 h-3 rounded-full bg-green-400" />
          </div>
          <span className="text-xs text-muted-foreground ml-2">
            resume-compile
          </span>
        </div>

        {/* Preview Content */}
        <div className="p-5 space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Your Resume</span>
            <span className="text-xs text-muted-foreground">
              12 bullets extracted
            </span>
          </div>

          {/* Demo Bullet */}
          <motion.div
            className={`p-3 rounded-lg border-2 transition-colors ${
              step >= 1 ? "border-primary bg-primary/5" : "border-border"
            }`}
          >
            <p className="text-sm">
              Led development of{" "}
              <motion.span
                className={`${step >= 3 ? "bg-yellow-200 dark:bg-yellow-900/50" : ""} transition-colors`}
              >
                real-time analytics dashboard
              </motion.span>{" "}
              serving 10K+ daily users, reducing page load time by 40%
            </p>
          </motion.div>

          {/* Match Status */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{
              opacity: step >= 2 ? 1 : 0,
              scale: step >= 2 ? 1 : 0.9,
            }}
            className="flex items-center gap-2"
          >
            <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-primary/10 text-primary text-xs font-medium">
              <CheckCircle className="w-3 h-3" />
              Matches requirement
            </span>
            <span className="text-xs text-muted-foreground">Score: 0.92</span>
          </motion.div>

          {/* View Source Link */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: step >= 4 ? 1 : 0 }}
          >
            <button className="text-sm text-primary hover:underline flex items-center gap-1">
              <Link2 className="w-3 h-3" />
              View source (page 1, line 8)
            </button>
          </motion.div>
        </div>
      </CardContent>
    </Card>
  );
}

// Proof Bullet Item
function ProofBullet({
  icon,
  text,
}: {
  icon: React.ReactNode;
  text: string;
}) {
  return (
    <div className="flex items-center gap-2 text-sm text-muted-foreground">
      <span className="text-primary">{icon}</span>
      <span>{text}</span>
    </div>
  );
}

// Feature Card
function FeatureCard({
  icon,
  title,
  description,
  highlight = false,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  highlight?: boolean;
}) {
  return (
    <Card
      className={`transition-shadow hover:shadow-md ${
        highlight ? "ring-2 ring-primary/20" : ""
      }`}
    >
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
            {icon}
          </div>
          <div>
            <h3 className="font-semibold text-foreground">{title}</h3>
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}


export default function Home() {
  const shouldReduceMotion = useReducedMotion();
  const [activeStep, setActiveStep] = useState(1);

  return (
    <>
      <Navigation />
      <main className="flex flex-col">
        {/* Hero Section */}
        <section className="relative px-6 py-section-lg lg:py-section-lg overflow-hidden">
          <div className="container">
            <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
              {/* Copy */}
              <motion.div
                initial={shouldReduceMotion ? "visible" : "hidden"}
                animate="visible"
                variants={staggerContainer}
                className="text-center lg:text-left"
              >
                <motion.h1
                  variants={fadeInUp}
                  className="text-h1-mobile lg:text-h1 tracking-tight text-foreground"
                >
                  Tailor your resume with{" "}
                  <span className="text-primary">zero hallucinations</span>
                </motion.h1>

                <motion.p
                  variants={fadeInUp}
                  className="mt-4 text-body text-muted-foreground max-w-xl mx-auto lg:mx-0"
                >
                  We only use bullets that already exist on your resume, and we
                  show the exact source for every bullet.
                </motion.p>

                {/* CTAs */}
                <motion.div
                  variants={fadeInUp}
                  className="mt-8 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
                >
                  <Button size="lg" asChild>
                    <Link href="/vault">
                      Start free
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Link>
                  </Button>
                  <Button variant="outline" size="lg" asChild>
                    <Link href="#how-it-works">See how it works</Link>
                  </Button>
                </motion.div>

                {/* Proof Bullets */}
                <motion.div
                  variants={fadeInUp}
                  className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4 justify-items-center lg:justify-items-start"
                >
                  <ProofBullet
                    icon={<Link2 className="w-4 h-4" />}
                    text="Source links per bullet"
                  />
                  <ProofBullet
                    icon={<FileText className="w-4 h-4" />}
                    text="ATS-friendly export"
                  />
                  <ProofBullet
                    icon={<Shield className="w-4 h-4" />}
                    text="No sign-up required"
                  />
                </motion.div>
              </motion.div>

              {/* Product Preview */}
              <motion.div
                initial={shouldReduceMotion ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: 0.3 }}
                className="flex justify-center lg:justify-end"
              >
                <ProductPreview />
              </motion.div>
            </div>
          </div>
        </section>

        {/* Trust Strip */}
        <section className="py-8 border-y bg-muted/30">
          <div className="container">
            <div className="flex flex-wrap justify-center gap-8 lg:gap-16 text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span>Verified-only content</span>
              </div>
              <div className="flex items-center gap-2">
                <Eye className="w-4 h-4 text-primary" />
                <span>Full source tracking</span>
              </div>
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-primary" />
                <span>Privacy first</span>
              </div>
              <div className="flex items-center gap-2">
                <Github className="w-4 h-4" />
                <span>Open source</span>
              </div>
            </div>
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="py-section-lg px-6 bg-muted/20">
          <div className="container">
            <AnimatedSection className="text-center mb-16">
              <h2 className="text-h2 text-foreground">How it works</h2>
              <p className="mt-3 text-body-sm text-muted-foreground max-w-2xl mx-auto">
                Two inputs converge into one tailored resume, every bullet traceable
              </p>
            </AnimatedSection>

            <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-start">
              {/* Interactive Steps */}
              <AnimatedSection>
                <StepperTabs activeStep={activeStep} onStepChange={setActiveStep} />
              </AnimatedSection>

              {/* Flow Diagram */}
              <AnimatedSection delay={0.2}>
                <div className="lg:sticky lg:top-24">
                  <FlowDiagram activeStep={activeStep} />
                </div>
              </AnimatedSection>
            </div>
          </div>
        </section>

        {/* Source Tracking Spotlight */}
        <section className="py-section-lg px-6">
          <div className="container">
            <AnimatedSection className="text-center mb-16">
              <h2 className="text-h2 text-foreground">
                Every bullet has a source
              </h2>
              <p className="mt-3 text-body-sm text-muted-foreground max-w-2xl mx-auto">
                Click any bullet to see exactly where it came from in your
                original resume
              </p>
            </AnimatedSection>

            <AnimatedSection delay={0.1}>
              <div className="max-w-4xl mx-auto">
                <div className="grid md:grid-cols-2 gap-6 items-center">
                  {/* Resume Card */}
                  <Card className="shadow-md">
                    <CardContent className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <FileText className="w-4 h-4 text-primary" />
                        <span className="text-sm font-medium">Your Resume</span>
                      </div>
                      <div className="p-3 rounded bg-muted/50 border-l-4 border-primary">
                        <p className="text-sm">
                          Built and deployed{" "}
                          <span className="bg-yellow-200 dark:bg-yellow-900/50 px-0.5">
                            machine learning pipeline
                          </span>{" "}
                          processing 1M+ records daily with 99.9% uptime
                        </p>
                        <div className="mt-2 text-xs text-muted-foreground">
                          Page 1, Line 12
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Connector */}
                  <div className="hidden md:flex items-center justify-center absolute left-1/2 -translate-x-1/2">
                    <div className="w-16 h-0.5 bg-gradient-to-r from-primary/50 to-primary" />
                  </div>

                  {/* Job Requirement Card */}
                  <Card className="shadow-md">
                    <CardContent className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <Target className="w-4 h-4 text-primary" />
                        <span className="text-sm font-medium">
                          Job Requirement
                        </span>
                      </div>
                      <div className="p-3 rounded bg-muted/50 border-l-4 border-green-500">
                        <p className="text-sm">
                          Experience with{" "}
                          <span className="bg-yellow-200 dark:bg-yellow-900/50 px-0.5">
                            ML/AI systems
                          </span>{" "}
                          and large-scale data processing
                        </p>
                        <div className="mt-2 flex items-center gap-2">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-xs font-medium">
                            <CheckCircle className="w-3 h-3" />
                            Matched
                          </span>
                          <span className="text-xs text-muted-foreground">
                            Score: 0.89
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Source Link */}
                <div className="mt-6 text-center">
                  <button className="inline-flex items-center gap-2 text-sm text-primary hover:underline focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded px-2 py-1">
                    <Link2 className="w-4 h-4" />
                    View source (page 1, line 12)
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </AnimatedSection>
          </div>
        </section>

        {/* Feature Grid */}
        <section className="py-section-lg px-6 bg-muted/20">
          <div className="container">
            <AnimatedSection className="text-center mb-16">
              <h2 className="text-h2 text-foreground">What makes it different</h2>
              <p className="mt-3 text-body-sm text-muted-foreground max-w-2xl mx-auto">
                Built for trust and transparency, not just convenience
              </p>
            </AnimatedSection>

            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-100px" }}
              variants={staggerContainer}
              className="grid md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {[
                {
                  icon: <Link2 className="w-5 h-5" />,
                  title: "Source links per bullet",
                  description:
                    "Every bullet links back to the exact line in your original resume. No guessing where content came from.",
                  highlight: true,
                },
                {
                  icon: <Shield className="w-5 h-5" />,
                  title: "Verified-only content",
                  description:
                    "We never generate or embellish. Every word in your output existed in your input.",
                  highlight: false,
                },
                {
                  icon: <Sparkles className="w-5 h-5" />,
                  title: "Match explanations",
                  description:
                    "See why each bullet was selected and which job requirements it addresses.",
                  highlight: false,
                },
                {
                  icon: <FileText className="w-5 h-5" />,
                  title: "One-page export",
                  description:
                    "Automatically optimized to fit the best content into a clean, ATS-friendly one-page format.",
                  highlight: false,
                },
                {
                  icon: <Lock className="w-5 h-5" />,
                  title: "Privacy first",
                  description:
                    "Your resume is processed in-memory and not stored. No tracking, no data selling.",
                  highlight: false,
                },
                {
                  icon: <Github className="w-5 h-5" />,
                  title: "Free and open source",
                  description:
                    "Fully transparent. Inspect the code, self-host, or contribute on GitHub.",
                  highlight: false,
                },
              ].map((feature, i) => (
                <motion.div key={feature.title} variants={fadeInUp}>
                  <FeatureCard {...feature} />
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* Questions Section */}
        <section className="py-section-md px-6">
          <div className="container">
            <AnimatedSection className="text-center">
              <h2 className="text-h2 text-foreground mb-4">
                Have questions?
              </h2>
              <p className="text-body-sm text-muted-foreground max-w-lg mx-auto mb-6">
                Check out our FAQ and documentation on GitHub, or open an issue if you need help.
              </p>
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-primary hover:underline font-medium"
              >
                <Github className="w-5 h-5" />
                View FAQ on GitHub
                <ExternalLink className="w-4 h-4" />
              </a>
            </AnimatedSection>
          </div>
        </section>

        {/* Final CTA Band */}
        <section id="privacy" className="py-section-md px-6 bg-gradient-to-br from-primary/5 to-primary/10">
          <div className="container text-center">
            <AnimatedSection>
              <h2 className="text-h2 text-foreground">
                Ready to compile your perfect resume?
              </h2>
              <p className="mt-3 text-body-sm text-muted-foreground max-w-xl mx-auto">
                No sign-up required. Your resume is not stored permanently.
              </p>
              <div className="mt-8 flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Button size="lg" asChild>
                  <Link href="/vault">
                    Start free
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Link>
                </Button>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Read privacy details on GitHub
                </a>
              </div>
            </AnimatedSection>
          </div>
        </section>

        {/* Footer */}
        <footer className="py-12 px-6 border-t">
          <div className="container">
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              {/* Logo */}
              <div className="flex items-center gap-1">
                <span className="text-lg font-bold tracking-tight">
                  Resume.<span className="text-primary">compile</span>()
                </span>
              </div>

              {/* Links */}
              <div className="flex items-center gap-6 text-sm text-muted-foreground">
                <Link
                  href="#how-it-works"
                  className="hover:text-foreground transition-colors"
                >
                  How it works
                </Link>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-foreground transition-colors"
                >
                  FAQ
                </a>
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-foreground transition-colors flex items-center gap-1"
                >
                  <Github className="w-4 h-4" />
                  GitHub
                </a>
              </div>

              {/* Built for */}
              <div className="text-sm text-muted-foreground">
                Built for SwampHacks XI 💙🧡🐊
              </div>
            </div>
          </div>
        </footer>
      </main>
    </>
  );
}
