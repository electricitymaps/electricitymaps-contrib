import { multiPolygon } from '@turf/turf';
import { merge } from 'topojson-client';
import { MapGeometries, Theme } from 'types';
import { ToggleOptions } from 'utils/constants';
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

/**
 * This function takes the topojson file and converts it to a geojson file
 */
const generateTopos = (theme: Theme, spatialAggregate: string): MapGeometries => {
  const geometries: MapGeometries = { features: [], type: 'FeatureCollection' };
  const topography = topo as Topo;

  for (const k of Object.keys(topography.objects)) {
    if (!topography.objects[k].arcs) {
      continue;
    }

    // Exclude if spatial aggregate is on and the feature is not highest granularity
    if (
      spatialAggregate === ToggleOptions.OFF &&
      !topography.objects[k].properties.isHighestGranularity
    ) {
      continue;
    }

    const topoObject = merge(topography, [topography.objects[k]]);
    const mp = multiPolygon(topoObject.coordinates, {
      zoneId: topography.objects[k].properties.zoneName,
      color: theme.nonClickableFill,
      ...topography.objects[k].properties,
    });

    geometries.features.push(mp);
  }
  return geometries;
};

export default generateTopos;
