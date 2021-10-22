const { polygon, getCoords, getType, featureEach, featureCollection, dissolve, unkinkPolygon, area, convex, multiPolygon, booleanEqual, truncate } = require("@turf/turf")
const fs = require("fs")

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
 
 function getHoles(fc, minArea) {
     const holes = []
     featureEach(fc, (ft) => {
         const coords = getCoords(ft);
         if (coords.length > 1) {
             for (let i = 1; i < coords.length; i++) {
                 const pol = polygon([coords[i]]);
                 if (area(pol) < minArea) {
                     holes.push(pol);
                 }
             }
         }
     });
     return featureCollection(holes);
 }


const newFileCallback = fileName => console.log(`Created new file: ${  fileName}`);
const getJSON = (fileName, encoding = "utf8", callBack = () => { }) =>
    typeof fileName === "string" ?
        JSON.parse(fs.readFileSync(fileName, encoding, () => callBack())) :
        fileName;

const writeJSON = (fileName, obj, callBack = newFileCallback, encoding = 'utf8') =>
    fs.writeFile(fileName, JSON.stringify(obj), encoding, () => callBack(fileName));

function log(message) {
    console.log("\x1b[31m%s\x1b[0m", `ERROR: ${message}`);
}    

module.exports = { getPolygons, getHoles, writeJSON, getJSON, log }