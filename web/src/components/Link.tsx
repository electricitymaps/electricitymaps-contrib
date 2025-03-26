import { ExternalLink } from 'lucide-react';
import { memo } from 'react';

function Link({
  href,
  children,
  isExternal,
}: {
  href: string;
  children: React.ReactNode;
  isExternal?: boolean;
}) {
  if (isExternal) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener"
        className="flex w-full items-center justify-between text-sm font-semibold text-emerald-800 underline underline-offset-2 dark:text-emerald-500"
      >
        <span>{children}</span>
        <ExternalLink size={14} />
      </a>
    );
  }

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
