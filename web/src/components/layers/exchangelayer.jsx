import React, { useEffect, useState, useMemo } from 'react';
import { useSelector } from 'react-redux';
import styled from 'styled-components';

import { dispatchApplication } from '../../store';
import { useExchangeArrowsData } from '../../hooks/layers';
import { useRefWidthHeightObserver } from '../../hooks/viewport';

import MapExchangeTooltip from '../tooltips/mapexchangetooltip';
import ExchangeArrow from '../exchangearrow';

const Layer = styled.div`
  pointer-events: none;
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
`;

export default React.memo(({ project }) => {
  const arrows = useExchangeArrowsData();
  const { ref, width, height } = useRefWidthHeightObserver();

  const isMoving = useSelector((state) => state.application.isMovingMap);
  const [tooltip, setTooltip] = useState(null);

  // Mouse interaction handlers
  const handleArrowMouseMove = useMemo(
    () => (exchangeData, x, y) => {
      dispatchApplication('isHoveringExchange', true);
      dispatchApplication('co2ColorbarValue', exchangeData.co2intensity);
      setTooltip({ exchangeData, position: { x, y } });
    },
    []
  );
  const handleArrowMouseOut = useMemo(
    () => () => {
      dispatchApplication('isHoveringExchange', false);
      dispatchApplication('co2ColorbarValue', null);
      setTooltip(null);
    },
    []
  );

  // Call mouse out handler immidiately if moving the map.
  useEffect(
    () => {
      if (isMoving && tooltip) {
        handleArrowMouseOut();
      }
    },
    [isMoving, tooltip] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return (
    <Layer id="exchange" ref={ref}>
      {tooltip && (
        <MapExchangeTooltip
          exchangeData={tooltip.exchangeData}
          position={tooltip.position}
          onClose={() => setTooltip(null)}
        />
      )}
      {/* Don't render arrows when moving map - see https://github.com/tmrowco/electricitymap-contrib/issues/1590. */}
      {!isMoving &&
        arrows.map((arrow) => (
          <ExchangeArrow
            data={arrow}
            key={arrow.sortedCountryCodes}
            mouseMoveHandler={handleArrowMouseMove}
            mouseOutHandler={handleArrowMouseOut}
            project={project}
            viewportWidth={width}
            viewportHeight={height}
          />
        ))}
    </Layer>
  );
});
