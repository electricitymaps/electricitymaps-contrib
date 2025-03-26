import * as Toggle from '@radix-ui/react-toggle';
import { GlassBackdrop } from 'components/GlassContainer';
import LabelTooltip from 'components/tooltips/LabelTooltip';
import { twMerge } from 'tailwind-merge';
import { useIsMobile } from 'utils/styling';

import TooltipWrapper from '../../components/tooltips/TooltipWrapper';

interface MapButtonProperties {
  onClick?: (event: React.MouseEvent) => void;
  icon: JSX.Element;
  tooltipText?: string;
  className?: string;
  dataTestId?: string;
  asToggle?: boolean;
  ariaLabel?: string;
  isMobile?: boolean;
}

export default function MapButton({
  icon,
  tooltipText,
  className,
  dataTestId,
  onClick,
  asToggle,
  ariaLabel,
}: MapButtonProperties) {
  const Component = asToggle ? Toggle.Root : 'div';
  const isMobile = useIsMobile();
  // If on mobile, don't wrap with tooltip
  if (isMobile) {
    return (
      <Component
        onClick={onClick}
        className={twMerge(
          `relative flex h-8 w-8 items-center justify-center overflow-hidden rounded-lg border border-neutral-200 bg-white/80 text-left transition hover:bg-white focus-visible:border-none focus-visible:outline-brand-green dark:border-neutral-700/60 dark:bg-neutral-900/80 dark:hover:bg-neutral-800`,
          className,
          asToggle && 'pointer-events-auto'
        )}
        aria-label={ariaLabel}
        data-testid={dataTestId}
        role="button"
      >
        <GlassBackdrop className="backdrop-blur-sm" />
        <div>{icon}</div>
      </Component>
    );
  }

  return (
    <TooltipWrapper tooltipContent={<LabelTooltip>{tooltipText}</LabelTooltip>}>
      <Component
        onClick={onClick}
        className={twMerge(
          `relative flex h-8 w-8 items-center justify-center overflow-hidden rounded-lg border border-neutral-200 bg-white/80 text-left transition hover:bg-white focus-visible:border-none focus-visible:outline-brand-green dark:border-neutral-700/60 dark:bg-neutral-900/80 dark:hover:bg-neutral-800`,
          className,
          asToggle && 'pointer-events-auto'
        )}
        aria-label={ariaLabel}
        data-testid={dataTestId}
        role="button"
      >
        <GlassBackdrop className="backdrop-blur-sm" />
        <div>{icon}</div>
      </Component>
    </TooltipWrapper>
  );
}
