/** 4210 -> "4,210". Used for stat cards and count columns everywhere. */
export function formatNumber(value: number): string {
  return value.toLocaleString('en-US');
}

/** ISO timestamp -> "Aug 20, 2026". Used for "created" columns. */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}
