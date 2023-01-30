import MapControls from 'features/map-controls/MapControls';
import { useAtom } from 'jotai';
import { useEffect } from 'react';
import Map from './Map';
import MapFallback, { isOldIOSVersion } from './MapFallback';
import MapTooltip from './MapTooltip';
import { loadingMapAtom } from './mapAtoms';

export default function MapWrapper() {
  const shouldShowFallback = isOldIOSVersion();
  const [_, setIsLoadingMap] = useAtom(loadingMapAtom);

  useEffect(() => {
    if (shouldShowFallback) {
      setIsLoadingMap(false);
    }
  }, [shouldShowFallback]);

  return (
    <>
      <MapTooltip />
      {shouldShowFallback ? <MapFallback /> : <Map />}
      <MapControls />
    </>
  );
}
