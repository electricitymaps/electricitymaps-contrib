import { forwardRef, ReactNode } from 'react';
import { twMerge } from 'tailwind-merge';

const RoundedCard = forwardRef<
  HTMLDivElement,
  { children: ReactNode; className?: string }
>(function RoundedCard({ children, className }, reference) {
  return (
    <div
      className={twMerge(
        'rounded-2xl border border-neutral-200 px-4 dark:border-gray-700',
        className
      )}
      ref={reference}
    >
      {children}
    </div>
  );
});

export default RoundedCard;
