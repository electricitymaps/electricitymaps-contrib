import type { ReactElement } from 'react';

import * as Portal from '@radix-ui/react-portal';

import * as Tooltip from '@radix-ui/react-tooltip';

interface MapTooltipProperties {
  mousePositionX: number;
  mousePositionY: number;
  hoveredFeatureId: string | number | undefined;
}

const ToolTipFlipBoundary = 100;

const getTooltipPosition = (
  mousePositionX: number,
  mousePositionY: number,
  screenHeight: number,
  screenWidth: number
) => {
  const mousePosition = { x: mousePositionX, y: mousePositionY };
  if (screenWidth - mousePositionX < ToolTipFlipBoundary) {
    mousePosition.x = mousePositionX - ToolTipFlipBoundary;
  }
  if (screenHeight - mousePositionY < ToolTipFlipBoundary) {
    mousePosition.y = mousePositionY - ToolTipFlipBoundary;
  }
  if (mousePositionX < ToolTipFlipBoundary) {
    mousePosition.x = mousePositionX + ToolTipFlipBoundary;
  }
  if (mousePositionY < ToolTipFlipBoundary) {
    mousePosition.y = mousePositionY + ToolTipFlipBoundary;
  }
  return mousePosition;
};
export default function MapTooltip(properties: MapTooltipProperties): ReactElement {
  const { mousePositionX, mousePositionY, hoveredFeatureId } = properties;
  const screenWidth = window.innerWidth;
  const screenHeight = window.innerHeight;

  const mousePosition = getTooltipPosition(
    mousePositionX,
    mousePositionY,
    screenHeight,
    screenWidth
  );
  return (
    <Portal.Root className="fixed left-5 top-10">
      <Tooltip.Provider>
        <Tooltip.Root open={Boolean(hoveredFeatureId)} delayDuration={0}>
          <Tooltip.Trigger>
            <div></div>
          </Tooltip.Trigger>
          <Tooltip.Portal>
            <Tooltip.Content
              className="TooltipContent relative  h-7 max-w-[164px] rounded border bg-white p-1 px-3 text-center text-sm drop-shadow-sm dark:border-0 dark:bg-gray-900"
              sideOffset={3}
              side="top"
              style={{ left: mousePosition.x, top: mousePosition.y }}
            >
              <div>dsss</div>
            </Tooltip.Content>
          </Tooltip.Portal>
        </Tooltip.Root>
      </Tooltip.Provider>
    </Portal.Root>
  );
}
