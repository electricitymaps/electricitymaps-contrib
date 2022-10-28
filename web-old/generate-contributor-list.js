var d3 = require('d3');
const { mergeZones } = require('./generate-zones-config');
const { saveZoneYaml } = require('./files');

function fetch(path) {
  return new Promise(function (resolve, reject) {
    d3.json(path, function (err, data) {
      if (err || !data) {
        reject(err);
      } else {
        resolve(data);
      }
    });
  });
}

var zones = mergeZones();
var jobs = Object.keys(zones).map(function (zone_name) {
  var generationParser = (zones[zone_name].parsers || {}).production;
  if (!generationParser) {
    return Promise.resolve(null);
  }
  var path = `https://api.github.com/repos/tmrowco/electricitymap/commits?path=parsers/${`${
    generationParser.split('.')[0]
  }.py`}`;
  // Get all commits
  return fetch(path)
    .then((e) => [zone_name, e])
    .catch((e) => {
      console.error(`Zone ${zone_name} failed with error ${e}`);
      process.exit(-1);
    });
});

Promise.all(jobs).then((parsers) => {
  parsers.forEach((obj) => {
    if (!obj) {
      return;
    }
    var zone_name = obj[0];
    var commits = obj[1];
    var authors = {}; // unique author list
    commits.forEach((commit) => {
      console.info(commit.author);
      if (commit.author) {
        authors[commit.author.html_url] = true;
      }
    });
    zones[zone_name].contributors = Object.keys(authors);
    saveZoneYaml(zone_name, zones[zone_name]);
  });
});
