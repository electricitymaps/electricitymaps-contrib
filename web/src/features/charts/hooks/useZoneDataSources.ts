import useGetZone from 'api/getZone';
import { ElectricityModeType, ZoneDetails } from 'types';

export default function useZoneDataSources() {
  const { data: zoneData, isSuccess } = useGetZone();

  if (!isSuccess) {
    return {
      capacitySources: [],
      powerGenerationSources: [],
      emissionFactorSources: [],
      emissionFactorSourcesToProductionSources: {},
    };
  }

  const capacitySources = getCapacitySources(zoneData);
  const powerGenerationSources = getPowerGenerationSources(zoneData);
  const emissionFactorSourcesToProductionSources =
    getEmissionFactorSourcesToProductionSource(zoneData);
  const emissionFactorSources = getEmissionFactorSource(zoneData);

  return {
    capacitySources,
    powerGenerationSources,
    emissionFactorSources,
    emissionFactorSourcesToProductionSources,
  };
}

function getCapacitySources(zoneData: ZoneDetails) {
  const capacitySources: string[] = [];
  for (const state of Object.values(zoneData.zoneStates)) {
    const currentSources = extractUniqueSourcesFromDictionary(state.capacitySources);
    for (const source of currentSources) {
      if (!capacitySources.includes(source)) {
        capacitySources.push(source);
      }
    }
  }
  return capacitySources;
}

function extractUniqueSourcesFromDictionary(
  sourceDict:
    | {
        [key in ElectricityModeType]: string[] | null;
      }
    | undefined
): Set<string> {
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
}

function getPowerGenerationSources(zoneData: ZoneDetails) {
  const sourceSet = new Set<string>();

  for (const state of Object.values(zoneData.zoneStates)) {
    const currentSources = state.source;
    for (const source of currentSources) {
      sourceSet.add(source);
    }
  }

  const sources = [...sourceSet];
  return sources;
}

function getEmissionFactorSource(zoneData: ZoneDetails) {
  const emissionFactorSources = new Set<string>();

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

  return [...emissionFactorSources];
}

function getEmissionFactorSourcesToProductionSource(zoneData: ZoneDetails) {
  const emissionFactorsourceToProductionSource = {};

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

  return emissionFactorsourceToProductionSource;
}

function updateEmissionFactorSourcesWithProductionSources(
  sources: { [key: string]: string },
  emissionFactorsourceToProductionSource: { [key: string]: string[] },
  storageType?: boolean
) {
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
}

function getProductionSourcesToAdd(
  productionSource: string,
  productionSourceArray: string[] | undefined,
  emissionFactorSource: string
): string[] {
  if (emissionFactorSource.startsWith('assumes')) {
    return [];
  } else if (productionSourceArray == undefined) {
    return [productionSource];
  } else if (!productionSourceArray?.includes(productionSource)) {
    productionSourceArray?.push(productionSource);
  }
  return productionSourceArray;
}
