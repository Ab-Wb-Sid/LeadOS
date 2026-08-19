'use client';

import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { getMe, type User } from './api';

interface AuthContextValue {
  user: User;
  /** Re-fetches /auth/me. Call after anything that could change the current user. */
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

/** Read the current user inside any page/component under app/(protected)/. */
export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth() must be used within <AuthProvider>');
  }
  return ctx;
}

/**
 * Client-side auth gate for the (protected) route group.
 *
 * On mount, calls GET /auth/me (via getMe(), which sends the httpOnly
 * cookie automatically). If that succeeds, the user is stored in context
 * and children render. If it throws (401 — no cookie, expired token, or
 * deleted user), we redirect to /login instead of rendering children.
 *
 * This is a client component because httpOnly cookies aren't readable by
 * JS and there's no server-side session store to check synchronously —
 * asking the backend is the actual source of truth. See middleware.ts for
 * the fast, non-authoritative pre-check that avoids most flashes of this
 * loading state.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [checked, setChecked] = useState(false);

  const refreshUser = useCallback(async () => {
    try {
      const me = await getMe();
      setUser(me);
    } catch {
      setUser(null);
      router.replace('/login');
    } finally {
      setChecked(true);
    }
  }, [router]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  if (!checked || !user) {
    // Covers both "still checking" and "check failed, redirect in flight" —
    // never render protected content in either case.
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-50">
        <p className="text-sm text-neutral-500">Checking your session…</p>
      </div>
    );
  }

  return <AuthContext.Provider value={{ user, refreshUser }}>{children}</AuthContext.Provider>;
}
