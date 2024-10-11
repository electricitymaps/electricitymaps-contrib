import * as Toggle from '@radix-ui/react-toggle';
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
    <TooltipWrapper tooltipContent={tooltipText}>
      <Component
        onClick={onClick}
        className={twMerge(
          `flex h-8 w-8 items-center justify-center rounded bg-white/80 text-left shadow-lg backdrop-blur-sm transition hover:bg-white dark:bg-gray-800/80 dark:hover:bg-gray-900/90`,
          className,
          asToggle && 'pointer-events-auto'
        )}
        aria-label={ariaLabel}
        data-test-id={dataTestId}
        role="button"
      >
        <div>{icon}</div>
      </Component>
    </TooltipWrapper>
  );
}
