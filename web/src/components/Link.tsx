import { memo } from 'react';

function Link({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener"
      className="text-sm font-semibold text-emerald-800 underline underline-offset-2 dark:text-emerald-500"
    >
      {children}
    </a>
  );
}

export default memo(Link);
