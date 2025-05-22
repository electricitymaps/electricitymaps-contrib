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
    compressFile(p);
    await uploadFile(p);
    cleanupFile(p);
  }
}

function compressFile(inputPath) {
  fs.readFile(inputPath, 'utf8', (error, data) => {
    if (error) {
      console.error('Error reading file:', error);
      process.exit(1);
    }

    const outputPath = inputPath + '.gz';
    try {
      const json = JSON.parse(data);
      const minified = JSON.stringify(json);
      const gzipped = zlib.gzipSync(minified);
      fs.writeFileSync(outputPath, gzipped);
      console.log(`✅ Minified and gzipped: ${outputPath}`);
    } catch (error) {
      console.error('Error parsing or compressing JSON:', error);
      process.exit(1);
    }
  });
}

async function uploadFile(inputPath) {
  const storage = new Storage();
  const inputFile = inputPath + '.gz';
  const destinationFile = path.basename(inputFile);

  try {
    await storage.bucket(BUCKET_NAME).upload(inputFile, {
      destinationFile,
      metadata: {
        cacheControl: 'public, max-age=60',
        contentType: 'application/json',
        contentEncoding: 'gzip',
      },
    });

    console.log(`${inputFile} uploaded to ${BUCKET_NAME} as ${destinationFile}`);
  } catch (error) {
    console.error('Upload failed:', error);
  }
}

function cleanupFile(inputPath) {
  const inputFile = inputPath + '.gz';
  fs.rm(inputFile, (error, _data) => {
    if (error) {
      console.error('Error deleting file:', error);
      process.exit(1);
    }
  });
}

await uploadFiles([SOLAR_ASSETS_PATH, WIND_ASSESTS_PATH]);
