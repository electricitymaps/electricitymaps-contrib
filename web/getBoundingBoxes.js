const fs = require('fs');

function readNDJSON(path) {
  return fs.readFileSync(path, 'utf8').split('\n')
    .filter(d => d !== '')
    .map(JSON.parse);
}

const zones = readNDJSON('build/zonegeometries.json');

let allCoords = [];
const boundingBoxes = {};

zones.forEach((zone) => {
  allCoords = [];
  zone.geometry.coordinates.forEach((coords1) => {
    coords1[0].forEach(coord => allCoords.push(coord));
  });

  let minLat = 200;
  let maxLat = -200;
  let minLon = 200;
  let maxLon = -200;

  allCoords.forEach((coord) => {
    const lon = coord[0];
    const lat = coord[1];

    minLon = Math.min(minLon, lon);
    maxLon = Math.max(maxLon, lon);
    minLat = Math.min(minLat, lat);
    maxLat = Math.max(maxLat, lat);
  });

  boundingBoxes[zone.properties.zoneName] = [[minLon - 0.5, minLat - 0.5],
    [maxLon + 0.5, maxLat + 0.5]];
});

console.log(JSON.stringify(boundingBoxes));
