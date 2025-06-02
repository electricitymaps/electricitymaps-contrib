import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import zlib from 'node:zlib';

import { Storage } from '@google-cloud/storage';

// Fix the paths for Windows/Linux consistency
let dirname = path.dirname(fileURLToPath(import.meta.url));
const __dirname = decodeURIComponent(dirname);

const SOLAR_ASSETS_PATH = path.join(__dirname, '..', 'geo', 'solar_assets.geojson');
const WIND_ASSESTS_PATH = path.join(__dirname, '..', 'geo', 'wind_assets.geojson');
const BUCKET_NAME = 'geojson-assets';

async function uploadFiles(paths) {
  for (const p of paths) {
    const gzippedPath = p + '.gz';
    await uploadFile(p, gzippedPath);
  }
}

async function uploadFile(inputPath) {
  const data = fs.readFileSync(inputPath, 'utf8', (error, data) => {
    if (error) {
      console.error('Error reading file:', error);
      process.exit(1);
    }
    return data;
  });

  const outputPath = inputPath + '.gz';

  try {
    const json = JSON.parse(data);
    const minified = JSON.stringify(json);
    const gzipped = zlib.gzipSync(minified);
    fs.writeFileSync(outputPath, gzipped);
  } catch (error) {
    console.error('Error processing file:', error);
    process.exit(1);
  }

  const storage = new Storage();
  const destinationFile = path.basename(outputPath);

  try {
    await storage.bucket(BUCKET_NAME).upload(outputPath, {
      destinationFile,
      metadata: {
        cacheControl: 'public, max-age=60',
        contentType: 'application/json',
        contentEncoding: 'gzip',
      },
    });

    console.log(`${inputPath} uploaded to ${BUCKET_NAME} as ${destinationFile}`);
  } catch (error) {
    console.error('Upload failed:', error);
  }

  fs.rmSync(outputPath);
}

await uploadFiles([SOLAR_ASSETS_PATH, WIND_ASSESTS_PATH]);
