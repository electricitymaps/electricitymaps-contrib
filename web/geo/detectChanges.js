const topojsonClient = require("topojson-client");
const {  getCoords, featureCollection, area, multiPolygon } = require("@turf/turf")
const fs = require("fs");
const { getPolygons } = require("./utilities");

const getJSON = (fileName, encoding = "utf8", callBack = () => { }) =>
    typeof fileName === "string" ?
        JSON.parse(fs.readFileSync(fileName, encoding, () => callBack())) :
        fileName;


function topoToGeojson(topo) {
    const features = [];
    Object.keys(topo.objects).forEach((obj) => {
        const feature = topojsonClient.feature(topo, topo.objects[obj]);
        if (feature.geometry) { // TODO: remove this line after updating world.geojson
            features.push(feature);
        }
    });
    const fc = featureCollection(features);
    return getPolygons(fc)
}

function getModifications(curFC, newFC) {
    const modified = []
    const zoneNames = [... new Set(curFC.features.map(x => x.properties.zoneName))];
    zoneNames.forEach((name) => {
        try {
            const curArea = area(getCombinedFeature(curFC, name));
            const newArea = area(getCombinedFeature(newFC, name));
            const pctAreaDiff = Math.abs(curArea - newArea) / curArea // accounts for lossy conversion between topojson and geojson
            if (pctAreaDiff > 0.0001) {
                modified.push(name);
            }
        } catch (error) {
            // assumes the zone is modified
            modified.push(name)
        }
    });

    return modified;
}


function getCombinedFeature(fc, id) {
    // returns polygon or multipolygon
    const polygons = fc.features.filter(x => x.properties.zoneName === id);
    if (polygons.length > 1) {
        return multiPolygon(polygons.map(x => getCoords(x)), { zoneName: id }); // TODO remove id
    } else return polygons[0];
}

function getAdditions(curFC, newFC) {
    const added = [];
    curFC.features.filter(x => {
        const id = x.properties.zoneName;
        if (!newFC.features.some(x2 => x2.properties.zoneName === id)) {
            added.push(id);
        }
    })
    return added
}

function getDeletions(curFC, newFC) {
    const deletions = [];
    newFC.features.filter(x => {
        const id = x.properties.zoneName;
        if (!curFC.features.some(x2 => x2.properties.zoneName === id)) {
            deletions.push(id)
        }
    })
    return deletions;
}

function detectChanges(newFC, {OUT_PATH}) {
    // eslint-disable-next-line no-param-reassign
    newFC = featureCollection(newFC.features.filter(x => x.geometry.coordinates.length)); // TODO: remove this line
    console.log("Detecting changes...");
    const curFC = topoToGeojson(getJSON(OUT_PATH));
    const deletions = getDeletions(curFC, newFC)
    const additions = getAdditions(curFC, newFC)
    const modified = getModifications(curFC, newFC).filter(x => !(deletions.includes(x) || additions.includes(x)));


    modified.forEach(x => console.log("MODIFIED:", x))
    deletions.forEach(x => console.log("DELETED:", x))
    additions.forEach(x => console.log("ADDED:", x))

    if (!(modified.length + additions.length + deletions.length)) {
        console.log("No changes detected!");
    }
}

module.exports = { detectChanges }