const axios = require('axios');
const fs = require('fs');

const writeJSON = (fileName, obj, encoding = 'utf8') =>
  fs.writeFileSync(fileName, JSON.stringify(obj), encoding);

const fetchAndStoreData = async (url, savePath) => {
  // Create folder for savePath if it doesn't exist
  const saveDir = savePath.split('/').slice(0, -1).join('/');
  await fs.promises.mkdir(saveDir, { recursive: true }).catch(console.error);

  return axios.get(url).then((res) => writeJSON(savePath, res.data));
};

const CORE_URL = 'http://localhost:8001/v8';
const timeAggregates = ['last_hour', 'hourly', 'daily', 'monthly', 'yearly'];
const detailsZones = ['DE', 'DK-DK2'];

const generateMockData = async () => {
  timeAggregates.forEach(async (agg) => {
    try {
      await fetchAndStoreData(
        `${CORE_URL}/state/${agg}`,
        `./public/v8/state/${agg}.json`
      );

      if (agg !== 'last_hour') {
        detailsZones.forEach(async (zoneId) => {
          await fetchAndStoreData(
            `${CORE_URL}/details/${agg}/${zoneId}`,
            `./public/v8/details/${agg}/${zoneId}.json`
          );
        });
      }
    } catch (error) {
      console.error(error);
    }
  });
};

generateMockData();
