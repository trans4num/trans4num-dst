"use client";

import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";

export function AuthGuard({
  children,
  requireAuth,
}: {
  children: React.ReactNode;
  requireAuth: boolean;
}) {
  const { isReady, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isReady) {
      return;
    }

    if (requireAuth && !isAuthenticated) {
      router.replace("/login");
      return;
    }

    if (!requireAuth && isAuthenticated) {
      router.replace("/region");
    }
  }, [isAuthenticated, isReady, requireAuth, router]);

  if (!isReady) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if ((requireAuth && !isAuthenticated) || (!requireAuth && isAuthenticated)) {
    return (
      <div className="flex min-h-svh items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  return <>{children}</>;
}
