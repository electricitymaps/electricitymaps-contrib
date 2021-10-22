const { topology } = require("topojson-server");
const { writeJSON } = require("./utilities")


function generateTopojson(fc) {
  console.log(fc)
  const topo = topology({
    world: fc,
  });

  writeJSON("./world.topojson", topo)
}

module.exports = { generateTopojson };
