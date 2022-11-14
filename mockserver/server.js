const express = require('express');
const app = express();
const cors = require('cors');
const fs = require('fs');
const url = require('url');

const PORT = process.argv[2] || 8001;

app.use(cors());

app.get('/v6/details/:aggregate/:zoneId', (req, res, next) => {
  const { aggregate, zoneId } = req.params;
  if (zoneId && fs.existsSync(`./public/v6/details/${zoneId}/${aggregate}.json`)) {
    // we alter the URL to use the specific zone details file if available
    res.redirect(`/v6/details/${zoneId}/${aggregate}`);
  } else {
    // otherwise fallback to general details files (that are using data from DE)
    next();
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
