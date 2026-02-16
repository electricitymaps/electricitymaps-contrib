import { readFileSync, readdirSync, writeFileSync } from "fs";
import { join } from "path";
import bbox from "@turf/bbox";
import centerOfMass from "@turf/center-of-mass";
import union from "@turf/union";
import type {
  Feature,
  FeatureCollection,
  MultiPolygon,
  Polygon,
} from "geojson";

const GEO_PATH = join(import.meta.dir, "world.geojson");
const ZONES_DIR = join(import.meta.dir, "..", "config", "zones");

// Load the geojson
const geojson: FeatureCollection<Polygon | MultiPolygon> = JSON.parse(
  readFileSync(GEO_PATH, "utf-8")
);

// Build a map of zoneName -> features
const featuresByZone = new Map<string, Feature<Polygon | MultiPolygon>[]>();
for (const feature of geojson.features) {
  const zoneName = feature.properties?.zoneName;
  if (!zoneName) continue;
  if (!featuresByZone.has(zoneName)) featuresByZone.set(zoneName, []);
  featuresByZone.get(zoneName)!.push(feature);
}

// Parse subZoneNames from YAML files to find aggregate zones
function getSubZoneNames(content: string): string[] {
  const match = content.match(/subZoneNames:\n((?:  - .+\n)+)/);
  if (!match) return [];
  return [...match[1].matchAll(/  - (.+)/g)].map((m) => m[1]!);
}

interface ZoneGeo {
  centerPoint: [number, number];
  boundingBox: [[number, number], [number, number]];
}

function computeZoneGeo(features: Feature<Polygon | MultiPolygon>[]): ZoneGeo {
  const fc: FeatureCollection<Polygon | MultiPolygon> = {
    type: "FeatureCollection",
    features,
  };

  const combined = features.length === 1 ? features[0]! : union(fc)!;
  const center = centerOfMass(combined);
  const [minLon, minLat, maxLon, maxLat] = bbox(fc);

  return {
    centerPoint: center.geometry.coordinates as [number, number],
    boundingBox: [
      [minLon, minLat],
      [maxLon, maxLat],
    ],
  };
}

// Build a map of zoneName -> geo data
const zoneGeos = new Map<string, ZoneGeo>();

// First pass: compute for zones that have their own geometry
for (const [zoneName, features] of featuresByZone) {
  zoneGeos.set(zoneName, computeZoneGeo(features));
}

console.log(`Computed geo data for ${zoneGeos.size} zones from geojson`);

// Second pass: compute for aggregate zones by combining sub-zone geometries
const zoneFiles = readdirSync(ZONES_DIR).filter((f) => f.endsWith(".yaml"));

for (const file of zoneFiles) {
  const zoneName = file.replace(".yaml", "");
  if (zoneGeos.has(zoneName)) continue;

  const filePath = join(ZONES_DIR, file);
  const content = readFileSync(filePath, "utf-8");
  const subZoneNames = getSubZoneNames(content);
  if (subZoneNames.length === 0) continue;

  const subFeatures: Feature<Polygon | MultiPolygon>[] = [];
  for (const sub of subZoneNames) {
    const features = featuresByZone.get(sub);
    if (features) subFeatures.push(...features);
  }

  if (subFeatures.length === 0) {
    console.warn(
      `No sub-zone geometries found for aggregate zone ${zoneName}`
    );
    continue;
  }

  zoneGeos.set(zoneName, computeZoneGeo(subFeatures));
  console.log(
    `Computed geo for aggregate zone ${zoneName} from ${subFeatures.length} sub-zone features`
  );
}

// Update each zone YAML file
let updated = 0;
let skipped = 0;

for (const file of zoneFiles) {
  const zoneName = file.replace(".yaml", "");
  const geo = zoneGeos.get(zoneName);
  if (!geo) {
    console.warn(`No geometry found for zone ${zoneName}`);
    skipped++;
    continue;
  }

  const filePath = join(ZONES_DIR, file);
  let content = readFileSync(filePath, "utf-8");

  // Remove existing bounding_box and center_point
  content = content.replace(/^bounding_box:\n((?:  .+\n)+)/m, "");
  content = content.replace(/^center_point:\n((?:  - .+\n)+)/m, "");

  const [[minLon, minLat], [maxLon, maxLat]] = geo.boundingBox;
  const [lon, lat] = geo.centerPoint;

  const geoYaml = [
    `bounding_box:`,
    `  - - ${minLon}`,
    `    - ${minLat}`,
    `  - - ${maxLon}`,
    `    - ${maxLat}`,
    `center_point:`,
    `  - ${lon}`,
    `  - ${lat}`,
    "",
  ].join("\n");

  // Insert at the very beginning (bounding_box is always first, after optional _comment)
  const commentMatch = content.match(/^_comment:.*\n((?:  .+\n)*)/);
  if (commentMatch) {
    const insertPos = commentMatch.index! + commentMatch[0].length;
    content =
      content.slice(0, insertPos) + geoYaml + content.slice(insertPos);
  } else {
    content = geoYaml + content;
  }

  writeFileSync(filePath, content);
  updated++;
}

console.log(`\nUpdated ${updated} zone files, skipped ${skipped}`);
