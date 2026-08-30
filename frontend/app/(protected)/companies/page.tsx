'use client';

import { useEffect, useState, useCallback } from 'react';
import { 
  ApiError, 
  listCompanies, 
  syncCompanyToHubspot, 
  bulkSyncToHubspot,
  updateCompanyStatus,
  type Company 
} from '@/lib/api';
import { StatusBadge } from '@/components/StatusBadge';
import { useAuth } from '@/lib/auth-context';

const PAGE_SIZE = 20;

// Industries for the dropdown (in a real app this might come from an API)
const INDUSTRIES = [
  'Software', 'Hardware', 'Manufacturing', 'Roofing', 'Garage Door Repair',
  'Plumbing', 'HVAC', 'Construction', 'Consulting', 'Retail', 'Other'
];

export default function CompaniesPage() {
  const { user } = useAuth();
  const [page, setPage] = useState(1);
  const [companies, setCompanies] = useState<Company[] | null>(null);
  const [totalPages, setTotalPages] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [syncing, setSyncing] = useState(false);
  const [actionId, setActionId] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [industryFilter, setIndustryFilter] = useState('');
  const [searchFilter, setSearchFilter] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchFilter);
      setPage(1); // Reset page on search change
    }, 500);
    return () => clearTimeout(handler);
  }, [searchFilter]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [statusFilter, industryFilter]);

  const loadCompanies = useCallback(async (cancelled: { value: boolean }) => {
    setLoading(true);
    try {
      const result = await listCompanies(
        page, 
        PAGE_SIZE, 
        statusFilter || undefined, 
        industryFilter || undefined, 
        debouncedSearch || undefined
      );
      if (cancelled.value) return;
      setCompanies(result.items);
      setTotalPages(Math.max(result.total_pages, 1));
      setError(null);
    } catch (err) {
      if (cancelled.value) return;
      if (err instanceof ApiError && err.status === 404) {
           setError("The GET /companies endpoint is not implemented yet on the backend.");
      } else {
           setError(err instanceof ApiError ? err.message : 'Something went wrong while fetching companies.');
      }
    } finally {
      if (!cancelled.value) {
        setLoading(false);
      }
    }
  }, [page, statusFilter, industryFilter, debouncedSearch]);

  useEffect(() => {
    const cancelled = { value: false };
    loadCompanies(cancelled);
    setSelectedIds(new Set());
    return () => {
      cancelled.value = true;
    };
  }, [loadCompanies]);

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
      setActionId(companyId);
      setError(null);
      await syncCompanyToHubspot(companyId);
      setCompanies(prev => prev?.map(c => 
        c.id === companyId ? { ...c, status: 'HUBSPOT' } : c
      ) ?? null);
      alert('Successfully synced company to HubSpot!');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to sync company.');
    } finally {
      setActionId(null);
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

  const handleStatusUpdate = async (companyId: string, newStatus: string) => {
    try {
      setActionId(companyId);
      setError(null);
      const updatedCompany = await updateCompanyStatus(companyId, newStatus);
      setCompanies(prev => prev?.map(c => 
        c.id === companyId ? { ...c, status: updatedCompany.status } : c
      ) ?? null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to update company status.');
    } finally {
      setActionId(null);
    }
  };

  const renderActions = (company: Company) => {
    if (['RAW', 'CLEANED', 'ENRICHED', 'READY'].includes(company.status)) {
      if (user.role !== 'admin') return null;
      return (
        <button
          onClick={() => handleSingleSync(company.id)}
          disabled={actionId === company.id}
          className="text-primary-600 font-medium hover:text-primary-700 disabled:opacity-50 text-xs uppercase tracking-wide"
        >
          {actionId === company.id ? 'Processing...' : 'Sync to HubSpot'}
        </button>
      );
    } else {
      return (
        <select
          value={company.status}
          onChange={(e) => handleStatusUpdate(company.id, e.target.value)}
          disabled={actionId === company.id}
          className="text-xs uppercase tracking-wide rounded border-neutral-300 py-1 pl-2 pr-6 focus:border-primary-500 focus:ring-primary-500 disabled:opacity-50"
        >
          <option value="HUBSPOT">HubSpot</option>
          <option value="CONTACTED">Contacted</option>
          <option value="QUALIFIED">Qualified</option>
          <option value="CUSTOMER">Customer</option>
        </select>
      );
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl">Companies</h1>
        {user.role === 'admin' && (
          <button 
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
            onClick={handleBulkSync}
            disabled={selectedIds.size === 0 || syncing}
          >
            {syncing ? 'Syncing...' : `Sync Selected (${selectedIds.size})`}
          </button>
        )}
      </div>
      
      {/* Filter Bar */}
      <div className="grid gap-4 md:grid-cols-3">
        <div>
          <label className="sr-only" htmlFor="search">Search</label>
          <input
            id="search"
            type="text"
            placeholder="Search by name, website, city..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="w-full rounded-lg border-neutral-300 text-sm focus:border-primary-500 focus:ring-primary-500"
          />
        </div>
        <div>
          <label className="sr-only" htmlFor="status">Status</label>
          <select
            id="status"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full rounded-lg border-neutral-300 text-sm focus:border-primary-500 focus:ring-primary-500"
          >
            <option value="">All Statuses</option>
            <option value="RAW">Raw</option>
            <option value="CLEANED">Cleaned</option>
            <option value="ENRICHED">Enriched</option>
            <option value="READY">Ready</option>
            <option value="HUBSPOT">HubSpot</option>
            <option value="CONTACTED">Contacted</option>
            <option value="QUALIFIED">Qualified</option>
            <option value="CUSTOMER">Customer</option>
          </select>
        </div>
        <div>
          <label className="sr-only" htmlFor="industry">Industry</label>
          <select
            id="industry"
            value={industryFilter}
            onChange={(e) => setIndustryFilter(e.target.value)}
            className="w-full rounded-lg border-neutral-300 text-sm focus:border-primary-500 focus:ring-primary-500"
          >
            <option value="">All Industries</option>
            {INDUSTRIES.map(ind => (
              <option key={ind} value={ind}>{ind}</option>
            ))}
          </select>
        </div>
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
                        {renderActions(company)}
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
            No companies found matching filters.
          </p>
        )}
      </div>
    </div>
  );
}
