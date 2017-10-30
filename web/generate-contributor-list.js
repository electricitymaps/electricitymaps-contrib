// Pass as argument the path to zones.json

var d3 = require('d3')
var fs = require('fs')

function fetch(path) {
    return new Promise(function(resolve, reject) {
        d3.json(path, function(err, data) {
            if (err || !data) { reject(err); }
            else { resolve(data); }
        })
    })
}

var zones = JSON.parse(fs.readFileSync(process.argv[2]))
var jobs = Object.keys(zones).map(function(zone_name, i) {
    var generationParser = (zones[zone_name].parsers || {}).production;
    if (!generationParser) { return Promise.resolve(null); }
    var path = `https://api.github.com/repos/tmrowco/electricitymap/commits?path=parsers/${generationParser.split('.')[0] + '.py'}`
    // Get all commits
    return fetch(path).then((e) => [zone_name, e]).catch((e) => {
        console.error(`Zone ${zone_name} failed with error ${e}`);
        process.exit(-1)
    })
})

Promise.all(jobs).then((parsers) => {
    parsers.forEach((obj, i) => {
        if (!obj) { return; }
        var zone_name = obj[0]
        var commits = obj[1]
        var authors = {} // unique author list
        commits.forEach((commit) => {
            console.log(commit.author)
            if (commit.author) {
                authors[commit.author.html_url] = true
            }
        })
        zones[zone_name].contributors = Object.keys(authors)
    })
    fs.writeFileSync(process.argv[2], JSON.stringify(zones, null, '  '))
})
