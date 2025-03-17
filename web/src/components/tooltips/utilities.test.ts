import { describe, expect, it } from 'vitest';

import { getOffsetTooltipPosition, getSafeTooltipPosition } from './utilities';

describe('getSafeTooltipPosition', () => {
  it('should position the tooltip correctly when it fits within the screen width', () => {
    const result = getSafeTooltipPosition(100, 100, 500, 50, 50);
    expect(result).toEqual({ x: 173, y: 34 });
  });

  it('should flip the tooltip position when it exceeds the screen width', () => {
    const result = getSafeTooltipPosition(480, 100, 500, 50, 50);
    expect(result).toEqual({ x: 483, y: 34 });
  });

  it('should position the tooltip correctly when it fits within the screen height', () => {
    const result = getSafeTooltipPosition(100, 100, 500, 50, 50);
    expect(result).toEqual({ x: 173, y: 34 });
  });

  it('should adjust the tooltip position when it exceeds the screen height', () => {
    const result = getSafeTooltipPosition(100, 30, 500, 50, 50);
    expect(result).toEqual({ x: 173, y: 30 });
  });

  it('should flip the tooltip position when it exceeds the screen height', () => {
    const result = getSafeTooltipPosition(100, 50, 500, 50, 100);
    expect(result).toEqual({ x: 173, y: 50 });
  });
});

describe('getOffsetTooltipPosition', () => {
  it('should position the tooltip at the top-left corner for smaller screens', () => {
    const result = getOffsetTooltipPosition({
      mousePositionX: 100,
      mousePositionY: 100,
      tooltipHeight: 50,
      isBiggerThanMobile: false,
    });
    expect(result).toEqual({ x: 0, y: 0 });
  });

  it('should position the tooltip correctly when it fits within the screen height for bigger screens', () => {
    const result = getOffsetTooltipPosition({
      mousePositionX: 100,
      mousePositionY: 100,
      tooltipHeight: 50,
      isBiggerThanMobile: true,
    });
    expect(result).toEqual({ x: 110, y: 90 });
  });

  it('should adjust the tooltip position when it exceeds the screen height for bigger screens', () => {
    const result = getOffsetTooltipPosition({
      mousePositionX: 100,
      mousePositionY: 30,
      tooltipHeight: 50,
      isBiggerThanMobile: true,
    });
    expect(result).toEqual({ x: 110, y: 20 });
  });
});
