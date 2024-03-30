import * as Tooltip from '@radix-ui/react-tooltip';
import { useDimensions } from 'hooks/dimensions';
import { ReactElement, useState } from 'react';
import { twMerge } from 'tailwind-merge';

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
  const [isOpen, setIsOpen] = useState(false);
  const { isMobile } = useDimensions();

  // Declare the event handlers outside of the JSX to avoid re-creating them on every render.
  const handleMouseEnter = isMobile ? () => {} : () => setIsOpen(true);
  const handleMouseLeave = isMobile ? () => {} : () => setIsOpen(false);
  const handleClick = isMobile ? () => setIsOpen(!isOpen) : () => {};
  const handleContentClick = isMobile ? () => setIsOpen(false) : () => {};
  const handleContentPointerDownOutside = isMobile ? () => setIsOpen(false) : () => {};

  return (
    <Tooltip.Provider>
      <Tooltip.Root open={isOpen} delayDuration={0}>
        <Tooltip.Trigger
          onMouseEnter={handleMouseEnter}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
          asChild
        >
          {children}
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            className={twMerge(
              'relative h-auto max-w-[164px] rounded border bg-zinc-50 p-4 text-center text-sm shadow-md dark:border-0 dark:bg-gray-800',
              tooltipClassName
            )}
            sideOffset={sideOffset ?? 3}
            side={side ?? 'left'}
            onClick={handleContentClick}
            onPointerDownOutside={handleContentPointerDownOutside}
          >
            {tooltipContent}
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
