// Run this script using `pnpm run generate-arrows`
// Requires `brew install imagemagick`
import child_process from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

import { ScaleLinear, ScaleQuantize } from 'd3-scale';

import {
  arrowfilesIndices,
  generateQuantizedExchangeColorScale,
} from '../src/features/exchanges/scales';
import { colors } from '../src/hooks/colors';
import { MapColorSource } from '../src/utils/constants';

// Create output directory if it doesn't exist
const ensureDirectoryExists = (directoryPath) => {
  const absolutePath = path.resolve(directoryPath);
  console.log(`Checking directory: ${absolutePath}`);
  if (!fs.existsSync(absolutePath)) {
    console.log(`Creating directory: ${absolutePath}`);
    fs.mkdirSync(absolutePath, { recursive: true });
  }
};

// Make sure template and output directories exist
ensureDirectoryExists('./scripts/arrows/arrow-highlights');
ensureDirectoryExists('./public/images/arrows');

// Check if ImageMagick is installed
try {
  const result = child_process.execSync('magick -version', { encoding: 'utf8' });
  console.log(`ImageMagick found: ${result.trim().split('\n')[0]}`);
} catch {
  console.error('ImageMagick not found! Please install with: brew install imagemagick');
  process.exit(1);
}

async function runCommandWithOutput(command, arguments_: string[] = []) {
  return new Promise((resolve, reject) => {
    const child = child_process.spawn(command, arguments_);
    let output = '';
    let errorOutput = '';

    child.stdout.on('data', (data) => {
      output += data.toString();
    });

    child.stderr.on('data', (data) => {
      errorOutput += data.toString();
    });

    child.on('error', reject);

    child.on('close', (code) => {
      if (code === 0) {
        resolve(output);
      } else {
        reject(new Error(`Error: ${errorOutput}`));
      }
    });
  });
}

async function generateArrows(
  prefix: string,
  scaleArrow: ScaleQuantize<number, string> | undefined,
  scaleColor: ScaleLinear<string, string, string>
) {
  if (!scaleArrow) {
    return;
  }
  console.log(`\nGenerating arrows with prefix: "${prefix}"`);

  const colors = { nan: '#A9A9A9' };
  const keys = arrowfilesIndices;

  for (const k of keys) {
    const valueExtent = scaleArrow.invertExtent(k);
    const value = (valueExtent[0] + valueExtent[1]) / 2;
    colors[k] = scaleColor(value);
  }

  // Check if arrow template exists
  const templatePath = 'scripts/arrows/arrow-template.png';
  if (!fs.existsSync(templatePath)) {
    console.error(`Template file not found: ${templatePath}`);
    console.error('Make sure you are running the script from the web directory');
    return;
  }

  console.log(`Processing ${Object.keys(colors).length} color values...`);

  for (const [key, color] of Object.entries(colors)) {
    // generate specific color
    const outputPath = `./public/images/arrows/${prefix}arrow-${key}.png`;
    console.log(`\nGenerating arrow for value ${key} with color ${color}`);
    console.log(`Output path: ${path.resolve(outputPath)}`);

    const convertArguments = [
      templatePath,
      '+level-colors',
      `transparent,${color}`,
      outputPath,
    ];

    console.log(`Running: convert ${convertArguments.join(' ')}`);

    await runCommandWithOutput('convert', convertArguments);

    console.log(`Successfully created base arrow for ${key}`);
    const outlineSize = 2;

    // Apply highlight and generate GIF
    for (const [index, speed] of [10, 6, 2].entries()) {
      const gifOutput = `./public/images/arrows/${prefix}arrow-${key}-animated-${index}.gif`;

      console.log(
        `Generating animated gif: ${path.resolve(gifOutput)} with speed ${speed}`
      );

      const convertArguments = [
        '-dispose',
        'none',
        '-delay',
        '0',
        outputPath,
        '-dispose',
        'previous',
        '-delay',
        `${speed}`,
        '-loop',
        '0',
        '-page',
        `45x77+${outlineSize}+${outlineSize}`,
        'scripts/arrows/arrow-highlights/*.png',
        '-layers',
        'coalesce',
        gifOutput,
      ];

      await runCommandWithOutput('convert', convertArguments);

      console.log(
        `Successfully created animated GIF for ${key} with speed index ${index}`
      );

      // Generate WebP version from the GIF
      const webpOutput = `./public/images/arrows/${prefix}arrow-${key}-animated-${index}.webp`;
      console.log(`Converting to WebP: ${path.resolve(webpOutput)}`);

      const webpArguments = [gifOutput, '-quality', '40', webpOutput];

      await runCommandWithOutput('magick', webpArguments);

      console.log(
        `Successfully created WebP version for ${key} with speed index ${index}`
      );
    }

    // Clean up temporary files after both GIF and WebP are created
    fs.unlink(outputPath, (error) => {
      if (error) {
        console.error(`Error deleting ${outputPath}:`, error);
      }
    });

    const outlineFile = `./public/images/arrows/${prefix}arrow-${key}-outline.png`;
    fs.unlink(outlineFile, (error) => {
      if (error && error.code !== 'ENOENT') {
        console.error(`Error deleting ${outlineFile}:`, error);
      }
    });
  }
}

console.log('Starting arrow generation process...');
for (const mapColorSource of Object.keys(MapColorSource)) {
  console.log(`Generating arrows for ${mapColorSource}`);
  await generateArrows(
    mapColorSource.toLowerCase() + '-',
    generateQuantizedExchangeColorScale(mapColorSource),
    colors.bright.colorScale[mapColorSource]
  );
  await generateArrows(
    mapColorSource.toLowerCase() + '-colorblind-',
    generateQuantizedExchangeColorScale(mapColorSource),
    colors.colorblindBright.colorScale[mapColorSource]
  );
}
process.exit(0);
