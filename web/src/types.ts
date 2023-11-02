import type {
  Feature,
  FeatureCollection,
  Geometry,
  MultiPolygon,
  Polygon,
} from '@turf/turf';
import { LineString, MultiLineString, Point } from 'geojson';

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
  estimationMethod?: string;
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
    [key: ZoneKey]: number[];
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
  totalCo2Consumption: number;
  totalCo2Discharge: number | null;
  totalCo2Export: number | null;
  totalCo2Import: number | null;
  totalCo2NetExchange: number | null;
  totalCo2Production: number;
  totalCo2Storage: number | null;
  totalConsumption: number;
  totalDischarge: number | null;
  totalExport: number | null;
  totalImport: number | null;
  totalProduction: number | null;
  totalStorage: number | null;
}

export interface ZoneDetails {
  hasData: boolean;
  stateAggregation: 'daily' | 'hourly' | 'monthly' | 'yearly';
  zoneStates: {
    [key: string]: ZoneDetail;
  };
  zoneMessage?: { message: string; issue: string };
}

export interface GeometryProperties {
  center: [number, number];
  color: string;
  countryKey: string;
  isAggregatedView: boolean;
  isHighestGranularity: boolean;
  zoneId: string;
  zoneName: string;
}
export interface StateGeometryProperties {
  center?: [number, number];
  stateName?: string;
  stateId?: string;
}

export interface MapGeometries extends FeatureCollection<Geometry> {
  features: Array<MapGeometry>;
}

export interface StatesGeometries extends FeatureCollection<Geometry> {
  features: Array<StatesGeometry>;
}
export interface MapGeometry extends Feature<Polygon | MultiPolygon> {
  geometry: MultiPolygon | Polygon;
  Id?: number;
  properties: GeometryProperties;
}

export interface StatesGeometry extends Feature<LineString | MultiLineString | Point> {
  geometry: LineString | MultiLineString | Point;
  Id?: number;
  properties: StateGeometryProperties;
}

export interface MapTheme {
  co2Scale: {
    steps: number[];
    colors: string[];
  };
  oceanColor: string;
  strokeWidth: number;
  strokeColor: string;
  stateBorderColor: string;
  clickableFill: string;
  nonClickableFill: string;
}
