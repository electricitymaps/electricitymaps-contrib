import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { CSSTransition } from 'react-transition-group';
import styled from 'styled-components';
import parse from 'color-parse';
import Snowfall from 'react-snowfall';
import { useRefWidthHeightObserver } from '../../hooks/viewport';
import { useSnowEnabled } from '../../hooks/router';
import { stackBlurImageOpacity } from '../../helpers/image';
import { snowColor } from '../../helpers/scales';

import { useInterpolatedSnowData } from '../../hooks/layers';

const maxSnow = snowColor.domain().at(-1);
const solarIntensityToOpacity = (intensity) => Math.floor((intensity / maxSnow) * 255);
const opacityToSolarIntensity = (opacity) => Math.floor((opacity * maxSnow) / 255);

// Pre-process solar color components across all integer values
// for faster vertex shading when generating the canvas image.
const snowColorComponents = [...Array(maxSnow + 1).keys()].map((value) => {
  const parsed = parse(snowColor(value));
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
  const { ref, width, height, node } = useRefWidthHeightObserver();
  const snow = useInterpolatedSnowData();
  const enabled = useSnowEnabled();

  const mapZoom = useSelector((state) => state.application.mapViewport.zoom);
  const isMapLoaded = useSelector((state) => !state.application.isLoadingMap);
  const isMoving = useSelector((state) => state.application.isMovingMap);
  const isVisible = enabled && isMapLoaded && !isMoving;

  // Render the processed snow forecast image into the canvas.
  useEffect(() => {
    if (node && isVisible && snow && width && height) {
      const ctx = node.getContext('2d');
      const image = ctx.createImageData(width, height);

      const [minLon, minLat] = unproject([0, 0]);
      const [maxLon, maxLat] = unproject([width, height]);
      const { lo1, la1 } = snow.header;

      // Project snow data onto the image opacity channel
      for (let x = 0; x < image.width; x += 1) {
        for (let y = 0; y < image.height; y += 1) {
          // Taking [lon, lat] = unproject([x, y]) here would be
          // simpler but also slower as unproject method seems more
          // complex than just these basic arithmetic operations.
          const lon = minLon + (maxLon - minLon) * (x / image.width);
          const lat = minLat + (maxLat - minLat) * (y / image.height);

          const sx = Math.floor(lon - lo1 / snow.header.dx);
          const sy = Math.floor(la1 - lat / snow.header.dy);
          const sourceIndex = sy * snow.header.nx + sx;
          const targetIndex = 4 * (y * image.width + x);

          image.data[targetIndex + 3] = solarIntensityToOpacity(snow.data[sourceIndex]);
        }
      }

      // Apply stack blur filter over the image opacity.
      stackBlurImageOpacity(image, 0, 0, width, height, 10 * mapZoom);

      // Map image opacity channel onto snowColor scale to get the real solar colors.
      for (let i = 0; i < image.data.length; i += 4) {
        const color = snowColorComponents[opacityToSolarIntensity(image.data[i + 3])];
        image.data[i + 0] = color.red;
        image.data[i + 1] = color.green;
        image.data[i + 2] = color.blue;
        image.data[i + 3] = color.alpha;
      }

      // Render the image into canvas and mark as ready so that fading in can start.
      ctx.clearRect(0, 0, width, height);
      ctx.putImageData(image, 0, 0);
    }
  }, [node, isVisible, snow, width, height, mapZoom, unproject]);

  return (
    <CSSTransition classNames="fade" in={isVisible} timeout={300}>
      <div>
        {isVisible ? <embed src="music/lastchristmas.mp3" loop="true" autostart="true" width="2" height="0" /> : null}
        {isVisible ? <Snowfall color="white" snowflakeCount={200} /> : null}
        <Canvas id="snow" width={width} height={height} ref={ref} />
      </div>
    </CSSTransition>
  );
};
