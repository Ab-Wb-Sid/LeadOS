import type { ReactNode } from 'react';
import { AuthProvider } from '@/lib/auth-context';
import { AppShell } from '@/components/AppShell';

// Everything under app/(protected)/ renders through here. The (protected)
// segment is a route group, so it doesn't appear in the URL: pages here
// still serve at /dashboard, /campaigns, etc., not /protected/dashboard.
//
// AuthProvider gates on the user being logged in (redirecting to /login
// otherwise) and only then renders AppShell — the nav bar + sidebar shell
// — around the page content. So every page added under this group gets
// the shell automatically, with zero per-page wiring.
export default function ProtectedLayout({ children }: { children: ReactNode }) {
  return (
    <AuthProvider>
      <AppShell>{children}</AppShell>
    </AuthProvider>
  );
}
