'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavLink {
  label: string;
  href: string;
}

interface NavGroup {
  label: string;
  children: NavLink[];
}

type NavItem = NavLink | NavGroup;

function isGroup(item: NavItem): item is NavGroup {
  return 'children' in item;
}

// Mirrors frontend/app/ under the (protected) group — see architecture
// doc section 4. Add a link here whenever a new top-level section is
// added under app/(protected)/.
const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', href: '/dashboard' },
  { label: 'Campaigns', href: '/campaigns' },
  { label: 'Companies', href: '/companies' },
  { label: 'Contacts', href: '/contacts' },
  {
    label: 'Accounts',
    children: [
      { label: 'Apify', href: '/accounts/apify' },
      { label: 'Apollo', href: '/accounts/apollo' },
    ],
  },
  { label: 'HubSpot', href: '/hubspot' },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function linkClasses(active: boolean): string {
  return [
    'block rounded-lg px-3 py-2 text-sm font-medium transition-colors',
    active
      ? 'bg-primary-50 text-primary-700'
      : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900',
  ].join(' ');
}

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="w-56 shrink-0 border-r border-neutral-200 bg-white px-3 py-6">
      <ul className="space-y-1">
        {NAV_ITEMS.map((item) =>
          isGroup(item) ? (
            <li key={item.label}>
              <p className="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-neutral-400">
                {item.label}
              </p>
              <ul className="space-y-1">
                {item.children.map((child) => (
                  <li key={child.href}>
                    <Link href={child.href} className={`ml-3 ${linkClasses(isActive(pathname, child.href))}`}>
                      {child.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </li>
          ) : (
            <li key={item.href}>
              <Link href={item.href} className={linkClasses(isActive(pathname, item.href))}>
                {item.label}
              </Link>
            </li>
          ),
        )}
      </ul>
    </nav>
  );
}
