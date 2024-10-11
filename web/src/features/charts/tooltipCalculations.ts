import {
  ElectricityModeType,
  ElectricityStorageKeyType,
  GenerationType,
  ZoneDetail,
} from 'types';
import { getProductionCo2Intensity } from 'utils/helpers';

import {
  getElectricityProductionValue,
  getTotalElectricityAvailable,
  getTotalEmissionsAvailable,
} from './graphUtils';

export function getProductionTooltipData(
  selectedLayerKey: ElectricityModeType,
  zoneDetail: ZoneDetail,
  displayByEmissions: boolean,
  isConsumption: boolean
) {
  const co2Intensity = getProductionCo2Intensity(selectedLayerKey, zoneDetail);
  const isStorage = selectedLayerKey.includes('storage');

  const generationType = isStorage
    ? (selectedLayerKey.replace(' storage', '') as GenerationType)
    : (selectedLayerKey as GenerationType);

  const storageKey = generationType as ElectricityStorageKeyType;

  const totalElectricity = getTotalElectricityAvailable(zoneDetail, isConsumption);
  const totalEmissions = getTotalEmissionsAvailable(zoneDetail, isConsumption);

  const {
    capacity,
    production,
    storage,
    dischargeCo2IntensitySources,
    productionCo2IntensitySources,
    zoneKey,
    capacitySources,
  } = zoneDetail;

  const co2IntensitySource = isStorage
    ? (dischargeCo2IntensitySources || {})[storageKey]
    : (productionCo2IntensitySources || {})[generationType];

  const generationTypeCapacity = capacity ? capacity[selectedLayerKey] : undefined;
  const generationTypeProduction = production[generationType];
  const capacitySource = generationTypeCapacity
    ? capacitySources?.[selectedLayerKey]
    : undefined;

  const generationTypeStorage = storageKey ? storage[storageKey] : 0;

  const electricity = getElectricityProductionValue({
    generationTypeCapacity,
    isStorage,
    generationTypeStorage,
    generationTypeProduction,
  });
  const isExport = electricity ? electricity < 0 : false;

  let usage = electricity === 0 ? 0 : Number.NaN;
  let emissions = electricity === 0 ? 0 : Number.NaN;

  if (electricity && Number.isFinite(electricity)) {
    usage = Math.abs(
      displayByEmissions ? electricity * co2Intensity * 1000 : electricity
    );
    emissions = Math.abs(electricity * co2Intensity * 1000);
  }

  return {
    co2Intensity,
    co2IntensitySource,
    displayByEmissions,
    totalElectricity,
    totalEmissions,
    emissions,
    usage,
    zoneKey,
    isExport,
    production: generationTypeProduction,
    capacity: generationTypeCapacity,
    storage: generationTypeStorage,
    capacitySource,
  };
}

export function getExchangeTooltipData(
  exchangeKey: string,
  zoneDetail: ZoneDetail,
  displayByEmissions: boolean
) {
  const { zoneKey, exchangeCo2Intensities, exchangeCapacities } = zoneDetail;

  const co2Intensity = exchangeCo2Intensities?.[exchangeKey];
  const exchangeCapacityRange = exchangeCapacities?.[exchangeKey];
  const exchange = zoneDetail?.exchange?.[exchangeKey];

  const isExport = exchange < 0;

  const usage = Math.abs(displayByEmissions ? exchange * co2Intensity * 1000 : exchange);
  const totalElectricity = getTotalElectricityAvailable(zoneDetail, true);
  const totalCapacity = exchangeCapacityRange
    ? Math.abs(exchangeCapacityRange[isExport ? 0 : 1])
    : undefined;
  const emissions = Math.abs(exchange * co2Intensity * 1000);
  const totalEmissions = getTotalEmissionsAvailable(zoneDetail, true);

  return {
    co2Intensity,
    displayByEmissions,
    totalElectricity,
    totalEmissions,
    emissions,
    usage,
    zoneKey,
    isExport,
    capacity: totalCapacity,
  };
}
