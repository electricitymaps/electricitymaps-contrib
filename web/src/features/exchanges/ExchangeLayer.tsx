import { mapMovingAtom } from 'features/map/mapAtoms';
import { useExchangeArrowsData } from 'hooks/arrows';
import { useAtom } from 'jotai';
import React from 'react';
import { MapboxMap } from 'react-map-gl';
import { useReferenceWidthHeightObserver } from 'utils/viewport';
import ExchangeArrow from './ExchangeArrow';

function ExchangeLayer({ map }: { map?: MapboxMap }) {
  const [isMapMoving] = useAtom(mapMovingAtom);
  const { ref, width, height } = useReferenceWidthHeightObserver();
  const arrows = useExchangeArrowsData();

  return (
    <div id="exchange-layer" className="h-full w-full" ref={ref}>
      {/* Don't render arrows when moving map - see https://github.com/electricitymaps/electricitymaps-contrib/issues/1590. */}
      {!isMapMoving &&
        map &&
        arrows.map((arrow) => (
          <ExchangeArrow
            key={arrow.key}
            data={arrow}
            map={map}
            viewportWidth={width}
            viewportHeight={height}
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
