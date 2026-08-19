interface ComingSoonProps {
  title: string;
}

/** Placeholder body for sidebar destinations that don't have a real page yet. */
export function ComingSoon({ title }: ComingSoonProps) {
  return (
    <div className="card max-w-md p-6">
      <h1 className="text-xl">{title}</h1>
      <p className="mt-1 text-sm text-neutral-500">This page is coming in a later prompt.</p>
    </div>
  );
}
