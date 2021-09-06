const path = require("path");
const fs = require("fs");
const zonesConfig = require("./config/zones.json");

const DELAY = 30;

let zones = zonesConfig;
Object.keys(zones)
  .filter((z) => {
    if (
      zones[z]?.parsers?.production &&
      zones[z].parsers.production.includes("EIA")
    ) {
      return true;
    }

    return false;
  })
  .forEach((z) => {
    const data = zones[z];

    let delays = {};
    // For each key in parser, add similar key to delays
    Object.keys(data.parsers).forEach((p) => {
      // Only add delay if the specific parser is EIA
      if (data.parsers[p].includes("EIA")) {
        delays[p] = DELAY;
      }
    });

    // Sort delays by key
    const sortedDelays = Object.keys(delays)
      .sort()
      .reduce((acc, k) => {
        acc[k] = delays[k];
        return acc;
      }, {});

    zones[z] = { ...data, delays: sortedDelays };
  });

const data = `${JSON.stringify(zones, null, 2)}\n`;

const outputLocation = path.resolve(__dirname, "./config/zones.json");
fs.writeFile(outputLocation, data, function (err) {
  if (err) {
    console.log(err);
  } else {
    console.log(`JSON saved to ${outputLocation}`);
  }
});
