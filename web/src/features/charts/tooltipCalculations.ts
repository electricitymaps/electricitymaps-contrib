import { ElectricityStorageType, GenerationType, ZoneDetail } from 'types';
import { getProductionCo2Intensity } from 'utils/helpers';
import { getElectricityProductionValue, getTotalElectricity } from './graphUtils';

export function getProductionTooltipData(
  selectedLayerKey: string,
  zoneDetail: ZoneDetail,
  displayByEmissions: boolean
) {
  const co2Intensity = getProductionCo2Intensity(selectedLayerKey, zoneDetail);
  const generationType = selectedLayerKey as GenerationType;
  const isStorage = generationType.includes('storage');

  const totalElectricity = getTotalElectricity(zoneDetail, displayByEmissions);
  const totalEmissions = getTotalElectricity(zoneDetail, true);

  const {
    capacity,
    production,
    storage,
    dischargeCo2IntensitySources,
    productionCo2IntensitySources,
    zoneKey,
  } = zoneDetail;

  const co2IntensitySource = isStorage
    ? (dischargeCo2IntensitySources || {})[generationType]
    : (productionCo2IntensitySources || {})[generationType];

  const generationTypeCapacity = capacity[generationType];
  const generationTypeProduction = production[generationType];
  const storageType = isStorage
    ? (generationType.replace('storage', '') as ElectricityStorageType)
    : undefined;
  const generationTypeStorage = storageType ? storage[storageType] : 0;

  const electricity = getElectricityProductionValue({
    generationTypeCapacity,
    isStorage,
    generationTypeStorage,
    generationTypeProduction,
  });
  const isExport = electricity < 0;
  const usage =
    (Number.isFinite(electricity) &&
      Math.abs(displayByEmissions ? electricity * co2Intensity * 1000 : electricity)) ||
    Number.NaN;

  const emissions =
    (Number.isFinite(electricity) && Math.abs(electricity * co2Intensity * 1000)) ||
    Number.NaN;

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
  };
}

export function getExchangeTooltipData(
  exchangeKey: string,
  zoneDetail: ZoneDetail,
  displayByEmissions: boolean
) {
  const { zoneKey, exchangeCo2Intensities, exchangeCapacities } = zoneDetail;

  const co2Intensity = exchangeCo2Intensities[exchangeKey];

  const exchangeCapacityRange = (exchangeCapacities || {})[exchangeKey];
  const exchange = (zoneDetail.exchange || {})[exchangeKey];

  const isExport = exchange < 0;

  const usage = Math.abs(displayByEmissions ? exchange * 1000 * co2Intensity : exchange);
  const totalElectricity = getTotalElectricity(zoneDetail, displayByEmissions);
  const totalCapacity = exchangeCapacityRange
    ? Math.abs(exchangeCapacityRange[isExport ? 0 : 1])
    : Number.NaN;
  const emissions = Math.abs(exchange * 1000 * co2Intensity);
  const totalEmissions = getTotalElectricity(zoneDetail, true);

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
