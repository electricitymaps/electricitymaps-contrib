import * as Toggle from '@radix-ui/react-toggle';
import TooltipWrapper from '../../components/tooltips/TooltipWrapper';

interface MapButtonProperties {
  onClick?: () => void;
  icon: any;
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
        className={`pointer-events-auto flex h-8 w-8 items-center justify-center rounded bg-white text-left shadow-lg transition hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-800 ${className}`}
        aria-label={ariaLabel}
        data-test-id={dataTestId}
        role="button"
      >
        <div>{icon}</div>
      </Component>
    </TooltipWrapper>
  );
}
