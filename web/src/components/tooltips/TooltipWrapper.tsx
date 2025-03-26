import * as Tooltip from '@radix-ui/react-tooltip';
import { useAtom } from 'jotai';
import {
  forwardRef,
  ReactElement,
  useCallback,
  useImperativeHandle,
  useState,
} from 'react';
import { openTooltipIdAtom } from 'utils/state/atoms';
import { useIsMobile } from 'utils/styling';

interface TooltipWrapperProperties {
  tooltipContent?: string | ReactElement;
  children: ReactElement;
  side?: 'top' | 'bottom' | 'left' | 'right';
  sideOffset?: number;
  tooltipId?: string;
}

export interface TooltipWrapperReference {
  close: () => void;
}

const TooltipWrapper = forwardRef<TooltipWrapperReference, TooltipWrapperProperties>(
  function TooltipWrapper(
    {
      tooltipContent,
      children,
      side = 'left',
      sideOffset = 3,
      tooltipId,
    }: TooltipWrapperProperties,
    reference
  ): ReactElement {
    const [openTooltipId, setOpenTooltipId] = useAtom(openTooltipIdAtom);
    const [localIsOpen, setLocalIsOpen] = useState(false);
    const isMobile = useIsMobile();

    const openTooltip = useCallback(() => {
      if (tooltipId) {
        setOpenTooltipId(tooltipId);
      } else {
        setLocalIsOpen(true);
      }
    }, [tooltipId, setOpenTooltipId]);

    const closeTooltip = useCallback(() => {
      if (tooltipId) {
        setOpenTooltipId(null);
      } else {
        setLocalIsOpen(false);
      }
    }, [tooltipId, setOpenTooltipId]);

    const toggleTooltip = useCallback(() => {
      if (tooltipId) {
        setOpenTooltipId(openTooltipId === tooltipId ? null : tooltipId);
      } else {
        setLocalIsOpen((previous) => !previous);
      }
    }, [tooltipId, openTooltipId, setOpenTooltipId]);

    // Expose the close method to the parent via ref
    useImperativeHandle(reference, () => ({
      close: closeTooltip,
    }));

    // Simple event handlers using memoized functions
    const handleMouseEnter = useCallback(
      () => !isMobile && openTooltip(),
      [isMobile, openTooltip]
    );
    const handleMouseLeave = useCallback(
      () => !isMobile && closeTooltip(),
      [isMobile, closeTooltip]
    );
    const handleClick = useCallback(
      () => isMobile && toggleTooltip(),
      [isMobile, toggleTooltip]
    );
    const handleContentClick = useCallback(
      () => isMobile && closeTooltip(),
      [isMobile, closeTooltip]
    );

    if (!tooltipContent) {
      return children;
    }

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
              sideOffset={sideOffset}
              side={side}
              onClick={handleContentClick}
              onPointerDownOutside={handleContentClick}
            >
              {tooltipContent}
            </Tooltip.Content>
          </Tooltip.Portal>
        </Tooltip.Root>
      </Tooltip.Provider>
    );
  }
);

export default TooltipWrapper;
