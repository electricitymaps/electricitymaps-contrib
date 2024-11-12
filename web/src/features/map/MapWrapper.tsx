import MapControls from 'features/map-controls/MapControls';
import { useAtom } from 'jotai';
import { useEffect } from 'react';

import Map from './Map';
import { loadingMapAtom } from './mapAtoms';
import MapFallback, { isOldIOSVersion } from './MapFallback';
import MapTooltip from './MapTooltip';

export default function MapWrapper() {
  const shouldShowFallback = isOldIOSVersion();
  const [_, setIsLoadingMap] = useAtom(loadingMapAtom);

  useEffect(() => {
    if (shouldShowFallback) {
      setIsLoadingMap(false);
    }
  }, [setIsLoadingMap, shouldShowFallback]);
  return (
    <>
      <MapTooltip />
      {shouldShowFallback ? <MapFallback /> : <Map />}
      <MapControls />
    </>
  );
}
