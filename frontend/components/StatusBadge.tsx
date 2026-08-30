import type { CampaignStatus } from '@/lib/api';

const STATUS_BADGE_CLASS: Record<string, string> = {
  // Campaign Statuses
  PENDING: 'badge-neutral',
  SCRAPING: 'badge-info',
  ENRICHING: 'badge-info',
  SYNCING: 'badge-info',
  COMPLETED: 'badge-success',
  FAILED: 'badge-danger',
  // Company Statuses
  RAW: 'badge-neutral',
  CLEANED: 'bg-blue-100 text-blue-800 rounded-full px-2.5 py-0.5 text-xs font-medium',
  ENRICHED: 'bg-indigo-100 text-indigo-800 rounded-full px-2.5 py-0.5 text-xs font-medium',
  READY: 'bg-purple-100 text-purple-800 rounded-full px-2.5 py-0.5 text-xs font-medium',
  HUBSPOT: 'bg-orange-100 text-orange-800 rounded-full px-2.5 py-0.5 text-xs font-medium',
  CONTACTED: 'bg-yellow-100 text-yellow-800 rounded-full px-2.5 py-0.5 text-xs font-medium',
  QUALIFIED: 'bg-emerald-100 text-emerald-800 rounded-full px-2.5 py-0.5 text-xs font-medium',
  CUSTOMER: 'badge-success',
};

const STATUS_LABEL: Record<string, string> = {
  // Campaign Statuses
  PENDING: 'Pending',
  SCRAPING: 'Scraping',
  ENRICHING: 'Enriching',
  SYNCING: 'Syncing',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
  // Company Statuses
  RAW: 'Raw',
  CLEANED: 'Cleaned',
  ENRICHED: 'Enriched',
  READY: 'Ready',
  HUBSPOT: 'HubSpot',
  CONTACTED: 'Contacted',
  QUALIFIED: 'Qualified',
  CUSTOMER: 'Customer',
};

interface StatusBadgeProps {
  status: string;
}

/** Renders a campaign or company status as a colored pill. Falls back to a neutral
 * badge with the raw string for any status value it doesn't recognize. */
export function StatusBadge({ status }: StatusBadgeProps) {
  const className = STATUS_BADGE_CLASS[status] ?? 'badge-neutral';
  const label = STATUS_LABEL[status] ?? status;

  return <span className={className}>{label}</span>;
}
