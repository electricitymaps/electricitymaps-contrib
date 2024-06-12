export function Link({ href, linkText }: { href: string; linkText: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-sm font-semibold text-emerald-800 underline underline-offset-2 dark:text-emerald-500"
    >
      {linkText}
    </a>
  );
}
