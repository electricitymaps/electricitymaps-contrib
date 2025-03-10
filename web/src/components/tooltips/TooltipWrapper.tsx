import * as Tooltip from '@radix-ui/react-tooltip';
import { ReactElement, useState } from 'react';
import { twMerge } from 'tailwind-merge';
import { useIsMobile } from 'utils/styling';

interface TooltipWrapperProperties {
  tooltipContent?: string | ReactElement;
  children: ReactElement;
  side?: 'top' | 'bottom' | 'left' | 'right';
  sideOffset?: number;
  tooltipClassName?: string;
}

const noop = () => undefined;

export default function TooltipWrapper({
  tooltipContent,
  children,
  side,
  sideOffset,
  tooltipClassName,
}: TooltipWrapperProperties): ReactElement {
  const [isOpen, setIsOpen] = useState(false);
  const isMobile = useIsMobile();
  if (!tooltipContent) {
    return children;
  }

  // Helpers
  const openTooltip = () => setIsOpen(true);
  const closeTooltip = () => setIsOpen(false);
  const toggleTooltip = () => setIsOpen(!isOpen);

  // Declare the event handlers outside of the JSX to avoid re-creating them on every render.
  const handleMouseEnter = isMobile ? noop : openTooltip;
  const handleMouseLeave = isMobile ? noop : closeTooltip;
  const handleClick = isMobile ? toggleTooltip : noop;
  const handleContentClick = isMobile ? closeTooltip : noop;
  const handleContentPointerDownOutside = isMobile ? closeTooltip : noop;

  return (
    <Tooltip.Provider disableHoverableContent>
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
