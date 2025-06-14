import { mapMovingAtom } from 'features/map/mapAtoms';
import { useAtomValue } from 'jotai';
import React from 'react';
import { useMap } from 'react-map-gl/maplibre';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { RouteParameters } from 'types';
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
  region,
  zoneKey,
  timeRange,
  resolution,
  searchParams,
}: {
  map: maplibregl.Map;
  lonlat: [number, number];
  label: string;
  provider: string;
  region: string;
  zoneKey: string;
  timeRange: string;
  resolution: string;
  searchParams: URLSearchParams;
}) {
  const navigate = useNavigate();
  // Convert geographic coordinates to pixel coordinates
  const point = map.project({ lng: lonlat[0], lat: lonlat[1] });

  const handleClick = () => {
    const searchParametersString = searchParams.toString();
    const queryString = searchParametersString ? `?${searchParametersString}` : '';
    navigate(
      `/data-center/${zoneKey}/${provider}/${region}/${timeRange}/${resolution}${queryString}`
    );
  };

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
      onClick={handleClick}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          handleClick();
        }
      }}
      role="button"
      tabIndex={0}
      aria-label={`${label} data center`}
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
  const { urlTimeRange = '72h', resolution = 'hourly' } = useParams<RouteParameters>();
  const [searchParameters] = useSearchParams();

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
          region={dc.region}
          zoneKey={dc.zoneKey}
          timeRange={urlTimeRange}
          resolution={resolution}
          searchParams={searchParameters}
        />
      ))}
    </div>
  );
}

export default React.memo(DataCenterLayer);
