export const getZoneIdFromLocation = (
  map: maplibregl.Map,
  coordinates: [number, number],
  zoneSource: string
) => {
  const point = map.project(coordinates);

  // Query a larger area around the point
  const buffer = 1;
  const features = map.queryRenderedFeatures(
    [
      [point.x - buffer, point.y - buffer],
      [point.x + buffer, point.y + buffer],
    ],
    {
      layers: ['zones-clickable-layer'],
    }
  );

  return features.find((feature) => feature.source === zoneSource);
};
