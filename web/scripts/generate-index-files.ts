import * as fs from 'fs';
import * as path from 'node:path';
import { mergeZones } from './generate-zones-config';
console.log('Generating index files...');

// Create list of paths to be used
const generalPaths = ['/map', '/faq'];
const zones = mergeZones();
const zonePaths = Object.keys(zones).map((zone) => `/zone/${zone}`);
const allPaths = [...generalPaths, ...zonePaths];

// Generate index.html files for all paths
let filesGenerated = 0;
const indexHtml = fs.readFileSync(path.resolve(__dirname, '../dist/index.html'), 'utf8');
allPaths.forEach((filePath) => {
  const dir = path.resolve(__dirname, `../dist${filePath}`);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  const file = path.resolve(dir, 'index.html');
  if (!fs.existsSync(file)) {
    fs.writeFileSync(path.resolve(dir, 'index.html'), indexHtml);
    console.log(`Created index.html for ${filePath}`);
    filesGenerated++;
  }
});

console.log(`Generated ${filesGenerated} new files.`);
