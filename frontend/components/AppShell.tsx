'use client';

import type { ReactNode } from 'react';
import { TopNav } from './TopNav';
import { Sidebar } from './Sidebar';

// Renders once AuthProvider has confirmed the user is logged in — see
// app/(protected)/layout.tsx. TopNav and Sidebar both call useAuth()/usePathname(),
// so this must stay a client component.
export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-neutral-50">
      <TopNav />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-8">{children}</main>
      </div>
    </div>
  );
}
