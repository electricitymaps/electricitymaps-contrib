// Requires `brew install imagemagick`

import child_process from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

import { range } from 'd3-array';
import { scaleLinear } from 'd3-scale';

// Copied from '../src/hooks/colors.ts'
const defaultCo2Scale = {
  steps: [0, 150, 600, 750, 800],
  colors: ['#2AA364', '#F5EB4D', '#9E4229', '#381D02', '#381D02'],
};
const colorblindCo2Scale = {
  steps: [0, 200, 400, 600, 800],
  colors: ['#FFFFB0', '#E0B040', '#A06030', '#602020', '#000010'],
};

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
ensureDirectoryExists('arrows/arrow-highlights');
ensureDirectoryExists('../public/images/arrows');

// Check if ImageMagick is installed
try {
  const result = child_process.execSync('magick -version', { encoding: 'utf8' });
  console.log(`ImageMagick found: ${result.trim().split('\n')[0]}`);
} catch {
  console.error('ImageMagick not found! Please install with: brew install imagemagick');
  process.exit(1);
}

function generateArrows(prefix, scaleTheme) {
  console.log(`\nGenerating arrows with prefix: "${prefix}"`);
  const co2color = scaleLinear().domain(scaleTheme.steps).range(scaleTheme.colors);

  const colors = { nan: '#A9A9A9' };
  const keys = range(0, 800 + 80, 80);

  for (const k of keys) {
    colors[k] = co2color(k);
  }

  // Check if arrow template exists
  const templatePath = 'arrows/arrow-template.png';
  if (!fs.existsSync(templatePath)) {
    console.error(`Template file not found: ${templatePath}`);
    console.error('Make sure you are running the script from the web directory');
    return;
  }

  console.log(`Processing ${Object.keys(colors).length} color values...`);

  for (const [co2value, color] of Object.entries(colors)) {
    // generate specific color
    const outputPath = `../public/images/arrows/${prefix}arrow-${co2value}.png`;
    console.log(`\nGenerating arrow for value ${co2value} with color ${color}`);
    console.log(`Output path: ${path.resolve(outputPath)}`);

    const convertArguments = [
      templatePath,
      '+level-colors',
      `transparent,${color}`,
      outputPath,
    ];

    console.log(`Running: convert ${convertArguments.join(' ')}`);

    const baseArrowProcess = child_process.spawn('magick', convertArguments);

    baseArrowProcess.stderr.on('data', (data) => {
      console.error(`Base arrow stderr: ${data}`);
    });

    baseArrowProcess.on('close', (code) => {
      if (code !== 0) {
        console.error(`Error: Base arrow process exited with code ${code}`);
        return;
      }

      console.log(`Successfully created base arrow for ${co2value}`);
      const outlineSize = 2;

      // Apply highlight and generate GIF
      for (const [index, speed] of [10, 6, 2].entries()) {
        const gifOutput = `../public/images/arrows/${prefix}arrow-${co2value}-animated-${index}.gif`;

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
          'arrows/arrow-highlights/*.png',
          '-layers',
          'coalesce',
          gifOutput,
        ];

        const child = child_process.spawn('magick', convertArguments);

        child.stderr.on('data', (data) => {
          console.error(`GIF stderr: ${data}`);
        });

        child.on('close', (code) => {
          if (code !== 0) {
            console.error(`Error: GIF process exited with code ${code}`);
            return;
          }

          console.log(
            `Successfully created animated GIF for ${co2value} with speed index ${index}`
          );

          // Generate WebP version from the GIF
          const webpOutput = `../public/images/arrows/${prefix}arrow-${co2value}-animated-${index}.webp`;
          console.log(`Converting to WebP: ${path.resolve(webpOutput)}`);

          const webpArguments = [gifOutput, '-quality', '75', webpOutput];

          const webpChild = child_process.spawn('magick', webpArguments);

          webpChild.stderr.on('data', (data) => {
            console.error(`WebP stderr: ${data}`);
          });

          webpChild.on('close', (webpCode) => {
            if (webpCode !== 0) {
              console.error(`Error: WebP conversion failed with code ${webpCode}`);
              return;
            }

            console.log(
              `Successfully created WebP version for ${co2value} with speed index ${index}`
            );

            // Clean up temporary files after both GIF and WebP are created
            fs.unlink(outputPath, (error) => {
              if (error) {
                console.error(`Error deleting ${outputPath}:`, error);
              }
            });

            const outlineFile = `../public/images/arrows/${prefix}arrow-${co2value}-outline.png`;
            fs.unlink(outlineFile, (error) => {
              if (error && error.code !== 'ENOENT') {
                console.error(`Error deleting ${outlineFile}:`, error);
              }
            });
          });
        });
      }
    });
  }
}

console.log('Starting arrow generation process...');
generateArrows('', defaultCo2Scale);
generateArrows('colorblind-', colorblindCo2Scale);
