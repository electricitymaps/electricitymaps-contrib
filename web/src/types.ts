import { Feature, FeatureCollection, Geometry, MultiPolygon, Polygon } from '@turf/turf';

export interface GridState {
  callerLocation?: [number, number];
  data: {
    zones: { [key: string]: ZoneResponse };
    createdAt: string;
    datetime: string;
    datetimes: Array<string>;
    exchanges: { [key: string]: ExchangeResponse };
    stateAggregation: string;
  };
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

export interface ZoneResponse {
  [key: string]: {
    co2intensity: number;
    co2intensityProduction: number;
    countryCode: string;
    fossilFuelRatio: number;
    fossilFuelRatioProduction: number;
    renewableRatio: number;
    renewableRatioProduction: number;
    stateDatetime: number;
  };
}

export interface ZoneOverviewForTimePeriod {
  [dateTimeKey: string]: ZoneOverview;
}
export interface ZoneOverview {
  countryCode: string;
  co2intensity?: number;
  co2intensityProduction?: number;
  consumptionColour?: string;
  productionColour?: string;
  colorBlindConsumptionColour?: string;
  colorBlindProductionColour?: string;
  stateDatetime: string;
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
  | 'hydro storage' // storage should perhaps be separated
  | 'battery storage' // storage should perhaps be separated
  | 'wind';

export interface ZoneDetail extends ZoneOverview {
  production: { [key in GenerationType]: number }; // TODO: this assumes all modes are present
  capacity: { [key in GenerationType]: number };
  exchange: { [key: string]: number };
  co2intensity: numbewr;
  co2intensityProduction: number;
  totalco2intensity: number;
  totalCo2Import: number;
  totalCo2Discharge: number;
  totalCo2Production: number;
  totalProduction: number;
  totalImport: number;
  totalDischarge: number;
  dischargeCo2Intensities: { [key in StorageType]: number };
  productionCo2Intensities: { [key in GenerationType]: number };
  exchangeCo2Intensities: { [key: string]: number };
  storage: { [key in StorageType]: number };
  price?: {
    value: number;
    currency: string;
  };
}

export interface ZoneDetails {
  hasData: boolean;
  stateAggregation: 'daily' | 'hourly' | 'monthly' | 'yearly';
  zoneStates: ZoneDetail[];
}

export type StorageType = 'battery' | 'hydro';

export interface MapGeometries extends FeatureCollection<Geometry> {
  features: Array<MapGeometry>;
}
export interface MapGeometry extends Feature<Polygon | MultiPolygon> {
  geometry: MultiPolygon | Polygon;
  Id?: number;
  properties: {
    zoneId: string;
    color: string;
  };
}

export interface MapTheme {
  co2Scale: CO2Scale;
  clickableFill: string;
  nonClickableFill: string;
  oceanColor: string;
  strokeWidth: number;
  strokeColor: string;
}

export interface CO2Scale {
  steps: number[];
  colors: string[];
}
