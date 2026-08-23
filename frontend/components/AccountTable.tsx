'use client';

import { useState, useEffect } from 'react';
import { Account, AccountCreateInput, listAccounts, createAccount } from '@/lib/api';

interface AccountTableProps {
  provider: 'apify' | 'apollo';
  title: string;
}

const STATUS_BADGE_CLASS: Record<string, string> = {
  ACTIVE: 'badge-success',
  COOLDOWN: 'badge-warning',
  DISABLED: 'badge-danger',
};

export function AccountTable({ provider, title }: AccountTableProps) {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newKey, setNewKey] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    loadAccounts();
  }, [provider]);

  async function loadAccounts() {
    setLoading(true);
    setError(null);
    try {
      const data = await listAccounts(provider);
      setAccounts(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load accounts');
    } finally {
      setLoading(false);
    }
  }

  async function handleAddAccount(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setFormError(null);
    try {
      const payload: AccountCreateInput = {
        name: newName,
        api_key: newKey,
      };
      const created = await createAccount(provider, payload);
      setAccounts((prev) => [...prev, created]);
      setIsModalOpen(false);
      setNewName('');
      setNewKey('');
    } catch (err: any) {
      setFormError(err.message || 'Failed to create account');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-neutral-900">{title}</h1>
        <button onClick={() => setIsModalOpen(true)} className="btn-primary">
          + Add
        </button>
      </div>

      {error && <div className="p-4 rounded-md bg-red-50 text-red-700">{error}</div>}

      <div className="rounded-lg border border-neutral-200 bg-white overflow-hidden">
        <table className="w-full text-left text-sm text-neutral-600">
          <thead className="border-b border-neutral-200 bg-neutral-50 text-neutral-500">
            <tr>
              <th className="px-6 py-4 font-medium">Name</th>
              <th className="px-6 py-4 font-medium">API Key</th>
              <th className="px-6 py-4 font-medium">Credits</th>
              <th className="px-6 py-4 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-200">
            {loading ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-neutral-500">
                  Loading accounts...
                </td>
              </tr>
            ) : accounts.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-neutral-500">
                  No accounts found. Click "+ Add" to create one.
                </td>
              </tr>
            ) : (
              accounts.map((acc) => (
                <tr key={acc.id} className="hover:bg-neutral-50">
                  <td className="px-6 py-4 font-medium text-neutral-900">{acc.name}</td>
                  <td className="px-6 py-4 font-mono text-neutral-500">{acc.api_key}</td>
                  <td className="px-6 py-4">{acc.remaining_credits}</td>
                  <td className="px-6 py-4">
                    <span className={STATUS_BADGE_CLASS[acc.status] || 'badge-neutral'}>
                      {acc.status}
                    </span>
                    {acc.status === 'COOLDOWN' && acc.reset_date && (
                      <span className="ml-2 text-xs text-neutral-400">
                        (Resets: {acc.reset_date})
                      </span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-neutral-900/50 p-4">
          <div className="w-full max-w-md rounded-xl bg-white p-6 shadow-xl">
            <h2 className="text-lg font-bold text-neutral-900 mb-4">Add {title}</h2>
            
            {formError && <div className="mb-4 p-3 rounded-md bg-red-50 text-sm text-red-700">{formError}</div>}
            
            <form onSubmit={handleAddAccount} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">Account Name</label>
                <input
                  type="text"
                  required
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="block w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="e.g. Primary Account"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-neutral-700 mb-1">API Key</label>
                <input
                  type="text"
                  required
                  value={newKey}
                  onChange={(e) => setNewKey(e.target.value)}
                  className="block w-full rounded-md border border-neutral-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  placeholder="Paste your raw API key here"
                />
                <p className="mt-1 text-xs text-amber-600">
                  ⚠️ This key will be encrypted at rest and will not be displayed again after creation.
                </p>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="rounded-md px-4 py-2 text-sm font-medium text-neutral-600 hover:bg-neutral-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="btn-primary"
                >
                  {submitting ? 'Saving...' : 'Save Account'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
