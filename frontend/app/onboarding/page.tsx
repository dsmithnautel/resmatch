"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, ChevronLeft, Loader2 } from "lucide-react";

import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  completeUserOnboarding,
  type UserPreferences,
} from "@/lib/firebase/user-profile";

type FieldErrors = {
  fullName?: string;
  roleFocus?: string;
  preferredLocation?: string;
};

function inputClassName(hasError: boolean): string {
  const baseClassName =
    "w-full rounded-md border bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2";
  if (!hasError) return baseClassName;
  return `${baseClassName} border-destructive focus-visible:ring-destructive`;
}

export default function OnboardingPage() {
  const router = useRouter();
  const {
    configured,
    loading,
    profileLoading,
    user,
    profile,
    signInWithGoogle,
    refreshProfile,
  } = useAuth();

  const [fullName, setFullName] = useState("");
  const [roleFocus, setRoleFocus] = useState("");
  const [preferredLocation, setPreferredLocation] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const isBusy = loading || profileLoading || saving;
  const onboardingStep = profile?.onboardingStep ?? 1;

  useEffect(() => {
    if (!profile) return;

    setFullName(profile.fullName || user?.displayName || "");
    setRoleFocus(profile.preferences.roleFocus);
    setPreferredLocation(profile.preferences.preferredLocation);
  }, [profile, user]);

  useEffect(() => {
    if (profile?.onboardingCompleted) {
      router.replace("/vault");
    }
  }, [profile, router]);

  const progressPercent = useMemo(() => {
    return Math.min(Math.max((onboardingStep / 3) * 100, 33), 100);
  }, [onboardingStep]);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextFieldErrors: FieldErrors = {};

    if (!user) {
      setError("Sign in first to finish onboarding.");
      return;
    }

    if (!fullName.trim()) {
      nextFieldErrors.fullName = "Full name is required.";
    }
    if (!roleFocus.trim()) {
      nextFieldErrors.roleFocus = "Role focus is required.";
    }
    if (!preferredLocation.trim()) {
      nextFieldErrors.preferredLocation = "Preferred location is required.";
    }

    if (
      nextFieldErrors.fullName ||
      nextFieldErrors.roleFocus ||
      nextFieldErrors.preferredLocation
    ) {
      setFieldErrors(nextFieldErrors);
      setError("Please fix the highlighted fields.");
      return;
    }

    setFieldErrors({});
    setError(null);
    setSaving(true);

    try {
      const nextPreferences: UserPreferences = {
        roleFocus: roleFocus.trim(),
        preferredLocation: preferredLocation.trim(),
        keywords: [],
      };

      await completeUserOnboarding(user, {
        fullName: fullName.trim(),
        preferences: nextPreferences,
      });

      await refreshProfile();
      router.push("/vault");
    } catch (submitError) {
      if (
        submitError instanceof Error &&
        (submitError.message.toLowerCase().includes("missing or insufficient permissions") ||
          submitError.message.toLowerCase().includes("permission-denied"))
      ) {
        setError(
          "Unable to save your profile due to Firestore permissions. Make sure signed-in users can read/write their own users/{uid} document.",
        );
        return;
      }
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Failed to save onboarding profile.",
      );
    } finally {
      setSaving(false);
    }
  };

  if (!configured) {
    return (
      <main className="min-h-screen bg-background">
        <div className="container py-10 px-4">
          <Card className="max-w-xl mx-auto">
            <CardHeader>
              <CardTitle>Firebase setup required</CardTitle>
              <CardDescription>
                Add your `NEXT_PUBLIC_FIREBASE_*` values in
                `frontend/.env.local` to enable onboarding.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button asChild variant="outline">
                <Link href="/">Back to home</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </main>
    );
  }

  if (loading || profileLoading) {
    return (
      <main className="min-h-screen bg-background">
        <div className="container py-10 px-4">
          <Card className="max-w-xl mx-auto">
            <CardContent className="pt-6 flex items-center gap-3">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span className="text-sm text-muted-foreground">
                Loading your profile...
              </span>
            </CardContent>
          </Card>
        </div>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="min-h-screen bg-background">
        <div className="container py-10 px-4">
          <Card className="max-w-xl mx-auto">
            <CardHeader>
              <CardTitle>Sign in to continue</CardTitle>
              <CardDescription>
                We need your account to create your profile in Firestore.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex items-center gap-3">
              <Button onClick={signInWithGoogle}>Sign in with Google</Button>
              <Button asChild variant="outline">
                <Link href="/">Back to home</Link>
              </Button>
            </CardContent>
          </Card>
        </div>
      </main>
    );
  }

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

      <div className="container py-8 px-4">
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-foreground">
              Finish your profile
            </h1>
            <p className="text-muted-foreground">
              This saves your profile and unlocks match history + personalized
              defaults.
            </p>
          </div>

          <Card>
            <CardHeader className="space-y-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">
                  Step {Math.min(onboardingStep, 3)} of 3
                </CardTitle>
                <span className="text-xs text-muted-foreground">
                  {Math.round(progressPercent)}% complete
                </span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Full name
                  </label>
                  <input
                    value={fullName}
                    onChange={(event) => {
                      setFullName(event.target.value);
                      setFieldErrors((prev) => ({ ...prev, fullName: undefined }));
                    }}
                    className={inputClassName(Boolean(fieldErrors.fullName))}
                    placeholder="Jane Doe"
                    autoComplete="name"
                  />
                  {fieldErrors.fullName && (
                    <p className="text-xs text-destructive">{fieldErrors.fullName}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Role focus
                  </label>
                  <input
                    value={roleFocus}
                    onChange={(event) => {
                      setRoleFocus(event.target.value);
                      setFieldErrors((prev) => ({ ...prev, roleFocus: undefined }));
                    }}
                    className={inputClassName(Boolean(fieldErrors.roleFocus))}
                    placeholder="Frontend Engineer"
                  />
                  {fieldErrors.roleFocus && (
                    <p className="text-xs text-destructive">{fieldErrors.roleFocus}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-foreground">
                    Preferred location
                  </label>
                  <input
                    value={preferredLocation}
                    onChange={(event) => {
                      setPreferredLocation(event.target.value);
                      setFieldErrors((prev) => ({
                        ...prev,
                        preferredLocation: undefined,
                      }));
                    }}
                    className={inputClassName(Boolean(fieldErrors.preferredLocation))}
                    placeholder="Remote / New York, NY"
                  />
                  {fieldErrors.preferredLocation && (
                    <p className="text-xs text-destructive">
                      {fieldErrors.preferredLocation}
                    </p>
                  )}
                </div>

                {error && (
                  <p className="text-sm text-destructive">{error}</p>
                )}

                <div className="flex items-center justify-between gap-3 pt-2">
                  <p className="text-xs text-muted-foreground">
                    Your account starts on the Free plan.
                  </p>
                  <Button type="submit" disabled={isBusy} className="gap-2">
                    {saving ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="h-4 w-4" />
                        Complete setup
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </main>
  );
}
