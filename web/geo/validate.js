const { area, bbox, bboxPolygon, convex, dissolve, getCoords, getType, featureEach, featureCollection, intersect, polygon, truncate, unkinkPolygon, getGeom } = require("@turf/turf")
const zones = require("../../config/zones.json");
const { getPolygons, getHoles, writeJSON, log } = require("./utilities")

function validateGeometry(fc, config) {
    console.log("Validating geometries...");
    const summary = {
        count_nullGeometries: checkGeometryNotNull(fc),
        count_invalidProperties: validateProperties(fc),
        count_notInZones: matchWithZonesJSON(fc),
        count_complexPolygons: getComplexPolygons(fc, config),
        count_gaps: countGaps(fc, config),
        count_neighboringIds: ensureNoNeighbouringIds(fc),
        count_overlaps: countOverlaps(fc) 
    }
    console.log("\nVALIDATION SUMMARY\n");
    console.log(summary);
    console.log("_________");
}

function checkGeometryNotNull(fc) {
    const nullGeometries = fc.features.filter(ft => !getGeom(ft).coordinates.length).map(ft => ft.properties.zoneName);
    nullGeometries.forEach(x => log(`${x} has null geometry`))
    return nullGeometries.length;
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
            invalidPropertiesPolygons.push(ftIdx);
        }
    })
    if (invalidPropertiesPolygons.length > 0) {
        invalidPropertiesPolygons.forEach(x => log(`feature (idx ${x}) missing properties`))
    }
    return invalidPropertiesPolygons.length;
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
            log(`${pol.properties.zoneName} cannot calculate complexity`)
        }
    });
    if (complexPolsNames.length > 0) {
        complexPolsNames.forEach(x => log(`${x} is too complex`))
    }
    return complexPols.length;
}

function matchWithZonesJSON(fc) {
    const features = [];
    featureEach(fc, (ft, ftIdx) => {
        if (!(ft.properties.zoneName in zones)) {
            features.push(ft.properties.zoneName);
        }
    });
    if (features.length > 0) {
        features.forEach(x => log(`${x} not in zones.json`))
    }
    return features.length;
}

function countGaps(fc, config) {
    const dissolved = getPolygons(dissolve(getPolygons(fc)));
    const holes = getHoles(dissolved, config.MIN_AREA_HOLES);
    if (holes.features.length > 0) {
        writeJSON("./tmp/gaps.geojson", holes);
        console.log(`${holes.features.length} holes left.`);
        holes.features.forEach(_ => log(`Found gap, see ./tmp/gaps.geojson`))
    }
    return holes.features.length;
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
        zonesWithNeighbouringIds.forEach(x => log(`${x} has neighbor with identical ID`))
    }
    return zonesWithNeighbouringIds.length;
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
        overlapIDs.forEach(x => log(`${x} overlaps`))
    }
    return numberOverlaps;
}

module.exports = { validateGeometry };
