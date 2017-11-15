'use strict'

var d3 = require('d3');
var getSymbolFromCurrency = require('currency-symbol-map').getSymbolFromCurrency;

var flags = require('../flags');
var translation = require('../translation');

var formatting = require('./formatting')

// Production
var FLAG_SIZE = 16;
module.exports.showProduction = function(tooltipInstance, mode, country, displayByEmissions, co2color, co2Colorbars) {
    var selector = tooltipInstance._selector;

    if (!country.productionCo2Intensities) { return; }
    if (co2Colorbars) co2Colorbars.forEach(function(d) { d.currentMarker(co2intensity) });
    var tooltip = d3.select(selector);
    tooltip.selectAll('#mode').text(translation.translate(mode) || mode);

    var value = mode.indexOf('storage') != -1 ?
        -1 * country.storage[mode.replace(' storage', '')] :
        country.production[mode]

    var isStorage = value < 0

    var co2intensity = value < 0 ?
        undefined :
        mode.indexOf('storage') != -1 ?
            country.dischargeCo2Intensities[mode.replace(' storage', '')] :
            country.productionCo2Intensities[mode];
    var co2intensitySource = value < 0 ?
        undefined :
        mode.indexOf('storage') != -1 ?
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

    var absValue = Math.abs(value)

    tooltip.select('.production-visible')
        .style('display', displayByEmissions ? 'none' : undefined);

    var format = displayByEmissions ? formatting.formatCo2 : formatting.formatPower;

    // capacity
    var capacity = (country.capacity || {})[mode]
    var hasCapacity = capacity !== undefined && capacity >= (country.production[mode] || 0);
    var capacityFactor = hasCapacity && Math.round(absValue / capacity * 100) || '?';
    tooltip.select('#capacity-factor').text(capacityFactor + ' %');
    tooltip.select('#capacity-factor-detail').html(
        (format(absValue) || '?') + ' ' +
        ' / ' +
        (hasCapacity && format(capacity) || '?'));

    var totalPositive = displayByEmissions ?
        (country.totalCo2Production + country.totalCo2Discharge + country.totalCo2Import) : // gCO2eq/h
        (country.totalProduction + country.totalDischarge + country.totalImport);

    var domain = totalPositive;
    var domainName = translation.translate(mode);
    var isNull = !isFinite(absValue) || absValue == undefined;

    var productionProportion = !isNull ? Math.round(absValue / domain * 100) : '?';
    tooltip.select('#production-proportion-detail').html(
        (!isNull ? format(absValue) : '?') + ' ' +
        ' / ' +
        (!isNull ? format(domain) : '?'));

    var langString = isStorage ?
            displayByEmissions ? 'emissionsStoredUsing' : 'electricityStoredUsing' :
            displayByEmissions ? 'emissionsComeFrom' : 'electricityComesFrom';
    tooltip.select('#line1')
        .html(formatting.co2Sub(
            translation.translate(
                langString,
                productionProportion,
                translation.translate(
                    'zoneShortName.' + country.countryCode) || country.countryCode,
                domainName)))
        .select('#country-flag')
            .classed('flag', true)
            .attr('src', flags.flagUri(country.countryCode, FLAG_SIZE));

    tooltipInstance.show()
}

// Exchange
module.exports.showExchange = function(tooltipInstance, key, country, displayByEmissions, co2color, co2Colorbars) {
    var selector = tooltipInstance._selector;
    var value = country.exchange[key];

    var isExport = value < 0;
    var co2intensity = country.exchangeCo2Intensities[key];
    var tooltip = d3.select(selector);

    var totalPositive = displayByEmissions ?
        (country.totalCo2Production + country.totalCo2Discharge + country.totalCo2Import) : // gCO2eq/h
        (country.totalProduction + country.totalDischarge + country.totalImport);

    var domain = totalPositive;
    var domainName = isExport ? translation.translate('electricityto') : translation.translate('electricityfrom');
    var value = displayByEmissions ? (value * 1000 * co2intensity) : value;
    var isNull = !isFinite(value) || value == undefined;

    tooltip.select('.production-visible')
        .style('display', displayByEmissions ? 'none' : undefined);

    var format = displayByEmissions ? formatting.formatCo2 : formatting.formatPower;

    var absFlow = Math.abs(value);
    var exchangeProportion = !isNull ? Math.round(absFlow / domain * 100.0) : '?';
    tooltip.select('#exchange-proportion').text(exchangeProportion + ' %');
    tooltip.select('#exchange-proportion-detail').html(
        (!isNull ? format(absFlow) : '?') +
        ' / ' +
        (!isNull ? format(domain) : '?'));
    tooltip.select('#domain-name').text(domainName);

    // Exchange
    var langString = isExport ?
            displayByEmissions ? 'emissionsExportedTo' : 'electricityExportedTo' :
            displayByEmissions ? 'emissionsImportedFrom' : 'electricityImportedFrom';

    tooltip.select('#line1')
        .html(formatting.co2Sub(translation.translate(langString,
            exchangeProportion,
            translation.translate('zoneShortName.' + country.countryCode) || country.countryCode,
            translation.translate('zoneShortName.' + key) || key)));
    tooltip.select('#line1 #country-flag')
            .classed('flag', true)
            .attr('src', flags.flagUri(country.countryCode, FLAG_SIZE));
    tooltip.select('#line1 #country-exchange-flag')
            .classed('flag', true)
            .attr('src', flags.flagUri(key, FLAG_SIZE));


    // Capacity
    var absCapacity = Math.abs(
        ((country.exchangeCapacities || {})[key] || [])[isExport ? 0 : 1]);
    var hasCapacity = absCapacity !== undefined && isFinite(absCapacity);
    var capacityFactor = hasCapacity && Math.round(absFlow / absCapacity * 100) || '?';
    tooltip.select('#capacity-factor').text(capacityFactor + ' %');
    tooltip.select('#capacity-factor-detail').html(
        (format(absFlow) || '?') + ' ' +
        ' / ' +
        (hasCapacity && format(absCapacity) || '?'));


    // Carbon intensity
    if (co2Colorbars) co2Colorbars.forEach(function(d) { d.currentMarker(co2intensity) });
    var o = value < 0 ? country.countryCode : key;
    tooltip.selectAll('.country-exchange-source-flag')
        .attr('src', flags.flagUri(o, FLAG_SIZE));
    tooltip.select('.emission-rect')
        .style('background-color', co2intensity ? co2color(co2intensity) : 'gray');
    tooltip.select('.emission-intensity')
        .text(Math.round(co2intensity) || '?');
    tooltip.select('.country-exchange-source-name')
        .text(translation.translate('zoneShortName.' + o) || o)
        .style('font-weight', 'bold');

    tooltipInstance.show()
}

module.exports.showMapCountry = function(tooltipInstance, countryData, co2color, co2Colorbars) {
    if (countryData.co2intensity && co2Colorbars)
        co2Colorbars.forEach(function(c) { c.currentMarker(countryData.co2intensity) });
    var tooltip = d3.select(tooltipInstance._selector);
    tooltip.select('#country-flag')
        .attr('src', flags.flagUri(countryData.countryCode, 16));
    tooltip.select('#country-name')
        .text(translation.translate('zoneShortName.' + countryData.countryCode) || countryData.countryCode)
        .style('font-weight', 'bold');
    tooltip.select('.emission-rect')
        .style('background-color', countryData.co2intensity ? co2color(countryData.co2intensity) : 'gray');
    tooltip.select('.country-emission-intensity')
        .text(Math.round(countryData.co2intensity) || '?');

    var priceData = countryData.price || {};
    var hasPrice = priceData.value != null;
    tooltip.select('.country-spot-price')
        .text(hasPrice ? Math.round(priceData.value) : '?')
        .style('color', (priceData.value || 0) < 0 ? 'red' : undefined);
    tooltip.select('.country-spot-price-currency')
        .text(getSymbolFromCurrency(priceData.currency) || priceData.currency || '?')
    var hasFossilFuelData = countryData.fossilFuelRatio != null;
    var fossilFuelPercent = countryData.fossilFuelRatio * 100;
    tooltip.select('.lowcarbon-percentage')
        .text(hasFossilFuelData ? Math.round(100 - fossilFuelPercent) : '?');
    var hasRenewableData = countryData.renewableRatio != null;
    var renewablePercent = countryData.renewableRatio * 100;
    tooltip.select('.renewable-percentage')
        .text(hasRenewableData ? Math.round(renewablePercent) : '?');

    tooltipInstance.show()
}

module.exports.showMapExchange = function(tooltipInstance, exchangeData, co2color, co2Colorbars) {
    var tooltip = d3.select(tooltipInstance._selector)
    if (exchangeData.co2intensity && co2Colorbars)
        co2Colorbars.forEach(function(c) { c.currentMarker(exchangeData.co2intensity) });
    var tooltip = d3.select('#exchange-tooltip');
    tooltip.select('.emission-rect')
        .style('background-color', exchangeData.co2intensity ? co2color(exchangeData.co2intensity) : 'gray');
    var i = exchangeData.netFlow > 0 ? 0 : 1;
    var ctrFrom = exchangeData.countryCodes[i];
    tooltip.selectAll('span#from')
        .text(translation.translate('zoneShortName.' + ctrFrom) || ctrFrom);
    var ctrTo = exchangeData.countryCodes[(i + 1) % 2];
    tooltip.select('span#to')
        .text(translation.translate('zoneShortName.' + ctrTo) || ctrTo);
    tooltip.select('span#flow')
        .text(Math.abs(Math.round(exchangeData.netFlow)));
    tooltip.select('img.flag.from')
        .attr('src', flags.flagUri(exchangeData.countryCodes[i], 16));
    tooltip.select('img.flag.to')
        .attr('src', flags.flagUri(exchangeData.countryCodes[(i + 1) % 2], 16));
    tooltip.select('.country-emission-intensity')
        .text(Math.round(exchangeData.co2intensity) || '?');

    tooltipInstance.show()
}
