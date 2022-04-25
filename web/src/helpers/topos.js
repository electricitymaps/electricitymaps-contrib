import { merge } from 'topojson';
import aggTopo from '../aggWorld.json';
import topo from '../world.json';

const constructAggregatedTopos = () => {
  const zones = {};
  aggTopo.objects.aggregatedWorld.geometries.forEach((obj) => {
    const geo = {
      geometry: merge(aggTopo, [obj]),
      properties: obj.properties,
    };
    zones[geo.properties.countryKey] = geo;
  });
  return zones;
};

const constructTopos = (shouldAggregate) => {
  if (shouldAggregate === "true") {
    return constructAggregatedTopos();
  }
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
      zones[k] = geo;
    }
  });
  return zones;
};

export default constructTopos;
