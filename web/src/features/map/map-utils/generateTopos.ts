import { multiPolygon } from '@turf/helpers';
import { merge } from 'topojson-client';
import { MapGeometries, MapTheme } from 'types';
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
    center: [number, number];
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
const generateTopos = (theme: MapTheme, spatialAggregate: string): MapGeometries => {
  const geometries: MapGeometries = { features: [], type: 'FeatureCollection' };
  // Casting to unknown first to allow using [number, number] for center property
  const topography = topo as unknown as Topo;

  for (const k of Object.keys(topography.objects)) {
    if (!topography.objects[k].arcs) {
      continue;
    }

    // Exclude if spatial aggregate is on and the feature is not highest granularity
    // I.e excludes SE if spatialAggregate is off.
    if (
      spatialAggregate === ToggleOptions.OFF &&
      !topography.objects[k].properties.isHighestGranularity
    ) {
      continue;
    }

    // Exclude if spatial aggregate is off and the feature is aggregated view,
    // I.e excludes SE-SE4 if spatialAggregate is on.
    if (
      spatialAggregate === ToggleOptions.ON &&
      !topography.objects[k].properties.isAggregatedView
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
