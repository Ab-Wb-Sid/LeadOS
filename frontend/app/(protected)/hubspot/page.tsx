'use client';

import { useEffect, useState } from 'react';
import { 
  ApiError, 
  getHubspotLogs, 
  type HubspotSyncLogOut 
} from '@/lib/api';
import { formatDate } from '@/lib/format';

const PAGE_SIZE = 20;

export default function HubSpotPage() {
  const [page, setPage] = useState(1);
  const [logs, setLogs] = useState<HubspotSyncLogOut[] | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const result = await getHubspotLogs(page, PAGE_SIZE);
        if (cancelled) return;
        setLogs(result.items);
        setTotalPages(Math.max(result.total_pages, 1));
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof ApiError ? err.message : 'Something went wrong while loading logs.');
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [page]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl">HubSpot Sync Logs</h1>
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-danger-50 px-3 py-2 text-sm text-danger-700">
          {error}
        </p>
      )}

      <div className="card">
        {loading ? (
          <p className="px-5 py-6 text-sm text-neutral-500">Loading logs…</p>
        ) : logs && logs.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead>
                  <tr className="border-b border-neutral-200 text-xs uppercase tracking-wide text-neutral-500">
                    <th className="px-5 py-3 font-medium">Company</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium">Error Message</th>
                    <th className="px-5 py-3 font-medium">Synced At</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-b border-neutral-100 last:border-0 hover:bg-neutral-50">
                      <td className="px-5 py-3 font-medium text-neutral-900">
                        {log.company_name || 'Unknown Company'}
                      </td>
                      <td className="px-5 py-3">
                        <span className={`
                          ${log.sync_status === 'SUCCESS' ? 'badge-success' : 
                            log.sync_status === 'FAILED' ? 'badge-danger' : 
                            'badge-neutral'}
                        `}>
                          {log.sync_status || 'UNKNOWN'}
                        </span>
                      </td>
                      <td className="px-5 py-3 text-neutral-600 max-w-md truncate">
                        {log.error_message || '—'}
                      </td>
                      <td className="px-5 py-3 text-neutral-600">
                        {formatDate(log.synced_at)}
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
            No HubSpot sync logs found.
          </p>
        )}
      </div>
    </div>
  );
}
