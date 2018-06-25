// Requires `brew install imagemagick`
// import themes from './helpers/themes'

const child_process = require('child_process');
const fs = require('fs');
const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-collection'),
  require('d3-scale'),
);

const { themes } = require('./src/helpers/themes');

const numTicks = 11;
const co2color = d3.scaleLinear()
  .domain(themes.dark.co2Scale.steps)
  .range(themes.dark.co2Scale.colors);
const keys = d3.range(0, 800 + 80, 80);
const colors = {};
keys.forEach((k) => { colors[k] = co2color(k) });
colors['nan'] = '#A9A9A9';

for (let co2value in colors) {
  // generate specific color
  console.log([
    'public/images/arrow-template.png',
    '+level-colors', 'transparent,'+colors[co2value],
    `public/images/arrow-${co2value}.png`
  ])
  child_process.spawn('convert', [
    'public/images/arrow-template.png',
    '+level-colors', 'transparent,'+colors[co2value],
    `public/images/arrow-${co2value}.png`
  ]).on('close', (code) => {
    if(code !== 0) {
      console.log('child exited with code', code);
      return;
    }

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
    //     console.log('child exited with code', code);
    //     return;
    //   }

      // Apply highlight and generate GIF
      [10, 6, 2].forEach((speed, index) => {
        const args = [
          '-dispose', 'none',
          '-delay', '0',
          `public/images/arrow-${co2value}.png`,
          '-dispose', 'previous',
          '-delay', `${speed}`,
          '-loop', '0',
          '-page', `45x77+${outlineSize}+${outlineSize}`,
          'public/images/arrow-highlights/*.png',
          '-layers', 'coalesce',
          `public/images/arrow-${co2value}-animated-${index}.gif`
        ];
        const child = child_process.spawn('convert', args);
        child.on('close', (code) => {
          if(code !== 0) {
            console.log('child exited with code', code, 'for args', args);
            console.log('command: ', 'convert ' + args.join(' '));
            return;
          }

          fs.unlink(`public/images/arrow-${co2value}.png`, () => {});
          fs.unlink(`public/images/arrow-${co2value}-outline.png`, () => {});
        });

        child.stderr.on('data', (data) => {
          console.log('stderr:', data);
        });
      });
    });
  // });
}
// echo $color;
// #convert demo-arrow.png +level-colors transparent,"$color" mod-arrow.png

// done;
// #convert -dispose none -delay 0 demo-arrow.png -dispose previous -delay 16x1000 -loop 0 highlight/*.png -layers coalesce animated.gif
