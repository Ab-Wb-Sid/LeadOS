import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Fast, edge-safe pre-check: redirects to /login if the auth cookie is
// missing entirely. This only checks *presence*, not validity — the JWT
// is signed with a backend-only secret this middleware doesn't have, so
// an expired or tampered token still passes here. That's fine: the real
// check is the getMe() call in app/(protected)/layout.tsx (via
// AuthProvider), which hits GET /auth/me and redirects on a 401. Keep
// both — this middleware just avoids a flash of the protected page for
// the common case of "no cookie at all".
const COOKIE_NAME = 'access_token';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (!request.cookies.has(COOKIE_NAME)) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

// Mirrors the top-level routes under app/(protected)/ — see the NAV_ITEMS
// list in components/Sidebar.tsx and architecture doc section 4. Add a
// pattern here whenever a new top-level protected route is added.
export const config = {
  matcher: [
    '/dashboard/:path*',
    '/campaigns/:path*',
    '/companies/:path*',
    '/contacts/:path*',
    '/accounts/:path*',
    '/hubspot/:path*',
  ],
};
