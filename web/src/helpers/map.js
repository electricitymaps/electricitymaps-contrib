import { max, min, mean, isArray } from 'lodash';

export function getCenteredLocationViewport([longitude, latitude]) {
  return {
    width: window.innerWidth,
    height: window.innerHeight,
    latitude,
    longitude,
    zoom: 4,
  };
}

// If the panel is open the zoom doesn't appear perfectly centered because
// it centers on the whole window and not just the visible map part, which
// is something one could fix in the future.
// TODO: this could be done build time instead of runtime
export function getCenteredZoneViewport(zone) {
  const longitudes = [];
  const latitudes = [];

  zone.geometry.coordinates.forEach((geojson) => {
    // There seems to be an inconsistency in the generate-topojson script:
    const data = isArray(geojson[0][0]) ? geojson[0] : geojson;
    data.forEach(([longitude, latitude]) => {
      longitudes.push(longitude);
      latitudes.push(latitude);
    });
  });

  return getCenteredLocationViewport([
    mean([min(longitudes), max(longitudes)]),
    mean([min(latitudes), max(latitudes)]),
  ]);
}
