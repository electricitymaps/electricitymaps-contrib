import { t } from 'i18next';
import { GridState } from 'types';

import { ZoneRowType } from './ZoneList';

export const getAllZones = (language: string) => {
  // Get all zone data directly from translations
  const zoneData = t(($) => $.zoneShortName, {
    returnObjects: true,
  }) as Record<string, ZoneRowType>;

  // If current language is not English, also get English translations
  if (language !== 'en') {
    const englishZoneData = t(($) => $.zoneShortName, {
      lng: 'en',
      returnObjects: true,
    }) as Record<string, ZoneRowType>;

    // Merge English translations under same key
    for (const [key, value] of Object.entries(zoneData)) {
      zoneData[key] = {
        ...value,
        englishZoneName: englishZoneData[key].zoneName,
      };
    }
  }

  return zoneData;
};

export const getFilteredList = (
  searchTerm: string,
  zoneData: Record<string, ZoneRowType>
): ZoneRowType[] => {
  if (!searchTerm) {
    return [];
  }

  // Filter zones based on search term
  const filtered = Object.entries(zoneData).filter(([zoneKey, zone]) => {
    const searchLower = searchTerm.toLowerCase();
    // TODO: If adding fuzzy search, we might need to change the zoneKey to be part of the same object instead
    return (
      zoneKey.toString().toLowerCase().includes(searchLower) ||
      zone.zoneName?.toLowerCase().includes(searchLower) ||
      zone.countryName?.toLowerCase().includes(searchLower) ||
      zone.seoZoneName?.toLowerCase().includes(searchLower) ||
      zone.displayName?.toLowerCase().includes(searchLower) ||
      zone.englishZoneName?.toLowerCase().includes(searchLower)
    );
  });

  // Convert filtered entries to array of ZoneRowType
  return filtered.map(([zoneKey, zone]) => ({
    ...zone,
    zoneId: zoneKey as keyof GridState,
  }));
};
