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
  Sparkles,
  Github,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Navigation } from "@/components/navigation";

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
  const isInView = useInView(ref, { once: true, margin: "-50px" });
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
            ResMatch
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
            className={`p-3 rounded-lg border-2 transition-colors ${step >= 1 ? "border-primary bg-primary/5" : "border-border"
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

// Differentiator Card (top row - stronger emphasis)
function DifferentiatorCard({
  icon,
  title,
  description,
  proof,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  proof?: React.ReactNode;
}) {
  return (
    <Card className="h-full transition-all duration-200 hover:shadow-lg hover:-translate-y-1 border-primary/20 bg-gradient-to-b from-primary/[0.03] to-transparent">
      <CardContent className="p-6">
        <div className="flex flex-col h-full">
          <div className="flex items-start gap-4 mb-3">
            <div className="flex-shrink-0 w-11 h-11 rounded-xl bg-primary/15 flex items-center justify-center text-primary transition-colors group-hover:bg-primary/20">
              {icon}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-foreground text-base">{title}</h3>
            </div>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">
            {description}
          </p>
          {proof && (
            <div className="mt-4 pt-3 border-t border-border/50">
              {proof}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// Feature Card (bottom row - quieter)
function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <Card className="h-full transition-all duration-200 hover:shadow-md hover:-translate-y-0.5 hover:border-border">
      <CardContent className="p-5">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-muted flex items-center justify-center text-muted-foreground">
            {icon}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-medium text-foreground text-sm">{title}</h3>
            <p className="text-sm text-muted-foreground mt-1 leading-relaxed line-clamp-2">
              {description}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}


export default function Home() {
  const shouldReduceMotion = useReducedMotion();

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
                  Tailor your resume{" "}
                  <span className="text-primary">for any job</span>
                </motion.h1>

                <motion.p
                  variants={fadeInUp}
                  className="mt-4 text-body text-muted-foreground max-w-xl mx-auto lg:mx-0"
                >
                  Upload your resume, paste a job description, and get a tailored
                  version that highlights your most relevant experience.
                </motion.p>

                {/* CTAs */}
                <motion.div
                  variants={fadeInUp}
                  className="mt-8 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
                >
                  <Button size="lg" asChild>
                    <Link href="/vault">
                      Start tailoring
                      <ChevronRight className="w-4 h-4 ml-1" />
                    </Link>
                  </Button>
                  <Button variant="outline" size="lg" asChild>
                    <Link href="#how-it-works">Try a demo</Link>
                  </Button>
                </motion.div>

                {/* Trust Points */}
                <motion.div
                  variants={fadeInUp}
                  className="mt-8 flex flex-wrap gap-4 justify-center lg:justify-start text-sm text-muted-foreground"
                >
                  <span className="flex items-center gap-1.5">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    Free to use
                  </span>
                  <span className="flex items-center gap-1.5">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    No sign-up required
                  </span>
                  <span className="flex items-center gap-1.5">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    Export as PDF
                  </span>
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
                <span>Uses only your real experience</span>
              </div>
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-primary" />
                <span>Matches job requirements</span>
              </div>
              <div className="flex items-center gap-2">
                <Download className="w-4 h-4 text-primary" />
                <span>Export-ready PDF</span>
              </div>
              <div className="flex items-center gap-2">
                <Github className="w-4 h-4" />
                <span>Open source</span>
              </div>
            </div>
          </div>
        </section>

        {/* Why Tailor - moved up to establish value first */}
        <section className="py-section-lg px-6">
          <div className="container">
            <AnimatedSection className="text-center mb-10">
              <h2 className="text-h2 text-foreground">Why tailor your resume?</h2>
              <p className="mt-3 text-body-sm text-muted-foreground max-w-2xl mx-auto">
                Generic resumes get overlooked. Tailored resumes get interviews.
              </p>
            </AnimatedSection>

            {/* Feature Cards */}
            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-50px" }}
              variants={staggerContainer}
              className="grid md:grid-cols-2 lg:grid-cols-4 gap-5"
            >
              <motion.div variants={fadeInUp}>
                <DifferentiatorCard
                  icon={<Target className="w-5 h-5" />}
                  title="Match job requirements"
                  description="Highlight the experience that matters most for each specific role."
                />
              </motion.div>
              <motion.div variants={fadeInUp}>
                <DifferentiatorCard
                  icon={<FileText className="w-5 h-5" />}
                  title="Works with projects"
                  description="No work experience? Projects and skills count just as much."
                />
              </motion.div>
              <motion.div variants={fadeInUp}>
                <DifferentiatorCard
                  icon={<Shield className="w-5 h-5" />}
                  title="Uses only real experience"
                  description="We never make things up. Everything comes from your resume."
                />
              </motion.div>
              <motion.div variants={fadeInUp}>
                <DifferentiatorCard
                  icon={<Sparkles className="w-5 h-5" />}
                  title="Save hours of work"
                  description="Create tailored versions in minutes, not hours."
                />
              </motion.div>
            </motion.div>
          </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="py-12 px-6 bg-muted/20">
          <div className="container">
            <AnimatedSection className="text-center mb-6">
              <h2 className="text-h2 text-foreground">How it works</h2>
              <p className="mt-2 text-body-sm text-muted-foreground max-w-2xl mx-auto">
                Upload your resume, paste a job description, download your tailored version.
              </p>
            </AnimatedSection>

            {/* Horizontal Steps */}
            <AnimatedSection delay={0.1}>
              <div className="max-w-4xl mx-auto">
                <div className="flex flex-col md:flex-row items-start justify-between gap-4">
                  {/* Step 1: Upload */}
                  <div className="flex items-start">
                    <div className="flex flex-col items-center text-center w-[140px]">
                      <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground mb-2">
                        <FileText className="w-5 h-5" />
                      </div>
                      <h3 className="font-semibold text-foreground text-sm h-10 flex items-center">Upload resume</h3>
                      <p className="text-xs text-muted-foreground leading-tight">
                        We extract your experience
                      </p>
                    </div>
                    <ChevronRight className="hidden md:block w-5 h-5 text-muted-foreground/40 mt-3.5 mx-4 flex-shrink-0" />
                  </div>

                  {/* Step 2: Paste */}
                  <div className="flex items-start">
                    <div className="flex flex-col items-center text-center w-[140px]">
                      <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground mb-2">
                        <Target className="w-5 h-5" />
                      </div>
                      <h3 className="font-semibold text-foreground text-sm h-10 flex items-center">Paste job description</h3>
                      <p className="text-xs text-muted-foreground leading-tight">
                        Copy from any posting
                      </p>
                    </div>
                    <ChevronRight className="hidden md:block w-5 h-5 text-muted-foreground/40 mt-3.5 mx-4 flex-shrink-0" />
                  </div>

                  {/* Step 3: Review */}
                  <div className="flex items-start">
                    <div className="flex flex-col items-center text-center w-[140px]">
                      <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground mb-2">
                        <Sparkles className="w-5 h-5" />
                      </div>
                      <h3 className="font-semibold text-foreground text-sm h-10 flex items-center">Review matches</h3>
                      <p className="text-xs text-muted-foreground leading-tight">
                        See what fits each role
                      </p>
                    </div>
                    <ChevronRight className="hidden md:block w-5 h-5 text-muted-foreground/40 mt-3.5 mx-4 flex-shrink-0" />
                  </div>

                  {/* Step 4: Export */}
                  <div className="flex items-start">
                    <div className="flex flex-col items-center text-center w-[140px]">
                      <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground mb-2">
                        <Download className="w-5 h-5" />
                      </div>
                      <h3 className="font-semibold text-foreground text-sm h-10 flex items-center">Export PDF</h3>
                      <p className="text-xs text-muted-foreground leading-tight">
                        Download tailored resume
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </AnimatedSection>
          </div>
        </section>

        {/* Examples Section */}
        <section className="py-section-lg px-6">
          <div className="container">
            <AnimatedSection className="text-center mb-12">
              <h2 className="text-h2 text-foreground">
                See how it matches your experience
              </h2>
              <p className="mt-3 text-body-sm text-muted-foreground max-w-2xl mx-auto">
                We find the best parts of your resume for each job requirement.
              </p>
            </AnimatedSection>

            <motion.div
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true, margin: "-50px" }}
              variants={staggerContainer}
              className="max-w-5xl mx-auto"
            >
              <div className="grid md:grid-cols-3 gap-5">
                {/* SWE Intern Example */}
                <motion.div variants={fadeInUp} className="flex">
                  <Card className="flex-1 transition-all duration-200 hover:shadow-lg hover:-translate-y-1 border-primary/20 bg-gradient-to-b from-primary/[0.03] to-transparent">
                    <CardContent className="p-5 h-full flex flex-col">
                      <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Target className="w-4 h-4 text-primary" />
                        </div>
                        <span className="text-sm font-semibold text-foreground">SWE Intern</span>
                      </div>
                      <div className="space-y-3 flex-1 flex flex-col">
                        <div className="h-[70px]">
                          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">Requirement</span>
                          <p className="text-sm mt-1 text-foreground">&quot;Built and shipped web features&quot;</p>
                        </div>
                        <div className="p-3 rounded-lg bg-primary/5 border-l-2 border-primary h-[120px]">
                          <span className="text-[10px] text-primary uppercase tracking-wider font-medium">Matched bullet</span>
                          <p className="text-sm mt-1 text-foreground leading-relaxed">
                            Implemented X feature in React; improved load time by 28% by memoizing heavy components.
                          </p>
                        </div>
                        <div className="pt-2 mt-auto">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/10 text-green-600 dark:text-green-400 text-xs font-medium">
                            <CheckCircle className="w-3 h-3" />
                            0.82 match
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>

                {/* Data Analyst Example */}
                <motion.div variants={fadeInUp} className="flex">
                  <Card className="flex-1 transition-all duration-200 hover:shadow-lg hover:-translate-y-1 border-primary/20 bg-gradient-to-b from-primary/[0.03] to-transparent">
                    <CardContent className="p-5 h-full flex flex-col">
                      <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Target className="w-4 h-4 text-primary" />
                        </div>
                        <span className="text-sm font-semibold text-foreground">Data Analyst</span>
                      </div>
                      <div className="space-y-3 flex-1 flex flex-col">
                        <div className="h-[70px]">
                          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">Requirement</span>
                          <p className="text-sm mt-1 text-foreground">&quot;SQL proficiency and dashboard experience&quot;</p>
                        </div>
                        <div className="p-3 rounded-lg bg-primary/5 border-l-2 border-primary h-[120px]">
                          <span className="text-[10px] text-primary uppercase tracking-wider font-medium">Matched bullet</span>
                          <p className="text-sm mt-1 text-foreground leading-relaxed">
                            Built SQL queries analyzing 500K+ rows; created Tableau dashboard tracking weekly KPIs.
                          </p>
                        </div>
                        <div className="pt-2 mt-auto">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/10 text-green-600 dark:text-green-400 text-xs font-medium">
                            <CheckCircle className="w-3 h-3" />
                            0.87 match
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>

                {/* PM Intern Example */}
                <motion.div variants={fadeInUp} className="flex">
                  <Card className="flex-1 transition-all duration-200 hover:shadow-lg hover:-translate-y-1 border-primary/20 bg-gradient-to-b from-primary/[0.03] to-transparent">
                    <CardContent className="p-5 h-full flex flex-col">
                      <div className="flex items-center gap-2 mb-4">
                        <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
                          <Target className="w-4 h-4 text-primary" />
                        </div>
                        <span className="text-sm font-semibold text-foreground">PM Intern</span>
                      </div>
                      <div className="space-y-3 flex-1 flex flex-col">
                        <div className="h-[70px]">
                          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-medium">Requirement</span>
                          <p className="text-sm mt-1 text-foreground">&quot;Gathered requirements from stakeholders&quot;</p>
                        </div>
                        <div className="p-3 rounded-lg bg-primary/5 border-l-2 border-primary h-[120px]">
                          <span className="text-[10px] text-primary uppercase tracking-wider font-medium">Matched bullet</span>
                          <p className="text-sm mt-1 text-foreground leading-relaxed">
                            Led 3 user interviews to define MVP scope; documented requirements in PRD reviewed by 2 engineers.
                          </p>
                        </div>
                        <div className="pt-2 mt-auto">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/10 text-green-600 dark:text-green-400 text-xs font-medium">
                            <CheckCircle className="w-3 h-3" />
                            0.79 match
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              </div>

              {/* Bottom Note */}
              <motion.p
                variants={fadeIn}
                className="mt-10 text-center text-sm text-muted-foreground"
              >
                Examples are illustrative. Your output is generated only from your resume content.
              </motion.p>
            </motion.div>
          </div>
        </section>

        {/* Final CTA Band */}
        <section className="py-section-md px-6 bg-gradient-to-br from-primary/5 to-primary/10">
          <div className="container text-center">
            <AnimatedSection>
              <h2 className="text-h2 text-foreground">
                Ready to tailor your resume?
              </h2>
              <p className="mt-3 text-body-sm text-muted-foreground max-w-xl mx-auto">
                Upload your resume, paste a job description, and get a tailored version in minutes.
              </p>
              <div className="mt-8">
                <Button size="lg" asChild>
                  <Link href="/vault">
                    Get started free
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Link>
                </Button>
              </div>
              <p className="mt-6 text-sm text-muted-foreground">
                No sign-up required
              </p>
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
                  Res<span className="text-primary">Match</span>
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
                  href="https://github.com/dsmithnautel/resmatch"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-foreground transition-colors"
                >
                  FAQ
                </a>
                <a
                  href="https://github.com/dsmithnautel/resmatch"
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
                Built for SwampHacks XI | Made With Love in Gainesville 💙🧡🐊
              </div>
            </div>
          </div>
        </footer>
      </main>
    </>
  );
}
