function CountryTable(selector, co2color) {
    this.root = d3.select(selector);
    this.co2color = co2color;

    // Create containers
    this.headerRoot = this.root.append('g');
    this.productionRoot = this.root.append('g');
    this.exchangeRoot = this.root.append('g');
    this.verticalAxis = this.root.append('path');

    // Constants
    this.ROW_HEIGHT = 10;
    this.LABEL_MAX_WIDTH = 50;
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
}

CountryTable.prototype.render = function() {
    let that = this;

    let width = this.root.node().getBoundingClientRect().width;

    // Update scale
    this.barMaxWidth = width - 2 * this.PADDING_X - this.LABEL_MAX_WIDTH;
    this.powerScale = d3.scale.linear()
        .range([0, this.barMaxWidth]);

    // Header
    this.headerRoot.append('image')
        .attr('class', 'flag-icon')
        .attr('width', 4 * this.FLAG_SIZE_MULTIPLIER)
        .attr('height', 3 * this.FLAG_SIZE_MULTIPLIER)
        .attr('shape-rendering', 'crispEdges');
    this.headerRoot.append('text')
        .attr('class', 'country')
        .style('font-weight', 'bold')
        .attr('transform', 'translate(' + (4 * this.FLAG_SIZE_MULTIPLIER + this.PADDING_Y) + ', ' + this.TEXT_ADJUST_Y + ')') // TODO: Translate by the right amount of em
        .text('<click on a country>');
    this.gPowerAxis = this.headerRoot.append('g')
        .attr('class', 'x axis');

    // ** Production labels and rects **
    let gNewRow = this.productionRoot.selectAll('.row')
        .data(this.PRODUCTION_MODES)
        .enter()
        .append('g')
            .attr('class', 'row')
            .attr('transform', function(d, i) {
                return 'translate(0,' + (i * (that.ROW_HEIGHT + that.PADDING_Y)) + ')';
            });
    gNewRow.append('text')
        .text(function(d) { return d; })
        .attr('transform', 'translate(0, ' + this.TEXT_ADJUST_Y + ')'); // TODO: Translate by the right amount of em
    gNewRow.append('rect')
        .attr('class', 'capacity')
        .attr('height', this.ROW_HEIGHT)
        .attr('fill', 'none')
        .attr('stroke', function (d) { return that.PRODUCTION_COLORS[d]; })
        .attr('stroke-width', 1.0)
        .attr('opacity', 0.4)
        .attr('shape-rendering', 'crispEdges');
    gNewRow.append('rect')
        .attr('class', 'production')
        .attr('height', this.ROW_HEIGHT)
        .attr('fill', function (d) { return that.PRODUCTION_COLORS[d]; })
        .attr('shape-rendering', 'crispEdges');

    // Vertical axis
    this.verticalAxis
        .attr('stroke-width', 1)
        .attr('stroke', 'gray')
        .attr('opacity', 0.4)
        .attr('shape-rendering', 'crispEdges');

    this.resize();
}

CountryTable.prototype.powerDomain = function(arg) {
    if (!arg) return this.powerScale.domain();
    else this.powerScale.domain(arg);
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

CountryTable.prototype.resize = function() {
    this.headerHeight = this.ROW_HEIGHT;
    this.productionHeight = this.PRODUCTION_MODES.length * (this.ROW_HEIGHT + this.PADDING_Y);
    this.exchangeHeight = (!this._data) ? 0 : d3.entries(this._data.exchange).length * (this.ROW_HEIGHT + this.PADDING_Y);
    
    this.yProduction = this.headerHeight + this.ROW_HEIGHT;
    this.productionRoot
        .attr('transform', 'translate(0,' + this.yProduction + ')');
    this.yExchange = this.yProduction + this.productionHeight + this.ROW_HEIGHT;
    this.exchangeRoot
        .attr('transform', 'translate(0,' + this.yExchange + ')');

    this.root
        .attr('height', this.yExchange + this.exchangeHeight);
}

CountryTable.prototype.data = function(arg) {
    let that = this;

    if (!arg) return this._data;
    else {
        this._data = arg;

        // Prepare axis
        this.axis = d3.svg.axis()
            .scale(this.powerScale)
            .orient('top')
            .innerTickSize(-5)
            .outerTickSize(0)
            .ticks(4)
            .tickFormat(function (d) { return d3.format('s')(d * 1000000) + 'W'; });
        this.gPowerAxis
            .attr('transform', 'translate(' + (this.powerScale.range()[0] + this.LABEL_MAX_WIDTH) + ', 10)')
            .call(this.axis);
        this.gPowerAxis.selectAll('.tick text')
            .attr('fill', 'gray')
            .attr('font-size', '0.4em')
        this.gPowerAxis.selectAll('.tick line')
                .style('stroke', 'gray')
                .style('stroke-width', 1)
                .attr('shape-rendering', 'crispEdges')
        this.gPowerAxis.select('path')
                .style('fill', 'none')
                .style('stroke', 'gray')
                .attr('shape-rendering', 'crispEdges')

        // Set header
        this.headerRoot.select('image.flag-icon')
            .attr('xlink:href', 'vendor/flag-icon-css/flags/4x3/' + this._data.countryCode.toLowerCase() + '.svg')
        this.headerRoot.select('text.country')
            .text(this._data.countryCode);


        // Construct a list having each production in the same order as
        // `this.PRODUCTION_MODES`
        let sortedProductionData = this.PRODUCTION_MODES.map(function (d) {
            return {
                production: arg.production[d],
                capacity: arg.capacity[d]
            };
        });
        var selection = this.productionRoot.selectAll('.row')
            .data(sortedProductionData);
        selection.select('rect.capacity')
            .transition()
            .attr('x', that.LABEL_MAX_WIDTH + that.powerScale(0))
            .attr('width', function (d) {
                return d.capacity === undefined ? 0 : (that.powerScale(d.capacity) - that.powerScale(0));
            });
        selection.select('rect.production')
            .transition()
            .attr('x', that.LABEL_MAX_WIDTH + that.powerScale(0))
            .attr('width', function (d) {
                return d.production === undefined ? 0 : (that.powerScale(d.production) - that.powerScale(0));
            });

        // Construct exchanges
        let exchangeData = d3.entries(this._data.exchange)
            .filter(function (o) {
                return o.key != 'other';
            });
        var selection = this.exchangeRoot.selectAll('.row')
            .data(exchangeData);
        selection.exit().remove();
        let gNewRow = selection.enter().append('g')
            .attr('class', 'row')
            .attr('transform', function (d, i) {
                return 'translate(0,' + i * (that.ROW_HEIGHT + that.PADDING_Y) + ')';
            });
        gNewRow.append('image')
            .attr('width', 4 * this.FLAG_SIZE_MULTIPLIER)
            .attr('height', 3 * this.FLAG_SIZE_MULTIPLIER)
            .attr('xlink:href', function (d) { 
                return 'vendor/flag-icon-css/flags/4x3/' + d.key + '.svg';
            });
        gNewRow.append('text')
            .attr('x', 4 * this.FLAG_SIZE_MULTIPLIER + this.PADDING_X)
            .attr('transform', 'translate(0, ' + this.TEXT_ADJUST_Y + ')'); // TODO: Translate by the right amount of em
        gNewRow.append('rect')
            .attr('height', this.ROW_HEIGHT)
            .attr('fill', 'black')
            .style('transform-origin', 'left')
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
                    that._data.neighborCo2[d.key] ? that.co2color(that._data.neighborCo2[d.key]) : 'gray'
                    : that._data.co2 ? that.co2color(that._data.co2) : 'gray';
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

        // Vertical axis
        this.verticalAxis
            .transition()
            .attr('d', 'M 0 0 L 0 ' + this.productionHeight + this.exchangeHeight + this.ROW_HEIGHT)
            .attr('transform', 'translate(' + 
                (this.LABEL_MAX_WIDTH + this.powerScale(0)) + ',' +
                this.yProduction + ')')
    }
    return this;
};
