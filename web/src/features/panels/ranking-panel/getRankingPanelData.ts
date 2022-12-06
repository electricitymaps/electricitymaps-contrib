import { getCountryName, getZoneName } from 'translation/translation';
import type { GridState } from 'types';
import { getCO2IntensityByMode } from 'utils/helpers';
import { ZoneRowType } from './ZoneList';

export const getRankedState = (
  data: GridState | undefined,
  getCo2colorScale: (co2intensity: number) => string,
  sortOrder: 'asc' | 'desc',
  datetimeIndex: string,
  electricityMode: string
): ZoneRowType[] => {
  if (!data) {
    return [];
  }
  const zonesData = data.data;
  const keys = Object.keys(zonesData.zones) as Array<keyof GridState>;

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
    .filter((zone) => zone.co2intensity !== undefined);

  const orderedZones =
    sortOrder === 'asc'
      ? zones.sort((a, b) => a.co2intensity! - b.co2intensity!)
      : zones.sort((a, b) => b.co2intensity! - a.co2intensity!);

  return orderedZones;
};
