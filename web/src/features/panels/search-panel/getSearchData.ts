import { t } from 'i18next';
import { GridState } from 'types';

import { ZoneRowType } from './ZoneList';

export const getAllZones = () => {
  // Get all zone data directly from translations
  const zoneData = t('zoneShortName', { returnObjects: true }) as Record<
    string,
    ZoneRowType
  >;

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
    return (
      zoneKey.toString().toLowerCase().includes(searchLower) ||
      zone.zoneName?.toLowerCase().includes(searchLower) ||
      zone.countryName?.toLowerCase().includes(searchLower) ||
      zone.seoZoneName?.toLowerCase().includes(searchLower) ||
      zone.displayName?.toLowerCase().includes(searchLower)
    );
  });

  // Convert filtered entries to array of ZoneRowType
  return filtered.map(([zoneKey, zone]) => ({
    ...zone,
    zoneId: zoneKey as keyof GridState,
  }));
};
