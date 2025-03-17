import * as Tooltip from '@radix-ui/react-tooltip';
import { useAtom } from 'jotai';
import { ReactElement, useState } from 'react';
import { openTooltipIdAtom } from 'utils/state/atoms';
import { useIsMobile } from 'utils/styling';

interface TooltipWrapperProperties {
  tooltipContent?: string | ReactElement;
  children: ReactElement;
  side?: 'top' | 'bottom' | 'left' | 'right';
  sideOffset?: number;
  tooltipId?: string;
}

const noop = () => undefined;

export default function TooltipWrapper({
  tooltipContent,
  children,
  side,
  sideOffset,
  tooltipId,
}: TooltipWrapperProperties): ReactElement {
  const [openTooltipId, setOpenTooltipId] = useAtom(openTooltipIdAtom);
  const [localIsOpen, setLocalIsOpen] = useState(false);
  const isMobile = useIsMobile();
  if (!tooltipContent) {
    return children;
  }

  // Helpers
  const openTooltip = () => {
    if (tooltipId) {
      setOpenTooltipId(tooltipId);
    } else {
      setLocalIsOpen(true);
    }
  };
  const closeTooltip = () => {
    if (tooltipId) {
      setOpenTooltipId(null);
    } else {
      setLocalIsOpen(false);
    }
  };
  const toggleTooltip = () => {
    if (tooltipId) {
      if (openTooltipId === tooltipId) {
        closeTooltip();
      } else {
        openTooltip();
      }
    } else {
      setLocalIsOpen(!localIsOpen);
    }
  };

  // Declare the event handlers outside of the JSX to avoid re-creating them on every render.
  const handleMouseEnter = isMobile ? noop : openTooltip;
  const handleMouseLeave = isMobile ? noop : closeTooltip;
  const handleClick = isMobile ? toggleTooltip : noop;
  const handleContentClick = isMobile ? closeTooltip : noop;
  const handleContentPointerDownOutside = isMobile ? closeTooltip : noop;

  const isOpen = tooltipId ? openTooltipId === tooltipId : localIsOpen;

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
            className="z-50"
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
