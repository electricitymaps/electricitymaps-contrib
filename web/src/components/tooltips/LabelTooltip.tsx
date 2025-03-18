import GlassContainer from 'components/GlassContainer';
import { twMerge } from 'tailwind-merge';

export default function LabelTooltip({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <GlassContainer
      className={twMerge(
        'relative h-auto max-w-[164px] rounded px-3 py-1.5 text-center text-sm sm:rounded sm:bg-white',
        className
      )}
    >
      {children}
    </GlassContainer>
  );
}
