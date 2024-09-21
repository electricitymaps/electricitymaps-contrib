// Generates a static sitemap for the app based on the zones in the config file

import fs from 'node:fs';
import path from 'node:path';

import zonesConfig from '../config/zones.json' assert { type: 'json' };

const __dirname = path.dirname(new URL(import.meta.url).pathname);
const SITEMAP_DIR = path.join(__dirname, '..', 'public');
const SITEMAP_PATH = path.join(SITEMAP_DIR, 'sitemap.xml');

function generateSitemap() {
  // Ensure the directory exists
  if (!fs.existsSync(SITEMAP_DIR)) {
    fs.mkdirSync(SITEMAP_DIR, { recursive: true });
  }

  const zoneUrls = Object.keys(zonesConfig.zones)
    .map((zone) => `<url><loc>https://app.electricitymaps.com/zone/${zone}</loc></url>`)
    .join('');

  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
  <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://app.electricitymaps.com/</loc></url>
  <url><loc>https://app.electricitymaps.com/map/</loc></url>
  ${zoneUrls}
</urlset>`.replaceAll(/\n\s*/g, '');

  fs.writeFileSync(SITEMAP_PATH, sitemap);
}

generateSitemap();
