"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  clearSession,
  type AuthSession,
  isSessionValid,
  loginWithPassword,
  readSession,
  writeSession,
} from "@/lib/auth-client";

type AuthContextValue = {
  isReady: boolean;
  session: AuthSession | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(null);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    const currentSession = readSession();
    setSession(currentSession);
    setIsReady(true);
  }, []);

  useEffect(() => {
    if (!session || !isSessionValid(session)) {
      return;
    }

    const timeout = window.setTimeout(() => {
      clearSession();
      setSession(null);
      window.location.replace("/login");
    }, Math.max(session.expiresAt - Date.now(), 0));

    return () => window.clearTimeout(timeout);
  }, [session]);

  const value = useMemo<AuthContextValue>(
    () => ({
      isReady,
      session,
      isAuthenticated: isSessionValid(session),
      login: async (username: string, password: string) => {
        const nextSession = await loginWithPassword(username, password);
        writeSession(nextSession);
        setSession(nextSession);
      },
      logout: () => {
        clearSession();
        setSession(null);
      },
    }),
    [isReady, session],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
};
