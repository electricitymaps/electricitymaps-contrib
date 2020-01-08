const d3 = Object.assign(
  {},
  require('d3-array'),
);

export function centerOnZoneName(state, zoneMap, zoneName, zoomLevel) {
  if (typeof zoneMap === 'undefined') { return; }
  const selectedZone = state.data.grid.zones[zoneName];
  const selectedZoneCoordinates = [];
  selectedZone.geometry.coordinates.forEach((geojson) => {
    // selectedZoneCoordinates.push(geojson[0]);
    geojson[0].forEach((coord) => {
      selectedZoneCoordinates.push(coord);
    });
  });
  const maxLon = d3.max(selectedZoneCoordinates, d => d[0]);
  const minLon = d3.min(selectedZoneCoordinates, d => d[0]);
  const maxLat = d3.max(selectedZoneCoordinates, d => d[1]);
  const minLat = d3.min(selectedZoneCoordinates, d => d[1]);
  const lon = d3.mean([minLon, maxLon]);
  const lat = d3.mean([minLat, maxLat]);

  zoneMap.setCenter([lon, lat]);
  if (zoomLevel) {
    // Remember to set center and zoom in case the map wasn't loaded yet
    zoneMap.setZoom(zoomLevel);
    // If the panel is open the zoom doesn't appear perfectly centered because
    // it centers on the whole window and not just the visible map part.
    // something one could fix in the future. It's tricky because one has to project, unproject
    // and project again taking both starting and ending zoomlevel into account
    zoneMap.map.easeTo({ center: [lon, lat], zoom: zoomLevel });
  }
}
