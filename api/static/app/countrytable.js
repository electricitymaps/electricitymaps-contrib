function CountryTable(selector, co2Color) {
    this.root = d3.select(selector);
    this.co2Color = co2Color;

    // Create containers
    this.headerRoot = this.root.append('g');
    this.productionRoot = this.root.append('g');
    this.exchangeRoot = this.root.append('g');

    // Constants
    this.ROW_HEIGHT = 10;
    this.RECT_OPACITY = 0.8;
    this.LABEL_MAX_WIDTH = 60;
    this.PADDING_X = 5; this.PADDING_Y = 5; // Inner paddings
    this.FLAG_SIZE_MULTIPLIER = 3;
    this.TEXT_ADJUST_Y = 9; // To align properly on a line
    this.PRODUCTION_COLORS = {
        'wind': '#74cdb9',
        'solar': '#f27406',
        'hydro': '#2772b2',
        'biomass': '#166a57',
        'nuclear': '#AEB800',
        'gas': '#f30a0a',
        'coal': '#ac8c35',
        'oil': '#8356a2',
        'unknown': 'gray'
    };
    this.PRODUCTION_MODES = d3.keys(this.PRODUCTION_COLORS);
    this.POWER_FORMAT = function (d) { return d3.format('s')(d * 1000000) + 'W'; };

    // State
    this._displayByEmissions = false;

    // Header
    this.gPowerAxis = this.headerRoot.append('g')
        .attr('class', 'x axis');
}

CountryTable.prototype.render = function() {
    var that = this;

    var width = this.root.node().getBoundingClientRect().width;
    if (width == 0)
        return;

    // Update scale
    this.barMaxWidth = width - 2 * this.PADDING_X - this.LABEL_MAX_WIDTH;
    this.powerScale = d3.scale.linear()
        .range([0, this.barMaxWidth]);
    this.co2Scale = d3.scale.linear()
        .range([0, this.barMaxWidth]);

    // ** Production labels and rects **
    var gNewRow = this.productionRoot.selectAll('.row')
        .data(this.PRODUCTION_MODES)
        .enter()
        .append('g')
            .attr('class', 'row')
            .attr('transform', function(d, i) {
                return 'translate(0,' + (i * (that.ROW_HEIGHT + that.PADDING_Y)) + ')';
            });
    gNewRow.append('text')
        .text(function(d) { return d; })
        .attr('transform', 'translate(0, ' + this.TEXT_ADJUST_Y + ')');
    gNewRow.append('rect')
        .attr('class', 'capacity')
        .attr('height', this.ROW_HEIGHT)
        .attr('fill', function (d) { return that.PRODUCTION_COLORS[d]; })
        .attr('fill-opacity', 0.2)
        .attr('stroke', function (d) { return that.PRODUCTION_COLORS[d]; })
        .attr('stroke-width', 1.0)
        .attr('opacity', 0.3)
        .attr('shape-rendering', 'crispEdges');
    gNewRow.append('rect')
        .attr('class', 'production')
        .attr('height', this.ROW_HEIGHT)
        .attr('fill', function (d) { return that.PRODUCTION_COLORS[d]; })
        .attr('opacity', this.RECT_OPACITY)
        .attr('shape-rendering', 'crispEdges');
    gNewRow.append('text')
        .attr('class', 'unknown')
        .text('?')
        .style('fill', 'darkgray')
        .attr('transform', 'translate(1, ' + this.TEXT_ADJUST_Y + ')')
        .style('display', 'none');
    this.resize();
}

CountryTable.prototype.displayByEmissions = function(arg) {
    if (arg === undefined) return this._displayByEmissions;
    else {
        this._displayByEmissions = arg;
        // Quick hack to re-render
        this.data(this._data);
    }
    return this;
}

CountryTable.prototype.onExchangeMouseOver = function(arg) {
    if (!arg) return this.exchangeMouseOverHandler;
    else this.exchangeMouseOverHandler = arg;
    return this;
}
CountryTable.prototype.onExchangeMouseOut = function(arg) {
    if (!arg) return this.exchangeMouseOutHandler;
    else this.exchangeMouseOutHandler = arg;
    return this;
}
CountryTable.prototype.onProductionMouseOver = function(arg) {
    if (!arg) return this.productionMouseOverHandler;
    else this.productionMouseOverHandler = arg;
    return this;
}
CountryTable.prototype.onProductionMouseOut = function(arg) {
    if (!arg) return this.productionMouseOutHandler;
    else this.productionMouseOutHandler = arg;
    return this;
}

CountryTable.prototype.resize = function() {
    this.headerHeight = 2 * this.ROW_HEIGHT;
    this.productionHeight = this.PRODUCTION_MODES.length * (this.ROW_HEIGHT + this.PADDING_Y);
    this.exchangeHeight = (!this._data) ? 0 : d3.entries(this._data.exchange).length * (this.ROW_HEIGHT + this.PADDING_Y);

    this.yProduction = this.headerHeight + this.ROW_HEIGHT;
    this.productionRoot
        .attr('transform', 'translate(0,' + this.yProduction + ')');
    this.yExchange = this.yProduction + this.productionHeight + this.ROW_HEIGHT + this.PADDING_Y;
    this.exchangeRoot
        .attr('transform', 'translate(0,' + this.yExchange + ')');

    this.root
        .attr('height', this.yExchange + this.exchangeHeight);
}

CountryTable.prototype.show = function() {
    this.root.style('display', 'block');
    d3.select('.country-table-header')
        .style('display', 'block');
    this.render();
}

CountryTable.prototype.hide = function() {
    this.root.style('display', 'none');
    d3.select('.country-table-header')
        .style('display', 'none');
}

CountryTable.prototype.data = function(arg) {
    var that = this;

    if (!arg) return this._data;
    else {
        this._data = arg;
        var exchangeData = d3.entries(this._data.exchange);

        // Construct a list having each production in the same order as
        // `this.PRODUCTION_MODES`
        var sortedProductionData = this.PRODUCTION_MODES.map(function (d) {
            return {
                production: arg.production[d],
                capacity: arg.capacity[d],
                mode: d,
                gCo2eqPerkWh: co2eqCalculator.footprintOf(d, that._data.countryCode),
                gCo2eqPerH: co2eqCalculator.footprintOf(d, that._data.countryCode) * 1000.0 * arg.production[d]
            };
        }).filter(function (d) {
            return d.mode != 'unknown' || d !== undefined;
        });

        // update scales
        this.powerScale
            .domain([
                -this._data.maxExport,
                Math.max(this._data.maxCapacity, this._data.maxProduction)
            ]);
        // co2 scale in tCO2eq/s
        var maxCO2eqExport = d3.max(exchangeData, function (d) {
            return d.value >= 0 ? 0 : that._data.co2 / 1000.0 * -d.value;
        });
        var maxCO2eqImport = d3.max(exchangeData, function (d) {
            return d.value <= 0 ? 0 : that._data.neighborCo2[d.key]() / 1000.0 * d.value;
        });
        this.co2Scale
            .domain([
                -maxCO2eqExport || 0,
                Math.max(
                    d3.max(sortedProductionData, function (d) { return d.gCo2eqPerH / 1000000.0; }),
                    maxCO2eqImport || 0
                )
            ]);

        // Prepare axis
        this.axis = d3.svg.axis()
            .orient('top')
            .innerTickSize(-250)
            .outerTickSize(0)
            .ticks(4);
        if (that._displayByEmissions)
            this.axis
                .scale(this.co2Scale)
                .tickFormat(function (d) { return d3.format('s')(d) + 't/h'; });
        else
            this.axis
                .scale(this.powerScale)
                .tickFormat(this.POWER_FORMAT)
        this.gPowerAxis
            .transition()
            .attr('transform', 'translate(' + (this.powerScale.range()[0] + this.LABEL_MAX_WIDTH) + ', 24)')
            .call(this.axis);
        this.gPowerAxis.selectAll('.tick text')
            .attr('fill', 'gray')
            .attr('font-size', '0.7em')
        this.gPowerAxis.selectAll('.tick line')
                .style('stroke', 'gray')
                .style('stroke-width', 1)
                .attr('opacity', 0.3)
                .attr('shape-rendering', 'crispEdges')
        this.gPowerAxis.select('path')
                .style('fill', 'none')
                .style('stroke', 'gray')
                .attr('opacity', 0.3)
                .attr('shape-rendering', 'crispEdges')


        // Set header
        var header = d3.select('.country-table-header');
        header.select('img.country-flag')
            .attr('width', 4 * this.FLAG_SIZE_MULTIPLIER)
            .attr('height', 3 * this.FLAG_SIZE_MULTIPLIER)
            .attr('src', 'vendor/flag-icon-css/flags/4x3/' + this._data.countryCode.toLowerCase() + '.svg')
        header.select('span.country-name')
            .text(this._data.countryCode);
        header.select('span.country-last-update')
            .text(moment(this._data.datetime).fromNow())

        var selection = this.productionRoot.selectAll('.row')
            .data(sortedProductionData);
        /*selection.select('rect.capacity')
            .attr('fill', function (d) { return that.co2Color(d.gCo2eqPerkWh); })
            .attr('stroke', function (d) { return that.co2Color(d.gCo2eqPerkWh); });*/
        if (that._displayByEmissions)
            selection.select('rect.capacity')
                .transition()
                .style('display', 'none')
        else
            selection.select('rect.capacity')
                .transition()
                .attr('x', that.LABEL_MAX_WIDTH + that.powerScale(0))
                .attr('width', function (d) {
                    return (d.capacity === undefined || d.production === undefined) ? 0 : (that.powerScale(d.capacity) - that.powerScale(0));
                })
                .each('end', function () { d3.select(this).style('display', 'block'); });
        selection.select('rect.production')
            .on('mouseover', function (d) {
                that.productionMouseOverHandler.call(this, d, that._data.countryCode);
            })
            .on('mouseout', function (d) {
                that.productionMouseOutHandler.call(this, d);
            })
            .on('click', function (d) {
                console.log(d.gCo2eqPerH / 1000000.0, 'tCO2eq/h');
            })
        /*selection.select('rect.production')
            .attr('fill', function (d) { return that.co2Color(d.gCo2eqPerkWh); });*/
        if (that._displayByEmissions)
            selection.select('rect.production')
                .transition()
                .attr('x', that.LABEL_MAX_WIDTH + that.co2Scale(0))
                .attr('width', function (d) {
                    return !isFinite(d.gCo2eqPerH) ? 0 : (that.co2Scale(d.gCo2eqPerH / 1000000.0) - that.co2Scale(0));
                });
        else
            selection.select('rect.production')
                .transition()
                .attr('x', that.LABEL_MAX_WIDTH + that.powerScale(0))
                .attr('width', function (d) {
                    return d.production === undefined ? 0 : (that.powerScale(d.production) - that.powerScale(0));
                });
        selection.select('text.unknown')
            .transition()
            .attr('x', that.LABEL_MAX_WIDTH + (that._displayByEmissions ? that.co2Scale(0) : that.powerScale(0)))
            .style('display', function (d) {
                return d.production === undefined ? 'block' : 'none';
            });

        // Construct exchanges
        var selection = this.exchangeRoot.selectAll('.row')
            .data(exchangeData);
        selection.exit().remove();
        var gNewRow = selection.enter().append('g')
            .attr('class', 'row')
            .attr('transform', function (d, i) {
                return 'translate(0,' + i * (that.ROW_HEIGHT + that.PADDING_Y) + ')';
            });
        gNewRow.append('image')
            .attr('width', 4 * this.FLAG_SIZE_MULTIPLIER)
            .attr('height', 3 * this.FLAG_SIZE_MULTIPLIER);
        gNewRow.append('text')
            .attr('x', 4 * this.FLAG_SIZE_MULTIPLIER + this.PADDING_X)
            .attr('transform', 'translate(0, ' + this.TEXT_ADJUST_Y + ')'); // TODO: Translate by the right amount of em
        gNewRow.append('text')
            .attr('class', 'unknown')
            .style('fill', 'darkgray')
            .text('?');
        gNewRow.append('rect')
            .attr('height', this.ROW_HEIGHT)
            .attr('opacity', this.RECT_OPACITY)
            .style('transform-origin', 'left')
        selection.select('text.unknown')
            .transition()
            .attr('transform', 'translate(' + (that.LABEL_MAX_WIDTH + that.co2Scale(0)) + ', ' + this.TEXT_ADJUST_Y + ')')
            .style('display', function(d) {
                return (that._displayByEmissions && getExchangeCo2eq(d) === undefined) ? 'block' : 'none';
            });
        selection.select('image')
            .attr('xlink:href', function (d) {
                return 'vendor/flag-icon-css/flags/4x3/' + d.key.toLowerCase() + '.svg';
            })
        function getExchangeCo2eq(d) {
            return d.value > 0 ? 
                (that._data.neighborCo2[d.key]() !== undefined) ? that._data.neighborCo2[d.key]() : undefined
                : (that._data.co2 !== undefined) ? that._data.co2 : undefined;
        }
        selection.select('rect')
            .on('mouseover', function (d) {
                that.exchangeMouseOverHandler.call(this, d, that._data.countryCode);
            })
            .on('mouseout', function (d) {
                that.exchangeMouseOutHandler.call(this, d);
            })
            .transition()
            .attr('fill', function (d, i) {
                if (that._displayByEmissions)
                    return 'gray'
                else {
                    var co2intensity = getExchangeCo2eq(d);
                    return (co2intensity !== undefined) ? that.co2Color(co2intensity) : 'gray';
                }
            })
            .attr('x', function (d) {
                if (that._displayByEmissions) {
                    var co2intensity = getExchangeCo2eq(d);
                    if (getExchangeCo2eq(d) === undefined)
                        return that.LABEL_MAX_WIDTH;
                    else
                        return that.LABEL_MAX_WIDTH + that.co2Scale(Math.min(d.value / 1000.0 * co2intensity, 0));
                }
                else
                    return that.LABEL_MAX_WIDTH + that.powerScale(Math.min(d.value, 0));
            })
            .attr('width', function (d) { 
                if (that._displayByEmissions) {
                    var co2intensity = getExchangeCo2eq(d);
                    if (getExchangeCo2eq(d) === undefined)
                        return 0;
                    else
                        return Math.abs(that.co2Scale(d.value / 1000.0 * co2intensity) - that.co2Scale(0));
                }
                else
                    return Math.abs(that.powerScale(d.value) - that.powerScale(0));
            })
        selection.select('text')
            .text(function(d) { return d.key; });
        d3.select('.country-emission-intensity')
            .text(Math.round(this._data.co2));
        d3.select('.country-emission-rect')
            .transition()
            .style('background-color', that.co2Color(this._data.co2));

        this.resize();
    }
    return this;
};
