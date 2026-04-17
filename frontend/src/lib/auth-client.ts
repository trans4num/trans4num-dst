"use client";

import { PUBLIC_CONFIG } from "@/lib/public-config";

export const AUTH_STORAGE_KEY = "trans4num-auth";
const EXPIRY_BUFFER_MS = 60 * 1000;

export type AuthSession = {
  token: string;
  expiresAt: number;
  tokenType?: string;
};

type LoginResponse = {
  token: string;
  tokenType?: string;
  expiresAt: number;
};

const normalizeExpiry = (expiresAt: number) => {
  return expiresAt < 1_000_000_000_000 ? expiresAt * 1000 : expiresAt;
};

export const getBackendApiBaseUrl = () => {
  return PUBLIC_CONFIG.apiBaseUrl.replace(/\/+$/, "");
};

export const isSessionValid = (session?: AuthSession | null) => {
  if (!session?.token) {
    return false;
  }

  return normalizeExpiry(session.expiresAt) - Date.now() > EXPIRY_BUFFER_MS;
};

export const readSession = (): AuthSession | null => {
  if (typeof window === "undefined") {
    return null;
  }

  const rawSession = window.sessionStorage.getItem(AUTH_STORAGE_KEY);

  if (!rawSession) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawSession) as AuthSession;
    const session = {
      ...parsed,
      expiresAt: normalizeExpiry(parsed.expiresAt),
    };

    if (!isSessionValid(session)) {
      clearSession();
      return null;
    }

    return session;
  } catch {
    clearSession();
    return null;
  }
};

export const writeSession = (session: AuthSession) => {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(
    AUTH_STORAGE_KEY,
    JSON.stringify({
      ...session,
      expiresAt: normalizeExpiry(session.expiresAt),
    }),
  );
};

export const clearSession = () => {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.removeItem(AUTH_STORAGE_KEY);
};

export const loginWithPassword = async (username: string, password: string): Promise<AuthSession> => {
  const response = await fetch(`${getBackendApiBaseUrl()}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new Error(data?.message ?? "Invalid username or password");
  }

  const data = (await response.json()) as LoginResponse;

  return {
    token: data.token,
    tokenType: data.tokenType ?? "Bearer",
    expiresAt: normalizeExpiry(data.expiresAt),
  };
};
