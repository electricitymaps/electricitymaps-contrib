const { polygon, getCoords, getType, featureEach, featureCollection, dissolve, unkinkPolygon, area } = require("@turf/turf")
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
    MIN_AREA_HOLES: 800000000
}

const fc = getJSON("./world.geojson");
validateGeometry(fc)

function validateGeometry(fc) {
    matchWithZonesJSON(fc);
    ensureComplexity(fc);
    // check match with zones.json
    countGaps(fc);
    // ensure no neighbouring ids
    ensureNoNeighbouringIds(fc);
    // find line intersections
    // find overlaps
    // find complexity
    // ensure ids
    // ensure physical consistency
    // ensure geojson specification
    // bound on complexity
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

function matchWithZonesJSON(fc) {
    const superfluousZones = [];
    featureEach(fc, (ft, ftIdx) => {
      if (!(ft.properties.id in zones)) {
        superfluousZones.push(ft.properties.id);
      }
    });
    if (superfluousZones.length > 0) {
      console.log(`${superfluousZones.length} superfluous zones still in world.geojson:`);
      console.log(superfluousZones);
    }
}

function ensureComplexity(fc) {

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

    return featureCollection(polygons);
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

