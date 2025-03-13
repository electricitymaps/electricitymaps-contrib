import { twMerge } from 'tailwind-merge';

export function GlassBackdrop({ className }: { className?: string }) {
  return (
    <div
      className={twMerge(
        `absolute inset-0 -z-10 h-full w-full backdrop-blur-xl `,
        className
      )}
    />
  );
}

export default function GlassContainer({
  className,
  children,
  backdropClassName,
  ...props
}: {
  className?: string;
  backdropClassName?: string;
  children: React.ReactNode;
  [key: string]: React.HTMLAttributes<HTMLDivElement>;
}): JSX.Element {
  return (
    <div
      className={twMerge(
        `absolute z-30 w-full overflow-hidden border border-neutral-200 bg-white dark:border-neutral-700/60 dark:bg-neutral-900 sm:rounded-2xl sm:bg-white/80 sm:dark:bg-neutral-900/80`,
        className
      )}
      {...props}
    >
      <GlassBackdrop className={backdropClassName} />
      {children}
    </div>
  );
}
