const yaml = require('js-yaml');
const path = require('path');
const fs = require('fs');
const readline = require('readline-sync');

const zone = readline.question('For which zone do you wish to sum its subzones? ');

const basePath = path.resolve(__dirname, '../config/zones');
let zoneObject;
try {
  zoneObject = yaml.load(fs.readFileSync(`${basePath}/${zone}.yaml`, 'utf8'));
} catch (e) {
  if (e.code === 'ENOENT') {
    console.error(`Zone ${zone} does not exist.`);
  } else {
    console.error('An unknown error occurred while reading the zone file.');
    console.error(e);
  }
  process.exit(1);
}
const capacities = {};
if (zoneObject.subZoneNames) {
  zoneObject.subZoneNames.forEach((subzone) => {
    const subzoneObject = yaml.load(fs.readFileSync(`${basePath}/${subzone}.yaml`, 'utf8'));
    for (const key in subzoneObject.capacity) {
      if (subzoneObject.capacity[key] !== null) {
        capacities[key]
          ? (capacities[key] += subzoneObject.capacity[key])
          : (capacities[key] = subzoneObject.capacity[key]);
      }
    }
  });
} else {
  console.error(`Zone ${zone} does not have any subzones.`);
  process.exit(1);
}

for (const key in capacities) {
  if (capacities[key] === null) {
    delete capacities[key];
  }
}
zoneObject.capacity = capacities;
// eslint-disable-next-line no-console
console.info('Sucscessfully summed subzone capacities to:', zoneObject.capacity);
try {
  fs.writeFileSync(`${basePath}/${zone}.yaml`, yaml.dump(zoneObject));
} catch (e) {
  console.error('An unknown error occurred while writing the zone file.');
  console.error(e);
  process.exit(1);
}
// eslint-disable-next-line no-console
console.info(`Successfully added capacity to ${basePath}/${zone}.yaml`);
