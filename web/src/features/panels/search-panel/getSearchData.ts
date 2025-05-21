import { RawDataCenter } from 'features/data-centers/DataCenterLayer';
import { t } from 'i18next';
import { GridState } from 'types';

import { SearchResultRowType } from './ZoneList';

export interface ZoneRowType {
  zoneId: keyof GridState;
  countryName?: string;
  zoneName?: string;
  fullZoneName?: string;
  displayName?: string;
  seoZoneName?: string;
  englishZoneName?: string;
}

export const getAllZones = (language: string) => {
  // Get all zone data directly from translations
  const zoneData = t('zoneShortName', { returnObjects: true }) as Record<
    string,
    ZoneRowType
  >;

  const searchData = {} as Record<string, SearchResultRowType>;
  for (const [key, value] of Object.entries(zoneData)) {
    searchData[key] = {
      key: key,
      displayName: value.zoneName,
      secondaryDisplayName: value.countryName,
      flagZoneId: key as keyof GridState,
      link: `/zones/${key}`,
    };

    // If current language is not English, also get English translations
    if (language !== 'en') {
      const englishZoneData = t('zoneShortName', {
        lng: 'en',
        returnObjects: true,
      }) as Record<string, ZoneRowType>;
      searchData[key].englishDisplayName = englishZoneData[key].zoneName;
    }
  }

  return searchData;
};

export const getFilteredZoneList = (
  searchTerm: string,
  zoneData: Record<string, SearchResultRowType>
): SearchResultRowType[] => {
  if (!searchTerm) {
    return [];
  }

  // Filter zones based on search term
  const filtered = Object.entries(zoneData).filter(([zoneKey, zone]) => {
    const searchLower = searchTerm.toLowerCase();
    // TODO: If adding fuzzy search, we might need to change the zoneKey to be part of the same object instead
    return (
      zoneKey.toString().toLowerCase().includes(searchLower) ||
      zone.displayName?.toLowerCase().includes(searchLower) ||
      zone.secondaryDisplayName?.toLowerCase().includes(searchLower) ||
      zone.englishDisplayName?.toLowerCase().includes(searchLower)
    );
  });

  // Convert filtered entries to array of ZoneRowType
  return filtered.map(([_, value]) => value);
};

export const getFilteredDataCenterList = (
  searchTerm: string,
  dataCenterData: Record<string, RawDataCenter>
): SearchResultRowType[] => {
  if (!searchTerm) {
    return [];
  }

  return Object.entries(dataCenterData)
    .filter(([key, data]) => {
      const searchLower = searchTerm.toLowerCase();
      return (
        key.toLowerCase().includes(searchLower) ||
        data.region.toLowerCase().includes(searchLower)
      );
    })
    .map(([key, data]) => ({
      key: key,
      link: `/data-centers/${key}`,
      displayName: data.displayName,
      secondaryDisplayName: data.region,
    }));
};
