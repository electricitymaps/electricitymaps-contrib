import type {
  Feature,
  FeatureCollection,
  Geometry,
  MultiPolygon,
  Polygon,
} from '@turf/turf';

export type Maybe<T> = T | null | undefined;

export type ZoneKey = string;

export interface GridState {
  callerLocation?: [number, number];
  data: {
    zones: { [key: string]: StateZoneDataForTimePeriod };
    createdAt: string;
    datetime: string;
    datetimes: Array<string>;
    exchanges: { [key: string]: ExchangeResponse };
    stateAggregation: string;
  };
}

interface StateZoneDataForTimePeriod {
  [timestamp: string]: StateZoneData;
}

export interface StateZoneData {
  co2intensity: number; //TODO https://linear.app/electricitymaps/issue/ELE-1495/update-app-backend-variable-naming-to-use-camel-case-update-the
  co2intensityProduction: number;
  fossilFuelRatio: number;
  fossilFuelRatioProduction: number;
  renewableRatio: number;
  renewableRatioProduction: number;
  stateDatetime: number;
  zoneKey: string;
  // TODO: Add spatial aggregate info to the request so we can use it for filtering in ranking panel
}

export interface ExchangeResponse {
  [datetimeKey: string]: {
    netFlow: number;
    co2intensity: number;
  };
}

export interface ExchangeOverview {
  netFlow: number;
  co2intensity: number;
}

export interface ExchangeArrowData extends ExchangeOverview {
  rotation: number;
  lonlat: [number, number];
  key: string;
}

export interface ZoneOverviewForTimePeriod {
  [dateTimeKey: string]: ZoneOverview;
}
export interface ZoneOverview {
  zoneKey: string;
  co2intensity?: number;
  co2intensityProduction?: number;
  stateDatetime: string;
  fossilFuelRatio: number;
  renewableRatio: number;
  estimationMethod: string;
}

export type GenerationType =
  | 'biomass'
  | 'coal'
  | 'gas'
  | 'hydro'
  | 'nuclear'
  | 'oil'
  | 'solar'
  | 'unknown'
  | 'geothermal'
  | 'wind';

export type ElectricityStorageType = 'hydro storage' | 'battery storage';
export type ElectricityStorageKeyType = 'battery' | 'hydro';

export type ElectricityModeType = GenerationType | ElectricityStorageType;

export type Exchange = { [key: string]: number };

export interface ZoneDetail extends ZoneOverview {
  _isFinestGranularity: boolean;
  // Capacity is only available on hourly details
  capacity?: { [key in ElectricityModeType]: number | null };
  dischargeCo2Intensities: { [key in ElectricityStorageKeyType]: number };
  dischargeCo2IntensitySources: { [key in ElectricityStorageKeyType]: string };
  exchange: Exchange;
  exchangeCapacities?: {
    [key: ZoneKey]: [number, number];
  };
  exchangeCo2Intensities: Exchange;
  fossilFuelRatio: number;
  fossilFuelRatioProduction: number;
  isValid: boolean;
  maxCapacity: number;
  maxDischarge: number;
  maxExport: number;
  maxExportCapacity: number;
  maxImport: number;
  maxImportCapacity: number;
  maxProduction: number;
  maxStorage: number;
  maxStorageCapacity: number;
  price?: {
    value: number;
    currency: string;
    disabledReason?: string;
  };
  production: { [key in GenerationType]: Maybe<number> };
  productionCo2Intensities: { [key in GenerationType]: number };
  productionCo2IntensitySources: { [key in GenerationType]: string };
  renewableRatio: number;
  renewableRatioProduction: number;
  source: string;
  storage: { [key in ElectricityStorageKeyType]: Maybe<number> };
  totalCo2Discharge: number;
  totalCo2Export: number;
  totalCo2Import: number;
  totalCo2NetExchange: number;
  totalCo2Production: number;
  totalCo2Storage: number;
  totalConsumption: number;
  totalDischarge: number;
  totalExport: number;
  totalImport: number;
  totalProduction: number;
  totalStorage: number;
}

export interface ZoneDetails {
  hasData: boolean;
  stateAggregation: 'daily' | 'hourly' | 'monthly' | 'yearly';
  zoneStates: {
    [key: string]: ZoneDetail;
  };
}

export interface MapGeometries extends FeatureCollection<Geometry> {
  features: Array<MapGeometry>;
}
export interface MapGeometry extends Feature<Polygon | MultiPolygon> {
  geometry: MultiPolygon | Polygon;
  Id?: number;
  properties: {
    zoneId: string;
    color: string;
    center: [number, number];
  };
}

export interface MapTheme {
  co2Scale: {
    steps: number[];
    colors: string[];
  };
  oceanColor: string;
  strokeWidth: number;
  strokeColor: string;
  clickableFill: string;
  nonClickableFill: string;
}
