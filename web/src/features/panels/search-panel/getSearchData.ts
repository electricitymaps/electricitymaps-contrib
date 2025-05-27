import useGetSolarAssets from 'api/getSolarAssets';
import { t } from 'i18next';
import { useAtomValue } from 'jotai';
import { useEffect, useState } from 'react';
import { GridState } from 'types';
import { isSolarAssetsLayerEnabledAtom } from 'utils/state/atoms';

import { ZoneRowType } from './ZoneList';

// Extended types for search results
export type SearchResultType = ZoneRowType | SolarAssetRowType;

export interface SolarAssetRowType {
  type: 'solar';
  id: string;
  name: string;
  country?: string;
  capacity?: string;
  coordinates?: [number, number];
  status?: string;
}

export const getAllZones = (language: string) => {
  // Get all zone data directly from translations
  const zoneData = t('zoneShortName', { returnObjects: true }) as Record<
    string,
    ZoneRowType
  >;

  // If current language is not English, also get English translations
  if (language !== 'en') {
    const englishZoneData = t('zoneShortName', {
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

// Hook to get all solar assets for search
export const useGetSolarAssetsForSearch = () => {
  const isSolarAssetsLayerEnabled = useAtomValue(isSolarAssetsLayerEnabledAtom);
  const { data: geoJsonData, isLoading, error } = useGetSolarAssets();
  const [solarAssets, setSolarAssets] = useState<SolarAssetRowType[]>([]);

  useEffect(() => {
    if (geoJsonData && 'features' in geoJsonData && Array.isArray(geoJsonData.features)) {
      // Process GeoJSON features into a searchable format
      const assets = geoJsonData.features
        .filter(
          (feature) =>
            feature?.properties?.name &&
            feature?.geometry?.type === 'Point' &&
            Array.isArray(feature?.geometry?.coordinates) &&
            isSolarAssetsLayerEnabled
        )
        .map((feature) => {
          // Ensure we use the correct ID format that matches what the map expects
          // The map layer is using 'name' as the promoteId in the source
          const id = feature.properties.name;

          return {
            type: 'solar' as const,
            id: String(id),
            name: feature.properties.name,
            country: feature.properties.country,
            capacity: feature.properties.capacity_mw
              ? `${Number.parseFloat(String(feature.properties.capacity_mw)).toFixed(
                  1
                )} MW`
              : undefined,
            coordinates: feature.geometry.coordinates.slice(0, 2) as [number, number],
            status: feature.properties.status,
          };
        });

      setSolarAssets(assets);
    }
  }, [geoJsonData, isSolarAssetsLayerEnabled]);

  return { solarAssets, isLoading, error };
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

// Filter solar assets based on search term
export const getFilteredSolarAssets = (
  searchTerm: string,
  solarAssets: SolarAssetRowType[]
): SolarAssetRowType[] => {
  if (!searchTerm) {
    return [];
  }

  const searchLower = searchTerm.toLowerCase();

  return solarAssets.filter(
    (asset) =>
      asset.name.toLowerCase().includes(searchLower) ||
      (asset.country && asset.country.toLowerCase().includes(searchLower)) ||
      (asset.capacity && asset.capacity.toLowerCase().includes(searchLower)) ||
      (asset.status && asset.status.toLowerCase().includes(searchLower))
  );
};

// Combined search function that returns both zone and solar asset results
export const getCombinedSearchResults = (
  searchTerm: string,
  zoneData: Record<string, ZoneRowType>,
  solarAssets: SolarAssetRowType[]
): SearchResultType[] => {
  if (!searchTerm) {
    return [];
  }

  const filteredZones = getFilteredList(searchTerm, zoneData);
  const filteredSolarAssets = getFilteredSolarAssets(searchTerm, solarAssets);

  // Combine results - zones first, then solar assets
  return [...filteredZones, ...filteredSolarAssets];
};
