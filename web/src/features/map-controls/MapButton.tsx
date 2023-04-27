import * as Toggle from '@radix-ui/react-toggle';
import TooltipWrapper from '../../components/tooltips/TooltipWrapper';

interface MapButtonProperties {
  onClick?: () => void;
  icon: any;
  tooltipText?: string;
  className?: string;
  dataTestId?: string;
  asToggle?: boolean;
}

export default function MapButton({
  icon,
  tooltipText,
  className,
  dataTestId,
  onClick,
  asToggle,
}: MapButtonProperties) {
  const Component = asToggle ? Toggle.Root : 'div';
  return (
    <TooltipWrapper tooltipContent={tooltipText}>
      <Component
        onClick={onClick}
        className={`pointer-events-auto flex h-8 w-8 items-center justify-center rounded bg-white text-left shadow-lg transition hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-800 ${className}`}
        aria-label="Toggle functionality" // TODO: This should be more precise!
        data-test-id={dataTestId}
      >
        <div>{icon}</div>
      </Component>
    </TooltipWrapper>
  );
}
