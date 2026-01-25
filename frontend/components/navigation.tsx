"use client";

import Link from "next/link";
import { Github } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Navigation() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-8">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-1">
            <span className="text-xl font-bold tracking-tight">
              Resume.<span className="text-primary">compile</span>()
            </span>
          </Link>
          
        </div>

        <div className="flex items-center gap-4">
          {/* GitHub Link */}
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="View on GitHub"
          >
            <Github className="h-5 w-5" />
          </a>
          
          {/* Primary CTA */}
          <Button asChild size="sm">
            <Link href="/vault">Start free</Link>
          </Button>
        </div>
      </nav>
    </header>
  );
}
