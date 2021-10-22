const { area, bbox, bboxPolygon, convex, dissolve, getCoords, getType, featureEach, featureCollection, intersect, polygon, truncate, unkinkPolygon } = require("@turf/turf")
const zones = require("../../config/zones.json");
const { getPolygons, getHoles, writeJSON } = require("./utilities")

function validateGeometry(fc, config) {
    checkGeometryValidity(fc)
    validateProperties(fc);
    // matchWithZonesJSON(fc);
    getComplexPolygons(fc, config);
    countGaps(fc, config);
    ensureNoNeighbouringIds(fc);
    countOverlaps(fc);
}

function checkGeometryValidity(fc) {
    // check that all geometries are valid
}

function validateProperties(fc) {
    const propertiesValidator = (properties) => {
        let validProperties = true;
        validProperties &= ('zoneName' in properties);
        return validProperties;
    }

    const invalidPropertiesPolygons = [];
    featureEach(getPolygons(fc), (ft, ftIdx) => {
        if (!propertiesValidator(ft.properties)) {
            invalidPropertiesPolygons.push(ft);
        }
    })
    if (invalidPropertiesPolygons.length > 0) {
        console.log(`${invalidPropertiesPolygons.length} polygons with invalid properties`);
        console.log(invalidPropertiesPolygons)
    }
}

function getComplexPolygons(fc, config) {
    // https://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.73.1045&rep=rep1&type=pdf
    // calculate deviation from the convex hull and returns array of polygons with high complexity
    const polygons = getPolygons(fc);
    const complexPolsNames = [];
    const complexPols = [];
    featureEach(polygons, (pol) => {
        try {
            const conv = convex(pol);
            const deviation = (area(conv) - area(pol)) / area(conv)
            if (deviation > config.MAX_CONVEX_DEVIATION) {
              complexPolsNames.push(pol.properties.zoneName);
              complexPols.push(pol);
            }
        } catch (error) {
            console.log("Failed to calculate complexity for", pol.properties.zoneName);
        }
    });
    if (complexPolsNames.length > 0) {
        console.log(`${complexPolsNames.length} complex polygons found:`);
        console.log(complexPolsNames);
        writeJSON("./tmp/complexZones.geojson", featureCollection(complexPols));
    }
    return complexPols;
}

function matchWithZonesJSON(fc) {
    const superfluousZones = [];
    featureEach(fc, (ft, ftIdx) => {
        if (!(ft.properties.zoneName in zones)) {
            superfluousZones.push(ft.properties.zoneName);
        }
    });
    if (superfluousZones.length > 0) {
        console.log(`${superfluousZones.length} superfluous zones still in world.geojson:`);
        console.log(superfluousZones);
    }
}

function countGaps(fc, config) {
    const dissolved = getPolygons(dissolve(getPolygons(fc)));
    const holes = getHoles(dissolved, config.MIN_AREA_HOLES);
    if (holes.features.length > 0) {
        writeJSON("./tmp/dissolved.geojson", dissolved);
        console.log(`${holes.features.length} holes left.`);
        writeJSON("./tmp/holes.geojson", holes);
    }
}

function ensureNoNeighbouringIds(fc) {
    const groupById = (arr, key) => {
        const initialValue = {};
        return arr.reduce((acc, cval) => {
            const myAttribute = cval.properties[key];
            acc[myAttribute] = [...(acc[myAttribute] || []), cval]
            return acc;
        }, initialValue);
    };

    const zonesWithNeighbouringIds = [];
    const featuresPerId = groupById(getPolygons(fc).features, "id");
    Object.entries(featuresPerId).forEach(([zoneId, polygons]) => {
        const dissolved = dissolve(featureCollection(polygons));
        if ((dissolved.features.length !== polygons.length) && (polygons.length > 0)) {
            zonesWithNeighbouringIds.push(zoneId);
        }
    });

    if (zonesWithNeighbouringIds.length > 0) {
        console.log(`${zonesWithNeighbouringIds.length} zones with neighbouring IDs:`)
        console.log(zonesWithNeighbouringIds);
    }
}

function countOverlaps(fc) {
    const polygons = getPolygons(fc);
    // 1. Build bounding box overlaps adjacency list
    const bboxes = [];
    featureEach(polygons, (ft, ftIdx) => {
        bboxes.push(bboxPolygon(bbox(ft)));
    });

    const overlaps = [];
    const intersects = [];
    for (let i = 0; i < bboxes.length; i++) {
        const overlapIdx = [];
        for (let j = i + 1; j < bboxes.length; j++) {
            if (intersect(bboxes[i], bboxes[j])) {
                const intsct = intersect(polygons.features[i], polygons.features[j])
                if ((intsct) && (area(intsct) > 500000)) {
                    overlapIdx.push(j);
                    intersects.push(intsct);
                }
            }
        }
        overlaps.push(overlapIdx)
    }

    const numberOverlaps = overlaps.reduce((acc, cval) => {
        const newAcc = acc + cval.length;
        return newAcc;
    }, 0)
    if (numberOverlaps > 0) {
        const overlapIDs = new Set();
        overlaps.forEach((overlapWithI, i) => {
            const zone1 = polygons.features[i].properties.zoneName;
            overlapWithI.forEach((j, idx) => {
                const zone2 = polygons.features[j].properties.zoneName;
                const overlappingZones = [zone1, zone2];
                overlappingZones.sort();
                overlapIDs.add(`${overlappingZones[0]} & ${overlappingZones[1]}`)
            })
        })
        console.log(`${numberOverlaps} overlaps detected:`);
        console.log(overlapIDs)
    }
}

module.exports = { validateGeometry };
