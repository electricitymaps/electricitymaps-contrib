import { FeatureCollection, Feature, MultiPolygon, Polygon } from '@turf/turf';
import { config } from './generateWorld';

export type GeoConfig = typeof config;

export interface ZoneConfig {
  subZoneNames?: string[];
  bounding_box: number[][];
  timezone: string;
  [key: string]: any;
}

export interface ZonesConfig {
  [key: string]: ZoneConfig;
}

export interface ExchangeConfig {
  capacity?: [number, number];
  lonlat: [number, number];
  rotation: number;
  [key: string]: any;
  // The following properties are removed from the generated exchange config
  // comment?: string;
  // _comment?: string;
  // parsers?: {
  //   exchange?: string;
  //   exchangeForecast?: string;
  // };
}

export interface ExchangesConfig {
  [key: string]: ExchangeConfig;
}

export declare type FeatureProperties = {
  zoneName: string;
  countryKey: string;
  countryName: string;
  isAggregatedView?: boolean;
  isHighestGranularity?: boolean;
  isCombined?: boolean;
};

export interface WorldFeatureCollection extends FeatureCollection {
  features: Feature<MultiPolygon | Polygon, FeatureProperties>[];
}
