import moment from 'moment';

import { modeOrder } from './constants';

const d3 = Object.assign(
  {},
  require('d3-collection'),
);

// TODO: Refactor this function to make it more readable
export const prepareGraphData = (data, displayByEmissions, electricityMixMode, formattingFactor) => {
  const exchangeKeysSet = d3.set();
  const graphData = data.map((d) => {
    const obj = {
      datetime: moment(d.stateDatetime).toDate(),
    };
    // Add production
    modeOrder.forEach((k) => {
      const isStorage = k.indexOf('storage') !== -1;
      const value = isStorage
        ? -1 * Math.min(0, (d.storage || {})[k.replace(' storage', '')])
        : (d.production || {})[k];
      // in GW or MW
      obj[k] = value / formattingFactor;
      if (Number.isFinite(value) && displayByEmissions && obj[k] != null) {
        // in tCO2eq/min
        if (isStorage && obj[k] >= 0) {
          obj[k] *= d.dischargeCo2Intensities[k.replace(' storage', '')] / 1e3 / 60.0;
        } else {
          obj[k] *= d.productionCo2Intensities[k] / 1e3 / 60.0;
        }
      }
    });
    if (electricityMixMode === 'consumption') {
      // Add exchange
      d3.entries(d.exchange).forEach((o) => {
        exchangeKeysSet.add(o.key);
        // in GW or MW
        obj[o.key] = Math.max(0, o.value / formattingFactor);
        if (Number.isFinite(o.value) && displayByEmissions && obj[o.key] != null) {
          // in tCO2eq/min
          obj[o.key] *= d.exchangeCo2Intensities[o.key] / 1e3 / 60.0;
        }
      });
    }
    // Keep a pointer to original data
    obj._countryData = d;
    return obj;
  });
  const datetimes = graphData.map(d => d.datetime);
  const exchangeKeys = exchangeKeysSet.values();
  return { datetimes, exchangeKeys, graphData };
};
