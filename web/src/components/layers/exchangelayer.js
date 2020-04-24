import React, { useState, useEffect, useMemo } from 'react';
import { useSelector } from 'react-redux';
import { scaleLinear, scaleQuantize } from 'd3-scale';
import styled from 'styled-components';
import { noop } from 'lodash';

import global from '../../global';
import { useExchangeArrowsData } from '../../hooks/layers';
import { dispatchApplication } from '../../store';

import MapExchangeTooltip from '../tooltips/mapexchangetooltip';

// TODO: Fix map scrolling when hovering over arrows when moving map to React.
const ArrowImage = styled.img`
  cursor: pointer;
  overflow: hidden;
  position: absolute;
  image-rendering: crisp-edges;
  left: -25px;
  top: -41px;
`;

const exchangeAnimationIntensityScale = scaleQuantize()
  .domain([0, 800])
  .range([0, 80, 160, 240, 320, 400, 480, 560, 640, 720, 800])
  .unknown('nan');

const exchangeAnimationDurationScale = scaleLinear()
  .domain([500, 5000])
  .rangeRound([0, 2])
  .unknown(0)
  .clamp(true);

const Arrow = React.memo(({
  arrow,
  mapTransform,
  mouseMoveHandler,
  mouseOutHandler,
}) => {
  const isMobile = useSelector(state => state.application.isMobile);
  const colorBlindModeEnabled = useSelector(state => state.application.colorBlindModeEnabled);
  const {
    co2intensity,
    lonlat,
    netFlow,
    rotation,
  } = arrow;

  const imageSource = useMemo(
    () => {
      const prefix = colorBlindModeEnabled ? 'colorblind-' : '';
      const intensity = exchangeAnimationIntensityScale(co2intensity);
      const duration = exchangeAnimationDurationScale(Math.abs(netFlow));
      return resolvePath(`images/${prefix}arrow-${intensity}-animated-${duration}.gif`);
    },
    [colorBlindModeEnabled, co2intensity, netFlow]
  );

  const transform = useMemo(
    () => {
      const [x, y] = global.zoneMap ? global.zoneMap.projection()(lonlat) : [0, 0];
      const k = mapTransform ? (0.04 + (mapTransform.k - 1.5) * 0.1) * 0.2 : 0;
      const r = rotation + (netFlow > 0 ? 180 : 0);
      return `translateX(${x}px) translateY(${y}px) rotate(${r}deg) scale(${k})`;
    },
    [lonlat, rotation, netFlow, mapTransform],
  );

  // Hide arrows with a very low flow.
  // TODO: Consider hiding the arrows that are outside of the screen.
  const display = useMemo(
    () => (Math.abs(netFlow || 0) < 1 ? 'none' : ''),
    [netFlow],
  );

  return (
    <ArrowImage
      style={{ display, transform }}
      src={imageSource}
      width="49"
      height="81"
      /* Support only click events in mobile mode, otherwise react to mouse hovers */
      onClick={isMobile ? (e => mouseMoveHandler(arrow, e.clientX, e.clientY)) : noop}
      onMouseMove={!isMobile ? (e => mouseMoveHandler(arrow, e.clientX, e.clientY)) : noop}
      onMouseOut={mouseOutHandler}
      onBlur={mouseOutHandler}
    />
  );
});

const ArrowsContainer = styled.div`
  position: absolute;
  top: 0;
  left: 0;
`;

export default () => {
  const arrows = useExchangeArrowsData();
  const [transform, setTransform] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [tooltip, setTooltip] = useState(null);

  // Set up map interaction handlers once the map gets initialized.
  // TODO: Consider hidding the arrows or stopping their animation when dragging.
  useEffect(() => {
    if (global.zoneMap && !isInitialized) {
      global.zoneMap.onDrag((t) => { setTransform(t); });
      setIsInitialized(true);
    }
  }, [global.zoneMap, isInitialized]);

  // Mouse interaction handlers
  const handleArrowMouseMove = useMemo(() => (exchangeData, x, y) => {
    dispatchApplication('co2ColorbarValue', exchangeData.co2intensity);
    setTooltip({ exchangeData, position: { x, y } });
  }, []);
  const handleArrowMouseOut = useMemo(() => () => {
    dispatchApplication('co2ColorbarValue', null);
    setTooltip(null);
  }, []);

  return (
    <ArrowsContainer id="exchange">
      {tooltip && (
        <MapExchangeTooltip
          exchangeData={tooltip.exchangeData}
          position={tooltip.position}
        />
      )}
      {arrows.map(arrow => (
        <Arrow
          key={arrow.sortedCountryCodes}
          mouseMoveHandler={handleArrowMouseMove}
          mouseOutHandler={handleArrowMouseOut}
          mapTransform={transform}
          arrow={arrow}
        />
      ))}
    </ArrowsContainer>
  );
};
