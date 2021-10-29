const { topology } = require("topojson-server");
const { writeJSON } = require("./utilities")


function generateTopojson(fc, {OUT_PATH}) {
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


  writeJSON(OUT_PATH, topo)
}

module.exports = { generateTopojson };
