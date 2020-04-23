/* eslint-disable no-bitwise */
// TODO: re-enable rule

import React, {
  useRef,
  useState,
  useEffect,
  useMemo,
} from 'react';
import { CSSTransition } from 'react-transition-group';
import styled from 'styled-components';
import { interpolate } from 'd3-interpolate';
import { range } from 'lodash';

import { useWidthObserver, useHeightObserver } from '../../hooks/viewport';
import { stackBlurImageOpacity } from '../../helpers/image';
import { useSolarEnabled } from '../../helpers/router';

import global from '../../global';
import { useInterpolatedSolarData } from '../../hooks/layers';

const SOLAR_SCALE = 1000;
const MAX_OPACITY = 0.85;

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
  const interpolatedData = useInterpolatedSolarData();
  const enabled = useSolarEnabled();

  const [isInitialized, setIsInitialized] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isReady, setIsReady] = useState(false);

  // const unproject = useMemo(
  //   () => global.zoneMap && global.zoneMap.unprojection(),
  //   [global.zoneMap],
  // );

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
    if (!ref || !ref.current || !interpolatedData || !width || !height || isReady) return;

    const unproject = global.zoneMap.unprojection();

    const ul = unproject([0, 0]);
    const br = unproject([width, height]);

    // ** Those need to be integers **
    const minLon = parseInt(Math.floor(ul[0]), 10);
    const maxLon = parseInt(Math.ceil(br[0]), 10);
    const minLat = parseInt(Math.floor(br[1]), 10);
    const maxLat = parseInt(Math.ceil(ul[1]), 10);
  
    // Grib constants
    const {
      nx,
      ny,
      lo1,
      la1,
      dx,
      dy,
    } = interpolatedData.header;

    const h = 100; // number of points in longitude space
    const w = 100; // number of points in latitude space
    const ctx = ref.current.getContext('2d');

    // Draw initial image
    const imgGrib = ctx.createImageData(w, h);

    // Iterate over lon, lat
    range(0, h).forEach((yi) => {
      range(0, w).forEach((xi) => {
        // (x, y) are in (lon, lat) space
        const x = interpolate(minLon, maxLon)((xi + 1) / w);
        const y = interpolate(minLat, maxLat)((yi + 1) / h);

        const i = parseInt(x - lo1 / dx, 10);
        const j = parseInt(la1 - y / dy, 10);
        const val = interpolatedData.data[i + nx * j];

        // (pix_x, pix_y) are in pixel space
        const pixX = xi;
        const pixY = h - yi;

        imgGrib.data[[((pixY * (imgGrib.width * 4)) + (pixX * 4)) + 3]] = parseInt(val / SOLAR_SCALE * 255, 10);
      });
    });

    // Reproject this image on our projection
    const sourceData = imgGrib.data;
    let target = ctx.createImageData(width, height);
    const targetData = target.data;

    // From https://bl.ocks.org/mbostock/4329423
    // x and y are the coordinate on the new image
    // i is the new image 1D normalized index (R G B Alpha for each pixel)
    // q is the 1D normalize index for the source map
    for (let y = 0, i = -1; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        // (x, y) is in the (final) pixel space

        // We shift the lat/lon so that the truncation result in a rounding
        // p represents the (lon, lat) point we wish to obtain a value for
        const p = unproject([x, y]);
        const lon = p[0];
        const lat = p[1];

        // q is the index of the associated data point in the other space
        let q = (((maxLat - lat) / (maxLat - minLat)) * h | 0) * w + (((lon - minLon) / (maxLon - minLon)) * w | 0) << 2;

        // Since we are reading the map pixel by pixel we go to the next Alpha channel
        i += 4;
        // Shift source index to alpha
        q += 3;
        targetData[i] = sourceData[q];
      }
    }

    // Apply a gaussian blur on grid cells (blur radius should be about 1deg on screen)
    target = stackBlurImageOpacity(target, 0, 0, width, height, width / (maxLon - minLon) * 2);

    // Apply level of opacity rather than continous scale
    const bluredData = target.data;
    const next = ctx.createImageData(width, height);
    const nextData = next.data;

    let i = 3;
    range(height).forEach((y) => {
      range(width).forEach((x) => {
        // The bluredData correspond to the solar value projected from 0 to 255 hence, 128 is mid-scale
        if (bluredData[i] > 128) {
          // Gold
          nextData[i - 3] = 255;
          nextData[i - 2] = 215;
          nextData[i - 1] = 0;
          nextData[i] = 256 * MAX_OPACITY * (bluredData[i] / 128 - 1);
        }
        else {
          nextData[i] = 256 * MAX_OPACITY * (1 - bluredData[i] / 128);
        }

        i += 4;
      });
    });
    target = next;

    ctx.clearRect(0, 0, width, height);
    ctx.putImageData(target, 0, 0);
    setIsReady(true);
  }, [ref, interpolatedData, width, height, isReady]);

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
