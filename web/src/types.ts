import { Feature, FeatureCollection, Geometry, MultiPolygon, Polygon } from '@turf/turf';

export interface GridState {
  callerLocation?: [number, number];
  data: {
    zones: { [key: string]: ZoneResponse };
    createdAt: string;
    datetime: string;
    datetimes: Array<string>;
    exchanges: { [key: string]: [unknown] };
    stateAggregation: string;
  };
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
  consumptionColour?: string;
  productionColour?: string;
  colorBlindConsumptionColour?: string;
  colorBlindProductionColour?: string;
  stateDatetime: string;
}

export interface ZoneDetail extends ZoneOverview {
  production: GenerationTypes;
  capacity: GenerationTypes;
}

export interface ZoneDetails {
  hasData: boolean;
  stateAggregation: 'daily' | 'hourly' | 'monthly' | 'yearly';
  zoneStates: ZoneDetail[];
}

export interface GenerationTypes {
  biomass?: number;
  coal?: number;
  gas?: number;
  geothermal?: number;
  hydro?: number;
  nuclear?: number;
  oil?: number;
  solar?: number;
  wind?: number;
  unknown?: number;
}

export interface StorageTypes {
  battery: number;
  hydro: number;
}

export interface MapGrid extends FeatureCollection<Geometry> {
  features: Array<MapZone>;
}
export interface MapZone extends Feature<Polygon | MultiPolygon> {
  geometry: MultiPolygon | Polygon;
  Id?: number;
  properties: {
    zoneData: ZoneOverviewForTimePeriod;
    zoneId: string;
    color: string;
  };
}
