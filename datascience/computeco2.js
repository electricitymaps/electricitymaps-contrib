var co2calculatorlib = require('../api/static/app/co2eq');
var fs = require('fs')

var lineReader = require('readline').createInterface({
  input: fs.createReadStream('backup.jsonr')
});
var writer = fs.createWriteStream('backupWithCo2.jsonr', {
  flags: 'w'
});

lineReader.on('line', function (line) {
  writer.write(line + "\n");
});
lineReader.on('end', function () {
    console.log('end');
    writer.end();
})
