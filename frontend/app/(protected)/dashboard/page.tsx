'use client';

import { useAuth } from '@/lib/auth-context';

// AppShell (nav bar + sidebar + page padding) is applied by
// app/(protected)/layout.tsx, so this only needs to render its own content.
export default function DashboardPage() {
  const { user } = useAuth();

  return (
    <div className="card max-w-md p-6">
      <h1 className="text-xl">Welcome, {user.name}</h1>
      <p className="mt-1 text-sm text-neutral-500">{user.email}</p>
    </div>
  );
}
