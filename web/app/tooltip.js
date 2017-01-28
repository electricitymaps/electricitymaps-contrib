exports = module.exports = {};

var d3 = require('d3');

// Create power formatting
function formatPower(d, numDigits) {
    // Assume MW input
    if (d == null || d == NaN) return d;
    if (numDigits == null) numDigits = 3;
    return d3.format('.' + numDigits + 's')(d * 1e6) + 'W';
}

// ** Country table
exports.setupCountryTable = function (countryTable, countries, co2Colorbar, co2color) {
    countryTable
        .onExchangeMouseOver(function (d, countryCode) {
            var isExport = d.value < 0;
            var o = d.value < 0 ? countryCode : d.key;
            var co2intensity = countries[o].co2intensity;
            co2Colorbar.currentMarker(co2intensity);
            var tooltip = d3.select('#countrypanel-exchange-tooltip');
            tooltip.style('display', 'inline');
            tooltip.select('#label').text(isExport ? 'export to' : 'import from');
            tooltip.select('#country-code').text(d.key);
            tooltip.select('.emission-rect')
                .style('background-color', co2intensity ? co2color(co2intensity) : 'gray');
            tooltip.select('.emission-intensity')
                .text(Math.round(co2intensity) || '?');
            tooltip.select('i#country-flag')
                .attr('class', 'flag-icon flag-icon-' + d.key.toLowerCase());
            tooltip.select('#import-detail').style('display', 
                isExport ? 'none' : undefined);
            tooltip.select('#export-detail').style('display', 
                isExport ? undefined : 'none');
            var totalProduction = countries[countryCode].totalProduction;
            var absFlow = Math.abs(d.value);
            if (isExport) {
                // Proportion compared to production
                var exportProportion = Math.round(absFlow / totalProduction * 100) || '?';
                tooltip.select('#export-proportion-production').text(exportProportion + ' %');
                tooltip.select('#export-proportion-production-detail').text(
                    (formatPower(absFlow) || '?') + ' ' +
                    ' / ' + 
                    (formatPower(totalProduction) || '?'));
            } else {
                // Proportion compared to consumption
                var netExchange = countries[countryCode].totalNetExchange;
                var totalConsumption = totalProduction + netExchange;
                var importProportion = Math.round(absFlow / totalConsumption * 100) || '?';
                tooltip.select('#import-proportion-consumption').text(importProportion + ' %');
                tooltip.select('#import-proportion-consumption-detail').text(
                    (formatPower(absFlow) || '?') + ' ' +
                    ' / ' + 
                    (formatPower(totalConsumption) || '?'));
            }
            tooltip.selectAll('.country-code').text(countryCode);
        })
        .onExchangeMouseOut(function (d) {
            co2Colorbar.currentMarker(undefined);
            d3.select('#countrypanel-exchange-tooltip')
                .style('display', 'none');
        })
        .onExchangeMouseMove(function(d) {
            d3.select('#countrypanel-exchange-tooltip')
                .style('transform',
                    'translate(' +
                        (d3.event.pageX + 15) + 'px' + ',' + 
                        (d3.event.pageY + 15) + 'px' +
                    ')');
        })
        .onProductionMouseOver(function (d, countryCode) {
            var co2intensity = countries[countryCode].productionCo2Intensities[d.mode];
            co2Colorbar.currentMarker(co2intensity);
            var tooltip = d3.select('#countrypanel-production-tooltip');
            tooltip.style('display', 'inline');
            tooltip.selectAll('#mode').text(d.mode);
            tooltip.select('.emission-rect')
                .style('background-color', co2intensity ? co2color(co2intensity) : 'gray');
            tooltip.select('.emission-intensity')
                .text(Math.round(co2intensity) || '?');
            var capacityFactor = Math.round(d.production / d.capacity * 100) || '?';
            tooltip.select('#capacity-factor').text(capacityFactor + ' %');
            tooltip.select('#capacity-factor-detail').text(
                (formatPower(d.production) || '?') + ' ' +
                ' / ' + 
                (formatPower(d.capacity) || '?'));
            // Calculate total power available in zone
            var totalProduction = countries[countryCode].totalProduction;
            var netExchange = countries[countryCode].totalNetExchange;
            var totalConsumption = totalProduction + netExchange;
            var productionProportion = Math.round(d.production / totalConsumption * 100) || '?';
            tooltip.select('#production-proportion').text(
                productionProportion + ' %');
            tooltip.select('#production-proportion-detail').text(
                (formatPower(d.production) || '?') + ' ' +
                ' / ' + 
                (formatPower(totalConsumption) || '?'));
            tooltip.select('.country-code').text(countryCode);
        })
        .onProductionMouseMove(function(d) {
            d3.select('#countrypanel-production-tooltip')
                .style('transform',
                    'translate(' +
                        (d3.event.pageX + 10) + 'px' + ',' + 
                        (d3.event.pageY + 10) + 'px' +
                    ')');
        })
        .onProductionMouseOut(function (d) {
            co2Colorbar.currentMarker(undefined);
            d3.select('#countrypanel-production-tooltip')
                .style('display', 'none');
        });
}
