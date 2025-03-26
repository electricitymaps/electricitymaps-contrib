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
      <div className="flex items-center">
        <a
          href={href}
          target="_blank"
          rel="noopener"
          className="text-sm font-semibold text-emerald-800 underline underline-offset-2 dark:text-emerald-500"
        >
          {children}
        </a>
        <ExternalLink size={14} className="ml-1 text-emerald-800 dark:text-emerald-500" />
      </div>
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
