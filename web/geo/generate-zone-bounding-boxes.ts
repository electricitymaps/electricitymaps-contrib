// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'path'.
import path from 'path';

// @ts-expect-error TS(2580): Cannot find name 'process'. Do you need to install... Remove this comment to see the full error message
const args = process.argv.slice(2);

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getJSON'.
import { getJSON } from './utilities';
// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'getZonesJs... Remove this comment to see the full error message
import { getZonesJson, saveZonesJson } from './files';

// @ts-expect-error TS(2451): Cannot redeclare block-scoped variable 'zones'.
let zones = getJSON(path.resolve(__dirname, './world.geojson'));

if (args.length <= 0) {
  console.error('ERROR: Please add a zoneName parameter ("node generate-zone-bounding-boxes.js DE")');
  // @ts-expect-error TS(2580): Cannot find name 'process'. Do you need to install... Remove this comment to see the full error message
  process.exit(1);
}
zones.features = zones.features.filter((d: any) => d.properties.zoneName === args[0]);

let allCoords: any = [];
const boundingBoxes = {};

zones.features.forEach((zone: any) => {
  allCoords = [];
  const geometryType = zone.geometry.type;
  zone.geometry.coordinates.forEach((coords1: any) => {
    coords1[0].forEach((coord: any) => allCoords.push(coord));
  });

  let minLat = 200;
  let maxLat = -200;
  let minLon = 200;
  let maxLon = -200;

  if (geometryType == 'MultiPolygon') {
    // @ts-expect-error TS(7006): Parameter 'coord' implicitly has an 'any' type.
    allCoords.forEach((coord) => {
      const lon = coord[0];
      const lat = coord[1];

      minLon = Math.min(minLon, lon);
      maxLon = Math.max(maxLon, lon);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    });
  } else {
    const lon = allCoords[0];
    const lat = allCoords[1];

    minLon = Math.min(minLon, lon);
    maxLon = Math.max(maxLon, lon);
    minLat = Math.min(minLat, lat);
    maxLat = Math.max(maxLat, lat);
  }

  // @ts-expect-error TS(7053): Element implicitly has an 'any' type because expre... Remove this comment to see the full error message
  boundingBoxes[zone.properties.zoneName] = [
    [minLon - 0.5, minLat - 0.5],
    [maxLon + 0.5, maxLat + 0.5],
  ];
});

// @ts-expect-error TS(2588): Cannot assign to 'zones' because it is a constant.
zones = getZonesJson();

// @ts-expect-error TS(2550): Property 'entries' does not exist on type 'ObjectC... Remove this comment to see the full error message
for (const [zone, bbox] of Object.entries(boundingBoxes)) {
  // do not add new entries to zones.json, do not add RU because it crosses the 180th meridian
  if (!(zone in zones) || zone === 'RU' || zone === 'RU-FE') {
    continue;
  }
  // do not modifiy current bounding boxes
  if (zones[zone].bounding_box) {
    continue;
  }
  zones[zone].bounding_box = [bbox[0], bbox[1]];
}

saveZonesJson(zones);

console.error('Done, check /config/zones.json to verify that the result looks good!');
