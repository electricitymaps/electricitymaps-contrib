import React, {
  useRef,
  useState,
  useEffect,
  useMemo,
} from 'react';
import { useSelector } from 'react-redux';
import { CSSTransition } from 'react-transition-group';
import { range, last } from 'lodash';
import styled from 'styled-components';
import parse from 'color-parse';

import { useWidthObserver, useHeightObserver } from '../../hooks/viewport';
import { stackBlurImageOpacity } from '../../helpers/image';
import { useSolarEnabled } from '../../helpers/router';
import { solarColor } from '../../helpers/scales';

import { useInterpolatedSolarData } from '../../hooks/layers';

const maxSolar = last(solarColor.domain());
const solarIntensityToOpacity = intensity => Math.floor(intensity / maxSolar * 255);
const opacityToSolarIntensity = opacity => Math.floor(opacity * maxSolar / 255);

// Pre-process solar color components across all integer values
// for faster vertex shading when generating the canvas image.
const solarColorComponents = range(maxSolar + 1).map((value) => {
  const parsed = parse(solarColor(value));
  return {
    red: parsed.values[0],
    green: parsed.values[1],
    blue: parsed.values[2],
    alpha: Math.floor(255 * 0.85 * parsed.alpha), // Max layer opacity 85%
  };
});

const Canvas = styled.canvas`
  top: 0;
  left: 0;
  pointer-events: none;
  position: absolute;
  transition: opacity 300ms ease-in-out;
  width: 100%;
  height: 100%;
`;

export default ({ unproject }) => {
  const ref = useRef(null);
  const width = useWidthObserver(ref);
  const height = useHeightObserver(ref);
  const solar = useInterpolatedSolarData();
  const enabled = useSolarEnabled();

  const mapZoom = useSelector(state => state.application.mapViewport.zoom);
  const isMapLoaded = useSelector(state => !state.application.isLoadingMap);
  const isDragging = useSelector(state => state.application.isDraggingMap);
  const isVisible = enabled && isMapLoaded && !isDragging;

  // Render the processed solar forecast image into the canvas.
  useEffect(() => {
    if (ref.current && isVisible && solar && width && height) {
      const ctx = ref.current.getContext('2d');
      const image = ctx.createImageData(width, height);

      const [minLon, minLat] = unproject([0, 0]);
      const [maxLon, maxLat] = unproject([width, height]);
      const { lo1, la1 } = solar.header;

      // Project solar data onto the image opacity channel
      for (let x = 0; x < image.width; x += 1) {
        for (let y = 0; y < image.height; y += 1) {
          // Taking [lon, lat] = unproject([x, y]) here would be
          // simpler but also slower as unproject method seems more
          // complex than just these basic arithmetic operations.
          const lon = minLon + (maxLon - minLon) * (x / image.width);
          const lat = minLat + (maxLat - minLat) * (y / image.height);

          const sx = Math.floor(lon - lo1 / solar.header.dx);
          const sy = Math.floor(la1 - lat / solar.header.dy);
          const sourceIndex = sy * solar.header.nx + sx;
          const targetIndex = 4 * (y * image.width + x);

          image.data[targetIndex + 3] = solarIntensityToOpacity(solar.data[sourceIndex]);
        }
      }

      // Apply stack blur filter over the image opacity.
      stackBlurImageOpacity(image, 0, 0, width, height, 10 * mapZoom);

      // Map image opacity channel onto solarColor scale to get the real solar colors.
      for (let i = 0; i < image.data.length; i += 4) {
        const color = solarColorComponents[opacityToSolarIntensity(image.data[i + 3])];
        image.data[i + 0] = color.red;
        image.data[i + 1] = color.green;
        image.data[i + 2] = color.blue;
        image.data[i + 3] = color.alpha;
      }

      // Render the image into canvas and mark as ready so that fading in can start.
      ctx.clearRect(0, 0, width, height);
      ctx.putImageData(image, 0, 0);
    }
  }, [ref.current, isVisible, solar, width, height]);

  return (
    <CSSTransition
      classNames="fade"
      in={isVisible}
      timeout={300}
    >
      <Canvas
        id="solar"
        width={width}
        height={height}
        ref={ref}
      />
    </CSSTransition>
  );
};
