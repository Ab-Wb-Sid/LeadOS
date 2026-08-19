import type { CampaignStatus } from '@/lib/api';

// Single source of truth for status -> badge color, used identically on
// the dashboard's "Recent Campaigns" table and the full campaigns list.
// Scheme: PENDING is neutral (queued, nothing happening yet), the three
// in-progress stages (SCRAPING/ENRICHING/SYNCING) are all "info" since
// they're all "actively running" from a glance-at-the-table perspective,
// COMPLETED is success, FAILED is danger.
const STATUS_BADGE_CLASS: Record<CampaignStatus, string> = {
  PENDING: 'badge-neutral',
  SCRAPING: 'badge-info',
  ENRICHING: 'badge-info',
  SYNCING: 'badge-info',
  COMPLETED: 'badge-success',
  FAILED: 'badge-danger',
};

const STATUS_LABEL: Record<CampaignStatus, string> = {
  PENDING: 'Pending',
  SCRAPING: 'Scraping',
  ENRICHING: 'Enriching',
  SYNCING: 'Syncing',
  COMPLETED: 'Completed',
  FAILED: 'Failed',
};

interface StatusBadgeProps {
  status: string;
}

/** Renders a campaign status as a colored pill. Falls back to a neutral
 * badge with the raw string for any status value it doesn't recognize,
 * so this never throws on unexpected backend data. */
export function StatusBadge({ status }: StatusBadgeProps) {
  const known = status as CampaignStatus;
  const className = STATUS_BADGE_CLASS[known] ?? 'badge-neutral';
  const label = STATUS_LABEL[known] ?? status;

  return <span className={className}>{label}</span>;
}
