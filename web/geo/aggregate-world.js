const { featureCollection, dissolve } = require('@turf/turf');
const fs = require('fs');
const { getJSON, combineFeatureCollections } = require('./utilities')


const data = getJSON("world.geojson")

function combine(arr) {
    let features = []
    arr.forEach(ft => features.push(ft));
    
    return dissolve(features);

}

const country = data.features.reduce((acc, cur) => {
    if (acc[cur.properties.countryKey]) {
        acc[cur.properties.countryKey].push(cur)
        return acc;
    } else {
        acc[cur.properties.countryKey] = [cur]
        return acc;
    }
}, {})


let combinedFeatures = []
Object.keys(country).forEach(key => {
    combinedFeatures.push(combine(country[key]))
});

console.log(combinedFeatures[0]);


// Object.keys(country).forEach(key => {
//     const combined = combineFeatureCollections(country[key])
//     console.log(combined);
// })

// console.log(combined);