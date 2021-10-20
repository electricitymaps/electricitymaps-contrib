const { area, bbox, bboxPolygon, convex, dissolve, getCoords, getType, featureEach, featureCollection, intersect, polygon, truncate, unkinkPolygon } = require("@turf/turf")
const fs = require("fs");
const zones = require("../../config/zones.json");

const newFileCallback = fileName => console.log(`Created new file: ${  fileName}`);
const getJSON = (fileName, encoding = "utf8", callBack = () => { }) =>
    typeof fileName === "string" ?
        JSON.parse(fs.readFileSync(fileName, encoding, () => callBack())) :
        fileName;

const writeJSON = (fileName, obj, callBack = newFileCallback, encoding = 'utf8') =>
    fs.writeFile(fileName, JSON.stringify(obj), encoding, () => callBack(fileName));

const config = {
    MIN_AREA_HOLES: 800000000,
    MAX_CONVEX_DEVIATION: 0.7
}

const fc = getJSON("./world.geojson");
// validateGeometry(fc)

function validateGeometry(fc) {
    validateProperties(fc);
    matchWithZonesJSON(fc);
    getComplexPolygons(fc);
    countGaps(fc);
    ensureNoNeighbouringIds(fc);
    countOverlaps(fc);

    // ensure physical consistency
    // ensure geojson specification
}

function detectChanges() {
    // get added
    // get removed
    // all zonekeys affected
}

function generateTopojson() {

}


// create world.geojson
// const data = getJSON("../src/world.json")
// Object.keys(data.objects).forEach(key => {
//     data.objects[key]['id'] = key;
//     data.objects[key]["properties"] = {"zoneName": key}
// })

// writeJSON("./world.json", data);

// console.log(data.objects["DK-DK1"]);


/* Helper functions */
function validateProperties(fc) {
    const propertiesValidator = (properties) => {
        let validProperties = true;
        validProperties &= ('zoneName' in properties);
        return validProperties;
    }

    const invalidPropertiesPolygons = [];
    featureEach(getPolygons(fc), (ft, ftIdx) => {
        if (!propertiesValidator(ft.properties)) {
          invalidPropertiesPolygons.push(ft);
        }
    })
    if (invalidPropertiesPolygons.length > 0) {
      console.log(`${invalidPropertiesPolygons.length} polygons with invalid properties`);
      console.log(invalidPropertiesPolygons)
    }
}

function getComplexPolygons(fc) {
    // https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.73.1045&rep=rep1&type=pdf
    // calculate deviation from the convex hull and returns array of polygons with high complexity
    const polygons = getPolygons(fc);
    const complexPols = [];
    featureEach(polygons, (pol) => {
        try {
            const conv = convex(pol);
            const deviation = (area(conv) - area(pol)) / area(conv)
            if (deviation > config.MAX_CONVEX_DEVIATION) {
                complexPols.push(pol);
            }
        } catch (error) {
            console.log("Failed to calculate complexity for", pol.properties.zoneName);
        }
    });
    return complexPols;
}

function matchWithZonesJSON(fc) {
    const superfluousZones = [];
    featureEach(fc, (ft, ftIdx) => {
      if (!(ft.properties.zoneName in zones)) {
        superfluousZones.push(ft.properties.zoneName);
      }
    });
    if (superfluousZones.length > 0) {
      console.log(`${superfluousZones.length} superfluous zones still in world.geojson:`);
      console.log(superfluousZones);
    }
}

function countGaps(fc) {
    const dissolved = getPolygons(dissolve(getPolygons(fc)));
    writeJSON("./tmp/dissolved.geojson", dissolved)
    const holes = getHoles(dissolved);
    console.log(`${holes.features.length} holes left.`);
    writeJSON("./tmp/holes.geojson", holes)

}


function getPolygons(data) {
   /* Transform the feature collection of polygons and multi-polygons into a feature collection of polygons only */
   /* all helper functions should rely on its output */
    const handlePolygon = (feature, props) => polygon(getCoords(feature), props)
    const handleMultiPolygon = (feature, props) => getCoords(feature).map(coord => polygon(coord, props));
    const handleGeometryCollection = (feature) => feature.geometries.map((ft) => getType(ft) === "Polygon" ? handlePolygon(ft) : handleMultiPolygon(ft));

    const polygons = [];

    const dataGeojsonType = getType(data);
    if (dataGeojsonType !== "FeatureCollection") {
        data = featureCollection([data]);
    }
    featureEach(data, (feature) => {
        const type = getType(feature);
        switch (type) {
            case "Polygon":
                polygons.push(handlePolygon(feature, feature.properties))
                break;
            case "MultiPolygon":
                polygons.push(...handleMultiPolygon(feature, feature.properties))
                break;
            default:
                throw Error(`Encountered unhandled type: ${  type}`);
        }
    })

    return truncate(featureCollection(polygons), {precision: 6});
}

function getHoles(fc) {
    const holes = []
    featureEach(fc, (ft) => {
        const coords = getCoords(ft);
        if (coords.length > 1) {
            for (let i = 1; i < coords.length; i++) {
                const pol = polygon([coords[i]]);
                if (area(pol) < config.MIN_AREA_HOLES) {
                    holes.push(pol);
                }
            }
        }
    });
    return featureCollection(holes);
}

function ensureNoNeighbouringIds(fc) {
    const groupById = (arr, key) => {
      const initialValue = {};
      return arr.reduce((acc, cval) => {
        const myAttribute = cval.properties[key];
        acc[myAttribute] = [...(acc[myAttribute] || []), cval]
        return acc;
      }, initialValue);
    };

    const zonesWithNeighbouringIds = [];
    const featuresPerId = groupById(getPolygons(fc).features, "id");
    Object.entries(featuresPerId).forEach(([zoneId, polygons]) => {
        const dissolved = dissolve(featureCollection(polygons));
        if ((dissolved.features.length !== polygons.length) && (polygons.length > 0)) {
          zonesWithNeighbouringIds.push(zoneId);
        }
    });

    console.log(`${zonesWithNeighbouringIds.length} zones with neighbouring IDs:`)
    console.log(zonesWithNeighbouringIds);
}

function countOverlaps(fc) {
    const polygons = getPolygons(fc);
    // 1. Build bounding box overlaps adjacency list
    const bboxes = [];
    featureEach(polygons, (ft, ftIdx) => {
        bboxes.push(bboxPolygon(bbox(ft)));
    });

    const overlaps = [];
    const intersects = [];
    for (let i = 0; i < bboxes.length; i++) {
      const overlapIdx = [];
      for (let j = i + 1; j < bboxes.length; j++) {
        if (intersect(bboxes[i], bboxes[j])) {
          const intsct = intersect(polygons.features[i], polygons.features[j])
          if ((intsct) && (area(intsct) > 500000)) {
              overlapIdx.push(j);
              intersects.push(intsct);
          }
        }
      }
      overlaps.push(overlapIdx)
    }
    writeJSON("./tmp/countOverlapsIntersects.geojson", featureCollection(intersects))

    const numberOverlaps = overlaps.reduce((acc, cval) => {
      const newAcc = acc + cval.length;
      return newAcc;
    }, 0)
    if (numberOverlaps > 0) {
      const overlapIDs = new Set();
      overlaps.forEach((overlapWithI, i) => {
        const zone1 = polygons.features[i].properties.zoneName;
        overlapWithI.forEach((j, idx) => {
          const zone2 = polygons.features[j].properties.zoneName;
          const overlappingZones = [zone1, zone2];
          overlappingZones.sort();
          overlapIDs.add(`${overlappingZones[0]} & ${overlappingZones[1]}`)
        })
      })
      console.log(`${numberOverlaps} overlaps detected:`);
      console.log(overlapIDs)
    }
}
