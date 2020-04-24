import React, {
  useRef,
  useState,
  useEffect,
  useMemo,
} from 'react';
import { CSSTransition } from 'react-transition-group';
import styled from 'styled-components';

import { useWidthObserver, useHeightObserver } from '../../hooks/viewport';
import { applySolarColorFilter, stackBlurImageOpacity } from '../../helpers/image';
import { useSolarEnabled } from '../../helpers/router';

import global from '../../global';
import { useInterpolatedSolarData } from '../../hooks/layers';

const SOLAR_SCALE = 1000;

const Canvas = styled.canvas`
  top: 0;
  left: 0;
  pointer-events: none;
  position: absolute;
  transition: opacity 300ms ease-in-out;
  width: 100%;
  height: 100%;
`;

export default () => {
  const ref = useRef(null);
  const width = useWidthObserver(ref);
  const height = useHeightObserver(ref);
  const solar = useInterpolatedSolarData();
  const enabled = useSolarEnabled();

  const [isInitialized, setIsInitialized] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isReady, setIsReady] = useState(false);

  // Set up map interaction handlers once the map gets initialized.
  useEffect(() => {
    if (global.zoneMap && !isInitialized) {
      global.zoneMap
        .onDragStart((transform) => {
          setIsDragging(true);
        })
        .onDragEnd(() => {
          setIsDragging(false);
          setIsReady(false);
        });
      setIsInitialized(true);
    }
  }, [global.zoneMap, isInitialized]);

  // Render the processed solar forecast image into the canvas.
  useEffect(() => {
    if (!ref || !ref.current || !solar || !width || !height || isReady) return;

    const unproject = global.zoneMap.unprojection();
    const zoom = global.zoneMap.map.getZoom();

    const ctx = ref.current.getContext('2d');
    const image = ctx.createImageData(width, height);

    const [minLon, minLat] = unproject([0, 0]);
    const [maxLon, maxLat] = unproject([width, height]);
    const { lo1, la1 } = solar.header;

    // Project solar data onto the image opacity channel
    // TODO: Consider using bilinear interpolation here instead of Gaussian blur.
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

        image.data[targetIndex + 3] = Math.floor(solar.data[sourceIndex] / SOLAR_SCALE * 255);
      }
    }

    // Apply a gaussian blur on grid cells
    // TODO: Consider replacing with https://github.com/flozz/StackBlur
    stackBlurImageOpacity(image, 0, 0, width, height, 10 * zoom);

    // Apply solarColor scale to the grayscale image
    // TODO: Use actual solarColor scale (maybe use https://www.npmjs.com/package/color-parse)
    applySolarColorFilter(image);

    // Render the image into canvas and mark as ready so that fading in can start.
    ctx.putImageData(image, 0, 0);
    setIsReady(true);
  }, [ref, solar, width, height, isReady]);

  return (
    <CSSTransition
      classNames="fade"
      in={enabled && isReady && !isDragging}
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
