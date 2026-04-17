"use client";

import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { useAuth } from "@/components/auth-provider";

export default function HomePage() {
  const { isReady, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isReady) {
      return;
    }

    router.replace(isAuthenticated ? "/region" : "/login");
  }, [isAuthenticated, isReady, router]);

  return (
    <div className="flex min-h-svh items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-primary" />
    </div>
  );
}
