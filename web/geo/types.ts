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
export declare type FeatureProperties = {
  zoneName: string;
  countryKey: string;
  countryName: string;
  isAggregatedView?: boolean;
  isHighestGranularity?: boolean;
  isCombined?: boolean;
  [name: string]: any;
};

export interface WorldFeatureCollection extends FeatureCollection {
  features: Feature<MultiPolygon | Polygon, FeatureProperties>[];
}
