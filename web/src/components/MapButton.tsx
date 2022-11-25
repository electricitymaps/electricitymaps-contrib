import type { ReactElement } from 'react';
import * as Toggle from '@radix-ui/react-toggle';
import TooltipWrapper from './TooltipWrapper';

interface MapButtonProperties {
  onClick: () => void;
  icon: any;
  tooltipText?: string;
  className?: string;
}

export default function MapButton(properties: MapButtonProperties): ReactElement {
  const { onClick, icon, tooltipText, className } = properties;

  return (
    <TooltipWrapper tooltipContent={tooltipText}>
      <Toggle.Root
        onClick={onClick}
        className={`Toggle pointer-events-auto flex h-8 w-8 items-center justify-center rounded bg-white  drop-shadow dark:bg-gray-900 ${className}`}
        aria-label="Toggle italic"
      >
        <div>{icon}</div>
      </Toggle.Root>
    </TooltipWrapper>
  );
}
