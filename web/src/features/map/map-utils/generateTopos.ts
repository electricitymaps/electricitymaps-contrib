import { multiLineString, multiPolygon } from '@turf/helpers';
import { merge, mesh } from 'topojson-client';
import {
  GeometryProperties,
  MapGeometries,
  MapTheme,
  StateGeometryProperties,
  StatesGeometries,
} from 'types';
import { SpatialAggregate } from 'utils/constants';

import statesTopo from '../../../../config/usa_states.json';
import worldTopo from '../../../../config/world.json';
// TODO: Investigate if we can move this step to buildtime geo scripts
export interface TopoObject {
  type: 'MultiPolygon';
  arcs: number[][][];
  properties: Omit<GeometryProperties, 'color' | 'zoneId'>;
}

export interface Topo {
  type: 'Topology';
  arcs: number[][][];
  objects: {
    [key: string]: TopoObject;
  };
}

export interface StatesTopoObject {
  type: 'MultiLineString';
  arcs: Arc[];
  properties: Omit<StateGeometryProperties, 'zoneId'>;
}

type Arc = Positions[];
type Positions = number[];

export interface StatesTopo {
  type: 'Topology';
  arcs: Arc[];
  objects: any;
}

/**
 * This function takes the topojson file and converts it to a geojson file
 */
const generateTopos = (
  theme: MapTheme,
  spatialAggregate: SpatialAggregate
): { worldGeometries: MapGeometries; statesGeometries: StatesGeometries } => {
  const worldGeometries: MapGeometries = { features: [], type: 'FeatureCollection' };
  const statesGeometries: StatesGeometries = { features: [], type: 'FeatureCollection' };
  // Casting to unknown first to allow using [number, number] for center property
  const worldTopography = worldTopo as unknown as Topo;
  const statesTopography = statesTopo as unknown as StatesTopo;

  for (const k of Object.keys(worldTopography.objects)) {
    if (!worldTopography.objects[k].arcs) {
      continue;
    }

    // Exclude if spatial aggregate is on and the feature is not highest granularity
    // I.e excludes SE if spatialAggregate is off.
    if (
      spatialAggregate === SpatialAggregate.ZONE &&
      !worldTopography.objects[k].properties.isHighestGranularity
    ) {
      continue;
    }

    // Exclude if spatial aggregate is off and the feature is aggregated view,
    // I.e excludes SE-SE4 if spatialAggregate is on.
    if (
      spatialAggregate === SpatialAggregate.COUNTRY &&
      !worldTopography.objects[k].properties.isAggregatedView
    ) {
      continue;
    }

    const topoObject = merge(worldTopography, [worldTopography.objects[k]]);
    const mp = multiPolygon(topoObject.coordinates, {
      zoneId: worldTopography.objects[k].properties.zoneName,
      color: theme.nonClickableFill,
      ...worldTopography.objects[k].properties,
    });

    worldGeometries.features.push(mp);
  }
  for (const k of Object.keys(statesTopography.objects)) {
    if (!statesTopography.objects[k].arcs) {
      continue;
    }
    const topoObject = mesh(statesTopography, statesTopography.objects[k]);

    const stateMp = multiLineString(topoObject.coordinates, {
      ...statesTopography.objects[k].properties,
    });
    statesGeometries.features.push(stateMp);
  }

  return { worldGeometries, statesGeometries };
};

export default generateTopos;
