import { useExchangeArrowsData } from 'hooks/arrows';
import React from 'react';
import { MapboxMap } from 'react-map-gl';
import { useRefWidthHeightObserver } from 'utils/viewport';
import ExchangeArrow from './ExchangeArrow';

function ExchangeLayer({ map, isMoving }: { map?: MapboxMap; isMoving: boolean }) {
  const { ref, width, height } = useRefWidthHeightObserver();
  const arrows = useExchangeArrowsData();

  return (
    <div className="h-full w-full" ref={ref}>
      {/* Don't render arrows when moving map - see https://github.com/tmrowco/electricitymap-contrib/issues/1590. */}
      {!isMoving &&
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
