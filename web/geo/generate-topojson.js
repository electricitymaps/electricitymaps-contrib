const { topology } = require("topojson-server");
const { getJSON, writeJSON } = require("./utilities")


function generateTopojson(fc, {OUT_PATH, verifyNoUpdates}) {
  console.log("Generating new world.json");
  const topo = topology({
    objects: fc,
  });

  // We do the following to match the specific format needed for visualization
  const geoms = topo.objects.objects.geometries
  const newObjects = {}
  geoms.forEach(geo => {
    newObjects[geo.properties.zoneName] = geo
  });
  topo.objects = newObjects

  const currentTopo = getJSON(OUT_PATH);
  if (JSON.stringify(currentTopo) === JSON.stringify(topo)) {
    console.log("No changes to world.json");
    return;
  }

  if (verifyNoUpdates) {
    console.error('Did not expect any updates to world.json. Please run "yarn update-world"');
    process.exit(1);
  }

  writeJSON(OUT_PATH, topo)
}

module.exports = { generateTopojson };
