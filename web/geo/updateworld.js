const fs = require("fs");
const zones = require("../../config/zones.json");
const { validateGeometry } = require("./validate");
const { detectChanges } = require("./detectChanges")
const { getJSON } = require("./utilities")
const { generateTopojson } = require("./generateTopojson")

const config = {
    WORLD_PATH: "./world.geojson",
    MIN_AREA_HOLES: 800000000,
    MAX_CONVEX_DEVIATION: 0.7
}

const fc = getJSON(config.WORLD_PATH);
// validateGeometry(fc);
detectChanges(fc);
generateTopojson(fc);


