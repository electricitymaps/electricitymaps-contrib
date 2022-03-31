const fs = require("fs");

const REQUIRED_KEYS = [
  "co2intensity",
  "co2intensityProduction",
  "countryCode",
  "exchange",
  "exchangeCapacities",
  "exchangeCo2Intensities",
  "fossilFuelRatio",
  "fossilFuelRatioProduction",
  "renewableRatio",
  "renewableRatioProduction",
  "stateDatetime",
];
const REQUIRED_KEYS_HISTORY = [
  ...REQUIRED_KEYS,
  "capacity",
  "price",
  "production",
  "productionCo2Intensities",
  "productionCo2IntensitySources",
  "estimationMethod",
  "dischargeCo2Intensities",
  "dischargeCo2IntensitySources",
  "exchangeCapacities",
  "exchangeCo2Intensities",
  "maxCapacity",
  "maxDischarge",
  "maxCapacity",
  "maxDischarge",
  "maxExport",
  "maxExportCapacity",
  "maxImport",
  "maxImportCapacity",
  "maxProduction",
  "maxStorage",
  "maxStorageCapacity",
];
// // load public/v4 as json file
// let state = JSON.parse(fs.readFileSync("./public/v4/state"))

// // delete all countries where co2intensity is null
// Object.keys(state.data.countries).forEach(country => {
//     if (state.data.countries[country].co2intensity == null) {
//         delete state.data.countries[country]
//     }
// });

// // delete all keys of countries that are not in REQUIRED_KEYS
// Object.keys(state.data.countries).forEach(country => {
//     Object.keys(state.data.countries[country]).forEach(key => {
//         if (!REQUIRED_KEYS.includes(key)) {
//             console.log("deleting key: " + key);
//             delete state.data.countries[country][key]
//         }
//     })
// });

// // save new file state_min to public/v4
// fs.writeFileSync("./public/v4/state_min", JSON.stringify(state));

let history = JSON.parse(fs.readFileSync("./public/v4/history_DK-DK2"));

history.data.forEach((state) => {
  Object.keys(state).forEach((key) => {
    if (!REQUIRED_KEYS_HISTORY.includes(key)) {
      console.log("deleting key: " + key);
      delete state[key];
    }
  });
});
console.log(history.data[0]);

// save new file history_DK-DK2_min to public/v4
fs.writeFileSync("./public/v4/history_DK-DK2_min", JSON.stringify(history));
