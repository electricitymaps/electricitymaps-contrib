import { SIDEBAR_WIDTH } from 'features/app-sidebar/AppSidebar';

export const getSafeTooltipPosition = (
  mousePositionX: number,
  mousePositionY: number,
  screenWidth: number,
  tooltipWidth: number,
  tooltipHeight: number
) => {
  const sidebarWidth = Number.parseInt(SIDEBAR_WIDTH.replace('px', ''));
  const ToolTipFlipBoundaryX = tooltipWidth + 80;
  const ToolTipFlipBoundaryY = tooltipHeight + 16;
  const xOffset = sidebarWidth + 10;
  const yOffset = tooltipHeight + 16;

  const tooltipPosition = {
    x: mousePositionX + xOffset,
    y: mousePositionY - yOffset,
  };
  if (screenWidth - mousePositionX < ToolTipFlipBoundaryX) {
    tooltipPosition.x = mousePositionX - tooltipWidth + sidebarWidth - 10;
  }
  if (mousePositionY < ToolTipFlipBoundaryY) {
    tooltipPosition.y = mousePositionY;
  }

  return tooltipPosition;
};

export const getOffsetTooltipPosition = ({
  mousePositionX,
  mousePositionY,
  isBiggerThanMobile,
}: {
  mousePositionX: number;
  mousePositionY: number;
  isBiggerThanMobile: boolean;
}) => {
  const xOffset = 15;
  const yOffset = 10;

  // For smaller screens we translate the tooltip to the top
  if (!isBiggerThanMobile) {
    return {
      x: 0,
      y: 0,
    };
  }

  const tooltipPosition = {
    x: mousePositionX + xOffset,
    y: Math.max(mousePositionY - yOffset, 0),
  };

  return tooltipPosition;
};
