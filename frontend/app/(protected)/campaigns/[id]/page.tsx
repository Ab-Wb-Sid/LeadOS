'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { 
  ApiError, 
  getCampaign, 
  listCampaignCompanies,
  type Campaign, 
  type Company 
} from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';

const PAGE_SIZE = 10;

export default function CampaignDetailPage() {
  const params = useParams<{ id: string }>();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [companies, setCompanies] = useState<Company[] | null>(null);
  
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [campResult, compResult] = await Promise.all([
          getCampaign(params.id),
          listCampaignCompanies(params.id, page, PAGE_SIZE)
        ]);
        
        if (!cancelled) {
          setCampaign(campResult);
          setCompanies(compResult.items);
          setTotalPages(Math.max(compResult.total_pages, 1));
        }
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

    loadData();
    return () => {
      cancelled = true;
    };
  }, [params.id, page]);

  // Order of statuses for consistent display
  const STATUS_ORDER = ['RAW', 'CLEANED', 'ENRICHED', 'READY', 'HUBSPOT', 'CONTACTED', 'QUALIFIED', 'CUSTOMER'];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RAW': return 'bg-neutral-300';
      case 'CLEANED': return 'bg-blue-300';
      case 'ENRICHED': return 'bg-indigo-400';
      case 'READY': return 'bg-purple-500';
      case 'HUBSPOT': return 'bg-orange-400';
      case 'CONTACTED': return 'bg-yellow-400';
      case 'QUALIFIED': return 'bg-green-400';
      case 'CUSTOMER': return 'bg-emerald-600';
      default: return 'bg-neutral-200';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link href="/campaigns" className="text-sm font-medium text-primary-600 hover:text-primary-700 flex items-center gap-1">
          &larr; Back to Campaigns
        </Link>
        
        <button 
          className="rounded-lg bg-neutral-100 px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-200 transition-colors"
          onClick={() => alert('Stub: Rerun functionality coming soon.')}
        >
          Rerun Campaign (Stub)
        </button>
      </div>

      {error ? (
        <div className="card p-6">
          <p role="alert" className="text-sm text-danger-700">{error}</p>
        </div>
      ) : loading && !campaign ? (
        <div className="card p-6">
          <p className="text-sm text-neutral-500">Loading campaign analytics…</p>
        </div>
      ) : campaign && (
        <>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-neutral-900">{campaign.name}</h1>
              <p className="text-sm text-neutral-500 mt-1">
                {campaign.industry} • {campaign.state ? `${campaign.state}, ` : ''}{campaign.country || 'Global'}
              </p>
            </div>
            <StatusBadge status={campaign.status} />
          </div>

          {campaign.status === 'FAILED' && campaign.error_message && (
            <div className="rounded-lg bg-danger-50 p-4 border border-danger-200">
              <h3 className="text-sm font-medium text-danger-800">Campaign Failed</h3>
              <p className="mt-1 text-sm text-danger-700">{campaign.error_message}</p>
            </div>
          )}

          {/* Header Stats */}
          <div className="grid gap-4 md:grid-cols-4">
            <div className="card px-5 py-4">
              <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Target Leads</p>
              <p className="mt-1 text-2xl font-semibold text-neutral-900">{campaign.max_leads}</p>
            </div>
            <div className="card px-5 py-4">
              <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Scraped</p>
              <p className="mt-1 text-2xl font-semibold text-neutral-900">{campaign.total_scraped}</p>
            </div>
            <div className="card px-5 py-4">
              <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Enriched</p>
              <p className="mt-1 text-2xl font-semibold text-neutral-900">{campaign.total_enriched}</p>
            </div>
            <div className="card px-5 py-4">
              <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide">Imported</p>
              <p className="mt-1 text-2xl font-semibold text-neutral-900">{campaign.total_imported}</p>
            </div>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {/* Status Breakdown Chart */}
            <div className="card p-5 md:col-span-1">
              <h2 className="text-base font-semibold text-neutral-900 mb-4">Pipeline Breakdown</h2>
              
              <div className="space-y-3">
                {STATUS_ORDER.map(status => {
                  const count = campaign.status_breakdown?.[status] || 0;
                  const total = Math.max(campaign.total_scraped, 1); // Avoid division by zero
                  const percentage = Math.round((count / total) * 100);
                  
                  return (
                    <div key={status} className="flex items-center gap-3">
                      <div className="w-24 text-xs font-medium text-neutral-600">{status}</div>
                      <div className="flex-1 h-2 bg-neutral-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${getStatusColor(status)}`} 
                          style={{ width: `${Math.min(percentage, 100)}%` }} 
                        />
                      </div>
                      <div className="w-8 text-right text-xs text-neutral-500">{count}</div>
                    </div>
                  );
                })}
              </div>
              
              <div className="mt-6 pt-4 border-t border-neutral-100 text-xs text-neutral-500 space-y-1">
                <p>Created: {new Date(campaign.created_at).toLocaleString()}</p>
                {campaign.completed_at && (
                  <p>Completed: {new Date(campaign.completed_at).toLocaleString()}</p>
                )}
              </div>
            </div>

            {/* Scoped Company List */}
            <div className="card md:col-span-2">
              <div className="border-b border-neutral-200 px-5 py-4 flex items-center justify-between">
                <h2 className="text-base font-semibold text-neutral-900">Companies</h2>
              </div>
              
              {loading && companies === null ? (
                <p className="px-5 py-6 text-sm text-neutral-500">Loading companies…</p>
              ) : companies && companies.length > 0 ? (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm whitespace-nowrap">
                      <thead>
                        <tr className="border-b border-neutral-200 text-xs uppercase tracking-wide text-neutral-500">
                          <th className="px-5 py-3 font-medium">Name</th>
                          <th className="px-5 py-3 font-medium">Domain</th>
                          <th className="px-5 py-3 font-medium">Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {companies.map((company) => (
                          <tr key={company.id} className="border-b border-neutral-100 last:border-0 hover:bg-neutral-50">
                            <td className="px-5 py-3 font-medium text-neutral-900">{company.name}</td>
                            <td className="px-5 py-3 text-neutral-600">{company.normalized_domain || '—'}</td>
                            <td className="px-5 py-3">
                              <StatusBadge status={company.status} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="flex items-center justify-between border-t border-neutral-200 px-5 py-4">
                    <p className="text-sm text-neutral-500">
                      Page {page} of {totalPages}
                    </p>
                    <div className="flex gap-2">
                      <button
                        type="button"
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page <= 1}
                        className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-100 disabled:opacity-50 disabled:pointer-events-none transition-colors"
                      >
                        Previous
                      </button>
                      <button
                        type="button"
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page >= totalPages}
                        className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-100 disabled:opacity-50 disabled:pointer-events-none transition-colors"
                      >
                        Next
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <p className="px-5 py-6 text-sm text-neutral-500">
                  No companies found for this campaign.
                </p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
