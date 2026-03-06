"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      <Card className="max-w-md w-full">
        <CardContent className="pt-6 text-center space-y-4">
          <AlertCircle className="w-12 h-12 mx-auto text-red-500" />
          <h2 className="text-xl font-semibold">Something went wrong</h2>
          <p className="text-muted-foreground">
            An unexpected error occurred. Please try again.
          </p>
          <Button onClick={reset}>Try Again</Button>
        </CardContent>
      </Card>
    </div>
  );
}
