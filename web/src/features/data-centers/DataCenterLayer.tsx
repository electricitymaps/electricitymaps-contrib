import { mapMovingAtom } from 'features/map/mapAtoms';
import { useAtomValue } from 'jotai';
import React from 'react';
import { useMap } from 'react-map-gl/maplibre';
import useResizeObserver from 'use-resize-observer';
import { isDataCenterLayerEnabledAtom } from 'utils/state/atoms';

import dataCentersData from '../../../config/data_centers.json';
import { DataCenterIcon } from './DataCenterIcons';

// Define the data center type
export interface DataCenter {
  displayName: string;
  lonlat: [number, number];
  provider: string;
  region: string;
  zoneKey: string;
}

// Type for the raw data from JSON
export interface RawDataCenter {
  displayName: string;
  lonlat: number[];
  provider: string;
  region: string;
  zoneKey: string;
}

// Type assertion for the imported data with proper type safety
export const dataCenters: Record<string, DataCenter> = {};
for (const [key, value] of Object.entries(
  dataCentersData as unknown as Record<string, RawDataCenter>
)) {
  dataCenters[key] = {
    displayName: value.displayName,
    provider: value.provider,
    region: value.region,
    zoneKey: value.zoneKey,
    lonlat: value.lonlat as [number, number],
  };
}

function DataCenterMarker({
  map,
  lonlat,
  label,
  provider,
}: {
  map: maplibregl.Map;
  lonlat: [number, number];
  label: string;
  provider: string;
}) {
  // Convert geographic coordinates to pixel coordinates
  const point = map.project({ lng: lonlat[1], lat: lonlat[0] });

  return (
    <div
      style={{
        position: 'absolute',
        left: point.x,
        top: point.y,
        transform: 'translate(-50%, -50%)',
        cursor: 'pointer',
      }}
      title={label}
    >
      <DataCenterIcon provider={provider} withPin />
    </div>
  );
}

function DataCenterLayer() {
  const { current: mapReference } = useMap();
  const isMapMoving = useAtomValue(mapMovingAtom);
  const isLayerEnabled = useAtomValue(isDataCenterLayerEnabledAtom);
  const { ref } = useResizeObserver<HTMLDivElement>();

  if (!mapReference || isMapMoving || !isLayerEnabled) {
    return <div ref={ref} className="h-full w-full" />;
  }

  // Get the underlying maplibre Map instance
  const map = mapReference.getMap();

  return (
    <div
      data-testid="data-center-layer"
      id="data-center-layer"
      className="h-full w-full"
      ref={ref}
    >
      {Object.entries(dataCenters).map(([key, dc]) => (
        <DataCenterMarker
          key={key}
          map={map}
          lonlat={dc.lonlat}
          label={dc.displayName}
          provider={dc.provider}
        />
      ))}
    </div>
  );
}

export default React.memo(DataCenterLayer);
