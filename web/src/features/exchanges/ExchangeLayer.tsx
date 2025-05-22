import { mapMovingAtom } from 'features/map/mapAtoms';
import { useExchangeArrowsData } from 'hooks/arrows';
import { useAtomValue } from 'jotai';
import React, { useMemo } from 'react';
import useResizeObserver from 'use-resize-observer';
import {
  colorblindModeAtom,
  isConsumptionAtom,
  mapColorSourceAtom,
} from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';

import ExchangeArrow from './ExchangeArrow';
import { generateQuantizedExchangeColorScale } from './scales';

function ExchangeLayer({ map }: { map?: maplibregl.Map }) {
  const isMapMoving = useAtomValue(mapMovingAtom);
  const isColorBlindModeEnabled = useAtomValue(colorblindModeAtom);
  const { ref, width = 0, height = 0 } = useResizeObserver<HTMLDivElement>();
  const arrows = useExchangeArrowsData();
  const isMobile = !useBreakpoint('md');
  const isConsumption = useAtomValue(isConsumptionAtom);
  const mapColorSource = useAtomValue(mapColorSourceAtom);
  const quantizedColorScale = useMemo(
    () => generateQuantizedExchangeColorScale(mapColorSource),
    [mapColorSource]
  );

  return (
    <div
      data-testid="exchange-layer"
      id="exchange-layer"
      className="h-full w-full"
      ref={ref}
    >
      {/* Don't render arrows when moving map - see https://github.com/electricitymaps/electricitymaps-contrib/issues/1590. */}
      {!isMapMoving &&
        map &&
        isConsumption &&
        quantizedColorScale != null &&
        arrows.map((arrow) => (
          <ExchangeArrow
            key={arrow.key}
            data={arrow}
            map={map}
            colorBlindMode={isColorBlindModeEnabled}
            viewportWidth={width}
            viewportHeight={height}
            isMobile={isMobile}
            quantizedColorScale={quantizedColorScale}
          />
        ))}
    </div>
  );
}

// TODO: We are memoizing to avoid recalculating the arrows
// when the map is not moving and far zoomed out so no arrows are visible.
// This could also be done by not
// rendering the component at all on certain zoom levels.
export default React.memo(ExchangeLayer);
