var express = require('express');
var app = express();
var http = require('http').Server(app);
var statsd = require('node-statsd');
var MongoClient = require('mongodb').MongoClient;

// * Database
var mongoCollection;
MongoClient.connect(process.env['MONGO_URL'], function(err, db) {
    if (err) throw (err);
    console.log('Connected to database');
    mongoCollection = db.collection('realtime');
    // Create indexes
    mongoCollection.createIndexes(
        [
            { datetime: -1 },
            { countryCode: 1},
            { datetime: -1, countryCode: 1 }
        ],
        null,
        function (err, indexName) {
            if (err) console.error(err);
            else console.log('Database indexes created');
        }
    );
    http.listen(8000, function() {
        console.log('Listening on *:8000');
    });
});

// * Metrics
var statsdClient = new statsd.StatsD();
statsdClient.post = 8125;
statsdClient.host = process.env['STATSD_HOST'];
statsdClient.prefix = 'electricymap_api';

// * Routes
app.use(express.static('static'));
app.use(express.static('vendor'));
app.get('/v1/wind', function(req, res) {
    statsdClient.increment('wind_GET');
    res.header('Content-Encoding', 'gzip');
    res.sendFile(__dirname + '/data/wind.json.gz');
});
app.get('/v1/solar', function(req, res) {
    statsdClient.increment('solar_GET');
    res.header('Content-Encoding', 'gzip');
    res.sendFile(__dirname + '/data/solar.json.gz');
});
app.get('/v1/production', function(req, res) {
    statsdClient.increment('production_GET');
    var t0 = new Date().getTime();
    mongoCollection.aggregate([
        {'$sort': {'countryCode': 1, 'datetime': -1}},
        {'$group': {'_id': '$countryCode', 'lastDocument': {'$first': '$$CURRENT'}}}
    ], function (err, result) {
        if (err) {
            statsdClient.increment('production_GET_ERROR');
            console.error(err);
            res.status(500).json({error: 'Unknown database error'});
        } else {
            obj = {}
            result.forEach(function(d) { obj[d['_id']] = d.lastDocument; });
            res.json({status: 'ok', data: obj});
            statsdClient.timing('production', new Date().getTime() - t0);
        }
    });
});
app.get('/health', function(req, res) {
    statsdClient.increment('health_GET');
    var EXPIRATION_SECONDS = 30 * 60.0;
    mongoCollection.findOne({}, {sort: [['datetime', -1]]}, function (err, doc) {
        if (err) {
            console.error(err);
            res.status(500).json({error: 'Unknown database error'});
        } else {
            if (new Date().getTime() - new Date(doc.datetime).getTime() > EXPIRATION_SECONDS * 1000.0)
                res.status(500).json({error: 'Database is empty or last measurement is too old'});
            else
                res.json({status: 'ok'});
        }
    });
});
