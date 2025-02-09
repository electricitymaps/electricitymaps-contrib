const express = require('express');
const app = express();
const cors = require('cors');
const fs = require('fs');
const url = require('url');

const HOST = '127.0.0.1';
const PORT = process.argv[2] || 8001;

app.use(cors());

const DEFAULT_ZONE_KEY = 'DE';

app.get('/v8/details/:aggregate/:zoneId', (req, res, next) => {
  const { aggregate, zoneId } = req.params;

  // if file exists return it, otherwise redirect to DEFAULT file
  if (fs.existsSync(`./public/v8/details/${aggregate}/${zoneId}.json`)) {
    // file structure of project will return the correct file
    next();
  } else {
    res.redirect(`/v8/details/${aggregate}/${DEFAULT_ZONE_KEY}`);
  }
});

app.get('/v8/gfs/wind', (req, res, next) => {
  const { refTime, targetTime } = req.query;

  fs.readFile(`./public/v8/gfs/wind.json`, (err, data) => {
    const jsonData = JSON.parse(data);
    jsonData.data[0].header.refTime = targetTime;

    res.json(jsonData);
  });
});

app.get('/v8/gfs/solar', (req, res, next) => {
  const { refTime, targetTime } = req.query;

  fs.readFile(`./public/v8/gfs/solar.json`, (err, data) => {
    const jsonData = JSON.parse(data);
    jsonData.data[0].header.refTime = targetTime;

    res.json(jsonData);
  });
});

app.use(function (req, res, next) {
  // Get rid of query parameters so we can serve static files
  if (Object.entries(req.query).length !== 0) {
    res.redirect(url.parse(req.url).pathname);
  } else {
    // Log all requests to static files
    console.log(req.method, req.path);
    next();
  }
});

app.use(express.static('public', { extensions: ['json'] }));

const server = app.listen(PORT, HOST, () => {
  console.log(`mockserver running at: http://${HOST}:${PORT}/`);
});
