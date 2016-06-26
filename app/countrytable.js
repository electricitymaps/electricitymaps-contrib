function CountryTable(selector, co2color) {
    this.root = d3.select(selector);
    this.co2color = co2color;

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
        'coal': '#ac8c35',
        'oil': '#8356a2',
        'nuclear': '#f5b300',
        'gas': '#f30a0a',
        'other': 'gray'
    };
    this.PRODUCTION_MODES = d3.keys(this.PRODUCTION_COLORS);

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
        .attr('transform', 'translate(1, ' + this.TEXT_ADJUST_Y + ')')
        .style('display', 'none');
    this.resize();
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

        // update scales
        this.powerScale
            .domain([
                -this._data.maxExport,
                Math.max(this._data.maxCapacity, this._data.maxProduction)
            ])

        // Prepare axis
        this.axis = d3.svg.axis()
            .scale(this.powerScale)
            .orient('top')
            .innerTickSize(-250)
            .outerTickSize(0)
            .ticks(4)
            .tickFormat(function (d) { return d3.format('s')(d * 1000000) + 'W'; });
        this.gPowerAxis
            .transition()
            .attr('transform', 'translate(' + (this.powerScale.range()[0] + this.LABEL_MAX_WIDTH) + ', 24)')
            .call(this.axis);
        this.gPowerAxis.selectAll('.tick text')
            .attr('fill', 'gray')
            .attr('font-size', '0.4em')
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


        // Construct a list having each production in the same order as
        // `this.PRODUCTION_MODES`
        var sortedProductionData = this.PRODUCTION_MODES.map(function (d) {
            return {
                production: arg.production[d],
                capacity: arg.capacity[d],
                mode: d,
                gCo2eqPerkWh: co2eqCalculator.footprintOf(d, that._data.countryCode),
                gCo2eqPerHour: co2eqCalculator.footprintOf(d, that._data.countryCode) * 1000.0 * arg.production[d]
            };
        });

        var selection = this.productionRoot.selectAll('.row')
            .data(sortedProductionData);
        selection.select('rect.capacity')
            .transition()
            /*.attr('fill', function (d) { return that.co2color(d.gCo2eqPerkWh); })
            .attr('stroke', function (d) { return that.co2color(d.gCo2eqPerkWh); })*/
            .attr('x', that.LABEL_MAX_WIDTH + that.powerScale(0))
            .attr('width', function (d) {
                return (d.capacity === undefined || d.production === undefined) ? 0 : (that.powerScale(d.capacity) - that.powerScale(0));
            });
        selection.select('rect.production')
            .on('mouseover', function (d) {
                that.productionMouseOverHandler.call(this, d, that._data.countryCode);
            })
            .on('mouseout', function (d) {
                that.productionMouseOutHandler.call(this, d);
            })
            .on('click', function (d) {
                console.log(d.gCo2eqPerHour / 1000000.0 / 3600.0, 'tCo2eq/s');
            })
            .transition()
            //.attr('fill', function (d) { return that.co2color(d.gCo2eqPerkWh); })
            .attr('x', that.LABEL_MAX_WIDTH + that.powerScale(0))
            .attr('width', function (d) {
                return d.production === undefined ? 0 : (that.powerScale(d.production) - that.powerScale(0));
            });
        selection.select('text.unknown')
            .transition()
            .attr('x', that.LABEL_MAX_WIDTH + that.powerScale(0))
            .style('fill', 'lightgray')
            .style('display', function (d) {
                return d.production === undefined ? 'block' : 'none';
            });
        // Construct exchanges
        var exchangeData = d3.entries(this._data.exchange);
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
        gNewRow.append('rect')
            .attr('height', this.ROW_HEIGHT)
            .attr('opacity', this.RECT_OPACITY)
            .style('transform-origin', 'left')
        selection.select('image')
            .attr('xlink:href', function (d) {
                return 'vendor/flag-icon-css/flags/4x3/' + d.key.toLowerCase() + '.svg';
            })
        selection.select('rect')
            .on('mouseover', function (d) {
                that.exchangeMouseOverHandler.call(this, d, that._data.countryCode);
            })
            .on('mouseout', function (d) {
                that.exchangeMouseOutHandler.call(this, d);
            })
            .transition()
            .attr('fill', function (d, i) {
                return d.value > 0 ? 
                    (that._data.neighborCo2[d.key]() !== undefined) ? that.co2color(that._data.neighborCo2[d.key]()) : 'gray'
                    : (that._data.co2 !== undefined) ? that.co2color(that._data.co2) : 'gray';
            })
            .attr('x', function (d) {
                return that.LABEL_MAX_WIDTH + that.powerScale(Math.min(d.value, 0));
            })
            .attr('width', function (d) { 
                return Math.abs(that.powerScale(d.value) - that.powerScale(0));
            })
        selection.select('text')
            .text(function(d) { return d.key; });

        this.resize();
    }
    return this;
};
