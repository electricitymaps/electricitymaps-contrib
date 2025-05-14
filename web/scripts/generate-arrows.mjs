// Requires `brew install imagemagick`

import child_process from 'node:child_process';
import fs from 'node:fs';

import { range } from 'd3-array';
import { scaleLinear } from 'd3-scale';

// Copied from '../src/hooks/colors.ts'
const defaultCo2Scale = {
  steps: [0, 150, 600, 750, 800],
  colors: ['#2AA364', '#F5EB4D', '#9E4229', '#381D02', '#381D02'],
};
const colorblindCo2Scale = {
  steps: [0, 200, 400, 600, 800],
  colors: ['#FFFFB0', '#E3BF66', '#BB833C', '#8B4D2B', '#4E241F'],
};
function generateArrows(prefix, scaleTheme) {
  const co2color = scaleLinear().domain(scaleTheme.steps).range(scaleTheme.colors);

  const colors = { nan: '#A9A9A9' };
  const keys = range(0, 800 + 80, 80);
  for (const k of keys) {
    colors[k] = co2color(k);
  }

  for (const co2value in colors) {
    // generate specific color
    console.info([
      'arrows/arrow-template.png',
      '+level-colors',
      `transparent,${colors[co2value]}`,
      `../public/images/arrows/${prefix}arrow-${co2value}.png`,
    ]);
    child_process
      .spawn('convert', [
        'arrows/arrow-template.png',
        '+level-colors',
        `transparent,${colors[co2value]}`,
        `../public/images/arrows/${prefix}arrow-${co2value}.png`,
      ])
      .on('close', (code) => {
        if (code !== 0) {
          console.error('child exited with code', code);
          return;
        }
        const outlineSize = 2;

        // Apply highlight and generate GIF
        for (const [index, speed] of [10, 6, 2].entries()) {
          const arguments_ = [
            '-dispose',
            'none',
            '-delay',
            '0',
            `../public/images/arrows/${prefix}arrow-${co2value}.png`,
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
            `../public/images/arrows/${prefix}arrow-${co2value}-animated-${index}.gif`,
          ];
          const child = child_process.spawn('convert', arguments_);
          child.on('close', (code) => {
            if (code !== 0) {
              console.error('child exited with code', code, 'for args', arguments_);
              console.error('command:', `convert ${arguments_.join(' ')}`);
              return;
            }

            fs.unlink(`../public/images/arrows/${prefix}arrow-${co2value}.png`, () => {});
            fs.unlink(
              `../public/images/arrows/${prefix}arrow-${co2value}-outline.png`,
              () => {}
            );
          });

          child.stderr.on('data', (data) => {
            console.info('stderr:', data);
          });
        }
      });
    // });
  }
  // echo $color;
  // #convert demo-arrow.png +level-colors transparent,"$color" mod-arrow.png

  // done;
  // #convert -dispose none -delay 0 demo-arrow.png -dispose previous -delay 16x1000 -loop 0 highlight/*.png -layers coalesce animated.gif
}

generateArrows('', defaultCo2Scale);
generateArrows('colorblind-', colorblindCo2Scale);
