import { multiLineString, multiPolygon } from '@turf/helpers';
import { Feature, Point } from 'geojson';
import { merge, mesh } from 'topojson-client';
import { Objects, Topology } from 'topojson-specification';
import {
  GeometryProperties,
  MapGeometries,
  MapTheme,
  StateGeometryProperties,
  StatesGeometries,
} from 'types';
import { SpatialAggregate } from 'utils/constants';

import stateBordersTopo from '../../../../config/usa_states.json';
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

type Arc = Positions[];
type Positions = number[];
export interface StateBordersTopo extends Topology {
  type: 'Topology';
  arcs: Arc[];
  objects: Objects<StateGeometryProperties>;
}

export interface StateBordersTopoObject {
  type: 'MultiLineString' | 'Point';
  arcs: TopoJSON.ArcIndexes[];
  properties: Omit<StateGeometryProperties, 'zoneId'>;
}

function isTopoObject(object: unknown): object is TopoObject {
  return (
    typeof object === 'object' &&
    object !== null &&
    'arcs' in object &&
    'properties' in object
  );
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
  const stateBordersTopography = stateBordersTopo as unknown as StateBordersTopo;

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
  for (const k of Object.keys(stateBordersTopography.objects)) {
    const topoObject = stateBordersTopography.objects[k];

    if (isTopoObject(topoObject)) {
      const meshedObject = mesh(stateBordersTopography, topoObject);
      const stateMp = multiLineString(meshedObject.coordinates, {});
      statesGeometries.features.push(stateMp);
    } else if (topoObject.type === 'Point' && topoObject.properties) {
      const statePoint: Feature<Point, StateGeometryProperties> = {
        type: 'Feature',
        properties: topoObject.properties,
        geometry: { type: 'Point', coordinates: topoObject.coordinates },
      };
      statesGeometries.features.push(statePoint);
    }
  }

  return { worldGeometries, statesGeometries };
};

export default generateTopos;
