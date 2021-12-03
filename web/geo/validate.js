const { area, bbox, bboxPolygon, convex, dissolve, featureEach, featureCollection, intersect, getGeom } = require("@turf/turf")
const zones = require("../../config/zones.json");
const { getPolygons, getHoles, writeJSON, log } = require("./utilities")

function validateGeometry(fc, config) {
    console.log("Validating geometries...");
    zeroNullGeometries(fc);
    containsRequiredProperties(fc)
    zeroComplexPolygons(fc, config);
    zeroNeighboringIds(fc);
    zeroGaps(fc, config);
    matchesZonesConfig(fc);
    zeroOverlaps(fc);
}

function zeroNullGeometries(fc) {
    const nullGeometries = fc.features.filter(ft => !getGeom(ft).coordinates.length).map(ft => ft.properties.zoneName);
    if (nullGeometries.length) {
        nullGeometries.forEach(zoneName => log(`${zoneName} has null geometry`))
        throw Error("Feature(s) contains null geometry")
    }
}

function containsRequiredProperties(fc) {
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
    if (invalidPropertiesPolygons.length) {
        invalidPropertiesPolygons.forEach(x => log(`feature (idx ${x}) missing properties`))
        throw Error("Feature(s) are missing properties")
    }
}

function zeroComplexPolygons(fc, config) {
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
        throw Error("Feature(s) too complex");
    }
}

function matchesZonesConfig(fc) {
    const features = [];
    featureEach(fc, (ft) => {
        if (!(ft.properties.zoneName in zones)) {
            features.push(ft.properties.zoneName);
        }
    });
    if (features.length) {
        features.forEach(x => log(`${x} not in zones.json`))
        throw Error("Zonename not in zones.json");
    }
}

function zeroGaps(fc, config) {
    const dissolved = getPolygons(dissolve(getPolygons(fc)));
    const holes = getHoles(dissolved, config.MIN_AREA_HOLES);
    if (holes.features.length > 0) {
        writeJSON("gaps.geojson", holes);
        holes.features.forEach(_ => log(`Found gap, see gaps.geojson`))
        throw Error("Contains gaps")
    }
}

function zeroNeighboringIds(fc) {
    const groupById = (arr, key) => {
        const initialValue = {};
        return arr.reduce((acc, cval) => {
            const myAttribute = cval.properties[key];
            acc[myAttribute] = [...(acc[myAttribute] || []), cval]
            return acc;
        }, initialValue);
    };

    const zonesWithNeighbouringIds = [];
    const featuresPerId = groupById(getPolygons(fc).features, "zoneName");
    Object.entries(featuresPerId).forEach(([zoneId, polygons]) => {
        const dissolved = dissolve(featureCollection(polygons));
        if ((dissolved.features.length !== polygons.length) && (polygons.length > 0)) {
            zonesWithNeighbouringIds.push(zoneId);
        }
    });

    if (zonesWithNeighbouringIds.length) {
        zonesWithNeighbouringIds.forEach(x => log(`${x} has neighbor with identical ID`))
        throw Error("Contains neighboring id zone")
    }
}

function zeroOverlaps(fc) {
    const polygons = getPolygons(fc);
    // 1. Build bounding box overlaps adjacency list
    const bboxes = [];
    featureEach(polygons, (ft) => {
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
            overlapWithI.forEach((j) => {
                const zone2 = polygons.features[j].properties.zoneName;
                const overlappingZones = [zone1, zone2];
                overlappingZones.sort();
                overlapIDs.add(`${overlappingZones[0]} & ${overlappingZones[1]}`)
            })
        })
        overlapIDs.forEach(x => log(`${x} overlaps`))
        throw Error("Feature(s) overlaps");
    }
}

module.exports = { validateGeometry };
