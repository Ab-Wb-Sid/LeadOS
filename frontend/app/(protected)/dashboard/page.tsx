'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ApiError,
  getDashboardStats,
  listCampaigns,
  type Campaign,
  type DashboardStats,
} from '@/lib/api';
import { formatNumber } from '@/lib/format';
import { StatusBadge } from '@/components/StatusBadge';

// How many campaigns to show in the "Recent Campaigns" strip — the full
// list lives at /campaigns.
const RECENT_CAMPAIGNS_LIMIT = 5;

interface StatCard {
  label: string;
  value: number;
}

// AppShell (nav bar + sidebar + page padding) is applied by
// app/(protected)/layout.tsx, so this only needs to render its own content.
export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [campaigns, setCampaigns] = useState<Campaign[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [statsResult, campaignsResult] = await Promise.all([
          getDashboardStats(),
          listCampaigns(1, RECENT_CAMPAIGNS_LIMIT),
        ]);
        if (cancelled) return;
        setStats(statsResult);
        setCampaigns(campaignsResult.items);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const statCards: StatCard[] = stats
    ? [
        { label: 'Total Scraped', value: stats.total_scraped },
        { label: 'Enriched', value: stats.total_enriched },
        { label: 'Imported', value: stats.total_imported },
        { label: 'Active Jobs', value: stats.active_jobs },
        { label: 'Failed Jobs', value: stats.failed_jobs },
      ]
    : [];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-xl">Dashboard</h1>
        <Link href="/campaigns/new" className="btn-primary">
          + New Campaign
        </Link>
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-danger-50 px-3 py-2 text-sm text-danger-700">
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-sm text-neutral-500">Loading dashboard…</p>
      ) : (
        <>
          {/* Stat cards — architecture doc section 6 wireframe:
              "Total Scraped: 4,210  Enriched: 2,980  Imported: 2,100"
              "Active Jobs: 2         Failed Jobs: 1" */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {statCards.map((card) => (
              <div key={card.label} className="card p-5">
                <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
                  {card.label}
                </p>
                <p className="mt-2 text-2xl font-semibold text-neutral-900">
                  {formatNumber(card.value)}
                </p>
              </div>
            ))}
          </div>

          {/* Recent Campaigns */}
          <div className="card">
            <div className="flex items-center justify-between border-b border-neutral-200 px-5 py-4">
              <h2 className="text-base">Recent Campaigns</h2>
              <Link href="/campaigns" className="text-sm font-medium text-primary-600 hover:text-primary-700">
                View all
              </Link>
            </div>

            {campaigns && campaigns.length > 0 ? (
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-neutral-200 text-xs uppercase tracking-wide text-neutral-500">
                    <th className="px-5 py-3 font-medium">Name</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Scraped → Enriched → Imported</th>
                  </tr>
                </thead>
                <tbody>
                  {campaigns.map((campaign) => (
                    <tr key={campaign.id} className="border-b border-neutral-100 last:border-0">
                      <td className="px-5 py-3">
                        <Link
                          href={`/campaigns/${campaign.id}`}
                          className="font-medium text-neutral-900 hover:text-primary-600"
                        >
                          {campaign.name}
                        </Link>
                      </td>
                      <td className="px-5 py-3">
                        <StatusBadge status={campaign.status} />
                      </td>
                      <td className="px-5 py-3 text-neutral-600">
                        {formatNumber(campaign.total_scraped)} → {formatNumber(campaign.total_enriched)} →{' '}
                        {formatNumber(campaign.total_imported)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="px-5 py-6 text-sm text-neutral-500">
                No campaigns yet.{' '}
                <Link href="/campaigns/new" className="font-medium text-primary-600 hover:text-primary-700">
                  Start your first one
                </Link>
                .
              </p>
            )}
          </div>
        </>
      )}
    </div>
  );
}
