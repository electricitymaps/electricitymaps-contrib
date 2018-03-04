// Production/imports-exports mode
const modeColor = {
  'solar': '#f27406',
  'wind': '#74cdb9',
  'hydro': '#2772b2',
  'hydro storage': '#0052cc',
  'battery': 'lightgray',
  'biomass': '#166a57',
  'geothermal': 'yellow',
  'nuclear': '#AEB800',
  'gas': '#bb2f51',
  'coal': '#ac8c35',
  'oil': '#867d66',
  'unknown': 'lightgray',
};
const modeOrder = [
  'solar',
  'wind',
  'hydro',
  'hydro storage',
  'battery storage',
  'geothermal',
  'biomass',
  'nuclear',
  'gas',
  'coal',
  'oil',
  'unknown',
];

module.exports = {
  modeColor,
  modeOrder,
};
