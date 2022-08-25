import { merge } from 'topojson';
import topoV1 from '../world.json';
import topoV2 from '../world2.json';
import { isAggregatedViewEnabled } from './featureFlags';

const constructTopos = () => {
  const zones = {};
  const topo = isAggregatedViewEnabled() ? topoV2 : topoV1;
  Object.keys(topo.objects).forEach((k) => {
    if (!topo.objects[k].arcs) {
      return;
    }
    const geo = {
      geometry: merge(topo, [topo.objects[k]]),
      properties: topo.objects[k].properties,
    };
    // Exclude zones with null geometries.
    if (geo.geometry) {
      zones[k] = geo;
    }
  });

  return zones;
};

export default constructTopos;
