import { twMerge } from 'tailwind-merge';

export function GraphCard({
  children,
  ref,
  className,
}: {
  children: React.ReactNode;
  ref?: (newNode: Element | null) => void;
  className?: string;
}) {
  return (
    <div
      className={twMerge(
        'my-2 rounded-2xl border-[1px] border-neutral-200 px-4 pb-2 dark:border-gray-700',
        className
      )}
      ref={ref}
    >
      {children}
    </div>
  );
}
