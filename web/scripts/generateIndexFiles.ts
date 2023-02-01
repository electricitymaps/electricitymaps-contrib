import * as fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { mergeZones } from './generateZonesConfig.js';
console.log('Generating index files...');

// Create list of paths to be used
const generalPaths = ['/map', '/faq'];
const zones = mergeZones();
const zonePaths = Object.keys(zones).map((zone) => `/zone/${zone}`);
const allPaths = [...generalPaths, ...zonePaths];

// Generate index.html files for all paths
let filesGenerated = 0;
const indexHtml = fs.readFileSync(new URL('../dist/index.html', import.meta.url), 'utf8');
for (const filePath of allPaths) {
  const directory = fileURLToPath(new URL(`../dist${filePath}`, import.meta.url));
  if (!fs.existsSync(directory)) {
    fs.mkdirSync(directory, { recursive: true });
  }
  const file = path.resolve(directory, 'index.html');
  if (!fs.existsSync(file)) {
    fs.writeFileSync(path.resolve(directory, 'index.html'), indexHtml);
    console.log(`Created index.html for ${filePath}`);
    filesGenerated++;
  }
}

console.log(`Generated ${filesGenerated} new files.`);
