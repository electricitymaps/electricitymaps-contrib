// Requires `brew install imagemagick`

const child_process = require('child_process');
const fs = require('fs');
const d3 = Object.assign({}, require('d3-array'), require('d3-collection'), require('d3-scale'));

import { themes } from './src/helpers/themes';

function generateArrows(prefix, scaleTheme) {
  const co2color = d3.scaleLinear().domain(scaleTheme.steps).range(scaleTheme.colors);

  const colors = { nan: '#A9A9A9' };
  const keys = d3.range(0, 800 + 80, 80);
  keys.forEach((k) => {
    colors[k] = co2color(k);
  });

  for (const co2value in colors) {
    // generate specific color
    console.info([
      'public/images/arrow-template.png',
      '+level-colors',
      `transparent,${colors[co2value]}`,
      `public/images/${prefix}arrow-${co2value}.png`,
    ]);
    child_process
      .spawn('convert', [
        'public/images/arrow-template.png',
        '+level-colors',
        `transparent,${colors[co2value]}`,
        `public/images/${prefix}arrow-${co2value}.png`,
      ])
      .on('close', (code) => {
        if (code !== 0) {
          console.error('child exited with code', code);
          return;
        }
        const outlineSize = 2;

        // make an outline (NOT being currently used with new arrow shape)
        // const outlineSize = 2;
        // const whiteArrowAfterCo2Intensity = 640;
        // child_process.spawn('convert', [
        //   `public/images/arrow-${co2value}.png`,
        //   '-bordercolor', 'none',
        //   '-border', outlineSize,
        //   '\(', '-clone', '0', '-alpha', 'off', '-fill', co2value >= whiteArrowAfterCo2Intensity ? 'white' : 'black', '-colorize', '100%', '\)',
        //   '\(', '-clone', '0', '-alpha', 'extract', '-morphology', 'edgeout', 'octagon:'+outlineSize, '\)',
        //   '-compose', 'over',
        //   '-composite', `public/images/arrow-${co2value}-outline.png`
        // ]).on('close', code => {
        //   if(code !== 0) {
        //     console.error('child exited with code', code);
        //     return;
        //   }

        // Apply highlight and generate GIF
        [10, 6, 2].forEach((speed, index) => {
          const args = [
            '-dispose',
            'none',
            '-delay',
            '0',
            `public/images/${prefix}arrow-${co2value}.png`,
            '-dispose',
            'previous',
            '-delay',
            `${speed}`,
            '-loop',
            '0',
            '-page',
            `45x77+${outlineSize}+${outlineSize}`,
            'public/images/arrow-highlights/*.png',
            '-layers',
            'coalesce',
            `public/images/${prefix}arrow-${co2value}-animated-${index}.gif`,
          ];
          const child = child_process.spawn('convert', args);
          child.on('close', (code) => {
            if (code !== 0) {
              console.error('child exited with code', code, 'for args', args);
              console.error('command: ', `convert ${args.join(' ')}`);
              return;
            }

            fs.unlink(`public/images/${prefix}arrow-${co2value}.png`, () => {});
            fs.unlink(`public/images/${prefix}arrow-${co2value}-outline.png`, () => {});
          });

          child.stderr.on('data', (data) => {
            console.info('stderr:', data);
          });
        });
      });
    // });
  }
  // echo $color;
  // #convert demo-arrow.png +level-colors transparent,"$color" mod-arrow.png

  // done;
  // #convert -dispose none -delay 0 demo-arrow.png -dispose previous -delay 16x1000 -loop 0 highlight/*.png -layers coalesce animated.gif
}

generateArrows('', themes.dark.co2Scale);
generateArrows('colorblind-', themes.colorblindDark.co2Scale);
