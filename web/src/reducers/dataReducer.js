const moment = require('moment');

const { modeOrder } = require('../helpers/constants');
const constructTopos = require('../helpers/topos');
const translation = require('../helpers/translation');

const exchangesConfig = require('../../../config/exchanges.json');
const zonesConfig = require('../../../config/zones.json');

// ** Prepare initial zone data
const zones = constructTopos();
Object.entries(zonesConfig).forEach((d) => {
  const [key, zoneConfig] = d;
  const zone = zones[key];
  if (!zone) {
    console.warn(`Zone ${key} from configuration is not found. Ignoring..`);
    return;
  }
  // copy attributes ("capacity", "contributors"...)
  zone.capacity = zoneConfig.capacity;
  zone.contributors = zoneConfig.contributors;
  zone.timezone = zoneConfig.timezone;
  zone.shortname = translation.getFullZoneName(key);
  zone.hasParser = (zoneConfig.parsers || {}).production !== undefined;
});
// Add id to each zone
Object.keys(zones).forEach((k) => { zones[k].countryCode = k; });

// ** Prepare initial exchange data
const exchanges = Object.assign({}, exchangesConfig);
Object.entries(exchanges).forEach((entry) => {
  const [key, value] = entry;
  value.countryCodes = key.split('->').sort();
  if (key.split('->')[0] !== value.countryCodes[0]) {
    console.warn(`Exchange sorted key pair ${key} is not sorted alphabetically`);
  }
});

const initialDataState = {
  // Here we will store data items
  grid: { zones, exchanges },
  histories: {},
  solar: null, // TODO(olc)
  wind: null, // TODO(olc)
};

module.exports = (state = initialDataState, action) => {
  switch (action.type) {
    case 'GRID_DATA': {
      // Create new grid object
      const newGrid = Object.assign({}, {
        zones: Object.assign({}, state.grid.zones),
        exchanges: Object.assign({}, state.grid.exchanges),
      });
      // Create new state
      const newState = Object.assign({}, state);
      newState.grid = newGrid;

      // Reset histories that expired
      newState.histories = Object.assign({}, state.histories);
      Object.keys(state.histories).forEach((k) => {
        const history = state.histories[k];
        const lastHistoryMoment = moment(history[history.length - 1].stateDatetime).utc();
        const stateMoment = moment(action.payload.datetime).utc();
        if (lastHistoryMoment.add(15, 'minutes').isBefore(stateMoment)) {
          delete newState.histories[k];
        }
      });

      // Set date
      newGrid.datetime = action.payload.datetime;

      // Reset all data we want to update (for instance, not maxCapacity)
      Object.keys(newGrid.zones).forEach((key) => {
        const zone = newGrid.zones[key];
        zone.co2intensity = undefined;
        zone.exchange = {};
        zone.production = {};
        zone.productionCo2Intensities = {};
        zone.productionCo2IntensitySources = {};
        zone.dischargeCo2Intensities = {};
        zone.dischargeCo2IntensitySources = {};
        zone.storage = {};
        zone.source = undefined;
      });
      Object.keys(newGrid.exchanges).forEach((key) => {
        newGrid.exchanges[key].netFlow = undefined;
      });

      // Populate with realtime country data
      Object.entries(action.payload.countries).forEach((entry) => {
        const [key, value] = entry;
        const zone = newGrid.zones[key];
        if (!zone) {
          console.warn(`${key} has no zone configuration.`);
          return;
        }
        // Assign data from payload
        Object.keys(value).forEach((k) => {
          // Warning: k takes all values, even those that are not meant
          // to be updated (like maxCapacity)
          zone[k] = value[k];
        });
        // Set date
        zone.datetime = action.payload.datetime;
        // Validate data
        if (!zone.production) return;
        modeOrder.forEach((mode) => {
          if (mode === 'other' || mode === 'unknown' || !zone.datetime) { return; }
          // Check missing values
          // if (country.production[mode] === undefined && country.storage[mode] === undefined)
          //    console.warn(`${key} is missing production or storage of ' + mode`);
          // Check validity of production
          if (zone.production[mode] !== undefined && zone.production[mode] < 0) {
            console.warn(`${key} has negative production of ${mode}`);
          }
          // Check load factors > 1
          if (zone.production[mode] !== undefined &&
            (zone.capacity || {})[mode] !== undefined &&
            zone.production[mode] > zone.capacity[mode]) {
            console.warn(`${key} produces more than its capacity of ${mode}`);
          }
        });
        if (!zone.exchange || !Object.keys(zone.exchange).length) {
          console.warn(`${key} is missing exchanges`);
        } 

      });

      // Populate exchange pairs for exchange layer
      Object.entries(action.payload.exchanges).forEach((entry) => {
        const [key, value] = entry;
        const exchange = newGrid.exchanges[key];
        if (!exchange || !exchange.lonlat) {
          console.warn(`Missing exchange configuration for ${key}`);
          return;
        }
        // Assign all data
        Object.keys(value).forEach((k) => {
          exchange[k] = value[k];
        });
      });

      // Debug
      console.log(newGrid.zones);

      return newState;
    }

    case 'HISTORY_DATA': {
      // Create new histories
      const newHistories = Object.assign({}, state.histories);

      const zoneHistory = action.payload.map((observation) => {
        const ret = Object.assign({}, observation);
        
        ret.hasParser = true;
        if (observation.exchange && Object.keys(observation.exchange).length
          && (!observation.production || !Object.keys(observation.production).length)) {
              // Exchange information is not shown in history observations without production data, as the percentages are incorrect
          ret.exchange = {};
        }

        return ret;
      });


      newHistories[action.zoneName] = zoneHistory;
      // Create new state
      const newState = Object.assign({}, state);
      newState.histories = newHistories;

      return newState;
    }

    default:
      return state;
  }
};
