import { SIDEBAR_WIDTH } from 'features/app-sidebar/AppSidebar';

export const getSafeTooltipPosition = (
  mousePositionX: number,
  mousePositionY: number,
  screenWidth: number,
  tooltipWidth: number,
  tooltipHeight: number
) => {
  const ToolTipFlipBoundaryX = tooltipWidth + 30;
  const ToolTipFlipBoundaryY = tooltipHeight - 40;
  const xOffset = Number.parseInt(SIDEBAR_WIDTH.replace('px', '')) + 10;
  const yOffset = tooltipHeight - 40;

  const tooltipPosition = {
    x: mousePositionX + xOffset,
    y: mousePositionY - yOffset,
  };
  if (screenWidth - mousePositionX < ToolTipFlipBoundaryX) {
    tooltipPosition.x = mousePositionX - tooltipWidth;
  }
  if (mousePositionY < ToolTipFlipBoundaryY) {
    tooltipPosition.y = mousePositionY;
  }

  return tooltipPosition;
};

export const getOffsetTooltipPosition = ({
  mousePositionX,
  mousePositionY,
  tooltipHeight,
  isBiggerThanMobile,
}: {
  mousePositionX: number;
  mousePositionY: number;
  tooltipHeight: number;
  isBiggerThanMobile: boolean;
}) => {
  const xOffset = 10;
  const yOffset = tooltipHeight - 40;

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
