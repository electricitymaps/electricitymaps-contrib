import { useGetSolar } from 'api/getWeatherData';
import { mapMovingAtom } from 'features/map/mapAtoms';
import { useAtom, useSetAtom } from 'jotai';

import { useEffect } from 'react';
import { MapboxMap } from 'react-map-gl';
import { ToggleOptions } from 'utils/constants';
import {
  selectedDatetimeIndexAtom,
  solarLayerEnabledAtom,
  solarLayerLoadingAtom,
} from 'utils/state/atoms';
import { useReferenceWidthHeightObserver } from 'utils/viewport';
import { stackBlurImageOpacity } from './stackBlurImageOpacity';
import {
  opacityToSolarIntensity,
  solarColorComponents,
  solarIntensityToOpacity,
} from './utils';

// TODO: Figure out why the layer is "shifting" when zooming in and out on the map!
export default function SolarLayer({ map }: { map?: MapboxMap }) {
  const [isMapMoving] = useAtom(mapMovingAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [solarLayerToggle] = useAtom(solarLayerEnabledAtom);
  const setIsLoadingSolarLayer = useSetAtom(solarLayerLoadingAtom);

  const isSolarLayerEnabled =
    solarLayerToggle === ToggleOptions.ON && selectedDatetime.index === 24;
  const { data: solarDataArray, isSuccess } = useGetSolar({
    enabled: isSolarLayerEnabled,
  });
  const solarData = solarDataArray?.[0];

  const { ref, node, width, height } = useReferenceWidthHeightObserver();
  const isVisible = isSuccess && !isMapMoving && isSolarLayerEnabled;

  // Render the processed solar forecast image into the canvas.
  useEffect(() => {
    if (map && node && isVisible && solarData && width && height) {
      const canvas = (node as HTMLCanvasElement).getContext('2d');
      if (!canvas) {
        return;
      }

      const image = canvas.createImageData(width, height);

      const { lng: minLon, lat: minLat } = map.unproject([0, 0]);
      const { lng: maxLon, lat: maxLat } = map.unproject([width, height]);

      const { lo1, la1, dx, dy, nx } = solarData.header;

      // Project solar data onto the image opacity channel
      for (let x = 0; x < image.width; x += 1) {
        for (let y = 0; y < image.height; y += 1) {
          // Taking [lon, lat] = unproject([x, y]) here would be
          // simpler but also slower as unproject method seems more
          // complex than just these basic arithmetic operations.
          const lon = minLon + (maxLon - minLon) * (x / image.width);
          const lat = minLat + (maxLat - minLat) * (y / image.height);

          const sx = Math.floor(lon - lo1 / dx);
          const sy = Math.floor(la1 - lat / dy);
          const sourceIndex = sy * nx + sx;
          const targetIndex = 4 * (y * image.width + x);

          image.data[targetIndex + 3] = solarIntensityToOpacity(
            solarData.data[sourceIndex]
          );
        }
      }

      // Apply stack blur filter over the image opacity.
      stackBlurImageOpacity(image, 0, 0, width, height, 10 * map.getZoom());

      // // Map image opacity channel onto solarColor scale to get the real solar colors.
      for (let index = 0; index < image.data.length; index += 4) {
        const color =
          solarColorComponents[opacityToSolarIntensity(image.data[index + 3])];
        image.data[index + 0] = color.red;
        image.data[index + 1] = color.green;
        image.data[index + 2] = color.blue;
        image.data[index + 3] = color.alpha;
      }

      // Render the image into canvas and mark as ready so that fading in can start.
      canvas.clearRect(0, 0, width, height);
      canvas.putImageData(image, 0, 0);
      setIsLoadingSolarLayer(false);
    }
  }, [node, isVisible, solarData, width, height, map]);

  return (
    <canvas
      id="solar"
      width={width}
      height={height}
      ref={ref}
      className={`pointer-events-none absolute inset-0 h-full w-full duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
    />
  );
}
