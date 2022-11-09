import { GeoJsonProperties, MultiPolygon, Polygon } from 'geojson';
import { merge } from 'topojson-client';
import { Zones } from 'types';
import topo from '../../../../config/world.json';
// TODO: Investigate if we can move this step to buildtime geo scripts
export interface TopoObject {
  type: any;
  arcs: number[][][];
  properties: {
    zoneName: string;
    countryKey: string;
    countryName?: string; //Potential bug spotted, check why aggregated view value doesn't have country name
    isAggregatedView: boolean;
    isHighestGranularity: boolean;
    center: number[];
  };
}

export interface Topo {
  type: any;
  arcs: number[][][];
  objects: {
    [key: string]: TopoObject;
  };
}

const generateTopos = (): Zones => {
  const zones: Zones = {};
  const topography = topo as Topo;

  for (const k of Object.keys(topography.objects)) {
    if (!topography.objects[k].arcs) {
      continue;
    }
    const geo = {
      geometry: merge(topography as any, [topography.objects[k]]),
      properties: topography.objects[k].properties,
    };
    // Exclude zones with null geometries.
    if (geo.geometry) {
      zones[k] = geo;
    }
  }
  return zones;
};

export default generateTopos;
