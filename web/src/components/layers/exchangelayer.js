import React, {
  useState,
  useEffect,
  useMemo,
  useRef,
} from 'react';
import { useSelector } from 'react-redux';
import { scaleLinear, scaleQuantize } from 'd3-scale';
import styled from 'styled-components';
import { noop } from 'lodash';

import global from '../../global';
import { dispatchApplication } from '../../store';
import { useExchangeArrowsData } from '../../hooks/layers';
import { useWidthObserver, useHeightObserver } from '../../hooks/viewport';
import {
  exchangeQuantizedIntensityScale,
  exchangeSpeedCategoryScale,
} from '../../helpers/scales';

import MapExchangeTooltip from '../tooltips/mapexchangetooltip';

// TODO: Fix map scrolling when hovering over arrows when moving map to React.
// See https://github.com/tmrowco/electricitymap-contrib/issues/2309.
const ArrowImage = styled.img`
  cursor: pointer;
  overflow: hidden;
  position: absolute;
  pointer-events: all;
  image-rendering: crisp-edges;
  left: -25px;
  top: -41px;
`;

const Arrow = React.memo(({
  arrow,
  mapTransform,
  mouseMoveHandler,
  mouseOutHandler,
  viewportWidth,
  viewportHeight,
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
      const intensity = exchangeQuantizedIntensityScale(co2intensity);
      const speed = exchangeSpeedCategoryScale(Math.abs(netFlow));
      return resolvePath(`images/${prefix}arrow-${intensity}-animated-${speed}.gif`);
    },
    [colorBlindModeEnabled, co2intensity, netFlow]
  );

  const transform = useMemo(
    () => ({
      x: global.zoneMap ? global.zoneMap.projection()(lonlat)[0] : 0,
      y: global.zoneMap ? global.zoneMap.projection()(lonlat)[1] : 0,
      k: mapTransform ? (0.04 + (mapTransform.k - 1.5) * 0.1) * 0.2 : 0,
      r: rotation + (netFlow > 0 ? 180 : 0),
    }),
    [lonlat, rotation, netFlow, mapTransform],
  );

  const isVisible = useMemo(
    () => {
      // Hide arrows with a very low flow...
      if (Math.abs(netFlow || 0) < 1) return false;

      // ... or the ones that would be rendered outside of viewport ...
      if (transform.x + 100 * transform.k < 0) return false;
      if (transform.y + 100 * transform.k < 0) return false;
      if (transform.x - 100 * transform.k > viewportWidth) return false;
      if (transform.y - 100 * transform.k > viewportHeight) return false;

      // ... and show all the other ones.
      return true;
    },
    [netFlow, transform],
  );

  return (
    <ArrowImage
      style={{
        display: isVisible ? '' : 'none',
        transform: `translateX(${transform.x}px) translateY(${transform.y}px) rotate(${transform.r}deg) scale(${transform.k})`,
      }}
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
  pointer-events: none;
  position: absolute;
  width: 100%;
  height: 100%;
  top: 0;
  left: 0;
`;

export default () => {
  const ref = useRef();
  const arrows = useExchangeArrowsData();
  const width = useWidthObserver(ref);
  const height = useHeightObserver(ref);

  const [transform, setTransform] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [tooltip, setTooltip] = useState(null);

  // Set up map interaction handlers once the map gets initialized.
  useEffect(() => {
    if (global.zoneMap && !isInitialized) {
      global.zoneMap
        .onDrag(setTransform)
        .onDragStart(() => { setIsDragging(true); })
        .onDragEnd(() => { setIsDragging(false); });
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

  if (true) return null;

  return (
    <ArrowsContainer id="exchange" ref={ref}>
      {tooltip && (
        <MapExchangeTooltip
          exchangeData={tooltip.exchangeData}
          position={tooltip.position}
        />
      )}
      {/* Don't render arrows when dragging - see https://github.com/tmrowco/electricitymap-contrib/issues/1590. */}
      {!isDragging && arrows.map(arrow => (
        <Arrow
          arrow={arrow}
          key={arrow.sortedCountryCodes}
          mouseMoveHandler={handleArrowMouseMove}
          mouseOutHandler={handleArrowMouseOut}
          mapTransform={transform}
          viewportWidth={width}
          viewportHeight={height}
        />
      ))}
    </ArrowsContainer>
  );
};
