// TODO: Merge themes and scales

const d3 = Object.assign(
  {},
  require('d3-array'),
  require('d3-interpolate'),
  require('d3-scale'),
  require('d3-scale-chromatic'),
);


// ** Wind
const maxWind = 15;
const windColor = d3.scaleLinear()
  .domain(d3.range(10).map(i => d3.interpolate(0, maxWind)(i / (10 - 1))))
  .range([
    'rgba(0,   255, 255, 1.0)',
    'rgba(100, 240, 255, 1.0)',
    'rgba(135, 225, 255, 1.0)',
    'rgba(160, 208, 255, 1.0)',
    'rgba(181, 192, 255, 1.0)',
    'rgba(198, 173, 255, 1.0)',
    'rgba(212, 155, 255, 1.0)',
    'rgba(225, 133, 255, 1.0)',
    'rgba(236, 109, 255, 1.0)',
    'rgba(255,  30, 219, 1.0)',
  ])
  .clamp(true);


// ** Solar
const maxSolarDSWRF = 1000;
const minDayDSWRF = 0;
// const nightOpacity = 0.8;
const minSolarDayOpacity = 0.6;
const maxSolarDayOpacity = 0.0;
const solarDomain = d3.range(10).map(i => d3.interpolate(minDayDSWRF, maxSolarDSWRF)(i / (10 - 1)));
const solarRange = d3.range(10).map((i) => {
  const c = Math.round(d3.interpolate(0, 0)(i / (10 - 1)));
  const a = d3.interpolate(minSolarDayOpacity, maxSolarDayOpacity)(i / (10 - 1));
  return `rgba(${c}, ${c}, ${c}, ${a})`;
});

const solarColor = d3.scaleLinear()
  .domain(solarDomain)
  .range(solarRange)
  .clamp(true);

// ** CO2
const maxCo2 = 800;

module.exports = {
  maxCo2,
  maxSolarDSWRF,
  solarColor,
  windColor,
};
