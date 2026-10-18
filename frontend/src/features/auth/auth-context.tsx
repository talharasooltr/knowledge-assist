"use client";

import { createContext, type ReactNode, useContext, useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";

export type UserRole = "user" | "admin";

type AuthState = { role: UserRole; username: string };
type SessionResponse = { authenticated: false } | ({ authenticated: true } & AuthState);
type LoginResponse = { authenticated: true } & AuthState;
type AuthContextValue = AuthState & {
  ready: boolean;
  signedIn: boolean;
  error: string;
  signIn: (username: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthState | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    window.sessionStorage.removeItem("knowledge-auth");
    window.sessionStorage.removeItem("knowledge-role");
    window.sessionStorage.removeItem("knowledge-user");
    void apiRequest<SessionResponse>("/auth/session")
      .then((result) => {
        if (active) {
          setSession(result.authenticated ? { role: result.role, username: result.username } : null);
        }
      })
      .catch((caught) => {
        if (active) setError(caught instanceof Error ? caught.message : "Unable to restore your session.");
      })
      .finally(() => {
        if (active) setReady(true);
      });

    return () => {
      active = false;
    };
  }, []);

  async function signIn(username: string, password: string) {
    const normalizedUsername = username.trim();
    const result = await apiRequest<LoginResponse>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: normalizedUsername, password }),
    });
    setSession({ role: result.role, username: result.username });
    setError("");
  }

  async function signOut() {
    await apiRequest("/auth/logout", { method: "POST" });
    setSession(null);
    setError("");
  }

  return (
    <AuthContext.Provider value={{
      role: session?.role ?? "user",
      username: session?.username ?? "",
      ready,
      signedIn: Boolean(session),
      error,
      signIn,
      signOut,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider.");
  return context;
}
