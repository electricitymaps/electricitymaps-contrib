const { topology } = require("topojson-server");
const { writeJSON } = require("./utilities")


function generateTopojson(fc, {OUT_PATH}) {
  console.log("Generating new world.json");
  const topo = topology({
    world: fc,
  });

  writeJSON(OUT_PATH, topo)
}

module.exports = { generateTopojson };
