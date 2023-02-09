const express = require('express');
const app = express();
const cors = require('cors');
const fs = require('fs');
const url = require('url');

const PORT = process.argv[2] || 8001;

app.use(cors());

const DEFAULT_ZONE_KEY = 'DE';

app.get('/v6/details/:aggregate/:zoneId', (req, res, next) => {
  const { aggregate, zoneId } = req.params;

  // if file exists return it, otherwise redirect to DEFAULT file
  if (fs.existsSync(`./public/v6/details/${aggregate}/${zoneId}.json`)) {
    // file structure of project will return the correct file
    next();
  } else {
    res.redirect(`/v6/details/${aggregate}/${DEFAULT_ZONE_KEY}`);
  }
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

const server = app.listen(PORT, () => {
  console.log('Started mockserver on port: ' + PORT);
});
