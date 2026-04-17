"use client";

import { clearSession, getBackendApiBaseUrl, readSession } from "@/lib/auth-client";

type ApiFetchOptions = Omit<RequestInit, "headers"> & {
  headers?: HeadersInit;
};

const createHeaders = (token: string, headers?: HeadersInit) => {
  const requestHeaders = new Headers(headers);

  requestHeaders.set("Authorization", `Bearer ${token}`);

  if (!requestHeaders.has("Content-Type")) {
    requestHeaders.set("Content-Type", "application/json");
  }

  return requestHeaders;
};

export const apiFetch = async (path: string, options: ApiFetchOptions = {}) => {
  const session = readSession();

  if (!session) {
    throw new Error("Authentication required");
  }

  const response = await fetch(`${getBackendApiBaseUrl()}${path}`, {
    ...options,
    headers: createHeaders(session.token, options.headers),
  });

  if (response.status === 401) {
    clearSession();

    if (typeof window !== "undefined") {
      window.location.replace("/login");
    }

    throw new Error("Session expired");
  }

  return response;
};
