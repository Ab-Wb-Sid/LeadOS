'use client';

import { useEffect, useState } from 'react';
import { 
  ApiError, 
  listCompanies, 
  syncCompanyToHubspot, 
  bulkSyncToHubspot, 
  type Company 
} from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';

const PAGE_SIZE = 20;

export default function CompaniesPage() {
  const [page, setPage] = useState(1);
  const [companies, setCompanies] = useState<Company[] | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [syncing, setSyncing] = useState(false);
  const [syncingId, setSyncingId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      try {
        const result = await listCompanies(page, PAGE_SIZE);
        if (cancelled) return;
        setCompanies(result.items);
        setTotalPages(Math.max(result.total_pages, 1));
        setError(null);
      } catch (err) {
        if (cancelled) return;
        // Handle gracefully if GET /companies isn't fully implemented in backend yet
        if (err instanceof ApiError && err.status === 404) {
             setError("The GET /companies endpoint is not implemented yet on the backend.");
        } else {
             setError(err instanceof ApiError ? err.message : 'Something went wrong while fetching companies.');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    setSelectedIds(new Set());

    return () => {
      cancelled = true;
    };
  }, [page]);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!companies) return;
    if (e.target.checked) {
      setSelectedIds(new Set(companies.map(c => c.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectOne = (id: string, checked: boolean) => {
    const next = new Set(selectedIds);
    if (checked) next.add(id);
    else next.delete(id);
    setSelectedIds(next);
  };

  const handleSingleSync = async (companyId: string) => {
    try {
      setSyncingId(companyId);
      setError(null);
      await syncCompanyToHubspot(companyId);
      setCompanies(prev => prev?.map(c => 
        c.id === companyId ? { ...c, status: 'HUBSPOT' } : c
      ) ?? null);
      alert('Successfully synced company to HubSpot!');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to sync company.');
    } finally {
      setSyncingId(null);
    }
  };

  const handleBulkSync = async () => {
    if (selectedIds.size === 0) return;
    try {
      setSyncing(true);
      setError(null);
      await bulkSyncToHubspot(Array.from(selectedIds));
      setCompanies(prev => prev?.map(c => 
        selectedIds.has(c.id) ? { ...c, status: 'HUBSPOT' } : c
      ) ?? null);
      alert(`Successfully synced ${selectedIds.size} companies to HubSpot!`);
      setSelectedIds(new Set());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to bulk sync companies.');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl">Companies</h1>
        <button 
          className="btn-primary flex items-center gap-2 disabled:opacity-50"
          onClick={handleBulkSync}
          disabled={selectedIds.size === 0 || syncing}
        >
          {syncing ? 'Syncing...' : `Sync Selected (${selectedIds.size})`}
        </button>
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-danger-50 px-3 py-2 text-sm text-danger-700">
          {error}
        </p>
      )}

      <div className="card">
        {loading ? (
          <p className="px-5 py-6 text-sm text-neutral-500">Loading companies…</p>
        ) : companies && companies.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead>
                  <tr className="border-b border-neutral-200 text-xs uppercase tracking-wide text-neutral-500">
                    <th className="px-5 py-3 w-10">
                      <input 
                        type="checkbox" 
                        className="rounded border-neutral-300 text-primary-600 focus:ring-primary-600"
                        checked={selectedIds.size > 0 && selectedIds.size === companies.length}
                        onChange={handleSelectAll}
                      />
                    </th>
                    <th className="px-5 py-3 font-medium">Name</th>
                    <th className="px-5 py-3 font-medium">Industry</th>
                    <th className="px-5 py-3 font-medium">Domain</th>
                    <th className="px-5 py-3 font-medium">Status</th>
                    <th className="px-5 py-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {companies.map((company) => (
                    <tr key={company.id} className="border-b border-neutral-100 last:border-0 hover:bg-neutral-50">
                      <td className="px-5 py-3">
                        <input 
                          type="checkbox" 
                          className="rounded border-neutral-300 text-primary-600 focus:ring-primary-600"
                          checked={selectedIds.has(company.id)}
                          onChange={(e) => handleSelectOne(company.id, e.target.checked)}
                        />
                      </td>
                      <td className="px-5 py-3 font-medium text-neutral-900">{company.name}</td>
                      <td className="px-5 py-3 text-neutral-600">{company.industry || '—'}</td>
                      <td className="px-5 py-3 text-neutral-600">{company.normalized_domain || '—'}</td>
                      <td className="px-5 py-3">
                        <StatusBadge status={company.status} />
                      </td>
                      <td className="px-5 py-3 text-right">
                        <button
                          onClick={() => handleSingleSync(company.id)}
                          disabled={syncingId === company.id}
                          className="text-primary-600 font-medium hover:text-primary-700 disabled:opacity-50 text-xs uppercase tracking-wide"
                        >
                          {syncingId === company.id ? 'Syncing...' : 'Sync to HubSpot'}
                        </button>
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
            No companies found. 
          </p>
        )}
      </div>
    </div>
  );
}
