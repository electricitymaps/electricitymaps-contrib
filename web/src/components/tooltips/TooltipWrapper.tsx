import { ReactElement } from 'react';
import * as Tooltip from '@radix-ui/react-tooltip';

interface TooltipWrapperProperties {
  tooltipContent?: string | ReactElement;
  children: ReactElement;
  side?: 'top' | 'bottom' | 'left' | 'right';
  sideOffset?: number;
  tooltipClassName?: string;
}

export default function TooltipWrapper(
  properties: TooltipWrapperProperties
): ReactElement {
  const { tooltipContent, children, side, sideOffset, tooltipClassName } = properties;
  if (!tooltipContent) {
    return children;
  }
  return (
    <Tooltip.Provider disableHoverableContent>
      <Tooltip.Root delayDuration={0}>
        <Tooltip.Trigger asChild>{children}</Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            className={
              tooltipClassName ??
              'relative   h-7 max-w-[164px] rounded border bg-gray-100 p-1 px-3 text-center text-sm drop-shadow-sm dark:border-0 dark:bg-gray-900'
            }
            sideOffset={sideOffset ?? 3}
            side={side ?? 'left'}
          >
            <div>{tooltipContent}</div>
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
