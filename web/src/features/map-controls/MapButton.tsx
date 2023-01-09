import * as Toggle from '@radix-ui/react-toggle';
import type { ReactElement } from 'react';
import TooltipWrapper from '../../components/tooltips/TooltipWrapper';

interface MapButtonProperties {
  onClick: () => void;
  icon: any;
  tooltipText?: string;
  className?: string;
  dataTestId?: string;
}

export default function MapButton(properties: MapButtonProperties): ReactElement {
  const { onClick, icon, tooltipText, className, dataTestId } = properties;

  return (
    <TooltipWrapper tooltipContent={tooltipText}>
      <Toggle.Root
        onClick={onClick}
        className={`pointer-events-auto flex h-8 w-8 items-center justify-center rounded bg-white text-left drop-shadow transition hover:bg-gray-100 dark:bg-gray-900 dark:hover:bg-gray-800 ${className}`}
        aria-label="Toggle functionality" // TODO: This should be more precise!
        data-test-id={dataTestId}
      >
        <div>{icon}</div>
      </Toggle.Root>
    </TooltipWrapper>
  );
}
