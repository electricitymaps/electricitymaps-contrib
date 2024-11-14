import { mapMovingAtom } from 'features/map/mapAtoms';
import { useExchangeArrowsData } from 'hooks/arrows';
import { useAtom, useAtomValue } from 'jotai';
import React from 'react';
import useResizeObserver from 'use-resize-observer';
import { colorblindModeAtom, isConsumptionAtom } from 'utils/state/atoms';
import { useBreakpoint } from 'utils/styling';

import ExchangeArrow from './ExchangeArrow';

function ExchangeLayer({ map }: { map?: maplibregl.Map }) {
  const [isMapMoving] = useAtom(mapMovingAtom);
  const [isColorBlindModeEnabled] = useAtom(colorblindModeAtom);
  const { ref, width = 0, height = 0 } = useResizeObserver<HTMLDivElement>();
  const arrows = useExchangeArrowsData();
  const isMobile = !useBreakpoint('md');
  const isConsumption = useAtomValue(isConsumptionAtom);

  return (
    <div
      data-test-id="exchange-layer"
      id="exchange-layer"
      className="h-full w-full"
      ref={ref}
    >
      {/* Don't render arrows when moving map - see https://github.com/electricitymaps/electricitymaps-contrib/issues/1590. */}
      {!isMapMoving &&
        map &&
        isConsumption &&
        arrows.map((arrow) => (
          <ExchangeArrow
            key={arrow.key}
            data={arrow}
            map={map}
            colorBlindMode={isColorBlindModeEnabled}
            viewportWidth={width}
            viewportHeight={height}
            isMobile={isMobile}
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
