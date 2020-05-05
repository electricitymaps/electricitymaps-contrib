import { max, min, mean } from 'lodash';

// If the panel is open the zoom doesn't appear perfectly centered because
// it centers on the whole window and not just the visible map part, which
// is something one could fix in the future.
export function getCenteredZoneViewport(zone) {
  const longitudes = [];
  const latitudes = [];

  zone.geometry.coordinates.forEach((geojson) => {
    geojson[0].forEach(([longitude, latitude]) => {
      longitudes.push(longitude);
      latitudes.push(latitude);
    });
  });

  return {
    latitude: mean([min(latitudes), max(latitudes)]),
    longitude: mean([min(longitudes), max(longitudes)]),
    zoom: 4,
  };
}

export function getCenteredLocationViewport([longitude, latitude]) {
  return { latitude, longitude, zoom: 4 };
}
