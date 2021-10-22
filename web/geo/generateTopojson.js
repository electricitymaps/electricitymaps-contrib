const { topology } = require("topojson-server");
const { writeJSON } = require("./utilities")


function generateTopojson(fc) {
  console.log("Generating new world.json");
  const topo = topology({
    world: fc,
  });

  writeJSON("./world.json", topo)
}

module.exports = { generateTopojson };
