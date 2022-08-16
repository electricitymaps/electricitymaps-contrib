// @ts-expect-error TS(7016): Could not find a declaration file for module 'topo... Remove this comment to see the full error message
import { merge } from 'topojson';
// @ts-expect-error TS(2732): Cannot find module '../world.json'. Consider using... Remove this comment to see the full error message
import topo from '../world.json';

const constructTopos = () => {
  const zones = {};
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
      // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
      zones[k] = geo;
    }
  });

  return zones;
};

export default constructTopos;
