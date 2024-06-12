export function Link({
  href,
  rel,
  children,
}: {
  href: string;
  rel?: string;
  children: React.ReactNode;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel={`noopener ${rel}`}
      className="text-sm font-semibold text-emerald-800 underline underline-offset-2 dark:text-emerald-500"
    >
      {children}
    </a>
  );
}
