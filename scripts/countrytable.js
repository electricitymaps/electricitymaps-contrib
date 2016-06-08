function CountryTable(selector, co2color) {
    this.root = d3.select(selector);
    this.co2color = co2color;

    // Create containers
    this.productionRoot = this.root.append('g');
    this.exchangeRoot = this.root.append('g');
    this.verticalAxis = this.root.append('path');

    // Constants
    this.BAR_HEIGHT = 10;
    this.LABEL_MAX_WIDTH = 60;
    // Inner paddings
    this.PADDING_X = 5;
    this.PADDING_Y = 5;
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

    // ** Production labels and rects **
    let gNewRow = this.productionRoot.selectAll('.row')
        .data(this.PRODUCTION_MODES)
        .enter()
        .append('g')
            .attr('class', 'row')
            .attr('transform', function(d, i) {
                return 'translate(0,' + (i * (that.BAR_HEIGHT + that.PADDING_Y)) + ')';
            });
    gNewRow.append('text')
        .text(function(d) { return d; })
        .attr('transform', 'translate(0, 10)'); // TODO: Translate by the right amount of em
    gNewRow.append('rect')
        .attr('class', 'capacity')
        .attr('height', this.BAR_HEIGHT)
        .attr('fill', 'none')
        .attr('stroke', function (d) { return that.PRODUCTION_COLORS[d]; })
        .attr('stroke-width', 1.0)
        .attr('opacity', 0.2)
        .attr('x', that.LABEL_MAX_WIDTH)
        .attr('shape-rendering', 'crispEdges');
    gNewRow.append('rect')
        .attr('class', 'production')
        .attr('height', this.BAR_HEIGHT)
        .attr('fill', function (d) { return that.PRODUCTION_COLORS[d]; })
        .attr('x', that.LABEL_MAX_WIDTH)
        .attr('shape-rendering', 'crispEdges');

    // Vertical axis
    this.verticalAxis
        .attr('stroke-width', 1)
        .attr('stroke', 'black')
        .attr('opacity', 0.1)
        .attr('shape-rendering', 'crispEdges');

    // Resize root
    let productionPanelHeight = this.PRODUCTION_MODES.length * (this.BAR_HEIGHT + this.PADDING_Y);
    this.exchangeRoot.attr('transform', 'translate(0,' + productionPanelHeight + ')');
    this.root
        .attr('height', productionPanelHeight);

    // Update scale
    this.barMaxWidth = width - 2 * this.PADDING_X - this.LABEL_MAX_WIDTH;
    this.powerScale = d3.scale.linear()
        .range([0, this.barMaxWidth]);
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

CountryTable.prototype.data = function(arg) {
    let that = this;

    if (!arg) return this._data;
    else {
        this._data = arg;

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
            .attr('width', function (d) {
                return d.capacity === undefined ? 0 : that.powerScale(d.capacity);
            });
        selection.select('rect.production')
            .transition()
            .attr('width', function (d) {
                return d.production === undefined ? 0 : that.powerScale(d.production);
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
                return 'translate(0,' + i * (that.BAR_HEIGHT + that.PADDING_Y) + ')';
            });
        gNewRow.append('text')
            .attr('transform', 'translate(0, 10)'); // TODO: Translate by the right amount of em
        gNewRow.append('rect')
            .attr('x', this.LABEL_MAX_WIDTH)
            .attr('height', this.BAR_HEIGHT)
            .attr('fill', 'black')
            .style('transform-origin', 'left')
        selection.select('rect')
            .attr('fill', function (d, i) {
                return d.value > 0 ? 
                    that._data.exchangeCo2[d.key] ? that.co2color(that._data.exchangeCo2[d.key]) : 'gray'
                    : that._data.co2 ? that.co2color(that._data.co2) : 'gray';
            })
            .on('mouseover', function (d) {
                that.exchangeMouseOverHandler.call(this, d, that._data.countryCode);
            })
            .on('mouseout', function (d) {
                that.exchangeMouseOverHandler.call(this, d);
            })
            .transition()
            .attr('width', function (d) { 
                return that.powerScale(Math.abs(d.value));
            })
            .style('transform', function (d) {
                return d.value < 0 ? 'scaleX(-1)' : ''; 
            });
        selection.select('text')
            .text(function(d) { return d.key; });

        // Resize root
        let productionPanelHeight = this.PRODUCTION_MODES.length * (this.BAR_HEIGHT + this.PADDING_Y);
        let exchangePanelHeight = exchangeData.length * (this.BAR_HEIGHT + this.PADDING_Y);
        this.root
            .attr('height', productionPanelHeight + exchangePanelHeight);

        // Vertical axis
        this.verticalAxis
            .attr('d', 'M 0 0 L 0 ' + (productionPanelHeight + exchangePanelHeight))
            .attr('transform', 'translate(' + this.LABEL_MAX_WIDTH + ',0)')
    }
    return this;
};
