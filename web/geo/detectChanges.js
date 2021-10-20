const topojsonClient = require("topojson-client");
const { polygon, getCoords, getType, featureEach, featureCollection, dissolve, unkinkPolygon, area, convex, multiPolygon, booleanEqual } = require("@turf/turf")
const fs = require("fs");
const { getPolygons } = require("./utilities")
const getJSON = (fileName, encoding = "utf8", callBack = () => { }) =>
    typeof fileName === "string" ?
        JSON.parse(fs.readFileSync(fileName, encoding, () => callBack())) :
        fileName;


const newFC = getJSON("world.geojson");
const curFC = topoToGeojson(getJSON("world.json"));

function topoToGeojson(topo) {
    let features = [];
    Object.keys(topo.objects).forEach((obj) => {
        const feature = topojsonClient.feature(topo, topo.objects[obj]);
        if (feature.geometry) {
            features.push(feature);
        } else {
            // console.log("Warning, empty geometry in current world.json");
        }
    });
    const fc = featureCollection(features);
    return getPolygons(fc)
}

function getModifications(curFC, newFC) {
    const modified = []
    const zoneNames = [... new Set(curFC.features.map(x => x.properties.zoneName))];
    zoneNames.forEach((name) => {
        const curArea = area(getCombinedFeature(curFC, name));
        const newArea = area(getCombinedFeature(newFC, name));
        if (Math.abs(curArea - newArea) > 1) {
            modified.push(name)
        }
    })

    if (modified.length) {
        console.log("The following zones have been modified:\n");
        modified.forEach((x) => console.log(x))
        console.log("_________________");
    }
}


function getCombinedFeature(fc, id) {
    // returns polygon or multipolygon
    const polygons = fc.features.filter(x => x.properties.zoneName === id);
    if (polygons.length > 1) {
        return multiPolygon(polygons.map(x => getCoords(x)), { id: id, zoneName: id }); // TODO remove id
    } else return polygons[0];
}

function detectChanges(newFC) {
    getModifications(curFC, newFC)

}

module.exports = { detectChanges }