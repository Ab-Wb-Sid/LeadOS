'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { logout } from '@/lib/api';

export function TopNav() {
  const { user } = useAuth();
  const router = useRouter();
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await logout();
    } catch {
      // Even if /auth/logout fails (network blip, etc.) there's nothing
      // useful to do besides send the user back to /login — the next
      // protected page load re-validates via /auth/me regardless.
    } finally {
      router.replace('/login');
    }
  }

  return (
    <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center justify-between border-b border-neutral-200 bg-white px-6">
      <Link href="/dashboard" className="text-base font-semibold text-neutral-900">
        LeadOS
      </Link>

      <div className="flex items-center gap-4">
        <span className="text-sm text-neutral-600">{user.name}</span>
        <button
          type="button"
          onClick={handleLogout}
          disabled={loggingOut}
          className="btn-primary px-3 py-1.5 text-xs"
        >
          {loggingOut ? 'Logging out…' : 'Log out'}
        </button>
      </div>
    </header>
  );
}
