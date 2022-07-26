const axios = require('axios');
const fs = require('fs');

const writeJSON = (fileName, obj, encoding = 'utf8') => fs.writeFileSync(fileName, JSON.stringify(obj), encoding);

const fetchAndStoreData = async (url, savePath) => axios.get(url).then((res) => writeJSON(savePath, res.data));

const CORE_URL = 'http://localhost:8001/v5';
const timeAggregates = ['hourly', 'daily', 'monthly', 'yearly'];
const historyZones = ['UA', 'DK-DK2'];

timeAggregates.forEach(async (agg) => {
  await fetchAndStoreData(`${CORE_URL}/state/${agg}`, `./public/v5/state/${agg}.json`);
  await fetchAndStoreData(`${CORE_URL}/history/${agg}?countryCode=DE`, `./public/v5/history/${agg}.json`); // default history data
  historyZones.forEach(async (zoneId) => {
    await fetchAndStoreData(
      `${CORE_URL}/history/${agg}?countryCode=${zoneId}`,
      `./public/v5/history/${zoneId}/${agg}.json`
    );
  });
});
