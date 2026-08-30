'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { ApiError, listCampaigns, type Campaign } from '@/lib/api';
import { formatDate, formatNumber } from '@/lib/format';
import { StatusBadge } from '@/components/StatusBadge';

const PAGE_SIZE = 20;

export default function CampaignsPage() {
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [campaigns, setCampaigns] = useState<Campaign[] | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout>;

    async function load() {
      try {
        const result = await listCampaigns(page, PAGE_SIZE);
        if (cancelled) return;
        setCampaigns(result.items);
        setTotalPages(Math.max(result.total_pages, 1));
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
      } finally {
        if (!cancelled) {
          setLoading(false);
          timeout = setTimeout(load, 5000); // Poll every 5 seconds after request finishes
        }
      }
    }

    load();

    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [page]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl">Campaigns</h1>
        {user.role === 'admin' && (
          <Link href="/campaigns/new" className="btn-primary">
            + New Campaign
          </Link>
        )}
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-danger-50 px-3 py-2 text-sm text-danger-700">
          {error}
        </p>
      )}

      <div className="card">
        {loading ? (
          <p className="px-5 py-6 text-sm text-neutral-500">Loading campaigns…</p>
        ) : campaigns && campaigns.length > 0 ? (
          <>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-neutral-200 text-xs uppercase tracking-wide text-neutral-500">
                  <th className="px-5 py-3 font-medium">Name</th>
                  <th className="px-5 py-3 font-medium">Industry</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Scraped → Enriched → Imported</th>
                  <th className="px-5 py-3 font-medium">Created</th>
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
                    <td className="px-5 py-3 text-neutral-600">{campaign.industry}</td>
                    <td className="px-5 py-3">
                      <StatusBadge status={campaign.status} />
                    </td>
                    <td className="px-5 py-3 text-neutral-600">
                      {formatNumber(campaign.total_scraped)} → {formatNumber(campaign.total_enriched)} →{' '}
                      {formatNumber(campaign.total_imported)}
                    </td>
                    <td className="px-5 py-3 text-neutral-600">{formatDate(campaign.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="flex items-center justify-between border-t border-neutral-200 px-5 py-4">
              <p className="text-sm text-neutral-500">
                Page {page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-700
                             transition-colors hover:bg-neutral-100 disabled:opacity-50 disabled:pointer-events-none"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-700
                             transition-colors hover:bg-neutral-100 disabled:opacity-50 disabled:pointer-events-none"
                >
                  Next
                </button>
              </div>
            </div>
          </>
        ) : (
          <p className="px-5 py-6 text-sm text-neutral-500">
            No campaigns yet.{' '}
            {user.role === 'admin' && (
              <>
                <Link href="/campaigns/new" className="font-medium text-primary-600 hover:text-primary-700">
                  Start your first one
                </Link>
                .
              </>
            )}
          </p>
        )}
      </div>
    </div>
  );
}
