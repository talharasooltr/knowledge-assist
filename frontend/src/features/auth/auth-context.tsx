"use client";

import { createContext, type ReactNode, useContext, useState, useSyncExternalStore } from "react";
import { apiRequest, encodeBasicAuth } from "@/lib/api";

export type UserRole = "user" | "admin";

type AuthState = { auth: string; role: UserRole; username: string };
type AuthContextValue = AuthState & {
  ready: boolean;
  signedIn: boolean;
  signIn: (role: UserRole, username: string, password: string) => Promise<void>;
  signOut: () => void;
};

const SESSION_KEYS = ["knowledge-auth", "knowledge-role", "knowledge-user"];
const AuthContext = createContext<AuthContextValue | null>(null);

function readStoredSession(): AuthState | null {
  if (typeof window === "undefined") return null;
  const auth = window.sessionStorage.getItem(SESSION_KEYS[0]);
  const role = window.sessionStorage.getItem(SESSION_KEYS[1]);
  const username = window.sessionStorage.getItem(SESSION_KEYS[2]);
  if (!auth || (role !== "user" && role !== "admin") || !username) return null;
  return { auth, role, username };
}

function subscribeToNothing(): () => void {
  return () => {};
}

function getClientReady(): boolean {
  return true;
}

function getServerReady(): boolean {
  return false;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthState | null>(readStoredSession);
  const ready = useSyncExternalStore(subscribeToNothing, getClientReady, getServerReady);

  async function signIn(role: UserRole, username: string, password: string) {
    const normalizedUsername = username.trim();
    const auth = encodeBasicAuth(normalizedUsername, password);
    await apiRequest(`/${role}/auth/check`, auth);
    const nextSession = { auth, role, username: normalizedUsername };
    window.sessionStorage.setItem(SESSION_KEYS[0], auth);
    window.sessionStorage.setItem(SESSION_KEYS[1], role);
    window.sessionStorage.setItem(SESSION_KEYS[2], normalizedUsername);
    setSession(nextSession);
  }

  function signOut() {
    SESSION_KEYS.forEach((key) => window.sessionStorage.removeItem(key));
    setSession(null);
  }

  return (
    <AuthContext.Provider value={{
      auth: session?.auth ?? "",
      role: session?.role ?? "user",
      username: session?.username ?? "",
      ready,
      signedIn: Boolean(session),
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