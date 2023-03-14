import * as Tooltip from '@radix-ui/react-tooltip';
import { ReactElement, useState } from 'react';
import { twMerge } from 'tailwind-merge';

interface MobileTooltipWrapperProperties {
  tooltipContent?: string | ReactElement;
  children: ReactElement;
  side?: 'top' | 'bottom' | 'left' | 'right';
  sideOffset?: number;
  tooltipClassName?: string;
}

export default function MobileTooltipWrapper(
  properties: MobileTooltipWrapperProperties
): ReactElement {
  const { tooltipContent, children, side, sideOffset, tooltipClassName } = properties;
  if (!tooltipContent) {
    return children;
  }
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Tooltip.Provider>
      <Tooltip.Root open={isOpen} delayDuration={0}>
        <Tooltip.Trigger
          onClick={() => {
            setIsOpen(!isOpen);
          }}
          asChild
        >
          {children}
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            className={twMerge(
              'relative h-auto max-w-[164px] rounded border bg-zinc-50 p-4 text-center text-sm shadow-md dark:border-0 dark:bg-gray-900',
              tooltipClassName
            )}
            sideOffset={sideOffset ?? 3}
            side={side ?? 'left'}
            onClick={() => {
              setIsOpen(false);
            }}
            onPointerDownOutside={() => {
              setIsOpen(false);
            }}
          >
            <div>{tooltipContent}</div>
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
