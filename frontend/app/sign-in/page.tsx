"use client";

import Link from "next/link";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { ChevronLeft, Loader2, LogIn } from "lucide-react";

import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

function safeNextPath(nextPath: string | null): string {
  if (!nextPath || !nextPath.startsWith("/")) return "/vault";
  return nextPath;
}

function SignInContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const {
    configured,
    loading,
    profileLoading,
    user,
    profile,
    signInWithGoogle,
  } = useAuth();

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const nextPath = searchParams.get("next");

  const targetPath = useMemo(() => safeNextPath(nextPath), [nextPath]);

  useEffect(() => {
    if (loading || profileLoading || !user) return;

    if (!profile?.onboardingCompleted) {
      router.replace("/onboarding");
      return;
    }

    router.replace(targetPath);
  }, [loading, profileLoading, user, profile, router, targetPath]);

  const handleGoogleSignIn = async () => {
    setError(null);
    setSubmitting(true);

    try {
      await signInWithGoogle();
      router.push(targetPath);
    } catch (signInError) {
      setError(
        signInError instanceof Error ? signInError.message : "Google sign-in failed.",
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-background">
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

      <div className="container py-10 px-4">
        <Card className="max-w-xl mx-auto">
          <CardHeader>
            <CardTitle className="text-2xl">Sign in to ResMatch</CardTitle>
            <CardDescription>
              Pick a sign-on option to save profile data and match history.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {!configured && (
              <p className="text-sm text-destructive">
                Firebase is not configured. Add `NEXT_PUBLIC_FIREBASE_*` values in
                `frontend/.env.local`.
              </p>
            )}

            <Button
              className="w-full gap-2"
              onClick={handleGoogleSignIn}
              disabled={!configured || loading || profileLoading || submitting}
            >
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Connecting to Google...
                </>
              ) : (
                <>
                  <LogIn className="h-4 w-4" />
                  Continue with Google
                </>
              )}
            </Button>

            {error && <p className="text-sm text-destructive">{error}</p>}

          </CardContent>
        </Card>
      </div>
    </main>
  );
}

export default function SignInPage() {
  return (
    <Suspense
      fallback={<main className="min-h-screen bg-background" aria-busy="true" />}
    >
      <SignInContent />
    </Suspense>
  );
}
