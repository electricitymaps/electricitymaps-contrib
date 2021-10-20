const fs = require("fs");
const zones = require("../../config/zones.json");
const { validateGeometry } = require("./validate");
const { detectChanges } = require("./detectChanges")
const { getJSON } = require("./utilities")

const config = {
    MIN_AREA_HOLES: 800000000,
    MAX_CONVEX_DEVIATION: 0.7
}

const fc = getJSON("./world.geojson");
// validateGeometry(fc);
detectChanges(fc);
// generateTopojson(fc);
