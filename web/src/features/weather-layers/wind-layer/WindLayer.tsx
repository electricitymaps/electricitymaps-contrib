import { useGetWind } from 'api/getWeatherData';
import { mapMovingAtom } from 'features/map/mapAtoms';
import { useAtom, useSetAtom } from 'jotai';
import { useEffect, useMemo, useState } from 'react';
import { MapboxMap } from 'react-map-gl';
import { Maybe } from 'types';
import { ToggleOptions } from 'utils/constants';
import {
  selectedDatetimeIndexAtom,
  windLayerAtom,
  windLayerLoadingAtom,
} from 'utils/state/atoms';
import { useReferenceWidthHeightObserver } from 'utils/viewport';
import Windy from './windy';

type WindyType = ReturnType<typeof Windy>;
let windySingleton: Maybe<WindyType> = null;
const createWindy = async (canvas: HTMLCanvasElement, data: any, map: MapboxMap) => {
  if (!windySingleton) {
    windySingleton = new (Windy as any)({
      canvas,
      data,
      map,
    });
  }
  return windySingleton as WindyType;
};

export default function WindLayer({ map }: { map?: MapboxMap }) {
  const [isMapMoving] = useAtom(mapMovingAtom);
  const [windy, setWindy] = useState<Maybe<WindyType>>(null);
  const { ref, node, width, height } = useReferenceWidthHeightObserver();
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

  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const [windLayerToggle] = useAtom(windLayerAtom);
  const setIsLoadingWindLayer = useSetAtom(windLayerLoadingAtom);
  const isWindLayerEnabled =
    windLayerToggle === ToggleOptions.ON && selectedDatetime.index === 24;
  const { data: windData, isSuccess } = useGetWind({ enabled: isWindLayerEnabled });
  const isVisible = isSuccess && !isMapMoving && isWindLayerEnabled;

  useEffect(() => {
    if (map && !windy && isVisible && node && isWindLayerEnabled && windData) {
      createWindy(node as HTMLCanvasElement, windData, map).then((w) => {
        const { bounds, width, height, extent } = viewport;
        w.start(bounds, width, height, extent);
        setWindy(w);
      });
      setIsLoadingWindLayer(false);
    } else if (!isVisible && windy) {
      windy.stop();
      setWindy(null);
    }
  }, [isVisible, isSuccess, node, windy, viewport]);

  return (
    <canvas
      className={`pointer-events-none absolute h-full w-full duration-300 ${
        // Using display: none here will cause the observer to return width and height of 0
        // so instead we use opacity which can also be transitioned nicely
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
      id="wind"
      width={width}
      height={height}
      ref={ref}
    />
  );
}
