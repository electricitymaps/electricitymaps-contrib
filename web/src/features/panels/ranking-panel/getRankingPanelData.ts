import { getCountryName, getZoneName } from 'translation/translation';
import type { GridState, ZoneKey } from 'types';
import { getCO2IntensityByMode } from 'utils/helpers';
import { ZoneRowType } from './ZoneList';
import { getHasSubZones } from '../zone/util';
import { SpatialAggregate } from 'utils/constants';

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
  const zonesData = data.data;
  const keys = Object.keys(zonesData.zones) as Array<keyof GridState>;

  console.log('mode', zonesData);
  if (!keys) {
    return [];
  }
  const zones = keys
    .map((key) => {
      const zoneData = zonesData.zones[key][datetimeIndex];

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
        zone.co2intensity !== undefined &&
        filterZonesBySpatialAggregation(zone.zoneId, spatialAggregation)
    );

  const orderedZones =
    sortOrder === 'asc'
      ? zones.sort((a, b) => a.co2intensity! - b.co2intensity!)
      : zones.sort((a, b) => b.co2intensity! - a.co2intensity!);

  return orderedZones;
};
