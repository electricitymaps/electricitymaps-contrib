import { ExternalLink } from 'lucide-react';
import { memo } from 'react';
import { twMerge } from 'tailwind-merge';

function Link({
  href,
  children,
  isExternal,
  className,
}: {
  href: string;
  children: React.ReactNode;
  isExternal?: boolean;
  className?: string;
}) {
  if (isExternal) {
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener"
        className={twMerge(
          'flex w-full items-center justify-between text-sm font-semibold text-emerald-800 underline underline-offset-2 dark:text-emerald-500',
          className
        )}
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
      className={twMerge(
        'text-sm font-semibold text-emerald-800 underline underline-offset-2 dark:text-emerald-500',
        className
      )}
    >
      {children}
    </a>
  );
}

export default memo(Link);
