// Production/imports-exports mode
const modeColor = {
  'solar': '#f27406',
  'wind': '#74cdb9',
  'hydro': '#2772b2',
  'hydro storage': '#0052cc',
  'battery': 'lightgray',
  'battery storage': 'lightgray',
  'biomass': '#166a57',
  'geothermal': 'yellow',
  'nuclear': '#AEB800',
  'gas': '#bb2f51',
  'coal': '#ac8c35',
  'oil': '#867d66',
  'unknown': '#ACACAC',
};
const modeOrder = [
  'nuclear',
  'geothermal',
  'biomass',
  'coal',
  'wind',
  'solar',
  'hydro',
  'hydro storage',
  'battery storage',
  'gas',
  'oil',
  'unknown',
];

const PRODUCTION_MODES = modeOrder.filter(d => d.indexOf('storage') === -1);
const OUTPUT_MODES = modeOrger.map(d => d.replace('storage','discharge'));
const STORAGE_MODES = modeOrder.filter(d => d.indexOf('storage') !== -1).map(d => d.replace(' storage', ''));

const LOW_CARBON_INFO_TOOLTIP_KEY = 'low-carbon-info';
const MAP_EXCHANGE_TOOLTIP_KEY = 'map-exchange';
const MAP_COUNTRY_TOOLTIP_KEY = 'map-country';

const CARBON_GRAPH_LAYER_KEY = MAP_COUNTRY_TOOLTIP_KEY;
const PRICES_GRAPH_LAYER_KEY = 'price';

const DEFAULT_FLAG_SIZE = 16;

module.exports = {
  modeColor,
  modeOrder,
  PRODUCTION_MODES,
  STORAGE_MODES,
  CARBON_GRAPH_LAYER_KEY,
  PRICES_GRAPH_LAYER_KEY,
  LOW_CARBON_INFO_TOOLTIP_KEY,
  MAP_EXCHANGE_TOOLTIP_KEY,
  MAP_COUNTRY_TOOLTIP_KEY,
  DEFAULT_FLAG_SIZE,
};
