import Link from 'next/link';

// The sidebar's "Accounts" entry is a group heading (Apify/Apollo are the
// actual links) rather than its own link, but this covers anyone landing
// on the bare /accounts URL directly instead of 404ing on them.
export default function AccountsIndexPage() {
  return (
    <div className="card max-w-md p-6">
      <h1 className="text-xl">Accounts</h1>
      <p className="mt-1 text-sm text-neutral-500">
        Choose an account type:{' '}
        <Link href="/accounts/apify" className="text-primary-600 hover:underline">
          Apify
        </Link>{' '}
        or{' '}
        <Link href="/accounts/apollo" className="text-primary-600 hover:underline">
          Apollo
        </Link>
        .
      </p>
    </div>
  );
}
