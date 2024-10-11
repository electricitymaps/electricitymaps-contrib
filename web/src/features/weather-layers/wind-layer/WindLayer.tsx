import { GfsForecastResponse, useGetWind } from 'api/getWeatherData';
import { mapMovingAtom } from 'features/map/mapAtoms';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import { useEffect, useMemo, useRef, useState } from 'react';
import useResizeObserver from 'use-resize-observer';
import { isWindLayerEnabledAtom, windLayerLoadingAtom } from 'utils/state/atoms';

import { Windy } from './windy';

let windySingleton: Windy | null = null;
const createWindy = async (
  canvas: HTMLCanvasElement,
  data: GfsForecastResponse,
  map: maplibregl.Map
) => {
  if (!windySingleton) {
    windySingleton = new Windy(canvas, data, map);
  }
  return windySingleton;
};

export default function WindLayer({ map }: { map?: maplibregl.Map }) {
  const [isMapMoving] = useAtom(mapMovingAtom);
  const [windy, setWindy] = useState<Windy | null>(null);
  const reference = useRef(null);
  const { width = 0, height = 0 } = useResizeObserver<HTMLCanvasElement>({
    ref: reference,
  });
  const viewport = useMemo(() => {
    const sw = map?.unproject([0, height]);
    const ne = map?.unproject([width, 0]);
    const swArray = [sw?.lng, sw?.lat];
    const neArray = [ne?.lng, ne?.lat];

    return {
      bounds: [
        [0, 0],
        [width, height],
      ],
      width,
      height,
      extent: [swArray, neArray],
    };
  }, [map, width, height]);

  const setIsLoadingWindLayer = useSetAtom(windLayerLoadingAtom);
  const isWindLayerEnabled = useAtomValue(isWindLayerEnabledAtom);
  const { data: windData, isSuccess } = useGetWind({ enabled: isWindLayerEnabled });
  const isVisible = isSuccess && !isMapMoving && isWindLayerEnabled;

  useEffect(() => {
    if (
      map &&
      !windy &&
      isVisible &&
      reference.current &&
      isWindLayerEnabled &&
      windData
    ) {
      createWindy(reference.current as HTMLCanvasElement, windData, map).then((w) => {
        const { bounds, width, height } = viewport;
        w.start(bounds, width, height);
        setWindy(w);
      });
      setIsLoadingWindLayer(false);
    } else if (!isVisible && windy) {
      windy.stop();
      setWindy(null);
    }
  }, [
    isVisible,
    isSuccess,
    windy,
    map,
    isWindLayerEnabled,
    windData,
    setIsLoadingWindLayer,
    viewport,
  ]);

  useEffect(() => {
    if (windy) {
      const { bounds, width, height } = viewport;
      windy.start(bounds, width, height);
    }
  }, [viewport, windy]);

  return (
    <canvas
      className={`pointer-events-none absolute h-full w-full duration-300 ${
        // Using display: none here will cause the observer to return width and height of 0
        // so instead we use opacity which can also be transitioned nicely
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      id="wind"
      data-test-id="wind-layer"
      width={width}
      height={height}
      ref={reference}
    />
  );
}
