"use client";

import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/components/auth-provider";
import { LocaleProvider } from "@/components/locale-provider";

export const Providers = ({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) => {
  return (
    <LocaleProvider>
      <AuthProvider>
        <TooltipProvider delayDuration={0}>
          {children}
          <Toaster />
        </TooltipProvider>
      </AuthProvider>
    </LocaleProvider>
  );
};
