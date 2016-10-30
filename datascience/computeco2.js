var fs = require('fs');
var d3 = require('d3');
var co2calculatorlib = require('../api/static/app/co2eq');
console.log('Starting..')

// Requires a sorted list:
// cat backup.jsonr | jq --slurp --compact-output 'sort_by(."datetime.$date") | .[]' > backupSorted.jsonr

var lineReader = require('readline').createInterface({
    input: fs.createReadStream('backupSorted.jsonr')
});
var writer = fs.createWriteStream('backupWithCo2.jsonr', {
    flags: 'w'
});

var lastCountries = {};
lineReader.on('line', function (line) {
    obj = JSON.parse(line);
    var countryCode = obj['countryCode'];
    lastCountries[countryCode] = {'data': obj};
    var co2calc = co2calculatorlib.Co2eqCalculator();
    co2calc.compute(lastCountries);
    d3.values(lastCountries).forEach(function (country) {
        console.log(country.data.datetime['$date'], country.data.countryCode, co2calc.assignments[country.data.countryCode]);
        country.data.co2intensity = co2calc.assignments[country.data.countryCode];
    });
    writer.write(JSON.stringify(lastCountries) + "\n");
});
lineReader.on('end', function () {
    console.log('end');
    writer.end();
});
