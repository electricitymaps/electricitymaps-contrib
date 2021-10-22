const fs = require("fs");
const zones = require("../../config/zones.json");
const { validateGeometry } = require("./validate");
const { detectChanges } = require("./detectChanges")
const { getJSON } = require("./utilities")
const { generateTopojson } = require("./generateTopojson")

const config = {
    WORLD_PATH: "./world.geojson",
    MIN_AREA_HOLES: 600000000,
    MAX_CONVEX_DEVIATION: 0.708
}

const fc = getJSON(config.WORLD_PATH);
validateGeometry(fc, config);
detectChanges(fc);
generateTopojson(fc);


