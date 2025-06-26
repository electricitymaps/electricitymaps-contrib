import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// Get the directory of this script
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Define source and destination paths
const sourcePath = path.resolve(__dirname, '../../config/data_centers/data_centers.json');
const destinationPath = path.resolve(__dirname, '../config/data_centers.json');

// Make sure the destination directory exists
const destinationDirectory = path.dirname(destinationPath);
if (!fs.existsSync(destinationDirectory)) {
  fs.mkdirSync(destinationDirectory, { recursive: true });
}

// Copy the file
try {
  const data = fs.readFileSync(sourcePath, 'utf8');
  fs.writeFileSync(destinationPath, data, 'utf8');
  console.log(`Successfully copied data_centers.json to ${destinationPath}`);
} catch (error) {
  console.error('Error copying data_centers.json:', error);
  process.exit(1);
}
