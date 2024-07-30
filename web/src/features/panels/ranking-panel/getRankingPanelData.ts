import { getCountryName, getZoneName } from 'translation/translation';
import type { GridState, ZoneKey } from 'types';
import { SpatialAggregate } from 'utils/constants';
import { getCO2IntensityByMode } from 'utils/helpers';

import { getHasSubZones, isGenerationOnlyZone } from '../zone/util';
import { ZoneRowType } from './ZoneList';

function filterZonesBySpatialAggregation(
  zoneKey: ZoneKey,
  spatialAggregation: string
): boolean {
  const hasSubZones = getHasSubZones(zoneKey);
  const isSubZone = zoneKey ? zoneKey.includes('-') : true;
  const isCountryView = spatialAggregation === SpatialAggregate.COUNTRY;
  if (isCountryView && isSubZone) {
    return false;
  }
  if (!isCountryView && hasSubZones) {
    return false;
  }
  return true;
}

export const getRankedState = (
  data: GridState | undefined,
  getCo2colorScale: (co2intensity: number) => string,
  sortOrder: 'asc' | 'desc',
  datetimeIndex: string,
  electricityMode: string,
  spatialAggregation: string
): ZoneRowType[] => {
  if (!data) {
    return [];
  }
  const gridState = data.data.datetimes[datetimeIndex];

  if (!gridState || !gridState.z) {
    return [];
  }

  const zoneState = gridState.z;

  const keys = Object.keys(zoneState) as Array<keyof GridState>;

  const zones = keys
    .map((key) => {
      const zoneData = zoneState[key];

      const co2intensity = zoneData
        ? getCO2IntensityByMode(zoneData, electricityMode)
        : undefined;
      const fillColor = co2intensity ? getCo2colorScale(co2intensity) : undefined;
      return {
        zoneId: key,
        color: fillColor,
        co2intensity,
        countryName: getCountryName(key),
        zoneName: getZoneName(key),
        ranking: undefined,
      };
    })
    .filter(
      (zone) =>
        Boolean(zone.co2intensity) &&
        filterZonesBySpatialAggregation(zone.zoneId, spatialAggregation) &&
        !isGenerationOnlyZone(zone.zoneId)
    );

  const orderedZones =
    sortOrder === 'asc'
      ? zones.sort((a, b) => (a.co2intensity ?? 0) - (b.co2intensity ?? 0))
      : zones.sort((a, b) => (b.co2intensity ?? 0) - (a.co2intensity ?? 0));

  return orderedZones;
};
