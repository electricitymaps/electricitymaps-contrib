import { Feature, FeatureCollection, MultiPolygon, Polygon } from '@turf/turf';

import { GEO_CONFIG } from './generateWorld';

export type GeoConfig = typeof GEO_CONFIG;

export interface ZoneConfig {
  aggregates_displayed?: string[];
  subZoneNames?: string[];
  bounding_box?: number[][];
  contributors?: string[];
  disclaimer?: string;
  estimation_method?: string;
  generation_only?: boolean;
  parsers?: {
    consumption?: string;
    consumptionForecast?: string;
    generationForecast?: string;
    price?: string;
    production?: string;
    productionPerModeForecast?: string;
    productionPerUnit?: string;
  };
  [key: string]: any;
}

export interface OptimizedZoneConfig
  extends Omit<ZoneConfig, 'contributors' | 'parsers'> {
  contributors: number[];
  parsers: boolean;
}

export interface ZonesConfig {
  [key: string]: ZoneConfig;
}

export interface OptimizedZonesConfig {
  [key: string]: OptimizedZoneConfig;
}

export interface CombinedZonesConfig {
  contributors: string[];
  zones: OptimizedZonesConfig;
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
  isAggregatedView?: boolean;
  isHighestGranularity?: boolean;
  isCombined?: boolean;
};

export interface WorldFeatureCollection extends FeatureCollection {
  features: Feature<MultiPolygon | Polygon, FeatureProperties>[];
}
