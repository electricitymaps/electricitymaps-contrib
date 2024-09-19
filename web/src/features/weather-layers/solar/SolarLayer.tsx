import { useGetSolar } from 'api/getWeatherData';
import { useAtomValue, useSetAtom } from 'jotai';
import { useEffect, useMemo, useRef, useState } from 'react';
import { isSolarLayerEnabledAtom, solarLayerLoadingAtom } from 'utils/state/atoms';

import { stackBlurImageOpacity } from './stackBlurImageOpacity';
import {
  opacityToSolarIntensity,
  solarColorComponents,
  solarIntensityToOpacity,
} from './utils';

const RADIANS_PER_DEGREE = Math.PI / 180;
const DEGREES_PER_RADIAN = 180 / Math.PI;

function gudermannian(y: number): number {
  return Math.atan(Math.sinh(y)) * DEGREES_PER_RADIAN;
}
function convertRange(value: number, r1: [number, number], r2: [number, number]): number {
  return ((value - r1[0]) * (r2[1] - r2[0])) / (r1[1] - r1[0]) + r2[0];
}
function convertYToLat(yMax: number, y: number): number {
  return convertRange(
    y,
    [0, yMax],
    [90 * RADIANS_PER_DEGREE * 2, -90 * RADIANS_PER_DEGREE * 2]
  );
}

export default function SolarLayer({ map }: { map?: maplibregl.Map }) {
  const setIsLoadingSolarLayer = useSetAtom(solarLayerLoadingAtom);
  const isSolarLayerEnabled = useAtomValue(isSolarLayerEnabledAtom);

  const { data: solarDataArray, isSuccess } = useGetSolar({
    enabled: isSolarLayerEnabled,
  });
  const solarData = solarDataArray?.[0];

  const isVisibleReference = useRef(false);
  isVisibleReference.current = isSuccess && isSolarLayerEnabled;

  const [canvasScale, setCanvasScale] = useState(4);

  // Shrink canvasScale so that canvas dimensions don't exceed WebGL MAX_TEXTURE_SIZE of the user's device
  useEffect(() => {
    const gl = document.createElement('canvas').getContext('webgl');
    if (gl) {
      const targetCanvasScale =
        gl.getParameter(gl.MAX_TEXTURE_SIZE) /
        Math.max(3 * (solarData?.header.nx ?? 360), solarData?.header.ny ?? 180);
      const newCanvasScale = Math.max(1, Math.min(4, Math.floor(targetCanvasScale)));
      setCanvasScale(newCanvasScale);
    }
  }, [solarData?.header.nx, solarData?.header.ny]);

  const node: HTMLCanvasElement = useMemo(() => {
    const canvas = document.createElement('canvas');
    // wrap around Earth three times to avoid a seam where 180 and -180 meet
    canvas.width = 3 * canvasScale * (solarData?.header.nx ?? 360);
    canvas.height = canvasScale * (solarData?.header.ny ?? 180);
    return canvas;
  }, [canvasScale, solarData?.header.nx, solarData?.header.ny]);

  useEffect(() => {
    if (!node || !map?.isStyleLoaded()) {
      return;
    }

    const north = gudermannian(convertYToLat(node.height - 1, 0));
    const south = gudermannian(convertYToLat(node.height - 1, node.height - 1));

    map.addSource(
      'solar',
      {
        type: 'canvas',
        canvas: node,
        coordinates: [
          [-540, north],
          [539.999, north],
          [539.999, south],
          [-540, south],
        ],
      } as any // Workaround for https://github.com/maplibre/maplibre-gl-js/issues/2242
    );

    if (isVisibleReference.current) {
      if (!map.getLayer('solar-point')) {
        map.addLayer({ id: 'solar-point', type: 'raster', source: 'solar' });
      }
      setIsLoadingSolarLayer(false);
    }

    return () => {
      if (map.getLayer('solar-point')) {
        map.removeLayer('solar-point');
      }
      if (map.getSource('solar')) {
        map.removeSource('solar');
      }
    };
  }, [map, node, setIsLoadingSolarLayer, isVisibleReference.current]);

  // Render the processed solar forecast image into the canvas.
  useEffect(() => {
    if (!map || !node || !solarData || !isVisibleReference.current) {
      return;
    }
    const canvas = node.getContext('2d');
    if (!canvas) {
      return;
    }

    const image = canvas.createImageData(node.width, node.height);

    const { lo1, la1, dx, dy, nx } = solarData.header;

    // Project solar data onto the image opacity channel
    for (let x = 0; x < image.width / 3; x += 1) {
      const lon = ((x / canvasScale) % 360) - 180;
      const sx = Math.floor(lon - lo1 / dx);
      for (let y = 0; y < image.height; y += 1) {
        const lat = gudermannian(convertYToLat(image.height - 1, y));
        const sy = Math.floor(la1 - lat / dy);

        const sourceIndex = sy * nx + sx;
        const targetIndex = 4 * (y * image.width + x);

        image.data[targetIndex + 3] = solarIntensityToOpacity(
          solarData.data[sourceIndex]
        );
      }
    }
    // copy already calculated opacity data from the left
    for (let x = Math.floor(image.width / 3); x < image.width; x += 1) {
      for (let y = 0; y < image.height; y += 1) {
        const targetIndex = 4 * (y * image.width + x);
        const sourceIndex = 4 * (y * image.width + (x % (360 * canvasScale)));
        image.data[targetIndex + 3] = image.data[sourceIndex + 3];
      }
    }

    // Apply stack blur filter over the image opacity.
    stackBlurImageOpacity(image, 0, 0, image.width, image.height, 10);

    // Map image opacity channel onto solarColor scale to get the real solar colors.
    for (let index = 0; index < image.data.length; index += 4) {
      const color = solarColorComponents[opacityToSolarIntensity(image.data[index + 3])];
      image.data[index + 0] = color.red;
      image.data[index + 1] = color.green;
      image.data[index + 2] = color.blue;
      image.data[index + 3] = color.alpha;
    }

    // Render the image into canvas and mark as ready so that fading in can start.
    canvas.clearRect(0, 0, node.width, node.height);
    canvas.putImageData(image, 0, 0);
  }, [node, solarData, map]);

  return null;
}
