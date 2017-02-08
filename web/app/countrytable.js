var d3 = require('d3');
var lang = require('json-loader!./configs/lang.json')[locale];
var moment = require('moment');

// TODO:
// All non-path (i.e. non-axis) elements should be drawn
// with a % scale.
// This means drawing them once at `.data()` or at construction, and not
// during `render()`

function CountryTable(selector, co2Color, modeColor, modeOrder) {
    var that = this;

    this.root = d3.select(selector);
    this.co2Color = co2Color;

    // Create containers
    this.headerRoot = this.root.append('g');
    this.productionRoot = this.root.append('g');
    this.exchangeRoot = this.root.append('g');

    // Constants
    this.ROW_HEIGHT = 10;
    this.RECT_OPACITY = 0.8;
    this.LABEL_MAX_WIDTH = 80;
    this.PADDING_X = 5; this.PADDING_Y = 5; // Inner paddings
    this.FLAG_SIZE_MULTIPLIER = 3;
    this.TEXT_ADJUST_Y = 9; // To align properly on a line
    this.MODE_COLORS = modeColor;
    this.MODES = [];
    modeOrder.forEach(function(k) {
        that.MODES.push({'mode': k, 'isStorage': k.indexOf('storage') != -1});
    });
    this.SCALE_TICKS = 4;
    this.TRANSITION_DURATION = 250;

    // State
    this._displayByEmissions = false;

    // Header
    this.gPowerAxis = this.headerRoot.append('g')
        .attr('class', 'x axis');

    // Scales
    this.powerScale = d3.scaleLinear();
    this.co2Scale = d3.scaleLinear();

    // Initial objects
    // ** Production labels and rects **
    var gNewRow = this.productionRoot.selectAll('.row')
        .data(this.MODES)
        .enter()
        .append('g')
            .attr('class', 'row')
            .attr('transform', function(d, i) {
                return 'translate(0,' + (i * (that.ROW_HEIGHT + that.PADDING_Y)) + ')';
            });
    gNewRow.append('text')
        .text(function(d) { return lang[d.mode] || d.mode })
        .attr('transform', 'translate(0, ' + this.TEXT_ADJUST_Y + ')');
    gNewRow.append('rect')
        .attr('class', 'capacity')
        .attr('height', this.ROW_HEIGHT)
        .attr('fill-opacity', 0.4)
        .attr('opacity', 0.3)
        .attr('shape-rendering', 'crispEdges');
    gNewRow.append('rect')
        .attr('class', 'production')
        .attr('height', this.ROW_HEIGHT)
        .attr('opacity', this.RECT_OPACITY)
        .attr('shape-rendering', 'crispEdges');
    gNewRow.append('text')
        .attr('class', 'unknown')
        .text('?')
        .style('fill', 'darkgray')
        .attr('transform', 'translate(1, ' + this.TEXT_ADJUST_Y + ')')
        .style('display', 'none');
}

CountryTable.prototype.render = function(ignoreTransitions) {
    var that = this;

    var width = this.root.node().getBoundingClientRect().width;
    if (width == 0)
        return;

    // Update scale
    this.barMaxWidth = width - 2 * this.PADDING_X - this.LABEL_MAX_WIDTH;
    this.powerScale
        .range([0, this.barMaxWidth]);
    this.co2Scale
        .range([0, this.barMaxWidth]);

    var axisHeight = 
        (this.MODES.length + this._exchangeData.length + 1) * (this.ROW_HEIGHT + this.PADDING_Y)
        + this.PADDING_Y;

    this.axis
        .tickSizeInner(-1 * axisHeight)
        .tickSizeOuter(0)
        .ticks(this.SCALE_TICKS);

    this.gPowerAxis
        .transition()
        .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
        // TODO: We should offset by just one pixel because it looks better when
        // the rectangles don't start exactly on the axis...
        // But we should also handle "negative" rects
        .attr('transform', 'translate(' + (this.powerScale.range()[0] + this.LABEL_MAX_WIDTH) + ', 24)')
        .call(this.axis);

    // Set header
    var header = d3.select('.country-table-header');
    header.select('i#country-flag')
        .attr('class', 'flag-icon flag-icon-' + this._data.countryCode.toLowerCase())
    header.select('span.country-name')
        .text(this._data.countryCode);
    header.select('span.country-last-update')
        .text(this._data.datetime ? moment(this._data.datetime).fromNow() : '? minutes ago')

    var selection = this.productionRoot.selectAll('.row')
        .data(this.sortedProductionData);
    /*selection.select('rect.capacity')
        .attr('fill', function (d) { return that.co2Color(d.gCo2eqPerkWh); })
        .attr('stroke', function (d) { return that.co2Color(d.gCo2eqPerkWh); });*/
    if (that._displayByEmissions)
        selection.select('rect.capacity')
            .transition()
            .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
            .style('display', 'none')
    else
        selection.select('rect.capacity')
            .transition()
            .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
            .attr('x', that.LABEL_MAX_WIDTH + that.powerScale(0))
            .attr('width', function (d) {
                return d.capacity !== undefined ? (that.powerScale(d.capacity) - that.powerScale(0)) : 0;
            })
            .on('end', function () { d3.select(this).style('display', 'block'); });
    // Add event handlers
    selection.selectAll('rect.capacity,rect.production')
        .on('mouseover', function (d) {
            if (that.productionMouseOverHandler)
                that.productionMouseOverHandler.call(this, d, that._data.countryCode);
        })
        .on('mouseout', function (d) {
            if (that.productionMouseOutHandler)
                that.productionMouseOutHandler.call(this, d);
        })
        .on('mousemove', function (d) {
            if (that.productionMouseMoveHandler)
                that.productionMouseMoveHandler.call(this, d);
        });
    /*selection.select('rect.production')
        .attr('fill', function (d) { return that.co2Color(d.gCo2eqPerkWh); });*/
    if (that._displayByEmissions)
        selection.select('rect.production')
            .transition()
            .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
            .attr('fill', function (d) {
                // color by Co2 Intensity
                // return that.co2Color(that._data.productionCo2Intensities[d.mode, that._data.countryCode]);
                // color by production mode
                return that.MODE_COLORS[d.mode];
            })
            .attr('x', that.LABEL_MAX_WIDTH + that.co2Scale(0))
            .attr('width', function (d) {
                return !isFinite(d.gCo2eqPerH) ? 0 : (that.co2Scale(d.gCo2eqPerH / 1e6 / 60.0) - that.co2Scale(0));
            });
    else
        selection.select('rect.production')
            .transition()
            .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
            .attr('fill', function (d) {
                return that.MODE_COLORS[d.mode];
            })
            .attr('x', function (d) {
                var value = (!d.isStorage) ? d.production : -1 * d.storage;
                return that.LABEL_MAX_WIDTH + ((value == undefined || !isFinite(value)) ? that.powerScale(0) : that.powerScale(Math.min(0, value)));
            })
            .attr('width', function (d) {
                var value = d.production != undefined ? d.production : -1 * d.storage;
                return (value == undefined || !isFinite(value)) ? 0 : Math.abs(that.powerScale(value) - that.powerScale(0));
            });
    selection.select('text.unknown')
        .transition()
        .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
        .attr('x', that.LABEL_MAX_WIDTH + (that._displayByEmissions ? that.co2Scale(0) : that.powerScale(0)))
        .style('display', function (d) {
            return (d.capacity == undefined || d.capacity > 0) && 
                d.mode != 'unknown' && 
                (d.isStorage ? d.storage == undefined : d.production == undefined) ?
                'block' : 'none';
        });

    // Construct exchanges
    function getExchangeCo2eq(d) {
        return d.value > 0 ? 
            (that._data.exchangeCo2Intensities !== undefined && that._data.exchangeCo2Intensities[d.key] !== undefined) ? that._data.exchangeCo2Intensities[d.key] : undefined
            : (that._data.co2intensity !== undefined) ? that._data.co2intensity : undefined;
    }
    var selection = this.exchangeRoot.selectAll('.row')
        .data(this._exchangeData);
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
        .attr('x', that.LABEL_MAX_WIDTH + 
            (this._displayByEmissions ? this.co2Scale(0) : this.powerScale(0)))
        .style('transform-origin', 'left');
    gNewRow.merge(selection).select('text.unknown')
        .transition()
        .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
        .attr('transform', 'translate(' + (that.LABEL_MAX_WIDTH + that.co2Scale(0)) + ', ' + this.TEXT_ADJUST_Y + ')')
        .style('display', function(d) {
            return (that._displayByEmissions && getExchangeCo2eq(d) === undefined) ? 'block' : 'none';
        });
    gNewRow.merge(selection).select('image')
        .attr('xlink:href', function (d) {
            return 'flag-icon-css/flags/4x3/' + d.key.toLowerCase() + '.svg';
        })
    gNewRow.merge(selection).select('rect')
        .on('mouseover', function (d) {
            if (that.exchangeMouseOverHandler)
                that.exchangeMouseOverHandler.call(this, d, that._data.countryCode);
        })
        .on('mouseout', function (d) {
            if (that.exchangeMouseOutHandler)
                that.exchangeMouseOutHandler.call(this, d);
        })
        .on('mousemove', function (d) {
            if (that.exchangeMouseMoveHandler)
                that.exchangeMouseMoveHandler.call(this, d);
        })
        .transition()
        .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
        .attr('fill', function (d, i) {
            if (that._displayByEmissions)
                return 'gray';
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
                    return that.LABEL_MAX_WIDTH + that.co2Scale(Math.min(d.value / 1e3 / 60.0 * co2intensity, 0));
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
                    return Math.abs(that.co2Scale(d.value / 1e3 / 60.0 * co2intensity) - that.co2Scale(0));
            }
            else
                return Math.abs(that.powerScale(d.value) - that.powerScale(0));
        })
    gNewRow.merge(selection).select('text')
        .text(function(d) { return d.key; });
    d3.select('.country-emission-intensity')
        .text(Math.round(this._data.co2intensity) || '?');
    var hasFossilFuelData = 
        ((this._data.production || {}).gas  != null) || 
        ((this._data.production || {}).coal != null) || 
        ((this._data.production || {}).oil  != null);
    var fossilFuelPercent = (
        ((this._data.production || {}).gas || 0) + 
        ((this._data.production || {}).coal || 0) + 
        ((this._data.production || {}).oil || 0)
    ) / (this._data.totalProduction + this._data.totalImport) * 100;
    d3.select('.fossil-fuel-percentage')
        .text(hasFossilFuelData ? Math.round(fossilFuelPercent) : '?');
    d3.select('.country-spot-price')
        .text(Math.round((this._data.price || {}).value) || '?')
        .style('color', ((this._data.price || {}).value || 0) < 0 ? 'darkred' : undefined);
    d3.select('#country-emission-rect')
        .transition()
        .duration(ignoreTransitions ? 0 : this.TRANSITION_DURATION)
        .style('background-color',
            this._data.co2intensity ?
                that.co2Color(this._data.co2intensity) : 'gray');

    this.resize();
}

CountryTable.prototype.displayByEmissions = function(arg) {
    if (arg === undefined) return this._displayByEmissions;
    else {
        this._displayByEmissions = arg;
        // Quick hack to re-render
        // TODO: In principle we shouldn't be calling `.data()`
        this
            .data(this._data)
            .render();
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
CountryTable.prototype.onExchangeMouseMove = function(arg) {
    if (!arg) return this.exchangeMouseMoveHandler;
    else this.exchangeMouseMoveHandler = arg;
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
CountryTable.prototype.onProductionMouseMove = function(arg) {
    if (!arg) return this.productionMouseMoveHandler;
    else this.productionMouseMoveHandler = arg;
    return this;
}

CountryTable.prototype.resize = function() {
    this.headerHeight = 2 * this.ROW_HEIGHT;
    this.productionHeight = this.MODES.length * (this.ROW_HEIGHT + this.PADDING_Y);
    this.exchangeHeight = (!this._data) ? 0 : d3.entries(this._exchangeData).length * (this.ROW_HEIGHT + this.PADDING_Y);

    this.yProduction = this.headerHeight + this.ROW_HEIGHT;
    this.productionRoot
        .attr('transform', 'translate(0,' + this.yProduction + ')');
    this.yExchange = this.yProduction + this.productionHeight + this.ROW_HEIGHT + this.PADDING_Y;
    this.exchangeRoot
        .attr('transform', 'translate(0,' + this.yExchange + ')');

    this.root
        .attr('height', this.yExchange + this.exchangeHeight);
}

CountryTable.prototype.data = function(arg) {
    var that = this;
    if (!arg) return this._data;

    this._data = arg;
    this._exchangeData = d3.entries(this._data.exchange)
        .sort(function(x, y) {
            return d3.ascending(x.key, y.key);
        });

    // Construct a list having each production in the same order as this.MODES.
    this.sortedProductionData = this.MODES.map(function (d) {
        var footprint = !d.isStorage ? 
            that._data.productionCo2Intensities ? 
                that._data.productionCo2Intensities[d.mode] :
                undefined :
            0;
        var production = !d.isStorage ? (that._data.production || {})[d.mode] : undefined;
        var storage = d.isStorage ? (that._data.storage || {})[d.mode.replace(' storage', '')] : undefined;
        var capacity = !d.isStorage ? (that._data.capacity || {})[d.mode] : undefined;
        return {
            production: production,
            storage: storage,
            isStorage: d.isStorage,
            capacity: capacity,
            mode: d.mode,
            text: lang[d.mode],
            gCo2eqPerkWh: footprint,
            gCo2eqPerH: footprint * 1000.0 * Math.max(production, 0)
        };
    });

    // update scales
    this.powerScale
        .domain(this._powerScaleDomain || [
            Math.min(
                -this._data.maxExport || 0,
                -this._data.maxStorage || 0),
            Math.max(
                this._data.maxCapacity || 0,
                this._data.maxProduction || 0,
                this._data.maxImport || 0)
        ]);
    // co2 scale in tCO2eq/min
    var maxCO2eqExport = d3.max(this._exchangeData, function (d) {
        return d.value >= 0 ? 0 : (that._data.co2intensity / 1e3 * -d.value / 60.0 || 0);
    });
    var maxCO2eqImport = d3.max(this._exchangeData, function (d) {
        if (!that._data.exchangeCo2Intensities) return 0;
        return d.value <= 0 ? 0 : that._data.exchangeCo2Intensities[d.key] / 1e3 * d.value / 60.0;
    });
    this.co2Scale // in tCO2eq/min
        .domain([
            -maxCO2eqExport || 0,
            Math.max(
                d3.max(this.sortedProductionData, function (d) { return d.gCo2eqPerH / 1e6 / 60.0; }) || 0,
                maxCO2eqImport || 0
            )
        ]);

    // Prepare axis
    if (that._displayByEmissions) {
        var value = d3.max(this.co2Scale.domain());
        var p = d3.precisionPrefix(
            (d3.max(this.co2Scale.domain()) - d3.min(this.co2Scale.domain())) / (this.SCALE_TICKS - 1),
            value);
        var f = d3.formatPrefix('.' + p, value);
        this.axis = d3.axisTop(this.co2Scale)
            .tickFormat(function (d) { return f(d) + 't/min'; });
    }
    else {
        var value = d3.max(this.powerScale.domain()) * 1e6;
        var p = d3.precisionPrefix(
            (d3.max(this.powerScale.domain()) - d3.min(this.powerScale.domain())) / (this.SCALE_TICKS - 1) * 1e6,
            value);
        var f = d3.formatPrefix('.' + p, value);
        this.axis = d3.axisTop(this.powerScale)
            .tickFormat(function (d) { return f(d * 1e6) + 'W'; });
    }

    return this;
};

// Hack to fix the scale at a minimum value
CountryTable.prototype.powerScaleDomain = function(arg) {
    if (arg === undefined) return this._powerScaleDomain;
    this._powerScaleDomain = arg;
    return this;
}

module.exports = CountryTable;
