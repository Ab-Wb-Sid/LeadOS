'use client';

import { useState } from 'react';
import type { FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { ApiError, createCampaign } from '@/lib/api';

// The architecture doc's section 6 wireframe only shows Industry/Country/
// State/Max Leads, but backend/app/schemas/campaign.py CampaignCreate
// also requires `name` (max 200 chars) — there's no server-side default,
// so a Campaign Name field is added here to make the form actually
// submittable. Everything else follows the wireframe exactly.
export default function NewCampaignPage() {
  const router = useRouter();

  const [name, setName] = useState('');
  const [industry, setIndustry] = useState('');
  const [country, setCountry] = useState('');
  const [state, setState] = useState('');
  const [maxLeads, setMaxLeads] = useState('500');

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  function validate(): string | null {
    if (!name.trim()) return 'Campaign name is required.';
    if (!industry.trim()) return 'Industry is required.';
    const parsedMaxLeads = Number(maxLeads);
    if (!Number.isInteger(parsedMaxLeads) || parsedMaxLeads <= 0) {
      return 'Max leads must be a whole number greater than 0.';
    }
    return null;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    try {
      await createCampaign({
        name: name.trim(),
        industry: industry.trim(),
        country: country.trim() || null,
        state: state.trim() || null,
        max_leads: Number(maxLeads),
      });
      router.push('/campaigns');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <Link href="/campaigns" className="text-sm font-medium text-primary-600 hover:text-primary-700">
        ← Back to Campaigns
      </Link>

      <div className="card max-w-lg p-8">
        <h1 className="text-xl">New Campaign</h1>
        <p className="mt-1 text-sm text-neutral-500">
          This kicks off a scrape job (n8n integration is stubbed for now — see backend
          services/n8n_trigger.py).
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-neutral-700">
              Campaign Name
            </label>
            <input
              id="name"
              name="name"
              type="text"
              required
              maxLength={200}
              value={name}
              onChange={(event) => setName(event.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm
                         text-neutral-900 placeholder:text-neutral-400
                         focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Garage Door USA"
            />
          </div>

          <div>
            <label htmlFor="industry" className="block text-sm font-medium text-neutral-700">
              Industry
            </label>
            <input
              id="industry"
              name="industry"
              type="text"
              required
              maxLength={120}
              value={industry}
              onChange={(event) => setIndustry(event.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm
                         text-neutral-900 placeholder:text-neutral-400
                         focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="Garage Door Repair"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="country" className="block text-sm font-medium text-neutral-700">
                Country
              </label>
              <input
                id="country"
                name="country"
                type="text"
                maxLength={80}
                value={country}
                onChange={(event) => setCountry(event.target.value)}
                className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm
                           text-neutral-900 placeholder:text-neutral-400
                           focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                placeholder="United States"
              />
            </div>

            <div>
              <label htmlFor="state" className="block text-sm font-medium text-neutral-700">
                State
              </label>
              <input
                id="state"
                name="state"
                type="text"
                maxLength={80}
                value={state}
                onChange={(event) => setState(event.target.value)}
                className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm
                           text-neutral-900 placeholder:text-neutral-400
                           focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                placeholder="Texas"
              />
            </div>
          </div>

          <div>
            <label htmlFor="max_leads" className="block text-sm font-medium text-neutral-700">
              Max Leads
            </label>
            <input
              id="max_leads"
              name="max_leads"
              type="number"
              min={1}
              step={1}
              required
              value={maxLeads}
              onChange={(event) => setMaxLeads(event.target.value)}
              className="mt-1 w-full rounded-lg border border-neutral-300 px-3 py-2 text-sm
                         text-neutral-900 placeholder:text-neutral-400
                         focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              placeholder="500"
            />
          </div>

          {error && (
            <p role="alert" className="rounded-lg bg-danger-50 px-3 py-2 text-sm text-danger-700">
              {error}
            </p>
          )}

          <button type="submit" disabled={submitting} className="btn-primary w-full">
            {submitting ? 'Starting…' : 'Start Campaign'}
          </button>
        </form>
      </div>
    </div>
  );
}
