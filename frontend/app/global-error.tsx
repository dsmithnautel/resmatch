"use client";

import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body className="flex items-center justify-center min-h-screen bg-background text-foreground">
        <div className="text-center space-y-4 p-8">
          <h2 className="text-xl font-semibold">Something went wrong</h2>
          <p className="text-muted-foreground">
            A critical error occurred. Please refresh the page.
          </p>
          <Button onClick={reset}>Try Again</Button>
        </div>
      </body>
    </html>
  );
}
