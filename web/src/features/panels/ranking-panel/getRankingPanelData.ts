import { getCountryName, getZoneName } from 'translation/translation';
import type { GridState, ZoneKey } from 'types';
import { SpatialAggregate } from 'utils/constants';
import { getCO2IntensityByMode } from 'utils/helpers';

import { getHasSubZones } from '../zone/util';
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
  const gird = data.data.datetimes[datetimeIndex];
  if (!gird) {
    return [];
  }
  if (!gird.z) {
    return [];
  }
  const keys = Object.keys(gird.z) as Array<keyof GridState>;

  if (!keys) {
    return [];
  }
  const zones = keys
    .map((key) => {
      const zoneData = gird.z[key];

      const co2intensity = zoneData
        ? getCO2IntensityByMode(zoneData, electricityMode)
        : undefined;
      const fillColor = co2intensity ? getCo2colorScale(co2intensity) : undefined;
      return {
        zoneId: key,
        color: fillColor,
        ci: co2intensity,
        countryName: getCountryName(key),
        zoneName: getZoneName(key),
        ranking: undefined,
      };
    })
    .filter(
      (zone) =>
        zone.ci !== undefined &&
        filterZonesBySpatialAggregation(zone.zoneId, spatialAggregation)
    );

  const orderedZones =
    sortOrder === 'asc'
      ? zones.sort((a, b) => a.ci! - b.ci!)
      : zones.sort((a, b) => b.ci! - a.ci!);

  return orderedZones;
};
