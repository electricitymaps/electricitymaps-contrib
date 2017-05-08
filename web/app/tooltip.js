var d3 = require('d3');
var flags = require('./flags');
var lang = require('json-loader!./configs/lang.json')[locale];
var utils = require('./utils');

var FLAG_SIZE = 16;

// Create power formatting
function formatPower(d, numDigits) {
    // Assume MW input
    if (d == null || d == NaN) return d;
    if (numDigits == null) numDigits = 3;
    return d3.format('.' + numDigits + 's')(d * 1e6) + 'W';
}
function formatCo2(d, numDigits) {
    // Assume gCO2 / h input
    d /= 60; // Convert to gCO2 / min
    d /= 1e6; // Convert to tCO2 / min
    if (d == null || d == NaN) return d;
    if (numDigits == null) numDigits = 3;
    if (d >= 1) // a ton or more
        return d3.format('.' + numDigits + 's')(d) + 't of CO2eq per minute';
    else
        return d3.format('.' + numDigits + 's')(d * 1e6) + 'g of CO2eq per minute';
}

function placeTooltip(selector, d3Event) {
    var tooltip = d3.select(selector);
    var w = tooltip.node().getBoundingClientRect().width;
    var h = tooltip.node().getBoundingClientRect().height;
    var margin = 7;
    var screenWidth = window.innerWidth;
    // On very small screens
    if (w > screenWidth) {
        tooltip
            .style('width', '100%');
    }
    else {
        var x = 0;
        if (w > screenWidth / 2 - 5) {
            // Tooltip won't fit on any side, so don't translate x
            x = 0.5 * (screenWidth - w);
        } else {
            x = d3Event.layerX + margin;
            if (screenWidth - x <= w) {
                x = d3Event.layerX - w - margin;
            }
        }
        var y = d3Event.layerY - h - margin; if (y <= margin) y = d3Event.layerY + margin;
        tooltip
            .style('transform',
                'translate(' + x + 'px' + ',' + y + 'px' + ')');
    }
}

function Tooltip(countryTable, countries) {
    var that = this;
    // ** Country table
    countryTable
        .onExchangeMouseOver(function (d, country, displayByEmissions) {
            var isExport = d.value < 0;
            var co2intensity = country.exchangeCo2Intensities[d.key];
            var tooltip = d3.select('#countrypanel-exchange-tooltip');
            tooltip.style('display', 'inline');

            var totalPositive = displayByEmissions ?
                (country.totalCo2Production + country.totalCo2Import) :
                (country.totalProduction + country.totalImport);

            var domain = totalPositive;
            var domainName = isExport ? lang['electricityto'] : lang['electricityfrom'];
            var value = displayByEmissions ? (d.value * 1000 * co2intensity) : d.value;
            var isNull = !isFinite(value) || value == undefined;

            tooltip.select('.production-visible')
                .style('display', displayByEmissions ? 'none' : undefined);

            var format = displayByEmissions ? formatCo2 : formatPower;

            var absFlow = Math.abs(value);
            var exchangeProportion = !isNull ? Math.round(absFlow / domain * 100) : '?';
            tooltip.select('#exchange-proportion').text(exchangeProportion + ' %');
            tooltip.select('#exchange-proportion-detail').text(
                (!isNull ? format(absFlow) : '?') + ' ' +
                ' / ' + 
                (!isNull ? format(domain) : '?'));
            tooltip.select('#domain-name').text(domainName);

            // Exchange
            var langString = isExport ?
                lang[displayByEmissions ? 'emissionsExportedTo' : 'electricityExportedTo'] :
                lang[displayByEmissions ? 'emissionsImportedFrom' : 'electricityImportedFrom'];

            tooltip.select('#line1')
                .html(utils.stringFormat(
                    langString,
                    exchangeProportion,
                    lang.zoneShortName[country.countryCode] || country.countryCode,
                    lang.zoneShortName[d.key] || d.key));
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
            tooltip.select('#capacity-factor-detail').text(
                (format(absFlow) || '?') + ' ' +
                ' / ' + 
                (hasCapacity && format(absCapacity) || '?'));


            // Carbon intensity
            if (that.co2Colorbar()) that.co2Colorbar().currentMarker(co2intensity);
            var o = d.value < 0 ? country.countryCode : d.key;
            tooltip.selectAll('.country-exchange-source-flag')
                .attr('src', flags.flagUri(o, FLAG_SIZE));
            tooltip.select('.emission-rect')
                .style('background-color', co2intensity ? that.co2color()(co2intensity) : 'gray');
            tooltip.select('.emission-intensity')
                .text(Math.round(co2intensity) || '?');
            tooltip.select('.country-exchange-source-name')
                .text(lang.zoneShortName[o] || o)
                .style('font-weight', 'bold');
        })
        .onExchangeMouseOut(function (d) {
            if (that.co2Colorbar()) that.co2Colorbar().currentMarker(undefined);
            d3.select('#countrypanel-exchange-tooltip')
                .style('display', 'none');
        })
        .onExchangeMouseMove(function(d) {
            placeTooltip('#countrypanel-exchange-tooltip', d3.event);
        })
        .onProductionMouseOver(function (d, country, displayByEmissions) {

            var co2intensity = country.productionCo2Intensities[d.mode];
            var co2intensitySource = country.productionCo2IntensitySources[d.mode];
            if (that.co2Colorbar()) that.co2Colorbar().currentMarker(co2intensity);
            var tooltip = d3.select('#countrypanel-production-tooltip');
            tooltip.style('display', 'inline');
            tooltip.selectAll('#mode').text(d.text || d.mode);
            tooltip.select('.emission-rect')
                .style('background-color', co2intensity ? that.co2color()(co2intensity) : 'gray');
            tooltip.select('.emission-intensity')
                .text(Math.round(co2intensity) || '?');
            tooltip.select('.emission-source')
                .text(co2intensitySource || '?');
            var value = displayByEmissions ?
                (d.isStorage ? 0 : (d.production * co2intensity * 1000)) :
                (d.isStorage ? d.storage : d.production);

            tooltip.select('.production-visible')
                .style('display', displayByEmissions ? 'none' : undefined);

            var format = displayByEmissions ? formatCo2 : formatPower;

            // Capacity
            var hasCapacity = d.capacity !== undefined && d.capacity >= (d.production || 0);
            var capacityFactor = hasCapacity && Math.round(value / d.capacity * 100) || '?';
            tooltip.select('#capacity-factor').text(capacityFactor + ' %');
            tooltip.select('#capacity-factor-detail').text(
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
            tooltip.select('#production-proportion-detail').text(
                (!isNull ? format(value) : '?') + ' ' +
                ' / ' + 
                (!isNull ? format(domain) : '?'));

            var langString = d.isStorage ?
                lang[displayByEmissions ? 'emissionsStoredUsing' : 'electricityStoredUsing'] :
                lang[displayByEmissions ? 'emissionsComeFrom' : 'electricityComesFrom'];
            tooltip.select('#line1')
                .html(utils.stringFormat(
                    langString,
                    productionProportion,
                    lang.zoneShortName[country.countryCode] || country.countryCode,
                    domainName))
                .select('#country-flag')
                    .classed('flag', true)
                    .attr('src', flags.flagUri(country.countryCode, FLAG_SIZE));
        })
        .onProductionMouseMove(function(d) {
            placeTooltip('#countrypanel-production-tooltip', d3.event);
        })
        .onProductionMouseOut(function (d) {
            if (that.co2Colorbar()) that.co2Colorbar().currentMarker(undefined);
            d3.select('#countrypanel-production-tooltip')
                .style('display', 'none');
        });
    return this;
}


Tooltip.prototype.co2color = function(arg) {
    if (!arg) return this._co2color;
    else this._co2color = arg;
    return this;
};


Tooltip.prototype.co2Colorbar = function(arg) {
    if (!arg) return this._co2Colorbar;
    else this._co2Colorbar = arg;
    return this;
};

module.exports = Tooltip;
