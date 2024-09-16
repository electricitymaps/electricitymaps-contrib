import { forwardRef, ReactNode } from 'react';
import { twMerge } from 'tailwind-merge';

export const RoundedCard = forwardRef<
  HTMLDivElement,
  { children: ReactNode; className?: string }
>(function RoundedCard({ children, className }, reference) {
  return (
    <div
      className={twMerge(
        'my-2 rounded-2xl border border-neutral-200 px-4 pb-2 dark:border-gray-700',
        className
      )}
      ref={reference}
    >
      {children}
    </div>
  );
});
