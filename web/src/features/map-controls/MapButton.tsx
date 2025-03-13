import * as Toggle from '@radix-ui/react-toggle';
import { GlassBackdrop } from 'components/GlassContainer';
import { twMerge } from 'tailwind-merge';

import TooltipWrapper from '../../components/tooltips/TooltipWrapper';

interface MapButtonProperties {
  onClick?: () => void;
  icon: JSX.Element;
  tooltipText?: string;
  className?: string;
  dataTestId?: string;
  asToggle?: boolean;
  ariaLabel?: string;
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
  return (
    <TooltipWrapper
      tooltipContent={tooltipText}
      tooltipClassName="relative py-1.5 px-3 rounded"
    >
      <Component
        onClick={onClick}
        className={twMerge(
          `relative flex h-8 w-8 items-center justify-center overflow-hidden rounded bg-white/80 text-left transition hover:bg-white dark:border-neutral-700/60 dark:bg-neutral-900/80 dark:hover:bg-neutral-800`,
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
