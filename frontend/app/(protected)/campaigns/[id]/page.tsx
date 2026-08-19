'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ApiError, getCampaign, type Campaign } from '@/lib/api';

// Stub detail page — just resolves and shows the campaign name so
// /campaigns/{id} links from the dashboard and campaign list have
// somewhere real to land. The full analytics/detail view (status
// timeline, company list, job history, etc.) is a later prompt.
export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const result = await getCampaign(params.id);
        if (!cancelled) setCampaign(result);
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setError('Campaign not found.');
        } else {
          setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [params.id]);

  return (
    <div className="space-y-4">
      <Link href="/campaigns" className="text-sm font-medium text-primary-600 hover:text-primary-700">
        ← Back to Campaigns
      </Link>

      <div className="card max-w-md p-6">
        {loading ? (
          <p className="text-sm text-neutral-500">Loading campaign…</p>
        ) : error ? (
          <p role="alert" className="text-sm text-danger-700">
            {error}
          </p>
        ) : (
          <>
            <h1 className="text-xl">{campaign?.name}</h1>
            <p className="mt-1 text-sm text-neutral-500">
              Full campaign detail and analytics are coming in a later prompt.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
