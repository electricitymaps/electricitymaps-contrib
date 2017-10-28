'use strict'

var d3 = require('d3');

var flags = require('../flags');
var translation = require('../translation');

var formatting = require('./formatting')

// Production
var FLAG_SIZE = 16;
module.exports.showProduction = function(tooltipInstance, d, country, displayByEmissions, co2color, co2Colorbars) {
    var selector = tooltipInstance._selector;

    if (!country.productionCo2Intensities) { return; }
    var co2intensity = country.productionCo2Intensities[d.mode];
    var co2intensitySource = country.productionCo2IntensitySources[d.mode];
    if (co2Colorbars) co2Colorbars.forEach(function(d) { d.currentMarker(co2intensity) });
    var tooltip = d3.select(selector);
    tooltip.style('display', 'inline');
    tooltip.selectAll('#mode').text(d.text || d.mode);
    tooltip.select('.emission-rect')
        .style('background-color', co2intensity ? co2color(co2intensity) : 'gray');
    tooltip.select('.emission-intensity')
        .text(Math.round(co2intensity) || '?');
    tooltip.select('.emission-source')
        .text(co2intensitySource || '?');
    var value = displayByEmissions ?
        (d.isStorage ? 0 : (d.production * co2intensity * 1000)) :
        (d.isStorage ? d.storage : d.production);

    tooltip.select('.production-visible')
        .style('display', displayByEmissions ? 'none' : undefined);

    var format = displayByEmissions ? formatting.formatCo2 : formatting.formatPower;

    // Capacity
    var hasCapacity = d.capacity !== undefined && d.capacity >= (d.production || 0);
    var capacityFactor = hasCapacity && Math.round(value / d.capacity * 100) || '?';
    tooltip.select('#capacity-factor').text(capacityFactor + ' %');
    tooltip.select('#capacity-factor-detail').html(
        (format(value) || '?') + ' ' +
        ' / ' + 
        (hasCapacity && format(d.capacity) || '?'));

    var totalPositive = displayByEmissions ?
        (country.totalCo2Production + country.totalCo2Import) :
        (country.totalProduction + country.totalImport);

    var domain = totalPositive;
    var domainName = d.text || d.mode;
    var isNull = !isFinite(value) || value == undefined;

    var productionProportion = !isNull ? Math.round(value / domain * 100) : '?';
    tooltip.select('#production-proportion-detail').html(
        (!isNull ? format(value) : '?') + ' ' +
        ' / ' + 
        (!isNull ? format(domain) : '?'));

    var langString = d.isStorage ?
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
module.exports.showExchange = function(tooltipInstance, d, country, displayByEmissions, co2color, co2Colorbars) {
    var selector = tooltipInstance._selector;

    var isExport = d.value < 0;
    var co2intensity = country.exchangeCo2Intensities[d.key];
    var tooltip = d3.select(selector);

    var totalPositive = displayByEmissions ?
        (country.totalCo2Production + country.totalCo2Import) :
        (country.totalProduction + country.totalImport);

    var domain = totalPositive;
    var domainName = isExport ? translation.translate('electricityto') : translation.translate('electricityfrom');
    var value = displayByEmissions ? (d.value * 1000 * co2intensity) : d.value;
    var isNull = !isFinite(value) || value == undefined;

    tooltip.select('.production-visible')
        .style('display', displayByEmissions ? 'none' : undefined);

    var format = displayByEmissions ? formatting.formatCo2 : formatting.formatPower;

    var absFlow = Math.abs(value);
    var exchangeProportion = !isNull ? Math.round(absFlow / domain * 100) : '?';
    tooltip.select('#exchange-proportion').text(exchangeProportion + ' %');
    tooltip.select('#exchange-proportion-detail').html(
        (!isNull ? format(absFlow) : '?') + ' ' +
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
            translation.translate('zoneShortName.' + d.key) || d.key)));
    tooltip.select('#line1 #country-flag')
            .classed('flag', true)
            .attr('src', flags.flagUri(country.countryCode, FLAG_SIZE));
    tooltip.select('#line1 #country-exchange-flag')
            .classed('flag', true)
            .attr('src', flags.flagUri(d.key, FLAG_SIZE));


    // Capacity
    var absCapacity = Math.abs(
        ((country.exchangeCapacities || {})[d.key] || [])[isExport ? 0 : 1]);
    var hasCapacity = absCapacity !== undefined && isFinite(absCapacity);
    var capacityFactor = hasCapacity && Math.round(absFlow / absCapacity * 100) || '?';
    tooltip.select('#capacity-factor').text(capacityFactor + ' %');
    tooltip.select('#capacity-factor-detail').html(
        (format(absFlow) || '?') + ' ' +
        ' / ' + 
        (hasCapacity && format(absCapacity) || '?'));


    // Carbon intensity
    if (co2Colorbars) co2Colorbars.forEach(function(d) { d.currentMarker(co2intensity) });
    var o = d.value < 0 ? country.countryCode : d.key;
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

