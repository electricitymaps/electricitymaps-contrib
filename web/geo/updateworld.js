const turf = require("@turf/turf")
const fs = require("fs");
const newFileCallback = fileName => console.log("Created new file: " + fileName);
const getJSON = (fileName, encoding = "utf8", callBack = () => {}) =>
  typeof fileName === "string" ?
  JSON.parse(fs.readFileSync(fileName, encoding, () => callBack())) :
  fileName;

const writeJSON = (fileName, obj, callBack = newFileCallback, encoding = 'utf8') =>
  fs.writeFile(fileName, JSON.stringify(obj), encoding, () => callBack(fileName));

function validateGeometry() {
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
const data = getJSON("../src/world.json")
Object.keys(data.objects).forEach(key => {
    data.objects[key]['id'] = key;
    data.objects[key]["properties"] = {"zoneName": key}
})

writeJSON("./world.json", data);

console.log(data.objects["DK-DK1"]);
