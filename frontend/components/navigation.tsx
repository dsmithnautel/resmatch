"use client";

import Link from "next/link";
import { ChevronDown, Github, Loader2, LogOut } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/components/auth-provider";

export function Navigation() {
  const {
    user,
    profile,
    loading,
    profileLoading,
    configured,
    signOutUser,
  } = useAuth();

  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  const firstName =
    profile?.fullName?.split(" ")[0] ||
    user?.displayName?.split(" ")[0] ||
    user?.email?.split("@")[0] ||
    "Account";
  const initials = firstName.charAt(0).toUpperCase();
  const needsOnboarding = Boolean(user && !profile?.onboardingCompleted);
  const onboardingStep = Math.min(profile?.onboardingStep ?? 1, 3);

  useEffect(() => {
    if (!menuOpen) return;

    function handleOutsideClick(event: MouseEvent) {
      if (!menuRef.current?.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [menuOpen]);

  async function handleSignOut() {
    await signOutUser();
    setMenuOpen(false);
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center gap-1">
          <span className="text-xl font-bold tracking-tight">
            Res<span className="text-primary">Match</span>
          </span>
        </Link>

        <div className="flex items-center gap-4">
          {/* GitHub Link */}
          <a
            href="https://github.com/dsmithnautel/resmatch"
            target="_blank"
            rel="noopener noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="View on GitHub"
          >
            <Github className="h-5 w-5" />
          </a>

          {/* Primary CTA */}
          <Button asChild size="sm">
            <Link href="/vault">{user ? "Open app" : "Start free"}</Link>
          </Button>

          {configured && (
            <>
              {loading || profileLoading ? (
                <span className="inline-flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Checking auth
                </span>
              ) : user ? (
                <div className="relative" ref={menuRef}>
                  <button
                    type="button"
                    onClick={() => setMenuOpen((current) => !current)}
                    className="inline-flex items-center gap-2 rounded-full border bg-background px-2.5 py-1.5 text-sm text-foreground hover:bg-accent transition-colors"
                    aria-expanded={menuOpen}
                    aria-haspopup="menu"
                  >
                    <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-semibold text-foreground">
                      {initials}
                    </span>
                    <span className="hidden sm:inline">{firstName}</span>
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  </button>

                  {menuOpen && (
                    <div
                      role="menu"
                      className="absolute right-0 mt-2 w-48 rounded-md border bg-popover shadow-lg z-50"
                    >
                      {needsOnboarding && (
                        <Link
                          href="/onboarding"
                          onClick={() => setMenuOpen(false)}
                          className="block px-3 py-2 text-sm hover:bg-accent transition-colors"
                        >
                          Setup {onboardingStep}/3
                        </Link>
                      )}
                      <Link
                        href="/onboarding"
                        onClick={() => setMenuOpen(false)}
                        className="block px-3 py-2 text-sm hover:bg-accent transition-colors"
                      >
                        Settings
                      </Link>
                      <button
                        type="button"
                        onClick={handleSignOut}
                        className="w-full text-left px-3 py-2 text-sm text-destructive hover:bg-accent transition-colors inline-flex items-center gap-2"
                      >
                        <LogOut className="h-4 w-4" />
                        Sign out
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/sign-in?next=/vault">Sign in</Link>
                </Button>
              )}
            </>
          )}
        </div>
      </nav>
    </header>
  );
}
