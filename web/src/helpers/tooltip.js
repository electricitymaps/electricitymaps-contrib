const d3 = require('d3-selection');

const flags = require('../helpers/flags');
const translation = require('../helpers/translation');

const formatting = require('./formatting');

// Production
const FLAG_SIZE = 16;
module.exports.showProduction = function showProduction(tooltipInstance, mode, country, displayByEmissions, co2color, co2Colorbars) {
  const selector = tooltipInstance._selector;

  if (!country.productionCo2Intensities) { return; }
  if (co2Colorbars) co2Colorbars.forEach((d) => { d.currentMarker(co2intensity); });
  const tooltip = d3.select(selector);
  tooltip.selectAll('#mode').text(translation.translate(mode) || mode);

  let value = mode.indexOf('storage') !== -1 ?
    -1 * country.storage[mode.replace(' storage', '')] :
    country.production[mode];

  const isStorage = value < 0;

  var co2intensity = value < 0 ?
    undefined :
    mode.indexOf('storage') !== -1 ?
      country.dischargeCo2Intensities[mode.replace(' storage', '')] :
      country.productionCo2Intensities[mode];
  const co2intensitySource = value < 0 ?
    undefined :
    mode.indexOf('storage') !== -1 ?
      country.dischargeCo2IntensitySources[mode.replace(' storage', '')] :
      country.productionCo2IntensitySources[mode];

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
    Math.round(absValue / capacity * 100) : '?';
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

  const productionProportion = !isNull ? Math.round(absValue / domain * 100) : '?';
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
    .attr('src', flags.flagUri(country.countryCode, FLAG_SIZE));

  tooltipInstance.show();
};

// Exchange
module.exports.showExchange = function showExchange(tooltipInstance, key, country, displayByEmissions, co2color, co2Colorbars) {
  const selector = tooltipInstance._selector;
  var value = country.exchange[key];

  const isExport = value < 0;
  const co2intensity = country.exchangeCo2Intensities[key];
  const tooltip = d3.select(selector);

  const totalPositive = displayByEmissions ?
    (country.totalCo2Production + country.totalCo2Discharge + country.totalCo2Import) : // gCO2eq/h
    (country.totalProduction + country.totalDischarge + country.totalImport);

  const domain = totalPositive;
  const domainName = isExport ? translation.translate('electricityto') : translation.translate('electricityfrom');
  var value = displayByEmissions ? (value * 1000 * co2intensity) : value;
  const isNull = !isFinite(value) || value === undefined;

  tooltip.select('.production-visible')
    .style('display', displayByEmissions ? 'none' : undefined);

  const format = displayByEmissions ? formatting.formatCo2 : formatting.formatPower;

  const absFlow = Math.abs(value);
  const exchangeProportion = !isNull ? Math.round(absFlow / domain * 100.0) : '?';
  tooltip.select('#exchange-proportion').text(`${exchangeProportion} %`);
  tooltip.select('#exchange-proportion-detail').html(`${!isNull ? format(absFlow) : '?'
  } / ${
    !isNull ? format(domain) : '?'}`);
  tooltip.select('#domain-name').text(domainName);

  // Exchange
  const langString = isExport ?
    displayByEmissions ? 'emissionsExportedTo' : 'electricityExportedTo' :
    displayByEmissions ? 'emissionsImportedFrom' : 'electricityImportedFrom';

  tooltip.select('#line1')
    .html(formatting.co2Sub(translation.translate(
      langString,
      exchangeProportion,
      translation.getFullZoneName(country.countryCode),
      translation.getFullZoneName(key),
    )));
  tooltip.select('#line1 #country-flag')
    .classed('flag', true)
    .attr('src', flags.flagUri(country.countryCode, FLAG_SIZE));
  tooltip.select('#line1 #country-exchange-flag')
    .classed('flag', true)
    .attr('src', flags.flagUri(key, FLAG_SIZE));


  // Capacity
  const absCapacity = Math.abs(((country.exchangeCapacities || {})[key] || [])[isExport ? 0 : 1]);
  const hasCapacity = absCapacity !== undefined && isFinite(absCapacity);
  const capacityFactor = hasCapacity && Math.round(absFlow / absCapacity * 100) || '?';
  tooltip.select('#capacity-factor').text(`${capacityFactor} %`);
  tooltip.select('#capacity-factor-detail').html(`${format(absFlow) || '?'} ` +
    ` / ${
      hasCapacity && format(absCapacity) || '?'}`);


  // Carbon intensity
  if (co2Colorbars) co2Colorbars.forEach((d) => { d.currentMarker(co2intensity); });
  const o = value < 0 ? country.countryCode : key;
  tooltip.selectAll('.country-exchange-source-flag')
    .attr('src', flags.flagUri(o, FLAG_SIZE));
  tooltip.select('.emission-rect')
    .style('background-color', co2intensity ? co2color(co2intensity) : 'gray');
  tooltip.select('.emission-intensity')
    .text(Math.round(co2intensity) || '?');
  tooltip.select('.country-exchange-source-name')
    .text(translation.getFullZoneName(o))
    .style('font-weight', 'bold');

  tooltipInstance.show();
};

module.exports.showMapCountry = function showMapCountry(tooltipInstance, countryData, co2color, co2Colorbars, lowCarbonGauge, renewableGauge) {
  if (countryData.co2intensity && co2Colorbars) {
    co2Colorbars.forEach((c) => { c.currentMarker(countryData.co2intensity); });
  }
  const tooltip = d3.select(tooltipInstance._selector);
  tooltip.select('#country-flag')
    .attr('src', flags.flagUri(countryData.countryCode, 16));
  tooltip.select('#country-name')
    .text(translation.getFullZoneName(countryData.countryCode))
    .style('font-weight', 'bold');

  if (countryData.hasParser && lowCarbonGauge && renewableGauge) {
    tooltip.select('.emission-rect')
      .style('background-color', countryData.co2intensity ? co2color(countryData.co2intensity) : 'gray');
    tooltip.select('.country-emission-intensity')
      .text(Math.round(countryData.co2intensity) || '?');

    const hasFossilFuelData = countryData.fossilFuelRatio !== undefined || countryData.fossilFuelRatio !== null;
    if (hasFossilFuelData) {
      const fossilFuelPercent = countryData.fossilFuelRatio * 100;
      lowCarbonGauge.setPercentage(Math.round(100 - fossilFuelPercent));
      tooltip.select('.lowcarbon-percentage').text(Math.round(100 - fossilFuelPercent));
    } else {
      tooltip.select('.lowcarbon-percentage').text('?');
    }
    const hasRenewableData = countryData.renewableRatio !== undefined || countryData.renewableRatio !== null;
    if (hasRenewableData) {
      const renewablePercent = countryData.renewableRatio * 100;
      renewableGauge.setPercentage(Math.round(renewablePercent));
      tooltip.select('.renewable-percentage').text(Math.round(renewablePercent));
    } else {
      tooltip.select('.renewable-percentage').text('?');
    }
  }
  tooltip.select('.zone-details').style('display', countryData.hasParser && countryData.co2intensity ? 'block' : 'none');
  tooltip.select('.temporary-outage-text').style('display', countryData.hasParser && !countryData.co2intensity ? 'block' : 'none');
  tooltip.select('.no-parser-text').style('display', !countryData.hasParser ? 'block' : 'none');

  tooltipInstance.show();
};

module.exports.showMapExchange = function showMapExchange(tooltipInstance, exchangeData, co2color, co2Colorbars) {
  const tooltip = d3.select(tooltipInstance._selector);
  if (exchangeData.co2intensity && co2Colorbars) { co2Colorbars.forEach((c) => { c.currentMarker(exchangeData.co2intensity); }); }
  tooltip.select('.emission-rect')
    .style('background-color', exchangeData.co2intensity ? co2color(exchangeData.co2intensity) : 'gray');
  const i = exchangeData.netFlow > 0 ? 0 : 1;
  const ctrFrom = exchangeData.countryCodes[i];
  tooltip.selectAll('span#from')
    .text(translation.getFullZoneName(ctrFrom));
  const ctrTo = exchangeData.countryCodes[(i + 1) % 2];
  tooltip.select('span#to')
    .text(translation.getFullZoneName(ctrTo));
  tooltip.select('span#flow')
    .text(Math.abs(Math.round(exchangeData.netFlow)));
  tooltip.select('img.flag.from')
    .attr('src', flags.flagUri(exchangeData.countryCodes[i], 16));
  tooltip.select('img.flag.to')
    .attr('src', flags.flagUri(exchangeData.countryCodes[(i + 1) % 2], 16));
  tooltip.select('.country-emission-intensity')
    .text(Math.round(exchangeData.co2intensity) || '?');

  tooltipInstance.show();
};
