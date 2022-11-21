import { ReactElement } from 'react';
import * as Tooltip from '@radix-ui/react-tooltip';

interface TooltipWrapperProperties {
  tooltipText?: string;
  children: ReactElement;
}

export default function TooltipWrapper(
  properties: TooltipWrapperProperties
): ReactElement {
  if (!properties.tooltipText) {
    return properties.children;
  }
  return (
    <Tooltip.Provider>
      <Tooltip.Root delayDuration={0}>
        <Tooltip.Trigger asChild>{properties.children}</Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            className="TooltipContent relative  h-7 max-w-[164px] rounded border bg-white p-1 px-3 text-center text-sm drop-shadow-sm dark:border-0 dark:bg-gray-900"
            sideOffset={3}
            side="left"
          >
            <p>{properties.tooltipText}</p>
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
