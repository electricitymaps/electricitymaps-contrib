/* eslint-disable */
// TODO: remove once refactored

const d3 = require('d3-selection');
const getSymbolFromCurrency = require('currency-symbol-map');

const flags = require('../helpers/flags');
const translation = require('../helpers/translation');

const formatting = require('./formatting');
const { dispatch, dispatchApplication } = require('../store');

// Production
module.exports.showProduction = function showProduction(
  tooltipInstance, mode, country, displayByEmissions, co2color, co2Colorbars, electricityMixMode)
{
  const selector = tooltipInstance._selector;

  if (!country || !country.productionCo2Intensities) { return; }
  const tooltip = d3.select(selector);
  tooltip.selectAll('#mode').text(translation.translate(mode) || mode);

  let value = mode.indexOf('storage') !== -1 ?
    -1 * country.storage[mode.replace(' storage', '')] :
    country.production[mode];

  const isStorage = value < 0;

  const co2intensity = value < 0 ?
    undefined :
    mode.indexOf('storage') !== -1 ?
      country.dischargeCo2Intensities[mode.replace(' storage', '')] :
      country.productionCo2Intensities[mode];
  const co2intensitySource = value < 0 ?
    undefined :
    mode.indexOf('storage') !== -1 ?
      country.dischargeCo2IntensitySources[mode.replace(' storage', '')] :
      country.productionCo2IntensitySources[mode];

  dispatch({ type: 'SET_CO2_COLORBAR_MARKER', payload: { marker: co2intensity } });

  tooltip.select('.emission-rect')
    .style('background-color', co2intensity ? co2color(co2intensity) : 'gray');
  tooltip.select('.emission-intensity')
    .text(Math.round(co2intensity) || '?');
  tooltip.select('.emission-source')
    .text(co2intensitySource || '?');

  if (displayByEmissions) {
    if (!isStorage) {
      value *= co2intensity * 1000.0; // MW * gCO2/kWh * 1000 --> gCO2/h
    }
  }

  const absValue = Math.abs(value);

  tooltip.select('.production-visible')
    .style('display', displayByEmissions ? 'none' : undefined);

  const format = displayByEmissions ? formatting.formatCo2 : formatting.formatPower;

  // capacity
  const capacity = (country.capacity || {})[mode];
  const hasCapacity = capacity !== undefined && capacity >= (country.production[mode] || 0);
  const capacityFactor = (hasCapacity && absValue != null) ?
    Math.round(absValue / capacity * 10000) / 100 : '?';
  tooltip.select('#capacity-factor').text(`${capacityFactor} %`);
  tooltip.select('#capacity-factor-detail').html(`${format(absValue) || '?'} ` +
    ` / ${
      hasCapacity && format(capacity) || '?'}`);

  const totalPositive = displayByEmissions ?
    (country.totalCo2Production + country.totalCo2Discharge + country.totalCo2Import) : // gCO2eq/h
    (country.totalProduction + country.totalDischarge + country.totalImport);

  const domain = totalPositive;
  const domainName = translation.translate(mode);
  const isNull = !isFinite(absValue) || absValue == undefined;

  const productionProportion = !isNull ? Math.round(absValue / domain * 10000) / 100 : '?';
  tooltip.select('#production-proportion-detail').html(`${!isNull ? format(absValue) : '?'} ` +
    ` / ${
      !isNull ? format(domain) : '?'}`);

  const langString = isStorage ?
    displayByEmissions ? 'emissionsStoredUsing' : 'electricityStoredUsing' :
    displayByEmissions ? 'emissionsComeFrom' : 'electricityComesFrom';
  tooltip.select('#line1')
    .html(formatting.co2Sub(translation.translate(
      langString,
      productionProportion,
      translation.getFullZoneName(country.countryCode),
      domainName,
    )))
    .select('#country-flag')
    .classed('flag', true)
    .attr('src', flags.flagUri(country.countryCode));

  tooltipInstance.show();
};
