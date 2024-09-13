import useGetZone from 'api/getZone';
import { useMemo } from 'react';
import { ElectricityModeType, ZoneDetails } from 'types';

const useZoneDataSources = () => {
  const { data: zoneData } = useGetZone();

  return useMemo(
    () => ({
      capacitySources: getCapacitySources(zoneData),
      powerGenerationSources: getPowerGenerationSources(zoneData),
      emissionFactorSources: getEmissionFactorSource(zoneData),
      emissionFactorSourcesToProductionSources:
        getEmissionFactorSourcesToProductionSource(zoneData),
    }),
    [zoneData]
  );
};

export default useZoneDataSources;

const getCapacitySources = (zoneData?: ZoneDetails): string[] => {
  const capacitySources: string[] = [];
  if (zoneData) {
    for (const state of Object.values(zoneData.zoneStates)) {
      const currentSources = extractUniqueSourcesFromDictionary(state.capacitySources);
      for (const source of currentSources) {
        if (!capacitySources.includes(source)) {
          capacitySources.push(source);
        }
      }
    }
  }
  return capacitySources;
};

const extractUniqueSourcesFromDictionary = (
  sourceDict:
    | {
        [key in ElectricityModeType]: string[] | null;
      }
    | undefined
): Set<string> => {
  const sourcesWithoutDuplicates: Set<string> = new Set();
  if (!sourceDict) {
    return sourcesWithoutDuplicates;
  }
  for (const key of Object.keys(sourceDict)) {
    const capacitySource = sourceDict?.[key as ElectricityModeType];
    if (capacitySource != null) {
      for (const source of capacitySource) {
        sourcesWithoutDuplicates.add(source);
      }
    }
  }
  return sourcesWithoutDuplicates;
};

const getPowerGenerationSources = (zoneData?: ZoneDetails) => {
  const sourceSet = new Set<string>();
  if (zoneData) {
    for (const state of Object.values(zoneData.zoneStates)) {
      const currentSources = state.source;
      for (const source of currentSources) {
        sourceSet.add(source);
      }
    }
  }

  return [...sourceSet];
};

const getEmissionFactorSource = (zoneData?: ZoneDetails) => {
  const emissionFactorSources = new Set<string>();

  if (zoneData) {
    const processSources = (sources: Record<string, string>) => {
      for (const source of Object.entries(sources)) {
        for (const emissionFactorSource of source[1].split('; ')) {
          if (!emissionFactorSource.startsWith('assumes')) {
            emissionFactorSources.add(emissionFactorSource);
          }
        }
      }
    };

    for (const state of Object.values(zoneData.zoneStates)) {
      processSources(state.productionCo2IntensitySources);
      processSources(state.dischargeCo2IntensitySources);
    }
  }

  return [...emissionFactorSources];
};

const getEmissionFactorSourcesToProductionSource = (zoneData?: ZoneDetails) => {
  const emissionFactorsourceToProductionSource = {};

  if (zoneData) {
    for (const state of Object.values(zoneData.zoneStates)) {
      updateEmissionFactorSourcesWithProductionSources(
        state.dischargeCo2IntensitySources,
        emissionFactorsourceToProductionSource,
        true
      );
      updateEmissionFactorSourcesWithProductionSources(
        state.productionCo2IntensitySources,
        emissionFactorsourceToProductionSource
      );
    }
  }

  return emissionFactorsourceToProductionSource;
};

const updateEmissionFactorSourcesWithProductionSources = (
  sources: { [key: string]: string },
  emissionFactorsourceToProductionSource: { [key: string]: string[] },
  storageType?: boolean
) => {
  for (const entry of Object.entries(sources)) {
    for (const emissionFactorSource of entry[1].split('; ')) {
      const productionSources = getProductionSourcesToAdd(
        storageType ? `${entry[0]} storage` : entry[0],
        emissionFactorsourceToProductionSource[emissionFactorSource],
        emissionFactorSource
      );
      if (productionSources.length > 0) {
        emissionFactorsourceToProductionSource[emissionFactorSource] = productionSources;
      }
    }
  }
};

const getProductionSourcesToAdd = (
  productionSource: string,
  productionSourceArray: string[] | undefined,
  emissionFactorSource: string
): string[] => {
  if (emissionFactorSource.startsWith('assumes')) {
    return [];
  } else if (productionSourceArray == undefined) {
    return [productionSource];
  } else if (!productionSourceArray?.includes(productionSource)) {
    productionSourceArray?.push(productionSource);
  }
  return productionSourceArray;
};
