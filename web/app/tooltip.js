exports = module.exports = {};

var d3 = require('d3');
var lang = require('json-loader!./configs/lang.json')[locale];

// Create power formatting
function formatPower(d, numDigits) {
    // Assume MW input
    if (d == null || d == NaN) return d;
    if (numDigits == null) numDigits = 3;
    return d3.format('.' + numDigits + 's')(d * 1e6) + 'W';
}

function getConsumption(country) {
    return country.totalProduction - country.totalStorage + country.totalNetExchange;
}

// ** Country table
exports.setupCountryTable = function (countryTable, countries, co2Colorbar, co2color) {
    countryTable
        .onExchangeMouseOver(function (d, countryCode) {
            var isExport = d.value < 0;
            var o = d.value < 0 ? countryCode : d.key;
            var country = countries[countryCode];
            var co2intensity = countries[o].co2intensity;
            if (co2Colorbar) co2Colorbar.currentMarker(co2intensity);
            var tooltip = d3.select('#countrypanel-exchange-tooltip');
            tooltip.style('display', 'inline');
            tooltip.select('#label').text(isExport ? lang['exportto'] : lang['importfrom']);
            tooltip.select('#country-code').text(d.key);
            tooltip.select('.emission-rect')
                .style('background-color', co2intensity ? co2color(co2intensity) : 'gray');
            tooltip.select('.emission-intensity')
                .text(Math.round(co2intensity) || '?');
            tooltip.selectAll('i.country-exchange-flag')
                .attr('class', 'country-exchange-flag flag-icon flag-icon-' + d.key.toLowerCase());
            tooltip.selectAll('i.country-flag')
                .attr('class', 'country-flag flag-icon flag-icon-' + countryCode.toLowerCase());
            var totalConsumption = getConsumption(country);
            var totalPositive = country.totalProduction + country.totalImport;

            var domain = isExport ? totalPositive : totalConsumption;
            var domainName = isExport ? lang['electricityto'] : lang['electricityfrom'];
            var isNull = !isFinite(d.value) || d.value == undefined;

            var absFlow = Math.abs(d.value);
            var exchangeProportion = !isNull ? Math.round(absFlow / domain * 100) : '?';
            tooltip.select('#exchange-proportion').text(exchangeProportion + ' %');
            tooltip.select('#exchange-proportion-detail').text(
                (!isNull ? formatPower(absFlow) : '?') + ' ' +
                ' / ' + 
                (!isNull ? formatPower(domain) : '?'));
            tooltip.select('#domain-name').text(domainName);

            tooltip.selectAll('.country-code')
                .text(countryCode)
                .style('font-weight', 'bold');
            tooltip.selectAll('.country-exchange-code')
                .text(d.key)
                .style('font-weight', 'bold');
            tooltip.selectAll('.country-exchange-source-code')
                .text(o)
                .style('font-weight', 'bold');
            tooltip.selectAll('i.country-exchange-source-flag')
                .attr('class', 'country-exchange-source-flag flag-icon flag-icon-' + o.toLowerCase());
        })
        .onExchangeMouseOut(function (d) {
            if (co2Colorbar) co2Colorbar.currentMarker(undefined);
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
            var country = countries[countryCode];
            var co2intensity = country.productionCo2Intensities[d.mode];
            if (co2Colorbar) co2Colorbar.currentMarker(co2intensity);
            var tooltip = d3.select('#countrypanel-production-tooltip');
            tooltip.style('display', 'inline');
            tooltip.selectAll('#mode').text(d.text || d.mode);
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
            var totalConsumption = getConsumption(country);
            var totalPositive = country.totalProduction + country.totalImport;
            var value = d.isStorage ? d.storage : d.production;

            var domain = d.isStorage ? totalPositive : totalPositive;
            var domainName = d.isStorage ?
                (lang['electricitystored'] + ' ' + (d.text || d.mode)) :
                (lang['electricityfrom']   + ' ' + (d.text || d.mode));
            var isNull = !isFinite(value) || value == undefined;

            var productionProportion = !isNull ? Math.round(value / domain * 100) : '?';
            tooltip.select('#production-proportion').text(
                productionProportion + ' %');
            tooltip.select('#production-proportion-detail').text(
                (!isNull ? formatPower(value) : '?') + ' ' +
                ' / ' + 
                (!isNull ? formatPower(domain) : '?'));
            tooltip.selectAll('#domain-name').text(domainName);

            tooltip.select('.country-code')
                .text(countryCode)
                .style('font-weight', 'bold');
            tooltip.select('i#country-flag')
                .attr('class', 'flag-icon flag-icon-' + countryCode.toLowerCase());
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
            if (co2Colorbar) co2Colorbar.currentMarker(undefined);
            d3.select('#countrypanel-production-tooltip')
                .style('display', 'none');
        });
}
