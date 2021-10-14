const turf = require("@turf/turf")
const fs = require("fs");
const newFileCallback = fileName => console.log("Created new file: " + fileName);
const getJSON = (fileName, encoding = "utf8", callBack = () => {}) =>
  typeof fileName === "string" ?
  JSON.parse(fs.readFileSync(fileName, encoding, () => callBack())) :
  fileName;

const writeJSON = (fileName, obj, callBack = newFileCallback, encoding = 'utf8') =>
  fs.writeFile(fileName, JSON.stringify(obj), encoding, () => callBack(fileName));


const fc = getJSON("./world.geojson");
validateGeometry(fc)

function validateGeometry(fc) {
    countGaps(fc);
    // find line intersections
    // find overlaps
    // find gaps
    // find complexity
    // ensure ids
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

function countGaps(fc) {
    const dissolved = turf.dissolve(getPolygons(fc));
    writeJSON("./tmp/dissolved.geojson", dissolved)
}


function getPolygons(data) {
    const handlePolygon = (feature, props) => turf.polygon(turf.getCoords(feature), props)
    const handleMultiPolygon = (feature, props) => turf.getCoords(feature).map(coord => turf.polygon(coord, props));
    const handleGeometryCollection = (feature) => feature.geometries.map((ft) => turf.getType(ft) === "Polygon" ? handlePolygon(ft) : handleMultiPolygon(ft));

    const polygons = [];

    const dataGeojsonType = turf.getType(data)
    if (dataGeojsonType !== "FeatureCollection") {
        data = turf.featureCollection([data]);
    }
    turf.featureEach(data, (feature) => {
        const type = turf.getType(feature);
        switch (type) {
            case "Polygon":
                polygons.push(handlePolygon(feature, feature.properties))
                break;
            case "MultiPolygon":
                polygons.push(...handleMultiPolygon(feature, feature.properties))
                break;
            default:
                throw Error("Encountered unhandled type: " + type);
        }
    })

    return turf.featureCollection(polygons);
}